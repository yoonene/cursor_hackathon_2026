from __future__ import annotations

import logging

from fastapi import APIRouter

from app.schemas.intake import StartReadingRequest
from app.schemas.responses import InitialReadingResponse
from app.services.reading_service import start_reading
from app.services.session_store import session_store

router = APIRouter(prefix="/reading", tags=["reading"])
logger = logging.getLogger("routes.reading")


@router.post("/start", response_model=InitialReadingResponse)
def post_start_reading(request: StartReadingRequest) -> InitialReadingResponse:
    logger.info(
        "POST /reading/start — session_id=%s name=%s birth_date=%s",
        request.session_id,
        request.display_name,
        request.birth_date,
    )
    return start_reading(request, session_store)
