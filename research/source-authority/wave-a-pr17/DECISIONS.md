# Biotech RAG Assistant decisions

This file records the early design decisions for the controlled-document retrieval pilot.

## ADR-001: Standalone portfolio asset

Status: accepted

Decision: Biotech RAG Assistant is a standalone portfolio asset at `live-asset/biotech-rag-assistant/`. It is not part of the C-A / C-B research apparatus and does not produce or consume apparatus artifacts.

Reasoning: The apparatus measures whether workflow scaffolds reduce unsupported claims. This asset tests a different product shape: controlled-document retrieval with explicit status, version, source hash, and chunk identity. The work shares vocabulary with Evidence Bundler and Claim Audit Lab, but the data model is specific to approved-document search.

Rejected alternatives: treating this as a fourth apparatus component, building inside Evidence Bundler, or waiting for a client discovery call before creating the local asset.

Consequences: Workspace-level portfolio rules still apply. Apparatus contract rules do not apply unless a future decision deliberately connects this asset to C-A or C-B.

## ADR-002: Local BM25 baseline before semantic retrieval

Status: accepted

Decision: Slice 1 uses local BM25 retrieval over deterministic chunks before adding embeddings, RRF, reranking, or answer generation.

Reasoning: BM25 is deterministic, cheap to test, and useful for exact regulated-document language such as SOP IDs, QA terms, and procedure names. It gives the project a stable baseline before semantic retrieval introduces model and index variation.

Rejected alternatives: starting with semantic retrieval, starting with a chat UI, or wiring an LLM before retrieval tests exist.

Consequences: Early tests focus on expected source nomination, status filtering, and no-hit behavior. Semantic retrieval can be added after the baseline has fixed fixtures.

## ADR-003: Synthetic-only corpus for public work

Status: accepted

Decision: The committed corpus is synthetic. No client documents, patient data, batch records, private SOPs, or real regulated records belong in the public asset.

Reasoning: The goal is to prove retrieval behavior and failure handling, not to expose or simulate possession of private quality records. A fictional corpus is enough to test metadata gates, source hashes, retrieval ranking, and obsolete-document traps.

Rejected alternatives: using real Apollo or former-employer documents, searching public SOP PDFs, or accepting redacted client examples before a data-handling agreement exists.

Consequences: Public examples can be shared and tested without privacy review. Any future private pilot needs its own data boundary and deployment decision.

## ADR-004: n8n deferred to orchestration

Status: accepted

Decision: n8n is deferred until the retrieval baseline is green. It is treated as orchestration for triggers, review routing, backfills, and notifications, not as the core retrieval-validation engine.

Reasoning: Metadata enforcement, status gating, source hashing, and retrieval tests need to live in versioned code. n8n can make the workflow legible and shareable later, but the evidence boundary should not depend on a visual workflow alone.

Rejected alternatives: starting from an n8n template, implementing retrieval logic inside Code nodes, or publishing a workflow before current-version behavior is reproduced.

Consequences: Slice 1 has no n8n runtime dependency. Any future n8n tutorial must pin versions and recheck metadata-filter behavior against the current release.

## ADR-005: Fail-closed status filtering

Status: accepted

Decision: Only `Approved` and `Effective` documents enter retrieval context. Draft, obsolete, and superseded documents can be present in the corpus but are excluded from indexing.

Reasoning: A controlled-document assistant is only useful if it refuses stale or non-approved sources by default. The status gate is mechanical and testable, so it belongs before retrieval.

Rejected alternatives: retrieve from every valid document and down-rank stale sources, expose draft content with warnings, or let the query choose status behavior.

Consequences: The synthetic corpus includes draft and obsolete traps. Retrieval tests assert that those documents do not appear in returned chunks.

## ADR-006: Reuse Evidence Bundler discipline without a package dependency

Status: accepted

Decision: Slice 1 follows Evidence Bundler's retrieval discipline and BM25 implementation pattern, but it implements local models and loader code rather than importing Evidence Bundler as a dependency.

Reasoning: Evidence Bundler is the strongest local reference for retrieval nomination, traceability, and calibrated language. This asset still needs product-specific metadata fields, especially status and version gating. A direct package dependency would couple this small pilot to an apparatus-adjacent tool with different schemas.

Rejected alternatives: copy Evidence Bundler modules wholesale, depend on Evidence Bundler as an installed package, or write a retrieval pipeline without referencing the existing portfolio pattern.

Consequences: Code stays small and local for Slice 1. If shared retrieval code becomes useful later, that should be recorded as a new decision before extraction.

## ADR-007: Citation resolution before answer generation

Status: accepted

Decision: The next trust-layer slice validates citation resolution before any LLM answer generation. Answer fixtures use a structured JSON shape with `answer_text`, `citations`, and `expected_outcome`. The validator treats the `citations` array as the source of truth. Inline markers in `answer_text` are allowed as reader-facing text, but they do not drive validation.

The metric name is `citation_resolves_to_retrieved_chunk`. It means only that every cited `chunk_id` resolves to a chunk in the retrieved result set. It does not mean the cited chunk semantically supports the answer.

Stale-document exclusion remains retriever-side by default. The validator still hard-fails any retrieved result or cited retrieved chunk whose status is not `Approved` or `Effective`, because that would mean the retrieval boundary leaked.

Rejected alternatives: validating free-text inline citations, adding LLM answer generation first, naming the metric `citation_validity`, or treating citation resolution as semantic support.

Consequences: Unit tests must cover valid citations, missing citations, hallucinated chunk IDs, stale retrieved chunks, refusal answers with citations, and CLI failure output. Verification for this slice is `ruff check .`, `python -m pytest`, `python -m compileall src`, a CLI smoke for citation validation, and the root workspace audit after status or planning docs change.

## ADR-008: Starter evaluation suite before expanding fixtures

Status: accepted

Decision: The first evaluation harness uses an 8-case synthetic suite before expanding to the planned 20-30 golden questions. Cases can encode expected bad outcomes, such as missing citations or hallucinated chunk IDs, so the suite passes only when the harness catches those traps.

The evaluation report includes `citation_resolves_to_retrieved_chunk_rate`, but the report states that this is structural resolution only. It does not measure semantic support.

Rejected alternatives: authoring 20-30 fixtures before the schema settles, treating every bad citation fixture as a suite failure, adding LLM answer generation in the same slice, or reporting citation resolution as grounding.

Consequences: `biotech-rag evaluate` writes JSON and Markdown reports from a fixed suite. The next expansion should add more questions only after this report shape is useful in review. Verification for this slice is `ruff check .`, `python -m pytest`, `python -m compileall src`, a CLI smoke for evaluation report writing, and the root workspace audit after status or planning docs change.

## ADR-009: Trust-layer report and deterministic extractive answers

Status: accepted

Decision: The next proof slice keeps the public contract narrow. Outcome values remain exactly `answer` and `refusal`. The `biotech-rag answer` command assembles a deterministic extractive answer from retrieved chunks. If retrieval returns no hits, the answer uses the fixed refusal text and emits no citations. If retrieval returns hits, the answer copies each retrieved chunk text into the response, tags each block with `[source: N]`, and includes doc ID, version, section heading, and source span metadata.

Citation validation runs inside answer assembly. The command emits `query`, `outcome`, `answer_text`, `citations`, `retrieved_chunks`, and `citation_validation`, and it must not succeed if the generated citations do not resolve to retrieved chunks. The standalone `validate-citations` command stays available for deliberately bad fixtures.

The trust-layer report replaces the starter evaluation report shape. It writes Markdown and JSON with `trust_layer_status`, corpus/config metadata, metric fractions, a case table, and a limits section. The headline reviewer signal is `trust_layer_status: pass` with `case_pass_rate: 24/24`. Required gates are retrieval expectations, stale-document exclusion, refusal expectations, fixture citation expectations, generated answer outcome, and generated answer citation validation.

Rejected alternatives: adding `supported` or `partial` outcomes, generating prose with an LLM, selecting sentences by query-term overlap, treating citation validation as only a post-step, adding FastAPI before the answer contract, or promoting semantic retrieval on an optional real-model smoke.

Reasoning: The portfolio value is the traceable trust layer, not fluent answer prose. A deterministic extractive answer exercises the end-to-end citation contract without model flakiness or unsupported synthesis. Keeping citation validation inside answer assembly also prevents later transports, such as FastAPI or n8n, from bypassing the boundary.

Consequences: `retrieve`, `evaluate`, and `answer` share `RetrievalConfig` and the same retrieval path. Semantic or hybrid retrieval remains a later comparison slice and can only be promoted with a committed BM25-vs-hybrid comparison report that keeps stale-document exclusion, refusal behavior, and citation checks green. Verification for this slice is `ruff check .`, `python -m pytest`, `python -m compileall src`, CLI smokes for `validate-corpus`, `retrieve`, `answer`, `validate-citations`, and `evaluate`, and the root workspace audit after planning or status docs change.

## ADR-010: FastAPI pure-transport layer and review-routing mini-spec

Status: accepted

Decision: The next slice exposes the existing CLI core over HTTP without changing any core logic. The transport layer calls the same functions the CLI calls (`load_corpus`, `run_retrieval`, `build_extractive_answer`, `validate_answer_citations`, `run_evaluation_suite`) and serializes the same `to_cli_record()` output, so API JSON equals CLI `--json` for the same input. "Pure transport" is enforced by parity tests, not assertion: `tests/test_api.py` compares parsed API JSON against parsed CLI JSON for `/retrieve`, `/validate-citations`, and `/evaluate`, and compares `/answer` minus its advisory `review_recommendation` key against the CLI `answer` record.

Corpora are server-bound at startup from a configured allowlist. Each request selects a bundle by name; no request body ever supplies a filesystem path. Invalid bundles fail the server closed at startup via the existing `load_corpus`. The service binds to `127.0.0.1` by default, with optional `X-API-Key` authentication enforced on every route except `/health`, request bodies validated by Pydantic (malformed input is 422), and CORS closed by default.

The surface is six routes: `GET /health`, `POST /validate-corpus`, `POST /retrieve`, `POST /answer`, `POST /validate-citations`, and `POST /evaluate`. The file-path arguments the CLI takes become inline JSON payloads. `/validate-corpus` builds its response dict explicitly because `IngestReport` has no `to_cli_record()` and `valid` is a property; it returns 200 even when `valid` is false, mirroring the CLI (which reports, then exits nonzero). `/evaluate` passes the server-bound corpus path into the existing `run_evaluation_suite`, with no core refactor and no server-side report file writes. An unknown corpus name is 404.

Every non-health request gets a uuid4 `request_id`, returned as the `X-Request-ID` header and written to one structured audit record (timestamp, request id, route, method, corpus, query, result summary, status code) via Python logging and, when `BIOTECH_RAG_AUDIT_LOG` is set, an append-only JSONL file.

Review-routing mini-spec: `/answer` returns an advisory `review_recommendation` sibling to the answer record. It does not change the answer contract — outcomes stay exactly `answer` and `refusal` (ADR-009), and the signal carries no semantic-support assessment, which remains deferred. Triggers are mechanical. Two are implemented now: `refusal_no_supporting_documents` (the answer is a refusal) and `low_top_score` (`top_score <= score_floor + low_score_margin`, margin from `BIOTECH_RAG_LOW_SCORE_MARGIN`, default `0.0`, so by default it fires only at the floor and operators tune it per corpus). Two are specified for later: `ambiguous_top_results` (near-tied top scores across different `doc_id`s) and `citation_validation_failed` (defensive; extractive answers should not reach it).

Configuration is environment-driven: `BIOTECH_RAG_CORPORA` (comma-separated `name=path` allowlist, default `synthetic=examples/synthetic-controlled-docs`), `BIOTECH_RAG_DEFAULT_CORPUS`, `BIOTECH_RAG_API_KEY`, `BIOTECH_RAG_AUDIT_LOG`, `BIOTECH_RAG_HOST`, `BIOTECH_RAG_PORT`, and `BIOTECH_RAG_LOW_SCORE_MARGIN`. Registry paths are the only filesystem locations the service reads corpora from; they resolve relative to the asset root and are validated at startup. The full contract and mini-spec live in `docs/api-transport.md`.

Rejected alternatives: accepting a corpus path in request bodies, refactoring core functions to accept pre-loaded documents for `/evaluate` in this slice, adding a review `outcome` value or semantic-support scoring, opening CORS or binding to all interfaces by default, writing evaluation reports server-side, building n8n workflows before the API shape and review-routing spec are pinned, or hand-checking responses instead of parity tests.

Reasoning: The portfolio value is a trust boundary that survives transport. Because citation validation already runs inside `build_extractive_answer` and the status gate runs inside retrieval, an HTTP layer that only serializes the same core records cannot bypass either boundary. Pinning the API shape and the review-routing mini-spec is exactly what the plan doc names as the precondition for n8n, so this slice unblocks orchestration without coupling the evidence boundary to a visual workflow.

Consequences: `uvicorn biotech_rag_assistant.api:app` and `biotech-rag serve` both run the same app from environment config. n8n is unblocked and is the next slice. Verification for this slice is `ruff check .`, `python -m pytest` (the existing suite plus `tests/test_api.py` parity, trust-boundary, security, review-routing, and audit cases), `python -m compileall src`, the ADR-009 CLI smokes, a live-server smoke (`biotech-rag serve` or `uvicorn biotech_rag_assistant.api:app`) exercising `/health`, `/retrieve`, `/answer` green and refusal paths, and `/validate-citations` with a citation trap while confirming the `X-Request-ID` header and one audit record per request, and the root workspace audit after planning or status docs change.

## ADR-011: Client-corpus onboarding as pre-ingest adoption layer

Status: accepted

Decision: The client-corpus onboarding slice runs before the existing corpus loader. It maps a synthetic messy client bundle into the current clean `DocumentMetadata` sidecar contract, writes a deterministic coverage report, and emits only `mapped_cleanly` and complete `excluded` records into a normalized corpus. `needs_review` and `rejected` records do not get clean sidecars and cannot enter retrieval.

The onboarding states are exactly `mapped_cleanly`, `excluded`, `needs_review`, and `rejected`. The fixture exercises all four states. Reports are deterministic: records are sorted by `source_path`, JSON keys are sorted when written, and there is no wall-clock field.

Rejected alternatives: relaxing `DocumentMetadata` to accept messy fields, adding a second retrieval path for partially mapped documents, guessing current status from the highest-looking version, adding a FastAPI onboarding route that accepts source paths, adding n8n orchestration, or using an LLM to infer metadata.

Reasoning: The existing retrieval trust boundary already works: `validate_corpus` checks sidecars and source hashes, and chunking indexes only `Approved` and `Effective` documents. The realistic client problem is earlier than retrieval. The system needs to show which documents can be mapped into that boundary and which need review before candidate passages are nominated.

Consequences: `biotech-rag onboard-corpus` is CLI-only in this slice. The generated normalized corpus must pass `validate-corpus` before retrieval, answer assembly, evaluation, or the FastAPI transport uses it. The slice stays synthetic-only and does not claim to validate a GxP system, certify compliance, or replace QA, validation, regulatory, legal, or document-control review.

## ADR-012: Lexical relevance gate for refusal

Status: accepted

Decision: Retrieval applies a lexical relevance gate before an answer is permitted. `RetrievalConfig.min_top_coverage` (default `0.6`) requires the top-ranked chunk to contain at least that fraction of the query's distinctive (non-stopword) terms; otherwise retrieval returns no hits and the answer is a refusal. The gate is policy applied through `RetrievalConfig`: the low-level `BM25Retriever.query` leaves it off by default (`min_top_coverage=0.0`) so the BM25 baseline stays pure and inspectable. Coverage is gated on rank 1 only, which keeps the decision independent of `top_k`.

Reasoning: BM25 returns a positive score for any non-trivial token overlap, and the previous `score_floor=0.0` only dropped scores `<= 0`. Empirically, off-topic natural-language questions ("vacation policy", "reset my password", "documentation procedure for shipping") shared enough incidental tokens to surface a loosely related Approved passage, which the deterministic extractive answer then copied verbatim with structurally valid citations. For a product whose central promise is refusal on unsupported questions, that is the gap between the claim and the behavior. Tuning data: every one of the 24 trust-suite answer cases has rank-1 coverage >= 0.78, while every off-topic probe measured <= 0.40, so a 0.6 threshold sits in a clean gap and keeps the trust suite at 24/24.

The gate is deliberately refusal-biased. Lexical coverage cannot separate an on-topic paraphrase from an off-topic question when both differ lexically from the source (a genuinely on-topic question phrased with document-level framing rather than the answer section's terms can fall to ~0.40, the same band as off-topic input). The gate therefore sometimes refuses a real question. That is the safe failure direction for a regulated-document assistant: refusing a supported question is recoverable; confidently answering an unsupported one is not. Robust paraphrase handling is the job of semantic/hybrid retrieval, which stays deferred (ADR-002, ADR-009) until a committed comparison report shows it beats this baseline while keeping stale-document exclusion, refusal, and citation checks green.

Rejected alternatives: an absolute BM25 `score_floor` (raw scores do not separate — a real paraphrase scored 4.13 while an off-topic query scored 4.41); IDF-weighted coverage (out-of-vocabulary query terms like "shipping" are absent from the BM25 idf table and get ignored rather than penalized, which inverts the signal); gating on the best of the top-k chunks (leaks as `top_k` grows); baking the gate into `BM25Retriever` (keeps the baseline impure and untestable); lowering the threshold to admit more paraphrases (re-admits the off-topic over-answers in the ~0.40 band).

Consequences: A new `examples/synthetic-controlled-docs/evaluation/natural-language-queries.json` suite exercises realistic conversational queries (on-topic answer, off-topic refusal), kept separate from the keyword-shaped trap suite. `tests/test_retrieval.py` covers the gate as policy-not-baked-in, off-topic refusal, and on-topic pass; `tests/test_evaluation.py` asserts the natural-language suite. The 24-case trust suite stays 24/24. The headline `24/24` remains a trust-control result, not a retrieval-quality result; the natural-language suite is the realistic-query signal.

## ADR-013: One retrievable version per doc_id

Status: accepted

Decision: `validate_corpus` fails closed when more than one retrievable (`Approved`/`Effective`) document shares a `doc_id`. The corpus does not load; the issue names the `doc_id` and the conflicting versions.

Reasoning: The product's primary use case is "show me the current approved version". The status gate (ADR-005) excludes Draft/Obsolete/Superseded, but nothing previously enforced a single current version, so two Approved versions of the same SOP would both validate and both retrieve, making "current" ambiguous. A fail-closed system must not leave the current-version invariant to corpus-authoring discipline. The onboarding layer (ADR-011) already flags `duplicate_current_version` upstream; this is the same invariant enforced defensively at the clean-corpus boundary the retrieval path actually depends on.

Rejected alternatives: silently keeping the highest version, down-ranking older versions instead of failing, warning without failing, or enforcing the invariant only at onboarding (which the direct corpus path bypasses).

Consequences: A `doc_id` may carry many versions in the corpus, but at most one may be `Approved`/`Effective`; predecessors must be `Superseded`/`Obsolete`. `tests/test_corpus.py` covers both the duplicate-current failure and the normal one-current-plus-superseded case. The existing synthetic corpus is unaffected (no duplicate retrievable doc_ids).

## ADR-014: Semantic-vs-BM25 comparison complete; semantic is the next retrieval slice

Status: accepted

Decision: The BM25-vs-hybrid comparison that ADR-009 and ADR-012 require before promoting semantic retrieval has been run (`experiments/semantic_vs_bm25.py`, report `experiments/comparison-report.md`, 2026-06-13). The chosen next retrieval slice is **semantic (bi-encoder, `all-MiniLM-L6-v2`) retrieval with a cosine refusal threshold** — not hybrid. It is not yet promoted into the package; this records the evidence and the direction.

Evidence (synthetic corpus, 16 labeled on-topic + 6 off-topic queries; directional, not a production validation): on easy corpus-vocabulary queries all three methods tie. On hard paraphrases, BM25 recall@1=0.38 / MRR=0.49 while semantic recall@1=1.00 / MRR=1.00; hybrid (RRF) was in between and diluted semantic's rank-1. Semantic cosine admits a clean refusal threshold (~0.30: max off-topic top 0.244 < min on-topic top 0.350); raw BM25 score does not separate (which is why ADR-012 gates on term coverage), and RRF scores do not either. The ADR-012 coverage gate refuses 6/6 off-topic but wrongly refuses 9/16 on-topic — quantifying its deliberate refusal-bias.

Rejected alternatives: hybrid/RRF (no ranking or thresholding benefit here, added complexity); promoting semantic now without a larger-corpus threshold validation (the on/off cosine gap is real but narrow and the paraphrases were hand-written); adding the embedding stack to the package dependencies before promotion (the experiment lives in `experiments/` with its own requirements so the package stays lean).

Consequences: When promoted, semantic retrieval replaces the coverage gate's refusal-bias while every deterministic trust control (status gating ADR-005, citation validation ADR-007/009, audit ADR-010, current-version invariant ADR-013) stays unchanged around it, and the retrieval-method contract gains `semantic` alongside `bm25` (ADR-009 reserved `method` for this). Promotion is gated on: validating the cosine threshold on a larger and ideally real corpus, and keeping stale-document exclusion, refusal, and citation checks green. The experiment harness is reproducible and re-runnable as the corpus grows.

## ADR-015: Vendor Evidence Bundler and Claim Audit Lab via git submodules

Status: accepted (direction; not yet wired)

Decision: When the generative phase needs them, this asset will vendor `evidence-bundler` (EB) and `claim-audit-lab` (CAL) as git submodules under `workbench/components/`, per the workspace shared-component policy (root ADR-022): pinned to release tags, kept current by Dependabot bump-PRs, with the canonical source remaining each component's own GitHub repo. This **supersedes the by-reference-only stance of ADR-001 and ADR-006 for the integration phase** — those kept Slice 1 standalone deliberately; this records the deliberate reversal now that reuse is concrete, exactly as ADR-006 anticipated ("if shared retrieval code becomes useful later, record it as a new decision before extraction").

Integration points (the *why*, mirroring how `scaffold-claims-study` composes them): EB → the client-corpus onboarding/ingest layer (deterministic ingest into chunk records, provenance, review sidecars, coverage reports), extending the slice already built under ADR-011; CAL → the answer-grounding auditor for the deferred controlled-generation phase (the semantic support / overstatement / missing-source check that is the successor to today's structural citation resolution, ADR-007/009).

Gates before wiring (all three): (1) this asset is pushed to a GitHub repo (submodules + Dependabot need a remote); (2) EB and CAL are stable and tagged (they are being actively revised — pin to a tag, never a moving `main`); (3) there is real integration code that consumes them (do not add dormant submodules). Until then this is a recorded direction plus a ready plan (`plans/eb-cal-integration-and-sync.md`).

Rejected alternatives: copying EB/CAL source into `src/` (drift, no provenance); a package dependency (heavier release process; the local controlled-document models still differ from EB/CAL schemas, the original ADR-006 reason); adding the submodules now while EB/CAL are mid-revision and this repo has no remote (dormant, premature, and risks pinning to a broken state).

Consequences: No code changes yet. The contract boundary is unchanged: EB/CAL would sit at the ingest and answer-grounding edges; the deterministic trust controls (status gating, citation validation, refusal, current-version invariant, audit) remain this asset's own. When wired, `pyproject` and CI gain a submodule-aware checkout, and a `.github/dependabot.yml` (`gitsubmodule`) lands per ADR-022.

## ADR-016: Chunk text is the verbatim cited span; the heading is folded in only at index time

Status: accepted

Decision: `DocumentChunk.text` is the exact source span the citation points at — byte-for-byte `raw_text[char_start:char_end]` — rather than `section_heading + "\n" + body`. The section heading stays available as the `section_heading` field and is recombined only at index/scoring time via `retrieval.index_text(chunk)` (`f"{section_heading}\n{text}"`), which is what BM25 tokenizes and what the ADR-012 coverage gate measures.

Reasoning: For a provenance-first product the cited offsets are the audit anchor — an auditor slices the source at `char_start:char_end` and expects the quoted passage back. Previously `text` prepended the section heading while the offsets covered only the body, so `text != raw_text[char_start:char_end]`: the quote disagreed with its own citation (demonstrated on `CAL-ENG-005_v1_0_chunk_001`, where `text` led with "Daily check" but the cited span began "The analyst verifies…"). Folding the heading in only at index time keeps heading terms matchable — the indexed string is byte-identical to the old `text`, so BM25 ranking, the 24/24 trust suite, the 13/13 natural-language suite, and the 0.6 coverage calibration are all unchanged — while making the stored, displayed, and quoted text equal the cited span.

Rejected alternatives: extending the offsets to cover the heading line (the raw heading line carries Markdown `#` markers and inter-line blanks, so `text` still would not equal the span); dropping the heading from indexing entirely (loses heading terms, shifts ranking and the coverage threshold); leaving it as "cosmetic" (it was the one place the provenance claim and the behavior disagreed).

Consequences: `chunk.text` in CLI/API JSON and the static demo's `corpus-data.json` is now body-only; `docs/retrieval.js` mirrors `index_text` (heading + "\n" + text) so the JS==Python pages parity stays 40/40; `tests/test_chunking.py` pins `text == raw_text[char_start:char_end]` for every chunk. The answer block already prints the section heading in its citation header, so reader-facing output is unchanged in substance and cleaner in form.

## ADR-017: Onboarding refuses to overwrite a non-empty output directory by default

Status: accepted

Decision: `onboard-corpus` (and `onboard_corpus(..., force=False)`) refuses to write into an output directory that already exists and is non-empty, raising before deleting anything. Overwriting requires an explicit `force=True` / `--force`. An empty existing directory is still written into, since nothing is destroyed.

Reasoning: The previous behavior unconditionally `shutil.rmtree`'d the output directory before writing. For a tool whose whole premise is careful handling of client documents, clobber-by-default is the wrong failure direction — a mistyped `--output` would silently destroy existing data. Fail-closed (refuse, keep the data, require an explicit override) matches the rest of the asset's posture (ADR-005, ADR-013).

Rejected alternatives: keep clobbering silently (the footgun); prompt interactively (breaks non-interactive and orchestrated use); write into the existing directory without clearing it (mixes stale and fresh sidecars, which the current-version and hash gates would then have to disentangle).

Consequences: `tests/test_onboarding.py` covers refuse-without-force and overwrite-with-force; the shared `build/onboarded-synthetic-corpus` test and CLI paths pass `force=True` because they intentionally regenerate. No change to the report shape or the onboarding states.
