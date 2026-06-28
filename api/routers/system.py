"""
System router: health check, Prometheus-style metrics, available intents.
"""
import time
import logging
from fastapi import APIRouter, HTTPException

from api.schemas.models import HealthResponse, MetricsResponse, IntentInfo
from api.middleware.cache import cache, metrics
from inference.predictor import get_predictor

log = logging.getLogger(__name__)
router = APIRouter(tags=["System"])

_startup_time = time.time()


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check():
    try:
        predictor = get_predictor()
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            device=str(predictor.device),
            num_intents=len(predictor.available_intents),
            uptime_seconds=round(time.time() - _startup_time, 2),
        )
    except Exception as e:
        log.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/metrics", response_model=MetricsResponse, summary="Request metrics")
async def get_metrics():
    total = metrics.total_requests
    hits = cache.hits
    return MetricsResponse(
        total_requests=total,
        cache_hits=hits,
        cache_hit_rate=round(hits / max(total + hits, 1), 4),
        avg_latency_ms=metrics.avg_latency_ms,
        intent_distribution=dict(metrics.intent_distribution),
    )


@router.get("/intents", response_model=list[IntentInfo], summary="List all available intents")
async def list_intents():
    try:
        predictor = get_predictor()
        return [IntentInfo(**i) for i in predictor.available_intents]
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
