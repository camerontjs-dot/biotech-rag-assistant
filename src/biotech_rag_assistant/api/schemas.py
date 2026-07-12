"""Request bodies for the transport layer.

Responses reuse the core models' ``to_cli_record()`` output so HTTP JSON matches the CLI
byte-for-byte. Only request bodies are defined here; the file-path arguments the CLI takes
become inline JSON payloads.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from biotech_rag_assistant.citations import AnswerFixture, RetrievedResultsPayload
from biotech_rag_assistant.evaluation import EvaluationSuite


class CorpusRequest(BaseModel):
    """Optional corpus selector for endpoints that take no other input."""

    model_config = ConfigDict(extra="forbid")

    corpus: str | None = None


class RetrieveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1)
    corpus: str | None = None


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1)
    corpus: str | None = None


class ValidateCitationsRequest(BaseModel):
    """The two JSON payloads the CLI reads from files, inline."""

    model_config = ConfigDict(extra="forbid")

    retrieved_results: RetrievedResultsPayload
    answer_fixture: AnswerFixture


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suite: EvaluationSuite
    corpus: str | None = None
