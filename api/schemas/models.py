"""
API schemas: Pydantic v2 models for all request/response contracts.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="User message to classify")
    top_k: int = Field(3, ge=1, le=10, description="Number of top predictions to return")

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        return v.strip()


class BatchPredictRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=50, description="List of user messages")
    top_k: int = Field(3, ge=1, le=10)

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v: List[str]) -> List[str]:
        cleaned = [t.strip() for t in v if t.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty text is required")
        return cleaned


class IntentPrediction(BaseModel):
    intent_id: str
    intent_label: str
    confidence: float


class PredictResponse(BaseModel):
    text: str
    top_intent: IntentPrediction
    all_predictions: List[IntentPrediction]
    model_version: str
    cached: bool = False
    latency_ms: Optional[float] = None


class BatchPredictResponse(BaseModel):
    results: List[PredictResponse]
    total: int
    latency_ms: float


class IntentInfo(BaseModel):
    id: str
    label: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    num_intents: int
    uptime_seconds: float


class MetricsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    cache_hit_rate: float
    avg_latency_ms: float
    intent_distribution: Dict[str, int]


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
