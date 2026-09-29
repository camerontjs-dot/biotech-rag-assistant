from __future__ import annotations

from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.evidence_packet import (
    EvidenceBudget,
    EvidencePacket,
    _packet_identity_payload,
    build_evidence_packet,
    stable_hash,
)
from biotech_rag_assistant.generation import ScriptedGenerator, synthesize_shadow
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "examples/synthetic-controlled-docs"
QUERY = "viable excursion affected product lots immediate containment"


def make_packet(
    *,
    top_k: int = 3,
    max_items: int = 3,
) -> tuple[EvidencePacket, list]:
    corpus = load_corpus(CORPUS_DIR)
    config = RetrievalConfig(top_k=top_k)
    hits = run_retrieval(corpus.documents, QUERY, config)
    packet = build_evidence_packet(
        corpus,
        QUERY,
        hits,
        config,
        budget=EvidenceBudget(
            max_items=max_items,
            max_context_chars=12_000,
        ),
    )
    return packet, hits


def reidentify(packet: EvidencePacket) -> EvidencePacket:
    payload = _packet_identity_payload(
        query=packet.query,
        corpus=packet.corpus_identity,
        retrieval_config=packet.retrieval_config_id,
        aperture_id=packet.aperture_id,
        admitted=packet.admitted_nominations,
        exclusion_summary=packet.exclusion_summary,
    )
    return packet.model_copy(
        update={"packet_id": stable_hash("ep1", payload)}
    )


def one_claim(
    *,
    text: str,
    chunk_id: str,
    quote: str,
    claim_id: str = "c1",
) -> dict:
    return {
        "claim_id": claim_id,
        "text": text,
        "citations": [{"chunk_id": chunk_id, "quote": quote}],
    }


def test_packet_identity_mismatch_blocks_generation_before_model_call() -> None:
    packet, _hits = make_packet()
    first = packet.admitted_nominations[0]
    tampered = packet.model_copy(
        update={"query": "a different query with the old packet id"}
    )
    generator = ScriptedGenerator(
        {
            "disposition": "answered",
            "claims": [
                one_claim(
                    text=first.text,
                    chunk_id=first.chunk_id,
                    quote=first.text,
                )
            ],
            "gaps": [],
        }
    )

    result = synthesize_shadow(tampered, generator)

    assert result.disposition == "refusal"
    assert result.outcome == "refusal"
    assert result.generator_called is False
    assert result.fallback_reason == "packet_identity_invalid"
    assert generator.call_count == 0


def test_g4_does_not_ground_5_days_from_quote_saying_15_days() -> None:
    packet, _hits = make_packet(top_k=1, max_items=1)
    item = packet.admitted_nominations[0].model_copy(
        update={"text": "The closure is required within 15 days."}
    )
    synthetic = reidentify(
        packet.model_copy(update={"admitted_nominations": [item]})
    )
    generator = ScriptedGenerator(
        {
            "disposition": "answered",
            "claims": [
                one_claim(
                    text="The closure is required within 5 days.",
                    chunk_id=item.chunk_id,
                    quote=item.text,
                )
            ],
            "gaps": [],
        }
    )

    result = synthesize_shadow(synthetic, generator)

    assert result.disposition == "extractive_fallback"
    assert any(issue.gate == "G4" for issue in result.issues)


def test_g4_binds_quantity_units_exactly() -> None:
    packet, _hits = make_packet(top_k=1, max_items=1)
    item = packet.admitted_nominations[0].model_copy(
        update={"text": "The hold time is 5 days."}
    )
    synthetic = reidentify(
        packet.model_copy(update={"admitted_nominations": [item]})
    )
    generator = ScriptedGenerator(
        {
            "disposition": "answered",
            "claims": [
                one_claim(
                    text="The hold time is 5 hours.",
                    chunk_id=item.chunk_id,
                    quote=item.text,
                )
            ],
            "gaps": [],
        }
    )

    result = synthesize_shadow(synthetic, generator)

    assert result.disposition == "extractive_fallback"
    assert any(issue.gate == "G4" for issue in result.issues)


def test_g5_catches_lowercase_fabricated_identifier() -> None:
    packet, _hits = make_packet(top_k=1, max_items=1)
    item = packet.admitted_nominations[0].model_copy(
        update={"text": "The assigned equipment is EQ-0417."}
    )
    synthetic = reidentify(
        packet.model_copy(update={"admitted_nominations": [item]})
    )
    generator = ScriptedGenerator(
        {
            "disposition": "answered",
            "claims": [
                one_claim(
                    text="The assigned equipment is eq-9999.",
                    chunk_id=item.chunk_id,
                    quote=item.text,
                )
            ],
            "gaps": [],
        }
    )

    result = synthesize_shadow(synthetic, generator)

    assert result.disposition == "extractive_fallback"
    assert any(issue.gate == "G5" for issue in result.issues)


def test_one_valid_claim_survives_when_sibling_claim_fails_g4() -> None:
    packet, _hits = make_packet(top_k=1, max_items=1)
    item = packet.admitted_nominations[0]
    payload = {
        "disposition": "answered",
        "claims": [
            one_claim(
                text=item.text,
                chunk_id=item.chunk_id,
                quote=item.text,
                claim_id="valid",
            ),
            one_claim(
                text="The unsupported deadline is 999 days.",
                chunk_id=item.chunk_id,
                quote=item.text,
                claim_id="invalid",
            ),
        ],
        "gaps": [],
    }

    result = synthesize_shadow(packet, ScriptedGenerator(payload))

    assert result.disposition == "generated"
    assert [claim.claim_id for claim in result.accepted_claims] == ["valid"]
    assert any(
        issue.gate == "G4" and issue.claim_id == "invalid"
        for issue in result.issues
    )


def test_existing_but_unadmitted_chunk_still_fails_packet_membership() -> None:
    packet, hits = make_packet(top_k=5, max_items=1)
    assert len(hits) >= 2
    unadmitted = hits[1].chunk
    assert unadmitted.chunk_id not in {
        item.chunk_id for item in packet.admitted_nominations
    }
    payload = {
        "disposition": "answered",
        "claims": [
            one_claim(
                text=unadmitted.text,
                chunk_id=unadmitted.chunk_id,
                quote=unadmitted.text,
            )
        ],
        "gaps": [],
    }

    result = synthesize_shadow(packet, ScriptedGenerator(payload))

    assert result.disposition == "extractive_fallback"
    assert any(issue.gate == "G2" for issue in result.issues)
