"""Configuration for the experimental conversational prototype.

Everything is read from environment variables at startup and validated fail-closed, like the
transport's ``ApiConfig``. Paid provider calls are opt-in: the default provider is ``none``, which
never contacts a model. The OpenAI API key is deliberately *not* a field here, so it can never
appear in a settings repr, log line, or status payload; the provider reads it directly from the
environment (see ``openai_provider.py``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

ProviderName = Literal["none", "openai"]

PROVIDERS: tuple[str, ...] = ("none", "openai")
REASONING_EFFORTS: tuple[str, ...] = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)
OMIT = "omit"

DEFAULT_OPENAI_MODEL = "gpt-5.5"


@dataclass(frozen=True)
class ChatSettings:
    """Resolved chat settings. Bounds keep requests, tokens, retries, and state finite."""

    provider: ProviderName = "none"
    openai_model: str = DEFAULT_OPENAI_MODEL
    # ``None`` means the ``reasoning`` parameter is not sent (for non-reasoning models).
    openai_reasoning_effort: str | None = "low"
    openai_max_output_tokens: int = 3000
    openai_timeout_s: float = 60.0
    openai_max_retries: int = 1
    openai_max_requests: int = 50
    max_sessions: int = 100
    max_turns_per_session: int = 30
    session_ttl_s: int = 3600
    history_turns: int = 6
    top_k: int = 3
    max_evidence_passages: int = 6

    def __post_init__(self) -> None:
        if self.provider not in PROVIDERS:
            raise ValueError(f"chat provider must be one of {PROVIDERS}, got {self.provider!r}")
        if not self.openai_model.strip():
            raise ValueError("openai model must not be blank")
        effort = self.openai_reasoning_effort
        if effort is not None and effort not in REASONING_EFFORTS:
            raise ValueError(
                f"reasoning effort must be one of {REASONING_EFFORTS} or {OMIT!r}, got {effort!r}"
            )
        _check_range("openai_max_output_tokens", self.openai_max_output_tokens, 256, 16000)
        _check_range("openai_timeout_s", self.openai_timeout_s, 1, 300)
        _check_range("openai_max_retries", self.openai_max_retries, 0, 3)
        _check_range("openai_max_requests", self.openai_max_requests, 1, 10000)
        _check_range("max_sessions", self.max_sessions, 1, 10000)
        _check_range("max_turns_per_session", self.max_turns_per_session, 1, 500)
        _check_range("session_ttl_s", self.session_ttl_s, 60, 86400)
        _check_range("history_turns", self.history_turns, 0, 20)
        _check_range("top_k", self.top_k, 1, 10)
        _check_range("max_evidence_passages", self.max_evidence_passages, self.top_k, 20)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ChatSettings:
        """Build settings from ``BIOTECH_RAG_CHAT_*`` / ``BIOTECH_RAG_OPENAI_*`` variables."""
        env = os.environ if env is None else env

        def text(name: str) -> str:
            return env.get(name, "").strip()

        effort_raw = text("BIOTECH_RAG_OPENAI_REASONING_EFFORT").lower() or "low"
        effort = None if effort_raw == OMIT else effort_raw
        defaults = cls()
        return cls(
            provider=(text("BIOTECH_RAG_CHAT_PROVIDER").lower() or "none"),  # type: ignore[arg-type]
            openai_model=text("BIOTECH_RAG_OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
            openai_reasoning_effort=effort,
            openai_max_output_tokens=_int(
                env, "BIOTECH_RAG_OPENAI_MAX_OUTPUT_TOKENS", defaults.openai_max_output_tokens
            ),
            openai_timeout_s=_float(env, "BIOTECH_RAG_OPENAI_TIMEOUT_S", defaults.openai_timeout_s),
            openai_max_retries=_int(
                env, "BIOTECH_RAG_OPENAI_MAX_RETRIES", defaults.openai_max_retries
            ),
            openai_max_requests=_int(
                env, "BIOTECH_RAG_OPENAI_MAX_REQUESTS", defaults.openai_max_requests
            ),
            max_sessions=_int(env, "BIOTECH_RAG_CHAT_MAX_SESSIONS", defaults.max_sessions),
            max_turns_per_session=_int(
                env, "BIOTECH_RAG_CHAT_MAX_TURNS", defaults.max_turns_per_session
            ),
            session_ttl_s=_int(env, "BIOTECH_RAG_CHAT_SESSION_TTL_S", defaults.session_ttl_s),
            history_turns=_int(env, "BIOTECH_RAG_CHAT_HISTORY_TURNS", defaults.history_turns),
            top_k=_int(env, "BIOTECH_RAG_CHAT_TOP_K", defaults.top_k),
            max_evidence_passages=_int(
                env, "BIOTECH_RAG_CHAT_MAX_EVIDENCE", defaults.max_evidence_passages
            ),
        )

    def public_limits(self) -> dict[str, object]:
        """Bounds that are safe to show to a client (no credentials)."""
        return {
            "max_output_tokens": self.openai_max_output_tokens,
            "timeout_s": self.openai_timeout_s,
            "max_retries": self.openai_max_retries,
            "max_provider_requests_per_process": self.openai_max_requests,
            "max_sessions": self.max_sessions,
            "max_turns_per_session": self.max_turns_per_session,
            "session_ttl_s": self.session_ttl_s,
            "history_turns_sent": self.history_turns,
            "top_k": self.top_k,
            "max_evidence_passages": self.max_evidence_passages,
        }


def _check_range(name: str, value: float, low: float, high: float) -> None:
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


def _int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc
