"""Provider Connection Repository with automatic token encryption/decryption."""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.provider_connection import ProviderConnection
from backend.app.utils.encryption import encrypt_data, decrypt_data


class ProviderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_and_provider(self, user_id: str, provider: str) -> Optional[ProviderConnection]:
        stmt = select(ProviderConnection).where(
            ProviderConnection.user_id == user_id,
            ProviderConnection.provider == provider,
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_by_user(self, user_id: str) -> List[ProviderConnection]:
        stmt = select(ProviderConnection).where(ProviderConnection.user_id == user_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def upsert_connection(
        self,
        user_id: str,
        provider: str,
        account_identifier: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        status: str = "connected",
    ) -> ProviderConnection:
        conn = await self.get_by_user_and_provider(user_id, provider)
        encrypted_access = encrypt_data(access_token) if access_token else None
        encrypted_refresh = encrypt_data(refresh_token) if refresh_token else None

        if not conn:
            conn = ProviderConnection(
                user_id=user_id,
                provider=provider,
                account_identifier=account_identifier,
                encrypted_access_token=encrypted_access,
                encrypted_refresh_token=encrypted_refresh,
                status=status,
            )
            self.session.add(conn)
        else:
            if account_identifier:
                conn.account_identifier = account_identifier
            if encrypted_access:
                conn.encrypted_access_token = encrypted_access
            if encrypted_refresh:
                conn.encrypted_refresh_token = encrypted_refresh
            conn.status = status

        await self.session.commit()
        await self.session.refresh(conn)
        return conn

    async def delete_connection(self, user_id: str, provider: str) -> bool:
        stmt = delete(ProviderConnection).where(
            ProviderConnection.user_id == user_id,
            ProviderConnection.provider == provider,
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    @staticmethod
    def decrypt_credentials(conn: ProviderConnection) -> dict:
        """Returns in-memory decrypted access and refresh tokens for provider API calls."""
        return {
            "access_token": decrypt_data(conn.encrypted_access_token) if conn.encrypted_access_token else None,
            "refresh_token": decrypt_data(conn.encrypted_refresh_token) if conn.encrypted_refresh_token else None,
            "account_identifier": conn.account_identifier,
        }
