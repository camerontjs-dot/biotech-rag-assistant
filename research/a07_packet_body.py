"""Deterministic A07 same-section body-expansion comparison.

No model call. The missing proposition is the frozen qualifier from PR #20.
A candidate span is admitted only when it is inside the authorized section
body of the authorized source.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CLAIM = "The analyst uses two traceable weights for the daily balance check."
CASE_ID = "A07-balance-weight-count"
MISSING_PROPOSITION = "daily balance check"
DOC_ID = "CAL-ENG-005"
VERSION = "1.0"
STATUS = "Effective"
CHUNK_ID = "CAL-ENG-005_v1_0_chunk_001"
PACKET_ID = "ep1:d593fa9971cf114ba0b3b6b091e5228d0d7a758b6d35be206df1854436264865"
SOURCE_SHA256 = "68992780e0d5982f28afa29766ce610e9eb6fcf777c559349b3edc5417ff73d4"
HEADING = "Daily check"
HISTORICAL_BODY = (
    "The analyst verifies the balance with two traceable weights before use. "
    "If either weight falls outside the acceptance range, the analyst stops "
    "use and labels the balance out of service."
)
BODY_START = 55
BODY_END = 240
SOURCE = Path(
    "examples/synthetic-controlled-docs/documents/CAL-ENG-005-balance-calibration.md"
)
HELD_OUT = {
    "role": "held_out_other_document",
    "doc_id": "CAL-0507",
    "version": "2.0",
    "status": "Effective",
    "source_sha256": "d2b05af8e2ee57afe760f24ef1563617a339fd738bd9ef1eb097820b757e3691",
    "source_commit": "600115f9590fb9e7d76cd90fc0171c35afd06905",
    "span": "Daily balance checks are logged on FRM-QC-141.",
    "span_char_start": 458,
    "span_char_end": 504,
    "corpus": "benchmarks/controlled-docs-v2.1",
}
STALE = {
    "role": "stale_status_trap",
    "doc_id": "SOP-EN-044",
    "version": "1.0",
    "status": "Obsolete",
    "source_sha256": "70a6e81aada422d613316f7f2b68782352750fc20eccef52a1f9f6be9ff6cbe3",
    "source_commit": "600115f9590fb9e7d76cd90fc0171c35afd06905",
    "corpus": "benchmarks/controlled-docs-v2.1",
}


def section_body(document: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = document.find(marker)
    if start < 0:
        raise ValueError(f"heading not found: {heading}")
    rest = document[start + len(marker) :]
    next_heading = rest.find("\n## ")
    section = rest if next_heading < 0 else rest[:next_heading]
    return section.strip("\n")


def admits(span: dict[str, str], authorized_body: str) -> bool:
    """Admit a span only from the authorized effective source body."""
    return (
        span.get("doc_id") == DOC_ID
        and span.get("version") == VERSION
        and span.get("status") == STATUS
        and span.get("source_sha256") == SOURCE_SHA256
        and span.get("text", "") in authorized_body
        and HEADING not in span.get("text", "")
    )


def evaluate(root: Path) -> dict[str, object]:
    path = root / SOURCE
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"source hash drift: {digest}")
    document = raw.decode("utf-8")
    if document[BODY_START:BODY_END] != HISTORICAL_BODY:
        raise ValueError("historical body offsets drifted")
    expanded = section_body(document, HEADING)
    next_section = section_body(document, "Calibration failure")
    historical = HISTORICAL_BODY
    added = expanded[len(historical) :] if expanded.startswith(historical) else expanded
    proposition_in_expanded = MISSING_PROPOSITION.casefold() in expanded.casefold()
    proposition_in_heading = MISSING_PROPOSITION.casefold() in HEADING.casefold()
    heading_contains_daily = "daily" in HEADING.casefold()
    candidate_supported = proposition_in_expanded
    authorized_span = {
        "doc_id": DOC_ID,
        "version": VERSION,
        "status": STATUS,
        "source_sha256": SOURCE_SHA256,
        "text": historical,
    }
    held_out_span = {
        "doc_id": HELD_OUT["doc_id"],
        "version": HELD_OUT["version"],
        "status": HELD_OUT["status"],
        "source_sha256": HELD_OUT["source_sha256"],
        "text": HELD_OUT["span"],
    }
    stale_span = {
        "doc_id": STALE["doc_id"],
        "version": STALE["version"],
        "status": STALE["status"],
        "source_sha256": STALE["source_sha256"],
        "text": historical,
    }
    disposition = (
        "SAME_SECTION_BODY_EXPANSION_SUPPORTED"
        if candidate_supported
        and admits(authorized_span, expanded)
        and not admits(held_out_span, expanded)
        else "SAME_SECTION_BODY_EXPANSION_NOT_SUPPORTED"
    )
    return {
        "experiment_id": "a07-body-expansion-20261003",
        "case_id": CASE_ID,
        "claim": CLAIM,
        "model_calls": 0,
        "semantic_oracle": "NONE_NEW",
        "inherited_judgment": {
            "source": "PR #20 wave-a-ep1-authority-readjudication",
            "q": "OVER_BROAD",
            "n": "OVER_BROAD",
            "p": "OVER_BROAD",
            "terminal": "PACKET_LEVEL_GROUNDING_DEFECT",
            "missing_proposition": MISSING_PROPOSITION,
            "qualifier_present_in_authorized_body": False,
            "qualifier_present_in_excluded_heading": True,
        },
        "held_fixed": {
            "claim": CLAIM,
            "packet_id": PACKET_ID,
            "doc_id": DOC_ID,
            "version": VERSION,
            "status": STATUS,
            "chunk_id": CHUNK_ID,
            "source_sha256": SOURCE_SHA256,
            "retrieval_baseline": "BM25_UNCHANGED",
            "heading_policy": "ADR-018",
        },
        "historical_body": {
            "text": historical,
            "char_start": BODY_START,
            "char_end": BODY_END,
            "characters": len(historical),
        },
        "candidate": {
            "rule": "entire same-section body under the authorized heading",
            "text": expanded,
            "characters": len(expanded),
            "characters_added": len(expanded) - len(historical),
            "spans_added": 0 if expanded == historical else 1,
            "proposition_present": proposition_in_expanded,
        },
        "negative_control": {
            "text": historical,
            "note": (
                "The section has no unused body. The second sentence is already "
                "inside the historical aperture and does not state the missing "
                "proposition. The following section was not admitted."
            ),
            "states_missing_proposition": (
                MISSING_PROPOSITION.casefold() in historical.casefold()
            ),
            "next_section_admitted": False,
            "next_section_text": next_section,
        },
        "authority_trap": {
            "held_out_admitted": admits(held_out_span, expanded),
            "stale_admitted": admits(stale_span, expanded),
            "authorized_span_admitted": admits(authorized_span, expanded),
            "held_out": HELD_OUT,
            "stale": STALE,
        },
        "heading": {
            "text": HEADING,
            "contains_daily_token": heading_contains_daily,
            "proposition_equals_heading": proposition_in_heading,
            "used_as_support": False,
            "added_text_excluded_heading": HEADING not in added,
        },
        "falsifiers": {
            "supported_only_by_heading": False,
            "stale_or_held_out_admitted": admits(held_out_span, expanded)
            or admits(stale_span, expanded),
            "negative_control_states_proposition": (
                MISSING_PROPOSITION.casefold() in historical.casefold()
            ),
            "source_identity_unreconstructed": document[BODY_START:BODY_END] != historical,
            "retrieval_or_reranker_changed": False,
        },
        "disposition": disposition,
        "disposition_basis": (
            "The authorized Daily check section body is byte-identical to the "
            "historical aperture. That text does not contain the frozen missing "
            "proposition. No same-section body remains to add. The heading is "
            "excluded. Held-out CAL-0507 and obsolete SOP-EN-044 are not admitted."
        ),
        "nonclaims": [
            "Does not test an explicit heading-semantic grant.",
            "Does not show the daily-check fact is false in the source document.",
            "Does not change retrieval, reranking, CAL, or Wave B.",
            "Does not implement packet expansion.",
        ],
    }
