# Biotech RAG Assistant

[![CI](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/workflows/ci.yml) &nbsp;·&nbsp; **▶ [Live demo](https://camerontjs-dot.github.io/biotech-rag-assistant/)** &nbsp;·&nbsp; [Design decisions (ADRs)](DECISIONS.md)

A controlled-document retrieval pilot for regulated industries (pharma, biotech, CRO, cosmetics/OTC) that **builds the trust layer before the model**. Most RAG demos generate first and bolt citations on afterward; this inverts the order — status gating, provenance, refusal, an audit log, and an evaluation harness all come first, and any LLM stays *behind* that boundary.

The current slice is deliberately narrow and fully deterministic: it validates document metadata and source hashes (fail-closed), gates retrieval to `Approved`/`Effective` documents, chunks source text with stable IDs and **exact-span provenance** (a citation's quote is byte-identical to `raw_text[char_start:char_end]`), ranks with BM25 behind a lexical refusal gate, and assembles extractive answers whose citations must resolve to retrieved chunks.

**If you're evaluating this:** open the [live demo](https://camerontjs-dot.github.io/biotech-rag-assistant/) and click the **obsolete-doc trap** — it refuses, then shows you the retired SOP the status gate kept out. Then read [`DECISIONS.md`](DECISIONS.md): 17 architecture decisions, each with the alternatives it rejected. Verified by 97 tests across Python 3.11–3.13 (CI above), a 24-case trust suite that plants traps and passes only when it catches them, and JS↔Python parity on the demo.

## What this is and is not

This is a portfolio asset for testing how a document assistant should behave before an LLM is added. The useful question here is whether the system can keep source identity, document status, version, hash, and chunk IDs attached to retrieval results and answer output.

This is not a regulated quality system. It does not certify compliance, verify that a document is true, make batch-release decisions, or replace QA, validation, regulatory, or legal review.

## Why this exists

Generic RAG demos often skip the boring parts that matter in regulated work: which document version was retrieved, whether it was approved, whether the cited section came from the retrieved context, and what should happen when no source supports the question.

This pilot starts with those controls. Retrieval nominates candidate passages from a bounded corpus. The answer command copies retrieved spans and validates its own citations, so later answer generation has to respect that boundary.

## Try it

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/biotech-rag onboard-corpus examples/synthetic-messy-client-corpus \
  --output build/onboarded-synthetic-corpus \
  --report-out build/onboarding-report.json \
  --markdown-out build/onboarding-report.md
.venv/bin/biotech-rag validate-corpus build/onboarded-synthetic-corpus
.venv/bin/biotech-rag validate-corpus examples/synthetic-controlled-docs
.venv/bin/biotech-rag retrieve examples/synthetic-controlled-docs \
  --query "viable excursion affected product lots immediate containment" \
  --top-k 3 \
  --json
.venv/bin/biotech-rag answer examples/synthetic-controlled-docs \
  --query "viable excursion affected product lots immediate containment" \
  --top-k 2
.venv/bin/biotech-rag validate-citations \
  tests/fixtures/citation-validation/retrieval-valid.json \
  tests/fixtures/citation-validation/answer-valid.json \
  --json
.venv/bin/biotech-rag evaluate \
  examples/synthetic-controlled-docs \
  examples/synthetic-controlled-docs/evaluation/golden-questions.json \
  --markdown-out build/evaluation-report.md \
  --json-out build/evaluation-report.json
```

Expected behavior:

- messy client-like sources are mapped into a normalized corpus only when required metadata can be established;
- documents that need review or are rejected stay out of the normalized retrieval corpus;
- the public synthetic corpus validates cleanly;
- approved and effective documents enter retrieval;
- draft and obsolete documents are excluded from retrieval context;
- JSON output includes `chunk_id`, `doc_id`, `source_hash`, status, version, and source span.
- answer output includes `outcome`, copied retrieved spans, structured citations, retrieved chunk metadata, and citation-validation results;
- citation checks report `citation_resolves_to_retrieved_chunk`, which means only that a cited `chunk_id` appeared in retrieved results;
- the trust-layer evaluation suite reports `trust_layer_status: pass` and `case_pass_rate: 24/24`.

## Run the HTTP API

The same core logic is exposed over HTTP as a pure-transport layer: each route calls the same
function as the matching CLI command and returns the same JSON. Corpora are bound to a name-based
allowlist at startup; requests never pass a filesystem path. See `docs/api-transport.md` for the
full contract, security posture, and environment variables, and ADR-010 for the decision record.

```bash
.venv/bin/biotech-rag serve            # or: .venv/bin/uvicorn biotech_rag_assistant.api:app
# in another shell:
curl -s localhost:8000/health
curl -s localhost:8000/retrieve -H 'content-type: application/json' \
  -d '{"query": "viable excursion affected product lots immediate containment", "top_k": 1}'
curl -s localhost:8000/answer -H 'content-type: application/json' \
  -d '{"query": "viable excursion affected product lots immediate containment", "top_k": 1}'
```

`/answer` adds an advisory `review_recommendation` an orchestrator can route on; it does not change
the `answer`/`refusal` outcome. Set `BIOTECH_RAG_API_KEY` to require an `X-API-Key` header on every
route except `/health`, and `BIOTECH_RAG_AUDIT_LOG` to append one JSONL audit record per request.

## Current build

The current code ships:

- synthetic controlled-document corpus under `examples/synthetic-controlled-docs/`;
- synthetic messy-client corpus under `examples/synthetic-messy-client-corpus/`;
- client-corpus onboarding CLI that writes a normalized corpus plus JSON and Markdown coverage reports;
- fail-closed metadata and source-hash validation, including a one-retrievable-version-per-`doc_id` invariant (ADR-013);
- deterministic paragraph chunking with stable chunk IDs;
- shared `RetrievalConfig` used by retrieval, evaluation, and answer assembly;
- BM25 retrieval over approved/effective chunks only, with a lexical relevance gate that refuses off-topic questions instead of copying loosely-related passages (ADR-012);
- CLI surfaces for corpus validation, retrieval, deterministic extractive answers, citation validation, and evaluation, plus a demo chat UI (`biotech-rag demo`) that serves a trust-forward page over the `/answer` contract;
- a FastAPI pure-transport layer (`biotech-rag serve`) exposing the same five operations plus `/health`, with a server-bound corpus allowlist, optional API-key auth, per-request audit records, and an advisory review-routing signal on `/answer`;
- structural citation-resolution validation over hand-written answer fixtures;
- a 24-case trust-layer evaluation suite (supported retrieval, refusal, stale-document, current-version, and citation traps), plus a separate 13-case natural-language query suite (on-topic answer, off-topic refusal);
- Markdown and JSON trust-layer reports with corpus/config metadata, metrics, a case table, and explicit limits;
- tests for status filtering, malformed metadata, deterministic ranking, unsupported queries, extractive answers, citation resolution, report writing, and JSON output.

Deferred work:

- LLM answer generation;
- semantic citation-support assessment;
- semantic retrieval and reciprocal-rank fusion;
- n8n workflow exports.

## Verification

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python -m compileall src
.venv/bin/biotech-rag onboard-corpus examples/synthetic-messy-client-corpus \
  --output build/onboarded-synthetic-corpus \
  --report-out build/onboarding-report.json \
  --markdown-out build/onboarding-report.md
.venv/bin/biotech-rag validate-corpus build/onboarded-synthetic-corpus
.venv/bin/biotech-rag validate-corpus examples/synthetic-controlled-docs
.venv/bin/biotech-rag retrieve \
  examples/synthetic-controlled-docs \
  --query "viable excursion affected product lots immediate containment" \
  --top-k 1 \
  --json
.venv/bin/biotech-rag answer \
  examples/synthetic-controlled-docs \
  --query "viable excursion affected product lots immediate containment" \
  --top-k 2
.venv/bin/biotech-rag validate-citations \
  tests/fixtures/citation-validation/retrieval-valid.json \
  tests/fixtures/citation-validation/answer-valid.json \
  --json
.venv/bin/biotech-rag evaluate \
  examples/synthetic-controlled-docs \
  examples/synthetic-controlled-docs/evaluation/golden-questions.json \
  --markdown-out build/evaluation-report.md \
  --json-out build/evaluation-report.json
```

Live-server smoke (start `biotech-rag serve` in another shell first):

```bash
curl -si localhost:8000/health | grep -i x-request-id
curl -s localhost:8000/answer -H 'content-type: application/json' \
  -d '{"query": "zzzz qqqq impossible-token"}'   # outcome: refusal, review_recommended: true
```

Regenerate and parity-check the static demo (requires Node):

```bash
.venv/bin/python scripts/build_pages_demo.py   # exports docs/corpus-data.json, asserts JS == Python
```

## License

Copyright © 2026 Cameron Sanderson. **All rights reserved — source-available, not open-source.**
The repository is public so the synthetic demo can be shared; no license to reuse, copy, or
modify the code is granted. The committed corpus is synthetic and contains no real, client, or
regulated records. See [`LICENSE`](LICENSE).
