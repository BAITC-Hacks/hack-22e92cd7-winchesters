"""Attribute-grouped fairness audit (task FAIR-07, plan §5.12).

Takes applicants as plain records (a ref, self-declared attributes, a BARS
level per competency) and, per attribute and per competency, compares groups:
n, the distribution of levels, the `no_evidence` rate, and the impact ratio of
the share rated High against the best group, with a bootstrap 95% interval.

Why "share rated High" and not a mean level: levels are ordinal and are never
averaged anywhere in the product. NYC's scoring rate (share above the cohort
median) reduces to the same thing on a three-level scale whose median is
Normal. The full distribution is reported next to it, so a gap made of `weak`
reads differently from one made of `no_evidence`.

The 0.8 line is a trigger for human review, never a pass mark (29 CFR 1607.4D
and the Watson et al. critique, docs/research/agent_fairness.md §1a). Three
states per group:

- not_enough_data: n < 10 or under 2% of the pool. Rates are still shown.
- review_needed: the ratio is below 0.8, or its interval reaches below 0.8.
  A wide interval crossing the line is inconclusive, not fair.
- ok: the whole interval is at or above 0.8.

The bootstrap is seeded per (attribute, competency, group), so the numbers do
not depend on which competency was asked for or in what order, and the CLI
(`python -m backend.scoring.fairness_audit`) prints exactly what the API
returns. The response carries a hash of the input records so a published
number can be traced to the data it came from.

Boundary: this module joins background to levels, which is what an audit is,
so the scoring path must never import it; it in turn never imports
`protected_attributes` (the records arrive as data). tests/test_fairness_audit.py
checks both directions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zlib
from collections.abc import Callable, Iterable
from typing import Any

import numpy as np

from backend.ledger.schema import Competency, Level

# The competencies the pipeline assigns a level to. 8 and 9 are flags only,
# levelled by humans (LED-10), so there is nothing of the AI's to audit there.
AUDITED_COMPETENCIES: tuple[Competency, ...] = (
    Competency.MOTIVATION_UNIVERSITY,
    Competency.MOTIVATION_MAJOR,
    Competency.LEADERSHIP_ABILITIES,
    Competency.TEAMWORK,
    Competency.VALUES,
    Competency.PRIOR_EXPERIENCE,
    Competency.INTELLECT,
)
LEVELS: tuple[Level, ...] = (Level.HIGH, Level.NORMAL, Level.WEAK, Level.NO_EVIDENCE)

REVIEW_THRESHOLD = 0.8
MIN_GROUP_N = 10
MIN_GROUP_SHARE = 0.02
N_BOOTSTRAP = 1000
BOOTSTRAP_SEED = 1003
OUTCOME_LEVEL = "high"

STATE_OK = "ok"
STATE_REVIEW = "review_needed"
STATE_NOT_ENOUGH = "not_enough_data"


def _declared(value: Any) -> str:
    """A self-declared value as a group label; "" when it was not declared."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value).strip().casefold()


def _intersection(attributes: dict) -> str:
    settlement = _declared(attributes.get("settlement_type"))
    language = _declared(attributes.get("application_language"))
    return f"{settlement} × {language}" if settlement and language else ""


# Attribute -> how to read an applicant's group. Order is display order.
DIMENSIONS: dict[str, Callable[[dict], str]] = {
    "settlement_type": lambda a: _declared(a.get("settlement_type")),
    "region": lambda a: _declared(a.get("region")),
    "school_type": lambda a: _declared(a.get("school_type")),
    "application_language": lambda a: _declared(a.get("application_language")),
    "foundation_eligible": lambda a: _declared(a.get("foundation_eligible")),
    "gender": lambda a: _declared(a.get("gender")),
    "settlement_x_language": _intersection,
}


def input_hash(records: Iterable[dict]) -> str:
    """sha256 of the records in a canonical form, independent of their order."""
    canonical = sorted(
        (
            {
                "applicant_ref": r["applicant_ref"],
                "attributes": {k: _declared(v) for k, v in r["attributes"].items()},
                "levels": {k: v for k, v in r["levels"].items() if v is not None},
            }
            for r in records
        ),
        key=lambda r: r["applicant_ref"],
    )
    body = json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _rng(seed: int, *keys: str) -> np.random.Generator:
    return np.random.default_rng([seed, *(zlib.crc32(key.encode("utf-8")) for key in keys)])


def _bootstrap_rates(n: int, hits: int, rng: np.random.Generator, n_bootstrap: int) -> np.ndarray:
    # Resampling n binary outcomes with replacement and counting the hits is
    # exactly a Binomial(n, hits/n) draw, so this is the ordinary nonparametric
    # bootstrap of a proportion, without materialising the resamples.
    return rng.binomial(n, hits / n, size=n_bootstrap) / n


def _audit_cell(
    dimension: str,
    competency: str,
    members: dict[str, list[str]],
    pool: int,
    *,
    seed: int,
    n_bootstrap: int,
) -> dict:
    """One attribute × one competency: every group against the best group."""
    groups = []
    for name in sorted(members):
        levels = members[name]
        n = len(levels)
        counts = {level.value: levels.count(level.value) for level in LEVELS}
        groups.append(
            {
                "group": name,
                "n": n,
                "share_of_pool": n / pool,
                "levels": counts,
                "high_rate": counts[OUTCOME_LEVEL] / n,
                "no_evidence_rate": counts["no_evidence"] / n,
                "enough_data": n >= MIN_GROUP_N and n / pool >= MIN_GROUP_SHARE,
            }
        )

    # The reference is the best-rated group among those large enough to judge,
    # so one lucky group of three cannot set the bar for everyone else. Groups
    # are in name order and max() keeps the first, so ties break by name.
    candidates = [g for g in groups if g["enough_data"] and g["high_rate"] > 0]
    reference = max(candidates, key=lambda g: g["high_rate"], default=None)

    ref_samples = None
    if reference is not None:
        ref_hits = reference["levels"][OUTCOME_LEVEL]
        ref_samples = _bootstrap_rates(
            reference["n"], ref_hits, _rng(seed, dimension, competency, reference["group"]), n_bootstrap
        )

    for g in groups:
        g["is_reference"] = reference is not None and g["group"] == reference["group"]
        g["impact_ratio"] = g["ci_low"] = g["ci_high"] = None
        g["review_reason"] = None
        if reference is not None:
            g["impact_ratio"] = g["high_rate"] / reference["high_rate"]
            if g["is_reference"]:
                g["ci_low"] = g["ci_high"] = 1.0
            else:
                samples = _bootstrap_rates(
                    g["n"], g["levels"][OUTCOME_LEVEL], _rng(seed, dimension, competency, g["group"]), n_bootstrap
                )
                with np.errstate(divide="ignore", invalid="ignore"):
                    ratios = np.where(ref_samples > 0, samples / ref_samples, np.nan)
                if np.isfinite(ratios).any():
                    g["ci_low"] = float(np.nanpercentile(ratios, 2.5))
                    g["ci_high"] = float(np.nanpercentile(ratios, 97.5))

        if not g["enough_data"] or reference is None:
            g["state"] = STATE_NOT_ENOUGH
        elif g["impact_ratio"] < REVIEW_THRESHOLD:
            g["state"], g["review_reason"] = STATE_REVIEW, "below_threshold"
        elif g["ci_low"] is not None and g["ci_low"] < REVIEW_THRESHOLD:
            g["state"], g["review_reason"] = STATE_REVIEW, "interval_crosses_threshold"
        else:
            g["state"] = STATE_OK
        del g["enough_data"]

    return {
        "competency": competency,
        "pool": pool,
        "reference_group": reference["group"] if reference else None,
        "groups": groups,
    }


def run_audit(
    records: list[dict],
    *,
    source: str,
    competencies: Iterable[str] | None = None,
    seed: int = BOOTSTRAP_SEED,
    n_bootstrap: int = N_BOOTSTRAP,
) -> dict:
    """The audit over `records` ({applicant_ref, attributes, levels}).

    Pure: the same records and seed give the same result, byte for byte.
    """
    wanted = list(competencies) if competencies is not None else [c.value for c in AUDITED_COMPETENCIES]
    dimensions = []
    for dimension, group_of in DIMENSIONS.items():
        cells = []
        undeclared = 0
        for competency in wanted:
            members: dict[str, list[str]] = {}
            pool = 0
            undeclared_here = 0
            for record in records:
                level = record["levels"].get(competency)
                if level is None:
                    continue
                pool += 1
                group = group_of(record["attributes"])
                if not group:
                    undeclared_here += 1
                    continue
                members.setdefault(group, []).append(level)
            undeclared = max(undeclared, undeclared_here)
            if pool:
                cells.append(_audit_cell(dimension, competency, members, pool, seed=seed, n_bootstrap=n_bootstrap))
        dimensions.append({"dimension": dimension, "undeclared": undeclared, "competencies": cells})

    return {
        "source": source,
        "applicants": len(records),
        "applicants_with_levels": sum(1 for r in records if any(v is not None for v in r["levels"].values())),
        "input_hash": input_hash(records),
        "method": {
            "outcome": f"share of the group rated '{OUTCOME_LEVEL}' on the competency",
            "reference": "the group with the highest rate among groups with enough data",
            "interval": f"{n_bootstrap}-sample percentile bootstrap, 95%",
            "bootstrap_seed": seed,
            "n_bootstrap": n_bootstrap,
            "review_threshold": REVIEW_THRESHOLD,
            "min_group_n": MIN_GROUP_N,
            "min_group_share": MIN_GROUP_SHARE,
        },
        "competencies": wanted,
        "dimensions": dimensions,
    }


# ── CLI: the same numbers the API returns ─────────────────────────


def _fmt(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _print_report(report: dict, out) -> None:
    method = report["method"]
    print(f"source: {report['source']}   applicants: {report['applicants']}", file=out)
    print(f"input sha256: {report['input_hash']}", file=out)
    print(
        f"outcome: {method['outcome']}; {method['interval']} (seed {method['bootstrap_seed']}); "
        f"review below {method['review_threshold']}",
        file=out,
    )
    for dimension in report["dimensions"]:
        for cell in dimension["competencies"]:
            print(f"\n{dimension['dimension']} · {cell['competency']}  (pool {cell['pool']}, "
                  f"undeclared {dimension['undeclared']})", file=out)
            print(f"  {'group':<20}{'n':>5}{'high':>7}{'no_ev':>7}{'ratio':>7}  {'95% CI':<13} state", file=out)
            for g in cell["groups"]:
                ci = f"[{_fmt(g['ci_low'])}, {_fmt(g['ci_high'])}]" if g["ci_low"] is not None else "—"
                marker = " (ref)" if g["is_reference"] else ""
                print(
                    f"  {g['group']:<20}{g['n']:>5}{g['high_rate']:>7.2f}{g['no_evidence_rate']:>7.2f}"
                    f"{_fmt(g['impact_ratio']):>7}  {ci:<13} {g['state']}{marker}",
                    file=out,
                )


def main(argv: list[str] | None = None) -> int:
    from backend.scoring import synthetic_cohort

    parser = argparse.ArgumentParser(prog="python -m backend.scoring.fairness_audit", description=__doc__.splitlines()[0])
    parser.add_argument("--source", choices=["synthetic", "db"], default="synthetic")
    parser.add_argument("--cohort-seed", type=int, default=synthetic_cohort.DEFAULT_SEED)
    parser.add_argument("--size", type=int, default=synthetic_cohort.DEFAULT_SIZE)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED, help="bootstrap seed")
    parser.add_argument("--competency", action="append", help="repeatable; default: all audited")
    parser.add_argument("--json", action="store_true", help="print the API response body")
    args = parser.parse_args(argv)

    if args.source == "synthetic":
        records = synthetic_cohort.generate(n=args.size, seed=args.cohort_seed)
    else:
        from backend.db.fairness import load_audit_records

        records = load_audit_records()
    report = run_audit(records, source=args.source, competencies=args.competency, seed=args.seed)

    out = sys.stdout
    if hasattr(out, "reconfigure"):
        out.reconfigure(encoding="utf-8")
    if args.json:
        json.dump(report, out, ensure_ascii=False, indent=2)
        print(file=out)
    else:
        _print_report(report, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
