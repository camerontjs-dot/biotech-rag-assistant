"""Render docs/chat-examples.md by replaying scripted conversations through the chat app.

Usage:
    python scripts/render_chat_examples.py          # rewrite docs/chat-examples.md
    python scripts/render_chat_examples.py --check  # exit 1 if the committed file is stale

Each conversation runs through the real HTTP app (``create_chat_app`` + ``POST /chat``) over the
named corpus. Only the model outputs are scripted (see ``chat_scenarios.py``); interpretation,
retrieval, evidence, checks, and the shown/withheld decisions are the application's own output.
The rendering is deterministic: no timestamps, session ids, or latencies.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Any

from chat_scenarios import CONVERSATIONS, CORPORA, Conversation
from fastapi.testclient import TestClient

from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.chat.app import create_chat_app
from biotech_rag_assistant.chat.settings import ChatSettings
from biotech_rag_assistant.chat.testing import ScriptedProvider

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/chat-examples.md"

STATUS_TEXT = {
    "answered": "answered",
    "partially_answered": "partly answered",
    "not_stated": "not stated in the documents",
    "needs_clarification": "needs clarification",
    "out_of_scope": "out of scope",
}


def run(conversation: Conversation) -> list[dict[str, Any]]:
    provider = ScriptedProvider(
        by_question={turn.message: turn.step for turn in conversation.turns if turn.step}
    )
    config = ApiConfig(
        corpora={conversation.corpus: CORPORA[conversation.corpus]},
        default_corpus=conversation.corpus,
    )
    client = TestClient(create_chat_app(config, ChatSettings(), provider=provider))
    session_id: str | None = None
    turns: list[dict[str, Any]] = []
    for scripted in conversation.turns:
        body: dict[str, Any] = {"message": scripted.message, "new_topic": scripted.new_topic}
        if session_id:
            body["session_id"] = session_id
        response = client.post("/chat", json=body)
        if response.status_code != 200:
            raise SystemExit(f"{conversation.key}: HTTP {response.status_code}: {response.text}")
        data = response.json()
        session_id = data["session_id"]
        turn = data["turn"]
        expected_call = scripted.step is not None
        if turn["provider"]["called"] != expected_call:
            raise SystemExit(
                f"{conversation.key} turn {turn['turn_index']}: expected model call "
                f"{expected_call}, got {turn['provider']['called']} ({turn['outcome']})"
            )
        turns.append(turn)
    return turns


def md(text: str) -> str:
    """Escape text for Markdown so passage and model text render literally."""
    out = text.replace("\\", "\\\\")
    for char in "`*_[]<>|":
        out = out.replace(char, "\\" + char)
    return out.replace("\n", " ")


def highlighted(passage: dict[str, Any], ranges: list[tuple[int, int]]) -> str:
    text = passage["text"]
    pieces: list[str] = []
    cursor = 0
    for start, end in sorted(ranges):
        if start < cursor:
            start = cursor
        if start >= end:
            continue
        pieces.append(md(text[cursor:start]))
        pieces.append("**" + md(text[start:end]) + "**")
        cursor = end
    pieces.append(md(text[cursor:]))
    return "".join(pieces)


def label(turn: dict[str, Any], ref: str) -> str:
    for passage in turn["evidence"]:
        if passage["ref"] == ref:
            return f"{ref}: {passage['doc_id']} v{passage['version']}"
    return ref


def render_turn(turn: dict[str, Any]) -> list[str]:
    resolution = turn["resolution"]
    lines = [
        f"#### Turn {turn['turn_index']}: “{md(turn['user_message'])}”",
        "",
        f"- **Interpretation** (`{resolution['kind']}`): {md(resolution['explanation'])}",
    ]
    for attempt in resolution["attempts"]:
        origin = (
            "this message"
            if attempt["origin"] == "current_message"
            else attempt["origin"].replace("anchor:turn_", "turn ") + "'s question"
        )
        hits = (
            ", ".join(f"`{chunk_id}`" for chunk_id in attempt["hit_chunk_ids"])
            or "no passage cleared the relevance gate"
        )
        lines.append(f"- **Searched** “{md(attempt['query'])}” ({origin}): {hits}")
    provider = turn["provider"]
    if provider["called"]:
        lines.append(
            f"- **Model call:** yes, scripted provider `{provider['model_reported']}` "
            "(hand-written output, not OpenAI)"
        )
    else:
        lines.append("- **Model call:** none")
    answer = turn["answer"]
    status = STATUS_TEXT.get(answer["status"], answer["status"]) if answer else None
    lines.append(f"- **Outcome:** `{turn['outcome']}`" + (f", status: {status}" if status else ""))
    lines.append("")

    if turn["message"]:
        lines += [f"> {md(turn['message'])}", ""]

    ranges: dict[str, list[tuple[int, int]]] = {}
    if answer:
        shown = [b for b in answer["blocks"] if not b["withheld"]]
        if shown:
            lines.append("**Answer as shown**")
            lines.append("")
            step_number = 0
            previous_kind: str | None = None
            for b in shown:
                cites = " ".join(f"[{md(label(turn, ref))}]" for ref in b["valid_refs"])
                if previous_kind is not None and (
                    b["kind"] == "paragraph" or b["kind"] != previous_kind
                ):
                    lines.append("")  # separate groups so Markdown does not merge them
                if b["kind"] == "step":
                    step_number += 1
                    prefix = f"{step_number}."
                elif b["kind"] == "checklist_item":
                    prefix = "- [ ]"
                elif b["kind"] == "bullet":
                    prefix = "-"
                else:
                    prefix = ""
                lines.append(f"{prefix} {md(b['text'])} {cites}".strip())
                previous_kind = b["kind"]
                for c in b["citations"]:
                    if c["quote_found"]:
                        ranges.setdefault(c["ref"], []).append(
                            (c["highlight_start"], c["highlight_end"])
                        )
            lines.append("")
        for b in answer["blocks"]:
            if b["withheld"]:
                lines += [
                    f"**Withheld by the checks:** {md(b['withheld_reason'])} "
                    f"(model text, not shown in the interface: “{md(b['withheld_text'])}”)",
                    "",
                ]
        for item in answer["missing_information"]:
            refs = " ".join(f"[{md(label(turn, ref))}]" for ref in item["related_refs"])
            lines += [
                f"**Not stated in the documents:** {md(item['requested'])}. "
                f"{md(item['explanation'])} {refs}".strip(),
                "",
            ]
        if answer["clarifying_question"]:
            lines += [f"**Question for the user:** {md(answer['clarifying_question'])}", ""]
        if answer["advisories"]:
            lines.append("**Review notes (advisory):**")
            lines += [f"- {md(note['message'])}" for note in answer["advisories"]]
            lines.append("")

    if turn["held_out"]:
        held = "; ".join(
            f"{h['doc_id']} v{h['version']} ({h['status']})" for h in turn["held_out"]
        )
        lines += [f"**Held out by the status gate (identity only, never evidence):** {held}", ""]

    if turn["evidence"]:
        lines.append("**Passages supplied** (bold = span located from a shown citation)")
        lines.append("")
        for passage in turn["evidence"]:
            cited = "cited" if passage["ref"] in ranges else "supplied, not cited"
            lines.append(
                f"- **{passage['ref']}** {passage['doc_id']} v{passage['version']} "
                f"({passage['status']}), {passage['line_or_page_span']}, `{passage['chunk_id']}`, "
                f"{cited}: {highlighted(passage, ranges.get(passage['ref'], []))}"
            )
        lines.append("")
    return lines


def render(results: list[tuple[Conversation, list[dict[str, Any]]]]) -> str:
    lines = [
        "# Chat prototype: example conversations",
        "",
        "<!-- Generated by scripts/render_chat_examples.py. Do not edit by hand. -->",
        "",
        "These conversations were replayed through the real chat application (`POST /chat`) over "
        "the committed synthetic corpora. **The model outputs are scripted**: they were written "
        "by hand for the test provider and are not OpenAI output. Everything else is the "
        "application's actual behavior: how each message was interpreted, what was searched, "
        "which passages were supplied, what the mechanical checks showed or withheld, and when "
        "no model was called at all.",
        "",
        "Live OpenAI behavior is not shown here. `scripts/chat_live_smoke.py` records real "
        "transcripts for review once a key and network access are available "
        "(see `docs/chat-prototype.md`).",
        "",
    ]
    for conversation, turns in results:
        snapshot = turns[0]["corpus_snapshot_id"] if turns else ""
        lines += [
            f"## {conversation.title}",
            "",
            f"Corpus `{conversation.corpus}`, snapshot `{snapshot}`.",
            "",
        ]
        if conversation.note:
            lines += [f"_{md(conversation.note)}_", ""]
        for turn in turns:
            lines += render_turn(turn)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the file is out of date")
    args = parser.parse_args()
    content = render([(conversation, run(conversation)) for conversation in CONVERSATIONS])
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            diff = difflib.unified_diff(
                current.splitlines(), content.splitlines(), "committed", "regenerated", lineterm=""
            )
            sys.stdout.write("\n".join(list(diff)[:80]) + "\n")
            print("docs/chat-examples.md is stale: run python scripts/render_chat_examples.py")
            return 1
        print("docs/chat-examples.md is current")
        return 0
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
