"""Provider-neutral shadow generation and deterministic claim gates G1-G7."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from biotech_rag_assistant.evidence import EvidencePacket, RetrievalNomination

IDENTIFIER_RE = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")
WHITESPACE_RE = re.compile(r"\s+")
NUMBER_RE = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?")
WORD_RE = re.compile(r"[a-z0-9]+(?:/[a-z0-9]+)?")

NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
    "thirty": "30",
    "forty": "40",
    "fifty": "50",
    "sixty": "60",
    "seventy": "70",
    "eighty": "80",
    "ninety": "90",
}

UNIT_ALIASES = {
    "pct": "percent",
    "percentage": "percent",
    "percent": "percent",
    "mg": "mg",
    "g": "g",
    "kg": "kg",
    "ug": "ug",
    "mcg": "ug",
    "ml": "ml",
    "l": "l",
    "l/min": "l/min",
    "cfu": "cfu",
    "ppb": "ppb",
    "ppm": "ppm",
    "eu": "eu",
    "us/cm": "us/cm",
    "cm": "cm",
    "mm": "mm",
    "um": "um",
    "m3": "m3",
    "degree": "degrees",
    "degrees": "degrees",
    "c": "c",
    "second": "seconds",
    "seconds": "seconds",
    "minute": "minutes",
    "minutes": "minutes",
    "min": "minutes",
    "mins": "minutes",
    "hour": "hours",
    "hours": "hours",
    "day": "days",
    "days": "days",
    "working": "working",
    "calendar": "calendar",
    "unit": "units",
    "units": "units",
}

GeneratedDisposition = Literal[
    "answered",
    "partially_answered",
    "not_stated",
    "insufficient_evidence",
]
DisplayDisposition = Literal[
    "generated",
    "generated_with_gaps",
    "not_stated",
    "extractive_fallback",
    "refusal",
]
GateName = Literal["G1", "G2", "G3", "G4", "G5", "G6", "G7", "provider"]


class GeneratedCitation(BaseModel):
    """Generator-proposed citation to a packet chunk and exact supporting quote."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class GeneratedClaim(BaseModel):
    """One structured material claim proposed by the generator."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    citations: tuple[GeneratedCitation, ...] = Field(min_length=1)
    qualifier: str | None = None
    limitation: str | None = None


class GeneratedGap(BaseModel):
    """A stated evidence gap tied to related admitted material."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asked_about: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    topic_citation: GeneratedCitation


class GeneratedAnswer(BaseModel):
    """Strict structured output accepted from a generator before gating."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    disposition: GeneratedDisposition
    claims: tuple[GeneratedClaim, ...] = ()
    gaps: tuple[GeneratedGap, ...] = ()


class GeneratorMetadata(BaseModel):
    """Pinned identity of the generator adapter used for one shadow run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    prompt_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class GateIssue(BaseModel):
    """One deterministic gate finding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: GateName
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    claim_id: str | None = None


class DroppedClaim(BaseModel):
    """Claim removed by one or more blocking claim-local gates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    text: str
    gates: tuple[GateName, ...]


class FallbackEvidence(BaseModel):
    """Packet passage shown under an explicit fallback/refusal label."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str
    doc_id: str
    version: str
    status: str
    section_heading: str
    source_hash: str
    char_start: int
    char_end: int
    text: str


class SynthesisResult(BaseModel):
    """Validated shadow result or explicit fallback/refusal record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["answer", "refusal"]
    disposition: DisplayDisposition
    packet_identity: str = Field(pattern=r"^ep1:[a-f0-9]{64}$")
    generator: GeneratorMetadata | None
    generator_called: bool
    generated_disposition: GeneratedDisposition | None = None
    claims: tuple[GeneratedClaim, ...] = ()
    gaps: tuple[GeneratedGap, ...] = ()
    dropped_claims: tuple[DroppedClaim, ...] = ()
    gate_issues: tuple[GateIssue, ...] = ()
    fallback_evidence: tuple[FallbackEvidence, ...] = ()

    def to_cli_record(self) -> dict[str, object]:
        return self.model_dump(mode="json")


class Generator(Protocol):
    """Narrow generator authority: one EvidencePacket in, structured candidate out."""

    provider: str
    model_id: str
    prompt_hash: str

    def generate(self, packet: EvidencePacket) -> object:
        """Return provider output to be schema-validated by the deterministic boundary."""


class GeneratorUnavailableError(RuntimeError):
    """Raised when a non-empty packet has no shadow generator configured."""


class ScriptedGenerator:
    """Deterministic generator adapter for CI gate qualification."""

    def __init__(
        self,
        raw_output: object | None = None,
        *,
        exception: Exception | None = None,
        model_id: str = "scripted-generator-v1",
    ) -> None:
        self.raw_output = raw_output
        self.exception = exception
        self.provider = "scripted"
        self.model_id = model_id
        prompt_digest = hashlib.sha256(b"scripted-generator-v1").hexdigest()
        self.prompt_hash = f"sha256:{prompt_digest}"
        self.call_count = 0

    def generate(self, packet: EvidencePacket) -> object:
        self.call_count += 1
        if self.exception is not None:
            raise self.exception
        return self.raw_output


def _generator_metadata(generator: Generator) -> GeneratorMetadata:
    return GeneratorMetadata(
        provider=generator.provider,
        model_id=generator.model_id,
        prompt_hash=generator.prompt_hash,
    )


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("%", " percent ")
    normalized = normalized.replace("°", " degrees ")
    normalized = normalized.replace("µ", "u")
    normalized = WHITESPACE_RE.sub(" ", normalized.strip())
    return normalized.casefold()


def _normalize_number_words(text: str) -> str:
    normalized = _normalize_text(text)
    tokens = normalized.split(" ")
    return " ".join(NUMBER_WORDS.get(token, token) for token in tokens)


def _quote_is_contained(quote: str, nomination: RetrievalNomination) -> bool:
    normalized_quote = _normalize_text(quote)
    if not normalized_quote:
        return False
    return normalized_quote in _normalize_text(nomination.text)


def _quantity_tokens(text: str) -> set[str]:
    """Return deterministic numeric/unit tokens after controlled identifiers are removed."""
    without_ids = IDENTIFIER_RE.sub(" ", unicodedata.normalize("NFC", text))
    normalized = _normalize_number_words(without_ids)
    tokens: set[str] = {
        f"num:{match.group(0)}"
        for match in NUMBER_RE.finditer(normalized)
    }
    if tokens:
        for word in WORD_RE.findall(normalized):
            unit = UNIT_ALIASES.get(word)
            if unit is not None:
                tokens.add(f"unit:{unit}")
    return tokens


def _identifiers(text: str) -> set[str]:
    return {match.group(0).upper() for match in IDENTIFIER_RE.finditer(text)}


def _metadata_identifiers(nomination: RetrievalNomination) -> set[str]:
    fields = (
        nomination.chunk_id,
        nomination.doc_id,
        nomination.source_file_path,
        nomination.doc_title,
        nomination.section_heading,
    )
    found: set[str] = set()
    for value in fields:
        found.update(_identifiers(value))
    return found


def _packet_chunks(packet: EvidencePacket) -> dict[str, RetrievalNomination]:
    return {
        item.nomination.chunk_id: item.nomination
        for item in packet.admitted
    }


def _fallback_evidence(packet: EvidencePacket) -> tuple[FallbackEvidence, ...]:
    return tuple(
        FallbackEvidence(
            chunk_id=item.nomination.chunk_id,
            doc_id=item.nomination.doc_id,
            version=item.nomination.version,
            status=item.nomination.status,
            section_heading=item.nomination.section_heading,
            source_hash=item.nomination.source_hash,
            char_start=item.nomination.char_start,
            char_end=item.nomination.char_end,
            text=item.nomination.text,
        )
        for item in packet.admitted
    )


def _fallback_result(
    packet: EvidencePacket,
    *,
    generator: Generator | None,
    generator_called: bool,
    issues: list[GateIssue],
    generated_disposition: GeneratedDisposition | None = None,
    dropped_claims: tuple[DroppedClaim, ...] = (),
) -> SynthesisResult:
    return SynthesisResult(
        outcome="answer",
        disposition="extractive_fallback",
        packet_identity=packet.packet_identity,
        generator=(
            _generator_metadata(generator)
            if generator is not None
            else None
        ),
        generator_called=generator_called,
        generated_disposition=generated_disposition,
        claims=(),
        gaps=(),
        dropped_claims=dropped_claims,
        gate_issues=tuple(issues),
        fallback_evidence=_fallback_evidence(packet),
    )


def _claim_gate_issues(
    claim: GeneratedClaim,
    packet_map: dict[str, RetrievalNomination],
) -> list[GateIssue]:
    issues: list[GateIssue] = []
    cited: list[RetrievalNomination] = []

    for citation in claim.citations:
        nomination = packet_map.get(citation.chunk_id)
        if nomination is None:
            issues.append(
                GateIssue(
                    gate="G2",
                    code="citation_outside_packet",
                    claim_id=claim.claim_id,
                    message=f"chunk_id {citation.chunk_id!r} is not admitted to the packet",
                )
            )
            continue
        cited.append(nomination)
        if not _quote_is_contained(citation.quote, nomination):
            issues.append(
                GateIssue(
                    gate="G3",
                    code="quote_not_contained",
                    claim_id=claim.claim_id,
                    message=f"quote is not contained in packet chunk {citation.chunk_id}",
                )
            )

    # Later gates consume only citations that passed packet membership and containment.
    if any(issue.gate in {"G2", "G3"} for issue in issues):
        return issues

    quote_text = "\n".join(citation.quote for citation in claim.citations)
    claim_quantities = _quantity_tokens(claim.text)
    quote_quantities = _quantity_tokens(quote_text)
    missing_quantities = sorted(claim_quantities - quote_quantities)
    if missing_quantities:
        issues.append(
            GateIssue(
                gate="G4",
                code="ungrounded_quantity",
                claim_id=claim.claim_id,
                message=f"claim quantity/unit tokens are not grounded: {missing_quantities}",
            )
        )

    claim_ids = _identifiers(claim.text)
    grounded_ids = _identifiers(quote_text)
    for nomination in cited:
        grounded_ids.update(_metadata_identifiers(nomination))
    missing_ids = sorted(claim_ids - grounded_ids)
    if missing_ids:
        issues.append(
            GateIssue(
                gate="G5",
                code="ungrounded_identifier",
                claim_id=claim.claim_id,
                message=f"claim identifiers are not grounded: {missing_ids}",
            )
        )

    disallowed_roles = {"revision_history", "references"}
    if cited and all(
        nomination.section_role in disallowed_roles
        for nomination in cited
    ):
        issues.append(
            GateIssue(
                gate="G6",
                code="non_normative_only",
                claim_id=claim.claim_id,
                message="claim relies only on revision-history/reference material",
            )
        )

    return issues


def _gap_g7_issues(
    gap: GeneratedGap,
    packet_map: dict[str, RetrievalNomination],
) -> list[GateIssue]:
    issues: list[GateIssue] = []
    citation = gap.topic_citation
    nomination = packet_map.get(citation.chunk_id)
    if nomination is None:
        return [
            GateIssue(
                gate="G7",
                code="gap_citation_outside_packet",
                message=f"gap citation {citation.chunk_id!r} is outside the packet",
            )
        ]
    if not _quote_is_contained(citation.quote, nomination):
        issues.append(
            GateIssue(
                gate="G7",
                code="gap_quote_not_contained",
                message=f"gap quote is not contained in packet chunk {citation.chunk_id}",
            )
        )
        return issues

    gap_quantities = _quantity_tokens(gap.statement)
    quote_quantities = _quantity_tokens(citation.quote)
    missing_quantities = sorted(gap_quantities - quote_quantities)
    if missing_quantities:
        issues.append(
            GateIssue(
                gate="G7",
                code="gap_ungrounded_quantity",
                message=f"gap statement has ungrounded quantity/unit tokens: {missing_quantities}",
            )
        )

    gap_ids = _identifiers(gap.statement)
    grounded_ids = _identifiers(citation.quote) | _metadata_identifiers(nomination)
    missing_ids = sorted(gap_ids - grounded_ids)
    if missing_ids:
        issues.append(
            GateIssue(
                gate="G7",
                code="gap_ungrounded_identifier",
                message=f"gap statement has ungrounded identifiers: {missing_ids}",
            )
        )
    return issues


def _global_g7_issues(
    answer: GeneratedAnswer,
    packet_map: dict[str, RetrievalNomination],
) -> list[GateIssue]:
    issues: list[GateIssue] = []
    if answer.disposition == "answered" and not answer.claims:
        issues.append(
            GateIssue(
                gate="G7",
                code="answered_without_claims",
                message="answered disposition requires at least one claim",
            )
        )
    elif answer.disposition == "partially_answered":
        if not answer.claims:
            issues.append(
                GateIssue(
                    gate="G7",
                    code="partial_without_claims",
                    message="partially_answered requires at least one claim",
                )
            )
        if not answer.gaps:
            issues.append(
                GateIssue(
                    gate="G7",
                    code="partial_without_gaps",
                    message="partially_answered requires at least one gap",
                )
            )
    elif answer.disposition == "not_stated":
        if answer.claims:
            issues.append(
                GateIssue(
                    gate="G7",
                    code="not_stated_with_claims",
                    message="not_stated cannot carry material claims",
                )
            )
        if not answer.gaps:
            issues.append(
                GateIssue(
                    gate="G7",
                    code="not_stated_without_gap",
                    message="not_stated requires at least one cited gap",
                )
            )
    elif answer.disposition == "insufficient_evidence" and answer.claims:
        issues.append(
            GateIssue(
                gate="G7",
                code="insufficient_with_claims",
                message="insufficient_evidence cannot carry material claims",
            )
        )

    for gap in answer.gaps:
        issues.extend(_gap_g7_issues(gap, packet_map))
    return issues


def run_shadow_synthesis(
    packet: EvidencePacket,
    generator: Generator | None,
) -> SynthesisResult:
    """Run one generator candidate through G1-G7 without changing the product answer path."""
    if not packet.admitted:
        return SynthesisResult(
            outcome="refusal",
            disposition="refusal",
            packet_identity=packet.packet_identity,
            generator=(
                _generator_metadata(generator)
                if generator is not None
                else None
            ),
            generator_called=False,
            gate_issues=(),
            fallback_evidence=(),
        )

    if generator is None:
        raise GeneratorUnavailableError(
            "shadow generator is not configured for a non-empty evidence packet"
        )

    try:
        raw_output = generator.generate(packet)
    except Exception as exc:
        issue = GateIssue(
            gate="provider",
            code="provider_error",
            message=f"{type(exc).__name__}: {exc}",
        )
        return _fallback_result(
            packet,
            generator=generator,
            generator_called=True,
            issues=[issue],
        )

    try:
        answer = GeneratedAnswer.model_validate(raw_output)
    except ValidationError as exc:
        issue = GateIssue(
            gate="G1",
            code="schema_invalid",
            message=str(exc),
        )
        return _fallback_result(
            packet,
            generator=generator,
            generator_called=True,
            issues=[issue],
        )

    packet_map = _packet_chunks(packet)
    g7_issues = _global_g7_issues(answer, packet_map)
    if g7_issues:
        return _fallback_result(
            packet,
            generator=generator,
            generator_called=True,
            issues=g7_issues,
            generated_disposition=answer.disposition,
        )

    if answer.disposition == "not_stated":
        return SynthesisResult(
            outcome="answer",
            disposition="not_stated",
            packet_identity=packet.packet_identity,
            generator=_generator_metadata(generator),
            generator_called=True,
            generated_disposition=answer.disposition,
            claims=(),
            gaps=answer.gaps,
            dropped_claims=(),
            gate_issues=(),
            fallback_evidence=(),
        )

    if answer.disposition == "insufficient_evidence":
        return SynthesisResult(
            outcome="refusal",
            disposition="refusal",
            packet_identity=packet.packet_identity,
            generator=_generator_metadata(generator),
            generator_called=True,
            generated_disposition=answer.disposition,
            claims=(),
            gaps=answer.gaps,
            dropped_claims=(),
            gate_issues=(),
            fallback_evidence=_fallback_evidence(packet),
        )

    accepted_claims: list[GeneratedClaim] = []
    dropped_claims: list[DroppedClaim] = []
    issues: list[GateIssue] = []

    for claim in answer.claims:
        claim_issues = _claim_gate_issues(claim, packet_map)
        if claim_issues:
            issues.extend(claim_issues)
            dropped_claims.append(
                DroppedClaim(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    gates=tuple(
                        dict.fromkeys(issue.gate for issue in claim_issues)
                    ),
                )
            )
        else:
            accepted_claims.append(claim)

    if answer.claims and not accepted_claims:
        return _fallback_result(
            packet,
            generator=generator,
            generator_called=True,
            issues=issues,
            generated_disposition=answer.disposition,
            dropped_claims=tuple(dropped_claims),
        )

    disposition: DisplayDisposition = (
        "generated_with_gaps"
        if answer.gaps or dropped_claims
        else "generated"
    )
    return SynthesisResult(
        outcome="answer",
        disposition=disposition,
        packet_identity=packet.packet_identity,
        generator=_generator_metadata(generator),
        generator_called=True,
        generated_disposition=answer.disposition,
        claims=tuple(accepted_claims),
        gaps=answer.gaps,
        dropped_claims=tuple(dropped_claims),
        gate_issues=tuple(issues),
        fallback_evidence=(),
    )
