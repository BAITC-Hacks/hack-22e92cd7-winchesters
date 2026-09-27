"""Background must not move a score, and it must be checkable (task LED-01).

The client's wording is that bias exclusion has to be "verifiable on data".
These tests are the smallest honest version of that: they take one application,
change only a background marker, and assert the number does not move. They run
offline on every push, so the property cannot quietly regress.

They do not prove the product is fair. Counterfactual probes over real
applications do more of that job (task FAIR-06), and a cohort audit does the
rest (FAIR-07). What these pin is that the arithmetic contains no demographic
term at all, which is the part that used to be false.
"""

from __future__ import annotations

import copy
import json
import pathlib

from backend.models import Candidate
from backend.scoring import protected_attributes as pa
from backend.scoring.ai_scorer import SCORING_PROMPT, SYSTEM_PROMPT, _build_candidate_context
from backend.scoring.baseline import compute_baseline_score
from backend.scoring.signal_extractor import extract_signals, signals_to_context

DATA = pathlib.Path(__file__).resolve().parents[1] / "backend" / "data" / "candidates.json"

SCHOOL_TYPES = ["village", "public", "lyceum", "gymnasium", "private", "international"]


def _candidate(index: int = 0) -> Candidate:
    return Candidate(**json.loads(DATA.read_text(encoding="utf-8"))[index])


def _with_school(candidate: Candidate, school_type: str) -> Candidate:
    twin = copy.deepcopy(candidate)
    twin.application.education.school_type = school_type
    return twin


# ── The invariance that used to fail ──────────────────────────────


def test_school_type_does_not_change_the_score():
    """The advantage table gave a village applicant fifty fewer starting points."""
    base = _candidate()
    scores = {school: compute_baseline_score(_with_school(base, school)).overall_score for school in SCHOOL_TYPES}
    assert len(set(scores.values())) == 1, f"school type still moves the score: {scores}"


def test_school_type_does_not_change_any_dimension():
    base = _candidate()
    per_school = {}
    for school in SCHOOL_TYPES:
        score = compute_baseline_score(_with_school(base, school))
        per_school[school] = tuple(round(d.score, 3) for d in score.dimensions)
    assert len(set(per_school.values())) == 1, f"dimensions still vary by school: {per_school}"


def test_gpa_does_not_change_the_score():
    """The client states grades do not measure what this selection is for."""
    base = _candidate()
    scores = set()
    for gpa in (2.0, 3.0, 3.5, 4.0):
        twin = copy.deepcopy(base)
        twin.application.education.gpa = gpa
        scores.add(compute_baseline_score(twin).overall_score)
    assert len(scores) == 1, f"GPA still moves the score: {scores}"


def test_narrating_hardship_does_not_change_the_score():
    """Every hardship word used to subtract five points from the starting level.

    Which means it paid to disclose hardship, and a candidate who did not narrate
    theirs was scored as though they had started from further ahead.
    """
    base = _candidate()
    twin = copy.deepcopy(base)
    twin.essay.text = (
        base.essay.text
        + " I come from a village, my single mother could not afford tutors, "
        "and I had to work part-time despite everything."
    )
    assert compute_baseline_score(twin).overall_score == compute_baseline_score(base).overall_score


def test_essay_length_does_not_change_the_score():
    """Length bands penalised Kazakh, which says the same thing in fewer tokens."""
    base = _candidate()
    twin = copy.deepcopy(base)
    twin.essay.text = base.essay.text * 3
    twin.essay.word_count = len(twin.essay.text.split())
    assert compute_baseline_score(twin).overall_score == compute_baseline_score(base).overall_score


def test_language_of_the_essay_does_not_change_the_score():
    """English keyword banks returned nothing for Kazakh and Russian essays.

    Both applications below describe the same thing; only the language differs.
    Under the old scorer the Kazakh one lost every keyword point.
    """
    base = _candidate()

    english = copy.deepcopy(base)
    english.essay.text = "I started a tutoring club and organised thirty volunteers. I learned to listen."

    kazakh = copy.deepcopy(base)
    kazakh.essay.text = "Мен репетиторлық клуб аштым және отыз еріктіні ұйымдастырдым. Тыңдауды үйрендім."

    russian = copy.deepcopy(base)
    russian.essay.text = "Я создал клуб репетиторства и организовал тридцать волонтёров. Я научился слушать."

    scores = {
        "en": compute_baseline_score(english).overall_score,
        "kk": compute_baseline_score(kazakh).overall_score,
        "ru": compute_baseline_score(russian).overall_score,
    }
    assert len(set(scores.values())) == 1, f"language still moves the score: {scores}"


# ── Nothing demographic reaches the model ─────────────────────────


def test_the_facts_sent_to_the_model_carry_no_school_type_or_gpa():
    context = signals_to_context(extract_signals(_candidate()))
    lowered = context.casefold()
    assert "school type" not in lowered
    assert "gpa" not in lowered
    assert not pa.find_protected_markers(context)


def test_changing_the_school_field_changes_nothing_the_model_sees():
    """The precise invariant, rather than banning a word.

    An applicant who writes "I tutored students in five villages" must keep
    those words: they are their own account of what they did. What must not
    reach the model is the school-type field from the form. So the check is that
    the rendered context is byte-identical whatever that field is set to.
    """
    base = _candidate()
    rendered = {signals_to_context(extract_signals(_with_school(base, school))) for school in SCHOOL_TYPES}
    assert len(rendered) == 1, "the school-type field still changes what the model sees"


def test_the_prompts_no_longer_instruct_the_model_about_background():
    combined = (SYSTEM_PROMPT + SCORING_PROMPT).casefold()
    for phrase in ("village school", "elite school", "starting_level", "delta", "public/village"):
        assert phrase not in combined, f"prompt still references {phrase!r}"


def test_the_applicant_documents_are_still_passed_whole():
    """Removing background must not quietly remove the applicant's own words."""
    candidate = _candidate()
    context = _build_candidate_context(candidate)
    assert candidate.essay.text[:40] in context


# ── The audit-only boundary ───────────────────────────────────────


def test_background_is_still_collected_for_auditing():
    """Bias exclusion that is verifiable on data needs the attributes kept somewhere."""
    attributes = pa.extract(_candidate())
    assert attributes.applicant_ref
    assert attributes.school_type


def test_no_scorer_imports_the_protected_attributes_module():
    """The boundary is only real if nothing on the scoring path can reach across it."""
    scoring = pathlib.Path(__file__).resolve().parents[1] / "backend" / "scoring"
    offenders = []
    for path in scoring.glob("*.py"):
        if path.name == "protected_attributes.py":
            continue
        body = path.read_text(encoding="utf-8")
        code = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))
        if "import protected_attributes" in code or "from backend.scoring.protected_attributes" in code:
            offenders.append(path.name)
    assert not offenders, f"these modules import protected attributes: {offenders}"


def test_the_exclusion_manifest_names_every_factor_the_client_protects():
    """Region, school, language, family income, manner of speech."""
    for key in ("school_type", "region", "application_language", "family_income", "gpa"):
        assert key in pa.EXCLUDED_FROM_SCORING
        assert pa.EXCLUDED_FROM_SCORING[key].strip(), f"{key} has no stated reason"
    manner_of_speech = {"speech_rate", "pause_ratio", "filler_ratio"}
    assert manner_of_speech <= set(pa.EXCLUDED_FROM_SCORING)


def test_keyword_banks_are_gone_from_the_scoring_path():
    """They were the language penalty; a reappearance should fail the build."""
    scoring = pathlib.Path(__file__).resolve().parents[1] / "backend" / "scoring"
    banned = ["SCHOOL_ADVANTAGE", "ADVERSITY_KEYWORDS", "GROWTH_KEYWORDS", "INITIATIVE_KEYWORDS"]
    for path in scoring.glob("*.py"):
        body = path.read_text(encoding="utf-8")
        code = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))
        for name in banned:
            assert f"{name} =" not in code, f"{name} is back in {path.name}"


def test_the_completeness_reference_recommends_nobody():
    """It measures how complete a file is, so it has no opinion on applicants.

    A badge reading "Recommend" because four sources were uploaded would be a
    merit claim the number does not support.
    """
    candidates = [Candidate(**c) for c in json.loads(DATA.read_text(encoding="utf-8"))]
    verdicts = {compute_baseline_score(c).recommendation for c in candidates}
    assert verdicts == {"consider"}
