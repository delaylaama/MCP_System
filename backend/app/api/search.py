"""Search API Routes."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.schemas.search import SearchRequest, SearchResponse, SearchHistoryResponse
from backend.app.services.search_service import SearchService
from backend.app.repositories.search_repository import SearchRepository

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_files(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    return await service.execute_search(user_id=current_user.id, request=request)


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
