"""A synthetic cohort for demonstrating the attribute audit (task FAIR-07).

Two hundred made-up applicants with self-declared background and a BARS level
per competency, drawn from fixed probabilities with a fixed seed. No model is
called and nothing is written to the database: the profiles exist only for the
duration of the request, carry `syn-` refs, and the audit labels its result
`source="synthetic"` so the panel can say what it is.

What the numbers show is this generator, not the scorer. The point on Oct 3 is
that the method runs end to end and that bootstrap intervals are visible at a
realistic cohort size. So that the "review needed" state appears at all, one
gap is planted on purpose and declared in `PLANTED_EFFECTS`; the panel prints
it. Everything else is drawn independently of background.

This module must not import `protected_attributes`, and no scorer may import
this module. The tests check both.
"""

from __future__ import annotations

import numpy as np

from backend.ledger.schema import Competency
from backend.scoring.fairness_audit import AUDITED_COMPETENCIES, LEVELS

DEFAULT_SEED = 20261003
DEFAULT_SIZE = 200

_BASE_LEVEL_P = (0.30, 0.42, 0.18, 0.10)

# (region, share of pool, share rural). Rough, not census figures.
_REGIONS: tuple[tuple[str, float, float], ...] = (
    ("almaty_city", 0.20, 0.0),
    ("astana", 0.15, 0.0),
    ("shymkent", 0.10, 0.1),
    ("turkistan", 0.14, 0.7),
    ("kyzylorda", 0.10, 0.6),
    ("karaganda", 0.10, 0.3),
    ("east_kazakhstan", 0.09, 0.4),
    ("mangystau", 0.08, 0.4),
    ("abai", 0.04, 0.5),
)
_URBAN_SCHOOLS = (("public", 0.50), ("lyceum", 0.20), ("gymnasium", 0.15), ("private", 0.15))
_RURAL_SCHOOLS = (("village", 0.60), ("public", 0.35), ("lyceum", 0.05))
_URBAN_LANGUAGES = (("ru", 0.40), ("kk", 0.30), ("mixed", 0.25), ("en", 0.05))
_RURAL_LANGUAGES = (("kk", 0.65), ("mixed", 0.25), ("ru", 0.08), ("en", 0.02))
_GENDERS = (("female", 0.50), ("male", 0.47), ("", 0.03))

# The deliberate gap, so the demo can show a group below the review line. It is
# a property of this generator; nothing in the scorer produces or corrects it.
PLANTED_EFFECTS: tuple[dict[str, str], ...] = (
    {
        "competency": Competency.PRIOR_EXPERIENCE.value,
        "group": "rural × kk",
        "effect": "rural applicants writing in Kazakh get High with p=0.12 instead of 0.30; the rest goes to Weak",
    },
)


def _pick(rng: np.random.Generator, options: tuple[tuple[str, float], ...]) -> str:
    values = [value for value, _ in options]
    weights = np.array([weight for _, weight in options])
    return values[int(rng.choice(len(values), p=weights / weights.sum()))]


def _level_probabilities(competency: Competency, attributes: dict) -> tuple[float, ...]:
    if (
        competency is Competency.PRIOR_EXPERIENCE
        and attributes["settlement_type"] == "rural"
        and attributes["application_language"] == "kk"
    ):
        high, normal, weak, no_evidence = _BASE_LEVEL_P
        return (0.12, normal, weak + (high - 0.12), no_evidence)
    return _BASE_LEVEL_P


def generate(n: int = DEFAULT_SIZE, seed: int = DEFAULT_SEED) -> list[dict]:
    """`n` synthetic applicants as audit records: ref, attributes, levels.

    The same (n, seed) always returns the same list.
    """
    rng = np.random.default_rng(seed)
    region_names = [name for name, _, _ in _REGIONS]
    region_p = np.array([share for _, share, _ in _REGIONS])
    rural_p = {name: rural for name, _, rural in _REGIONS}

    records = []
    for i in range(n):
        region = region_names[int(rng.choice(len(region_names), p=region_p / region_p.sum()))]
        rural = bool(rng.random() < rural_p[region])
        attributes = {
            "region": region,
            "settlement_type": "rural" if rural else "urban",
            "school_type": _pick(rng, _RURAL_SCHOOLS if rural else _URBAN_SCHOOLS),
            "application_language": _pick(rng, _RURAL_LANGUAGES if rural else _URBAN_LANGUAGES),
            "foundation_eligible": bool(rng.random() < (0.45 if rural else 0.20)),
            "gender": _pick(rng, _GENDERS),
        }
        levels = {}
        for competency in AUDITED_COMPETENCIES:
            p = _level_probabilities(competency, attributes)
            levels[competency.value] = LEVELS[int(rng.choice(len(LEVELS), p=p))].value
        records.append({"applicant_ref": f"syn-{i + 1:04d}", "attributes": attributes, "levels": levels})
    return records
