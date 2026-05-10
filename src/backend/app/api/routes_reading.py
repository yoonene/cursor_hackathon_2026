from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.intake import StartReadingRequest
from app.schemas.responses import InitialReadingResponse
from app.services.reading_service import start_reading, start_reading_stream
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


@router.post("/start-stream")
async def post_start_reading_stream(request: StartReadingRequest) -> StreamingResponse:
    """SSE 스트리밍으로 초기 리딩을 반환한다.

    이벤트 순서:
        prelude  — 사주 계산 완료, session_id 포함
        delta    — LLM 텍스트 조각 {"text": "..."}
        complete — 완전한 InitialReadingResponse JSON
    """
    logger.info(
        "POST /reading/start-stream — session_id=%s name=%s birth_date=%s",
        request.session_id,
        request.display_name,
        request.birth_date,
    )

    async def event_generator():
        async for event_type, data in start_reading_stream(request, session_store):
            if event_type == "prelude":
                yield f"event: prelude\ndata: {json.dumps(data)}\n\n"
            elif event_type == "delta":
                yield f"event: delta\ndata: {json.dumps({'text': data})}\n\n"
            elif event_type == "complete":
                yield f"event: complete\ndata: {data.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
