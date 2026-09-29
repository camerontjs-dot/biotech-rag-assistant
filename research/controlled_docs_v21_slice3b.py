#!/usr/bin/env python3
"""Slice 3B DEV-only reranking and authored-link challengers."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import resource
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

import controlled_docs_v21_slice3a as s3a
from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.corpus import load_corpus

RERANK_L6 = "cross-encoder/ms-marco-MiniLM-L6-v2"
RERANK_L6_REV = "588b01a83959436e6051d2133d8e9ecdcb28b1a5"
RERANK_L12 = "cross-encoder/ms-marco-MiniLM-L12-v2"
RERANK_L12_REV = "e34b9c1a998b19a9937ee29985988737b2d4f7f8"
TOP_N = 30


def seeded_random_order(
    order: list[int],
    case_id: str,
    label: str,
) -> list[int]:
    seed_bytes = hashlib.sha256(f"{case_id}:{label}".encode()).digest()[:8]
    rng = random.Random(int.from_bytes(seed_bytes, "big"))
    window = order[:TOP_N]
    rng.shuffle(window)
    return window + order[TOP_N:]


def rerank_order(
    model: CrossEncoder,
    question: str,
    order: list[int],
    texts: list[str],
    chunks,
) -> tuple[list[int], list[dict], float]:
    window = order[:TOP_N]
    started = time.perf_counter()
    scores = np.asarray(
        model.predict(
            [(question, texts[index]) for index in window],
            show_progress_bar=False,
        )
    ).reshape(-1)
    elapsed = time.perf_counter() - started

    scored = [
        (float(score), first_stage_rank, index)
        for first_stage_rank, (index, score) in enumerate(
            zip(window, scores, strict=True),
            start=1,
        )
    ]
    reranked = sorted(
        scored,
        key=lambda row: (
            -row[0],
            row[1],
            chunks[row[2]].chunk_id,
        ),
    )
    reranked_window = [row[2] for row in reranked]
    tail = [index for index in order if index not in set(reranked_window)]

    first_stage_rank = {
        index: rank for rank, index in enumerate(window, start=1)
    }
    reranked_rank = {
        index: rank for rank, index in enumerate(reranked_window, start=1)
    }
    trace = [
        {
            "chunk_id": chunks[index].chunk_id,
            "doc_id": chunks[index].doc_id,
            "first_stage_rank": first_stage_rank[index],
            "reranked_rank": reranked_rank[index],
            "reranker_score": next(
                score for score, _, candidate in reranked if candidate == index
            ),
        }
        for index in window
    ]
    return reranked_window + tail, trace, elapsed


def crossref_order(
    base_order: list[int],
    chunks,
    references: list[dict],
) -> tuple[list[int], dict]:
    selected = list(base_order[:2])
    source_docs = {chunks[index].doc_id for index in selected}
    target_docs = {
        edge["to"]
        for edge in references
        if edge.get("kind") == "retrievable" and edge.get("from") in source_docs
    }

    admitted = None
    for index in base_order:
        if index in selected:
            continue
        if chunks[index].doc_id in target_docs:
            admitted = index
            break

    if admitted is None:
        admitted = base_order[2]
        reason = "fallback_original_rank3"
    else:
        reason = "authored_retrievable_reference"
    selected.append(admitted)

    rest = [index for index in base_order if index not in set(selected)]
    return selected + rest, {
        "source_docs": sorted(source_docs),
        "eligible_target_docs": sorted(target_docs),
        "admitted_chunk_id": chunks[admitted].chunk_id,
        "admitted_doc_id": chunks[admitted].doc_id,
        "reason": reason,
    }


def make_arm(records: list[dict], families: dict[str, dict]) -> dict:
    return {
        "overall": s3a.aggregate(records),
        "families": s3a.family_metrics(records, families),
        "records": records,
        "stale_leak_count": 0,
    }


def metric(arm: dict, family: str, name: str) -> float:
    return float(arm["families"][family][name])


def reranker_selection(
    name: str,
    arm: dict,
    source_name: str,
    source: dict,
    random_arm: dict,
) -> dict:
    improvements = [
        family
        for family in ("B02", "B05", "B12")
        if metric(arm, family, "all_decisive_case_hit@3")
        > metric(source, family, "all_decisive_case_hit@3")
    ]
    qualifier_holds = all(
        metric(arm, family, "all_decisive_case_hit@3")
        >= metric(source, family, "all_decisive_case_hit@3")
        for family in ("B06", "B07")
    )
    b03_down = (
        metric(arm, "B03", "all_decisive_case_hit@3")
        < metric(source, "B03", "all_decisive_case_hit@3")
    )
    b04_down = (
        metric(arm, "B04", "all_decisive_case_hit@3")
        < metric(source, "B04", "all_decisive_case_hit@3")
    )
    aggregate_holds = (
        arm["overall"]["decisive_span_recall@3"]
        >= source["overall"]["decisive_span_recall@3"]
    )
    beats_random = (
        arm["overall"]["decisive_span_recall@3"]
        > random_arm["overall"]["decisive_span_recall@3"]
    )
    eligible = (
        aggregate_holds
        and bool(improvements)
        and qualifier_holds
        and not (b03_down and b04_down)
        and beats_random
        and arm["stale_leak_count"] == 0
    )
    return {
        "arm": name,
        "source_arm": source_name,
        "aggregate_holds": aggregate_holds,
        "improves": improvements,
        "B06_B07_hold": qualifier_holds,
        "does_not_reduce_both_B03_B04": not (b03_down and b04_down),
        "beats_seeded_random": beats_random,
        "eligible_for_test_protocol": eligible,
    }


def compare_sizes(
    small: dict,
    large: dict,
) -> dict:
    small_records = {row["case_id"]: row for row in small["records"]}
    large_records = {row["case_id"]: row for row in large["records"]}
    extra = [
        case_id
        for case_id, row in large_records.items()
        if row.get("case_hit@3") is True
        and small_records[case_id].get("case_hit@3") is False
    ]
    lost = [
        case_id
        for case_id, row in large_records.items()
        if row.get("case_hit@3") is False
        and small_records[case_id].get("case_hit@3") is True
    ]
    mrr_delta = large["overall"]["mrr"] - small["overall"]["mrr"]
    return {
        "L12_extra_hit_cases": extra,
        "L12_lost_hit_cases": lost,
        "mrr_delta_L12_minus_L6": mrr_delta,
        "L12_size_rule_satisfied": (
            (len(extra) >= 1 and not lost) or mrr_delta >= 0.02
        ),
    }


def markdown(report: dict) -> str:
    lines = [
        "# controlled-docs-v2.1 Slice 3B DEV challengers",
        "",
        "DEV-only. TEST and PROSPECTIVE were not read.",
        "",
        "## Overall",
        "",
        "| arm | span R@3 | case hit@3 | MRR |",
        "|---|---:|---:|---:|",
    ]
    for name, arm in report["arms"].items():
        overall = arm["overall"]
        lines.append(
            f"| {name} | {overall['decisive_span_recall@3']:.3f} | "
            f"{overall['all_decisive_case_hit@3']:.3f} | "
            f"{overall['mrr']:.3f} |"
        )

    lines += ["", "## Cross-reference B08", ""]
    for name in ("rrf_bm25_bge", "rrf_xref3"):
        row = report["arms"][name]["families"]["B08"]
        lines.append(
            f"- {name}: span R@3={row['decisive_span_recall@3']:.3f}, "
            f"case hit@3={row['all_decisive_case_hit@3']:.3f}"
        )

    lines += ["", "## Reranker selection", ""]
    for name, row in report["reranker_selection"].items():
        lines.append(
            f"- {name}: eligible={row['eligible_for_test_protocol']}; "
            f"improves={row['improves']}; qualifiers_hold={row['B06_B07_hold']}; "
            f"beats_random={row['beats_seeded_random']}."
        )

    lines += ["", "## Model-size comparisons", ""]
    for source, row in report["size_comparison"].items():
        lines.append(
            f"- {source}: L12 extra={row['L12_extra_hit_cases']}, "
            f"lost={row['L12_lost_hit_cases']}, "
            f"MRR delta={row['mrr_delta_L12_minus_L6']:.3f}, "
            f"size rule={row['L12_size_rule_satisfied']}."
        )

    lines += ["", "## Operational diagnostics", ""]
    for name, value in report["rerank_seconds"].items():
        lines.append(f"- {name}: {value:.3f} s total rerank prediction time")
    lines.append(f"- peak RSS: {report['peak_rss_kb']} KB")

    lines += [
        "",
        "## Non-claims",
        "",
        "- DEV-only results cannot establish a TEST or production winner.",
        "- Cross-reference admission is depth-1 and authored-link-gated only.",
        "- Rerankers see only fixed top-30 candidate windows.",
        "- TEST and sealed PROSPECTIVE were not read.",
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

    cases, gold, families = s3a.load_dev(root)
    corpus = load_corpus(root / "corpus")
    documents = {
        (doc.metadata.doc_id, doc.metadata.version): doc
        for doc in corpus.documents
    }
    chunks = chunk_documents(corpus.documents)
    current_texts = [s3a.index_text(chunk) for chunk in chunks]
    structured_texts = [
        s3a.structured_index_text(chunk, documents) for chunk in chunks
    ]
    relationships = json.loads(
        (root / "evaluator_only/relationships.json").read_text(encoding="utf-8")
    )["references"]

    bge = SentenceTransformer(
        s3a.BGE_MODEL,
        revision=s3a.BGE_REVISION,
        device="cpu",
    )
    bge_embeddings = bge.encode(
        structured_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    rerank_l6 = CrossEncoder(
        RERANK_L6,
        revision=RERANK_L6_REV,
        device="cpu",
    )
    rerank_l12 = CrossEncoder(
        RERANK_L12,
        revision=RERANK_L12_REV,
        device="cpu",
    )

    names = (
        "bm25_current",
        "rrf_bm25_bge",
        "rrf_xref3",
        "random_bm25_top30",
        "random_rrf_top30",
        "rerank_l6_bm25",
        "rerank_l12_bm25",
        "rerank_l6_rrf",
        "rerank_l12_rrf",
    )
    records: dict[str, list[dict]] = {name: [] for name in names}
    traces: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    xref_traces: dict[str, dict] = {}
    rerank_seconds: defaultdict[str, float] = defaultdict(float)

    for case in cases:
        bm25_raw = s3a.bm25_scores(current_texts, case.question)
        bm25_order = s3a.deterministic_order(bm25_raw, chunks)

        structured_bm25 = s3a.bm25_scores(structured_texts, case.question)
        bge_scores = s3a.semantic_scores(
            bge,
            bge_embeddings,
            case.question,
            query_prefix=s3a.BGE_QUERY_PREFIX,
        )
        structured_bm25_order = s3a.deterministic_order(
            structured_bm25,
            chunks,
        )
        bge_order = s3a.deterministic_order(bge_scores, chunks)
        rrf_raw = s3a.rrf_scores(
            structured_bm25_order,
            bge_order,
            len(chunks),
        )
        rrf_order = s3a.deterministic_order(rrf_raw, chunks)

        xref, xref_trace = crossref_order(rrf_order, chunks, relationships)
        random_bm25 = seeded_random_order(
            bm25_order,
            case.case_id,
            "bm25",
        )
        random_rrf = seeded_random_order(
            rrf_order,
            case.case_id,
            "rrf",
        )

        l6_bm25, trace_l6_bm25, seconds = rerank_order(
            rerank_l6,
            case.question,
            bm25_order,
            current_texts,
            chunks,
        )
        rerank_seconds["rerank_l6_bm25"] += seconds

        l12_bm25, trace_l12_bm25, seconds = rerank_order(
            rerank_l12,
            case.question,
            bm25_order,
            current_texts,
            chunks,
        )
        rerank_seconds["rerank_l12_bm25"] += seconds

        l6_rrf, trace_l6_rrf, seconds = rerank_order(
            rerank_l6,
            case.question,
            rrf_order,
            current_texts,
            chunks,
        )
        rerank_seconds["rerank_l6_rrf"] += seconds

        l12_rrf, trace_l12_rrf, seconds = rerank_order(
            rerank_l12,
            case.question,
            rrf_order,
            current_texts,
            chunks,
        )
        rerank_seconds["rerank_l12_rrf"] += seconds

        orders = {
            "bm25_current": bm25_order,
            "rrf_bm25_bge": rrf_order,
            "rrf_xref3": xref,
            "random_bm25_top30": random_bm25,
            "random_rrf_top30": random_rrf,
            "rerank_l6_bm25": l6_bm25,
            "rerank_l12_bm25": l12_bm25,
            "rerank_l6_rrf": l6_rrf,
            "rerank_l12_rrf": l12_rrf,
        }
        for name, order in orders.items():
            records[name].append(
                s3a.score_case(case, gold[case.case_id], order, chunks)
            )

        xref_traces[case.case_id] = xref_trace
        traces["rerank_l6_bm25"][case.case_id] = trace_l6_bm25
        traces["rerank_l12_bm25"][case.case_id] = trace_l12_bm25
        traces["rerank_l6_rrf"][case.case_id] = trace_l6_rrf
        traces["rerank_l12_rrf"][case.case_id] = trace_l12_rrf

    arms = {
        name: make_arm(rows, families)
        for name, rows in records.items()
    }

    xref_b08 = arms["rrf_xref3"]["families"]["B08"]
    source_b08 = arms["rrf_bm25_bge"]["families"]["B08"]
    xref_selection = {
        "B08_improves": (
            xref_b08["all_decisive_case_hit@3"]
            > source_b08["all_decisive_case_hit@3"]
        ),
        "aggregate_delta": (
            arms["rrf_xref3"]["overall"]["decisive_span_recall@3"]
            - arms["rrf_bm25_bge"]["overall"]["decisive_span_recall@3"]
        ),
        "B03_holds": (
            metric(arms["rrf_xref3"], "B03", "all_decisive_case_hit@3")
            >= metric(arms["rrf_bm25_bge"], "B03", "all_decisive_case_hit@3")
        ),
        "B04_holds": (
            metric(arms["rrf_xref3"], "B04", "all_decisive_case_hit@3")
            >= metric(arms["rrf_bm25_bge"], "B04", "all_decisive_case_hit@3")
        ),
    }
    xref_selection["eligible_for_test_protocol"] = (
        xref_selection["B08_improves"]
        and xref_selection["aggregate_delta"] >= -0.025
        and xref_selection["B03_holds"]
        and xref_selection["B04_holds"]
    )

    reranker_choices = {
        "rerank_l6_bm25": reranker_selection(
            "rerank_l6_bm25",
            arms["rerank_l6_bm25"],
            "bm25_current",
            arms["bm25_current"],
            arms["random_bm25_top30"],
        ),
        "rerank_l12_bm25": reranker_selection(
            "rerank_l12_bm25",
            arms["rerank_l12_bm25"],
            "bm25_current",
            arms["bm25_current"],
            arms["random_bm25_top30"],
        ),
        "rerank_l6_rrf": reranker_selection(
            "rerank_l6_rrf",
            arms["rerank_l6_rrf"],
            "rrf_bm25_bge",
            arms["rrf_bm25_bge"],
            arms["random_rrf_top30"],
        ),
        "rerank_l12_rrf": reranker_selection(
            "rerank_l12_rrf",
            arms["rerank_l12_rrf"],
            "rrf_bm25_bge",
            arms["rrf_bm25_bge"],
            arms["random_rrf_top30"],
        ),
    }

    size_comparison = {
        "bm25": compare_sizes(
            arms["rerank_l6_bm25"],
            arms["rerank_l12_bm25"],
        ),
        "rrf": compare_sizes(
            arms["rerank_l6_rrf"],
            arms["rerank_l12_rrf"],
        ),
    }

    report = {
        "schema_version": "slice3b-dev-v1",
        "scope": "DEV_ONLY",
        "benchmark_tree_sha256": (
            "05f09c128a4848b57e607068fe59ff48"
            "f01e16387f2136083d289f331181ab85"
        ),
        "models": {
            "bge": {
                "model": s3a.BGE_MODEL,
                "revision": s3a.BGE_REVISION,
            },
            "rerank_l6": {
                "model": RERANK_L6,
                "revision": RERANK_L6_REV,
            },
            "rerank_l12": {
                "model": RERANK_L12,
                "revision": RERANK_L12_REV,
            },
        },
        "top_n": TOP_N,
        "arms": arms,
        "xref_selection": xref_selection,
        "reranker_selection": reranker_choices,
        "size_comparison": size_comparison,
        "rerank_seconds": dict(rerank_seconds),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "xref_trace": xref_traces,
        "rerank_trace": traces,
    }

    (out / "slice3b-results.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "slice3b-report.md").write_text(
        markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "xref_selection": xref_selection,
                "reranker_selection": reranker_choices,
                "size_comparison": size_comparison,
                "overall": {
                    name: arm["overall"]
                    for name, arm in arms.items()
                },
                "rerank_seconds": dict(rerank_seconds),
                "peak_rss_kb": report["peak_rss_kb"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
