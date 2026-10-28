"""
Search Orchestrator uniting AI intent interpretation, MCP tools, Semantic Search, and Multi-Factor Ranking.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.schemas.file import FileRecord
from backend.app.services.ai_service import ai_service
from backend.app.services.ranking_service import ranking_service
from backend.app.services.indexing_service import semantic_search_service
from backend.app.repositories.search_repository import SearchRepository
from backend.app.repositories.file_repository import FileRepository
from backend.app.core.logging import logger


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.search_repo = SearchRepository(db)
        self.file_repo = FileRepository(db)

    async def execute_search(self, user_id: str, request: SearchRequest) -> SearchResponse:
        logger.info(f"Executing search for user {user_id}: '{request.query}'")

        # 0. Natural Language Entity & Location Extraction
        from backend.app.utils.query_parser import parse_natural_language_query
        nlp = parse_natural_language_query(request.query)
        effective_providers = request.providers or ([nlp["provider"]] if nlp["provider"] else None)
        effective_file_type = request.file_type or nlp["file_type"]
        effective_query = nlp["clean_target"]
        effective_folder = nlp["folder"]

        # 1. AI Intent & MCP Tool Calling
        if request.use_ai:
            ai_output = await ai_service.process_query(
                query=request.query,
                context={"user_id": user_id, "providers": effective_providers, "file_type": effective_file_type},
            )
            raw_candidates = ai_output.get("results", [])
            interpreted_intent = ai_output.get("intent")
            ai_summary = ai_output.get("ai_summary")
        else:
            from backend.app.mcp.client import mcp_client
            tool_args = {"query": effective_query, "user_id": user_id}
            if effective_providers and len(effective_providers) == 1:
                tool_args["provider"] = effective_providers[0]
            if effective_file_type:
                tool_args["file_type"] = effective_file_type
            raw_candidates = await mcp_client.call_tool("search_files", tool_args)
            interpreted_intent = {
                "action": "search_files",
                "parameters": tool_args,
                "natural_language_breakdown": {
                    "target_file": effective_query,
                    "target_provider": effective_providers[0] if (effective_providers and len(effective_providers) == 1) else "all_providers",
                    "target_folder": effective_folder,
                    "file_type": effective_file_type,
                },
            }
            ai_summary = f"Direct search for '{effective_query}' executed via MCP."

        # Convert raw dictionaries to FileRecord objects
        if isinstance(raw_candidates, dict):
            raw_candidates = [raw_candidates]
        elif not isinstance(raw_candidates, list):
            raw_candidates = []

        candidate_records: List[FileRecord] = []
        for item in raw_candidates:
            if isinstance(item, FileRecord):
                candidate_records.append(item)
            elif isinstance(item, dict):
                try:
                    candidate_records.append(FileRecord.model_validate(item))
                except Exception as e:
                    logger.warning(f"Skipping malformed record: {e}")
        # 1.1 Also include matching files from cached file_metadata repository
        # (ensures previously synced cloud files like Google Drive remain searchable)
        try:
            db_candidates = await self.file_repo.search_user_files(
                user_id=user_id,
                query=effective_query,
                providers=effective_providers,
                file_type=effective_file_type,
            )
            existing_ids = {c.id for c in candidate_records}
            existing_keys = {(c.provider, c.name.lower(), c.size) for c in candidate_records}
            for rec in db_candidates:
                rec_key = (rec.provider, rec.name.lower(), rec.size)
                if rec.id not in existing_ids and rec_key not in existing_keys:
                    candidate_records.append(rec)
                    existing_ids.add(rec.id)
                    existing_keys.add(rec_key)
        except Exception as e:
            logger.warning(f"Error querying file_metadata cache: {e}")

        # 2. Query Semantic Vector Database (LanceDB + ChromaDB fallback)
        semantic_scores = {}
        if request.query and request.query.strip() != "*":
            from backend.app.utils.query_parser import clean_query_text
            clean_q = clean_query_text(request.query)
            # 2.1 LanceDB text vector retrieval
            try:
                from backend.search.models import model_manager
                from backend.search.db import db as local_search_db
                q_vec = model_manager.embed_text(clean_q or request.query)
                if q_vec:
                    vec_results = local_search_db.search_text_vectors(q_vec, limit=50)
                    for r in vec_results:
                        fid = r.get("file_id")
                        dist = r.get("_distance", 1.0)
                        sim = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                        if fid:
                            semantic_scores[fid] = round(sim, 4)
                            clean_id = fid.removeprefix("local_").removeprefix("fixture_")
                            semantic_scores[clean_id] = round(sim, 4)
                            semantic_scores[f"local_{clean_id}"] = round(sim, 4)
            except Exception as e:
                logger.warning(f"LanceDB semantic vector search error: {e}")

            # 2.2 LanceDB CLIP image vector retrieval (Cross-modal visual search)
            try:
                from backend.search.models import model_manager
                from backend.search.db import db as local_search_db
                clip_vec = model_manager.embed_clip_text(clean_q or request.query)
                if clip_vec:
                    img_results = local_search_db.search_image_vectors(clip_vec, limit=50)
                    for r in img_results:
                        fid = r.get("file_id")
                        dist = r.get("_distance", 1.0)
                        sim = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                        if fid:
                            prev = semantic_scores.get(fid, 0.0)
                            semantic_scores[fid] = max(prev, round(sim, 4))
                            clean_id = fid.removeprefix("local_").removeprefix("fixture_")
                            semantic_scores[clean_id] = max(semantic_scores.get(clean_id, 0.0), round(sim, 4))
                            semantic_scores[f"local_{clean_id}"] = max(semantic_scores.get(f"local_{clean_id}", 0.0), round(sim, 4))
            except Exception as e:
                logger.warning(f"LanceDB CLIP image vector search error: {e}")

            # 2.3 ChromaDB fallback
            try:
                chroma_scores = semantic_search_service.semantic_query(clean_q or request.query, top_k=50)
                for k, v in chroma_scores.items():
                    if k not in semantic_scores:
                        semantic_scores[k] = v
            except Exception:
                pass

        # 3. Apply Multi-Factor Ranking Engine
        ranked_results = ranking_service.rank_results(
            query=request.query,
            candidates=candidate_records,
            semantic_scores=semantic_scores,
        )

        # Apply limits
        limited_results = ranked_results[:request.limit]

        # 4. Asynchronously cache metadata & log Search History
        try:
            await self.search_repo.create(
                user_id=user_id,
                query=request.query,
                intent_summary=ai_summary,
                number_of_results=len(limited_results),
            )
            for rec in limited_results:
                await self.file_repo.sync_record(user_id=user_id, record=rec)
        except Exception as e:
            logger.warning(f"Error persisting search metadata: {e}")

        return SearchResponse(
            query=request.query,
            interpreted_intent=interpreted_intent,
            ai_summary=ai_summary,
            total_results=len(ranked_results),
            results=limited_results,
            ranking_weights_used=ranking_service.get_weights(),
        )
