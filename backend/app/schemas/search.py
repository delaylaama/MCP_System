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


class ModelBenchmarkTopMatch(BaseModel):
    file_id: str
    name: str
    provider: str
    extension: Optional[str] = ""
    score: float
    match_percentage: float
    relevance_reason: Optional[str] = None


class ModelBenchmarkResult(BaseModel):
    model_id: str
    model_name: str
    family: str
    badge: str
    dimension: int
    parameter_count: str
    context_tokens: int
    memory_footprint: str
    architecture: str
    latency_ms: float
    top_score_pct: float
    avg_relevance_pct: float
    mteb_score: float
    status: str = "active"
    description: str
    strengths: List[str]
    flaws: List[str]
    best_for: str
    top_matches: List[ModelBenchmarkTopMatch]


class ModelCompareRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query to benchmark across 5 models")
    providers: Optional[List[str]] = None
    file_type: Optional[str] = None
    limit_per_model: int = Field(default=3, ge=1, le=10)


class ModelCompareResponse(BaseModel):
    query: str
    total_candidates_evaluated: int
    speed_champion_id: str
    accuracy_champion_id: str
    models: List[ModelBenchmarkResult]

