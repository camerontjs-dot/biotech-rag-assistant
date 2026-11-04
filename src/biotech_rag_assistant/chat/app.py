"""Experimental chat app, composed over the unchanged transport and demo page.

``create_chat_app`` builds the maintained app (``create_demo_app`` → ``create_app``, ADR-010) and
adds a separate ``/chat`` surface beside it. The maintained routes, including the deterministic
``/answer`` contract, are the same code and stay available as the regression baseline. Every chat
API route uses the transport's API-key dependency and is audited by its middleware.

There is no module-level app here, so importing this module never builds a provider. Run it
with ``biotech-rag chat`` or
``uvicorn --factory biotech_rag_assistant.chat.app:create_chat_app_from_env``.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.api.security import require_api_key
from biotech_rag_assistant.api.webui import create_demo_app
from biotech_rag_assistant.chat.engine import ChatEngine, TurnRecord
from biotech_rag_assistant.chat.evidence import CorpusBinding, EvidenceBoundaryError
from biotech_rag_assistant.chat.openai_provider import OpenAIResponsesProvider
from biotech_rag_assistant.chat.provider import ChatProvider, UnconfiguredProvider
from biotech_rag_assistant.chat.sessions import SESSION_ID_PATTERN, Session, SessionStore
from biotech_rag_assistant.chat.settings import ChatSettings

logger = logging.getLogger("biotech_rag_assistant.chat")

STATIC_DIR = Path(__file__).resolve().parent / "static"
CHAT_HTML = STATIC_DIR / "chat.html"
MAX_MESSAGE_CHARS = 2000


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)
    corpus: str | None = Field(default=None, max_length=200)
    new_topic: bool = False

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


@dataclass(frozen=True)
class ChatState:
    engine: ChatEngine
    store: SessionStore
    settings: ChatSettings
    provider: ChatProvider


def build_provider(
    settings: ChatSettings, env: Mapping[str, str] | None = None
) -> ChatProvider:
    """Construct the configured provider. Only ``openai`` can make paid calls (opt-in)."""
    if settings.provider == "openai":
        return OpenAIResponsesProvider.from_settings(settings, env)
    return UnconfiguredProvider()


def create_chat_app(
    config: ApiConfig | None = None,
    settings: ChatSettings | None = None,
    provider: ChatProvider | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> FastAPI:
    config = config or ApiConfig.from_env(env)
    settings = settings or ChatSettings.from_env(env)
    app = create_demo_app(config)
    provider = provider if provider is not None else build_provider(settings, env)
    loaded_at = datetime.now(UTC)
    bindings = {
        name: CorpusBinding.build(name, corpus, app.state.retrievers[name], loaded_at)
        for name, corpus in app.state.corpora.items()
    }
    state = ChatState(
        engine=ChatEngine(bindings, provider, settings),
        store=SessionStore(max_sessions=settings.max_sessions, ttl_s=settings.session_ttl_s),
        settings=settings,
        provider=provider,
    )
    app.state.chat = state

    @app.get("/chat", include_in_schema=False)
    async def chat_page() -> FileResponse:
        return FileResponse(CHAT_HTML, media_type="text/html")

    @app.get("/chat/status", dependencies=[Depends(require_api_key)])
    def chat_status(request: Request) -> dict[str, Any]:
        request.state.audit_summary = {"chat": "status"}
        return {
            "experimental": True,
            "support_scope": "mechanical_only",
            "provider": state.provider.availability().to_record(),
            "limits": {**state.settings.public_limits(), "max_message_chars": MAX_MESSAGE_CHARS},
            "default_corpus": config.default_corpus,
            "corpora": {
                name: binding.snapshot.model_dump()
                for name, binding in state.engine.bindings.items()
            },
        }

    @app.post("/chat", dependencies=[Depends(require_api_key)])
    def chat_turn(request: Request, body: ChatRequest) -> dict[str, Any]:
        session = _session_for(state, config, body)
        if len(session.turns) >= state.settings.max_turns_per_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="this conversation reached its turn limit; start a new conversation",
            )
        if not session.lock.acquire(blocking=False):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="a turn is already in progress for this conversation",
            )
        try:
            turn = state.engine.run_turn(session, body.message.strip(), new_topic=body.new_topic)
        except EvidenceBoundaryError as exc:
            logger.error("chat evidence boundary failure: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="evidence boundary check failed; no answer was produced",
            ) from exc
        finally:
            session.lock.release()
        request.state.audit_summary = _audit(session, turn)
        binding = state.engine.bindings[session.corpus]
        return {
            "session_id": session.session_id,
            "turn": turn.model_dump(mode="json"),
            "corpus_snapshot": binding.snapshot.model_dump(),
            "provider_status": state.provider.availability().to_record(),
            "turns_used": len(session.turns),
            "max_turns": state.settings.max_turns_per_session,
        }

    @app.get("/chat/sessions/{session_id}", dependencies=[Depends(require_api_key)])
    def chat_session(request: Request, session_id: str) -> dict[str, Any]:
        session = state.store.get(session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown session")
        request.state.audit_summary = {
            "chat": "session_read",
            "session": session_ref(session.session_id),
            "turns": len(session.turns),
        }
        return {
            "session_id": session.session_id,
            "corpus": session.corpus,
            "corpus_snapshot_id": session.snapshot_id,
            "created_at": session.created_at,
            "turns": [turn.model_dump(mode="json") for turn in session.turns],
        }

    @app.delete("/chat/sessions/{session_id}", dependencies=[Depends(require_api_key)])
    def chat_session_delete(request: Request, session_id: str) -> Response:
        removed = state.store.delete(session_id)
        request.state.audit_summary = {
            "chat": "session_delete",
            "session": session_ref(session_id),
            "removed": removed,
        }
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown session")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/chat/documents/{doc_id}", dependencies=[Depends(require_api_key)])
    def chat_document(request: Request, doc_id: str, corpus: str | None = None) -> dict[str, Any]:
        """Full text of an admitted (Approved/Effective) document, for viewing a passage in context.

        Held-out documents are not served: the chat surface never displays retired content.
        """
        binding = _binding(state, config, corpus)
        document = next(
            (d for d in binding.corpus.retrievable_documents if d.metadata.doc_id == doc_id),
            None,
        )
        request.state.audit_summary = {
            "chat": "document",
            "corpus": binding.name,
            "doc_id": doc_id,
            "found": document is not None,
        }
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="no admitted document with that id"
            )
        metadata = document.metadata
        return {
            "corpus": binding.name,
            "corpus_snapshot_id": binding.snapshot.snapshot_id,
            "doc_id": metadata.doc_id,
            "doc_title": metadata.doc_title,
            "version": metadata.version,
            "status": metadata.status,
            "effective_date": metadata.effective_date.isoformat(),
            "source_file_path": str(metadata.source_file_path),
            "source_hash": metadata.source_hash,
            "text": document.raw_text,
            "passages": [
                {
                    "chunk_id": chunk.chunk_id,
                    "section_heading": chunk.section_heading,
                    "line_or_page_span": chunk.line_or_page_span,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                }
                for chunk in binding.retriever.chunks
                if chunk.doc_id == metadata.doc_id
            ],
        }

    return app


def create_chat_app_from_env() -> FastAPI:
    """Factory for ``uvicorn --factory``."""
    return create_chat_app()


def session_ref(session_id: str) -> str:
    """A log-safe reference: correlates turns without recording the session capability."""
    return "sha256:" + hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:12]


def _binding(state: ChatState, config: ApiConfig, corpus: str | None) -> CorpusBinding:
    name = corpus or config.default_corpus
    binding = state.engine.bindings.get(name)
    if binding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown corpus: {name}")
    return binding


def _session_for(state: ChatState, config: ApiConfig, body: ChatRequest) -> Session:
    if body.session_id is None:
        binding = _binding(state, config, body.corpus)
        return state.store.create(corpus=binding.name, snapshot_id=binding.snapshot.snapshot_id)
    session = state.store.get(body.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unknown or expired conversation; start a new conversation",
        )
    if body.corpus is not None and body.corpus != session.corpus:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"this conversation is bound to corpus {session.corpus!r}",
        )
    return session


def _audit(session: Session, turn: TurnRecord) -> dict[str, Any]:
    answer = turn.answer
    return {
        "chat": "turn",
        "corpus": session.corpus,
        "corpus_snapshot_id": turn.corpus_snapshot_id,
        "session": session_ref(session.session_id),
        "turn_index": turn.turn_index,
        "query": turn.user_message,
        "resolution": turn.resolution.kind,
        "retrieval_queries": [attempt.query for attempt in turn.resolution.attempts],
        "evidence_chunk_ids": [passage.chunk_id for passage in turn.evidence],
        "held_out_doc_ids": [pointer.doc_id for pointer in turn.held_out],
        "outcome": turn.outcome,
        "provider": turn.provider.provider,
        "provider_called": turn.provider.called,
        "model_requested": turn.provider.model_requested,
        "model_reported": turn.provider.model_reported,
        "provider_error_kind": turn.provider.error_kind,
        "usage": turn.provider.usage,
        "withheld_count": answer.withheld_count if answer else None,
        "unknown_refs": answer.unknown_refs if answer else None,
    }
