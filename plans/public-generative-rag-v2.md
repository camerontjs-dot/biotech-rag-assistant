# Public Generative RAG v2 — research-backed implementation plan

**Status:** planning / research artifact, not product authorization  
**Research snapshot:** 2026-09-25  
**Base when written:** `main@40de3cdcd98973b0e3a1c91d6ac114bc62857c04`  
**Scope:** public synthetic biotech / pharma controlled-document demonstration  
**Existing authority:** `DECISIONS.md` ADR-001 through ADR-017, especially ADR-005, ADR-007, ADR-009, ADR-013, ADR-014, ADR-015, and ADR-016.

## Objective

Upgrade Biotech RAG Assistant from a deterministic trust-layer demonstration into a public generative RAG assistant without weakening the controls that currently make the project interesting.

The target is not "a chatbot with citations." The target is a bounded generative system in which:

1. document-control policy decides what may enter retrieval;
2. retrieval nominates evidence but does not decide truth;
3. a typed evidence packet defines the only evidence generation may use;
4. a language model proposes reader-facing synthesis;
5. deterministic and semantic checks determine whether that synthesis may be shown;
6. insufficient or failed evidence produces fallback or refusal rather than ungrounded completion;
7. every material stage remains inspectable and attributable to a versioned configuration.

The public demo remains explicitly **not a validated GxP system**, does not make regulated decisions, and uses synthetic data only.

## Why this plan now

The repository already built the difficult preconditions that many RAG demonstrations skip:

- fail-closed status gating;
- one-retrievable-version-per-document identity;
- source hashes and exact-span provenance;
- stable chunk IDs;
- deterministic BM25 baseline;
- refusal behavior;
- structural citation validation;
- trust-layer evaluation;
- API / CLI parity;
- request auditing;
- a static public demo with stale-document traps.

ADR-014 already records a small semantic-vs-BM25 experiment in which semantic retrieval substantially improved hard paraphrase retrieval and produced a cleaner observed refusal separation than the lexical gate. ADR-015 already reserves Evidence Bundler (EB) for ingest/provenance reuse and Claim Audit Lab (CAL) for a later semantic answer-grounding seam.

The new work should therefore extend those boundaries rather than replace them.

---

# 1. Research synthesis

This section separates **observed external practice** from our interpretation.

## 1.1 Enterprise RAG is converging on multi-stage retrieval, but the exact stack is workload-specific

### Observed

Major enterprise search platforms now expose combinations of:

- lexical + vector retrieval;
- metadata filtering;
- secondary semantic reranking;
- score thresholds;
- query decomposition / multi-query retrieval;
- citations and retrieval execution metadata.

Azure AI Search presents hybrid BM25 + vector retrieval with reciprocal-rank fusion and semantic reranking as a standard RAG pattern, and now offers agentic retrieval that decomposes complex questions into focused subqueries. Amazon Bedrock Knowledge Bases exposes semantic or hybrid search, metadata filters, reranking, citations, and agentic retrieval in managed configurations. OpenAI file search exposes hybrid semantic/text weighting, ranking options, and score thresholds.

### Inference for this project

These capabilities are **controls to compare**, not requirements to copy.

Our own ADR-014 experiment found semantic-only retrieval outperforming BM25 and RRF hybrid on the current synthetic corpus. Therefore:

- preserve BM25 as the deterministic control;
- qualify semantic retrieval on a larger frozen benchmark;
- include hybrid and reranking as challenger arms;
- promote only the smallest stack that actually improves the biotech benchmark.

Do not replace local evidence with vendor defaults.

## 1.2 Controlled-document and life-sciences systems emphasize permissions, auditability, human control, and bounded action

### Observed

Current life-sciences product patterns include:

- Veeva Vault AI queries only data the user has permission to access and its AI tab is read-oriented rather than an unrestricted action surface.
- MasterControl states that AI features are user-invoked, operate within existing permissions, remain subject to auditability, and do not independently take actions or make decisions inside validated workflows. It also describes version/change control for model, prompt, retrieval, policy, and infrastructure changes.
- Benchling AI emphasizes structured scientific context, tenant-admin capability controls, and provider/data governance rather than treating an LLM as a detached chat interface.
- MasterControl's SOP Analyzer explicitly uses RAG to compare SOPs with regulatory requirements.

### Inference for this project

The public demo should remain:

- query / synthesis oriented;
- non-authoritative;
- non-action-taking;
- explicit about source status and version;
- auditable;
- provider-neutral.

For future private pilots, authorization must be applied **before retrieval**, not merely hidden in the UI.

## 1.3 Life-sciences RAG failures occur at multiple layers, not just "hallucination"

### Observed

FDA researchers evaluating a RAG application over FDA guidance documents reported separate failure classes including:

- wrong document retrieved;
- wrong section retrieved;
- document text-extraction errors, including tables;
- poor/confusing generated wording;
- hallucination.

The system cited the correct source document more often than it produced a fully correct and complete answer, showing that citation existence alone is not enough.

A 2026 healthcare RAG/GraphRAG evaluation scoping review similarly found limited adoption of independent retrieval-layer evaluation, fine-grained evidence verification, formal safety evaluation, and safeguards around LLM-as-judge methods.

### Inference for this project

The evaluator must diagnose at least:

`ingest -> retrieval -> evidence admission -> generation -> attribution -> semantic support -> policy`

Do not collapse these into one "answer accuracy" score.

## 1.4 Document structure and extraction quality are first-class RAG problems

### Observed

Samsung Biologics publicly described an SOP Q&A RAG project where tables and images required separate preprocessing because naive passage chunking made complex SOP structures noisy. FDA's own guidance-document study also observed text-extraction errors from PDF tables.

Recent biomedical RAG studies continue to compare corpus structure and retrieval strategy rather than assuming raw fixed-size chunks are sufficient.

### Inference for this project

The current exact-span paragraph chunking remains an excellent provenance baseline, but a realistic v2 benchmark should include:

- headings and nested sections;
- tables;
- lists;
- structured procedural steps;
- references / cross-links;
- version history traps.

Structure-aware parsing should be tested before fine-tuning an embedder.

## 1.5 Fine-grained attribution is becoming more important than document-level citation

### Observed

Recent RAG research increasingly evaluates sentence- or claim-level attribution, citation precision/recall, and support rather than merely whether a cited document exists. Work such as ReClaim and OpenScholar shows the usefulness of attaching citations to specific generated statements and verifying whether cited passages actually support them.

### Inference for this project

The generator should not emit an opaque paragraph plus a bibliography. It should emit structured **claims with evidence IDs**. Rendering into prose happens after schema validation.

Existing `citation_resolves_to_retrieved_chunk` remains a structural gate, but must not be renamed or treated as semantic support.

## 1.6 Retrieved content is an untrusted-input security boundary

### Observed

Current OWASP and Microsoft guidance treats RAG corpora, retrieved chunks, tool output, and memory as untrusted input. Risks include:

- indirect prompt injection embedded in documents;
- poisoning of the retrieval corpus;
- vector/embedding manipulation;
- unauthorized retrieval;
- context flooding;
- cross-context information leakage.

The recommended posture is defense in depth: provenance, authorization, instruction/data separation, bounded context, sanitization/detection, monitoring, and deterministic impact controls.

### Inference for this project

Prompt injection belongs in the trust suite before a generative public endpoint is promoted.

The most important deterministic defense for this demo is architectural: generated text has no tools, no filesystem authority, no retrieval authority, and no ability to alter source state.

## 1.7 Regulatory direction supports context-of-use and lifecycle thinking

### Observed

FDA's January 2025 draft guidance for AI supporting drug/biologic regulatory decisions uses a risk-based credibility framework tied to a defined context of use. In January 2026 FDA and EMA published ten good-AI-practice principles emphasizing human-centric design, risk, context of use, data governance/documentation, performance assessment, lifecycle management, and clear information.

This public demo is outside that guidance's regulated-decision scope, but the design principles are still useful.

### Inference for this project

Every evaluated candidate should bind:

- intended use;
- model/provider;
- model version;
- prompt version;
- retrieval config;
- corpus/index identity;
- evidence packet identity;
- evaluator version;
- limits.

That is a portfolio-strength analogue of controlled lifecycle evidence without falsely claiming validation.

---

# 2. Current strengths and missing capabilities

## Already strong

The current project is ahead of many generic RAG demos on:

- controlled-document lifecycle gating;
- stale / obsolete exclusion;
- current-version invariants;
- exact source-span provenance;
- deterministic IDs;
- refusal;
- citation resolution;
- corpus validation;
- retrieval/evaluation config sharing;
- API/CLI parity;
- audit records;
- synthetic-only public boundary.

These remain non-negotiable.

## Missing or insufficiently tested

### A. Retrieval generalization

ADR-014 is encouraging but too small to promote a semantic threshold as a durable policy.

### B. Structure-aware ingestion

The public corpus does not yet stress realistic SOP structures such as tables, multi-level sections, procedural lists, and cross-references.

### C. Typed evidence packet

There is no canonical object between retrieval and generation that freezes exactly what the model was allowed to see.

### D. Controlled generation

There is no provider-neutral generative interface, structured claim output, or deterministic fallback path.

### E. Claim-level semantic support

Current citation validation proves identity/resolution only.

### F. Prompt-injection / poisoning tests

The non-generative system has little exposure here; generation changes that threat model.

### G. Layer-specific evaluation

The current trust suite is strong for the deterministic baseline, but v2 needs diagnostic metrics for retrieval, extraction, generation, attribution, support, security, latency, and cost.

### H. Public backend boundary

The GitHub Pages demo is intentionally static. Semantic retrieval and server-side generation should not put model credentials or authoritative retrieval policy in browser JavaScript.

### I. Provider/model lifecycle records

Model and prompt identity need to become explicit audit fields before generation is promoted.

### J. Permission-aware retrieval contract

Not required for the all-public synthetic demo, but the core contract should leave a clean seam for a future private pilot rather than bolting authorization on afterward.

---

# 3. Epistemic commitments

These are project rules, not implementation suggestions.

1. **Retrieval is nomination, not truth.**
2. **Similarity is not support.**
3. **A citation resolving to a chunk is not evidence that the chunk supports the generated claim.**
4. **A model confidence score is not epistemic authority.**
5. **A generated answer is a proposal until it passes policy gates.**
6. **Unresolved evidence should remain unresolved.**
7. **Weak controls must be capable of failing the evaluator.**
8. **No training decision may use frozen TEST or PROSPECTIVE labels in the same lineage.**
9. **Industry defaults do not override local measurement.**
10. **The public demo must not imply validation, compliance certification, or autonomous quality decisions.**

---

# 4. Target architecture

```text
User question
    |
    v
Query normalization / policy
    |
    v
Controlled corpus gate
(status + current version + source hash + future ACL)
    |
    v
Candidate retrieval
(BM25 control / semantic candidate / challengers)
    |
    v
Optional bounded expansion
(section parent / adjacent procedural context)
    |
    v
Evidence admission policy
(dedup + diversity + threshold + limits)
    |
    v
EvidencePacket v1  <---- immutable identity / hash
    |
    +--------------------------+
    |                          |
    v                          v
Deterministic extractive       Generative synthesizer
answer (existing control)      (provider-neutral, no tools)
                               |
                               v
                         structured claims
                               |
                               v
                    structural citation gate
                               |
                               v
                    semantic support shadow
                    (later CAL adapter)
                               |
                               v
                       answer policy
                    /       |        \
              generated  extractive  refusal
                    |
                    v
            public response + trace
```

Generation never receives draft/obsolete chunks, arbitrary filesystem paths, hidden extra corpus state, or tool authority.

---

# 5. New contracts

## 5.1 RetrievalNomination

Minimum fields:

- `nomination_id`
- `query_id`
- `chunk_id`
- `doc_id`
- `version`
- `status`
- `source_hash`
- `char_start`
- `char_end`
- `section_heading`
- `retrieval_signal` (`bm25`, `semantic`, future challenger)
- `raw_score`
- `rank`
- `retrieval_config_id`
- `corpus_identity`
- optional `parent_context_id`
- optional `authorization_scope`

Scores remain method-specific and are not support/confidence values.

## 5.2 EvidencePacket v1

An immutable packet assembled after policy admission.

Minimum fields:

- packet schema version;
- query + stable query ID;
- corpus/index identity;
- retrieval config identity;
- admitted nominations;
- any added parent context with explicit provenance;
- excluded-candidate summary by mechanical reason;
- evidence budget;
- packet SHA-256 identity.

No generated content belongs in the packet.

## 5.3 GeneratedClaim

Minimum fields:

- `claim_id`
- `text`
- one or more cited `chunk_id` values;
- optional `qualifier`;
- optional `limitation`.

The generator returns schema-valid claims, not final Markdown.

## 5.4 GenerationRecord

Minimum fields:

- EvidencePacket ID;
- provider;
- model ID / version;
- prompt template ID / hash;
- generation parameters;
- raw structured model output hash;
- validated claims;
- structural citation result;
- semantic audit result when enabled;
- final policy disposition;
- latency;
- input/output token count where available;
- error/fallback path.

This is an audit record, not a chain-of-thought record.

---

# 6. Evaluation programme

Use Training Room discipline even before model training exists.

## 6.1 Freeze a v2 benchmark before promotion work

Target: at least **120 cases**, grouped to avoid near-duplicate leakage across splits.

Suggested composition:

- 25 straightforward controlled-document questions;
- 25 paraphrases with low lexical overlap;
- 15 multi-section / multi-document questions;
- 15 status/version/stale traps;
- 10 table or structured-procedure questions;
- 10 qualifier/exception/contradiction cases;
- 10 ambiguous or intentionally under-supported questions;
- 10 prompt-injection / poisoned-content security cases.

Suggested split:

- DEV: 40
- TEST: 60
- PROSPECTIVE: 20, revealed only after candidate/config freeze

Group by source document, semantic family, and mutation parent where needed. Do not random-split near duplicates.

## 6.2 Add weak controls

At minimum:

- existing BM25 + current lexical gate;
- BM25 without semantic augmentation;
- naive dense retrieval;
- naive generator given top-K without claim-level citation requirement;
- a deliberately weak lexical-overlap support checker.

If a weak system passes the same decisive gate as the candidate, disposition the evaluator as non-discriminating / inconclusive rather than celebrating the candidate.

## 6.3 Layer-specific metrics

### Ingest / extraction

- source-hash validity;
- span round-trip validity;
- table-cell / structured-field recovery where gold exists;
- status/version metadata fidelity.

### Retrieval

- relevant-document recall@K;
- relevant-chunk recall@K;
- MRR / nDCG where ordering matters;
- decisive evidence recall;
- qualifier/exception recall;
- duplicate burden;
- evidence-role diversity;
- stale/draft leak count;
- refusal separation.

### Evidence packet

- provenance completeness;
- packet determinism;
- admitted-evidence diversity;
- context budget;
- source coverage;
- packet reconstitution from stored identities.

### Generation

- material-claim completeness;
- unsupported material-claim rate;
- contradiction rate;
- unnecessary-claim rate;
- refusal correctness;
- limitation disclosure.

### Citation / attribution

Keep structural and semantic dimensions separate:

- citation resolves to admitted chunk;
- citation precision;
- citation recall;
- claim-support classification;
- multi-citation necessity where a claim is jointly supported.

### Security

- stale/unauthorized retrieval observed count;
- indirect prompt-injection success observed count;
- schema escape / malformed output rate;
- context-budget overflow handling;
- poisoned-document handling;
- cross-query state leakage.

A zero observed count is a test result, not a claim of absolute security.

### Operational

- p50 / p95 retrieval latency;
- p50 / p95 generation latency;
- tokens per answer;
- estimated cost per answer;
- fallback rate;
- provider error rate.

## 6.4 Human review and LLM judges

LLM-as-judge may be used as a research instrument, never as the sole decisive authority for the first promotion.

For promotion-relevant semantic support evaluation:

- freeze the rubric first;
- label a human-reviewed subset;
- measure judge agreement against humans;
- preserve disagreement;
- compare at least one alternate judge or deterministic control where practical.

---

# 7. Work slices and promotion gates

Each slice should land independently and leave the existing deterministic path working.

## Slice 0 — freeze Baseline V1

**Purpose:** establish an immutable before-state.

Actions:

- record current `main` commit/tree and current trust-suite output;
- regenerate static demo parity;
- store current benchmark/config identities;
- capture latency and public UX baseline.

Gate: no behavior change.

## Slice 1 — v2 benchmark and diagnostic evaluator

**Purpose:** make future claims falsifiable before changing retrieval.

Deliver:

- frozen DEV/TEST manifests;
- PROSPECTIVE envelope with hidden labels/expected behavior where practical;
- error taxonomy matching ingest/retrieval/generation/attribution/security layers;
- weak controls;
- Markdown + JSON reports.

Do **not** implement semantic retrieval in the same slice.

Gate: evaluator rejects at least one deliberately weak system for the intended reasons.

## Slice 2 — realistic structured corpus

**Purpose:** test the problem life-sciences RAG systems actually encounter.

Add synthetic controlled documents with:

- nested sections;
- numbered procedure steps;
- tables;
- lists;
- references;
- controlled-document lifecycle/version traps.

Compare current paragraph parser with one or more structure-aware candidates. Preserve exact-span provenance or introduce an equally inspectable structured-cell provenance contract.

Gate: extraction changes must improve the designated structure cases without breaking existing exact-span and status invariants.

## Slice 3 — semantic retrieval promotion experiment

**Purpose:** reproduce or falsify ADR-014 at larger scale.

Arms:

1. current BM25;
2. semantic-only;
3. BM25 + semantic hybrid/RRF;
4. optional reranker only if candidate recall is adequate but ordering is a measured failure.

Thresholds are tuned on DEV only, frozen, then evaluated on TEST and PROSPECTIVE.

Primary decision questions:

- Does semantic retrieval improve paraphrase recall?
- Can refusal behavior remain acceptably conservative?
- Does hybrid add unique recoveries or merely dilute semantic results?
- Is reranking fixing an actual final-K ordering problem?

Gate: no retrieval method is promoted unless stale/draft exclusion remains perfect in the frozen suite and the candidate wins on predeclared decision metrics without unacceptable regression.

## Slice 4 — typed nominations + EvidencePacket v1

**Purpose:** create the hard seam before generation.

Deliver:

- typed nomination records;
- packet builder;
- packet hashing;
- admission policy;
- deterministic dedup;
- context budget;
- optional parent/section expansion behind a flag;
- packet inspection surface.

Test parent expansion separately from retrieval ranking.

Gate: identical inputs/config produce the same packet identity.

## Slice 5 — provider-neutral generation in shadow

**Purpose:** add GenAI without changing the public answer authority.

Implement a small interface such as:

```python
class Generator(Protocol):
    def generate(self, packet: EvidencePacket) -> GeneratedAnswer: ...
```

Requirements:

- server-side only;
- no tools;
- no filesystem;
- no retriever access;
- no web access;
- receives only the EvidencePacket;
- structured output schema;
- low-temperature / bounded output;
- provider/model selected by configuration;
- model ID and prompt hash recorded;
- generation failure falls back safely.

Add `/synthesize` or equivalent as a shadow/internal route first. Do not replace `/answer`.

Gate: generator cannot cite a chunk outside the packet and cannot bypass refusal mechanically.

## Slice 6 — claim-level attribution and support shadow

**Purpose:** move beyond structural citation resolution.

Pipeline:

`GeneratedClaim -> cited span(s) -> semantic support proposal -> policy`

Start with a bounded evaluator or NLI-style instrument as shadow telemetry. CAL becomes the preferred long-term adapter only when its owning repository exposes a stable, tagged contract that fits this use.

Possible labels must remain explicit and bounded, for example:

- `supported`
- `partially_supported`
- `unsupported`
- `contradicted`
- `unresolved`

Do not convert a similarity score directly into these labels.

Gate: promotion requires human-calibrated evidence that the checker distinguishes supported from unsupported/overstated claims. Until then it remains advisory.

## Slice 7 — RAG security qualification

**Purpose:** treat retrieval content as hostile data before public generation.

Add synthetic attacks:

- "ignore previous instructions" inside an approved-looking source;
- hidden/Unicode instruction variants;
- prompt-shaped section headings;
- malicious metadata;
- long-context flooding;
- adversarial near-duplicate content;
- stale document attempting to override current procedure;
- malformed generated schema;
- user prompt asking the model to reveal hidden instructions/config.

Controls:

- strict instruction/data separation;
- bounded chunk count/token budget;
- retrieved-content labeling;
- server-side prompt templates;
- output schema validation;
- no tools/action authority;
- source provenance and status gates;
- logging of blocked/fallback paths.

Do not claim prompt injection is "solved." Qualify bounded attacks.

Gate: no tested attack may cause source-policy bypass, unauthorized evidence admission, tool/action execution, or unstructured output promotion.

## Slice 8 — public generative demo

Move the generative experience behind a server-side backend. Keep GitHub Pages or the website as presentation only.

Public UX should expose three layers:

### Answer

Concise generated synthesis, only if gates pass.

### Evidence

For each material claim:

- exact source passage;
- document ID/title;
- version;
- lifecycle status;
- section;
- chunk ID;
- source-span information.

### Trace / "Why this answer"

Human-readable, not chain of thought:

- retrieval method;
- evidence count;
- whether expansion occurred;
- model/provider identity at a friendly level;
- whether structural citation validation passed;
- whether semantic audit was active;
- known limits.

Keep the obsolete-document trap and make it stronger: visibly show the stale document under **Excluded by document control**, never as model context.

Operational controls:

- origin allowlist / CORS restriction;
- rate limiting;
- input length caps;
- request timeout;
- per-request model budget;
- provider key only on server;
- abuse logging;
- deterministic extractive fallback.

Gate: public route cannot expose credentials, filesystem paths, hidden prompts, or non-synthetic data.

## Slice 9 — agentic/query-decomposition experiment, only if needed

Industry is moving toward query planning and multi-query retrieval, but do not add it merely because managed platforms do.

Trigger this slice only if the frozen benchmark shows a persistent class of complex questions whose required evidence cannot be recovered by the simpler pipeline.

Compare:

- original query;
- deterministic decomposition if feasible;
- LLM query decomposition;
- multi-query retrieval + merge.

Evaluate retrieval gain, cost, latency, duplicated evidence, and new failure modes.

Gate: no agentic retrieval in the public baseline unless it produces a clear measured improvement on a named failure class.

## Slice 10 — EB / CAL integration

Respect existing ADR-015 and `plans/eb-cal-integration-and-sync.md`.

- EB integration belongs at ingest/provenance boundaries only when a stable tagged release and real adapter exist.
- CAL integration belongs at semantic answer-audit boundaries only when a stable tagged contract exists.
- Do not vendor dormant submodules.
- Do not let either component silently replace this project's controlled-document policy.

---

# 8. Public demo UX

The demo should teach the architecture rather than merely imitate ChatGPT.

Suggested answer card:

```text
Answer
------
Generated synthesis...

Evidence status: 3 approved/effective passages
Grounding: structural citations passed
Semantic support audit: advisory / passed / not enabled
Model: <provider-neutral display label>

[Show evidence] [Show excluded sources] [Show trace]
```

Evidence drawer:

- claim-by-claim mapping;
- exact quoted source span;
- source metadata;
- status/version badges;
- "why excluded" entries for stale/draft traps.

Failure states should be first-class UX:

- "I found related material, but not enough approved evidence to answer."
- "The evidence supports only part of this question."
- "Generation failed validation; showing the retrieved source passages instead."

Never disguise fallback as successful synthesis.

---

# 9. Model/provider policy

Generation should be replaceable.

Selection criteria:

- structured-output reliability;
- grounded-answer quality on frozen benchmark;
- latency;
- cost;
- privacy/data-use terms;
- reproducibility/version pinning;
- availability.

Do not make "largest model" synonymous with "best."

A provider change is a candidate change. Re-run the generation/evidence suite before promotion.

For public synthetic data, a hosted model is acceptable if no secrets are exposed. Future private/client data requires a separate deployment/data-governance decision.

---

# 10. Model and system lifecycle record

Each public release should record:

- repository commit/tree;
- corpus manifest hash;
- index identity;
- embedding model/version;
- retrieval config ID;
- generator provider/model;
- prompt template hash;
- semantic-auditor identity/version;
- evaluation dataset version;
- decisive report identity;
- known limitations.

Any material change to retrieval, prompt, model, corpus parsing, policy, or evaluator must create a new candidate identity and rerun the relevant gates.

---

# 11. Decisions to record as ADRs when implementation starts

Do not silently convert this plan into accepted architecture.

Proposed ADR sequence:

1. **ADR-018 — v2 evaluation and promotion policy**
2. **ADR-019 — structure-aware controlled-document representation**
3. **ADR-020 — promoted retrieval method after frozen comparison**
4. **ADR-021 — EvidencePacket v1 authority boundary**
5. **ADR-022 — bounded generative synthesis contract**
6. **ADR-023 — claim-level semantic audit semantics**
7. **ADR-024 — RAG prompt-injection / untrusted-context boundary**
8. **ADR-025 — public backend deployment and fallback policy**

Numbers are provisional if the repository gains ADRs first.

---

# 12. What not to build yet

Explicitly deferred unless a measured failure activates them:

- custom biotech embedding fine-tuning;
- custom reranker training;
- GraphRAG / knowledge graph as the primary retriever;
- autonomous quality agents;
- workflow writes;
- model-generated document lifecycle/status;
- free-form agent tool use;
- live web search mixed into controlled-document answers;
- patient/clinical decision support;
- real client or employer documents;
- a single scalar "trust score."

MindGraph graph-admission ideas may become relevant for document relationships such as "supersedes," "references," or "related procedure," but graph retrieval should be a separate falsifiable experiment after simpler retrieval is qualified.

---

# 13. Stop conditions

Stop or narrow the programme if any of these are observed:

- semantic retrieval gains disappear on frozen/prospective data;
- the refusal threshold requires unacceptable unsupported-answer risk;
- structure-aware parsing breaks provenance without compensating measurable gain;
- a reranker improves headline ranking while losing qualifier/exception evidence;
- a semantic auditor cannot outperform a weak control on human-reviewed support cases;
- LLM judge agreement with human reviewers is too weak for the proposed use;
- generation adds little user value beyond extractive answers;
- public latency/cost makes the experience impractical;
- security qualification exposes a source-policy bypass that cannot be deterministically contained.

A negative result is a successful experiment if it removes unnecessary architecture.

---

# 14. First execution wave

The first implementation wave after this planning PR should be **evaluation-first**:

1. open a successor research/implementation issue for the v2 benchmark;
2. freeze case taxonomy and split policy before candidate retrieval work;
3. build the first 120-case synthetic benchmark and weak controls;
4. reproduce Baseline V1;
5. run BM25 / semantic / hybrid comparison;
6. classify failures;
7. only then authorize the next behavioral slice.

Do not start generation in the same branch as the retrieval promotion experiment.

---

# 15. External research references

Primary / regulatory:

- FDA, *Considerations for the Use of Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological Products* (draft, Jan 2025): https://www.fda.gov/regulatory-information/search-fda-guidance-documents/considerations-use-artificial-intelligence-support-regulatory-decision-making-drug-and-biological
- FDA + EMA, *Guiding Principles of Good AI Practice in Drug Development* (Jan 2026): https://www.fda.gov/about-fda/artificial-intelligence-drug-development/guiding-principles-good-ai-practice-drug-development
- FDA researchers, *Semantic Search of FDA Guidance Documents Using Generative AI* (2025): https://pubmed.ncbi.nlm.nih.gov/40517195/
- NIST, *AI RMF: Generative AI Profile*: https://www.nist.gov/itl/ai-risk-management-framework

Enterprise retrieval / security:

- Azure AI Search, RAG overview: https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview
- Azure AI Search, hybrid retrieval: https://learn.microsoft.com/azure/search/hybrid-search-overview
- Azure AI Search, agentic retrieval: https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview
- Amazon Bedrock Knowledge Bases: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- Amazon Bedrock reranking: https://docs.aws.amazon.com/bedrock/latest/userguide/rerank.html
- OWASP RAG Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
- Microsoft, input/context/retrieval hygiene: https://learn.microsoft.com/en-us/security/zero-trust/catalog-ai-defense-capabilities/input-context-retrieval-hygiene

Life-sciences product / implementation patterns:

- Veeva Vault AI: https://clinical.veevavault.help/en/lr/1187184/
- MasterControl AI Trust Center: https://www.mastercontrol.com/ai-trust-center/
- MasterControl SOP Analyzer: https://www.mastercontrol.com/news/mastercontrol-launches-ai-powered-sop-analyzer/
- Benchling AI: https://www.benchling.com/ai
- Samsung Biologics SOP Q&A case study: https://www.samsungsds.com/us/blog/samsung-biologics-case-with-brity-automation.html

Biomedical / RAG evaluation research:

- Liu et al., 2025 systematic review/meta-analysis of biomedical RAG: https://pubmed.ncbi.nlm.nih.gov/39812777/
- 2026 healthcare RAG/GraphRAG evaluation scoping review: https://pubmed.ncbi.nlm.nih.gov/42546264/
- OpenScholar, scientific retrieval + citation evaluation: https://www.nature.com/articles/s41586-025-10072-4
- ReClaim, sentence-level reference/claim generation: https://aclanthology.org/2025.findings-naacl.55/
- Generate but Verify / Answering with Faithfulness: https://aclanthology.org/2025.ijcnlp-long.56/

---

# 16. Research disposition

**Supported with bounds:** the industry and recent research support adding generative synthesis, semantic retrieval, fine-grained attribution, stronger evaluation, and a server-side trust boundary.

**Not established:** that hybrid/RRF, reranking, GraphRAG, agentic query planning, or custom model training are improvements for this project's corpus.

**Strongest next evidence-producing step:** freeze and run the v2 retrieval/evidence benchmark before changing the public answer path.
