"""Tests for end-to-end Search, AI intent resolution, ranking, and search history."""

import pytest
from backend.app.schemas.file import FileRecord
from backend.app.services.ranking_service import ranking_service


def test_ranking_service_scoring():
    candidates = [
        FileRecord(
            id="f1",
            provider="local",
            provider_file_id="Appointment_Letter_2026.txt",
            name="Appointment_Letter_2026.txt",
            path="/Appointment_Letter_2026.txt",
        ),
        FileRecord(
            id="f2",
            provider="local",
            provider_file_id="random_notes.txt",
            name="random_notes.txt",
            path="/random_notes.txt",
        ),
    ]

    ranked = ranking_service.rank_results(
        query="offer letter",
        candidates=candidates,
        semantic_scores={"f1": 0.95, "f2": 0.10},
    )

    assert len(ranked) == 2
    # f1 with high semantic similarity should be ranked first
    assert ranked[0].id == "f1"
    assert ranked[0].score is not None
    assert ranked[0].score > ranked[1].score
    assert "semantic_score" in ranked[0].score_breakdown
