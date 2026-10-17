"""
Evaluation Benchmark Script:
1. Indexes all ~20 test fixture files into the local search index.
2. Runs 30 distinct natural-language queries testing filename, metadata, content text, and visual CLIP embeddings.
3. Computes and displays Recall@1, Recall@5, and Mean Reciprocal Rank (MRR).
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Enforce offline mode for evaluation
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from backend.search.indexer import indexer
from backend.search.search import search_files
from backend.search.db import db

FIXTURES_DIR = root_dir / "tests" / "fixtures"

# 30 Natural-Language Test Queries with Expected Targets
BENCHMARK_QUERIES = [
    # --- Resume & Date Queries ---
    {
        "query": "give me my latest resume",
        "sort": "modified_desc",
        "file_types": ["pdf", "docx"],
        "expected": ["resume_latest_2026_ai_lead.pdf"],
    },
    {
        "query": "junior developer resume",
        "expected": ["resume_2022_thejas.docx"],
    },
    {
        "query": "senior software engineer resume",
        "expected": ["resume_2024_senior_engineer.pdf"],
    },
    {
        "query": "academic researcher cv",
        "expected": ["cv_academic_researcher.txt"],
    },
    {
        "query": "curriculum vitae publications neural retrieval",
        "expected": ["cv_academic_researcher.txt"],
    },

    # --- Visual Image Queries (CLIP Text-to-Image) ---
    {
        "query": "leaf png",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["green_oak_leaf.png", "tropical_palm_leaves.png", "fern_frond_macro.png", "autumn_maple_leaf.jpg"],
    },
    {
        "query": "autumn maple leaf",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["autumn_maple_leaf.jpg"],
    },
    {
        "query": "tropical palm leaves",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["tropical_palm_leaves.png"],
    },
    {
        "query": "green fern plant",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["fern_frond_macro.png", "green_oak_leaf.png"],
    },
    {
        "query": "red sports car",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["sports_car_red.png"],
    },
    {
        "query": "financial bar chart graph",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["financial_chart_q3.png"],
    },
    {
        "query": "modern skyscraper city building",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["modern_skyscraper_glass.png"],
    },
    {
        "query": "golden retriever pet dog",
        "file_types": ["png", "jpg", "jpeg"],
        "expected": ["golden_retriever_dog.jpg"],
    },

    # --- Invoices & Financial Documents ---
    {
        "query": "cloud hosting invoice",
        "file_types": ["pdf"],
        "expected": ["invoice_2026_01_cloud_hosting.pdf"],
    },
    {
        "query": "dedicated GPU server bill 1450",
        "expected": ["invoice_2026_01_cloud_hosting.pdf"],
    },
    {
        "query": "quarterly budget allocation spreadsheet",
        "expected": ["quarterly_budget_2025.csv"],
    },
    {
        "query": "engineering department budget",
        "expected": ["quarterly_budget_2025.csv"],
    },
    {
        "query": "Form W-2 wage and tax statement",
        "expected": ["taxes_w2_statement_2025.pdf"],
    },
    {
        "query": "federal income tax withheld 2025",
        "expected": ["taxes_w2_statement_2025.pdf"],
    },

    # --- Contracts, Architecture & Engineering Docs ---
    {
        "query": "mutual non disclosure agreement",
        "expected": ["nda_consulting_agreement.docx"],
    },
    {
        "query": "client contractor NDA",
        "expected": ["nda_consulting_agreement.docx"],
    },
    {
        "query": "transformer reciprocal rank fusion notes",
        "expected": ["machine_learning_notes.md"],
    },
    {
        "query": "CLIP ViT-B/32 cosine similarity",
        "expected": ["machine_learning_notes.md"],
    },
    {
        "query": "March 2026 team standup meeting minutes",
        "expected": ["meeting_minutes_march_2026.txt"],
    },
    {
        "query": "attendees Sarah Thejas Elena LanceDB migration",
        "expected": ["meeting_minutes_march_2026.txt"],
    },
    {
        "query": "project architecture specification",
        "expected": ["project_architecture_spec.md"],
    },
    {
        "query": "desktop application FastAPI Model Context Protocol",
        "expected": ["project_architecture_spec.md"],
    },
    {
        "query": "docker compose production environment",
        "expected": ["docker_compose_production.txt"],
    },
    {
        "query": "HF_HUB_OFFLINE TRANSFORMERS_OFFLINE config",
        "expected": ["docker_compose_production.txt"],
    },
    {
        "query": "oak leaf tree",
        "expected": ["green_oak_leaf.png"],
    },
]


def index_fixtures():
    print("=" * 75)
    print("STEP 1: Indexing Test Fixtures into Local AI Search Engine")
    print("=" * 75)
    if not FIXTURES_DIR.exists():
        print(f"Error: Fixtures directory not found: {FIXTURES_DIR}")
        return 0

    fixture_files = list(FIXTURES_DIR.glob("*.*"))
    print(f"Found {len(fixture_files)} files in {FIXTURES_DIR}")

    indexed = 0
    for p in fixture_files:
        stat = p.stat()
        mtime_iso = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        file_id = f"fixture_{p.name}"
        ok = indexer.index_single_file(
            file_id=file_id,
            source="local",
            name=p.name,
            path=str(p),
            local_path=p,
            modified=mtime_iso,
            size=stat.st_size,
        )
        if ok:
            indexed += 1
            print(f"  [INDEXED] {p.name}")

    print(f"\nIndexed {indexed}/{len(fixture_files)} fixture files successfully.\n")
    return indexed


def run_evaluation():
    indexed_count = index_fixtures()
    if indexed_count == 0:
        print("Cannot run evaluation without indexed fixtures.")
        return

    print("=" * 75)
    print("STEP 2: Executing 30 Natural-Language Benchmark Queries")
    print("=" * 75)
    print(f"{'#':<3} | {'Query':<38} | {'Top-1 Result':<25} | {'R@1':<4} | {'R@5':<4}")
    print("-" * 80)

    hits_top1 = 0
    hits_top5 = 0
    reciprocal_ranks = []

    for idx, test_case in enumerate(BENCHMARK_QUERIES, 1):
        q = test_case["query"]
        sort = test_case.get("sort", "relevance")
        file_types = test_case.get("file_types")
        expected_files = test_case["expected"]

        results = search_files(
            query=q,
            file_types=file_types,
            sort=sort,
            limit=5,
            relevance_threshold=0.005,
        )

        result_names = [r["name"] for r in results]
        top1_name = result_names[0] if result_names else "NONE"

        hit_1 = any(top1_name == exp for exp in expected_files)
        hit_5 = any(exp in result_names for exp in expected_files)

        if hit_1:
            hits_top1 += 1
        if hit_5:
            hits_top5 += 1

        # Calculate reciprocal rank
        rank = 0
        for pos, name in enumerate(result_names, 1):
            if name in expected_files:
                rank = pos
                break
        rr = 1.0 / rank if rank > 0 else 0.0
        reciprocal_ranks.append(rr)

        q_display = (q[:35] + "...") if len(q) > 38 else q
        top_display = (top1_name[:22] + "...") if len(top1_name) > 25 else top1_name
        r1_sym = "[OK]" if hit_1 else "[--]"
        r5_sym = "[OK]" if hit_5 else "[--]"

        print(f"{idx:<3} | {q_display:<38} | {top_display:<25} | {r1_sym:<4} | {r5_sym:<4}")

    total_queries = len(BENCHMARK_QUERIES)
    recall_at_1 = (hits_top1 / total_queries) * 100
    recall_at_5 = (hits_top5 / total_queries) * 100
    mrr = sum(reciprocal_ranks) / total_queries

    print("=" * 80)
    print("BENCHMARK EVALUATION RESULTS:")
    print(f"  Total Queries Evaluated: {total_queries}")
    print(f"  Recall@1:                {hits_top1}/{total_queries} ({recall_at_1:.1f}%)")
    print(f"  Recall@5:                {hits_top5}/{total_queries} ({recall_at_5:.1f}%)")
    print(f"  Mean Reciprocal Rank:    {mrr:.3f}")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
