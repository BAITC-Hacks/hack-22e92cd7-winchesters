"""Attribute-grouped fairness audit (FAIR-07).

The method's promises, pinned: the same data and seed give the same numbers
(and the CLI prints what the API returns), every interval contains its point
estimate, small groups are marked rather than judged, the 0.8 line triggers
review, only committee and admin can see it, and nothing on the scoring path
can reach the module that joins background to levels.
"""

from __future__ import annotations

import io
import json
import pathlib
from contextlib import redirect_stdout

import pytest
from sqlmodel import Session

from backend.db.candidates import applicant_id_for
from backend.db.fairness import load_audit_records
from backend.db.tables import CompetencyScore, PromptVersion, ProtectedAttributesRecord, RubricVersion
from backend.scoring import fairness_audit as fa
from backend.scoring import synthetic_cohort

URL = "/api/fairness/audit"
BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"


def _records(groups: dict[str, tuple[int, int]], competency: str = "teamwork") -> list[dict]:
    """{group: (n, how many rated high)} -> records split on school_type."""
    records = []
    for group, (n, highs) in groups.items():
        for i in range(n):
            records.append(
                {
                    "applicant_ref": f"{group}-{i}",
                    "attributes": {"school_type": group},
                    "levels": {competency: "high" if i < highs else "normal"},
                }
            )
    return records


def _groups(report: dict, dimension: str = "school_type", competency: str = "teamwork") -> dict[str, dict]:
    cell = next(
        c
        for d in report["dimensions"]
        if d["dimension"] == dimension
        for c in d["competencies"]
        if c["competency"] == competency
    )
    return {g["group"]: g for g in cell["groups"]}


# ── Reproducible ──────────────────────────────────────────────────


def test_same_data_and_seed_give_identical_numbers():
    records = synthetic_cohort.generate()
    first = fa.run_audit(records, source="synthetic")
    second = fa.run_audit(synthetic_cohort.generate(), source="synthetic")
    assert first == second


def test_the_seed_is_what_fixes_the_intervals():
    records = synthetic_cohort.generate()
    a = _groups(fa.run_audit(records, source="synthetic", seed=1), "settlement_type", "prior_experience")
    b = _groups(fa.run_audit(records, source="synthetic", seed=2), "settlement_type", "prior_experience")
    assert a["rural"]["impact_ratio"] == b["rural"]["impact_ratio"]
    assert a["rural"]["ci_low"] != b["rural"]["ci_low"]


def test_numbers_do_not_depend_on_which_competencies_were_asked_for():
    records = synthetic_cohort.generate()
    alone = fa.run_audit(records, source="synthetic", competencies=["values"])
    together = fa.run_audit(records, source="synthetic")
    assert _groups(alone, "region", "values") == _groups(together, "region", "values")


def test_input_hash_ignores_order_and_catches_a_changed_level():
    records = synthetic_cohort.generate(n=30)
    assert fa.input_hash(records) == fa.input_hash(list(reversed(records)))
    changed = json.loads(json.dumps(records))
    changed[0]["levels"]["teamwork"] = "weak" if records[0]["levels"]["teamwork"] != "weak" else "high"
    assert fa.input_hash(changed) != fa.input_hash(records)


def test_the_cli_prints_the_numbers_the_api_returns(client, auth_headers):
    out = io.StringIO()
    with redirect_stdout(out):
        assert fa.main(["--json"]) == 0
    from_cli = json.loads(out.getvalue())
    from_api = client.get(URL, headers=auth_headers("committee")).json()
    from_api.pop("synthetic")
    assert from_cli == from_api


# ── The statistics ────────────────────────────────────────────────


def test_every_interval_contains_its_point_estimate():
    report = fa.run_audit(synthetic_cohort.generate(), source="synthetic")
    checked = 0
    for dimension in report["dimensions"]:
        for cell in dimension["competencies"]:
            for g in cell["groups"]:
                if g["ci_low"] is None:
                    continue
                assert g["ci_low"] <= g["impact_ratio"] <= g["ci_high"], (dimension["dimension"], g)
                checked += 1
    assert checked > 100


def test_a_small_group_is_not_judged_but_its_rates_are_shown():
    groups = _groups(fa.run_audit(_records({"public": (60, 30), "private": (9, 0)}), source="test"))
    small = groups["private"]
    assert small["state"] == "not_enough_data"
    assert small["n"] == 9
    assert small["high_rate"] == 0.0
    assert small["impact_ratio"] == 0.0  # shown, not acted on


def test_a_group_under_two_percent_of_the_pool_is_not_judged():
    groups = _groups(fa.run_audit(_records({"public": (600, 300), "private": (11, 5)}), source="test"))
    assert groups["private"]["share_of_pool"] < 0.02
    assert groups["private"]["state"] == "not_enough_data"


def test_a_tiny_group_cannot_become_the_reference():
    groups = _groups(fa.run_audit(_records({"public": (60, 30), "private": (3, 3)}), source="test"))
    assert groups["public"]["is_reference"]
    assert groups["private"]["impact_ratio"] == 2.0
    assert groups["private"]["state"] == "not_enough_data"


def test_below_point_eight_triggers_review():
    groups = _groups(fa.run_audit(_records({"public": (200, 100), "village": (200, 70)}), source="test"))
    assert groups["public"]["is_reference"] and groups["public"]["state"] == "ok"
    village = groups["village"]
    assert village["impact_ratio"] == pytest.approx(0.7)
    assert (village["state"], village["review_reason"]) == ("review_needed", "below_threshold")


def test_an_interval_reaching_below_point_eight_is_inconclusive_not_ok():
    groups = _groups(fa.run_audit(_records({"public": (40, 20), "lyceum": (40, 18)}), source="test"))
    lyceum = groups["lyceum"]
    assert lyceum["impact_ratio"] == pytest.approx(0.9)
    assert lyceum["ci_low"] < 0.8
    assert (lyceum["state"], lyceum["review_reason"]) == ("review_needed", "interval_crosses_threshold")


def test_a_narrow_interval_above_point_eight_is_ok():
    groups = _groups(fa.run_audit(_records({"public": (4000, 2000), "lyceum": (4000, 1900)}), source="test"))
    assert groups["lyceum"]["ci_low"] >= 0.8
    assert (groups["lyceum"]["state"], groups["lyceum"]["review_reason"]) == ("ok", None)


def test_levels_are_counted_never_averaged():
    report = fa.run_audit(synthetic_cohort.generate(), source="synthetic")
    body = json.dumps(report)
    assert "mean" not in body and "average" not in body
    g = _groups(report, "application_language", "teamwork")["kk"]
    assert sum(g["levels"].values()) == g["n"]


def test_the_planted_gap_shows_up_as_review():
    """The demo's below-the-line group is the one the generator declares."""
    groups = _groups(
        fa.run_audit(synthetic_cohort.generate(), source="synthetic"), "settlement_x_language", "prior_experience"
    )
    assert groups["rural × kk"]["impact_ratio"] < 0.8
    assert groups["rural × kk"]["state"] == "review_needed"


def test_undeclared_background_is_counted_not_grouped():
    records = _records({"public": (20, 10)})
    records.append({"applicant_ref": "x", "attributes": {"school_type": ""}, "levels": {"teamwork": "high"}})
    report = fa.run_audit(records, source="test")
    school = next(d for d in report["dimensions"] if d["dimension"] == "school_type")
    assert school["undeclared"] == 1
    assert set(_groups(report)) == {"public"}


# ── Access ────────────────────────────────────────────────────────


@pytest.mark.parametrize("role", ["applicant", "interviewer"])
def test_only_committee_and_admin_see_the_audit(client, auth_headers, role):
    assert client.get(URL, headers=auth_headers(role)).status_code == 403


def test_no_token_is_401(client):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("role", ["committee", "admin"])
def test_the_synthetic_audit_labels_itself(client, auth_headers, role):
    body = client.get(URL, headers=auth_headers(role)).json()
    assert body["source"] == "synthetic"
    assert "not evidence" in body["synthetic"]["notice"]
    assert body["synthetic"]["planted_effects"]
    assert body["applicants"] == synthetic_cohort.DEFAULT_SIZE


# ── From the database ─────────────────────────────────────────────


def test_db_source_is_empty_until_levels_are_stored(client, auth_headers):
    body = client.get(URL, params={"source": "db"}, headers=auth_headers("committee")).json()
    assert (body["source"], body["applicants"], body["synthetic"]) == ("db", 0, None)
    assert all(not d["competencies"] for d in body["dimensions"])


def test_db_source_joins_declared_background_to_the_latest_level(db):
    applicant = applicant_id_for("c-016")
    with Session(db) as session:
        rubric = RubricVersion(version="provisional-0.1", content_hash="a" * 64)
        prompt = PromptVersion(version="led-04.0", content_hash="b" * 64)
        session.add_all([rubric, prompt])
        session.flush()
        session.add(ProtectedAttributesRecord(applicant_id=applicant, school_type="village", settlement_type="rural"))
        for level in ("weak", "high"):  # a re-score: the second row is current
            session.add(
                CompetencyScore(
                    applicant_id=applicant,
                    competency="teamwork",
                    level=level,
                    schema_version="led-03.1",
                    rubric_version_id=rubric.id,
                    prompt_version_id=prompt.id,
                    model_judge="judge",
                    model_extract="extract",
                )
            )
            session.flush()
        session.commit()

    (record,) = load_audit_records()
    assert record["applicant_ref"] == applicant
    assert record["levels"] == {"teamwork": "high"}
    assert record["attributes"]["school_type"] == "village"
    assert record["attributes"]["foundation_eligible"] is None


# ── The boundary ──────────────────────────────────────────────────

AUDIT_MODULES = (
    "fairness_audit",
    "synthetic_cohort",
    "backend.scoring.fairness_audit",
    "backend.scoring.synthetic_cohort",
    "backend.db.fairness",
)


def _code(path: pathlib.Path) -> str:
    body = path.read_text(encoding="utf-8")
    return "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))


def test_nothing_on_the_scoring_path_imports_the_audit():
    """The audit joins background to levels; a scorer that could reach it could read background."""
    offenders = []
    for folder in ("scoring", "ledger"):
        for path in (BACKEND / folder).rglob("*.py"):
            if path.stem in ("fairness_audit", "synthetic_cohort"):
                continue
            code = _code(path)
            if any(f"import {module}" in code or f"{module} import" in code for module in AUDIT_MODULES):
                offenders.append(str(path.relative_to(BACKEND)))
    assert not offenders, f"these scoring-path modules reach the audit: {offenders}"


def test_the_audit_takes_background_as_data_not_from_protected_attributes():
    for name in ("fairness_audit", "synthetic_cohort"):
        code = _code(BACKEND / "scoring" / f"{name}.py")
        assert "import protected_attributes" not in code
        assert "scoring.protected_attributes" not in code
