"""Search request and response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.schemas.file import FileRecord


class SearchFilter(BaseModel):
    providers: Optional[List[str]] = None
    file_type: Optional[str] = None
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural-language or keyword query")
    providers: Optional[List[str]] = Field(default=None, description="Specific providers to filter")
    file_type: Optional[str] = Field(default=None, description="File type filter, e.g. 'pdf', 'doc'")
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None
    use_ai: bool = Field(default=True, description="Enable LLM intent analysis and tool calling")
    limit: int = Field(default=20, ge=1, le=100)


class SearchHistoryResponse(BaseModel):
    id: str
    query: str
    intent_summary: Optional[str] = None
    number_of_results: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    interpreted_intent: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
    total_results: int
    results: List[FileRecord]
    ranking_weights_used: Optional[Dict[str, float]] = None
