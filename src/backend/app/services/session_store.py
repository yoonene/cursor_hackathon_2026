from __future__ import annotations

from threading import Lock

from app.schemas.state import ConversationState


class InMemorySessionStore:
    """Hackathon-ready in-memory session state store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, ConversationState] = {}

    def get(self, session_id: str) -> ConversationState | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.model_copy(deep=True) if session else None

    def set(self, session: ConversationState) -> ConversationState:
        with self._lock:
            self._sessions[session.session_id] = session.model_copy(deep=True)
            return session

    def reset(self, session_id: str) -> bool:
        with self._lock:
            removed = self._sessions.pop(session_id, None)
            return removed is not None


session_store = InMemorySessionStore()
