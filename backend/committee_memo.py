"""Assemble the committee decision memo from the evidence ledger."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, col, select

from backend.db.engine import get_engine
from backend.db.candidates import applicant_id_for
from backend.db.overrides import list_overrides
from backend.db.tables import AuditLogEntry
from backend.ledger.rubric import RUBRIC
from backend.ledger.schema import CandidateLedger, Level


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _probe_result(candidate_id: str) -> dict[str, Any]:
    with Session(get_engine()) as session:
        audit = session.exec(
            select(AuditLogEntry)
            .where(col(AuditLogEntry.action) == "fairness_probe_run", col(AuditLogEntry.object_id) == candidate_id)
            .order_by(col(AuditLogEntry.created_at).desc())
        ).first()
    if audit is None:
        return {"status": "not_run", "candidate_id": candidate_id}
    return {"status": "recorded", "candidate_id": candidate_id, **(audit.after or {})}


def _anchors(competency: str) -> dict[str, list[str]]:
    rubric = RUBRIC[next(item for item in RUBRIC if item.value == competency)]
    return {level.value: [indicator.anchor(level) for indicator in rubric.indicators] for level in (Level.WEAK, Level.NORMAL, Level.HIGH)}


def build_decision_memo(candidate_id: str, ledger: CandidateLedger) -> dict[str, Any]:
    """Return a JSON-safe memo; overrides affect only the displayed level."""
    overrides = list_overrides(applicant_id_for(candidate_id) or candidate_id)
    latest = {item["competency"]: item for item in overrides}
    competencies = []
    verified_quotes = []
    for rating in ledger.competencies:
        competency = rating.competency.value
        override = latest.get(competency)
        effective = override["to_level"] if override else (rating.level.value if rating.level else None)
        rubric = RUBRIC[rating.competency]
        indicators = []
        for indicator in rating.indicators:
            evidence = [item.model_dump(mode="json") for item in indicator.evidence if item.verified]
            verified_quotes.extend({"competency": competency, "indicator_id": indicator.indicator_id, **item} for item in evidence)
            rubric_indicator = next(item for item in rubric.indicators if item.id == indicator.indicator_id)
            indicators.append({
                "indicator_id": indicator.indicator_id,
                "observed_level": indicator.observed_level.value,
                "note": indicator.note,
                "capped_reason": indicator.capped_reason,
                "bars_anchors": {"weak": rubric_indicator.weak, "normal": rubric_indicator.normal, "high": rubric_indicator.high},
                "verified_quotes": evidence,
            })
        competencies.append({
            "competency": competency,
            "label": rubric.label,
            "ai_level": rating.level.value if rating.level else None,
            "effective_level": effective,
            "reserved_for_humans": rating.reserved_for_humans,
            "rule_applied": rating.rule_applied,
            "indicators": indicators,
            "probe_question": rating.probe_question,
            "flags": [flag.model_dump(mode="json") for flag in rating.flags],
            "bars_anchors": _anchors(competency),
            "override": override,
        })

    model = ledger.model_judge or "unknown"
    prompt = ledger.prompt_version or "unknown"
    rubric = ledger.rubric_version or "unknown"
    return {
        "candidate_id": candidate_id,
        "title": "Committee decision memo",
        "competencies": competencies,
        "verified_quotes": verified_quotes,
        "test_bands": [{"level": level.value, "label": level.value.replace("_", " ")} for level in (Level.WEAK, Level.NORMAL, Level.HIGH)],
        "overrides": overrides,
        "probe_result": _probe_result(candidate_id),
        "provenance": {"schema_version": ledger.schema_version, "model": model, "prompt": prompt, "rubric": rubric, "model_hash": _hash(model), "prompt_hash": _hash(prompt), "rubric_hash": _hash(rubric)},
        "counts": {"ai_drafted": sum(item["ai_level"] is not None for item in competencies), "items": len(competencies), "committee_changed": len(overrides)},
        "signatures": [{"role": "Committee chair", "name": "", "signed_at": ""}, {"role": "Committee member", "name": "", "signed_at": ""}],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def render_pdf(memo: dict[str, Any]) -> bytes:
    """Render a compact dependency-free printable PDF summary."""
    lines = [memo["title"], f"Candidate: {memo['candidate_id']}", ""]
    for item in memo["competencies"]:
        lines.append(f"{item['label']}: {item['effective_level'] or 'human review'}")
        for indicator in item["indicators"]:
            for quote in indicator["verified_quotes"]:
                lines.append(f"  [{indicator['indicator_id']}] {quote['quote']}")
        lines.append(f"  Probe: {item['probe_question']}")
    lines += ["", f"AI drafted {memo['counts']['ai_drafted']} of {memo['counts']['items']} items; committee changed {memo['counts']['committee_changed']}.", "", "Committee chair signature: ____________________", "Committee member signature: ____________________"]
    text_lines = []
    for line in lines:
        safe = line.encode("latin-1", errors="replace").decode("latin-1")
        escaped = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_lines.append(f"({escaped}) Tj T*\n")
    stream = "BT /F1 9 Tf 50 780 Td 12 TL\n" + "".join(text_lines) + "ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1"))
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    pdf.extend("".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:]).encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode("ascii"))
    return bytes(pdf)