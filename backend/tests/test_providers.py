"""Tests for provider adapters, Local filesystem, and path traversal protection."""

import pytest
from pathlib import Path
from backend.app.providers.local import LocalFileProvider


@pytest.mark.asyncio
async def test_local_provider_operations(tmp_path: Path):
    # Setup test directory with files
    test_file_1 = tmp_path / "resume_test.txt"
    test_file_1.write_text("Experienced Python and MCP Engineer", encoding="utf-8")

    test_file_2 = tmp_path / "invoice_june.txt"
    test_file_2.write_text("Total Amount: $500 for June 2026", encoding="utf-8")

    sub_dir = tmp_path / "documents"
    sub_dir.mkdir()
    (sub_dir / "report.md").write_text("# Capstone Project", encoding="utf-8")

    provider = LocalFileProvider(root_path=str(tmp_path))

    # Test list_files
    files = await provider.list_files()
    assert len(files) >= 2
    names = [f.name for f in files]
    assert "resume_test.txt" in names
    assert "invoice_june.txt" in names

    # Test search_files
    search_res = await provider.search_files(query="resume")
    assert len(search_res) == 1
    assert search_res[0].name == "resume_test.txt"

    # Test get_file_content
    content = await provider.get_file_content(file_id=search_res[0].provider_file_id)
    assert "Experienced Python" in content

    # Test path traversal prevention
    with pytest.raises(PermissionError):
        provider._resolve_safe_path("../../../etc/passwd")

    with pytest.raises(PermissionError):
        provider._resolve_safe_path("..\\..\\Windows\\System32")
