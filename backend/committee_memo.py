"""Assemble the committee decision memo from the evidence ledger."""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
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


def build_decision_memo(candidate_id: str, ledger: CandidateLedger, *, locale: str = "ru") -> dict[str, Any]:
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
    labels = {
        "ru": {"title": "Решение комитета", "candidate": "Кандидат", "human_review": "нужна проверка человеком"},
        "kk": {"title": "Комитет шешімі", "candidate": "Кандидат", "human_review": "адам тексеруі қажет"},
    }.get(locale, {"title": "Committee decision memo", "candidate": "Candidate", "human_review": "human review"})
    return {
        "candidate_id": candidate_id,
        "title": labels["title"],
        "locale": locale,
        "candidate_label": labels["candidate"],
        "human_review_label": labels["human_review"],
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


def render_pdf(memo: dict[str, Any], *, locale: str | None = None) -> bytes:
    """Render an A4, Unicode, print-ready PDF using a system TTF font."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas

    font_paths = [
        os.getenv("DECISION_MEMO_FONT", ""),
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((path for path in font_paths if path and Path(path).is_file()), None)
    if font_path is None:
        raise RuntimeError("A Unicode TTF font is required; set DECISION_MEMO_FONT to Arial or DejaVuSans")
    pdfmetrics.registerFont(TTFont("DecisionMemoUnicode", font_path))
    active_locale = locale or memo.get("locale", "ru")
    labels = {
        "ru": {"candidate": "Кандидат", "probe": "Вопрос", "summary": "AI подготовил", "changed": "пунктов изменено комитетом", "chair": "Председатель комитета", "member": "Член комитета"},
        "kk": {"candidate": "Кандидат", "probe": "Сұрақ", "summary": "AI дайындағаны", "changed": "тармақты комитет өзгертті", "chair": "Комитет төрағасы", "member": "Комитет мүшесі"},
    }.get(active_locale, {"candidate": "Candidate", "probe": "Probe", "summary": "AI drafted", "changed": "committee changes", "chair": "Committee chair", "member": "Committee member"})
    lines = [memo["title"], f"{labels['candidate']}: {memo['candidate_id']}", ""]
    for item in memo["competencies"]:
        lines.append(f"{item['label']}: {item['effective_level'] or 'human review'}")
        for indicator in item["indicators"]:
            for quote in indicator["verified_quotes"]:
                lines.append(f"  [{indicator['indicator_id']}] {quote['quote']}")
        lines.append(f"  {labels['probe']}: {item['probe_question']}")
    lines += ["", f"{labels['summary']} {memo['counts']['ai_drafted']} / {memo['counts']['items']}; {memo['counts']['committee_changed']} {labels['changed']}.", "", f"{labels['chair']}: ____________________", f"{labels['member']}: ____________________"]
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=A4)
    canvas.setTitle(memo["title"])
    canvas.setFont("DecisionMemoUnicode", 9)
    width, height = A4
    y = height - 48
    for line in lines:
        if y < 48:
            canvas.showPage()
            canvas.setFont("DecisionMemoUnicode", 9)
            y = height - 48
        canvas.drawString(42, y, line[:160])
        y -= 14
    canvas.save()
    return output.getvalue()