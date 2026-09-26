#!/usr/bin/env python3
"""Record Baseline V1, the before-state for the public generative RAG v2 plan (Slice 0).

Usage (from the repository root, with the dev venv active):
    python scripts/record_baseline.py              # write baselines/v1/baseline.json
    python scripts/record_baseline.py --check      # exit 1 if the committed record differs
    python scripts/record_baseline.py --latency    # also write baselines/v1/latency.json

baseline.json holds identities and behavior only: no timestamps, no absolute paths, sorted keys.
The same checkout always produces the same bytes, so --check compares files exactly. Once later
slices change the package on purpose, --check is expected to fail; record a new baseline instead
of editing this one. latency.json is machine-dependent and never checked.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import platform
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from biotech_rag_assistant import __version__  # noqa: E402
from biotech_rag_assistant.answer import build_extractive_answer  # noqa: E402
from biotech_rag_assistant.chunking import chunk_documents  # noqa: E402
from biotech_rag_assistant.corpus import load_corpus  # noqa: E402
from biotech_rag_assistant.evaluation import (  # noqa: E402
    load_evaluation_suite,
    run_evaluation_suite,
)
from biotech_rag_assistant.retrieval import (  # noqa: E402
    BM25Retriever,
    RetrievalConfig,
    build_retriever,
    query_retriever,
)

BASE_COMMIT = "40de3cdcd98973b0e3a1c91d6ac114bc62857c04"
BASELINE_DIR = ROOT / "baselines/v1"
BASELINE_PATH = BASELINE_DIR / "baseline.json"
LATENCY_PATH = BASELINE_DIR / "latency.json"
PROBES_PATH = BASELINE_DIR / "near-miss-probes.json"
CORPUS_DIR = ROOT / "examples/synthetic-controlled-docs"
SUITES = {
    "trust": CORPUS_DIR / "evaluation/golden-questions.json",
    "natural_language": CORPUS_DIR / "evaluation/natural-language-queries.json",
}
IDENTITY_FILES = (
    "examples/synthetic-controlled-docs/evaluation/golden-questions.json",
    "examples/synthetic-controlled-docs/evaluation/natural-language-queries.json",
    "baselines/v1/near-miss-probes.json",
    "experiments/queries-labeled.json",
    "experiments/comparison-results.json",
    "docs/index.html",
    "docs/retrieval.js",
    "docs/corpus-data.json",
    "docs/demo-offline.html",
)
# docs/index.html renders these chips and calls engine.answer(question, 3).
CHIP_RE = re.compile(
    r'<span class="chip[^"]*" data-q="([^"]+)"(?: data-reveal="([^"]+)")?>([^<]+)</span>'
)
DEMO_TOP_K = 3
RECIPES = {
    "canonical_sha256": (
        "sha256 of json.dumps(value, sort_keys=True, separators=(',', ':'), "
        "ensure_ascii=False) encoded as UTF-8"
    ),
    "corpus.manifest_sha256": (
        "canonical_sha256 of [{doc_id, version, status, source_hash}] sorted by (doc_id, version)"
    ),
    "corpus.chunk_manifest_sha256": (
        "canonical_sha256 of [{chunk_id, char_start, char_end, source_hash}] in index order"
    ),
    "package.source_digest": (
        "canonical_sha256 of sorted [relative_path, sha256(file bytes)] pairs for every file "
        "under src/biotech_rag_assistant, excluding __pycache__ and hidden files"
    ),
}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_sha256(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(text.encode("utf-8"))


def source_digest(package_dir: Path) -> str:
    files = sorted(
        path
        for path in package_dir.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    )
    return canonical_sha256(
        [[path.relative_to(package_dir).as_posix(), sha256_bytes(path.read_bytes())]
         for path in files]
    )


def corpus_record(corpus_dir: Path) -> dict:
    """Identity of a corpus: its documents and the chunks the current chunker produces."""
    corpus = load_corpus(corpus_dir)
    documents = sorted(
        (
            {
                "doc_id": document.metadata.doc_id,
                "version": document.metadata.version,
                "status": document.metadata.status,
                "source_hash": document.metadata.source_hash,
            }
            for document in corpus.documents
        ),
        key=lambda row: (row["doc_id"], row["version"]),
    )
    chunks = [
        {
            "chunk_id": chunk.chunk_id,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "source_hash": chunk.source_hash,
        }
        for chunk in chunk_documents(corpus.documents)
    ]
    return {
        "dir": corpus_dir.resolve().relative_to(ROOT).as_posix(),
        "documents": documents,
        "manifest_sha256": canonical_sha256(documents),
        "documents_valid": corpus.report.documents_valid,
        "documents_retrievable": corpus.report.documents_retrievable,
        "documents_excluded": corpus.report.documents_excluded,
        "chunk_count": len(chunks),
        "chunk_manifest_sha256": canonical_sha256(chunks),
    }


def suite_record(path: Path) -> dict:
    report = run_evaluation_suite(CORPUS_DIR, load_evaluation_suite(path))
    return {
        "file": path.relative_to(ROOT).as_posix(),
        "suite_name": report.suite_name,
        "trust_layer_status": report.trust_layer_status,
        "passed": f"{report.passed_case_count}/{report.case_count}",
        "metrics": report.metrics,
        "cases": [
            {
                "case_id": case.case_id,
                "passed": case.passed,
                "outcome": case.generated_answer_outcome,
                "hit_chunk_ids": case.hit_chunk_ids,
            }
            for case in report.cases
        ],
    }


def demo_record(retriever: BM25Retriever) -> dict:
    """Outcomes of the public demo's example chips, computed by the Python core.

    scripts/build_pages_demo.py asserts the browser engine matches the Python core, so these are
    also the outcomes a visitor sees.
    """
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    chips = []
    for question, reveal_doc_id, label in CHIP_RE.findall(page):
        question = html.unescape(question)
        hits = query_retriever(retriever, question, RetrievalConfig(top_k=DEMO_TOP_K))
        answer = build_extractive_answer(question, hits)
        chips.append(
            {
                "label": html.unescape(label).strip(),
                "question": question,
                "reveal_doc_id": reveal_doc_id or None,
                "outcome": answer.outcome,
                "cited_chunk_ids": [citation.chunk_id for citation in answer.citations],
            }
        )
    return {"top_k": DEMO_TOP_K, "chips": chips}


def adr014_record() -> dict:
    """Headline of the recorded ADR-014 comparison, as committed. Not re-run here."""
    results = json.loads(
        (ROOT / "experiments/comparison-results.json").read_text(encoding="utf-8")
    )
    methods = ("bm25", "semantic", "hybrid")
    return {
        "model": results["model"],
        "n_chunks": results["n_chunks"],
        "hard_mrr": {m: round(results["metrics"]["hard"][m]["mrr"], 4) for m in methods},
        "all_recall_at_1": {
            m: round(results["metrics"]["all"][m]["recall@1"], 4) for m in methods
        },
        "semantic_clean_threshold": results["separation"]["semantic"]["clean_threshold_exists"],
        "production_coverage_gate": results["production_coverage_gate"],
        "bm25_arm_checked_by": "tests/test_experiment_harness.py",
        "semantic_arm_rerun_after_2026_06_13": False,
    }


def build_record() -> dict:
    corpus = load_corpus(CORPUS_DIR)
    retriever = build_retriever(corpus.documents)
    config = RetrievalConfig().to_cli_record()
    return {
        "baseline": "v1",
        "schema_version": 1,
        "base_commit": BASE_COMMIT,
        "recipes": RECIPES,
        "package": {
            "name": "biotech-rag-assistant",
            "version": __version__,
            "source_digest": source_digest(ROOT / "src/biotech_rag_assistant"),
        },
        "corpus": corpus_record(CORPUS_DIR),
        "retrieval_config": {"record": config, "sha256": canonical_sha256(config)},
        "files": {rel: sha256_bytes((ROOT / rel).read_bytes()) for rel in IDENTITY_FILES},
        "suites": {name: suite_record(path) for name, path in SUITES.items()},
        "demo": demo_record(retriever),
        "adr014": adr014_record(),
    }


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[round(fraction * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict:
    return {
        "p50": round(_percentile(values, 0.50), 3),
        "p95": round(_percentile(values, 0.95), 3),
        "max": round(max(values), 3),
        "samples": len(values),
    }


def _latency_questions() -> list[tuple[str, int]]:
    questions: list[tuple[str, int]] = []
    for path in SUITES.values():
        suite = json.loads(path.read_text(encoding="utf-8"))
        questions += [(case["question"], case.get("top_k", 3)) for case in suite["cases"]]
    probes = json.loads(PROBES_PATH.read_text(encoding="utf-8"))
    questions += [(probe["question"], probes["top_k"]) for probe in probes["probes"]]
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    questions += [(html.unescape(q), DEMO_TOP_K) for q, _, _ in CHIP_RE.findall(page)]
    return list(dict.fromkeys(questions))


def latency_record(repeats: int = 30, build_repeats: int = 10) -> dict:
    corpus = load_corpus(CORPUS_DIR)
    build_ms = []
    for _ in range(build_repeats):
        start = time.perf_counter()
        build_retriever(corpus.documents)
        build_ms.append((time.perf_counter() - start) * 1000)

    retriever = build_retriever(corpus.documents)
    questions = _latency_questions()
    retrieve_ms: list[float] = []
    answer_ms: list[float] = []
    for question, top_k in questions:
        config = RetrievalConfig(top_k=top_k)
        query_retriever(retriever, question, config)  # warm-up, not timed
        for _ in range(repeats):
            start = time.perf_counter()
            hits = query_retriever(retriever, question, config)
            retrieved = time.perf_counter()
            build_extractive_answer(question, hits)
            done = time.perf_counter()
            retrieve_ms.append((retrieved - start) * 1000)
            answer_ms.append((done - start) * 1000)

    return {
        "note": (
            "In-process, warm, single-threaded timings in milliseconds on the recording machine. "
            "No HTTP transport. Machine-dependent: not an identity and never checked."
        ),
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "distinct_questions": len(questions),
        "repeats_per_question": repeats,
        "index_build_ms": _summary(build_ms),
        "retrieve_ms": _summary(retrieve_ms),
        "retrieve_and_answer_ms": _summary(answer_ms),
    }


def _dump(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare instead of writing")
    parser.add_argument("--latency", action="store_true", help="also write latency.json")
    args = parser.parse_args(argv)

    record = build_record()
    text = _dump(record)
    if args.check:
        committed = BASELINE_PATH.read_text(encoding="utf-8") if BASELINE_PATH.exists() else ""
        if committed == text:
            print(f"{BASELINE_PATH.relative_to(ROOT)} matches the current checkout")
            return 0
        previous = json.loads(committed) if committed else {}
        changed = sorted(key for key in record if previous.get(key) != record[key])
        print(
            f"{BASELINE_PATH.relative_to(ROOT)} differs from the current checkout in: "
            + (", ".join(changed) or "formatting"),
            file=sys.stderr,
        )
        return 1

    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {BASELINE_PATH.relative_to(ROOT)}")
    if args.latency:
        LATENCY_PATH.write_text(_dump(latency_record()), encoding="utf-8")
        print(f"wrote {LATENCY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
