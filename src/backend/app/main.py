from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_reading import router as reading_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging

logger = logging.getLogger("main")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("Starting %s — env=%s", settings.app_name, settings.environment)

    app = FastAPI(title=settings.app_name)

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        start = time.perf_counter()
        logger.info("→ %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "← %s %s %d (%dms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "! %s %s raised %s: %s (%dms)",
                request.method,
                request.url.path,
                type(exc).__name__,
                exc,
                duration_ms,
            )
            raise

    app.include_router(health_router)
    app.include_router(reading_router)
    app.include_router(chat_router)
    return app


app = create_app()
