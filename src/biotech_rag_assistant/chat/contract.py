"""The structured answer contract between the chat engine and a model.

The schema is built per turn so ``ref`` values are an enum of the passage refs actually supplied.
Strict structured outputs should then make invented refs impossible to decode. The application
still re-validates everything on return, because a provider that does not enforce the schema, or
a future schema change, must fail closed rather than reach the UI.

The schema stays inside the strict-mode subset: every object sets ``additionalProperties: false``
and lists every property in ``required``; only ``object``/``array``/``string`` and ``enum`` are
used.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

SCHEMA_NAME = "controlled_document_answer"

AnswerStatus = Literal[
    "answered", "partially_answered", "not_stated", "needs_clarification", "out_of_scope"
]
ANSWER_STATUSES: tuple[str, ...] = (
    "answered",
    "partially_answered",
    "not_stated",
    "needs_clarification",
    "out_of_scope",
)
BlockKind = Literal["paragraph", "step", "checklist_item", "bullet"]
BLOCK_KINDS: tuple[str, ...] = ("paragraph", "step", "checklist_item", "bullet")

MAX_BLOCKS = 30
MAX_BLOCK_TEXT = 2500
MAX_CITATIONS_PER_BLOCK = 8
MAX_QUOTE = 1200
MAX_MISSING = 10
MAX_SHORT_TEXT = 1200


class MalformedAnswer(Exception):
    """The model's output is not a valid answer under the contract."""


def answer_json_schema(refs: Sequence[str]) -> dict[str, object]:
    """Strict JSON schema for one turn's answer, with ``ref`` limited to ``refs``."""
    ref_schema: dict[str, object] = {
        "type": "string",
        "description": "A passage ref from this turn's passages array, such as S1.",
    }
    if refs:
        ref_schema["enum"] = list(refs)
    citation = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ref", "quote"],
        "properties": {
            "ref": ref_schema,
            "quote": {
                "type": "string",
                "description": (
                    "Contiguous text copied character-for-character from the cited passage's "
                    "text. No ellipses, no paraphrase."
                ),
            },
        },
    }
    block = {
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", "text", "citations"],
        "properties": {
            "kind": {"type": "string", "enum": list(BLOCK_KINDS)},
            "text": {"type": "string"},
            "citations": {"type": "array", "items": citation},
        },
    }
    missing = {
        "type": "object",
        "additionalProperties": False,
        "required": ["requested", "explanation", "related_refs"],
        "properties": {
            "requested": {"type": "string"},
            "explanation": {"type": "string"},
            "related_refs": {"type": "array", "items": ref_schema},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "blocks", "missing_information", "clarifying_question"],
        "properties": {
            "status": {"type": "string", "enum": list(ANSWER_STATUSES)},
            "blocks": {"type": "array", "items": block},
            "missing_information": {"type": "array", "items": missing},
            "clarifying_question": {"type": "string"},
        },
    }


class ModelCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Deliberately a plain string, not the enum: invented refs must reach the checks.
    ref: str = Field(max_length=32)
    quote: str = Field(max_length=MAX_QUOTE)


class ModelBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: BlockKind
    text: str = Field(max_length=MAX_BLOCK_TEXT)
    citations: list[ModelCitation] = Field(max_length=MAX_CITATIONS_PER_BLOCK)


class ModelMissing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested: str = Field(max_length=MAX_SHORT_TEXT)
    explanation: str = Field(max_length=MAX_SHORT_TEXT)
    related_refs: list[str] = Field(max_length=MAX_CITATIONS_PER_BLOCK)


class ModelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AnswerStatus
    blocks: list[ModelBlock] = Field(max_length=MAX_BLOCKS)
    missing_information: list[ModelMissing] = Field(max_length=MAX_MISSING)
    clarifying_question: str = Field(max_length=MAX_SHORT_TEXT)


def parse_model_answer(text: str) -> ModelAnswer:
    """Parse and validate model output. Raises ``MalformedAnswer``; never repairs output."""
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MalformedAnswer(f"output is not valid JSON: {exc.msg} at char {exc.pos}") from exc
    if not isinstance(raw, dict):
        raise MalformedAnswer("output JSON is not an object")
    try:
        return ModelAnswer.model_validate(raw)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or '<root>'}: {error['msg']}"
            for error in exc.errors()[:5]
        )
        raise MalformedAnswer(f"output does not match the answer contract: {problems}") from exc
