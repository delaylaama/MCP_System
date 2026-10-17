"""
Hybrid Local AI Search Engine.
Combines:
1. Keyword Full-Text Search (SQLite FTS5)
2. Semantic Document Search (MiniLM embeddings via LanceDB)
3. Visual Multimodal Search (CLIP ViT-B/32 text-to-image via LanceDB)
Merged via Reciprocal Rank Fusion (RRF, k=60).
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.search.db import db
from backend.search.models import model_manager
from backend.app.core.logging import logger


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Merges multiple ranked lists using Reciprocal Rank Fusion:
    RRF_score(d) = sum_{m} 1 / (k + rank_m(d))
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list):
            doc_id = item.get("file_id") or item.get("id")
            if not doc_id:
                continue
            if doc_id not in doc_map:
                doc_map[doc_id] = item
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

    # Sort items by merged RRF score descending
    sorted_ids = sorted(scores.keys(), key=lambda d_id: scores[d_id], reverse=True)
    merged = []
    for d_id in sorted_ids:
        item = doc_map[d_id].copy()
        item["score"] = round(scores[d_id], 4)
        merged.append(item)
    return merged


def search_files(
    query: str,
    file_types: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    sort: str = "relevance",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10,
    relevance_threshold: float = 0.015,
) -> List[Dict[str, Any]]:
    """
    Natural-language file search across all sources by filename, metadata, and content.
    Returns: list of dicts with name, path, source, modified, mime, score, snippet.
    """
    if not query or not query.strip():
        return []

    from backend.app.utils.query_parser import clean_query_text

    clean_query = clean_query_text(query)
    if not clean_query:
        clean_query = query.strip()

    candidate_lists: List[List[Dict[str, Any]]] = []

    # 1. Full-Text Search via SQLite FTS5
    fts_results = db.search_fts(clean_query, limit=50)
    if fts_results:
        # Standardize key names
        for item in fts_results:
            item["file_id"] = item["id"]
            item["snippet"] = item.get("content_snippet", "")
        candidate_lists.append(fts_results)

    # 2. Semantic Document Search via MiniLM (LanceDB text_vectors)
    text_vector = model_manager.embed_text(clean_query)
    if text_vector:
        text_vec_results = db.search_text_vectors(text_vector, limit=50)
        # Fetch metadata from SQLite
        enriched_text = []
        seen_files = set()
        for tv in text_vec_results:
            fid = tv.get("file_id")
            if fid in seen_files:
                continue
            seen_files.add(fid)
            meta = db.get_file(fid)
            if meta:
                meta["file_id"] = fid
                meta["snippet"] = tv.get("snippet", "")
                enriched_text.append(meta)
        if enriched_text:
            candidate_lists.append(enriched_text)

    # 3. Multimodal Visual Search via CLIP (LanceDB image_vectors)
    clip_text_vector = model_manager.embed_clip_text(clean_query)
    if clip_text_vector:
        image_vec_results = db.search_image_vectors(clip_text_vector, limit=50)
        enriched_images = []
        for iv in image_vec_results:
            fid = iv.get("file_id")
            meta = db.get_file(fid)
            if meta:
                meta["file_id"] = fid
                meta["snippet"] = meta.get("name", "")
                enriched_images.append(meta)
        if enriched_images:
            candidate_lists.append(enriched_images)

    # Merge results using Reciprocal Rank Fusion
    if not candidate_lists:
        return []

    merged_candidates = reciprocal_rank_fusion(candidate_lists, k=60)

    # Apply Metadata Filters
    filtered: List[Dict[str, Any]] = []
    
    # Normalize file_types filter
    norm_exts = set()
    if file_types:
        for ft in file_types:
            ft_clean = ft.lower().lstrip(".")
            norm_exts.add(ft_clean)
            if ft_clean in ("doc", "docs", "document", "documents", "resume"):
                norm_exts.update(["pdf", "docx", "doc", "txt", "md"])
            elif ft_clean in ("image", "images", "photo", "photos", "picture", "pictures"):
                norm_exts.update(["png", "jpg", "jpeg", "webp", "gif", "bmp"])

    # Normalize sources filter
    norm_sources = set()
    if sources:
        for s in sources:
            sc = s.lower().replace(" ", "_")
            if sc in ("gdrive", "google", "google_drive"):
                norm_sources.add("google_drive")
            elif sc in ("one_drive", "onedrive", "microsoft"):
                norm_sources.add("onedrive")
            elif sc in ("dropbox",):
                norm_sources.add("dropbox")
            elif sc in ("local", "system", "c", "c:", "d", "d:", "e", "e:"):
                norm_sources.add("local")
            else:
                norm_sources.add(sc)

    for item in merged_candidates:
        # Apply relevance threshold
        if item.get("score", 0.0) < relevance_threshold:
            continue

        # Filter by file type
        if norm_exts:
            item_ext = (item.get("ext") or "").lower().lstrip(".")
            if item_ext not in norm_exts:
                continue

        # Filter by source
        if norm_sources:
            item_source = (item.get("source") or "").lower()
            if item_source not in norm_sources:
                continue

        # Filter by date_from and date_to
        item_mod = item.get("modified")
        if item_mod:
            try:
                mod_dt = datetime.fromisoformat(item_mod.replace("Z", "+00:00"))
                if date_from:
                    from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                    if mod_dt < from_dt:
                        continue
                if date_to:
                    to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                    if mod_dt > to_dt:
                        continue
            except Exception:
                pass

        filtered.append(item)

    # Handle Sorting
    # For sort="modified_desc": take the top ~20 by relevance FIRST, then sort that set by date
    if sort in ("modified_desc", "latest", "recent"):
        top_relevance = filtered[:20]
        top_relevance.sort(key=lambda x: str(x.get("modified") or ""), reverse=True)
        final_results = top_relevance[:limit]
    elif sort in ("modified_asc", "oldest"):
        top_relevance = filtered[:20]
        top_relevance.sort(key=lambda x: str(x.get("modified") or ""), reverse=False)
        final_results = top_relevance[:limit]
    else:
        final_results = filtered[:limit]

    # Format output according to specification: name, path, source, modified, mime, score, snippet
    formatted = []
    for r in final_results:
        formatted.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "path": r.get("path"),
            "source": r.get("source"),
            "modified": r.get("modified"),
            "mime": r.get("mime"),
            "score": r.get("score"),
            "snippet": r.get("snippet") or r.get("content_snippet") or "",
        })
    return formatted
