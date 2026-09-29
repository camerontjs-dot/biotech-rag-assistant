#!/usr/bin/env python3
"""Slice 3C preregistered TEST retrieval comparison for controlled-docs-v2.1."""
from __future__ import annotations

import argparse
import json
import math
import resource
from collections import defaultdict
from pathlib import Path

import controlled_docs_v21_slice3a as s3a
import controlled_docs_v21_slice3b as s3b
import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import index_text

BOOTSTRAP_SEED = 20260929
BOOTSTRAP_REPS = 10_000
MIN_EFFECT = 0.050
BEST_TIE_WINDOW = 0.025
FAMILY_FLOORS = {
    "B01": 1.00,
    "B03": 0.80,
    "B04": 0.90,
}
COMPLEXITY_ORDER = {
    "minilm_current": 1,
    "rrf_bm25_bge": 2,
    "rerank_l6_bm25": 3,
}
CHALLENGERS = tuple(COMPLEXITY_ORDER)
BENCHMARK_TREE = (
    "05f09c128a4848b57e607068fe59ff48"
    "f01e16387f2136083d289f331181ab85"
)


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_test(
    root: Path,
) -> tuple[list[s3a.Case], dict[str, list[s3a.Gold]], dict[str, dict]]:
    cases = [
        s3a.Case(row["case_id"], row["question"], int(row["top_k"]))
        for row in jsonl(root / "cases/test_cases.jsonl")
    ]
    gold: dict[str, list[s3a.Gold]] = defaultdict(list)
    for row in jsonl(root / "evaluator_only/gold/test_relevance.jsonl"):
        gold[row["case_id"]].append(
            s3a.Gold(
                doc_id=row.get("doc_id"),
                version=(
                    str(row["version"])
                    if row.get("version") is not None
                    else None
                ),
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


def make_arm(
    records: list[dict],
    families: dict[str, dict],
    stale_leak_count: int,
) -> dict:
    return {
        "overall": s3a.aggregate(records),
        "families": s3a.family_metrics(records, families),
        "records": records,
        "stale_leak_count": stale_leak_count,
    }


def aligned_answerable(
    a: list[dict],
    b: list[dict],
) -> tuple[list[dict], list[dict]]:
    by_a = {
        row["case_id"]: row
        for row in a
        if row["decisive_spans"] > 0
    }
    by_b = {
        row["case_id"]: row
        for row in b
        if row["decisive_spans"] > 0
    }
    if set(by_a) != set(by_b):
        raise ValueError("paired record case sets differ")
    ids = sorted(by_a)
    return [by_a[case_id] for case_id in ids], [by_b[case_id] for case_id in ids]


def bootstrap_delta(
    candidate: list[dict],
    baseline: list[dict],
    *,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    cand, base = aligned_answerable(candidate, baseline)
    diffs = np.asarray(
        [
            float(c["span_recall@3"]) - float(b["span_recall@3"])
            for c, b in zip(cand, base, strict=True)
        ],
        dtype=float,
    )
    rng = np.random.default_rng(seed)
    indices = rng.integers(
        0,
        len(diffs),
        size=(BOOTSTRAP_REPS, len(diffs)),
    )
    boot = diffs[indices].mean(axis=1)
    return {
        "n_cases": len(diffs),
        "seed": seed,
        "repetitions": BOOTSTRAP_REPS,
        "mean_delta": float(diffs.mean()),
        "ci95_low": float(np.quantile(boot, 0.025)),
        "ci95_high": float(np.quantile(boot, 0.975)),
    }


def exact_mcnemar(
    candidate: list[dict],
    baseline: list[dict],
) -> dict:
    cand, base = aligned_answerable(candidate, baseline)
    b = sum(
        (not bool(base_row["case_hit@3"]))
        and bool(cand_row["case_hit@3"])
        for cand_row, base_row in zip(cand, base, strict=True)
    )
    c = sum(
        bool(base_row["case_hit@3"])
        and (not bool(cand_row["case_hit@3"]))
        for cand_row, base_row in zip(cand, base, strict=True)
    )
    n = b + c
    if n == 0:
        p_value = 1.0
    else:
        k = min(b, c)
        tail = sum(math.comb(n, index) for index in range(k + 1))
        p_value = min(1.0, 2.0 * tail / (2**n))
    return {
        "bm25_miss_challenger_hit": b,
        "bm25_hit_challenger_miss": c,
        "discordant_pairs": n,
        "two_sided_exact_p": p_value,
    }


def family_hit(arm: dict, family: str) -> float:
    return float(arm["families"][family]["all_decisive_case_hit@3"])


def candidate_decision(
    name: str,
    arm: dict,
    baseline: dict,
) -> dict:
    paired = bootstrap_delta(arm["records"], baseline["records"])
    mcnemar = exact_mcnemar(arm["records"], baseline["records"])

    primary_delta = (
        float(arm["overall"]["decisive_span_recall@3"])
        - float(baseline["overall"]["decisive_span_recall@3"])
    )
    case_hit_delta = (
        float(arm["overall"]["all_decisive_case_hit@3"])
        - float(baseline["overall"]["all_decisive_case_hit@3"])
    )

    floors = {
        family: family_hit(arm, family) >= floor
        for family, floor in FAMILY_FLOORS.items()
    }
    reliability_guards = {
        family: family_hit(arm, family) >= family_hit(baseline, family)
        for family in ("B06", "B07", "B08")
    }

    checks = {
        "minimum_effect": primary_delta >= MIN_EFFECT,
        "bootstrap_lower_bound_positive": paired["ci95_low"] > 0.0,
        "case_hit_holds": case_hit_delta >= 0.0,
        "family_floors": all(floors.values()),
        "reliability_guards": all(reliability_guards.values()),
        "zero_stale_leaks": arm["stale_leak_count"] == 0,
    }
    return {
        "arm": name,
        "primary_delta": primary_delta,
        "case_hit_delta": case_hit_delta,
        "bootstrap": paired,
        "mcnemar": mcnemar,
        "family_floor_checks": floors,
        "reliability_guard_checks": reliability_guards,
        "checks": checks,
        "eligible_for_prospective": all(checks.values()),
    }


def choose_provisional(
    arms: dict[str, dict],
    decisions: dict[str, dict],
) -> dict:
    eligible = [
        name
        for name in CHALLENGERS
        if decisions[name]["eligible_for_prospective"]
    ]
    if not eligible:
        return {
            "provisional_candidate": None,
            "reason": "no_challenger_met_preregistered_test_gate",
            "eligible": [],
            "pairwise_best_comparisons": {},
        }

    best = max(
        eligible,
        key=lambda name: arms[name]["overall"]["decisive_span_recall@3"],
    )
    best_score = float(arms[best]["overall"]["decisive_span_recall@3"])
    inconclusive_with_best = [best]
    comparisons: dict[str, dict] = {}

    for other in eligible:
        if other == best:
            continue
        other_score = float(
            arms[other]["overall"]["decisive_span_recall@3"]
        )
        gap = best_score - other_score
        row = {
            "best": best,
            "other": other,
            "point_gap": gap,
            "inside_0_025_window": gap <= BEST_TIE_WINDOW,
        }
        if gap <= BEST_TIE_WINDOW:
            stats = bootstrap_delta(
                arms[best]["records"],
                arms[other]["records"],
                seed=BOOTSTRAP_SEED + COMPLEXITY_ORDER[other],
            )
            row["paired_bootstrap_best_minus_other"] = stats
            includes_zero = (
                stats["ci95_low"] <= 0.0 <= stats["ci95_high"]
            )
            row["interval_includes_zero"] = includes_zero
            if includes_zero:
                inconclusive_with_best.append(other)
        comparisons[other] = row

    chosen = min(
        inconclusive_with_best,
        key=lambda name: COMPLEXITY_ORDER[name],
    )
    reason = (
        "simpler_arm_selected_within_inconclusive_best_window"
        if chosen != best
        else "highest_primary_metric_not_tied_with_simpler_eligible_arm"
    )
    return {
        "provisional_candidate": chosen,
        "best_point_estimate": best,
        "reason": reason,
        "eligible": eligible,
        "inconclusive_with_best": inconclusive_with_best,
        "pairwise_best_comparisons": comparisons,
    }


def markdown(report: dict) -> str:
    lines = [
        "# controlled-docs-v2.1 Slice 3C TEST retrieval comparison",
        "",
        "TEST-only preregistered comparison. PROSPECTIVE remained sealed.",
        "",
        "## Overall",
        "",
        "| arm | span R@1 | span R@3 | span R@5 | case hit@3 | MRR |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, arm in report["arms"].items():
        row = arm["overall"]
        lines.append(
            f"| {name} | {row['decisive_span_recall@1']:.3f} | "
            f"{row['decisive_span_recall@3']:.3f} | "
            f"{row['decisive_span_recall@5']:.3f} | "
            f"{row['all_decisive_case_hit@3']:.3f} | "
            f"{row['mrr']:.3f} |"
        )

    lines += [
        "",
        "## Preregistered challenger decisions",
        "",
    ]
    for name, decision in report["decisions"].items():
        boot = decision["bootstrap"]
        lines.append(
            f"- {name}: eligible={decision['eligible_for_prospective']}; "
            f"delta={decision['primary_delta']:.3f}; "
            f"95% CI [{boot['ci95_low']:.3f}, "
            f"{boot['ci95_high']:.3f}]; "
            f"checks={decision['checks']}."
        )

    lines += [
        "",
        "## Provisional selection",
        "",
        f"- candidate: {report['selection']['provisional_candidate']}",
        f"- reason: {report['selection']['reason']}",
        f"- eligible: {report['selection']['eligible']}",
        "",
        "## Family case hit@3",
        "",
        "| arm | B01 | B02 | B03 | B04 | B06 | B07 | B08 | B13 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, arm in report["arms"].items():
        values = [
            family_hit(arm, family)
            for family in (
                "B01",
                "B02",
                "B03",
                "B04",
                "B06",
                "B07",
                "B08",
                "B13",
            )
        ]
        lines.append(
            f"| {name} | " + " | ".join(f"{value:.3f}" for value in values)
            + " |"
        )

    lines += [
        "",
        "## Operational diagnostics",
        "",
        f"- reranker wall time: {report['rerank_seconds']:.3f} s",
        f"- peak RSS: {report['peak_rss_kb']} KB",
        "",
        "## Non-claims",
        "",
        "- TEST does not promote product retrieval behavior.",
        "- PROSPECTIVE was not read.",
        "- No TEST threshold or arm was retuned after measurement.",
        "- The provisional candidate requires a separately preregistered "
        "sealed PROSPECTIVE replication.",
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

    cases, gold, families = load_test(root)
    corpus = load_corpus(root / "corpus")
    documents = {
        (doc.metadata.doc_id, doc.metadata.version): doc
        for doc in corpus.documents
    }
    chunks = chunk_documents(corpus.documents)

    for chunk in chunks:
        document = documents[(chunk.doc_id, chunk.version)]
        assert chunk.text == document.raw_text[
            chunk.char_start : chunk.char_end
        ]

    stale_leak_count = sum(
        chunk.status not in {"Approved", "Effective"}
        for chunk in chunks
    )
    if stale_leak_count:
        raise RuntimeError("status-gated chunk list contains stale content")

    current_texts = [index_text(chunk) for chunk in chunks]
    structured_texts = [
        s3a.structured_index_text(chunk, documents)
        for chunk in chunks
    ]

    mini = SentenceTransformer(
        s3a.MINILM_MODEL,
        revision=s3a.MINILM_REVISION,
        device="cpu",
    )
    bge = SentenceTransformer(
        s3a.BGE_MODEL,
        revision=s3a.BGE_REVISION,
        device="cpu",
    )
    reranker = CrossEncoder(
        s3b.RERANK_L6,
        revision=s3b.RERANK_L6_REV,
        device="cpu",
    )

    mini_embeddings = mini.encode(
        current_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    bge_embeddings = bge.encode(
        structured_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    records: dict[str, list[dict]] = {
        name: []
        for name in (
            "bm25_current",
            "minilm_current",
            "rrf_bm25_bge",
            "rerank_l6_bm25",
        )
    }
    rerank_trace: dict[str, list[dict]] = {}
    rerank_seconds = 0.0

    for case in cases:
        bm25 = s3a.bm25_scores(current_texts, case.question)
        bm25_order = s3a.deterministic_order(bm25, chunks)

        mini_scores = s3a.semantic_scores(
            mini,
            mini_embeddings,
            case.question,
        )
        mini_order = s3a.deterministic_order(mini_scores, chunks)

        structured_bm25 = s3a.bm25_scores(
            structured_texts,
            case.question,
        )
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

        reranked, trace, seconds = s3b.rerank_order(
            reranker,
            case.question,
            bm25_order,
            current_texts,
            chunks,
        )
        rerank_seconds += seconds
        rerank_trace[case.case_id] = trace

        orders = {
            "bm25_current": bm25_order,
            "minilm_current": mini_order,
            "rrf_bm25_bge": rrf_order,
            "rerank_l6_bm25": reranked,
        }
        for name, order in orders.items():
            records[name].append(
                s3a.score_case(
                    case,
                    gold[case.case_id],
                    order,
                    chunks,
                )
            )

    arms = {
        name: make_arm(rows, families, stale_leak_count)
        for name, rows in records.items()
    }
    baseline = arms["bm25_current"]
    decisions = {
        name: candidate_decision(name, arms[name], baseline)
        for name in CHALLENGERS
    }
    selection = choose_provisional(arms, decisions)

    report = {
        "schema_version": "slice3c-test-v1",
        "scope": "TEST_ONLY",
        "benchmark": {
            "tree_sha256": BENCHMARK_TREE,
            "cases": len(cases),
            "chunks": len(chunks),
        },
        "models": {
            "minilm": {
                "model": s3a.MINILM_MODEL,
                "revision": s3a.MINILM_REVISION,
            },
            "bge": {
                "model": s3a.BGE_MODEL,
                "revision": s3a.BGE_REVISION,
                "query_prefix": s3a.BGE_QUERY_PREFIX,
            },
            "rerank_l6": {
                "model": s3b.RERANK_L6,
                "revision": s3b.RERANK_L6_REV,
                "top_n": s3b.TOP_N,
            },
        },
        "decision_rule": {
            "primary_metric": "mean per-case decisive-span recall@3",
            "minimum_effect": MIN_EFFECT,
            "bootstrap_repetitions": BOOTSTRAP_REPS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "family_floors": FAMILY_FLOORS,
            "reliability_guards": [
                "B06 >= BM25",
                "B07 >= BM25",
                "B08 >= BM25",
            ],
            "best_tie_window": BEST_TIE_WINDOW,
            "simplicity_order": COMPLEXITY_ORDER,
        },
        "truncation": {
            "minilm_current": s3a.truncation_report(
                mini,
                current_texts,
            ),
            "bge_structured": s3a.truncation_report(
                bge,
                structured_texts,
            ),
        },
        "arms": arms,
        "decisions": decisions,
        "selection": selection,
        "rerank_seconds": rerank_seconds,
        "peak_rss_kb": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
        "rerank_trace": rerank_trace,
    }

    (out / "slice3c-results.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "slice3c-report.md").write_text(
        markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "scope": report["scope"],
                "overall": {
                    name: arm["overall"]
                    for name, arm in arms.items()
                },
                "decisions": decisions,
                "selection": selection,
                "truncation": report["truncation"],
                "rerank_seconds": rerank_seconds,
                "peak_rss_kb": report["peak_rss_kb"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
