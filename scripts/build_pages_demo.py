#!/usr/bin/env python3
"""Regenerate the static GitHub Pages demo data and verify it stays faithful to the core.

Exports `docs/corpus-data.json` (status-gated chunks, plus the held-out chunks that only the
ADR-018 refusal explanation reads) from the Python corpus, then runs the client-side JS
(`docs/retrieval.js`) under node over a battery of queries and asserts the JS outcome + top doc
+ top chunk + held-out hits match the Python core exactly. Exits nonzero on any mismatch, so
the static demo can never silently drift from `biotech_rag_assistant`.

Usage (from the workbench root, with the dev venv active and node on PATH):
    python scripts/build_pages_demo.py
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CORPUS = ROOT / "examples/synthetic-controlled-docs"

sys.path.insert(0, str(ROOT / "src"))
from biotech_rag_assistant.answer import build_extractive_answer  # noqa: E402
from biotech_rag_assistant.chunking import chunk_document, chunk_documents  # noqa: E402
from biotech_rag_assistant.corpus import load_corpus  # noqa: E402
from biotech_rag_assistant.retrieval import (  # noqa: E402
    RetrievalConfig,
    build_status_blind_retriever,
    held_out_hits,
    run_retrieval,
)

ADVERSARIAL = [
    "reset my email password",
    "weather tomorrow",
    "quarterly sales revenue",
    "documentation procedure for shipping",
    "tell me a joke about cats",
]

# Questions opened through the demo's `?q=` deep link. Every question a link points at stays
# under parity, like the example chips (read from index.html below).
LINKED = [
    "What is the acceptance range for the analytical balance daily check?",
]


def _chunk_record(c) -> dict:
    return {
        "chunk_id": c.chunk_id, "doc_id": c.doc_id, "doc_title": c.doc_title,
        "doc_type": c.doc_type, "version": c.version, "status": c.status,
        "department": c.department, "section_heading": c.section_heading,
        "source_file_path": str(c.source_file_path), "chunk_index": c.chunk_index,
        "line_or_page_span": c.line_or_page_span, "text": c.text,
        "char_start": c.char_start, "char_end": c.char_end, "source_hash": c.source_hash,
    }


def export_corpus_data() -> dict:
    corpus = load_corpus(CORPUS)
    chunks = chunk_documents(corpus.documents)
    excluded = sorted(
        (d for d in corpus.documents if not d.is_retrievable),
        key=lambda d: d.metadata.doc_id,
    )
    # Source text for every valid document, keyed by path, so the UI can show a citation's exact
    # span highlighted in its source (retrievable docs) and reveal what a held-out doc would have
    # said (excluded docs). Retrieval still only ever indexes Approved/Effective chunks.
    sources = {
        str(d.metadata.source_file_path): d.raw_text
        for d in sorted(corpus.documents, key=lambda d: str(d.metadata.source_file_path))
    }
    data = {
        "corpus_name": "synthetic-controlled-docs",
        "documents_total": corpus.report.documents_valid,
        "documents_retrievable": corpus.report.documents_retrievable,
        "documents_excluded": corpus.report.documents_excluded,
        "min_top_coverage": RetrievalConfig().min_top_coverage,
        "score_floor": RetrievalConfig().score_floor,
        "refusal_text": (
            "The retrieved documents do not contain enough information to answer this question."
        ),
        "chunks": [_chunk_record(c) for c in chunks],
        # Held-out chunks feed only the status-blind index behind the refusal explanation
        # (ADR-018). The answer engine indexes `chunks` alone.
        "held_out_chunks": [
            _chunk_record(c) for d in excluded for c in chunk_document(d)
        ],
        "excluded_documents": [
            {
                "doc_id": d.metadata.doc_id, "doc_title": d.metadata.doc_title,
                "doc_type": d.metadata.doc_type, "version": d.metadata.version,
                "status": d.metadata.status, "department": d.metadata.department,
                "source_file_path": str(d.metadata.source_file_path),
            }
            for d in excluded
        ],
        "sources": sources,
    }
    (DOCS / "corpus-data.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return corpus, data


def demo_chip_questions() -> list[str]:
    """The questions behind the demo's example chips, read from index.html itself."""
    index_html = (DOCS / "index.html").read_text(encoding="utf-8")
    return [html.unescape(q) for q in re.findall(r'data-q="([^"]+)"', index_html)]


def python_battery(corpus) -> list[dict]:
    queries: list[tuple[str, int]] = []
    for name in ("golden-questions.json", "natural-language-queries.json"):
        suite = json.loads((CORPUS / "evaluation" / name).read_text(encoding="utf-8"))
        queries += [(c["question"], c.get("top_k", 3)) for c in suite["cases"]]
    queries += [(q, 3) for q in ADVERSARIAL]
    # The page runs chips and deep links with top_k 3 (index.html `engine.answer(q, 3)`).
    queries += [(q, 3) for q in demo_chip_questions() + LINKED]

    status_blind = build_status_blind_retriever(corpus.documents)
    seen: set[str] = set()
    battery: list[dict] = []
    for q, k in queries:
        if q in seen:
            continue
        seen.add(q)
        config = RetrievalConfig(top_k=k)
        hits = run_retrieval(corpus.documents, q, config)
        ans = build_extractive_answer(q, hits)
        battery.append({
            "q": q, "top_k": k, "outcome": ans.outcome,
            "top_doc": hits[0].chunk.doc_id if hits else None,
            "top_chunk": hits[0].chunk.chunk_id if hits else None,
            "held_out": [h.chunk.chunk_id for h in held_out_hits(status_blind, q, config)],
        })
    return battery


NODE_PARITY = """
const RAG = require(process.argv[1]);
const data = require(process.argv[2]);
const expected = require(process.argv[3]);
const eng = RAG.makeEngine(data);
let fails = [];
for (const e of expected) {
  const r = eng.answer(e.q, e.top_k);
  const topDoc = r.hits.length ? r.hits[0].chunk.doc_id : null;
  const topChunk = r.hits.length ? r.hits[0].chunk.chunk_id : null;
  const heldOut = eng.heldOut(e.q, e.top_k).map((h) => h.chunk.chunk_id).join(",");
  if (r.outcome !== e.outcome || topDoc !== e.top_doc || topChunk !== e.top_chunk
      || heldOut !== e.held_out.join(","))
    fails.push({ q: e.q,
      exp: [e.outcome, e.top_doc, e.top_chunk, e.held_out.join(",")],
      got: [r.outcome, topDoc, topChunk, heldOut] });
}
console.log(JSON.stringify({ total: expected.length, fails }));
"""


def export_offline_html() -> None:
    """Write a single self-contained docs/demo-offline.html (no server, no network).

    Inlines retrieval.js and corpus-data.json into index.html so the file runs by double-click
    over file://. index.html boots from window.CORPUS_DATA when present, else fetches as usual,
    so the served Pages version and this offline copy run identical retrieval.
    """
    index_html = (DOCS / "index.html").read_text(encoding="utf-8")
    retrieval_js = (DOCS / "retrieval.js").read_text(encoding="utf-8")
    corpus_json = (DOCS / "corpus-data.json").read_text(encoding="utf-8").strip()
    placeholder = '<script src="retrieval.js"></script>'
    if placeholder not in index_html:
        raise SystemExit('offline build: <script src="retrieval.js"> not found in index.html')
    # Keep a literal </script> inside the inlined JSON from closing the script tag early.
    safe_json = corpus_json.replace("</", "<\\/")
    inline = (
        "<script>window.CORPUS_DATA = " + safe_json + ";</script>\n"
        "<script>\n" + retrieval_js + "\n</script>"
    )
    offline = index_html.replace(placeholder, inline)
    (DOCS / "demo-offline.html").write_text(offline, encoding="utf-8")


def main() -> int:
    corpus, data = export_corpus_data()
    print(f"exported docs/corpus-data.json: {len(data['chunks'])} chunks, "
          f"{data['documents_retrievable']} retrievable, {data['documents_excluded']} excluded")
    export_offline_html()
    print("exported docs/demo-offline.html: single-file offline copy (no server, no network)")
    battery = python_battery(corpus)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(battery, fh)
        expected_path = fh.name
    result = subprocess.run(
        ["node", "-e", NODE_PARITY, str(DOCS / "retrieval.js"),
         str(DOCS / "corpus-data.json"), expected_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("node failed:", result.stderr, file=sys.stderr)
        return 2
    report = json.loads(result.stdout)
    if report["fails"]:
        print(f"PARITY FAILED: {len(report['fails'])}/{report['total']} mismatched")
        for f in report["fails"]:
            print("  ", f)
        return 1
    print(f"PARITY OK: {report['total']}/{report['total']} JS matches Python "
          "(outcome + top doc + top chunk + held-out hits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
