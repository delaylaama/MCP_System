"""File Metadata Cache Repository."""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.file_metadata import FileMetadata
from backend.app.schemas.file import FileRecord


class FileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_provider_and_file_id(self, user_id: str, provider: str, provider_file_id: str) -> Optional[FileMetadata]:
        stmt = select(FileMetadata).where(
            FileMetadata.user_id == user_id,
            FileMetadata.provider == provider,
            FileMetadata.provider_file_id == provider_file_id,
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def sync_record(self, user_id: str, record: FileRecord) -> FileMetadata:
        cached = await self.get_by_provider_and_file_id(user_id, record.provider, record.provider_file_id)
        if not cached:
            cached = FileMetadata(
                user_id=user_id,
                provider=record.provider,
                provider_file_id=record.provider_file_id,
                name=record.name,
                path=record.path,
                mime_type=record.mime_type,
                extension=record.extension,
                size=record.size,
                modified_at=record.modified_at,
                web_url=record.web_url,
                downloadable=record.downloadable,
                is_folder=record.is_folder,
                content_hash=record.content_hash,
            )
            self.session.add(cached)
        else:
            cached.name = record.name
            cached.path = record.path
            cached.mime_type = record.mime_type
            cached.size = record.size
            cached.modified_at = record.modified_at
            cached.content_hash = record.content_hash
        await self.session.commit()
        await self.session.refresh(cached)
        return cached

    async def list_user_files(self, user_id: str) -> List[FileMetadata]:
        stmt = select(FileMetadata).where(FileMetadata.user_id == user_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def search_user_files(
        self,
        user_id: str,
        query: str,
        providers: Optional[List[str]] = None,
        file_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[FileRecord]:
        """Searches indexed file metadata in SQLite cache with typo and keyword tolerance."""
        import re
        import difflib

        stmt = select(FileMetadata).where(FileMetadata.user_id == user_id)
        if providers:
            stmt = stmt.where(FileMetadata.provider.in_(providers))
        if file_type:
            clean_type = file_type.lower().lstrip(".")
            stmt = stmt.where(FileMetadata.extension == f".{clean_type}")

        res = await self.session.execute(stmt)
        records = res.scalars().all()

        from backend.app.utils.query_parser import extract_terms, compute_term_match, clean_query_text

        query_terms = extract_terms(query, keep_recency=True)
        query_distilled = clean_query_text(query)
        is_wildcard = not query or query.strip() in ["*", "all", "all files"]

        matched: List[FileRecord] = []
        for r in records:
            name_lower = r.name.lower()
            path_lower = (r.path or "").lower()

            hit = False
            if is_wildcard:
                hit = True
            elif query_distilled and (query_distilled in name_lower or query_distilled in path_lower):
                hit = True
            else:
                is_term_hit, coverage = compute_term_match(query_terms, f"{name_lower} {path_lower}")
                if is_term_hit:
                    hit = True

            if hit:
                matched.append(
                    FileRecord(
                        id=f"{r.provider}_{r.provider_file_id}",
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
                if len(matched) >= limit:
                    break
        return matched
