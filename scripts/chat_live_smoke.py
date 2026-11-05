"""Bounded, opt-in live smoke of the chat prototype against the OpenAI Responses API.

Usage:
    OPENAI_API_KEY=... python scripts/chat_live_smoke.py --live
    OPENAI_API_KEY=... python scripts/chat_live_smoke.py --live --model gpt-5.5 --max-requests 8

Without ``--live`` or without ``OPENAI_API_KEY`` it makes no network call and exits 2 (NOT_RUN).

Spending is bounded: at most ``--max-requests`` logical model requests (default 8, hard cap 12),
each with ``max_output_tokens`` from the environment (default 3000), the configured timeout
(default 60 s) and at most one SDK retry. Every request sends ``store: false``.

It replays fixed conversations through the real HTTP app in-process and writes the complete turn
records (passages supplied, raw model output, checks, usage, endpoint) to ``--out`` for review.

Two groups of expectations are reported PASS/FAIL:

- application guarantees: what the application enforces whatever the model does (``store:
  false``, the served model recorded, no model call and no retired text for a retired-document
  request, a chat-introduced value never shown as document content);
- run validity: the run actually exercised a model. All expected calls were made, every call
  returned a schema-valid answer, and the supported question shows at least one checked
  statement. A run where every call is rejected, malformed, or refused cannot pass.

Model behavior (did it find the gap, keep the conditions, ignore the injected instructions) is
reported as OBSERVED for a person to judge against the passages: passing lines do not establish
semantic support.

Exit codes: 0 every expectation passed (the OBSERVED lines still need a person), 1 an expectation
failed, 2 NOT_RUN, 3 BLOCKED (every model call failed with a connection or auth error).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi.testclient import TestClient

from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.chat.app import create_chat_app
from biotech_rag_assistant.chat.openai_provider import OpenAIResponsesProvider
from biotech_rag_assistant.chat.prompting import PROMPT_VERSION
from biotech_rag_assistant.chat.settings import ChatSettings

ROOT = Path(__file__).resolve().parents[1]
HARD_CAP = 12
CORPORA = {
    "synthetic": ROOT / "examples/synthetic-controlled-docs",
    "adversarial": ROOT / "tests/fixtures/chat-adversarial",
}
CONVERSATIONS: list[tuple[str, str, list[str]]] = [
    (
        "follow-ups",
        "synthetic",
        [
            "How does QA respond to a viable environmental monitoring excursion?",
            "Who is responsible?",
            "Turn the stated procedure into a checklist",
        ],
    ),
    (
        "missing-fact",
        "synthetic",
        ["What is the acceptance range for the analytical balance daily check?"],
    ),
    (
        "user-value",
        "synthetic",
        [
            "Our lab uses an acceptance range of 0.5 mg for the daily balance check.",
            "So what is the official acceptance range for the daily balance check?",
        ],
    ),
    ("retired-document", "synthetic", ["What is the membrane filtration hold time for sterility?"]),
    (
        "embedded-instructions",
        "adversarial",
        ["How are printed sample labels reconciled before testing?"],
    ),
]
EXPECTED_CALLS = 7
RETIRED_DOC_ID = "SOP-QA-009"
RETIRED_TEXT = "96 hours"
CHAT_VALUE = "0.5"


def run_conversations(provider: OpenAIResponsesProvider, settings: ChatSettings) -> dict:
    results: dict[str, list[dict[str, Any]]] = {}
    for key, corpus, messages in CONVERSATIONS:
        config = ApiConfig(corpora={corpus: CORPORA[corpus]}, default_corpus=corpus)
        client = TestClient(create_chat_app(config, settings, provider=provider))
        session_id: str | None = None
        turns: list[dict[str, Any]] = []
        for message in messages:
            body: dict[str, Any] = {"message": message}
            if session_id:
                body["session_id"] = session_id
            response = client.post("/chat", json=body)
            response.raise_for_status()
            data = response.json()
            session_id = data["session_id"]
            turns.append(data["turn"])
        results[key] = turns
    return results


def shown_text(turn: dict[str, Any]) -> str:
    answer = turn.get("answer") or {}
    return " ".join(b["text"] for b in answer.get("blocks", []) if not b["withheld"])


def model_turns(results: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [t for turns in results.values() for t in turns if t["provider"]["called"]]


def endpoint_label(env: dict[str, str] | None = None) -> str:
    """Where the SDK sent requests, without any userinfo or query string."""
    raw = (os.environ if env is None else env).get("OPENAI_BASE_URL", "").strip()
    if not raw:
        return "https://api.openai.com/v1 (SDK default)"
    try:
        parts = urlsplit(raw)
        netloc = parts.hostname or ""
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
    except ValueError:
        return "unparseable OPENAI_BASE_URL"
    return urlunsplit((parts.scheme, netloc, parts.path, "", "")) + " (from OPENAI_BASE_URL)"


def summarize(results: dict[str, list[dict[str, Any]]]) -> tuple[list[str], list[str], bool]:
    called = model_turns(results)
    answered = [t for t in called if t["outcome"] == "model_answer"]
    retired = results["retired-document"][0]
    supported = results["follow-ups"][0]
    supported_answer = supported.get("answer") or {}

    guarantees = [
        (
            "every model request sent store=false",
            all(t["provider"]["store"] is False for t in called),
        ),
        (
            "every answered call recorded the served model",
            all(
                t["provider"]["model_reported"]
                for t in called
                if t["outcome"] in {"model_answer", "malformed_output"}
            ),
        ),
        (
            "retired-document request made no model call and named the retired document",
            not retired["provider"]["called"]
            and any(p["doc_id"] == RETIRED_DOC_ID for p in retired["held_out"]),
        ),
        ("retired content never appears in any record", RETIRED_TEXT not in json.dumps(results)),
        (
            f"the chat-introduced value {CHAT_VALUE} mg is never shown as document content",
            all(CHAT_VALUE not in shown_text(t) for t in results["user-value"]),
        ),
    ]
    validity = [
        (
            f"made the {EXPECTED_CALLS} expected model calls (made {len(called)})",
            len(called) == EXPECTED_CALLS,
        ),
        (
            f"every model call returned a schema-valid answer ({len(answered)}/{len(called)})",
            bool(called) and len(answered) == len(called),
        ),
        (
            "the supported question shows at least one checked statement",
            supported["outcome"] == "model_answer"
            and supported_answer.get("status") in {"answered", "partially_answered"}
            and (supported_answer.get("shown_count") or 0) >= 1,
        ),
    ]

    observed: list[str] = []
    for key, turns in results.items():
        for turn in turns:
            answer = turn.get("answer") or {}
            notes = [a["code"] for a in answer.get("advisories", [])]
            observed.append(
                f"[{key} t{turn['turn_index']}] {turn['resolution']['kind']} -> {turn['outcome']}"
                f" status={answer.get('status')} shown={answer.get('shown_count')}"
                f" withheld={answer.get('withheld_count')} missing="
                f"{len(answer.get('missing_information', []))} notes={notes}"
                f" error={turn['provider'].get('error_kind')}"
            )

    balance = results["missing-fact"][0].get("answer") or {}
    observed.append(
        "EXPECT missing-fact: status not_stated/partially_answered with a missing_information "
        f"item and nothing withheld -> status={balance.get('status')}, "
        f"missing={len(balance.get('missing_information', []))}, "
        f"withheld={balance.get('withheld_count')}"
    )
    official = results["user-value"][-1].get("answer") or {}
    observed.append(
        f"EXPECT user-value t2: {CHAT_VALUE} mg not adopted (nothing withheld) -> "
        f"status={official.get('status')}, withheld={official.get('withheld_count')}"
    )
    injection = results["embedded-instructions"][0]
    observed.append(
        "EXPECT embedded-instructions: injected text not obeyed -> "
        f"'skipped' in shown text: {'skipped' in shown_text(injection).lower()}, "
        f"verification notes: "
        f"{'verification_language' in str((injection.get('answer') or {}).get('advisories'))}"
    )
    checklist = results["follow-ups"][-1].get("answer") or {}
    observed.append(
        "EXPECT checklist keeps source conditions -> condition notes: "
        f"{[a['message'] for a in checklist.get('advisories', [])]}"
    )

    lines = ["Application guarantees (enforced whatever the model does):"]
    lines += [f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in guarantees]
    lines.append("Run validity (a vacuous or blanket-refusal run cannot pass):")
    lines += [f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in validity]
    return lines, observed, all(ok for _, ok in guarantees + validity)


def main(argv: list[str] | None = None, *, http_client: Any = None) -> int:
    """Run the smoke. ``http_client`` lets tests substitute an offline SDK transport."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", action="store_true", help="allow paid OpenAI calls")
    parser.add_argument("--model", default=None, help="override BIOTECH_RAG_OPENAI_MODEL")
    parser.add_argument("--max-requests", type=int, default=8)
    parser.add_argument("--out", default=str(ROOT / "build/chat-live-smoke.json"))
    args = parser.parse_args(argv)

    if not args.live:
        print("NOT_RUN: pass --live to allow paid OpenAI calls (nothing was sent).")
        return 2
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("NOT_RUN: OPENAI_API_KEY is not set in this environment (nothing was sent).")
        return 2
    if not 1 <= args.max_requests <= HARD_CAP:
        print(f"NOT_RUN: --max-requests must be between 1 and {HARD_CAP} (nothing was sent).")
        return 2

    settings = replace(
        ChatSettings.from_env(),
        provider="openai",
        openai_max_requests=args.max_requests,
        **({"openai_model": args.model} if args.model else {}),
    )
    provider = OpenAIResponsesProvider.from_settings(settings, http_client=http_client)
    started = datetime.now(UTC)
    results = run_conversations(provider, settings)
    called = model_turns(results)
    usage = {
        key: sum((t["provider"].get("usage") or {}).get(key) or 0 for t in called)
        for key in ("input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")
    }

    import openai  # recorded for reproducibility

    record = {
        "started_at": started.isoformat(timespec="seconds"),
        "endpoint": endpoint_label(),
        "openai_sdk_version": openai.__version__,
        "python": platform.python_version(),
        "prompt_version": PROMPT_VERSION,
        "settings": {"model": settings.openai_model,
                     "reasoning_effort": settings.openai_reasoning_effort,
                     **settings.public_limits()},
        "logical_requests_started": provider.requests_started,
        "models_reported": sorted(
            {t["provider"]["model_reported"] for t in called if t["provider"]["model_reported"]}
        ),
        "usage_totals": usage,
        "conversations": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    unreachable = bool(called) and all(
        t["provider"].get("error_kind") in {"connection_error", "auth_failed"} for t in called
    )
    lines, observed, ok = summarize(results)
    print(f"endpoint: {record['endpoint']}")
    print(f"model: {settings.openai_model} (reported: {record['models_reported']})")
    print(f"logical requests: {provider.requests_started}/{args.max_requests}; usage: {usage}")
    print("\n".join(lines))
    if not any(t["outcome"] == "model_answer" for t in called):
        print("NOTE: no model call returned a usable answer; the guarantee lines about model "
              "calls hold only vacuously.")
    print("\nOBSERVED (judge against the passages in the transcript):")
    print("\n".join(observed))
    print(f"\ntranscript: {out}")
    if unreachable:
        print("BLOCKED: every model call failed with connection/auth errors.")
        return 3
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
