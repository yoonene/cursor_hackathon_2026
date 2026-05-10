from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.requests import ChatRequest
from app.schemas.responses import ChatResponse
from app.services.chat_service import continue_chat, iterate_continue_chat_sse
from app.services.session_store import session_store

router = APIRouter(tags=["chat"])
logger = logging.getLogger("routes.chat")


@router.post("/chat/stream")
async def post_chat_stream(request: ChatRequest) -> StreamingResponse:
    """SSE: ``prelude`` (board snapshot after tools) → ``delta`` tokens → ``complete`` (full ``ChatResponse`` JSON)."""

    if session_store.get(request.session_id) is None:
        logger.warning("POST /chat/stream — unknown session_id=%s", request.session_id)
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id — call POST /reading/start first.",
        )

    logger.info(
        "POST /chat/stream — session_id=%s msg_len=%d",
        request.session_id,
        len(request.message),
    )

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}

    async def sse_body() -> AsyncIterator[bytes]:
        async for chunk in iterate_continue_chat_sse(session_store, request):
            yield chunk

    return StreamingResponse(sse_body(), media_type="text/event-stream", headers=headers)


@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest) -> ChatResponse:
    logger.info(
        "POST /chat — session_id=%s msg_len=%d",
        request.session_id,
        len(request.message),
    )
    outcome = continue_chat(session_store, request)
    if outcome is None:
        logger.warning("POST /chat — unknown session_id=%s", request.session_id)
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id — call POST /reading/start first.",
        )
    return outcome
