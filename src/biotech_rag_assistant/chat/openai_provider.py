"""OpenAI Responses API provider for the conversational prototype.

Checked against the official ``openai`` Python SDK 3.x (generated from OpenAI's OpenAPI spec):

- ``store`` defaults to true when omitted, and stored responses are kept for at least 30 days, so
  every request sends ``store=False``. The application keeps conversation state itself; no
  ``previous_response_id`` or ``conversation`` object is used.
- ``text.format`` with ``type: json_schema`` and ``strict: true`` constrains output to the answer
  schema built per turn.
- ``max_output_tokens`` bounds visible plus reasoning tokens.
- The client's own defaults (10-minute timeout, 2 retries) are replaced by configured bounds.

The API key is read from the environment once, handed to the SDK client, and never stored on
this object, logged, or echoed in errors.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Mapping
from typing import Any

from biotech_rag_assistant.chat.provider import (
    USER_MESSAGES,
    ProviderAvailability,
    ProviderError,
    ProviderRequest,
    ProviderResult,
    ProviderTraceMeta,
    ProviderUsage,
    redact_secrets,
)
from biotech_rag_assistant.chat.settings import ChatSettings


class OpenAIResponsesProvider:
    """Structured-output generation through ``client.responses.create``."""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        reasoning_effort: str | None,
        max_output_tokens: int,
        timeout_s: float,
        max_retries: int,
        max_requests: int,
        http_client: Any = None,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_output_tokens = max_output_tokens
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.max_requests = max_requests
        self._lock = threading.Lock()
        self._requests_started = 0
        self._client: Any = None
        self._openai: Any = None
        self._unavailable_reason: str | None = None

        if not api_key:
            self._unavailable_reason = "missing_credentials"
            return
        try:
            import openai
        except ImportError:
            self._unavailable_reason = "sdk_unavailable"
            return
        self._openai = openai
        self._client = openai.OpenAI(
            api_key=api_key,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )

    @classmethod
    def from_settings(
        cls,
        settings: ChatSettings,
        env: Mapping[str, str] | None = None,
        *,
        http_client: Any = None,
    ) -> OpenAIResponsesProvider:
        env = os.environ if env is None else env
        return cls(
            api_key=(env.get("OPENAI_API_KEY") or "").strip() or None,
            model=settings.openai_model,
            reasoning_effort=settings.openai_reasoning_effort,
            max_output_tokens=settings.openai_max_output_tokens,
            timeout_s=settings.openai_timeout_s,
            max_retries=settings.openai_max_retries,
            max_requests=settings.openai_max_requests,
            http_client=http_client,
        )

    def __repr__(self) -> str:  # never include credentials
        return f"OpenAIResponsesProvider(model={self.model!r}, store=False)"

    @property
    def requests_started(self) -> int:
        return self._requests_started

    def availability(self) -> ProviderAvailability:
        reason = self._unavailable_reason
        if reason is None and self._requests_started >= self.max_requests:
            reason = "budget_exhausted"
        if reason is not None:
            return ProviderAvailability(
                available=False,
                provider=self.name,
                model=self.model,
                reason=reason,
                message=USER_MESSAGES[reason],
                store=False,
            )
        return ProviderAvailability(
            available=True,
            provider=self.name,
            model=self.model,
            message=f"OpenAI Responses API, model {self.model}, store=false",
            store=False,
        )

    def build_create_kwargs(self, request: ProviderRequest) -> dict[str, Any]:
        """Exact keyword arguments sent to ``client.responses.create`` (inspectable in tests)."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "instructions": request.instructions,
            "input": request.input,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": request.schema_name,
                    "schema": request.json_schema,
                    "strict": True,
                }
            },
            "max_output_tokens": min(request.max_output_tokens, self.max_output_tokens),
            "store": False,
        }
        if self.reasoning_effort is not None:
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        return kwargs

    def generate(self, request: ProviderRequest) -> ProviderResult:
        if self._unavailable_reason is not None:
            raise ProviderError(self._unavailable_reason)  # type: ignore[arg-type]
        with self._lock:
            if self._requests_started >= self.max_requests:
                raise ProviderError("budget_exhausted")
            # Counted before sending: a failed or timed-out call may still have been billed.
            self._requests_started += 1

        openai = self._openai
        started = time.monotonic()
        try:
            response = self._client.responses.create(**self.build_create_kwargs(request))
        except openai.APITimeoutError as exc:
            raise ProviderError("timeout", detail=_safe(exc), meta=_elapsed(started)) from exc
        except openai.RateLimitError as exc:
            raise ProviderError(
                "rate_limited", http_status=429, detail=_safe(exc), meta=_elapsed(started)
            ) from exc
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            # Upstream auth messages can echo a masked key fragment; keep only the status.
            raise ProviderError(
                "auth_failed",
                http_status=exc.status_code,
                detail=f"HTTP {exc.status_code}",
                meta=_elapsed(started),
            ) from exc
        except (
            openai.BadRequestError,
            openai.NotFoundError,
            openai.UnprocessableEntityError,
        ) as exc:
            raise ProviderError(
                "bad_request",
                http_status=exc.status_code,
                detail=_safe(exc),
                meta=_elapsed(started),
            ) from exc
        except openai.APIConnectionError as exc:
            raise ProviderError(
                "connection_error", detail=_safe(exc), meta=_elapsed(started)
            ) from exc
        except openai.APIStatusError as exc:
            raise ProviderError(
                "upstream_error",
                http_status=exc.status_code,
                detail=_safe(exc),
                meta=_elapsed(started),
            ) from exc
        except openai.OpenAIError as exc:
            raise ProviderError(
                "upstream_error", detail=_safe(exc), meta=_elapsed(started)
            ) from exc

        meta = ProviderTraceMeta(
            model_reported=_str_or_none(getattr(response, "model", None)),
            response_id=_str_or_none(getattr(response, "id", None)),
            usage=_usage(getattr(response, "usage", None)),
            latency_ms=int((time.monotonic() - started) * 1000),
        )

        refusal = _first_refusal(response)
        if refusal is not None:
            raise ProviderError("refused", detail=refusal, meta=meta)

        status = getattr(response, "status", None)
        if status == "incomplete":
            details = getattr(response, "incomplete_details", None)
            reason = getattr(details, "reason", None) or "unknown"
            raise ProviderError("incomplete", detail=f"incomplete reason: {reason}", meta=meta)
        if status == "failed":
            error = getattr(response, "error", None)
            message = getattr(error, "message", None) or "response status failed"
            raise ProviderError("upstream_error", detail=str(message), meta=meta)
        if status != "completed":
            raise ProviderError(
                "upstream_error", detail=f"unexpected response status: {status}", meta=meta
            )

        text = response.output_text
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("malformed_output", detail="empty output_text", meta=meta)

        return ProviderResult(
            output_text=text,
            provider=self.name,
            model_requested=self.model,
            meta=meta,
            store=False,
        )


def _safe(exc: Exception) -> str:
    return redact_secrets(f"{type(exc).__name__}: {exc}") or type(exc).__name__


def _elapsed(started: float) -> ProviderTraceMeta:
    return ProviderTraceMeta(latency_ms=int((time.monotonic() - started) * 1000))


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _usage(usage: Any) -> ProviderUsage | None:
    if usage is None:
        return None
    details = getattr(usage, "output_tokens_details", None)
    return ProviderUsage(
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        reasoning_tokens=getattr(details, "reasoning_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
    )


def _first_refusal(response: Any) -> str | None:
    for item in getattr(response, "output", None) or []:
        if getattr(item, "type", None) != "message":
            continue
        for content in getattr(item, "content", None) or []:
            if getattr(content, "type", None) == "refusal":
                return str(getattr(content, "refusal", "") or "refused")
    return None
