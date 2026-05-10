from __future__ import annotations

from fastapi import APIRouter

from app.schemas.intake import StartReadingRequest
from app.schemas.responses import InitialReadingResponse
from app.services.reading_service import start_reading
from app.services.session_store import session_store

router = APIRouter(prefix="/reading", tags=["reading"])


@router.post("/start", response_model=InitialReadingResponse)
def post_start_reading(request: StartReadingRequest) -> InitialReadingResponse:
    return start_reading(request, session_store)
