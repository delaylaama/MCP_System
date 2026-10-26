"""Search API Routes."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchHistoryResponse,
    ModelCompareRequest,
    ModelCompareResponse,
)
from backend.app.schemas.file import FileRecord
from backend.app.services.search_service import SearchService
from backend.app.services.model_comparison_service import model_comparison_service
from backend.app.repositories.search_repository import SearchRepository
from backend.app.repositories.file_repository import FileRepository

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_files(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    return await service.execute_search(user_id=current_user.id, request=request)


@router.post("/compare-models", response_model=ModelCompareResponse)
async def compare_search_models(
    request: ModelCompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_repo = FileRepository(db)
    candidates = await file_repo.search_user_files(
        user_id=current_user.id,
        query=request.query,
        providers=request.providers,
        file_type=request.file_type,
    )
    # If filtered candidates are limited, enrich with user files to give robust benchmark comparisons
    if len(candidates) < 5:
        recent_files = await file_repo.list_user_files(user_id=current_user.id)
        existing_ids = {c.id for c in candidates}
        for r in recent_files[:30]:
            rec_id = f"{r.provider}_{r.provider_file_id}"
            if rec_id not in existing_ids:
                candidates.append(
                    FileRecord(
                        id=rec_id,
                        provider=r.provider,
                        provider_file_id=r.provider_file_id,
                        name=r.name,
                        path=r.path or f"/{r.name}",
                        mime_type=r.mime_type or "application/octet-stream",
                        extension=r.extension or "",
                        size=r.size or 0,
                        modified_at=r.modified_at,
                        web_url=r.web_url,
                        downloadable=r.downloadable if r.downloadable is not None else True,
                        is_folder=r.is_folder if r.is_folder is not None else False,
                        content_available=False,
                        content_hash=r.content_hash,
                    )
                )

    return await model_comparison_service.benchmark_query(
        query=request.query,
        candidate_files=candidates,
        limit_per_model=request.limit_per_model,
    )


@router.get("/history", response_model=List[SearchHistoryResponse])
async def get_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SearchRepository(db)
    items = await repo.list_by_user(current_user.id)
    return [SearchHistoryResponse.model_validate(i) for i in items]


@router.delete("/history")
async def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SearchRepository(db)
    cleared = await repo.clear_by_user(current_user.id)
    return {"message": "Search history cleared.", "count": cleared}

