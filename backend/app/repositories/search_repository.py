"""Search History Repository for database access."""

from typing import List
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.search_history import SearchHistory


class SearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: str, query: str, intent_summary: str | None, number_of_results: int) -> SearchHistory:
        entry = SearchHistory(
            user_id=user_id,
            query=query,
            intent_summary=intent_summary,
            number_of_results=number_of_results,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_by_user(self, user_id: str, limit: int = 20) -> List[SearchHistory]:
        stmt = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.created_at))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def clear_by_user(self, user_id: str) -> int:
        stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount
