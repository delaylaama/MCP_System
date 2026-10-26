import pytest
from backend.app.services.model_comparison_service import model_comparison_service
from backend.app.schemas.file import FileRecord
from datetime import datetime


@pytest.mark.asyncio
async def test_model_comparison_benchmark():
    candidates = [
        FileRecord(
            id="f1",
            provider="local",
            provider_file_id="loc_1",
            name="June_Invoice_Cloud_2026.txt",
            path="/local/June_Invoice_Cloud_2026.txt",
            extension="txt",
            size=1024,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            downloadable=True,
            is_folder=False,
            content_available=True,
        ),
        FileRecord(
            id="f2",
            provider="google_drive",
            provider_file_id="gd_2",
            name="Final_Year_Fees_Receipt.pdf",
            path="/gdrive/Final_Year_Fees_Receipt.pdf",
            extension="pdf",
            size=2048,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            downloadable=True,
            is_folder=False,
            content_available=True,
        ),
    ]

    res = await model_comparison_service.benchmark_query(
        query="find my final year fees",
        candidate_files=candidates,
        limit_per_model=2,
    )

    assert res.query == "find my final year fees"
    assert len(res.models) == 5
    assert res.speed_champion_id in [m.model_id for m in res.models]
    assert res.accuracy_champion_id in [m.model_id for m in res.models]

    model_ids = {m.model_id for m in res.models}
    expected_ids = {
        "all-minilm-l6-v2",
        "bge-small-en-v1-5",
        "all-mpnet-base-v2",
        "e5-small-v2",
        "openclip-vit-b-32",
    }
    assert model_ids == expected_ids

    for m in res.models:
        assert m.latency_ms > 0
        assert m.dimension in [384, 512, 768]
        assert len(m.flaws) >= 2
        assert len(m.strengths) >= 2
        assert m.parameter_count
        assert m.memory_footprint
        assert m.context_tokens > 0
