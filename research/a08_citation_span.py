"""Deterministic A08 citation-span comparison.

No model call. The historical packet judgment is inherited from the frozen
PR #20 record. This module only checks span identity, provenance, and whether
the widened quote is the sentence that record already named.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CLAIM = "Both operations and QA must sign the clearance record before the run starts."
HISTORICAL_QUOTE = "both operations and QA sign the clearance record"
CASE_ID = "A08-line-clearance-signatories"
DOC_ID = "SOP-OPS-007"
VERSION = "1.2"
STATUS = "Approved"
CHUNK_ID = "SOP-OPS-007_v1_2_chunk_002"
PACKET_ID = "ep1:ea3928728472273819f3c6183683da95690b1bb012d514adfb9b9ce7d4086397"
SOURCE_SHA256 = "ad866150db306fbf8eaaab555acb8c661a203d34b42e62f4e510f3efff270735"
HEADING_EXCLUDED = "Independent check"
FROZEN_BODY = (
    "QA performs an independent line clearance check for product identity, "
    "lot number, printed component code, and room readiness. The run cannot "
    "start until both operations and QA sign the clearance record."
)
BODY_START = 213
BODY_END = 415
PR20_COUNTEREVIDENCE = (
    "The selected quote is an exact substring of the supporting conditional "
    "sentence, so the omission is at Q; N/P retain the full condition."
)
SOURCE = Path("examples/synthetic-controlled-docs/documents/SOP-OPS-007-line-clearance.md")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Split on a period that ends a sentence. Offsets are into ``text``."""
    spans: list[tuple[int, int]] = []
    start = 0
    index = 0
    while index < len(text):
        if text[index] == "." and (index + 1 == len(text) or text[index + 1].isspace()):
            spans.append((start, index + 1))
            start = index + 1
            while start < len(text) and text[start].isspace():
                start += 1
            index = start
            continue
        index += 1
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def smallest_quote_sentence(body: str, quote: str) -> tuple[int, int, str]:
    """Shortest sentence in ``body`` that contains ``quote``. Earliest wins ties."""
    matches = []
    for start, end in sentence_spans(body):
        sentence = body[start:end]
        if quote in sentence:
            matches.append((end - start, start, end, sentence))
    if not matches:
        raise ValueError("historical quote is not in the authorized body")
    matches.sort()
    _, start, end, sentence = matches[0]
    return start, end, sentence


def load_source(root: Path) -> str:
    path = root / SOURCE
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"source hash drift: {digest}")
    text = raw.decode("utf-8")
    if text[BODY_START:BODY_END] != FROZEN_BODY:
        raise ValueError("frozen body offsets drifted")
    if HEADING_EXCLUDED not in text:
        raise ValueError("excluded heading missing from source")
    return text


def evaluate(root: Path) -> dict[str, object]:
    document = load_source(root)
    body = document[BODY_START:BODY_END]
    relative_start, relative_end, sentence = smallest_quote_sentence(body, HISTORICAL_QUOTE)
    absolute_start = BODY_START + relative_start
    absolute_end = BODY_START + relative_end
    if document[absolute_start:absolute_end] != sentence:
        raise ValueError("sentence offsets do not round-trip")
    quote_at = sentence.find(HISTORICAL_QUOTE)
    prefix = sentence[:quote_at]
    suffix = sentence[quote_at + len(HISTORICAL_QUOTE) :]
    heading_in_span = HEADING_EXCLUDED in sentence
    quote_count = body.count(HISTORICAL_QUOTE)
    closes_named_omission = (
        quote_count == 1
        and quote_at >= 0
        and prefix.strip() != ""
        and sentence in body
        and not heading_in_span
        and sentence != HISTORICAL_QUOTE
    )
    disposition = (
        "BOUNDED_CITATION_SPAN_EXPANSION_SUPPORTED"
        if closes_named_omission
        else "CITATION_SPAN_EXPANSION_NOT_SUPPORTED"
    )
    return {
        "experiment_id": "a08-citation-span-20261003",
        "case_id": CASE_ID,
        "claim": CLAIM,
        "model_calls": 0,
        "semantic_oracle": "NONE_NEW",
        "inherited_judgment": {
            "source": "PR #20 wave-a-ep1-authority-readjudication",
            "q": "OVER_BROAD",
            "n": "SUPPORTED",
            "p": "SUPPORTED",
            "terminal": "CITATION_SPAN_INSUFFICIENCY",
            "counterevidence": PR20_COUNTEREVIDENCE,
        },
        "held_fixed": {
            "claim": CLAIM,
            "packet_id": PACKET_ID,
            "doc_id": DOC_ID,
            "version": VERSION,
            "status": STATUS,
            "chunk_id": CHUNK_ID,
            "source_sha256": SOURCE_SHA256,
            "body_sha256": sha256_text(body),
            "body_char_start": BODY_START,
            "body_char_end": BODY_END,
            "retrieval_baseline": "BM25_UNCHANGED",
            "heading_policy": "ADR-018",
        },
        "arm_a": {
            "name": "historical_quote",
            "text": HISTORICAL_QUOTE,
            "char_start": document.find(HISTORICAL_QUOTE),
            "char_end": document.find(HISTORICAL_QUOTE) + len(HISTORICAL_QUOTE),
            "characters": len(HISTORICAL_QUOTE),
        },
        "arm_b": {
            "name": "smallest_authorized_sentence_containing_quote",
            "text": sentence,
            "char_start": absolute_start,
            "char_end": absolute_end,
            "characters": len(sentence),
            "selection_rule": (
                "shortest sentence inside the frozen admitted body that contains "
                "the historical quote; earliest sentence wins a length tie"
            ),
        },
        "observations": {
            "character_increase": len(sentence) - len(HISTORICAL_QUOTE),
            "quote_occurrences_in_body": quote_count,
            "added_prefix": prefix,
            "added_suffix": suffix,
            "heading_imported": heading_in_span,
            "source_identity_changed": False,
            "packet_membership_changed": False,
            "new_source_required": False,
            "arm_b_equals_document_slice": document[absolute_start:absolute_end] == sentence,
            "arm_a_exact_substring_of_arm_b": HISTORICAL_QUOTE in sentence,
            "arm_b_contained_in_frozen_supported_body": sentence in body,
            "added_text": prefix + suffix,
        },
        "falsifiers": {
            "requires_new_packet_evidence": False,
            "imports_heading_semantics": heading_in_span,
            "source_identity_changed": False,
            "expansion_leaves_quote_ambiguous_inside_body": quote_count != 1,
            "cannot_distinguish_citation_from_packet": False,
        },
        "disposition": disposition,
        "disposition_basis": (
            "Arm B is the only sentence in the frozen N/P body that contains the "
            "historical quote. PR #20's counterevidence says that quote omitted "
            "part of this supporting conditional sentence while N/P retained the "
            "full condition. Widening the quote to that sentence closes the named "
            "omission without a new source, heading, or semantic model call."
        ),
        "nonclaims": [
            "Does not establish general semantic entailment.",
            "Does not re-judge the modality paraphrase already accepted at N/P.",
            "Does not support packet expansion, Wave B, CAL, or production generation.",
            "Does not show the selector is safe for every other quote.",
        ],
    }
