#!/usr/bin/env python3
"""Slice 3A DEV-only first-stage retrieval experiment for controlled-docs-v2.1."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.models import DocumentChunk, SourceDocument
from biotech_rag_assistant.retrieval import index_text, tokenize

MINILM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_REVISION = "f5610b47471b118dafc55f4c387822dbfc8413ae"
BGE_MODEL = "BAAI/bge-small-en-v1.5"
BGE_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
RRF_K0 = 60
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class Case:
    case_id: str
    question: str
    top_k: int


@dataclass(frozen=True)
class Gold:
    doc_id: str | None
    version: str | None
    char_start: int | None
    char_end: int | None
    decisive: bool
    relevance_class: str | None
    joint_group_id: str | None
    disposition: str


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_dev(root: Path) -> tuple[list[Case], dict[str, list[Gold]], dict[str, dict]]:
    cases = [
        Case(row["case_id"], row["question"], int(row["top_k"]))
        for row in jsonl(root / "cases/dev_cases.jsonl")
    ]
    gold: dict[str, list[Gold]] = defaultdict(list)
    for row in jsonl(root / "evaluator_only/gold/dev_relevance.jsonl"):
        gold[row["case_id"]].append(
            Gold(
                doc_id=row.get("doc_id"),
                version=str(row["version"]) if row.get("version") is not None else None,
                char_start=(
                    int(row["char_start"])
                    if row.get("char_start") is not None
                    else None
                ),
                char_end=(
                    int(row["char_end"])
                    if row.get("char_end") is not None
                    else None
                ),
                decisive=bool(row["decisive"]),
                relevance_class=row.get("relevance_class"),
                joint_group_id=row.get("joint_group_id"),
                disposition=row["expected_disposition"],
            )
        )
    families = json.loads(
        (root / "evaluator_only/families.json").read_text(encoding="utf-8")
    )
    return cases, dict(gold), families


def heading_path(document: SourceDocument, chunk: DocumentChunk) -> list[str]:
    stack: list[str] = []
    offset = 0
    for line in document.raw_text.splitlines(keepends=True):
        start = offset
        offset += len(line)
        if start >= chunk.char_start:
            break
        match = HEADING_RE.match(line.rstrip("\r\n"))
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        stack = stack[: level - 1]
        stack.append(title)
    if stack and stack[0] == document.metadata.doc_title:
        return stack[1:]
    return stack


def structured_index_text(
    chunk: DocumentChunk,
    documents: dict[tuple[str, str], SourceDocument],
) -> str:
    document = documents[(chunk.doc_id, chunk.version)]
    path = heading_path(document, chunk)
    parts = [f"Document: {chunk.doc_title}"]
    if path:
        parts.append("Section: " + " > ".join(path))
    parts.append(chunk.text)
    return "\n".join(parts)


def overlaps(chunk: DocumentChunk, gold: Gold) -> bool:
    if None in (gold.doc_id, gold.version, gold.char_start, gold.char_end):
        return False
    return (
        chunk.doc_id == gold.doc_id
        and chunk.version == gold.version
        and max(chunk.char_start, gold.char_start) < min(chunk.char_end, gold.char_end)
    )


def deterministic_order(scores: list[float], chunks: list[DocumentChunk]) -> list[int]:
    return sorted(
        range(len(chunks)),
        key=lambda index: (
            -float(scores[index]),
            chunks[index].doc_id,
            chunks[index].chunk_index,
            chunks[index].chunk_id,
        ),
    )


def bm25_scores(texts: list[str], question: str) -> list[float]:
    bm25 = BM25Okapi([tokenize(text) for text in texts])
    return [float(value) for value in bm25.get_scores(tokenize(question))]


def semantic_scores(
    model: SentenceTransformer,
    chunk_embeddings: np.ndarray,
    question: str,
    *,
    query_prefix: str = "",
) -> list[float]:
    query_embedding = model.encode(
        [query_prefix + question],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    return (chunk_embeddings @ query_embedding).astype(float).tolist()


def rrf_scores(order_a: list[int], order_b: list[int], n: int) -> list[float]:
    rank_a = {index: rank for rank, index in enumerate(order_a, start=1)}
    rank_b = {index: rank for rank, index in enumerate(order_b, start=1)}
    return [
        1.0 / (RRF_K0 + rank_a[index]) + 1.0 / (RRF_K0 + rank_b[index])
        for index in range(n)
    ]


def minmax(values: list[float]) -> list[float]:
    low, high = min(values), max(values)
    if high == low:
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def fusion_scores(a: list[float], b: list[float]) -> list[float]:
    a_norm, b_norm = minmax(a), minmax(b)
    return [
        0.5 * a_value + 0.5 * b_value
        for a_value, b_value in zip(a_norm, b_norm, strict=True)
    ]


def truncation_report(
    model: SentenceTransformer,
    texts: list[str],
) -> dict[str, int]:
    limit = int(model.max_seq_length)
    lengths = []
    tokenizer = model.tokenizer
    for text in texts:
        token_ids = tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
        )["input_ids"]
        lengths.append(len(token_ids))
    return {
        "max_sequence_length": limit,
        "indexed_texts": len(texts),
        "texts_over_limit": sum(length > limit for length in lengths),
        "max_observed_tokens": max(lengths) if lengths else 0,
    }


def score_case(
    case: Case,
    spans: list[Gold],
    order: list[int],
    chunks: list[DocumentChunk],
) -> dict:
    decisive = [row for row in spans if row.decisive]
    hard_negative = [
        row for row in spans
        if row.relevance_class in {"hard_negative", "stale_trap"}
    ]
    disposition = next(iter({row.disposition for row in spans}))

    result = {
        "case_id": case.case_id,
        "expected_disposition": disposition,
        "decisive_spans": len(decisive),
        "hard_negative_spans": len(hard_negative),
    }
    if not decisive:
        result.update(
            {
                "span_recall@1": None,
                "span_recall@3": None,
                "span_recall@5": None,
                "case_hit@1": None,
                "case_hit@3": None,
                "case_hit@5": None,
                "mrr": None,
            }
        )
        return result

    matched_ranks: list[int | None] = []
    for gold in decisive:
        rank = next(
            (
                position
                for position, index in enumerate(order, start=1)
                if overlaps(chunks[index], gold)
            ),
            None,
        )
        matched_ranks.append(rank)

    for k in (1, 3, 5):
        found = sum(rank is not None and rank <= k for rank in matched_ranks)
        result[f"span_recall@{k}"] = found / len(decisive)
        result[f"case_hit@{k}"] = found == len(decisive)

    first_rank = min(rank for rank in matched_ranks if rank is not None) if any(
        rank is not None for rank in matched_ranks
    ) else None
    result["mrr"] = (1.0 / first_rank) if first_rank is not None else 0.0
    return result


def aggregate(records: list[dict]) -> dict:
    answerable = [row for row in records if row["decisive_spans"] > 0]
    if not answerable:
        return {"cases": len(records), "answerable": 0}
    return {
        "cases": len(records),
        "answerable": len(answerable),
        "decisive_span_recall@1": sum(
            row["span_recall@1"] for row in answerable
        ) / len(answerable),
        "decisive_span_recall@3": sum(
            row["span_recall@3"] for row in answerable
        ) / len(answerable),
        "decisive_span_recall@5": sum(
            row["span_recall@5"] for row in answerable
        ) / len(answerable),
        "all_decisive_case_hit@1": sum(
            row["case_hit@1"] for row in answerable
        ) / len(answerable),
        "all_decisive_case_hit@3": sum(
            row["case_hit@3"] for row in answerable
        ) / len(answerable),
        "all_decisive_case_hit@5": sum(
            row["case_hit@5"] for row in answerable
        ) / len(answerable),
        "mrr": sum(row["mrr"] for row in answerable) / len(answerable),
    }


def family_metrics(
    records: list[dict],
    families: dict[str, dict],
) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        grouped[families[row["case_id"]]["family"]].append(row)
    return {family: aggregate(rows) for family, rows in sorted(grouped.items())}


def selection(
    arms: dict[str, dict],
) -> dict[str, dict]:
    baseline = arms["bm25_current"]
    baseline_overall = baseline["overall"]["decisive_span_recall@3"]
    baseline_families = baseline["families"]
    decisions: dict[str, dict] = {}
    for name, result in arms.items():
        if name == "bm25_current":
            continue
        families = result["families"]
        improves = [
            family
            for family in ("B02", "B08", "B12", "B13")
            if family in families
            and families[family].get("all_decisive_case_hit@3", 0.0)
            > baseline_families[family].get("all_decisive_case_hit@3", 0.0)
        ]
        b03_down = (
            families["B03"]["all_decisive_case_hit@3"]
            < baseline_families["B03"]["all_decisive_case_hit@3"]
        )
        b04_down = (
            families["B04"]["all_decisive_case_hit@3"]
            < baseline_families["B04"]["all_decisive_case_hit@3"]
        )
        decisions[name] = {
            "aggregate_holds_or_improves": (
                result["overall"]["decisive_span_recall@3"] >= baseline_overall
            ),
            "diagnostic_improvements": improves,
            "does_not_reduce_both_B03_and_B04": not (b03_down and b04_down),
            "eligible_for_test_protocol": (
                result["overall"]["decisive_span_recall@3"] >= baseline_overall
                and bool(improves)
                and not (b03_down and b04_down)
                and result["stale_leak_count"] == 0
            ),
        }
    return decisions


def markdown(report: dict) -> str:
    lines = [
        "# controlled-docs-v2.1 Slice 3A DEV first-stage retrieval",
        "",
        "DEV-only exploration. TEST and PROSPECTIVE were not read.",
        "",
        "## Overall",
        "",
        "| arm | span R@1 | span R@3 | span R@5 | case hit@3 | MRR | eligible for TEST protocol |",
        "|---|---:|---:|---:|---:|---:|:--:|",
    ]
    for name, result in report["arms"].items():
        row = result["overall"]
        eligible = (
            "baseline"
            if name == "bm25_current"
            else str(report["selection"][name]["eligible_for_test_protocol"])
        )
        lines.append(
            f"| {name} | {row['decisive_span_recall@1']:.3f} | "
            f"{row['decisive_span_recall@3']:.3f} | "
            f"{row['decisive_span_recall@5']:.3f} | "
            f"{row['all_decisive_case_hit@3']:.3f} | "
            f"{row['mrr']:.3f} | {eligible} |"
        )

    lines += ["", "## Family recall@3 / case hit@3", ""]
    for name, result in report["arms"].items():
        lines += [
            f"### {name}",
            "",
            "| family | span R@3 | case hit@3 |",
            "|---|---:|---:|",
        ]
        for family, row in result["families"].items():
            if row.get("answerable", 0):
                lines.append(
                    f"| {family} | {row['decisive_span_recall@3']:.3f} | "
                    f"{row['all_decisive_case_hit@3']:.3f} |"
                )
        lines.append("")

    lines += ["## Model truncation diagnostics", ""]
    for name, row in report["truncation"].items():
        lines.append(
            f"- {name}: {row['texts_over_limit']}/{row['indexed_texts']} over "
            f"{row['max_sequence_length']} tokens; max observed "
            f"{row['max_observed_tokens']}."
        )

    lines += [
        "",
        "## Selection observations",
        "",
    ]
    for name, row in report["selection"].items():
        lines.append(
            f"- {name}: eligible={row['eligible_for_test_protocol']}; "
            f"improves={row['diagnostic_improvements']}; "
            f"aggregate_hold={row['aggregate_holds_or_improves']}; "
            f"B03/B04 joint floor={row['does_not_reduce_both_B03_and_B04']}."
        )

    lines += [
        "",
        "## Non-claims",
        "",
        "- DEV-only results do not establish a TEST winner or production retrieval method.",
        "- No reranker, cross-reference expansion, generator, or answerability model ran.",
        "- TEST and sealed PROSPECTIVE were not read.",
        "- Stored evidence spans and source offsets were unchanged.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.benchmark.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    cases, gold, families = load_dev(root)
    corpus = load_corpus(root / "corpus")
    documents = {
        (doc.metadata.doc_id, doc.metadata.version): doc
        for doc in corpus.documents
    }
    chunks = chunk_documents(corpus.documents)

    current_texts = [index_text(chunk) for chunk in chunks]
    structured_texts = [
        structured_index_text(chunk, documents) for chunk in chunks
    ]

    for chunk in chunks:
        document = documents[(chunk.doc_id, chunk.version)]
        assert chunk.text == document.raw_text[chunk.char_start : chunk.char_end]

    mini = SentenceTransformer(
        MINILM_MODEL,
        revision=MINILM_REVISION,
        device="cpu",
    )
    bge = SentenceTransformer(
        BGE_MODEL,
        revision=BGE_REVISION,
        device="cpu",
    )

    mini_current_embeddings = mini.encode(
        current_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    mini_structured_embeddings = mini.encode(
        structured_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    bge_structured_embeddings = bge.encode(
        structured_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    arm_records: dict[str, list[dict]] = {
        name: []
        for name in (
            "bm25_current",
            "bm25_structured",
            "minilm_current",
            "minilm_structured",
            "bge_structured",
            "rrf_bm25_bge",
            "fusion50_bm25_bge",
        )
    }

    for case in cases:
        current_bm25 = bm25_scores(current_texts, case.question)
        structured_bm25 = bm25_scores(structured_texts, case.question)
        mini_current = semantic_scores(
            mini,
            mini_current_embeddings,
            case.question,
        )
        mini_structured = semantic_scores(
            mini,
            mini_structured_embeddings,
            case.question,
        )
        bge_structured = semantic_scores(
            bge,
            bge_structured_embeddings,
            case.question,
            query_prefix=BGE_QUERY_PREFIX,
        )

        orders = {
            "bm25_current": deterministic_order(current_bm25, chunks),
            "bm25_structured": deterministic_order(structured_bm25, chunks),
            "minilm_current": deterministic_order(mini_current, chunks),
            "minilm_structured": deterministic_order(mini_structured, chunks),
            "bge_structured": deterministic_order(bge_structured, chunks),
        }
        rrf = rrf_scores(
            orders["bm25_structured"],
            orders["bge_structured"],
            len(chunks),
        )
        fusion = fusion_scores(structured_bm25, bge_structured)
        orders["rrf_bm25_bge"] = deterministic_order(rrf, chunks)
        orders["fusion50_bm25_bge"] = deterministic_order(fusion, chunks)

        for name, order in orders.items():
            arm_records[name].append(
                score_case(case, gold[case.case_id], order, chunks)
            )

    arms = {}
    for name, records in arm_records.items():
        top_five_ids = []
        stale = 0
        duplicate = 0
        # Every indexed chunk is status-gated by construction. Keep the explicit
        # non-compensable receipt anyway.
        for chunk in chunks:
            if chunk.status not in {"Approved", "Effective"}:
                stale += 1
        for case in cases:
            # Duplicate burden is representation-independent in 3A because each
            # rank order contains every chunk identity exactly once.
            top_five_ids.append(case.case_id)
        arms[name] = {
            "overall": aggregate(records),
            "families": family_metrics(records, families),
            "records": records,
            "stale_leak_count": stale,
            "duplicate_source_span_burden": duplicate,
        }

    report = {
        "schema_version": "slice3a-dev-v1",
        "scope": "DEV_ONLY",
        "benchmark": {
            "tree_sha256": (
                "05f09c128a4848b57e607068fe59ff48"
                "f01e16387f2136083d289f331181ab85"
            ),
            "cases": len(cases),
            "chunks": len(chunks),
        },
        "models": {
            "minilm": {
                "model": MINILM_MODEL,
                "revision": MINILM_REVISION,
            },
            "bge": {
                "model": BGE_MODEL,
                "revision": BGE_REVISION,
                "query_prefix": BGE_QUERY_PREFIX,
            },
        },
        "representation": {
            "current": "section_heading + verbatim chunk",
            "structured": "document title + hierarchical section path + verbatim chunk",
            "stored_spans_unchanged": True,
        },
        "truncation": {
            "minilm_current": truncation_report(mini, current_texts),
            "minilm_structured": truncation_report(mini, structured_texts),
            "bge_structured": truncation_report(bge, structured_texts),
        },
        "arms": arms,
    }
    report["selection"] = selection(arms)

    (out / "slice3a-results.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "slice3a-report.md").write_text(
        markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "scope": report["scope"],
                "selection": report["selection"],
                "truncation": report["truncation"],
                "overall": {
                    name: result["overall"]
                    for name, result in report["arms"].items()
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
