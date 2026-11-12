"""Provider boundary for generated explanations.

The chat engine talks to a model only through ``ChatProvider``: one structured-output request in,
one text result (or one typed ``ProviderError``) out. Keeping the boundary this small lets tests
swap in a scripted provider, keeps SDK details out of the evidence logic, and gives the UI a closed
set of failure states to render.

Error messages shown to users are fixed strings per kind. Upstream error text is only kept as
``detail`` after secret redaction, because provider messages can echo key fragments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

ProviderErrorKind = Literal[
    "not_configured",
    "missing_credentials",
    "sdk_unavailable",
    "budget_exhausted",
    "timeout",
    "rate_limited",
    "connection_error",
    "auth_failed",
    "bad_request",
    "upstream_error",
    "refused",
    "incomplete",
    "malformed_output",
]

# Kinds that mean "no provider can be used in this process as configured" (rendered as an
# unavailable-provider state rather than a per-turn failure).
UNAVAILABLE_KINDS: frozenset[str] = frozenset(
    {"not_configured", "missing_credentials", "sdk_unavailable", "budget_exhausted"}
)

USER_MESSAGES: dict[str, str] = {
    "not_configured": (
        "No explanation provider is configured. Set BIOTECH_RAG_CHAT_PROVIDER=openai and "
        "OPENAI_API_KEY on the server to enable generated explanations."
    ),
    "missing_credentials": (
        "The OpenAI provider is selected but OPENAI_API_KEY is not set on the server."
    ),
    "sdk_unavailable": (
        "The OpenAI Python SDK is not installed. Install it with: pip install -e '.[chat]'"
    ),
    "budget_exhausted": (
        "This server process has used its configured provider request budget "
        "(BIOTECH_RAG_OPENAI_MAX_REQUESTS). Restart the server to reset it."
    ),
    "timeout": "The model request timed out.",
    "rate_limited": "The model provider rate-limited this request. Wait and try again.",
    "connection_error": "The server could not reach the model provider.",
    "auth_failed": "The model provider rejected the server's credentials.",
    "bad_request": "The model provider rejected the request as invalid.",
    "upstream_error": "The model provider returned an error.",
    "refused": "The model declined to answer this request.",
    "incomplete": "The model stopped before finishing its answer.",
    "malformed_output": (
        "The model's output did not match the required answer format, so it was not shown."
    ),
}

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-*]{6,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-*]{6,}"),
)


def redact_secrets(text: str | None, *, known: tuple[str, ...] = ()) -> str | None:
    """Remove API-key-shaped strings (and any exactly known secret) from ``text``."""
    if text is None:
        return None
    for secret in known:
        if secret:
            text = text.replace(secret, "[redacted]")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ProviderTraceMeta:
    """Identity and cost metadata reported by the provider, kept even when a call fails."""

    model_reported: str | None = None
    response_id: str | None = None
    usage: ProviderUsage | None = None
    latency_ms: int | None = None


class ProviderError(Exception):
    """A typed provider failure. ``message`` is a fixed, user-safe string for ``kind``."""

    def __init__(
        self,
        kind: ProviderErrorKind,
        *,
        detail: str | None = None,
        http_status: int | None = None,
        meta: ProviderTraceMeta | None = None,
    ) -> None:
        self.kind: ProviderErrorKind = kind
        self.message = USER_MESSAGES[kind]
        self.detail = redact_secrets(detail)
        self.http_status = http_status
        self.meta = meta or ProviderTraceMeta()
        super().__init__(f"{kind}: {self.message}")


@dataclass(frozen=True)
class ProviderAvailability:
    available: bool
    provider: str
    model: str | None
    reason: str | None = None
    message: str = ""
    store: bool | None = None

    def to_record(self) -> dict[str, object]:
        return {
            "available": self.available,
            "provider": self.provider,
            "model": self.model,
            "reason": self.reason,
            "message": self.message,
            "store": self.store,
        }


@dataclass(frozen=True)
class ProviderRequest:
    """One structured-output generation request, fully built by the application."""

    instructions: str
    input: list[dict[str, str]]
    schema_name: str
    json_schema: dict[str, object]
    max_output_tokens: int


@dataclass(frozen=True)
class ProviderResult:
    output_text: str
    provider: str
    model_requested: str
    meta: ProviderTraceMeta = field(default_factory=ProviderTraceMeta)
    store: bool | None = None


class ChatProvider(Protocol):
    """The only interface the chat engine uses to reach a model."""

    name: str

    def availability(self) -> ProviderAvailability: ...

    def generate(self, request: ProviderRequest) -> ProviderResult: ...


class UnconfiguredProvider:
    """Default provider: never contacts a model, always reports the not-configured state."""

    name = "none"

    def availability(self) -> ProviderAvailability:
        return ProviderAvailability(
            available=False,
            provider=self.name,
            model=None,
            reason="not_configured",
            message=USER_MESSAGES["not_configured"],
        )

    def generate(self, request: ProviderRequest) -> ProviderResult:
        raise ProviderError("not_configured")
