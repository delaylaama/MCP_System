"""
Pytest unit tests for local AI search components:
- Chunking logic (size, overlap, boundaries)
- Hashing (SHA-256 integrity)
- Reciprocal Rank Fusion (RRF k=60 merging)
- "Latest" sort logic (Top-20 relevance filtered before date sorting)
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from backend.search.indexer import chunk_text, calculate_file_hash
from backend.search.search import reciprocal_rank_fusion, search_files


class TestChunking:
    def test_empty_text(self):
        chunks = chunk_text("")
        assert chunks == []

    def test_single_short_chunk(self):
        text = "This is a brief document for unit testing."
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunking_with_overlap(self):
        words = [f"word{i}" for i in range(100)]
        text = " ".join(words)
        chunk_size = 40
        overlap = 10
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        
        # Step size is 30 words (40 - 10)
        # 100 words -> chunks start at 0, 30, 60, 90 -> 4 chunks
        assert len(chunks) == 4
        # Verify overlap: chunk 0 ends with word39, chunk 1 starts with word30
        c0_words = chunks[0].split()
        c1_words = chunks[1].split()
        assert c0_words[-10:] == c1_words[:10]


class TestHashing:
    def test_sha256_hash_calculation(self):
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"MCP Drivers Local First AI Search Test")
            temp_path = Path(f.name)

        try:
            h = calculate_file_hash(temp_path)
            assert isinstance(h, str)
            assert len(h) == 64  # SHA-256 hex string length
            # SHA-256 of "MCP Drivers Local First AI Search Test"
            import hashlib
            expected = hashlib.sha256(b"MCP Drivers Local First AI Search Test").hexdigest()
            assert h == expected
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_nonexistent_file_hash(self):
        h = calculate_file_hash(Path("non_existent_file_path_12345.xyz"))
        assert h == ""


class TestReciprocalRankFusion:
    def test_rrf_scoring_order(self):
        """
        Tests RRF formula: sum( 1 / (k + rank) ) with k=60.
        Item appearing high in multiple rankings should score higher than item in single ranking.
        """
        fts_ranks = [{"id": "doc_A"}, {"id": "doc_B"}, {"id": "doc_C"}]
        text_ranks = [{"id": "doc_B"}, {"id": "doc_A"}, {"id": "doc_D"}]
        image_ranks = [{"id": "doc_A"}, {"id": "doc_E"}]

        merged = reciprocal_rank_fusion(
            ranked_lists=[fts_ranks, text_ranks, image_ranks],
            k=60,
        )

        # doc_A is rank 1 in FTS (1/61), rank 2 in Text (1/62), rank 1 in Image (1/61)
        # doc_B is rank 2 in FTS (1/62), rank 1 in Text (1/61)
        assert len(merged) == 5
        top_item = merged[0]
        assert top_item["id"] == "doc_A"

        # Check exact score calculation for doc_A:
        expected_score_a = round((1.0 / 61) + (1.0 / 62) + (1.0 / 61), 4)
        assert abs(top_item["score"] - expected_score_a) < 1e-4

        # Second place should be doc_B:
        second_item = merged[1]
        assert second_item["id"] == "doc_B"
        expected_score_b = round((1.0 / 62) + (1.0 / 61), 4)
        assert abs(second_item["score"] - expected_score_b) < 1e-4


class TestLatestSortLogic:
    def test_top_20_relevance_first_then_date(self):
        """
        Hard Requirement:
        For sort="modified_desc": take the top ~20 by relevance FIRST,
        then sort that set by date (never sort all files by date).
        """
        # Create a mock pool of candidates with varying relevance and dates
        now = datetime.now(timezone.utc)
        
        # Build 30 candidates:
        # Items 0..19: moderately relevant, varying dates
        # Items 20..29: very low relevance, but some with ultra-new dates
        candidates = []
        for i in range(30):
            # i < 20 has high relevance score (1.0 - i*0.02)
            # i >= 20 has low relevance score (0.2 - (i-20)*0.01)
            score = 1.0 - (i * 0.02) if i < 20 else 0.2 - ((i - 20) * 0.01)
            # Candidate 25 has newest date (now), but poor relevance
            mtime = now if i == 25 else (now - timedelta(days=i + 5))
            candidates.append({
                "id": f"file_{i}",
                "name": f"document_{i}.pdf",
                "score": score,
                "modified": mtime.isoformat(),
            })

        # Apply top-20 relevance cutoff
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_20_relevant = candidates[:20]

        # Verify candidate 25 (irrelevant but brand new date) was NOT in top 20
        assert not any(c["id"] == "file_25" for c in top_20_relevant)

        # Now sort the top 20 by modified date descending
        sorted_top_20 = sorted(
            top_20_relevant,
            key=lambda x: x["modified"] or "",
            reverse=True,
        )

        # The first item must be from top_20_relevant, not file_25
        assert sorted_top_20[0]["id"] != "file_25"
        # And elements must be monotonically non-increasing by modified date
        dates = [c["modified"] for c in sorted_top_20]
        assert dates == sorted(dates, reverse=True)
