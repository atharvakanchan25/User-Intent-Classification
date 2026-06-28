"""
FastAPI application: intent classification service.
"""
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import prediction, system
from inference.predictor import get_predictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    log.info("Starting up: loading intent classification model...")
    try:
        predictor = get_predictor()
        log.info(f"Model ready. Intents: {len(predictor.available_intents)}")
    except FileNotFoundError:
        log.warning("Model not found. Run training/train.py first. Endpoints will return 503.")
    yield
    log.info("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Intent Classification API",
        description=(
            "Production-grade NLP service for classifying user messages into intents. "
            "Powered by DistilBERT fine-tuned on domain-specific data."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"})

    # Routers
    app.include_router(system.router)
    app.include_router(prediction.router)

    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": "Intent Classification API", "version": "1.0.0", "docs": "/docs"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "production") == "development",
        workers=int(os.getenv("WORKERS", "1")),
    )
