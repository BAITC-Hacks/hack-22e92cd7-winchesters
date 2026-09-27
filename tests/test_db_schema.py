"""FND-04, PR 2: the rest of the schema.

What these pin: every table exists after migrating, the models and the
migrations agree (`alembic check`), the ledger tables mirror the LED-03
contract field for field, the append-only tables reject UPDATE and DELETE,
erasing an applicant still removes everything of theirs, protected attributes
cannot be joined into scoring, a failed model run cannot pass for a result,
and a later batch rebuild cannot quietly strip the append-only triggers.
"""

from __future__ import annotations

import dataclasses
import shutil
import textwrap
import uuid

import pytest
from alembic import command
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import Column, Text, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from backend.db import candidates as candidate_store
from backend.db import users as user_store
from backend.db.engine import REPO_ROOT, alembic_config, make_engine, missing_append_only_triggers
from backend.db.tables import (
    APPEND_ONLY_TABLES,
    Applicant,
    Artifact,
    AuditLogEntry,
    CommitteeOverrideRecord,
    CommitteeSignatureRecord,
    CompetencyScore,
    Consent,
    EvidenceItemRecord,
    ModelRun,
    PromptVersion,
    ProtectedAttributesRecord,
    Rating,
    RubricVersion,
    User,
    append_only_trigger_names,
)
from backend.ledger.schema import CandidateLedger, CompetencyRating, EvidenceItem, IndicatorRating
from backend.scoring.protected_attributes import ProtectedAttributes

NEW_TABLES = {
    "model_runs",
    "rubric_versions",
    "prompt_versions",
    "evidence_items",
    "ratings",
    "competency_scores",
    "committee_overrides",
    "audit_log",
    "protected_attributes",
    "consents",
}

# Every table with a row per applicant. audit_log is deliberately absent.
APPLICANT_OWNED = [
    Artifact,
    ModelRun,
    CompetencyScore,
    Rating,
    EvidenceItemRecord,
    CommitteeOverrideRecord,
    ProtectedAttributesRecord,
    Consent,
]


def _url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _columns(model) -> set[str]:
    return set(model.__table__.columns.keys())


# ── A small ledger to act on ───────────────────────────────────────


@pytest.fixture
def ledger(db):
    """One applicant's ledger with a row in every new table: the ids by table."""
    committee = user_store.create_user(f"committee-{uuid.uuid4().hex[:8]}@example.kz", "unused", "C", role="committee")
    applicant_id = candidate_store.applicant_id_for("c-001")
    with Session(db) as session:
        artifact_id = session.exec(select(Artifact.id).where(Artifact.applicant_id == applicant_id)).first()
        rubric = RubricVersion(version="provisional-0.1", content_hash="a" * 64)
        prompt = PromptVersion(version="led-04.0", content_hash="b" * 64)
        session.add_all([rubric, prompt])
        session.flush()
        run = ModelRun(
            applicant_id=applicant_id,
            stage="rate",
            model="claude-opus-5",
            prompt_version_id=prompt.id,
            rubric_version_id=rubric.id,
            status="ok",
            output={"indicators": []},
        )
        session.add(run)
        session.flush()
        score = CompetencyScore(
            applicant_id=applicant_id,
            competency="leadership_abilities",
            level="high",
            rule_applied="R1",
            flags=[{"code": "verify_live", "quote": "", "source": None, "explanation": ""}],
            schema_version="led-03.1",
            rubric_version_id=rubric.id,
            prompt_version_id=prompt.id,
            model_judge="claude-opus-5",
            model_extract="claude-sonnet-5",
            rate_run_id=run.id,
        )
        session.add(score)
        session.flush()
        rating = Rating(
            competency_score_id=score.id,
            applicant_id=applicant_id,
            indicator_id="lead.initiative",
            observed_level="high",
            note="Started it because nobody else had.",
        )
        session.add(rating)
        session.flush()
        evidence = EvidenceItemRecord(
            rating_id=rating.id,
            applicant_id=applicant_id,
            quote="Ешкім бастамаған соң, мен өзім бастадым",
            source="essay",
            source_ref=artifact_id,
            char_start=0,
            char_end=39,
            atola="action",
            verified=True,
        )
        override = CommitteeOverrideRecord(
            applicant_id=applicant_id,
            competency="leadership_abilities",
            from_level="high",
            to_level="normal",
            reason="Interview did not confirm the scale of the project.",
            user_id=committee["id"],
        )
        signature = CommitteeSignatureRecord(
            applicant_id=applicant_id,
            role="chair",
            signer_user_id=committee["id"],
            signer_name="Committee Chair",
        )
        audit = AuditLogEntry(
            actor_user_id=committee["id"],
            action="override",
            object_type="applicant",
            object_id=applicant_id,
            after={"to_level": "normal"},
        )
        protected = ProtectedAttributesRecord(applicant_id=applicant_id, school_type="public", languages_spoken=["kk"])
        consent = Consent(applicant_id=applicant_id, kind="data_processing", given_by="applicant", version="v1")
        session.add_all([evidence, override, signature, audit, protected, consent])
        session.commit()
        return {
            "applicant": applicant_id,
            "committee_user": committee["id"],
            "artifact": artifact_id,
            "rating": rating.id,
            "evidence_items": evidence.id,
            "committee_overrides": override.id,
            "committee_signatures": signature.id,
            "audit_log": audit.id,
        }


# ── Every table exists, and the models match the migrations ────────


def test_every_table_is_created(db):
    tables = set(inspect(db).get_table_names())
    assert NEW_TABLES <= tables
    assert tables - {"alembic_version"} == set(SQLModel.metadata.tables)


def test_template_db_is_at_head_with_append_only_triggers(db):
    """What conftest builds every test's database from."""
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    with db.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == head
        assert missing_append_only_triggers(connection) == []


def test_models_and_migrations_agree(tmp_path):
    """`alembic check`: autogenerate finds nothing left to migrate."""
    config = alembic_config(_url(tmp_path / "check.db"))
    command.upgrade(config, "head")
    command.check(config)


def test_downgrade_removes_the_new_tables_and_upgrade_restores_them(tmp_path):
    config = alembic_config(_url(tmp_path / "cycle.db"))
    engine = make_engine(_url(tmp_path / "cycle.db"))
    command.upgrade(config, "head")
    command.downgrade(config, "0002")
    assert not NEW_TABLES & set(inspect(engine).get_table_names())
    command.upgrade(config, "head")
    engine.dispose()
    engine = make_engine(_url(tmp_path / "cycle.db"))
    assert NEW_TABLES <= set(inspect(engine).get_table_names())
    with engine.connect() as connection:
        assert missing_append_only_triggers(connection) == []
    command.check(config)
    engine.dispose()


# ── The ledger tables mirror LED-03 ────────────────────────────────

# Storage-only columns: keys, links and timestamps the contract has no field for.
STORAGE = {"id", "applicant_id", "created_at"}

# Contract fields that are computed from the stored rows rather than persisted
# (task LED-08). A derived value in a column can drift away from the rule that
# produced it, and a card showing a cap the rule no longer agrees with is worse
# than one showing nothing. `backend.ledger.atola.hydrate` fills them on read,
# and `tests/test_ledger_atola.py` pins that the result is identical.
DERIVED = {"atola_present", "capped_reason"}


def test_evidence_items_mirror_the_contract():
    assert _columns(EvidenceItemRecord) == set(EvidenceItem.model_fields) | STORAGE | {"rating_id"}


def test_ratings_mirror_the_contract():
    # `evidence` is the evidence_items rows pointing here.
    expected = set(IndicatorRating.model_fields) - {"evidence"} - DERIVED
    assert _columns(Rating) == expected | STORAGE | {"competency_score_id"}


def test_competency_scores_mirror_the_contract_and_the_ledger_header():
    # `indicators` are the ratings rows. The ledger header is repeated on each
    # row, its versions as keys into the version tables.
    header = {"schema_version", "model_judge", "model_extract", "rubric_version_id", "prompt_version_id"}
    runs = {"extract_run_id", "rate_run_id"}
    expected = set(CompetencyRating.model_fields) - {"indicators"} - DERIVED
    assert _columns(CompetencyScore) == expected | header | runs | STORAGE
    assert set(CandidateLedger.model_fields) == {
        "applicant_ref",  # applicant_id
        "competencies",  # the rows themselves
        "schema_version",
        "model_judge",
        "model_extract",
        "rubric_version",  # rubric_version_id
        "prompt_version",  # prompt_version_id
    }


def test_protected_attributes_mirror_led_01():
    fields = {f.name for f in dataclasses.fields(ProtectedAttributes)} - {"applicant_ref"}
    assert _columns(ProtectedAttributesRecord) == fields | STORAGE


# ── Protected attributes stay out of scoring ───────────────────────


def test_nothing_references_protected_attributes(db):
    """No score, rating or run can be joined to background through a key."""
    referencing = {
        table.name
        for table in SQLModel.metadata.tables.values()
        for fk in table.foreign_keys
        if fk.column.table.name == "protected_attributes"
    }
    assert referencing == set()
    with db.connect() as connection:
        for table in inspect(connection).get_table_names():
            targets = {fk["table"] for fk in connection.execute(text(f"PRAGMA foreign_key_list('{table}')")).mappings()}
            assert "protected_attributes" not in targets, table


# ── Append-only ────────────────────────────────────────────────────


@pytest.mark.parametrize("table", APPEND_ONLY_TABLES)
def test_append_only_rejects_update(db, ledger, table):
    with db.begin() as connection, pytest.raises(IntegrityError, match=f"{table} is append-only"):
        connection.execute(text(f"UPDATE {table} SET created_at = created_at WHERE id = :id"), {"id": ledger[table]})


@pytest.mark.parametrize("table", APPEND_ONLY_TABLES)
def test_append_only_rejects_delete(db, ledger, table):
    with db.begin() as connection, pytest.raises(IntegrityError, match=f"{table} is append-only"):
        connection.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": ledger[table]})


def test_evidence_cannot_be_deleted_through_its_rating(db, ledger):
    """A cascade from anything but the applicant is still a delete."""
    with db.begin() as connection, pytest.raises(IntegrityError, match="evidence_items is append-only"):
        connection.execute(text("DELETE FROM ratings WHERE id = :id"), {"id": ledger["rating"]})


def test_evidence_cannot_be_deleted_through_its_artifact(db, ledger):
    with db.begin() as connection, pytest.raises(IntegrityError, match="evidence_items is append-only"):
        connection.execute(text("DELETE FROM artifacts WHERE id = :id"), {"id": ledger["artifact"]})


def test_a_user_with_overrides_cannot_be_deleted(db, ledger):
    """Who overrode must survive; SET NULL would be an UPDATE the trigger rejects."""
    with db.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(text("DELETE FROM users WHERE id = :id"), {"id": ledger["committee_user"]})


# ── Erasing an applicant ───────────────────────────────────────────


def test_deleting_an_applicant_cascades_everywhere_but_the_audit_log(db, ledger):
    applicant_id = ledger["applicant"]
    with Session(db) as session:
        session.delete(session.get(Applicant, applicant_id))
        session.commit()

        for model in APPLICANT_OWNED:
            left = session.exec(select(model).where(model.applicant_id == applicant_id)).all()
            assert left == [], model.__tablename__
        assert session.get(EvidenceItemRecord, ledger["evidence_items"]) is None
        assert session.get(CommitteeOverrideRecord, ledger["committee_overrides"]) is None
        # The record that something happened outlives the applicant.
        assert session.get(AuditLogEntry, ledger["audit_log"]) is not None
        # Versions are shared and stay.
        assert session.exec(select(RubricVersion)).all()


def test_other_applicants_are_untouched_by_an_erasure(db, ledger):
    with Session(db) as session:
        before = len(session.exec(select(Artifact)).all())
        own = len(session.exec(select(Artifact).where(Artifact.applicant_id == ledger["applicant"])).all())
        session.delete(session.get(Applicant, ledger["applicant"]))
        session.commit()
        assert len(session.exec(select(Artifact)).all()) == before - own


# ── Model runs: failed is never a result ───────────────────────────


def test_failed_run_stores_null_output_not_a_zero(db):
    with Session(db) as session:
        run = ModelRun(stage="rate", model="claude-opus-5", status="failed", error="reply did not parse")
        session.add(run)
        session.commit()
        run_id = run.id
    with db.connect() as connection:
        output = connection.execute(text("SELECT output FROM model_runs WHERE id = :id"), {"id": run_id}).scalar()
    assert output is None  # SQL NULL, not the JSON text 'null'


@pytest.mark.parametrize(
    "fields",
    [
        {"status": "ok", "output": None},  # ok with nothing to show
        {"status": "failed", "error": None},  # failed without saying why
        {"status": "zero", "output": {"score": 0}},  # not a status
    ],
    ids=["ok-without-output", "failed-without-error", "unknown-status"],
)
def test_model_run_checks_reject(db, fields):
    with Session(db) as session:
        session.add(ModelRun(stage="rate", model="claude-opus-5", **fields))
        with pytest.raises(IntegrityError):
            session.commit()


# ── Batch rebuilds cannot strip the triggers ───────────────────────


def test_a_batch_rebuild_drops_the_triggers(tmp_path):
    """The failure the env.py check exists for: Alembic rebuilds the table and
    SQLite drops the old table's triggers with it."""
    config = alembic_config(_url(tmp_path / "batch.db"))
    command.upgrade(config, "head")
    engine = make_engine(_url(tmp_path / "batch.db"))
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        with operations.batch_alter_table("evidence_items", recreate="always") as batch:
            batch.add_column(Column("extra", Text(), nullable=True))
        assert missing_append_only_triggers(connection) == list(append_only_trigger_names("evidence_items"))
    engine.dispose()


def test_a_migration_that_drops_the_triggers_fails(tmp_path):
    """End to end through env.py: a revision that rebuilds evidence_items and
    forgets the triggers does not complete."""
    scripts = tmp_path / "migrations"
    shutil.copytree(REPO_ROOT / "backend" / "migrations", scripts, ignore=shutil.ignore_patterns("__pycache__"))
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    (scripts / "versions" / "9999_rebuild_evidence.py").write_text(
        textwrap.dedent(
            f'''
            import sqlalchemy as sa
            from alembic import op

            revision = "9999"
            down_revision = "{head}"
            branch_labels = None
            depends_on = None


            def upgrade():
                with op.batch_alter_table("evidence_items", recreate="always") as batch_op:
                    batch_op.add_column(sa.Column("extra", sa.Text(), nullable=True))


            def downgrade():
                pass
            '''
        ),
        encoding="utf-8",
    )
    config = alembic_config(_url(tmp_path / "forgot.db"))
    command.upgrade(config, head)
    config.set_main_option("script_location", str(scripts))
    with pytest.raises(RuntimeError, match="trg_evidence_items_no_update"):
        command.upgrade(config, "head")

    # Rolled back, not left half-applied and stamped as done: the next
    # `upgrade` must not report "already at head" on an editable table.
    engine = make_engine(_url(tmp_path / "forgot.db"))
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == head
        assert "extra" not in {c["name"] for c in inspect(connection).get_columns("evidence_items")}
        assert missing_append_only_triggers(connection) == []
    engine.dispose()


def test_a_database_already_at_0003_gets_committee_signatures(tmp_path):
    """COM-05 first added this table by editing 0003, which databases already
    at 0003 never re-run; the decision memo then failed with "no such table"."""
    url = f"sqlite:///{(tmp_path / 'at-0003.db').as_posix()}"
    command.upgrade(alembic_config(url), "0003")
    engine = make_engine(url)
    try:
        assert "committee_signatures" not in inspect(engine).get_table_names()
        command.upgrade(alembic_config(url), "head")
        assert "committee_signatures" in inspect(engine).get_table_names()
        with engine.connect() as connection:
            assert missing_append_only_triggers(connection) == []
    finally:
        engine.dispose()
