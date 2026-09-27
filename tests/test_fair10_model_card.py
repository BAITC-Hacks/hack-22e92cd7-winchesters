from __future__ import annotations

from backend.evals.historical import build_model_card, build_report


def _records(count: int = 20) -> list[dict]:
    return [
        {
            "applicant_id": f"fair10-{index}",
            "admitted": False,
            "attributes": {"region": "north" if index % 2 else "south"},
            "ratings": [{"competency": "teamwork", "model_level": "high", "committee_level": "high", "human_levels": ["high", "high"]}],
        }
        for index in range(count)
    ]


def test_model_card_is_populated_from_fair09_report():
    card = build_model_card(build_report(_records()))

    assert card["provenance"]["evaluation_data_hash"]
    assert card["provenance"]["model_hash"]
    assert card["metrics"]["agreement"][0]["human_human_ceiling"]["qwk"] == 1.0
    assert card["metrics"]["screening_safety"]["status"] == "usable"
    assert "No evidence" in card["abstention"]["policy"]
    assert card["impact_assessment"]["legal_basis"] == "EU AI Act Article 27"


def test_model_card_exposes_abstention_without_zeroing_scores():
    records = _records()
    records[0]["ratings"][0]["model_level"] = None
    card = build_model_card(build_report(records))

    assert card["abstention"]["failed_model_runs"] == 1
    assert card["abstention"]["no_evidence_state"] == "not_enough_data"