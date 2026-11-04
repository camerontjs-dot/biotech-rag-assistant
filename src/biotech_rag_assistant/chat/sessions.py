"""In-memory, bounded, isolated conversation state.

Sessions live only in server memory: nothing is persisted, and a restart forgets every
conversation. Each session is reachable only by its unguessable id (144 random bits); there is
no route that lists sessions. The store is bounded by a maximum session count (least recently
used is evicted first) and an idle time-to-live; turns per session are bounded by the engine
caller. A per-session lock rejects a second concurrent turn instead of interleaving history.
"""

from __future__ import annotations

import re
import secrets
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from biotech_rag_assistant.chat.resolution import ActiveTopic

if TYPE_CHECKING:
    from biotech_rag_assistant.chat.engine import TurnRecord

SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{16,64}$"
_SESSION_ID_RE = re.compile(SESSION_ID_PATTERN)


@dataclass
class Session:
    session_id: str
    corpus: str
    snapshot_id: str
    created_at: str
    last_active: float
    turns: list[TurnRecord] = field(default_factory=list)
    active_topic: ActiveTopic | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class SessionStore:
    def __init__(
        self,
        *,
        max_sessions: int,
        ttl_s: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_sessions = max_sessions
        self.ttl_s = ttl_s
        self._clock = clock
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)

    def create(self, *, corpus: str, snapshot_id: str) -> Session:
        with self._lock:
            self._evict_expired()
            while len(self._sessions) >= self.max_sessions:
                self._sessions.popitem(last=False)
            session_id = secrets.token_urlsafe(18)
            session = Session(
                session_id=session_id,
                corpus=corpus,
                snapshot_id=snapshot_id,
                created_at=datetime.now(UTC).isoformat(timespec="seconds"),
                last_active=self._clock(),
            )
            self._sessions[session_id] = session
            return session

    def get(self, session_id: str) -> Session | None:
        if not _SESSION_ID_RE.match(session_id):
            return None
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self._clock() - session.last_active > self.ttl_s:
                del self._sessions[session_id]
                return None
            session.last_active = self._clock()
            self._sessions.move_to_end(session_id)
            return session

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _evict_expired(self) -> None:
        now = self._clock()
        expired = [
            key for key, session in self._sessions.items() if now - session.last_active > self.ttl_s
        ]
        for key in expired:
            del self._sessions[key]
