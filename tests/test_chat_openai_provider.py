"""The OpenAI adapter, exercised through the real ``openai`` SDK with an in-process transport.

No network and no credentials: ``httpx2.MockTransport`` answers inside the process, so the SDK's
own request serialization, response parsing, retry policy, and exception classes are what is
tested. These tests pin what the application sends (``store: false``, strict JSON schema, bounded
tokens, configured model) and how each failure maps to a provider state. They establish
application behavior only, not live model quality.
"""

from __future__ import annotations

import builtins
import json
from typing import Any

import pytest

openai = pytest.importorskip("openai")
httpx2 = pytest.importorskip("httpx2")

from biotech_rag_assistant.chat.openai_provider import OpenAIResponsesProvider  # noqa: E402
from biotech_rag_assistant.chat.provider import ProviderError, ProviderRequest  # noqa: E402
from biotech_rag_assistant.chat.settings import ChatSettings  # noqa: E402

FAKE_KEY = "sk-test-not-a-real-key-0000000000"
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ok"],
    "properties": {"ok": {"type": "string"}},
}


def provider_request(max_output_tokens: int = 5000) -> ProviderRequest:
    return ProviderRequest(
        instructions="rules",
        input=[{"role": "user", "content": "question"}],
        schema_name="controlled_document_answer",
        json_schema=SCHEMA,
        max_output_tokens=max_output_tokens,
    )


def response_body(
    *,
    status: str = "completed",
    content: list[dict[str, Any]] | None = None,
    incomplete: str | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": "resp_mock_1",
        "object": "response",
        "created_at": 1.0,
        "status": status,
        "model": "gpt-5.5-2026-04-23",
        "output": [
            {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": content
                if content is not None
                else [{"type": "output_text", "text": '{"ok": "yes"}', "annotations": []}],
            }
        ],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "usage": {
            "input_tokens": 120,
            "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
            "output_tokens": 40,
            "output_tokens_details": {"reasoning_tokens": 12},
            "total_tokens": 160,
        },
        "error": error,
        "incomplete_details": {"reason": incomplete} if incomplete else None,
    }


class Transport:
    """Records every HTTP request and answers with a fixed handler."""

    def __init__(self, handler: Any) -> None:
        self.requests: list[Any] = []
        self._handler = handler

    def __call__(self, request: Any) -> Any:
        self.requests.append(request)
        return self._handler(request)

    @property
    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(request.content) for request in self.requests]


def json_response(body: dict[str, Any], status_code: int = 200, **headers: str) -> Any:
    return lambda request: httpx2.Response(status_code, json=body, headers=headers)


def error_response(status_code: int, message: str) -> Any:
    return json_response(
        {"error": {"message": message, "type": "error", "code": None}},
        status_code,
        **{"retry-after-ms": "1"},
    )


def make_provider(
    handler: Any, env: dict[str, str] | None = None, **settings: Any
) -> tuple[OpenAIResponsesProvider, Transport]:
    transport = Transport(handler)
    provider = OpenAIResponsesProvider.from_settings(
        ChatSettings(provider="openai", **settings),
        {"OPENAI_API_KEY": FAKE_KEY} if env is None else env,
        http_client=httpx2.Client(transport=httpx2.MockTransport(transport)),
    )
    return provider, transport


def test_request_sends_store_false_strict_schema_and_bounds() -> None:
    provider, transport = make_provider(json_response(response_body()))
    provider.generate(provider_request(max_output_tokens=5000))

    body = transport.bodies[0]
    assert transport.requests[0].url.path.endswith("/responses")
    assert body["store"] is False
    assert body["model"] == "gpt-5.5"
    assert body["instructions"] == "rules"
    assert body["input"] == [{"role": "user", "content": "question"}]
    assert body["text"] == {
        "format": {
            "type": "json_schema",
            "name": "controlled_document_answer",
            "schema": SCHEMA,
            "strict": True,
        }
    }
    # The configured bound (3000) caps a larger per-request value.
    assert body["max_output_tokens"] == 3000
    assert body["reasoning"] == {"effort": "low"}
    # Application-managed state only: no server-side conversation, no tools, no sampling knobs.
    for absent in ("previous_response_id", "conversation", "tools", "temperature", "background"):
        assert absent not in body


def test_model_and_reasoning_are_configurable() -> None:
    provider, transport = make_provider(
        json_response(response_body()), openai_model="gpt-5.4-mini", openai_reasoning_effort=None
    )
    provider.generate(provider_request())

    assert transport.bodies[0]["model"] == "gpt-5.4-mini"
    assert "reasoning" not in transport.bodies[0]


def test_result_records_requested_and_reported_model_and_usage() -> None:
    provider, _ = make_provider(json_response(response_body()))
    result = provider.generate(provider_request())

    assert result.output_text == '{"ok": "yes"}'
    assert result.model_requested == "gpt-5.5"
    assert result.meta.model_reported == "gpt-5.5-2026-04-23"
    assert result.meta.response_id == "resp_mock_1"
    assert result.meta.usage is not None
    assert (result.meta.usage.input_tokens, result.meta.usage.output_tokens) == (120, 40)
    assert result.meta.usage.reasoning_tokens == 12
    assert result.store is False


def test_refusal_maps_to_refused_and_keeps_usage() -> None:
    content = [{"type": "refusal", "refusal": "I can't help with that request."}]
    provider, _ = make_provider(json_response(response_body(content=content)))

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "refused"
    assert "can't help" in (caught.value.detail or "")
    assert caught.value.meta.model_reported == "gpt-5.5-2026-04-23"
    assert caught.value.meta.usage is not None


def test_incomplete_response_maps_to_incomplete() -> None:
    body = response_body(status="incomplete", incomplete="max_output_tokens")
    provider, _ = make_provider(json_response(body))

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "incomplete"
    assert "max_output_tokens" in (caught.value.detail or "")


def test_failed_response_maps_to_upstream_error() -> None:
    body = response_body(status="failed", error={"code": "server_error", "message": "boom"})
    provider, _ = make_provider(json_response(body))

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "upstream_error"


def test_empty_output_maps_to_malformed() -> None:
    content = [{"type": "output_text", "text": "", "annotations": []}]
    provider, _ = make_provider(json_response(response_body(content=content)))

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "malformed_output"


def test_rate_limit_is_retried_within_the_configured_bound() -> None:
    provider, transport = make_provider(error_response(429, "Rate limit reached"))

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "rate_limited"
    assert caught.value.http_status == 429
    assert len(transport.requests) == 1 + ChatSettings().openai_max_retries


def test_retries_can_be_disabled() -> None:
    provider, transport = make_provider(error_response(500, "boom"), openai_max_retries=0)

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "upstream_error"
    assert len(transport.requests) == 1


def test_timeout_maps_to_timeout_and_is_bounded() -> None:
    def handler(request: Any) -> Any:
        raise httpx2.ReadTimeout("simulated read timeout", request=request)

    provider, transport = make_provider(handler)

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "timeout"
    assert len(transport.requests) <= 1 + ChatSettings().openai_max_retries


def test_connection_failure_maps_to_connection_error() -> None:
    def handler(request: Any) -> Any:
        raise httpx2.ConnectError("simulated connect failure", request=request)

    provider, _ = make_provider(handler, openai_max_retries=0)

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "connection_error"


def test_auth_failure_never_echoes_key_fragments() -> None:
    provider, transport = make_provider(
        error_response(401, f"Incorrect API key provided: {FAKE_KEY[:8]}****0000.")
    )

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    error = caught.value
    assert error.kind == "auth_failed"
    assert error.detail == "HTTP 401"
    assert "sk-" not in f"{error} {error.message} {error.detail}"
    assert len(transport.requests) == 1  # 401 is not retried


def test_bad_request_detail_is_redacted() -> None:
    provider, _ = make_provider(error_response(400, "Unsupported parameter (key sk-abcdef123456)"))

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "bad_request"
    assert "sk-abcdef" not in (caught.value.detail or "")
    assert "[redacted]" in (caught.value.detail or "")


def test_missing_credentials_is_unavailable_and_sends_nothing() -> None:
    provider, transport = make_provider(json_response(response_body()), env={})

    availability = provider.availability()
    assert (availability.available, availability.reason) == (False, "missing_credentials")
    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())
    assert caught.value.kind == "missing_credentials"
    assert transport.requests == []


def test_missing_sdk_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "openai":
            raise ImportError("simulated missing SDK")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    provider = OpenAIResponsesProvider.from_settings(
        ChatSettings(provider="openai"), {"OPENAI_API_KEY": FAKE_KEY}
    )

    assert provider.availability().reason == "sdk_unavailable"


def test_request_budget_is_enforced_before_sending() -> None:
    provider, transport = make_provider(json_response(response_body()), openai_max_requests=2)
    provider.generate(provider_request())
    provider.generate(provider_request())

    with pytest.raises(ProviderError) as caught:
        provider.generate(provider_request())

    assert caught.value.kind == "budget_exhausted"
    assert len(transport.requests) == 2
    assert provider.availability().reason == "budget_exhausted"


def test_repr_and_availability_never_contain_the_key() -> None:
    provider, _ = make_provider(json_response(response_body()))

    assert FAKE_KEY not in repr(provider)
    assert FAKE_KEY not in json.dumps(provider.availability().to_record())
    assert not any(FAKE_KEY in str(value) for value in vars(provider).values())
