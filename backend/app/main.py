from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.middleware.rate_limiter import RateLimiterMiddleware
from app.api.v1.middleware.request_tracking import RequestTrackingMiddleware
from app.api.v1.router import api_router
from app.core.config.settings import settings
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging.structured_logger import StructuredLoggingMiddleware, setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info(
        "Starting %s v%s (%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    from app.api.v1.dependencies.getters import (
        get_agent_router,
        get_generative_ai_service,
        get_rag_service,
    )

    try:
        get_agent_router()
        logger.info("AgentRouter initialized")
    except Exception:
        logger.exception("Failed to initialize AgentRouter")

    try:
        get_generative_ai_service()
        logger.info("GenerativeAIService initialized")
    except Exception:
        logger.exception("Failed to initialize GenerativeAIService")

    try:
        get_rag_service()
        logger.info("RAGService initialized")
    except Exception:
        logger.exception("Failed to initialize RAGService")

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down %s", settings.APP_NAME)

    from app.api.v1.dependencies.getters import get_maps_service, get_identity_service

    try:
        maps_svc = get_maps_service()
        await maps_svc.close()
    except Exception:
        pass

    try:
        identity_svc = get_identity_service()
        await identity_svc.close()
    except Exception:
        pass

    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "StadiumOS AI - Intelligent Stadium Management Platform with "
        "multilingual AI agents, real-time operations, and Google Cloud integration."
    ),
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-Remaining"],
)

app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(RateLimiterMiddleware)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Infrastructure"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready", tags=["Infrastructure"])
async def readiness_probe() -> dict[str, Any]:
    checks: dict[str, Any] = {
        "firestore": "unknown",
        "vertex_ai": "unknown",
        "pubsub": "unknown",
    }

    try:
        from app.infrastructure.firestore.client import get_firestore_client

        client = get_firestore_client()
        client.collection("_health_check").limit(1).get()
        checks["firestore"] = "ok"
    except Exception as e:
        checks["firestore"] = f"error: {str(e)[:100]}"

    try:
        from app.api.v1.dependencies.getters import get_generative_ai_service

        svc = get_generative_ai_service()
        if svc._initialized:
            checks["vertex_ai"] = "ok"
        else:
            checks["vertex_ai"] = "not_initialized"
    except Exception as e:
        checks["vertex_ai"] = f"error: {str(e)[:100]}"

    try:
        from app.infrastructure.pubsub.publisher import PubSubPublisher

        checks["pubsub"] = "ok"
    except Exception as e:
        checks["pubsub"] = f"error: {str(e)[:100]}"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/live", tags=["Infrastructure"])
async def liveness_probe() -> dict[str, str]:
    return {"status": "alive", "service": settings.APP_NAME}
