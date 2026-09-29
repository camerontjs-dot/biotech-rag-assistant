"""Shadow generation contracts and deterministic claim gates G1-G7."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from biotech_rag_assistant.evidence_packet import EvidencePacket, RetrievalNomination

GeneratorDisposition = Literal[
    "answered",
    "partially_answered",
    "not_stated",
    "insufficient_evidence",
]
PublicDisposition = Literal[
    "generated",
    "generated_with_gaps",
    "not_stated",
    "extractive_fallback",
    "refusal",
]
Outcome = Literal["answer", "refusal"]

IDENTIFIER_RE = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")
REQUIREMENT_RE = re.compile(
    r"\b(must|shall|required|requires?|limit|within|at least)\b|no more than",
    re.IGNORECASE,
)
WHITESPACE_RE = re.compile(r"\s+")

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
TENS = {word for word, value in NUMBER_WORDS.items() if value >= 20 and value % 10 == 0}

UNIT_PATTERN = (
    r"(?:%|percent|percentage|working days?|calendar days?|days?|hours?|minutes?|"
    r"seconds?|weeks?|months?|years?|mg|ug|kg|g|ml|l|ppb|ppm|cfu(?: per (?:m3|ml|"
    r"100 ml|plate))?|us/cm|degrees? c|°c|l/min)"
)
QUANTITY_RE = re.compile(
    rf"(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?"
    rf"(?:\s*(?:to|through|-)\s*[-+]?\d+(?:\.\d+)?)?"
    rf"(?:\s*{UNIT_PATTERN})?",
    re.IGNORECASE,
)


class GeneratedCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class GeneratedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    citations: list[GeneratedCitation] = Field(min_length=1)
    qualifier: str | None = None
    limitation: str | None = None


class GeneratedGap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asked_about: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    topic_citation: GeneratedCitation


class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disposition: GeneratorDisposition
    claims: list[GeneratedClaim] = Field(default_factory=list)
    gaps: list[GeneratedGap] = Field(default_factory=list)


class GateIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gate: Literal["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
    code: str
    message: str
    claim_id: str | None = None
    gap_index: int | None = None


class ClaimGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    accepted: bool
    passed_gates: list[str]
    issues: list[GateIssue]


class ShadowSynthesisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Outcome
    disposition: PublicDisposition
    packet_id: str
    accepted_claims: list[GeneratedClaim]
    accepted_gaps: list[GeneratedGap]
    claim_gate_results: list[ClaimGateResult]
    issues: list[GateIssue]
    generator_model_id: str | None = None
    prompt_hash: str | None = None
    generator_called: bool
    fallback_reason: str | None = None

    def to_record(self) -> dict[str, object]:
        return self.model_dump()


class Generator(Protocol):
    model_id: str
    prompt_hash: str

    def generate(self, packet: EvidencePacket) -> object: ...


class ScriptedGenerator:
    """Fixture generator with no tools or external access."""

    def __init__(
        self,
        payload: object,
        *,
        model_id: str = "scripted-generator-v1",
        prompt_text: str = "scripted fixture",
    ) -> None:
        self.payload = payload
        self.model_id = model_id
        self.prompt_hash = "sha256:" + hashlib.sha256(
            prompt_text.encode("utf-8")
        ).hexdigest()
        self.call_count = 0

    def generate(self, packet: EvidencePacket) -> object:
        self.call_count += 1
        return self.payload


def normalize_source_text(text: str) -> str:
    """NFC plus deterministic whitespace normalization used by G3-G5."""
    return WHITESPACE_RE.sub(
        " ",
        unicodedata.normalize("NFC", text).strip(),
    )


def _normalize_number_words(text: str) -> str:
    tokens = re.findall(r"\w+|[^\w\s]+|\s+", text)
    out: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        lowered = token.lower()
        if lowered == "one":
            j = i + 1
            while j < len(tokens) and tokens[j].isspace():
                j += 1
            if j < len(tokens) and tokens[j].lower() == "hundred":
                value = 100
                k = j + 1
                while k < len(tokens) and tokens[k].isspace():
                    k += 1
                if k < len(tokens) and tokens[k].lower() in NUMBER_WORDS:
                    tail = NUMBER_WORDS[tokens[k].lower()]
                    if tail < 100:
                        value += tail
                        i = k + 1
                    else:
                        i = j + 1
                else:
                    i = j + 1
                out.append(str(value))
                continue
        if lowered in TENS:
            value = NUMBER_WORDS[lowered]
            j = i + 1
            while j < len(tokens) and tokens[j].isspace():
                j += 1
            if (
                j < len(tokens)
                and tokens[j].lower() in NUMBER_WORDS
                and 0 < NUMBER_WORDS[tokens[j].lower()] < 10
            ):
                value += NUMBER_WORDS[tokens[j].lower()]
                i = j + 1
                out.append(str(value))
                continue
        if lowered in NUMBER_WORDS:
            out.append(str(NUMBER_WORDS[lowered]))
        else:
            out.append(token)
        i += 1
    return "".join(out)


def normalized_for_grounding(text: str) -> str:
    return normalize_source_text(_normalize_number_words(text)).lower()


def quantity_atoms(text: str) -> list[str]:
    normalized = normalized_for_grounding(text)
    return [
        normalize_source_text(match.group(0)).lower()
        for match in QUANTITY_RE.finditer(normalized)
    ]


def identifiers(text: str) -> set[str]:
    return set(IDENTIFIER_RE.findall(normalize_source_text(text)))


def _packet_lookup(packet: EvidencePacket) -> dict[str, RetrievalNomination]:
    return {
        nomination.chunk_id: nomination
        for nomination in packet.admitted_nominations
    }


def _validate_citation(
    citation: GeneratedCitation,
    packet_lookup: dict[str, RetrievalNomination],
    *,
    claim_id: str | None = None,
    gap_index: int | None = None,
) -> tuple[RetrievalNomination | None, list[GateIssue]]:
    nomination = packet_lookup.get(citation.chunk_id)
    if nomination is None:
        return None, [
            GateIssue(
                gate="G2",
                code="citation_outside_packet",
                message=f"chunk_id {citation.chunk_id!r} is not admitted",
                claim_id=claim_id,
                gap_index=gap_index,
            )
        ]

    quote = normalize_source_text(citation.quote)
    source = normalize_source_text(nomination.text)
    if not quote or quote not in source:
        return nomination, [
            GateIssue(
                gate="G3",
                code="quote_not_contained",
                message="quote is not an exact normalized substring of the admitted chunk",
                claim_id=claim_id,
                gap_index=gap_index,
            )
        ]
    return nomination, []


def _quantity_issues(
    claim: GeneratedClaim,
    accepted_quotes: list[str],
) -> list[GateIssue]:
    quote_text = normalized_for_grounding(" ".join(accepted_quotes))
    issues = []
    for atom in quantity_atoms(claim.text):
        if atom not in quote_text:
            issues.append(
                GateIssue(
                    gate="G4",
                    code="ungrounded_quantity",
                    message=f"quantity {atom!r} does not occur in the claim quotes",
                    claim_id=claim.claim_id,
                )
            )
    return issues


def _identifier_issues(
    claim: GeneratedClaim,
    accepted_quotes: list[str],
    nominations: list[RetrievalNomination],
) -> list[GateIssue]:
    quote_text = normalize_source_text(" ".join(accepted_quotes))
    metadata_text = normalize_source_text(
        " ".join(
            " ".join(
                (
                    item.doc_id,
                    item.chunk_id,
                    item.section_heading,
                    str(item.source_hash),
                    item.expansion_handle,
                )
            )
            for item in nominations
        )
    )
    allowed = identifiers(quote_text) | identifiers(metadata_text)
    return [
        GateIssue(
            gate="G5",
            code="ungrounded_identifier",
            message=f"identifier {identifier!r} is absent from quotes and cited metadata",
            claim_id=claim.claim_id,
        )
        for identifier in sorted(identifiers(claim.text) - allowed)
    ]


def _section_role_issues(
    claim: GeneratedClaim,
    nominations: list[RetrievalNomination],
) -> list[GateIssue]:
    if not REQUIREMENT_RE.search(claim.text):
        return []
    if nominations and all(
        item.section_role in {"revision_history", "references"}
        for item in nominations
    ):
        return [
            GateIssue(
                gate="G6",
                code="current_requirement_from_non_normative_section",
                message=(
                    "current-requirement language cannot rest only on "
                    "revision-history or references sections"
                ),
                claim_id=claim.claim_id,
            )
        ]
    return []


def evaluate_claim(
    claim: GeneratedClaim,
    packet: EvidencePacket,
) -> ClaimGateResult:
    lookup = _packet_lookup(packet)
    issues: list[GateIssue] = []
    nominations: list[RetrievalNomination] = []
    quotes: list[str] = []

    for citation in claim.citations:
        nomination, citation_issues = _validate_citation(
            citation,
            lookup,
            claim_id=claim.claim_id,
        )
        issues.extend(citation_issues)
        if nomination is not None and not citation_issues:
            nominations.append(nomination)
            quotes.append(citation.quote)

    failed = {issue.gate for issue in issues}
    if not failed & {"G2", "G3"}:
        issues.extend(_quantity_issues(claim, quotes))
        issues.extend(_identifier_issues(claim, quotes, nominations))
        issues.extend(_section_role_issues(claim, nominations))

    failed = {issue.gate for issue in issues}
    return ClaimGateResult(
        claim_id=claim.claim_id,
        accepted=not failed,
        passed_gates=[
            gate
            for gate in ("G2", "G3", "G4", "G5", "G6")
            if gate not in failed
        ],
        issues=issues,
    )


def _validate_gaps(
    gaps: list[GeneratedGap],
    packet: EvidencePacket,
) -> tuple[list[GeneratedGap], list[GateIssue]]:
    lookup = _packet_lookup(packet)
    accepted = []
    issues: list[GateIssue] = []
    for index, gap in enumerate(gaps):
        _nomination, citation_issues = _validate_citation(
            gap.topic_citation,
            lookup,
            gap_index=index,
        )
        issues.extend(citation_issues)
        if not citation_issues:
            accepted.append(gap)
    return accepted, issues


def _g7_issues(
    generated: GeneratedAnswer,
    accepted_claims: list[GeneratedClaim],
    accepted_gaps: list[GeneratedGap],
    gap_issues: list[GateIssue],
) -> list[GateIssue]:
    issues = list(gap_issues)
    if generated.disposition in {"not_stated", "insufficient_evidence"} and generated.claims:
        issues.append(
            GateIssue(
                gate="G7",
                code="abstention_with_claims",
                message="not_stated/insufficient_evidence must not carry claims",
            )
        )
    if generated.disposition == "answered" and not accepted_claims:
        issues.append(
            GateIssue(
                gate="G7",
                code="answered_without_surviving_claim",
                message="answered requires at least one surviving claim",
            )
        )
    if generated.disposition == "partially_answered":
        if not accepted_claims or not accepted_gaps:
            issues.append(
                GateIssue(
                    gate="G7",
                    code="partial_without_claim_and_gap",
                    message="partially_answered requires a surviving claim and gap",
                )
            )
    if generated.disposition == "not_stated":
        if accepted_claims or not accepted_gaps:
            issues.append(
                GateIssue(
                    gate="G7",
                    code="invalid_not_stated_shape",
                    message="not_stated requires zero claims and at least one valid topic gap",
                )
            )
    if generated.disposition == "insufficient_evidence" and accepted_claims:
        issues.append(
            GateIssue(
                gate="G7",
                code="invalid_insufficient_evidence_shape",
                message="insufficient_evidence cannot carry surviving claims",
            )
        )
    return issues


def synthesize_shadow(
    packet: EvidencePacket,
    generator: Generator,
) -> ShadowSynthesisResult:
    """Run a provider-neutral generator behind blocking structural gates."""
    if not packet.admitted_nominations:
        return ShadowSynthesisResult(
            outcome="refusal",
            disposition="refusal",
            packet_id=packet.packet_id,
            accepted_claims=[],
            accepted_gaps=[],
            claim_gate_results=[],
            issues=[],
            generator_model_id=None,
            prompt_hash=None,
            generator_called=False,
            fallback_reason="empty_packet",
        )

    try:
        raw = generator.generate(packet)
        generated = GeneratedAnswer.model_validate(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        issue = GateIssue(
            gate="G1",
            code="schema_invalid",
            message=str(exc),
        )
        return ShadowSynthesisResult(
            outcome="answer",
            disposition="extractive_fallback",
            packet_id=packet.packet_id,
            accepted_claims=[],
            accepted_gaps=[],
            claim_gate_results=[],
            issues=[issue],
            generator_model_id=getattr(generator, "model_id", None),
            prompt_hash=getattr(generator, "prompt_hash", None),
            generator_called=True,
            fallback_reason="G1",
        )

    claim_results = [
        evaluate_claim(claim, packet)
        for claim in generated.claims
    ]
    accepted_claims = [
        claim
        for claim, result in zip(
            generated.claims,
            claim_results,
            strict=True,
        )
        if result.accepted
    ]
    claim_issues = [
        issue
        for result in claim_results
        for issue in result.issues
    ]
    accepted_gaps, gap_issues = _validate_gaps(generated.gaps, packet)

    if (
        generated.disposition in {"answered", "partially_answered"}
        and generated.claims
        and not accepted_claims
    ):
        return ShadowSynthesisResult(
            outcome="answer",
            disposition="extractive_fallback",
            packet_id=packet.packet_id,
            accepted_claims=[],
            accepted_gaps=accepted_gaps,
            claim_gate_results=claim_results,
            issues=claim_issues + gap_issues,
            generator_model_id=generator.model_id,
            prompt_hash=generator.prompt_hash,
            generator_called=True,
            fallback_reason="all_claims_dropped",
        )

    g7 = _g7_issues(
        generated,
        accepted_claims,
        accepted_gaps,
        gap_issues,
    )
    all_issues = claim_issues + g7

    if g7:
        return ShadowSynthesisResult(
            outcome="answer",
            disposition="extractive_fallback",
            packet_id=packet.packet_id,
            accepted_claims=accepted_claims,
            accepted_gaps=accepted_gaps,
            claim_gate_results=claim_results,
            issues=all_issues,
            generator_model_id=generator.model_id,
            prompt_hash=generator.prompt_hash,
            generator_called=True,
            fallback_reason="G7",
        )

    if generated.disposition == "not_stated":
        public_disposition: PublicDisposition = "not_stated"
        outcome: Outcome = "answer"
    elif generated.disposition == "insufficient_evidence":
        public_disposition = "refusal"
        outcome = "refusal"
    elif generated.disposition == "partially_answered":
        public_disposition = "generated_with_gaps"
        outcome = "answer"
    else:
        public_disposition = "generated"
        outcome = "answer"

    return ShadowSynthesisResult(
        outcome=outcome,
        disposition=public_disposition,
        packet_id=packet.packet_id,
        accepted_claims=accepted_claims,
        accepted_gaps=accepted_gaps,
        claim_gate_results=claim_results,
        issues=all_issues,
        generator_model_id=generator.model_id,
        prompt_hash=generator.prompt_hash,
        generator_called=True,
    )


def scripted_payload_hash(payload: object) -> str:
    """Stable fixture identifier for receipts."""
    return "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
