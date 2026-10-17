"""Provider connection schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProviderStatusResponse(BaseModel):
    provider: str
    name: str
    connected: bool
    account_identifier: Optional[str] = None
    connected_at: Optional[datetime] = None
    status: str = "disconnected"  # connected, expired, disconnected
    file_count: Optional[int] = 0
    used_storage: Optional[str] = "0 B"
    total_storage: Optional[str] = "0 B"
    used_percent: Optional[float] = 0.0


class ProviderConnectResponse(BaseModel):
    provider: str
    authorization_url: str
    state: str
