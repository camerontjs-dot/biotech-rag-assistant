"""The live smoke harness (``scripts/chat_live_smoke.py``), run offline against a stand-in.

The stand-in is the real ``openai`` SDK over an in-process ``httpx2.MockTransport`` that answers
with the hand-written scenario outputs in ``scripts/chat_scenarios.py``. No network, credentials,
or spending. These tests pin the harness's own logic (request bounds, transcript, PASS/FAIL lines,
exit codes) so that a run in which every call is rejected, malformed, or refused cannot report
success. They say nothing about live model quality.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

openai = pytest.importorskip("openai")
httpx2 = pytest.importorskip("httpx2")

from biotech_rag_assistant.chat.prompting import parse_payload  # noqa: E402
from biotech_rag_assistant.chat.provider import ProviderRequest  # noqa: E402
from biotech_rag_assistant.chat.testing import answer, block, find_passage  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STAND_IN_KEY = "sk-test-stand-in-not-a-real-key-0000"


def _load_script(name: str) -> Any:
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{name}_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve string annotations through sys.modules
    spec.loader.exec_module(module)
    return module


SMOKE = _load_script("chat_live_smoke")
SCENARIOS = _load_script("chat_scenarios")
SCRIPTED = {
    "How does QA respond to a viable environmental monitoring excursion?": SCENARIOS.em_response,
    "Who is responsible?": SCENARIOS.em_responsible,
    "Turn the stated procedure into a checklist": SCENARIOS.em_checklist,
    "What is the acceptance range for the analytical balance daily check?": (
        SCENARIOS.balance_not_stated
    ),
    "Our lab uses an acceptance range of 0.5 mg for the daily balance check.": (
        SCENARIOS.user_value_statement
    ),
    "So what is the official acceptance range for the daily balance check?": (
        SCENARIOS.user_value_official
    ),
    "How are printed sample labels reconciled before testing?": SCENARIOS.labels_with_injection,
}
USAGE = {
    "input_tokens": 100,
    "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
    "output_tokens": 40,
    "output_tokens_details": {"reasoning_tokens": 12},
    "total_tokens": 140,
}


def scripted(body: dict[str, Any]) -> str:
    payload = parse_payload(body["input"][-1]["content"])
    fmt = body["text"]["format"]
    request = ProviderRequest(
        instructions=body["instructions"],
        input=body["input"],
        schema_name=fmt["name"],
        json_schema=fmt["schema"],
        max_output_tokens=body["max_output_tokens"],
    )
    return json.dumps(SCRIPTED[payload["current_question"]](request, payload))


def blanket_refusal(body: dict[str, Any]) -> str:
    return json.dumps(
        {
            "status": "out_of_scope",
            "blocks": [],
            "missing_information": [],
            "clarifying_question": "",
        }
    )


def truncated_json(body: dict[str, Any]) -> str:
    return '{"status": "answered", "blocks": ['


def adopts_chat_value(body: dict[str, Any]) -> str:
    """Misbehaves on one turn: states the user's 0.5 mg as the official value."""
    payload = parse_payload(body["input"][-1]["content"])
    if not payload["current_question"].startswith("So what is the official"):
        return scripted(body)
    ref = find_passage(payload, doc_id="CAL-ENG-005", contains="acceptance range")["ref"]
    text = "The official acceptance range for the daily balance check is 0.5 mg."
    quote = "If either weight falls outside the acceptance range"
    return json.dumps(answer("answered", [block("paragraph", text, (ref, quote))]))


class StandIn:
    """Answers like the Responses endpoint and records every request body."""

    def __init__(
        self, reply: Callable[[dict[str, Any]], str] = scripted, status_code: int = 200
    ) -> None:
        self.reply = reply
        self.status_code = status_code
        self.bodies: list[dict[str, Any]] = []

    def __call__(self, request: Any) -> Any:
        body = json.loads(request.content)
        self.bodies.append(body)
        if self.status_code != 200:
            error = {"message": "stand-in error", "type": "invalid_request_error", "code": None}
            return httpx2.Response(self.status_code, json={"error": error})
        return httpx2.Response(
            200,
            json={
                "id": f"resp_stand_in_{len(self.bodies)}",
                "object": "response",
                "created_at": 1.0,
                "status": "completed",
                "model": f"{body['model']}-stand-in",
                "output": [
                    {
                        "id": "msg_stand_in",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "output_text", "text": self.reply(body), "annotations": []}
                        ],
                    }
                ],
                "parallel_tool_calls": True,
                "tool_choice": "auto",
                "tools": [],
                "usage": USAGE,
                "error": None,
                "incomplete_details": None,
            },
        )


def run_smoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stand_in: StandIn, *args: str
) -> tuple[int, Path]:
    for name in list(os.environ):
        if name.startswith("BIOTECH_RAG_"):
            monkeypatch.delenv(name)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", STAND_IN_KEY)
    out = tmp_path / "smoke.json"
    client = httpx2.Client(transport=httpx2.MockTransport(stand_in))
    return SMOKE.main(["--live", "--out", str(out), *args], http_client=client), out


def test_every_smoke_question_that_reaches_a_model_has_a_stand_in_answer() -> None:
    questions = {message for _, _, messages in SMOKE.CONVERSATIONS for message in messages}
    assert set(SCRIPTED) <= questions
    assert questions - set(SCRIPTED) == {"What is the membrane filtration hold time for sterility?"}


def test_a_useful_run_passes_and_records_a_complete_transcript(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stand_in = StandIn()
    code, out = run_smoke(monkeypatch, tmp_path, stand_in)
    printed = capsys.readouterr().out

    assert code == 0, printed
    assert "FAIL" not in printed and printed.count("PASS ") == 8
    assert len(stand_in.bodies) == SMOKE.EXPECTED_CALLS
    for body in stand_in.bodies:
        assert body["store"] is False
        assert body["max_output_tokens"] == 3000
        assert body["text"]["format"]["strict"] is True
    transcript = out.read_text(encoding="utf-8")
    record = json.loads(transcript)
    assert record["endpoint"] == "https://api.openai.com/v1 (SDK default)"
    assert record["logical_requests_started"] == SMOKE.EXPECTED_CALLS
    assert record["models_reported"] == ["gpt-5.5-stand-in"]
    calls = SMOKE.EXPECTED_CALLS
    assert record["usage_totals"] == {
        "input_tokens": 100 * calls,
        "output_tokens": 40 * calls,
        "reasoning_tokens": 12 * calls,
        "total_tokens": 140 * calls,
    }
    assert STAND_IN_KEY not in transcript and STAND_IN_KEY not in printed


@pytest.mark.parametrize(
    ("make_stand_in", "failing_line"),
    [
        (lambda: StandIn(status_code=400), "every model call returned a schema-valid answer (0/7)"),
        (lambda: StandIn(truncated_json), "every model call returned a schema-valid answer (0/7)"),
        (
            lambda: StandIn(blanket_refusal),
            "the supported question shows at least one checked statement",
        ),
    ],
    ids=["every-call-rejected", "malformed-output", "blanket-refusal"],
)
def test_a_vacuous_run_cannot_pass(
    make_stand_in: Callable[[], StandIn],
    failing_line: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _ = run_smoke(monkeypatch, tmp_path, make_stand_in())
    printed = capsys.readouterr().out
    assert code == 1, printed
    assert f"FAIL {failing_line}" in printed


def test_a_model_that_adopts_the_chat_value_is_observed_while_the_guarantee_holds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = run_smoke(monkeypatch, tmp_path, StandIn(adopts_chat_value))
    printed = capsys.readouterr().out
    assert code == 0, printed
    assert "PASS the chat-introduced value 0.5 mg is never shown as document content" in printed
    assert "EXPECT user-value t2: 0.5 mg not adopted (nothing withheld) -> status=answered, " \
        "withheld=1" in printed
    official = json.loads(out.read_text(encoding="utf-8"))["conversations"]["user-value"][-1]
    assert official["answer"]["blocks"][0]["withheld"] is True
    assert official["answer"]["blocks"][0]["text"] is None


def test_auth_failure_on_every_call_is_reported_blocked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _ = run_smoke(monkeypatch, tmp_path, StandIn(status_code=401))
    printed = capsys.readouterr().out
    assert code == 3, printed
    assert "BLOCKED: every model call failed with connection/auth errors." in printed


def test_the_request_bound_holds_and_an_incomplete_run_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stand_in = StandIn()
    code, out = run_smoke(monkeypatch, tmp_path, stand_in, "--max-requests", "5")
    printed = capsys.readouterr().out
    assert len(stand_in.bodies) == 5
    assert code == 1, printed
    assert "FAIL made the 7 expected model calls (made 5)" in printed
    assert json.loads(out.read_text(encoding="utf-8"))["logical_requests_started"] == 5


def test_not_run_paths_send_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stand_in = StandIn()
    client = httpx2.Client(transport=httpx2.MockTransport(stand_in))
    out = tmp_path / "smoke.json"
    monkeypatch.setenv("OPENAI_API_KEY", STAND_IN_KEY)
    assert SMOKE.main(["--out", str(out)], http_client=client) == 2
    for bad in ("0", "13"):
        argv = ["--live", "--max-requests", bad, "--out", str(out)]
        assert SMOKE.main(argv, http_client=client) == 2
    monkeypatch.delenv("OPENAI_API_KEY")
    assert SMOKE.main(["--live", "--out", str(out)], http_client=client) == 2
    assert stand_in.bodies == [] and not out.exists()
    assert capsys.readouterr().out.count("NOT_RUN") == 4


def test_endpoint_label_records_where_requests_went_without_credentials() -> None:
    assert SMOKE.endpoint_label({}) == "https://api.openai.com/v1 (SDK default)"
    label = SMOKE.endpoint_label(
        {"OPENAI_BASE_URL": "https://user:secret@gateway.example.test:8443/v1?token=abc"}
    )
    assert label == "https://gateway.example.test:8443/v1 (from OPENAI_BASE_URL)"
