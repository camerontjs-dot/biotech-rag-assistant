"""One conversational turn: resolve, retrieve, (maybe) generate, check, record.

Order of operations, and where each control lives:

1. ``resolve_turn`` decides which queries to run (history resolves references only).
2. Retrieval runs through the maintained path with the maintained ``RetrievalConfig`` defaults.
3. ``assemble_evidence`` re-verifies status, hash, and exact span for every admitted passage.
4. A model is asked only when admitted evidence exists *and* the provider is available. With no
   evidence the reply is deterministic (no model call), naming any held-out document a
   status-blind run would have used (identity only, ADR-018).
5. Model output is parsed fail-closed against the contract, then mechanically checked.
6. The turn is recorded: verbatim question, resolution and every retrieval attempt, the evidence
   actually supplied, the corpus snapshot id, provider/model identity, usage, and check results.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from biotech_rag_assistant.chat.checks import AnswerView, check_answer
from biotech_rag_assistant.chat.contract import MalformedAnswer, parse_model_answer
from biotech_rag_assistant.chat.evidence import (
    CorpusBinding,
    EvidencePassage,
    HeldOutPointer,
    assemble_evidence,
    held_out_pointers,
)
from biotech_rag_assistant.chat.prompting import PROMPT_VERSION, build_provider_request
from biotech_rag_assistant.chat.provider import (
    UNAVAILABLE_KINDS,
    ChatProvider,
    ProviderError,
    ProviderTraceMeta,
)
from biotech_rag_assistant.chat.resolution import Resolution, resolve_turn
from biotech_rag_assistant.chat.sessions import Session
from biotech_rag_assistant.chat.settings import ChatSettings
from biotech_rag_assistant.retrieval import RetrievalConfig

TurnOutcome = Literal[
    "model_answer",
    "no_admitted_evidence",
    "clarification_needed",
    "courtesy",
    "provider_unavailable",
    "provider_error",
    "malformed_output",
]

SOURCES_ONLY_SUFFIX = " The retrieved approved passages are shown below; read them directly."


class ProviderTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    called: bool
    provider: str
    model_requested: str | None = None
    model_reported: str | None = None
    response_id: str | None = None
    usage: dict[str, int | None] | None = None
    latency_ms: int | None = None
    store: bool | None = None
    prompt_version: str | None = None
    request_sha256: str | None = None
    error_kind: str | None = None
    error_message: str | None = None
    error_detail: str | None = None
    raw_output_unvalidated: str | None = None


class TurnRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int
    created_at: str
    corpus: str
    corpus_snapshot_id: str
    user_message: str
    resolution: Resolution
    evidence: list[EvidencePassage]
    held_out: list[HeldOutPointer]
    outcome: TurnOutcome
    message: str | None
    answer: AnswerView | None
    provider: ProviderTrace


class ChatEngine:
    def __init__(
        self,
        bindings: dict[str, CorpusBinding],
        provider: ChatProvider,
        settings: ChatSettings,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.bindings = bindings
        self.provider = provider
        self.settings = settings
        # Maintained defaults (score_floor, ADR-012 coverage gate); only top_k is chosen here.
        self.retrieval_config = RetrievalConfig(top_k=settings.top_k)
        self._clock = clock

    def run_turn(self, session: Session, message: str, *, new_topic: bool = False) -> TurnRecord:
        binding = self.bindings[session.corpus]
        turn_index = len(session.turns) + 1
        resolved = resolve_turn(
            message,
            turn_index=turn_index,
            active_topic=session.active_topic,
            new_topic=new_topic,
            binding=binding,
            config=self.retrieval_config,
        )
        resolution = resolved.resolution
        evidence = assemble_evidence(
            resolved.hit_sets, binding, self.settings.max_evidence_passages
        )
        refused = not evidence and resolution.kind == "not_found"
        held_out = held_out_pointers(
            binding,
            message=message,
            query=resolution.retrieval_query if refused else None,
            config=self.retrieval_config,
        )

        trace = ProviderTrace(called=False, provider=self.provider.name)
        answer: AnswerView | None = None
        reply: str | None = None

        if resolution.kind == "courtesy":
            outcome: TurnOutcome = "courtesy"
            reply = (
                "Ask a question about the controlled documents in this corpus whenever you're "
                "ready."
            )
        elif not evidence:
            if resolution.kind == "clarification_needed":
                outcome = "clarification_needed"
                reply = _clarification_text(resolution) + _held_out_text(held_out)
            else:
                outcome = "no_admitted_evidence"
                reply = _not_found_text(binding.name) + _held_out_text(held_out)
        else:
            availability = self.provider.availability()
            trace.model_requested = availability.model
            trace.store = availability.store
            if not availability.available:
                outcome = "provider_unavailable"
                trace.error_kind = availability.reason
                trace.error_message = availability.message
                reply = f"Explanation unavailable: {availability.message}{SOURCES_ONLY_SUFFIX}"
            else:
                outcome, answer, reply = self._generate(
                    session, message, resolution, evidence, held_out, trace, availability.model
                )

        record = TurnRecord(
            turn_index=turn_index,
            created_at=self._clock().isoformat(timespec="seconds"),
            corpus=binding.name,
            corpus_snapshot_id=binding.snapshot.snapshot_id,
            user_message=message,
            resolution=resolution,
            evidence=evidence,
            held_out=held_out,
            outcome=outcome,
            message=reply,
            answer=answer,
            provider=trace,
        )
        session.turns.append(record)
        session.active_topic = resolved.next_topic
        return record

    def _generate(
        self,
        session: Session,
        message: str,
        resolution: Resolution,
        evidence: list[EvidencePassage],
        held_out: list[HeldOutPointer],
        trace: ProviderTrace,
        model: str | None,
    ) -> tuple[TurnOutcome, AnswerView | None, str | None]:
        request = build_provider_request(
            history=session.turns,
            message=message,
            resolution=resolution,
            evidence=evidence,
            not_admitted=held_out,
            history_turns=self.settings.history_turns,
            max_output_tokens=self.settings.openai_max_output_tokens,
        )
        trace.called = True
        trace.prompt_version = PROMPT_VERSION
        trace.request_sha256 = _request_digest(model, request)
        try:
            result = self.provider.generate(request)
        except ProviderError as exc:
            _apply_meta(trace, exc.meta)
            trace.error_kind = exc.kind
            trace.error_message = exc.message
            trace.error_detail = exc.detail
            outcome: TurnOutcome = (
                "provider_unavailable" if exc.kind in UNAVAILABLE_KINDS else "provider_error"
            )
            return outcome, None, f"{exc.message}{SOURCES_ONLY_SUFFIX}"

        _apply_meta(trace, result.meta)
        trace.model_requested = result.model_requested
        trace.store = result.store
        trace.raw_output_unvalidated = result.output_text
        try:
            parsed = parse_model_answer(result.output_text)
        except MalformedAnswer as exc:
            trace.error_kind = "malformed_output"
            trace.error_message = ProviderError("malformed_output").message
            trace.error_detail = str(exc)
            return "malformed_output", None, f"{trace.error_message}{SOURCES_ONLY_SUFFIX}"

        user_messages = [turn.user_message for turn in session.turns] + [message]
        return "model_answer", check_answer(parsed, evidence, user_messages=user_messages), None


def _apply_meta(trace: ProviderTrace, meta: ProviderTraceMeta) -> None:
    trace.model_reported = meta.model_reported
    trace.response_id = meta.response_id
    trace.latency_ms = meta.latency_ms
    if meta.usage is not None:
        trace.usage = {
            "input_tokens": meta.usage.input_tokens,
            "output_tokens": meta.usage.output_tokens,
            "reasoning_tokens": meta.usage.reasoning_tokens,
            "total_tokens": meta.usage.total_tokens,
        }


def _request_digest(model: str | None, request: object) -> str:
    body = {
        "model": model,
        "instructions": getattr(request, "instructions", None),
        "input": getattr(request, "input", None),
        "schema": getattr(request, "json_schema", None),
        "max_output_tokens": getattr(request, "max_output_tokens", None),
    }
    encoded = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _not_found_text(corpus: str) -> str:
    return (
        f"No Approved or Effective passage in the '{corpus}' corpus matched enough of this "
        "message's key terms, so no model was asked and nothing is stated here. Try naming the "
        "procedure or using the document's own wording."
    )


def _held_out_text(held_out: list[HeldOutPointer]) -> str:
    text = ""
    for pointer in held_out:
        identity = (
            f"{pointer.doc_id} v{pointer.version} (“{pointer.doc_title}”, status "
            f"{pointer.status})"
        )
        if "status_blind_match" in pointer.reasons:
            text += (
                f" {identity} matches this question, but the status gate holds it out, so it is "
                "not used as evidence."
            )
        else:
            text += (
                f" {identity} is not an admitted document: the status gate holds it out, so its "
                "content is not available here."
            )
    return text


def _clarification_text(resolution: Resolution) -> str:
    if "correction" in resolution.explanation.lower():
        return (
            "Understood: I set the earlier topic aside. I could not find an approved passage for "
            "the corrected request on its own. Which procedure or document should I look at?"
        )
    return (
        "Which procedure or document do you mean? There is no earlier answered question in this "
        "conversation to connect that to."
    )
