"""Browser check of the chat UI against the real app, with a scripted provider (no model).

Usage:
    python scripts/chat_ui_check.py [--out build/chat-ui-check]

Requires Node and the Playwright package (``require('playwright')`` must resolve) with Chromium.
Starts four local servers (127.0.0.1, free ports) built with ``create_chat_app``:

- ``scripted``: synthetic corpus, scripted provider (answers, follow-ups, a withheld value, a
  timeout, malformed output);
- ``adversarial``: injection fixture corpus, scripted output carrying markup;
- ``unconfigured``: synthetic corpus, no provider (the shipped default);
- ``keyed``: synthetic corpus with ``BIOTECH_RAG_API_KEY``-style auth.

Then runs ``scripts/chat_ui_check.cjs`` in Chromium and writes results and screenshots to the
output directory. It exercises the UI and HTTP boundary only; it says nothing about live model
quality.
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import uvicorn
from chat_scenarios import (
    CORPORA,
    em_checklist,
    em_response,
    em_responsible,
    labels_unsafe_markup,
)

from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.chat.app import create_chat_app
from biotech_rag_assistant.chat.provider import ProviderError, UnconfiguredProvider
from biotech_rag_assistant.chat.settings import ChatSettings
from biotech_rag_assistant.chat.testing import (
    ScriptedProvider,
    answer,
    block,
    find_passage,
    missing_item,
)

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts/chat_ui_check.cjs"
UI_KEY = "ui-check-key-not-a-secret"


def balance_mixed(request: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """One invented value (must be withheld) beside an honest statement and a stated gap."""
    s = find_passage(payload, doc_id="CAL-ENG-005", contains="acceptance range")["ref"]
    return answer(
        "not_stated",
        [
            block(
                "paragraph",
                "The acceptance range is ±0.1 mg.",
                (s, "If either weight falls outside the acceptance range"),
            ),
            block(
                "paragraph",
                "If either weight falls outside the acceptance range, the analyst stops use and "
                "labels the balance out of service.",
                (s, "If either weight falls outside the acceptance range, the analyst stops use "
                 "and labels the balance out of service"),
            ),
        ],
        missing=[
            missing_item(
                "The numeric acceptance range",
                "The note names the acceptance range without stating it.",
                s,
            )
        ],
        question="Would you like the steps the note gives when a weight is outside the range?",
    )


def synthetic_config(**overrides: Any) -> ApiConfig:
    return ApiConfig(
        corpora={"synthetic": CORPORA["synthetic"]}, default_corpus="synthetic", **overrides
    )


def build_apps() -> dict[str, Any]:
    scripted = ScriptedProvider(
        by_question={
            "How does QA respond to a viable environmental monitoring excursion?": em_response,
            "Who is responsible?": em_responsible,
            "Turn the stated procedure into a checklist": em_checklist,
            "What is the acceptance range for the analytical balance daily check?": balance_mixed,
            "How do staff confirm the current approved version of a controlled document?": (
                ProviderError("timeout", detail="scripted timeout")
            ),
            "When is gowning requalification required?": "this is not JSON",
        }
    )
    adversarial = ScriptedProvider(
        by_question={
            "How are printed sample labels reconciled before testing?": labels_unsafe_markup
        }
    )
    keyed = ScriptedProvider(
        by_question={
            "How does QA respond to a viable environmental monitoring excursion?": em_response
        }
    )
    settings = ChatSettings()
    return {
        "scripted": create_chat_app(synthetic_config(), settings, provider=scripted),
        "adversarial": create_chat_app(
            ApiConfig(
                corpora={"adversarial": CORPORA["adversarial"]}, default_corpus="adversarial"
            ),
            settings,
            provider=adversarial,
        ),
        "unconfigured": create_chat_app(
            synthetic_config(), settings, provider=UnconfiguredProvider()
        ),
        "keyed": create_chat_app(synthetic_config(api_key=UI_KEY), settings, provider=keyed),
    }


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def serve(app: Any) -> tuple[uvicorn.Server, str]:
    port = free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    )
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.monotonic() + 15
    while not server.started:
        if time.monotonic() > deadline:
            raise SystemExit("server did not start")
        time.sleep(0.05)
    return server, f"http://127.0.0.1:{port}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "build/chat-ui-check"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    servers: list[uvicorn.Server] = []
    urls: dict[str, str] = {}
    for name, app in build_apps().items():
        server, url = serve(app)
        servers.append(server)
        urls[name] = url
    config = {"urls": urls, "out": str(out), "apiKey": UI_KEY}
    try:
        completed = subprocess.run(["node", str(DRIVER), json.dumps(config)], check=False)
    finally:
        for server in servers:
            server.should_exit = True
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
