from __future__ import annotations

from pathlib import Path

from biotech_rag_assistant.chunking import chunk_document
from biotech_rag_assistant.evidence import EvidencePacket, build_evidence_packet
from biotech_rag_assistant.generation import (
    GeneratedAnswer,
    GeneratedCitation,
    GeneratedClaim,
    GeneratedGap,
    ScriptedGenerator,
    run_shadow_synthesis,
)
from biotech_rag_assistant.models import (
    Corpus,
    DocumentMetadata,
    IngestReport,
    RetrievalHit,
    SourceDocument,
)
from biotech_rag_assistant.retrieval import RetrievalConfig

SOURCE_HASH = "sha256:" + ("c" * 64)
VALID_TEXT = (
    "The 100 g reading must be within 0.3 mg and the result is recorded on FRM-QA-201."
)


def make_packet(
    text: str = VALID_TEXT,
    *,
    heading: str = "Procedure",
    hits: bool = True,
) -> EvidencePacket:
    raw = f"# Demo SOP\n\n## {heading}\n\n{text}\n"
    metadata = DocumentMetadata(
        doc_id="SOP-DEMO-001",
        doc_title="Demo SOP",
        doc_type="SOP",
        version="1.0",
        status="Effective",
        effective_date="2026-01-01",
        department="QA",
        source_file_path=Path("documents/SOP-DEMO-001.md"),
        source_hash=SOURCE_HASH,
    )
    document = SourceDocument(
        metadata_path=Path("/tmp/metadata/SOP-DEMO-001.yaml"),
        content_path=Path("/tmp/documents/SOP-DEMO-001.md"),
        raw_text=raw,
        computed_source_hash=SOURCE_HASH,
        metadata=metadata,
    )
    corpus = Corpus(
        corpus_dir=Path("/tmp"),
        documents=[document],
        report=IngestReport(
            corpus_dir=Path("/tmp"),
            metadata_files_seen=1,
            documents_valid=1,
            documents_retrievable=1,
            documents_excluded=0,
            issues=[],
        ),
    )
    chunk = chunk_document(document)[0]
    retrieval_hits = (
        [RetrievalHit(rank=1, score=5.0, chunk=chunk)]
        if hits
        else []
    )
    return build_evidence_packet(
        corpus=corpus,
        query="What is the documented requirement?",
        hits=retrieval_hits,
        config=RetrievalConfig(top_k=1),
    )


def citation(packet: EvidencePacket, quote: str = VALID_TEXT) -> GeneratedCitation:
    return GeneratedCitation(
        chunk_id=packet.admitted[0].nomination.chunk_id,
        quote=quote,
    )


def valid_answer(packet: EvidencePacket) -> GeneratedAnswer:
    return GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C1",
                text=VALID_TEXT,
                citations=(citation(packet),),
            ),
        ),
    )


def issue_gates(result) -> set[str]:
    return {issue.gate for issue in result.gate_issues}


def test_valid_answer_passes_all_deterministic_gates() -> None:
    packet = make_packet()
    generator = ScriptedGenerator(valid_answer(packet))

    result = run_shadow_synthesis(packet, generator)

    assert result.outcome == "answer"
    assert result.disposition == "generated"
    assert result.generator_called is True
    assert result.claims == valid_answer(packet).claims
    assert result.gate_issues == ()
    assert result.fallback_evidence == ()
    assert generator.call_count == 1


def test_g1_schema_breaker_falls_back() -> None:
    packet = make_packet()
    raw = valid_answer(packet).model_dump()
    raw["unexpected"] = "not allowed"
    generator = ScriptedGenerator(raw)

    result = run_shadow_synthesis(packet, generator)

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G1"}
    assert result.fallback_evidence


def test_g2_out_of_packet_citation_drops_claim_and_falls_back() -> None:
    packet = make_packet()
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C2",
                text=VALID_TEXT,
                citations=(
                    GeneratedCitation(
                        chunk_id="outside_packet_chunk",
                        quote=VALID_TEXT,
                    ),
                ),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G2"}
    assert result.dropped_claims[0].gates == ("G2",)


def test_g3_forged_quote_drops_claim_and_falls_back() -> None:
    packet = make_packet()
    forged = VALID_TEXT.replace("0.3 mg", "0.4 mg")
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C3",
                text=VALID_TEXT,
                citations=(citation(packet, forged),),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G3"}


def test_g4_fabricated_quantity_drops_claim_and_falls_back() -> None:
    packet = make_packet()
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C4",
                text=VALID_TEXT.replace("0.3 mg", "0.5 mg"),
                citations=(citation(packet),),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G4"}


def test_g4_normalizes_number_words_for_grounding() -> None:
    packet = make_packet("The review is completed within 3 working days.")
    quote = "The review is completed within 3 working days."
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C4W",
                text="The review is completed within three working days.",
                citations=(citation(packet, quote),),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "generated"
    assert result.gate_issues == ()


def test_g5_fabricated_identifier_drops_claim_and_falls_back() -> None:
    packet = make_packet()
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C5",
                text=VALID_TEXT.replace("FRM-QA-201", "FRM-QA-999"),
                citations=(citation(packet),),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G5"}


def test_g6_revision_history_only_claim_drops_and_falls_back() -> None:
    text = "The previous limit was 0.5 mg."
    packet = make_packet(text, heading="Revision History")
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(
            GeneratedClaim(
                claim_id="C6",
                text=text,
                citations=(citation(packet, text),),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G6"}


def test_g7_insufficient_evidence_cannot_carry_claims() -> None:
    packet = make_packet()
    raw = GeneratedAnswer(
        disposition="insufficient_evidence",
        claims=valid_answer(packet).claims,
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G7"}


def test_g7_not_stated_gap_cannot_invent_a_value() -> None:
    packet = make_packet()
    raw = GeneratedAnswer(
        disposition="not_stated",
        gaps=(
            GeneratedGap(
                asked_about="daily tolerance",
                statement="The daily tolerance is 0.5 mg.",
                topic_citation=citation(packet),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"G7"}


def test_valid_not_stated_gap_passes_with_topic_citation() -> None:
    text = "The procedure refers to the acceptance range in the manufacturer datasheet."
    packet = make_packet(text)
    raw = GeneratedAnswer(
        disposition="not_stated",
        gaps=(
            GeneratedGap(
                asked_about="acceptance range value",
                statement="The procedure refers to the acceptance range but does not state its value.",
                topic_citation=citation(packet, text),
            ),
        ),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.outcome == "answer"
    assert result.disposition == "not_stated"
    assert result.gate_issues == ()
    assert len(result.gaps) == 1


def test_empty_packet_refuses_without_calling_generator() -> None:
    packet = make_packet(hits=False)
    generator = ScriptedGenerator({"not": "used"})

    result = run_shadow_synthesis(packet, generator)

    assert result.outcome == "refusal"
    assert result.disposition == "refusal"
    assert result.generator_called is False
    assert generator.call_count == 0


def test_provider_exception_is_labelled_fallback() -> None:
    packet = make_packet()
    generator = ScriptedGenerator(exception=RuntimeError("provider unavailable"))

    result = run_shadow_synthesis(packet, generator)

    assert result.outcome == "answer"
    assert result.disposition == "extractive_fallback"
    assert issue_gates(result) == {"provider"}
    assert result.generator_called is True
    assert result.fallback_evidence


def test_one_bad_claim_does_not_erase_a_valid_claim() -> None:
    packet = make_packet()
    valid = valid_answer(packet).claims[0]
    bad = GeneratedClaim(
        claim_id="C-bad",
        text=VALID_TEXT.replace("0.3 mg", "9.9 mg"),
        citations=(citation(packet),),
    )
    raw = GeneratedAnswer(
        disposition="answered",
        claims=(valid, bad),
    )

    result = run_shadow_synthesis(packet, ScriptedGenerator(raw))

    assert result.outcome == "answer"
    assert result.disposition == "generated_with_gaps"
    assert [claim.claim_id for claim in result.claims] == ["C1"]
    assert [claim.claim_id for claim in result.dropped_claims] == ["C-bad"]
    assert issue_gates(result) == {"G4"}
