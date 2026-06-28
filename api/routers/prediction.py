"""
Prediction router: /predict, /predict/batch, /predict/stream (SSE)
"""
import time
import json
import asyncio
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from api.schemas.models import (
    PredictRequest, PredictResponse,
    BatchPredictRequest, BatchPredictResponse,
    IntentPrediction,
)
from api.middleware.cache import cache, metrics
from inference.predictor import get_predictor, compute_cache_key, IntentPredictor

log = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["Prediction"])


def get_model() -> IntentPredictor:
    return get_predictor()


@router.post("", response_model=PredictResponse, summary="Classify a single user message")
async def predict_intent(req: PredictRequest, predictor: IntentPredictor = Depends(get_model)):
    cache_key = compute_cache_key(req.text)
    cached_result = cache.get(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return PredictResponse(**cached_result)

    t0 = time.perf_counter()
    try:
        result = predictor.predict(req.text, top_k=req.top_k)
    except Exception as e:
        log.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    latency = round((time.perf_counter() - t0) * 1000, 2)
    metrics.record(result["top_intent"]["intent_id"], latency)

    response_data = {
        "text": result["text"],
        "top_intent": IntentPrediction(**result["top_intent"]),
        "all_predictions": [IntentPrediction(**p) for p in result["all_predictions"]],
        "model_version": result["model_version"],
        "cached": False,
        "latency_ms": latency,
    }
    cache.set(cache_key, {
        **result,
        "top_intent": result["top_intent"],
        "all_predictions": result["all_predictions"],
        "latency_ms": latency,
    })
    return PredictResponse(**response_data)


@router.post("/batch", response_model=BatchPredictResponse, summary="Classify multiple messages")
async def predict_batch(req: BatchPredictRequest, predictor: IntentPredictor = Depends(get_model)):
    t0 = time.perf_counter()
    results = []
    for text in req.texts:
        cache_key = compute_cache_key(text)
        cached = cache.get(cache_key)
        if cached:
            r = PredictResponse(
                text=cached["text"],
                top_intent=IntentPrediction(**cached["top_intent"]),
                all_predictions=[IntentPrediction(**p) for p in cached["all_predictions"]],
                model_version=cached["model_version"],
                cached=True,
                latency_ms=cached.get("latency_ms"),
            )
            results.append(r)
            continue

        t1 = time.perf_counter()
        try:
            result = predictor.predict(text, top_k=req.top_k)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        lat = round((time.perf_counter() - t1) * 1000, 2)
        metrics.record(result["top_intent"]["intent_id"], lat)
        cache.set(cache_key, {**result, "latency_ms": lat})

        results.append(PredictResponse(
            text=result["text"],
            top_intent=IntentPrediction(**result["top_intent"]),
            all_predictions=[IntentPrediction(**p) for p in result["all_predictions"]],
            model_version=result["model_version"],
            cached=False,
            latency_ms=lat,
        ))

    total_latency = round((time.perf_counter() - t0) * 1000, 2)
    return BatchPredictResponse(results=results, total=len(results), latency_ms=total_latency)


@router.post("/stream", summary="Stream prediction tokens via SSE")
async def predict_stream(req: PredictRequest, predictor: IntentPredictor = Depends(get_model)):
    async def event_generator() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'status': 'processing', 'text': req.text})}\n\n"
        await asyncio.sleep(0.05)

        try:
            result = predictor.predict(req.text, top_k=req.top_k)
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'detail': str(e)})}\n\n"
            return

        for pred in result["all_predictions"]:
            yield f"data: {json.dumps({'status': 'partial', 'prediction': pred})}\n\n"
            await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'status': 'done', 'top_intent': result['top_intent']})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
