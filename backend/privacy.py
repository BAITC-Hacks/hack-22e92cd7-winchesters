"""PII anonymization utilities.

Strips or masks personally identifiable information for processing
while preserving data needed for scoring.
"""

from __future__ import annotations

import re

from backend.models import Candidate


def anonymize_candidate(candidate: Candidate) -> Candidate:
    """Return a copy of the candidate with PII masked for AI processing."""
    data = candidate.model_dump()
    data["name"] = f"Candidate {candidate.id}"
    # Mask any email-like patterns in text fields
    for field in ("interview_transcript", "recommendation_summary", "written_presentation", "video_transcript"):
        if data[field]:
            data[field] = _mask_emails(data[field])
            data[field] = _mask_phone_numbers(data[field])
    if data["essay"]["text"]:
        data["essay"]["text"] = _mask_emails(data["essay"]["text"])
        data["essay"]["text"] = _mask_phone_numbers(data["essay"]["text"])
    return Candidate(**data)


def _mask_emails(text: str) -> str:
    return re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL REDACTED]', text)


def _mask_phone_numbers(text: str) -> str:
    return re.sub(r'\+?\d[\d\s-]{8,}\d', '[PHONE REDACTED]', text)
