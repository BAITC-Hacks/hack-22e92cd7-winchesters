"""FAIR-09 historical ingest and the preregistered agreement report."""

from __future__ import annotations

import hashlib
import json
import zlib
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sklearn.metrics import cohen_kappa_score

from backend.scoring.fairness_audit import BOOTSTRAP_SEED, N_BOOTSTRAP, REVIEW_THRESHOLD

REGISTRATION_ID = "FAIR-08-2026-09-25"
SPLIT_SEED = 8009
LEVELS = ("weak", "normal", "high")
LEVEL_NUMBER = {level: index for index, level in enumerate(LEVELS)}
SUBGROUP_FIELDS = ("region", "settlement_type", "school_type", "application_language", "script", "foundation_eligible", "gender")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    """The byte representation used for reproducibility comparisons."""
    return _canonical(value).encode("utf-8")


def data_hash(records: list[dict[str, Any]]) -> str:
    body = canonical_bytes(sorted(records, key=lambda item: str(item["applicant_id"])))
    return hashlib.sha256(body).hexdigest()


def content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize either one row per rating or one applicant with ratings."""
    rows: list[dict[str, Any]] = []
    for record in records:
        applicant_id = str(record.get("applicant_id", record.get("applicant_ref", "")))
        if not applicant_id:
            raise ValueError("applicant_id is required")
        ratings = record.get("ratings") or [record]
        for rating in ratings:
            committee = rating.get("committee_level", rating.get("human_level"))
            model = rating.get("model_level", rating.get("scorer_level"))
            if not rating.get("competency") or (committee is not None and committee not in LEVELS) or (model is not None and model not in LEVELS):
                raise ValueError("each rating needs competency and valid model/committee levels")
            rows.append({
                "applicant_id": applicant_id,
                "competency": str(rating["competency"]),
                "model_level": model,
                "committee_level": committee,
                "human_levels": rating.get("human_levels", record.get("human_levels", [])),
                "admitted": bool(rating.get("admitted", record.get("admitted", False))),
                "attributes": dict(rating.get("attributes", record.get("attributes", {}))),
            })
    if not rows:
        raise ValueError("at least one historical rating is required")
    return rows


def split_rows(rows: list[dict[str, Any]], seed: int = SPLIT_SEED) -> tuple[list[dict], list[dict]]:
    applicants = sorted({row["applicant_id"] for row in rows})
    rng = np.random.default_rng(seed)
    profiles: dict[str, tuple] = {}
    for applicant_id in applicants:
        applicant_rows = [row for row in rows if row["applicant_id"] == applicant_id]
        attributes = applicant_rows[0]["attributes"]
        profiles[applicant_id] = (
            attributes.get("application_language", "undeclared"),
            attributes.get("region", "undeclared"),
            attributes.get("settlement_type", "undeclared"),
            tuple(sorted(row["committee_level"] or "missing" for row in applicant_rows)),
            tuple(sorted(row["competency"] for row in applicant_rows)),
        )
    strata: dict[tuple, list[str]] = defaultdict(list)
    for applicant_id in applicants:
        strata[profiles[applicant_id]].append(applicant_id)
    train_ids: set[str] = set()
    fractional: list[tuple[float, str]] = []
    for profile, members in sorted(strata.items(), key=lambda item: str(item[0])):
        rng.shuffle(members)
        exact = len(members) * 0.70
        quota = int(exact)
        train_ids.update(members[:quota])
        fractional.extend((exact - quota, applicant_id) for applicant_id in members[quota:])
    target = int(round(len(applicants) * 0.70))
    for _, applicant_id in sorted(fractional, reverse=True)[: max(0, target - len(train_ids))]:
        train_ids.add(applicant_id)
    return ([row for row in rows if row["applicant_id"] in train_ids], [row for row in rows if row["applicant_id"] not in train_ids])


def _icc(values: list[tuple[int, int]]) -> float | None:
    if len(values) < 2:
        return None
    matrix = np.asarray(values, dtype=float)
    if np.all(matrix == matrix[0, 0]):
        return 1.0 if np.all(matrix[:, 0] == matrix[:, 1]) else 0.0
    n, k = matrix.shape
    row_means, col_means, grand = matrix.mean(axis=1), matrix.mean(axis=0), matrix.mean()
    between = k * np.sum((row_means - grand) ** 2) / (n - 1)
    error = np.sum((matrix - row_means[:, None] - col_means + grand) ** 2) / ((n - 1) * (k - 1))
    denominator = between + (k - 1) * error
    return float((between - error) / denominator) if denominator else 1.0


def _agreement(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for competency in sorted({row["competency"] for row in rows}):
        selected = [row for row in rows if row["competency"] == competency and row["committee_level"] in LEVELS and row["model_level"] in LEVELS]
        committee = [LEVEL_NUMBER[row["committee_level"]] for row in selected]
        model = [LEVEL_NUMBER[row["model_level"]] for row in selected]
        human_pairs = [(LEVEL_NUMBER[row["human_levels"][0]], LEVEL_NUMBER[row["human_levels"][1]]) for row in selected if len(row["human_levels"]) >= 2 and row["human_levels"][0] in LEVELS and row["human_levels"][1] in LEVELS]
        result.append({
            "competency": competency,
            "n": len(selected),
            "model_level_counts": dict(Counter(row["model_level"] for row in selected)),
            "committee_level_counts": dict(Counter(row["committee_level"] for row in selected)),
            "qwk": (float(cohen_kappa_score(model, committee, weights="quadratic")) if len(selected) and (len(set(committee)) > 1 or len(set(model)) > 1) else (1.0 if selected else None)),
            "icc": _icc(list(zip(model, committee))),
            "human_human_qwk": float(cohen_kappa_score(*zip(*human_pairs), weights="quadratic")) if human_pairs and (len({p[0] for p in human_pairs}) > 1 or len({p[1] for p in human_pairs}) > 1) else (1.0 if human_pairs else None),
            "human_human_icc": _icc(human_pairs),
            "calibration": {model_level: {committee_level: sum(1 for row in selected if row["model_level"] == model_level and row["committee_level"] == committee_level) for committee_level in LEVELS} for model_level in LEVELS},
        })
    return result


def _impact(rows: list[dict[str, Any]], seed: int = BOOTSTRAP_SEED) -> list[dict[str, Any]]:
    output = []
    for field in SUBGROUP_FIELDS:
        members: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if row["model_level"] not in LEVELS:
                continue
            value = row["attributes"].get(field)
            members[str(value).casefold() if value not in (None, "") else "undeclared"].append(row)
        pool = len(rows)
        eligible = {name: items for name, items in members.items() if len(items) >= 10 and len(items) / pool >= 0.02}
        rates = {name: sum(row["model_level"] == "high" for row in items) / len(items) for name, items in eligible.items()}
        reference = max(rates, key=rates.get) if rates else None
        field_result = []
        for name in sorted(members):
            items = members[name]
            rate = sum(row["model_level"] == "high" for row in items) / len(items)
            ratio = rate / rates[reference] if reference and rates[reference] else None
            ci = None
            if ratio is not None and reference and name != reference:
                stable_key = zlib.crc32(f"{field}:{name}".encode("utf-8"))
                rng = np.random.default_rng([seed, stable_key])
                ref = np.asarray([row["model_level"] == "high" for row in eligible[reference]], dtype=float)
                sample = np.asarray([row["model_level"] == "high" for row in items], dtype=float)
                ratios = [rng.choice(sample, len(sample)).mean() / max(rng.choice(ref, len(ref)).mean(), 1e-12) for _ in range(N_BOOTSTRAP)]
                ci = [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]
            elif name == reference:
                ci = [1.0, 1.0]
            enough = name in eligible
            state = "not_enough_data" if not enough else ("review_needed" if ratio is not None and (ratio < REVIEW_THRESHOLD or (ci and ci[0] < REVIEW_THRESHOLD)) else "ok")
            field_result.append({"group": name, "n": len(items), "share_of_pool": len(items) / pool, "high_rate": rate, "impact_ratio": ratio, "ci_low": ci[0] if ci else None, "ci_high": ci[1] if ci else None, "reference": name == reference, "state": state})
        output.append({"dimension": field, "reference_group": reference, "groups": field_result})
    return output


def _report_hash(report: dict[str, Any]) -> str:
    comparable = json.loads(_canonical(report))
    comparable.get("reproducibility", {}).pop("report_hash", None)
    return hashlib.sha256(canonical_bytes(comparable)).hexdigest()


def build_report(
    records: list[dict[str, Any]],
    *,
    prompt_id: str = "historical-prompt-frozen",
    model_id: str = "historical-model-frozen",
    rubric_id: str = "historical-rubric-frozen",
    split_seed: int = SPLIT_SEED,
    timestamp_utc: str | None = None,
) -> dict[str, Any]:
    rows = _rows(records)
    train, holdout = split_rows(rows, split_seed)
    holdout_low = sum(row["admitted"] and row["model_level"] == "weak" for row in holdout)
    normalized_data_hash = data_hash(rows)
    report = {
        "manifest": {"registration_id": REGISTRATION_ID, "report_mode": "historical", "prompt_id": prompt_id, "model_id": model_id, "rubric_id": rubric_id, "fixture_or_data_hash": normalized_data_hash, "prompt_hash": content_hash(prompt_id), "model_hash": content_hash(model_id), "rubric_hash": content_hash(rubric_id), "evaluation_data_hash": normalized_data_hash, "seed": {"split": split_seed, "bootstrap": BOOTSTRAP_SEED, "n_bootstrap": N_BOOTSTRAP}, "timestamp_utc": timestamp_utc or datetime.now(UTC).isoformat()},
        "provenance": {"requested_mode": "historical", "effective_mode": "historical", "fallback_used": False, "fallback_reason": None, "live_result": None, "cached_result": None},
        "production_invariance": {"score_path_changed": False, "ranking_changed": False, "recommendation_changed": False},
        "split": {"train_applicants": len({row["applicant_id"] for row in train}), "holdout_applicants": len({row["applicant_id"] for row in holdout}), "train_rows": len(train), "holdout_rows": len(holdout), "holdout_sealed": True, "tuning_source": "train_only"},
        "missing_labels": sum(row["committee_level"] not in LEVELS for row in rows),
        "failed_model_runs": sum(row["model_level"] not in LEVELS for row in rows),
        "train": {"agreement": _agreement(train), "impact_ratios": _impact(train)},
        "holdout": {"agreement": _agreement(holdout), "impact_ratios": _impact(holdout), "screening_safety": {"lowest_band": "weak", "admitted_in_lowest_band": holdout_low, "safe": holdout_low == 0, "status": "usable" if holdout_low == 0 else "unusable"}},
    }
    report["reproducibility"] = {
        "ratings": rows,
        "rating_count": len(rows),
        "frozen_hashes": {
            "prompt": content_hash(prompt_id),
            "rubric": content_hash(rubric_id),
            "data": normalized_data_hash,
        },
        "report_hash": _report_hash(report),
    }
    return report


def replay_report(report: dict[str, Any]) -> dict[str, Any]:
    """Rebuild a report solely from its saved ratings and frozen manifest."""
    bundle = report.get("reproducibility") or {}
    manifest = report.get("manifest") or {}
    ratings = bundle.get("ratings")
    if not isinstance(ratings, list) or not ratings:
        raise ValueError("Report has no saved ratings for replay")
    required = ("prompt_id", "model_id", "rubric_id", "timestamp_utc")
    if any(not manifest.get(key) for key in required):
        raise ValueError("Report manifest is missing frozen replay fields")
    return build_report(
        ratings,
        prompt_id=manifest["prompt_id"],
        model_id=manifest["model_id"],
        rubric_id=manifest["rubric_id"],
        split_seed=manifest["seed"]["split"],
        timestamp_utc=manifest["timestamp_utc"],
    )


def compare_reports(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Compare canonical report bytes and explain the first mismatches."""
    expected_bytes = canonical_bytes(expected)
    actual_bytes = canonical_bytes(actual)
    mismatches: list[dict[str, Any]] = []

    def walk(left: Any, right: Any, path: str = "$") -> None:
        if len(mismatches) >= 50:
            return
        if type(left) is not type(right):
            mismatches.append({"path": path, "expected": left, "actual": right})
        elif isinstance(left, dict):
            for key in sorted(set(left) | set(right)):
                if key not in left or key not in right:
                    mismatches.append({"path": f"{path}.{key}", "expected": left.get(key), "actual": right.get(key)})
                else:
                    walk(left[key], right[key], f"{path}.{key}")
        elif isinstance(left, list):
            if len(left) != len(right):
                mismatches.append({"path": path, "expected": f"list[{len(left)}]", "actual": f"list[{len(right)}]"})
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                walk(left_item, right_item, f"{path}[{index}]")
        elif left != right:
            mismatches.append({"path": path, "expected": left, "actual": right})

    walk(expected, actual)
    return {
        "byte_identical": expected_bytes == actual_bytes,
        "expected_hash": hashlib.sha256(expected_bytes).hexdigest(),
        "actual_hash": hashlib.sha256(actual_bytes).hexdigest(),
        "mismatches": mismatches,
    }


def build_model_card(report: dict[str, Any]) -> dict[str, Any]:
    """Project the historical report into the committee-facing model card."""
    manifest = report["manifest"]
    holdout = report["holdout"]
    agreement = [
        {
            **metric,
            "human_human_ceiling": {"qwk": metric["human_human_qwk"], "icc": metric["human_human_icc"]},
        }
        for metric in holdout["agreement"]
    ]
    return {
        "title": "Historical scorer model card",
        "status": "historical_holdout",
        "intended_use": "Committee-only evaluation of an AI-drafted competency signal before human review. The committee remains the decision-maker.",
        "out_of_scope_use": [
            "Automated admission, rejection, ranking, or recommendation decisions",
            "Applicant or interviewer self-service access",
            "Inferring protected attributes or treating historical committee labels as ground truth",
        ],
        "provenance": {
            "registration_id": manifest["registration_id"],
            "report_mode": manifest["report_mode"],
            "model_hash": manifest["model_hash"],
            "prompt_hash": manifest["prompt_hash"],
            "rubric_hash": manifest["rubric_hash"],
            "evaluation_data_hash": manifest["evaluation_data_hash"],
            "split": report["split"],
            "execution": report["provenance"],
        },
        "metrics": {
            "agreement": agreement,
            "impact_ratios": holdout["impact_ratios"],
            "screening_safety": holdout["screening_safety"],
        },
        "abstention": {
            "policy": "No evidence is a first-class outcome: failed or missing model labels are excluded from agreement and fairness rates, never converted to zero.",
            "failed_model_runs": report["failed_model_runs"],
            "no_evidence_state": "not_enough_data" if report["failed_model_runs"] else "observed",
            "production_effect": "Abstention does not change production scores, recommendations, or ranking.",
        },
        "screening_safety": holdout["screening_safety"],
        "production_invariance": report["production_invariance"],
        "limitations": [
            "Historical committee labels reflect selection and interviewer severity; agreement is not ground truth.",
            "Small groups below n=10 or 2% of the pool are descriptive and marked not_enough_data.",
            "Confidence intervals are bootstrap diagnostics and do not establish causality or absence of discrimination.",
            "The holdout is sealed and no prompt, rubric, threshold, subgroup, or model tuning is permitted on it.",
        ],
        "impact_assessment": {
            "legal_basis": "EU AI Act Article 27",
            "scope": "Before deployment or substantial modification, the deployer documents intended purpose, affected groups, foreseeable risks, mitigations, human oversight, and monitoring.",
            "affected_people": "Applicants whose artifacts are reviewed by the admissions committee, including declared audit subgroups.",
            "risks": ["automation bias", "unequal error or abstention rates", "historical-label and selection bias", "privacy and purpose limitation"],
            "mitigations": ["committee/admin-only access", "human review and append-only overrides", "no protected attributes in scoring", "pre-registered metrics with confidence intervals", "abstention and small-n states shown explicitly"],
            "human_oversight": "Committee members can review evidence, disagree, and override; the model cannot publish a decision.",
            "monitoring": "Re-run agreement, calibration, abstention, screening-safety, and impact-ratio checks for each frozen model/prompt/rubric/data version.",
            "residual_risk": "A passing metric is not proof of fairness, safety, or legal compliance; governance review remains required.",
        },
    }


def build_funder_memo(report: dict[str, Any]) -> dict[str, Any]:
    """Project a frozen held-out report into the funder-facing memo contract."""
    manifest = report["manifest"]
    ratings = report.get("reproducibility", {}).get("ratings")
    if not isinstance(ratings, list) or not ratings:
        raise ValueError("Report has no saved ratings for the funder memo")
    _, holdout = split_rows(ratings, manifest["seed"]["split"])
    by_competency = []
    for competency in sorted({row["competency"] for row in holdout}):
        rows = [row for row in holdout if row["competency"] == competency]
        failed = sum(row["model_level"] not in LEVELS for row in rows)
        by_competency.append({
            "competency": competency,
            "ratings": len(rows),
            "abstentions": failed,
            "abstention_rate": failed / len(rows) if rows else 0.0,
        })
    abstentions = sum(row["model_level"] not in LEVELS for row in holdout)
    return {
        "title": "Funder cohort memo",
        "audience": "inDrive",
        "report_mode": manifest["report_mode"],
        "holdout": report["holdout"],
        "impact_ratios": report["holdout"]["impact_ratios"],
        "calibration": report["holdout"]["agreement"],
        "abstention": {
            "ratings": len(holdout),
            "abstentions": abstentions,
            "abstention_rate": abstentions / len(holdout) if holdout else 0.0,
            "by_competency": by_competency,
            "definition": "Failed or missing model labels are abstentions, not weak ratings.",
        },
        "provenance": {
            "registration_id": manifest["registration_id"],
            "report_hash": report["reproducibility"].get("report_hash"),
            "evaluation_data_hash": manifest["evaluation_data_hash"],
            "prompt_hash": manifest["prompt_hash"],
            "model_hash": manifest["model_hash"],
            "rubric_hash": manifest["rubric_hash"],
            "split_seed": manifest["seed"]["split"],
            "bootstrap_seed": manifest["seed"]["bootstrap"],
            "holdout_sealed": report["split"]["holdout_sealed"],
            "tuning_source": report["split"]["tuning_source"],
        },
        "production_invariance": report["production_invariance"],
    }