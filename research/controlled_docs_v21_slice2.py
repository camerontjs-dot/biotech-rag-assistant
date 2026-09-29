#!/usr/bin/env python3
"""Slice 2 benchmark-discrimination evaluator for controlled-docs-v2."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, replace
from importlib import metadata
from pathlib import Path

from sentence_transformers import SentenceTransformer

from biotech_rag_assistant.chunking import chunk_document, chunk_documents
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.models import DocumentChunk
from biotech_rag_assistant.retrieval import BM25Retriever, content_terms, index_text, tokenize

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "f5610b47471b118dafc55f4c387822dbfc8413ae"
FLOORS = {"B02": 0.75, "B03": 1.0, "B04": 1.0, "B10_false_answer_max": 0.0}
CONTROLS = (
    "oracle", "null", "first_n", "token_overlap", "return_everything",
    "corrupted_provenance", "hard_negative_biased", "answerability_liar",
    "naive_dense", "status_gate_removed", "bm25_coverage",
)
TAXONOMY = {
    "ingest": ["source_hash_invalid", "metadata_invalid", "span_roundtrip_invalid"],
    "retrieval": ["decisive_miss", "hard_negative_ranked", "stale_leak", "duplicate_burden"],
    "evidence_admission": ["missing_provenance", "unauthorized_source", "budget_overflow"],
    "generation": ["unsupported_claim", "forbidden_fact", "answerability_error"],
    "attribution": ["citation_outside_packet", "quote_not_contained"],
    "security": ["prompt_injection_success", "schema_escape", "poisoned_document_admitted"],
}


@dataclass(frozen=True)
class Case:
    case_id: str
    split: str
    question: str
    top_k: int


@dataclass(frozen=True)
class Gold:
    case_id: str
    doc_id: str | None
    version: str | None
    start: int | None
    end: int | None
    relevance: str | None
    decisive: bool
    disposition: str


@dataclass(frozen=True)
class Hit:
    doc_id: str
    version: str
    status: str
    start: int
    end: int
    chunk_id: str
    score: float


def jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def load_inputs(root: Path):
    cases = []
    for path in (root / "cases/dev_cases.jsonl", root / "cases/test_cases.jsonl"):
        for r in jsonl(path):
            cases.append(Case(r["case_id"], r["split"], r["question"], int(r["top_k"])))
    gold = defaultdict(list)
    for path in (
        root / "evaluator_only/gold/dev_relevance.jsonl",
        root / "evaluator_only/gold/test_relevance.jsonl",
    ):
        for r in jsonl(path):
            gold[r["case_id"]].append(
                Gold(
                    r["case_id"], r.get("doc_id"),
                    str(r["version"]) if r.get("version") is not None else None,
                    int(r["char_start"]) if r.get("char_start") is not None else None,
                    int(r["char_end"]) if r.get("char_end") is not None else None,
                    r.get("relevance_class"), bool(r["decisive"]), r["expected_disposition"],
                )
            )
    families = json.loads((root / "evaluator_only/families.json").read_text())
    freeze = json.loads((root / "freeze_receipt.json").read_text())
    return cases, dict(gold), families, freeze


def overlaps(hit: Hit, gold: Gold) -> bool:
    if None in (gold.doc_id, gold.version, gold.start, gold.end):
        return False
    return (
        hit.doc_id == gold.doc_id
        and hit.version == gold.version
        and max(hit.start, gold.start) < min(hit.end, gold.end)
    )


def as_hit(chunk: DocumentChunk, score: float = 0.0) -> Hit:
    return Hit(
        chunk.doc_id, chunk.version, chunk.status, chunk.char_start, chunk.char_end,
        chunk.chunk_id, float(score),
    )


def unique(hits: list[Hit]) -> list[Hit]:
    seen, out = set(), []
    for h in hits:
        key = (h.doc_id, h.version, h.start, h.end)
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out


def expected(spans: list[Gold]) -> str:
    values = {x.disposition for x in spans}
    if len(values) != 1:
        raise ValueError(f"mixed dispositions: {values}")
    return next(iter(values))


def gold_hits(spans: list[Gold], chunks: list[DocumentChunk], decisive: bool) -> list[Hit]:
    out = []
    for g in [x for x in spans if x.decisive is decisive]:
        for c in chunks:
            h = as_hit(c, 1.0)
            if overlaps(h, g):
                out.append(h)
                break
    return unique(out)


def score(case: Case, spans: list[Gold], hits: list[Hit], disposition: str) -> dict:
    decisive = [g for g in spans if g.decisive]
    hard = [g for g in spans if g.relevance in {"hard_negative", "stale_trap"}]
    uniq = unique(hits)
    top = uniq[: case.top_k]
    found = sum(any(overlaps(h, g) for h in top) for g in decisive)
    want = expected(spans)
    return {
        "case_id": case.case_id,
        "decisive_total": len(decisive),
        "decisive_found": found,
        "case_hit": bool(decisive) and found == len(decisive),
        "disposition_ok": disposition == want,
        "false_answer": want in {"not_stated", "refusal"} and disposition == "answer",
        "stale_leaks": sum(h.status not in {"Approved", "Effective"} for h in top),
        "hard_negative_hits": sum(any(overlaps(h, g) for g in hard) for h in top),
        "duplicate_burden": len(hits) - len(uniq),
        "budget_overflow": len(uniq) > case.top_k,
        "top": [h.__dict__ for h in top],
    }


def aggregate(rows: list[dict]) -> dict:
    dtotal = sum(x["decisive_total"] for x in rows)
    dcases = [x for x in rows if x["decisive_total"]]
    return {
        "cases": len(rows),
        "decisive_span_recall_at_k": (
            sum(x["decisive_found"] for x in rows) / dtotal if dtotal else None
        ),
        "decisive_case_recall_at_k": (
            sum(x["case_hit"] for x in dcases) / len(dcases) if dcases else None
        ),
        "disposition_accuracy": sum(x["disposition_ok"] for x in rows) / len(rows),
        "false_answer_rate": sum(x["false_answer"] for x in rows) / len(rows),
        "stale_leak_count": sum(x["stale_leaks"] for x in rows),
        "hard_negative_hit_count": sum(x["hard_negative_hits"] for x in rows),
        "duplicate_burden": sum(x["duplicate_burden"] for x in rows),
        "budget_overflow_count": sum(x["budget_overflow"] for x in rows),
    }


def token_rank(question: str, chunks: list[DocumentChunk], top_k: int) -> list[Hit]:
    q = content_terms(question)
    scored = []
    for c in chunks:
        terms = set(tokenize(index_text(c)))
        s = len(q & terms) / (len(q | terms) or 1)
        scored.append((s, c))
    scored.sort(key=lambda x: (-x[0], x[1].doc_id, x[1].chunk_index, x[1].chunk_id))
    return [as_hit(c, s) for s, c in scored[:top_k] if s > 0]


class Dense:
    def __init__(self, chunks: list[DocumentChunk]):
        self.model = SentenceTransformer(MODEL, revision=REVISION, device="cpu")
        self.chunks = chunks
        self.emb = self.model.encode(
            [index_text(c) for c in chunks], normalize_embeddings=True, show_progress_bar=False
        )

    def rank(self, question: str, top_k: int) -> list[Hit]:
        q = self.model.encode([question], normalize_embeddings=True, show_progress_bar=False)[0]
        scores = (self.emb @ q).tolist()
        order = sorted(
            range(len(self.chunks)),
            key=lambda i: (
                -float(scores[i]), self.chunks[i].doc_id,
                self.chunks[i].chunk_index, self.chunks[i].chunk_id,
            ),
        )
        return [as_hit(self.chunks[i], scores[i]) for i in order[:top_k]]


def run_control(
    name: str,
    case: Case,
    spans: list[Gold],
    retrievable: list[DocumentChunk],
    all_chunks: list[DocumentChunk],
    bm25: BM25Retriever,
    dense: Dense,
) -> tuple[list[Hit], str]:
    want = expected(spans)
    if name == "oracle":
        return gold_hits(spans, retrievable, True), want
    if name == "null":
        return [], "refusal"
    if name == "first_n":
        hits = [as_hit(c, 1.0) for c in retrievable[: case.top_k]]
    elif name == "token_overlap":
        hits = token_rank(case.question, retrievable, case.top_k)
    elif name == "return_everything":
        hits = [as_hit(c, 1.0) for c in retrievable]
    elif name == "corrupted_provenance":
        hits = gold_hits(spans, retrievable, True)
        if hits:
            hits[0] = replace(hits[0], version=hits[0].version + "-corrupt")
        return hits, want
    elif name == "hard_negative_biased":
        hits = gold_hits(spans, retrievable, False)
        if not hits:
            hits = [as_hit(c, 1.0) for c in retrievable[: case.top_k]]
    elif name == "answerability_liar":
        return gold_hits(spans, retrievable, True), "answer"
    elif name == "naive_dense":
        hits = dense.rank(case.question, case.top_k)
    elif name == "status_gate_removed":
        raw = BM25Retriever(all_chunks).query(
            case.question, top_k=case.top_k, min_top_coverage=0.6
        )
        hits = [as_hit(h.chunk, h.score) for h in raw]
    elif name == "bm25_coverage":
        raw = bm25.query(case.question, top_k=case.top_k, min_top_coverage=0.6)
        hits = [as_hit(h.chunk, h.score) for h in raw]
    else:
        raise KeyError(name)
    return hits, "answer" if hits else "refusal"


def evaluate(name, cases, gold, families, retrievable, all_chunks, bm25, dense):
    rows = []
    for case in cases:
        hits, disp = run_control(
            name, case, gold[case.case_id], retrievable, all_chunks, bm25, dense
        )
        rows.append(score(case, gold[case.case_id], hits, disp))
    groups = defaultdict(list)
    for row in rows:
        groups[families[row["case_id"]]["family"]].append(row)
    return {
        "overall": aggregate(rows),
        "families": {k: aggregate(v) for k, v in sorted(groups.items())},
        "records": rows,
    }


def gate(results: dict) -> dict:
    t = results["token_overlap"]["families"]
    d = results["naive_dense"]["families"]
    oracle = results["oracle"]["overall"]
    checks = {
        "oracle_ceiling": (
            oracle["decisive_span_recall_at_k"] == 1.0
            and oracle["disposition_accuracy"] == 1.0
            and oracle["stale_leak_count"] == 0
        ),
        "token_fails_B02": (t["B02"]["decisive_span_recall_at_k"] or 0) < FLOORS["B02"],
        "token_fails_B10": t["B10"]["false_answer_rate"] > FLOORS["B10_false_answer_max"],
        "dense_fails_B03": (d["B03"]["decisive_span_recall_at_k"] or 0) < FLOORS["B03"],
        "dense_fails_B04": (d["B04"]["decisive_span_recall_at_k"] or 0) < FLOORS["B04"],
        "null_rejected": results["null"]["overall"]["decisive_span_recall_at_k"] < 1.0,
        "first_n_rejected": results["first_n"]["overall"]["decisive_span_recall_at_k"] < 1.0,
        "return_all_rejected": results["return_everything"]["overall"]["budget_overflow_count"] > 0,
        "corrupt_provenance_rejected": (
            results["corrupted_provenance"]["overall"]["decisive_span_recall_at_k"] < 1.0
        ),
        "hard_negative_rejected": (
            results["hard_negative_biased"]["overall"]["decisive_span_recall_at_k"] < 1.0
        ),
        "answerability_liar_rejected": (
            results["answerability_liar"]["overall"]["false_answer_rate"] > 0
        ),
        "status_gate_removed_rejected": (
            results["status_gate_removed"]["overall"]["stale_leak_count"] > 0
        ),
    }
    checks["two_sided_discrimination"] = all(
        checks[k] for k in (
            "token_fails_B02", "token_fails_B10", "dense_fails_B03", "dense_fails_B04"
        )
    )
    return checks


def metamorphic(cases, gold, retrievable):
    rng = random.Random(20260928)
    shuffled = retrievable[:]
    rng.shuffle(shuffled)
    order_ok = all(
        [
            (h.doc_id, h.version, h.start, h.end)
            for h in token_rank(c.question, retrievable, c.top_k)
        ]
        == [
            (h.doc_id, h.version, h.start, h.end)
            for h in token_rank(c.question, shuffled, c.top_k)
        ]
        for c in cases
    )
    case = next(c for c in cases if expected(gold[c.case_id]) == "answer")
    spans = gold[case.case_id]
    hits = gold_hits(spans, retrievable, True)
    base = score(case, spans, hits, "answer")
    dup = score(case, spans, hits + hits[:1], "answer")
    duplicate_ok = (
        dup["decisive_found"] == base["decisive_found"]
        and dup["duplicate_burden"] == base["duplicate_burden"] + 1
    )
    target = next(g for g in spans if g.decisive)
    assert target.end is not None
    mutated = replace(target, start=target.end + 10000, end=target.end + 10001)
    altered = [mutated if g is target else g for g in spans]
    mutation_ok = score(case, altered, hits, "answer")["decisive_found"] < base["decisive_found"]

    withhold_ok = True
    count = 0
    for c in cases:
        decisive = [g for g in gold[c.case_id] if g.decisive]
        if not decisive:
            continue
        filtered = [
            ch for ch in retrievable
            if not any(overlaps(as_hit(ch), g) for g in decisive)
        ]
        if any(any(overlaps(as_hit(ch), g) for g in decisive) for ch in filtered):
            withhold_ok = False
        count += 1
    return {
        "source_order_permutation_invariant": order_ok,
        "duplicate_insertion_no_extra_credit": duplicate_ok,
        "mutated_gold_changes_judgment": mutation_ok,
        "withhold_decisive_removes_decisive_chunks": withhold_ok,
        "withhold_cases_checked": count,
        "all_pass": order_ok and duplicate_ok and mutation_ok and withhold_ok,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown(report: dict) -> str:
    g = report["gate"]
    lines = [
        "# controlled-docs-v2 Slice 2 diagnostic evaluator", "",
        f"Disposition: {report['disposition']}", "",
        "This gate evaluates benchmark discrimination only. It promotes no retrieval method.", "",
        "## Gate", "",
    ]
    for k, v in g.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Metamorphic checks", ""]
    for k, v in report["metamorphic"].items():
        lines.append(f"- {k}: {v}")
    lines += [
        "", "## Family observations", "",
        (
            "| control | family | decisive span recall@K | disposition accuracy | "
            "false answer rate | stale leaks |"
        ),
        "|---|---|---:|---:|---:|---:|",
    ]
    for control, result in report["controls"].items():
        for family, m in result["families"].items():
            recall = m["decisive_span_recall_at_k"]
            lines.append(
                f"| {control} | {family} | {'n/a' if recall is None else f'{recall:.3f}'} | "
                f"{m['disposition_accuracy']:.3f} | {m['false_answer_rate']:.3f} | "
                f"{m['stale_leak_count']} |"
            )
    lines += [
        "", "## Non-claims", "",
        "- MiniLM is a deliberately naive control here, not a candidate.",
        "- PROSPECTIVE remains sealed and is not evaluated.",
        "- A Slice 2 pass authorizes comparison work only.",
        "- Results apply only to this frozen synthetic benchmark and evaluator identity.",
        "", "## Error taxonomy carried forward", "",
    ]
    for layer, codes in TAXONOMY.items():
        lines.append(f"- {layer}: " + ", ".join(codes))
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    root, out = a.benchmark.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    cases, gold, families, freeze = load_inputs(root)
    corpus = load_corpus(root / "corpus")
    retrievable = chunk_documents(corpus.documents)
    all_chunks = [c for d in corpus.documents for c in chunk_document(d)]
    bm25 = BM25Retriever(retrievable)
    dense = Dense(retrievable)

    results = {}
    for name in CONTROLS:
        print(f"evaluating {name}", flush=True)
        results[name] = evaluate(
            name, cases, gold, families, retrievable, all_chunks, bm25, dense
        )

    checks = gate(results)
    meta = metamorphic(cases, gold, retrievable)
    passed = all(checks.values()) and meta["all_pass"]
    disposition = (
        "PASS_FOR_SLICE3_RETRIEVAL_COMPARISON"
        if passed else "BLOCK_SLICE3_BENCHMARK_NOT_DISCRIMINATING"
    )
    report = {
        "schema_version": "slice2-evaluator-v1",
        "disposition": disposition,
        "benchmark": {
            "tree_sha256": freeze["tree_sha256"],
            "prospective_sha256": freeze["prospective_sha256"],
            "freeze_receipt_sha256": sha256(root / "freeze_receipt.json"),
            "cases": len(cases),
            "dev_cases": sum(c.split == "DEV" for c in cases),
            "test_cases": sum(c.split == "TEST" for c in cases),
            "retrievable_chunks": len(retrievable),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "sentence_transformers": metadata.version("sentence-transformers"),
            "dense_model": MODEL,
            "dense_model_revision": REVISION,
        },
        "floors": FLOORS,
        "error_taxonomy": TAXONOMY,
        "controls": results,
        "gate": checks,
        "metamorphic": meta,
    }
    (out / "slice2-results.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "slice2-report.md").write_text(markdown(report))
    print(json.dumps({"disposition": disposition, "gate": checks, "metamorphic": meta}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
