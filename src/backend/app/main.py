from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_reading import router as reading_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(reading_router)
    return app


app = create_app()
