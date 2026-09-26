# Public Generative RAG v2 — research-backed implementation plan

**Status:** planning / research artifact, not product authorization  
**Research snapshot:** 2026-09-25; revised 2026-09-26 after a code-grounded review (see "Revision summary")  
**Base when written:** `main@40de3cdcd98973b0e3a1c91d6ac114bc62857c04`  
**Scope:** public synthetic biotech / pharma controlled-document demonstration  
**Existing authority:** `DECISIONS.md` ADR-001 through ADR-017, especially ADR-005, ADR-007, ADR-009, ADR-012, ADR-013, ADR-014, ADR-015, and ADR-016.

## Objective

Upgrade Biotech RAG Assistant from a deterministic trust-layer demonstration into a public generative RAG assistant without weakening the controls that currently make the project interesting.

The target is not "a chatbot with citations." The target is a bounded generative system in which:

1. document-control policy decides what may enter retrieval;
2. retrieval nominates evidence but does not decide truth;
3. a typed evidence packet defines the only evidence generation may use;
4. a language model proposes reader-facing synthesis;
5. deterministic checks decide whether that synthesis may be shown, and semantic checks advise until they are calibrated;
6. insufficient or failed evidence produces an explicit "not stated", a labelled fallback, or a refusal rather than ungrounded completion;
7. every material stage remains inspectable and attributable to a versioned configuration;
8. the public demo costs nothing to keep running: it serves reviewed, recorded runs instead of a live paid endpoint.

The public demo remains explicitly **not a validated GxP system**, does not make regulated decisions, and uses synthetic data only.

## Revision summary (2026-09-26)

The first draft had the right boundaries and the wrong first step. It froze a 120-case benchmark before the corpus that benchmark needs existed, and it treated refusal as a retrieval-threshold problem. A review against the code (§1.8) and the owner's adjacent public projects (§1.9) changed the plan in these ways:

- **Corpus before benchmark.** Today's index is 18 chunks of 14–36 words from 8 retrievable documents, with no tables. A 120-case benchmark split by source document cannot be built on it. Corpus v2 is now Slice 1, generated outside this repository against the specification in Appendix A.
- **Span-based gold.** Gold evidence is recorded as `(doc_id, version, char_start, char_end, span_text)`, not positional chunk IDs, so one frozen benchmark can compare chunkers.
- **Near-miss questions are a first-class case family.** On the production gate, questions whose topic is covered but whose fact is not stated pass the relevance gate and score higher than supported questions (§1.8). "Not stated in approved documents" becomes an explicit answer disposition.
- **Deterministic claim gates block from the first generated answer.** Quote containment, quantity grounding, identifier grounding, section role, and disposition consistency are blocking checks (§5.5). Semantic support auditing stays advisory until calibrated.
- **ADR-014 is directional evidence only.** Its harness no longer matches production after ADR-016, its hard set is one paraphrase per document, and it has no identifier or numeric queries. All retrieval arms now run through the package's retriever interface.
- **Adjacent evidence is reused.** The benchmark adopts Evidence Bundler's challenge-corpus conventions and its RC1 lesson that a weak lexical control can pass a synthetic benchmark. Retrieval work adopts MindGraph's nomination contract, its bounded graph-admission result, and its non-replicated reranking result.
- **Two tracks.** The EvidencePacket separates retrieval from generation, so the generation seam is built in parallel on today's BM25 path (shadow, DEV-only) instead of waiting for retrieval promotion.
- **Recorded-runs public demo.** Generated answers are produced offline, reviewed, and published as static records with their full identities. There is no standing paid endpoint.
- **CI without a live model.** Scripted adversarial generators prove each gate fires, recorded outputs cover regression, and live evaluation is a manually triggered, budgeted job.
- **Smaller fixes.** EvidencePacket identity excludes float scores; the ADR-009 outcome amendment is named; each slice predeclares primary metrics and a tie rule; single-annotator labels are disclosed; private-workspace vocabulary is replaced with public links or plain descriptions.

## Why this plan now

The repository already has the controls that generation will depend on:

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

ADR-014 already records a small semantic-vs-BM25 experiment in which semantic retrieval substantially improved hard paraphrase retrieval and produced a cleaner refusal separation than the lexical gate against clearly off-domain probes. ADR-015 already reserves Evidence Bundler (EB) for ingest/provenance reuse and Claim Audit Lab (CAL) for a later semantic answer-grounding seam.

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

ADR-014 found semantic-only retrieval ahead of BM25 and RRF hybrid on the current synthetic corpus, but that result is directional (§1.8). It rests on eight hand-written paraphrases over 18 chunks and contains no query type where lexical retrieval is expected to win. Therefore:

- preserve BM25 as the deterministic control;
- qualify semantic retrieval on a larger frozen benchmark that includes identifier and numeric queries;
- include hybrid (RRF and a score-fusion variant) as challenger arms;
- keep reranking parked unless a measured ordering failure reopens it (MindGraph's reranking gain did not replicate, §1.9);
- promote only the smallest stack that actually improves the biotech benchmark.

Do not replace local evidence with vendor defaults, and do not treat thin local evidence as settled.

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

The current exact-span paragraph chunking remains a good provenance baseline, but a realistic v2 corpus and benchmark should include:

- headings and nested sections;
- tables;
- lists;
- structured procedural steps;
- references / cross-links;
- version history traps.

Structure-aware representation should be tested before fine-tuning an embedder.

## 1.5 Fine-grained attribution is becoming more important than document-level citation

### Observed

Recent RAG research increasingly evaluates sentence- or claim-level attribution, citation precision/recall, and support rather than merely whether a cited document exists. Work such as ReClaim and OpenScholar shows the usefulness of attaching citations to specific generated statements and verifying whether cited passages actually support them.

### Inference for this project

The generator should not emit an opaque paragraph plus a bibliography. It should emit structured **claims with evidence IDs and verbatim quotes**. Rendering into prose happens after schema validation and the deterministic gates.

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

That is a small-scale analogue of controlled lifecycle evidence, without claiming validation.

## 1.8 Local evidence from this repository (review of 2026-09-25)

### Observed

**ADR-014 scope.** The comparison ran over 18 chunks of 14–36 words from 8 retrievable documents. The hard set is 8 paraphrases, one per retrievable document, written to be lexically distant from the source. Relevance was scored at document level, so recall@1 means picking 1 of 8 distinct topics. The 6 off-topic probes are far off-domain (vacation policy, weather, cafeteria hours). No query targets a document ID, code, or number.

**Harness drift.** `experiments/semantic_vs_bm25.py` indexes and embeds `c["text"]`. ADR-016 later made that field the body-only cited span, while production indexes `section_heading + "\n" + text` (`retrieval.index_text`). The BM25 ranks and coverage values recorded in `experiments/comparison-results.json` match heading+body indexing on 22/22 queries, so the experiment predates ADR-016. Re-running the harness today changes 2/22 coverage values (`easy-balance-daily` 0.88 → 0.62, `easy-customer-conflict` 0.78 → 0.67). The BM25 headline (the coverage gate wrongly refuses 9/16 on-topic queries; hard-set MRR 0.49) does not change. The semantic arm now embeds different text than it did in June and has not been re-run; the embedding model could not be downloaded in the review environment.

**Near-miss probe.** Questions whose topic is covered but whose specific fact is not stated were run through the production answer path (`build_retriever` → `query_retriever` → `build_extractive_answer`, BM25 with the 0.6 coverage gate, `top_k=3`, `examples/synthetic-controlled-docs`):

| Question | Rank-1 coverage | Outcome | Does the rank-1 passage state the fact? |
|---|---:|---|---|
| What is the acceptance range for the analytical balance daily check? | 0.83 | answer | No: "outside the acceptance range", no range given |
| How long an absence from the suite triggers gowning requalification? | 0.83 | answer | No: "a long absence" |
| What is the defined use period for printed copies stamped by document control? | 0.88 | answer | No: "for a defined use period" |
| What is the action limit for viable environmental monitoring? | 0.60 | answer | No: the SOP's purpose statement |
| How many days does QA have to close a deviation? | 0.40 | refusal | — |
| What is the action limit value for purified water? | 0.40 | refusal | — |
| *Supported control:* How many traceable weights are used for the daily balance check? | 0.71 | answer | Yes: "two traceable weights" |
| *Supported control:* Who must sign the line clearance record before the run starts? | 0.71 | answer | Yes: "both operations and QA" |
| *Demo trap:* What is the membrane filtration hold time for sterility? | 0.00 | refusal | The only source is Obsolete and excluded |

Four of six near-miss questions pass the gate, and three of them score above both supported controls.

### Inference for this project

- Near-miss questions reuse the source's own vocabulary ("acceptance range", "action limit") because the source names the concept without its value. Any relevance signal, lexical or dense, measures topic match, so a retrieval threshold cannot refuse this class. The dense case was not measured here; it is expected to behave the same, and Slice 3 measures it.
- Today the extractive answer shows the passage and asserts nothing, so the failure is benign. With a generator, this is the likely fabrication path: an invented value cited to a real chunk passes structural citation resolution. The defense belongs at the claim layer (§5.3–§5.6), not in a retrieval threshold.
- ADR-014 remains useful direction. It is not promotion evidence.
- Every retrieval arm must run through package code, so the arm that is measured is the arm that ships.

## 1.9 Evidence from adjacent projects

These are the owner's public repositories. Their results describe their own corpora; here they inform design, not promotion.

### Observed

- **Evidence Bundler challenge corpus** ([`eb-challenge-corpus-v1`](https://github.com/camerontjs-dot/evidence-bundler/tree/main/benchmarks/eb-challenge-corpus-v1)): a fully fictional regulated micro-world with 60 sources, 946 passages, and 148 cases across 12 challenge families (lexical, paraphrase, negation, numeric threshold, temporal supersession, condition/exception, hard distractor, duplicate, long-document burial, multi-passage, no-answer, aperture boundary). Gold is span-based (offsets plus `span_text`) with relevance classes (`decisive_support`, `decisive_qualifier`, `decisive_exception`, `decisive_contradiction`, `material_context`, `hard_negative`), joint groups, and named source subsets ("apertures") that withhold decisive evidence. Runtime inputs and evaluator-only gold live in separate directories. The generator is deterministic from a seed and an as-of date, and the frozen package carries a `SHA256SUMS` freeze receipt.
- **Evidence Bundler evaluator assurance RC1 and RC2** ([RC1 results](https://github.com/camerontjs-dot/evidence-bundler/blob/main/docs/research/results-07-eb-retrieval-evaluator-assurance-rc1.md), [RC2 results](https://github.com/camerontjs-dot/evidence-bundler/blob/main/docs/research/results-13-eb-retrieval-assurance-rc2.md)): in RC1 a deliberately weak token-overlap retriever reached case hit@K 1.000 and decisive recall 0.966, failing only on joint-group coverage; much of the synthetic benchmark was lexically recoverable. RC2 was rebuilt until three lexical controls failed (decisive recall 0.45; zero qualifier/exception and joint-group success) while the oracle scored 1.0. Gaming controls (return-everything, corrupted provenance, false completeness, false answerability) each fail on the surface they target. Critical failures are non-compensable.
- **MindGraph vNext retrieval** ([plan](https://github.com/camerontjs-dot/MindGraph/blob/main/docs/VNEXT_RETRIEVAL_PLAN.md), [decisions](https://github.com/camerontjs-dot/MindGraph/blob/main/DECISIONS.md)): a MiniLM cross-encoder improved one held-out case, then produced no ordering benefit on a document/family-disjoint replication (`RERANKING_NOT_REPLICATED`). A graph-only miss turned out to be a consumer cutoff and was fixed by bounded, authored-link-gated graph admission, merged as an opt-in typed sidecar with deterministic `ga1:<sha256>` identities over sorted-key JSON and unchanged defaults. The next planned slice is a canonical typed nomination with progressive expansion (`nomination -> excerpt -> section -> graph neighborhood -> source`). Its failure model separates representation, first-stage recall, ranking, stale admission, authority confusion, and context-budget failures.
- **Claim Audit Lab v0.5.0** ([README](https://github.com/camerontjs-dot/claim-audit-lab/tree/v0.5.0)): retrieve → NLI → frozen deterministic rules. The project describes itself as "mechanisms verified, accuracy not validated": 27/50 exact agreement with human gold, and numeric-bound comparison and two-hop composition are not yet implemented. Verdicts are `supported`, `partially_supported`, `unsupported`, `contradicted`, and `not_checkable` with named abstention reasons.

### Inference for this project

- Reuse EB's benchmark conventions rather than inventing new ones: span gold, relevance classes, joint groups, apertures, runtime/evaluator separation, freeze receipts, the control set, and non-compensable critical failures.
- Treat RC1 as a direct warning: a self-authored synthetic benchmark can be large and carefully labelled and still fail to discriminate. The evaluator must show two-sided discrimination before any arm comparison (§6.3).
- Adopt MindGraph's nomination shape and progressive expansion for both the EvidencePacket and the public evidence view. Use bounded, authored-link-gated admission for cross-references, with the status gate supplying currentness. Keep reranking parked.
- Align semantic-audit labels with CAL's verdicts. Because CAL does not yet check numeric bounds, quantity grounding has to be this project's own deterministic gate.

---

# 2. Current strengths and missing capabilities

## Already strong

The current project already has:

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

ADR-014 is too small, too paraphrase-heavy, and no longer reproducible with its harness as written (§1.8). It cannot promote a semantic threshold.

### B. Corpus realism and structure-aware representation

The public corpus is 8 retrievable documents of two or three short paragraphs each. It has no tables, numbered procedures, multi-level sections, cross-references, version families with changed values, or long documents.

### C. Typed evidence packet

There is no canonical object between retrieval and generation that freezes exactly what the model was allowed to see.

### D. Controlled generation

There is no provider-neutral generative interface, structured claim output, or deterministic fallback path.

### E. Claim-level support

Current citation validation proves identity/resolution only. Nothing checks that a quote exists in its cited chunk or that a stated quantity appears in the evidence.

### F. Near-miss handling

Neither the lexical gate nor a similarity threshold can refuse questions whose topic is covered but whose fact is not stated (§1.8). There is no "not stated" disposition.

### G. Prompt-injection / poisoning tests

The non-generative system has little exposure here; generation changes that threat model.

### H. Layer-specific evaluation

The current trust suite is strong for the deterministic baseline, but v2 needs diagnostic metrics for retrieval, extraction, generation, attribution, support, security, latency, and cost, and a harness that measures package code rather than a parallel port.

### I. Public demo economics

The GitHub Pages demo is intentionally static. A live generation endpoint would add standing cost, key management, and abuse exposure. Recorded runs avoid all three.

### J. Provider/model lifecycle records

Model and prompt identity need to become explicit audit fields before generation is promoted.

### K. Permission-aware retrieval contract

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
8. **No tuning or design decision may use frozen TEST or PROSPECTIVE labels.**
9. **Industry defaults do not override local measurement.**
10. **The public demo must not imply validation, compliance certification, or autonomous quality decisions.**
11. **The generator can narrow, never widen.** It may drop claims, report that a fact is not stated, or decline. It may never add evidence, cite outside the packet, or turn a refusal into an answer.
12. **"Not stated in approved documents" is an answer, not a failure.**
13. **A benchmark must be able to fail lexical and dense shortcuts alike.**

---

# 4. Target architecture

```text
User question (single turn)
    |
    v
Query normalization / policy (length caps)
    |
    v
Controlled corpus gate
(status + current version + source hash + future ACL)
    |
    v
Candidate retrieval -> typed RetrievalNominations
(BM25 control / semantic / hybrid challengers)
    |
    v
Bounded admission
(dedup + diversity + budget + optional section expansion
 + optional authored cross-reference admission; retrievable targets only)
    |
    v
EvidencePacket v1  <---- ep1:<sha256> identity (scores excluded)
    |
    +-- empty packet --> refusal (model is never called)
    |
    +--------------------------+
    |                          |
    v                          v
Deterministic extractive       Generative synthesizer
answer (existing control)      (provider-neutral, no tools, packet only)
                               |
                               v
                         structured answer:
                         claims + verbatim quotes + gaps
                               |
                               v
                         deterministic claim gates (blocking)
                         G1 schema, G2 packet membership,
                         G3 quote containment, G4 quantity grounding,
                         G5 identifier grounding, G6 section role,
                         G7 disposition consistency
                               |
                               v
                         semantic support audit
                         (advisory; CAL-aligned verdicts)
                               |
                               v
                         disposition policy
             /            |              |             \
       generated     not_stated     extractive       refusal
                     (cited topic   fallback
                      passage)      (labelled)
                               |
                               v
                 response + trace -> recorded run (public demo)
```

Generation never receives draft/obsolete chunks, arbitrary filesystem paths, hidden extra corpus state, or tool authority. A refusal at the retrieval gate costs nothing because the model is not called.

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

Added from the MindGraph nomination contract (§1.9):

- `nomination_kind` (`chunk`, `section_expansion`, `cross_reference_admission`);
- `retrieval_reasons`: which signals nominated it, with per-signal rank;
- `representation_level` (`chunk`, `section`, `document`);
- `section_role` where the representation supplies it (`normative`, `definitions`, `responsibilities`, `references`, `revision_history`);
- `authority_class` from a documented `doc_type` precedence table (ADR-018);
- `token_estimate`;
- `expansion_handle`.

Scores remain method-specific diagnostics, not support or confidence values. The CLI/API record, the packet, and the public evidence view are projections of the same nomination.

## 5.2 EvidencePacket v1

An immutable packet assembled after policy admission.

Minimum fields:

- packet schema version;
- query + stable query ID;
- corpus/index identity (corpus manifest hash);
- retrieval config identity;
- aperture ID (evaluation runs only);
- admitted nominations, each with its admission provenance;
- any added section or cross-reference context with explicit provenance;
- excluded-candidate summary by mechanical reason;
- evidence budget;
- packet identity.

Identity is `ep1:<sha256>` over canonical JSON (UTF-8, sorted keys, no insignificant whitespace, no timestamps) of the schema version, normalized query, corpus manifest hash, retrieval config ID, aperture ID, the ordered admitted items as `(chunk_id, doc_id, version, status, source_hash, char_start, char_end, nomination_kind)`, and the exclusion summary. Raw scores and per-signal ranks live in a `diagnostics` block outside the hash. Dense-retrieval scores differ in their last digits across hardware and library builds, and a hash over them would make "same inputs, same packet" fail intermittently. Ranking rounds scores to 1e-6 before the existing deterministic `(doc_id, chunk_index, chunk_id)` tie-break.

No generated content belongs in the packet.

## 5.3 GeneratedAnswer and GeneratedClaim

The generator returns a schema-valid structure, not Markdown:

- `disposition`: `answered`, `partially_answered`, `not_stated`, or `insufficient_evidence`;
- `claims[]`: `claim_id`, `text`, `citations[]` of `{chunk_id, quote}`, optional `qualifier`, optional `limitation`;
- `gaps[]`: `{asked_about, statement, topic_citation: {chunk_id, quote}}`, meaning what the question asked that the approved documents do not state, cited to the passage that names the topic.

Each quote must be a verbatim excerpt of its cited chunk. Because `chunk.text == raw_text[char_start:char_end]` (ADR-016), every accepted quote resolves to exact source offsets, which the evidence view uses for highlighting.

For the near-miss balance question in §1.8, the intended output is a gap, not a claim: "CAL-ENG-005 requires the daily check to stay within an acceptance range but does not state the range", cited to "falls outside the acceptance range".

## 5.4 GenerationRecord

Minimum fields:

- EvidencePacket ID;
- provider;
- model ID / version;
- prompt template ID / hash;
- generation parameters;
- raw structured model output hash;
- validated claims and gaps;
- per-claim gate results (§5.5);
- structural citation result;
- semantic audit result when enabled;
- final disposition (§5.6);
- latency;
- input/output token count where available;
- error/fallback path;
- recorded-run ID when published (§5.7).

This is an audit record, not a chain-of-thought record.

## 5.5 Deterministic claim gates

These gates are blocking from the first generated answer. Each has a scripted adversarial generator in CI that it must catch (§6.7).

| Gate | Check | On failure |
|---|---|---|
| G1 schema | output validates; unknown fields are rejected | extractive fallback |
| G2 packet membership | every cited `chunk_id` is an admitted packet item | drop the claim |
| G3 quote containment | each quote is an exact substring of its cited chunk after Unicode NFC and whitespace normalization | drop the claim |
| G4 quantity grounding | every number, range, unit, percentage, and duration in the claim text appears in that claim's quotes (numerals and number words normalized) | drop the claim |
| G5 identifier grounding | every document, equipment, room, form, or material code in the claim appears in its quotes or in packet metadata | drop the claim |
| G6 section role | a claim about a current requirement cannot rest only on revision-history or references sections | drop the claim |
| G7 disposition consistency | `not_stated` and `insufficient_evidence` carry no claim asserting the missing fact; every gap cites a topic passage; a refusal carries no claims | extractive fallback |

The normalizers fail closed: when a quantity or identifier cannot be matched with confidence, the claim is dropped. G6 uses heading names until ADR-019 defines section roles. It exists because a current document's revision-history table can quote a superseded value ("action limit changed from 5 to 3 CFU"), and G3 and G4 alone would pass a claim that states the old value from that line.

The gates do not decide whether a quoted passage supports the meaning of the claim. A claim that misreads a real quote passes them. That residual risk belongs to semantic audit and human review, which is one reason the public demo publishes reviewed recorded runs.

## 5.6 Disposition policy and the ADR-009 amendment

ADR-009 fixed `outcome` to exactly `answer` and `refusal` and rejected a `partial` outcome. This plan keeps `outcome` binary for CLI/API stability and adds a `disposition` field (`generated`, `generated_with_gaps`, `not_stated`, `extractive_fallback`, `refusal`) plus the `gaps[]` and per-claim gate results above.

| Situation | Disposition | Reader sees |
|---|---|---|
| empty packet | `refusal` | refusal text; the model is not called |
| G1 or G7 failure, provider error, timeout | `extractive_fallback` | "Generation failed validation; showing the retrieved source passages instead." |
| all material claims dropped by G2–G6 | `extractive_fallback` | the same label |
| generator reports `not_stated` with a valid topic citation | `not_stated` | "The approved documents mention this but do not state it." with the cited passage |
| generator reports `insufficient_evidence` | `refusal` | "I found related material, but not enough approved evidence to answer." with the passages shown as related material, not as citations |
| otherwise | `generated` or `generated_with_gaps` | the synthesis, its quotes, and any gaps |

`not_stated` keeps `outcome: answer` because it carries its topic citation. An extractive fallback is never presented as synthesis, and a generator abstention is never converted into an extractive "answer" that implies support. The amendment is recorded as its own ADR (§11), not applied silently.

## 5.7 RecordedRun

The public demo's unit of content. A recorded run is a static record containing:

- the question;
- the full EvidencePacket;
- the GenerationRecord (provider, model ID/version, prompt template hash, parameters);
- gate results and the semantic-audit result if enabled;
- the rendered answer;
- a review note (reviewer, date, accepted or flagged);
- the release identity (commit, corpus manifest hash, retrieval and generation config IDs).

Runs live under `docs/recorded-runs/` with a manifest of their hashes. The page renders only runs whose hashes match the manifest.

---

# 6. Evaluation programme

Use a frozen-split discipline even though nothing is trained: DEV for design and error analysis, TEST sealed until the candidate is frozen, and PROSPECTIVE written in a separate pass, sealed, and revealed only after freeze.

## 6.1 Corpus v2 (build first)

The corpus is generated outside this repository with the owner's local synthetic-corpus generator, against the specification in Appendix A, and imported as `benchmarks/controlled-docs-v2/`. In summary:

- 14 process areas, about 40–45 retrievable documents, plus superseded predecessors, drafts, and obsolete versions (about 60–70 documents in total);
- realistic structure: nested sections, numbered steps, Markdown tables for limits, frequencies, tolerances, and sampling plans, responsibilities tables, cross-references, revision-history tables, and 3–4 long documents;
- seeded traps: changed values across versions, named-but-unstated parameters, lagging training notes, identifier-rich text, and hard lexical distractors;
- a separate adversarial bundle for the security slice, never mixed into the benchmark corpus or the demo.

The existing v1 corpus, the 24-case trust suite, the 13-case natural-language suite, and the demo stay unchanged as regression fixtures.

## 6.2 Benchmark v2 (after the corpus is frozen)

Target about 150 cases: DEV about 40, TEST about 80, PROSPECTIVE about 30 (sealed). The case families adapt EB's twelve challenge families and add biotech-specific ones. Counts are across all splits.

| Case family | What it tests | Approx. cases |
|---|---|---:|
| B01 lexical direct | the question uses document vocabulary | 12 |
| B02 paraphrase, low overlap | content-term overlap with the decisive span ≤ 0.3 | 16 |
| B03 identifier lookup | document, equipment, room, and form codes | 10 |
| B04 numeric threshold | the answer is a value with units | 14 |
| B05 table cell | the answer sits in a table row or column | 10 |
| B06 condition / exception | "unless", "except", "only if" must be retrieved and stated | 10 |
| B07 negation / polarity | "is not required", "must not" | 6 |
| B08 multi-passage | the answer needs two passages or a cross-reference (joint groups) | 12 |
| B09 supersession / stale value | the current value differs from a superseded, draft, or obsolete version | 12 |
| B10 fact not stated | topic covered, fact absent; expected `not_stated` | 16 |
| B11 out of scope | off-domain, or in-domain but uncovered; expected refusal | 10 |
| B12 hard lexical distractor | alert vs action limit, Grade A vs Grade B | 8 |
| B13 authority conflict | a training note lags its SOP; the governing document wins | 6 |
| B14 long-document burial | the decisive fact is deep in a long SOP | 6 |

Each case has one primary family and optional secondary tags. Every case family appears in both DEV and TEST.

**Gold** (evaluator-only), per annotation: `doc_id`, `version`, `char_start` and `char_end` (Python character offsets over the decoded UTF-8 text), `span_text`, `relevance_class` (EB's classes plus `stale_trap`), `decisive`, `joint_group_id`, `expected_disposition` (`answer`, `not_stated`, or `refusal`), `required_facts` (atomic facts with values, each tied to a span), `forbidden_facts` (for example superseded values), and a one-line rationale. Relevance is scored by span overlap, so the benchmark does not depend on chunk boundaries.

**Apertures:** `full` and `withhold_decisive`. Under `withhold_decisive` the evaluator drops chunks that overlap decisive spans at index time. Running answerable cases under it produces matched pairs whose expected disposition becomes `not_stated`: the same question, with and without its decisive evidence.

**Question authorship.** Author leakage was the main weakness of ADR-014, so:

- documents, questions, and gold are produced in separate passes;
- questions are written from process-area briefs, personas, and document titles, not from passage text;
- styles are mixed: natural questions, short keyword queries, identifier-led queries, and a few abbreviations or typos;
- lexical overlap is measured with this repository's `coverage()` and capped per family (B02 ≤ 0.3, B01 ≥ 0.6), and the values are kept for diagnostics;
- splits are grouped by process area, so near-duplicate questions cannot straddle splits;
- PROSPECTIVE cases are written in a separate pass, kept outside the repository, and committed only as a SHA-256 in the freeze receipt until they are revealed.

## 6.3 Evaluator controls

Adopt EB's control set and add controls specific to this project:

- null; gold oracle; first-N / source order; token-overlap lexical retriever; return-everything (budget); corrupted provenance; hard-negative-biased; answerability liar (claims an answer on `not_stated` and refusal cases);
- a naive dense-only retriever;
- a retriever with the status gate removed, which must fail on stale leakage;
- the existing BM25 + coverage gate;
- for Slice 6, a naive generator given top-K without the claim schema.

Slice 2 gate: the oracle scores at ceiling; every gaming control is rejected on its intended surface; and the benchmark shows **two-sided discrimination**. The token-overlap control must fail the B02 and B10 floors, and the dense-only control must fail the B03 and B04 floors. If either shortcut passes, fix the benchmark before comparing arms.

If a weak system later passes the same decisive gate as a candidate, record the comparison as non-discriminating and inconclusive, not as a win for the candidate.

## 6.4 Layer-specific metrics

Primary metrics for each decision are named in the slice gates (§7). Everything else in this section is diagnostic.

### Ingest / extraction

- source-hash validity;
- span round-trip validity;
- table-cell / structured-field recovery where gold exists;
- status/version metadata fidelity.

### Retrieval

- relevant-document recall@K;
- decisive-span recall@K;
- MRR / nDCG where ordering matters;
- qualifier/exception recall;
- joint-group coverage;
- duplicate burden;
- evidence-role diversity;
- stale/draft leak count;
- out-of-scope refusal separation (B11 only; see Slice 3).

### Evidence packet

- provenance completeness;
- packet determinism;
- admitted-evidence diversity;
- context budget;
- source coverage;
- packet reconstitution from stored identities.

### Generation

- required-fact recall;
- unsupported material-claim rate;
- contradiction rate;
- unnecessary-claim rate;
- `not_stated` correctness on B10 and `withhold_decisive` pairs;
- forbidden-fact rate (stale values in answers);
- refusal correctness;
- limitation disclosure;
- per-gate drop rate.

### Citation / attribution

Keep structural and semantic dimensions separate:

- citation resolves to admitted chunk;
- quote containment rate;
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
- estimated cost per answer and per recorded-run release;
- fallback rate;
- provider error rate.

### Non-compensable failures

No recall, preference, or aggregate score compensates for any of these:

- stale, draft, or obsolete content in retrieval results or in a displayed answer;
- a displayed citation outside the packet, or a displayed quote that is not contained in its chunk;
- a displayed quantity or identifier absent from its quotes;
- schema-invalid output shown as an answer;
- different packet identities for identical inputs;
- false completeness or answerability claims;
- incomplete per-family reporting.

## 6.5 Decision rules and statistics

- Each slice predeclares one or two primary metrics, the minimum effect worth acting on, and family floors before TEST is run.
- Comparisons are paired per case: exact McNemar for hit/miss metrics, paired bootstrap intervals for rates. Reports give intervals, not only point estimates.
- Ties and inconclusive results go to the simpler arm.
- With about 80 TEST cases (about 6 per family), family results are diagnostic. Only the primary metrics and the non-compensable failures decide promotion.
- The diagnostic metrics in §6.4 cannot be mined for a win after the fact.

## 6.6 Human review and LLM judges

LLM-as-judge may be used as a research instrument, never as the sole decisive authority for the first promotion.

For promotion-relevant semantic support evaluation:

- freeze the rubric after DEV error analysis and before TEST;
- label a human-reviewed subset;
- measure judge agreement against humans;
- preserve disagreement;
- compare at least one alternate judge or deterministic control where practical;
- use CAL's verdict vocabulary so that a CAL adapter maps one-to-one.

Labels in this project come from one annotator, the maintainer. Reports say so. A random 20% of labels is re-labelled after at least a week, and intra-rater agreement is reported.

## 6.7 Harness and CI

- Every retrieval arm is a `RetrievalConfig.method` value in the package (`bm25`, `semantic`, `hybrid_rrf`, `hybrid_weighted`), and experiments call package code. Semantic dependencies ship as an optional extra, so default CI stays lean. The ADR-014 script is either rebuilt on package code or kept as a historical record marked non-reproducible.
- Generation tests use a `ScriptedGenerator` that replays fixture outputs. One scripted generator per failure mode must be caught by its named gate: out-of-packet citer (G2), quote forger (G3), number fabricator (G4), code fabricator (G5), revision-history quoter (G6), refusal-with-claims and not-stated-with-value (G7), schema breaker (G1), and injection follower. This extends the existing trap-suite approach to the generator.
- Recorded real-model outputs replay through the gates as regression fixtures.
- Live-model evaluation is a `workflow_dispatch` job with an explicit budget cap and a repository secret. It never runs on pull requests.

---

# 7. Work slices and promotion gates

Two tracks share Slice 0 and join at Slice 6. Each slice lands independently and leaves the deterministic path working.

```text
Track R (retrieval):   0 -> 1 corpus v2 -> 2 benchmark v2 -> 3 representation + retrieval arms
Track G (generation):  0 -> 4 nominations + packet -> 5 shadow generator + claim gates
Join:                  6 generation evaluation -> 7 security -> 8 recorded-runs demo
Conditional:           9 triggered experiments        10 EB / CAL integration
```

## Slice 0 — freeze Baseline V1

**Purpose:** establish an immutable before-state.

Actions:

- record current `main` commit/tree and current trust-suite output;
- regenerate static demo parity;
- store current benchmark/config identities;
- capture latency and public UX baseline;
- record that the ADR-014 harness predates ADR-016: re-run it with `index_text` where the embedding model can be downloaded and record whether the headline reproduces, or mark ADR-014's numbers as historical;
- add the §1.8 near-miss probe as a regression fixture that documents current behavior (answered, with the fact absent from the passage) without changing retrieval.

Gate: no behavior change.

## Slice 1 — corpus v2 (external generation, import only)

**Purpose:** give the benchmark a corpus that can carry it.

Deliver `benchmarks/controlled-docs-v2/` per Appendix A, with its freeze receipt, validation receipts, and a README stating the synthetic-data boundary.

Do not change `src/`, the v1 corpus, the trust suites, or the demo in this slice.

Gate: the Appendix A checklist passes; `biotech-rag validate-corpus` passes; the ADR-013 invariant holds; the publication-safety scan is clean.

## Slice 2 — benchmark v2 and diagnostic evaluator

**Purpose:** make future claims falsifiable before changing retrieval.

Deliver:

- frozen DEV/TEST manifests and the sealed PROSPECTIVE commitment;
- span-overlap scoring and apertures;
- an error taxonomy covering ingest, retrieval (MindGraph's failure model), evidence admission, generation, attribution, and security;
- the controls in §6.3;
- Markdown + JSON reports with per-family tables.

Do **not** implement new retrieval methods in the same slice.

Gate: two-sided discrimination (§6.3), plus metamorphic checks: source-order permutation leaves judgments unchanged, duplicate insertion earns no extra credit, and a mutated gold span changes the result.

## Slice 3 — representation and retrieval arms

**Purpose:** reproduce or falsify ADR-014 at scale, representation first.

1. Representation, with no model change: fold the document title, section path, and table header into the indexed text at index time while the stored text stays the verbatim span (the ADR-016 pattern); record section roles; test parent/section aggregation as EB does.
2. Arms, all through package code: BM25; semantic (the MiniLM baseline plus one current-generation small embedder chosen before TEST is run, with truncation counts logged, since MiniLM truncates input beyond 256 word pieces); hybrid RRF; hybrid weighted score fusion.
3. Bounded cross-reference admission, following MindGraph: depth 1, authored references in approved text only, retrievable targets only, exact-duplicate suppression, typed provenance, a budget cap. Measured on B08.
4. Reranking stays parked. Reopen it only if first-stage decisive recall is high and ordering is a measured failure, and replicate on a process-area-disjoint split before promotion.

Primary decision metric: decisive-span recall@K on TEST, compared per case. Non-compensable: stale leak must be zero.

Refusal: measure retrieval-level refusal only on B11 out-of-scope cases. B10 belongs to the answer layer, and no retrieval threshold is tuned to refuse it.

Gate: promote an arm only if it beats the control on the primary metric by the predeclared minimum effect, holds the B01, B03, and B04 floors, and keeps stale leakage at zero. Record the result in ADR-020.

## Slice 4 — typed nominations + EvidencePacket v1 (Track G; can start after Slice 0)

**Purpose:** create the hard seam before generation.

Deliver:

- typed nomination records (§5.1);
- packet builder and `ep1:` identity (§5.2);
- admission policy;
- deterministic dedup;
- context budget;
- optional section expansion behind a flag;
- a packet inspection surface in the CLI and API, with parity tests.

This works on today's BM25 path and the v1 corpus, and picks up the promoted retrieval arm later without a contract change. Test section expansion separately from retrieval ranking.

Gate: identical inputs and config produce the same packet identity across Python 3.11–3.13 in CI, with scores outside the identity.

## Slice 5 — shadow generator + deterministic claim gates (Track G)

**Purpose:** add generation without changing the public answer authority.

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
- structured output schema (§5.3);
- low-temperature / bounded output;
- provider/model selected by configuration;
- model ID and prompt hash recorded;
- gates G1–G7 (§5.5) and the disposition policy (§5.6);
- `ScriptedGenerator` stubs in CI (§6.7);
- generation failure falls back safely.

Add `/synthesize` or equivalent as a shadow/internal route. Do not replace `/answer`.

Before any generation rubric is frozen, run a small maintainer-run live pass on DEV cases only: the v1 suites and the §1.8 probes at first, and benchmark v2 DEV once it is frozen. Read the outputs, code the failure types, and only then freeze the rubric.

Gate: every scripted adversarial generator is caught by its named gate; the generator cannot cite outside the packet or bypass refusal; the model is not called on an empty packet.

## Slice 6 — generation evaluation and semantic-support shadow

**Purpose:** decide whether generation earns a place in the public answer. Requires Slices 2 and 5.

- Freeze the rubric from the DEV error analysis before TEST is run.
- Primary metrics: unsupported material-claim rate (human-labelled on TEST), required-fact recall, and `not_stated` correctness on B10 and the `withhold_decisive` pairs.
- Non-compensable: a forbidden fact (for example a superseded value) in a displayed answer; a quantity that reaches a displayed answer without appearing in its quotes.
- User value: blinded pairwise preference between generated and extractive answers on about 30 TEST questions. Preference counts only if the generated answers also meet the predeclared unsupported-claim ceiling. If generation does not win, the extractive answer stays the public answer.
- Semantic support audit in shadow: CAL (tagged `v0.5.0` exists) or an NLI instrument, using CAL's verdict labels. It stays advisory and is compared against human labels and against a deliberately weak lexical-overlap checker.

Gate: the primary metrics beat the naive-generator control, and the semantic auditor beats the weak checker on human-labelled cases before it gains any blocking role (ADR-023).

## Slice 7 — RAG security qualification

**Purpose:** treat retrieval content as hostile data before public generation.

Run against the separate adversarial bundle, registered as its own named corpus through the existing allowlist. It never enters the benchmark corpus or the demo.

Add synthetic attacks:

- "ignore previous instructions" inside an approved-looking source;
- hidden/Unicode instruction variants;
- prompt-shaped section headings;
- malicious metadata;
- long-context flooding;
- adversarial near-duplicate content;
- stale document attempting to override current procedure;
- malformed generated schema;
- user prompt asking the model to reveal hidden instructions/config;
- fake quotes and fake citations embedded in documents;
- instructions inside table cells;
- a user prompt asking the model to ignore the documents or answer from general knowledge.

Controls:

- strict instruction/data separation;
- bounded chunk count/token budget;
- retrieved-content labeling;
- server-side prompt templates;
- output schema validation;
- no tools/action authority;
- source provenance and status gates;
- deterministic claim gates;
- logging of blocked/fallback paths.

The deterministic gates are the main containment: a hijacked generator still cannot cite outside the packet (G2), present unquoted text as evidence (G3), or add quantities or codes that are absent from its quotes (G4, G5). The residual risk is misleading synthesis over real quotes.

Do not claim prompt injection is "solved." Qualify bounded attacks.

Gate: no tested attack may cause source-policy bypass, unauthorized evidence admission, tool/action execution, or promotion of unstructured output.

## Slice 8 — public recorded-runs demo

**Purpose:** show generated answers publicly with no live model endpoint.

- The maintainer generates runs offline for a curated question set drawn from DEV and demo-only questions, never from sealed PROSPECTIVE cases. The set includes traps, at least one `not_stated`, at least one fallback, and at least one refusal, and the page states how the set was chosen.
- Every published run is reviewed first, and the review note is part of the record (§5.7).
- The page renders recorded runs. Free-text questions run the deterministic extractive control in the browser, labelled as such.
- Once Slice 6 has frozen TEST results, show them next to the examples. Until then, label the examples as curated examples, not benchmark results.
- Cost is one generation pass per release. No provider key is stored in the browser, the repository, or default CI.

Keep the obsolete-document trap and make it stronger: show the stale document under **Excluded by document control**, never as model context.

Gate: the public page cannot expose credentials, filesystem paths, or non-synthetic data; the prompt template is published only by hash unless deliberately released; every rendered run verifies against the manifest.

## Slice 9 — conditional experiments, only on a named trigger

- **Agentic / query decomposition.** Trigger: a persistent class of B08-style questions whose required evidence the simpler pipeline cannot recover. Compare the original query, deterministic decomposition if feasible, LLM query decomposition, and multi-query retrieval + merge; evaluate retrieval gain, cost, latency, duplicated evidence, and new failure modes.
- **Reranking.** Trigger: an ordering failure with adequate first-stage recall, replicated on a disjoint split.
- **Live generation endpoint.** Trigger: an explicit budget and abuse-control decision covering rate limits, an origin allowlist, input caps, a per-request budget, and a server-side key.
- **Multi-turn follow-ups.** Trigger: a decision on how query rewriting, a model step before retrieval, is logged and evaluated.

Gate: nothing from this slice enters the public baseline without a clear measured improvement on a named failure class.

## Slice 10 — EB / CAL integration

Respect existing ADR-015 and `plans/eb-cal-integration-and-sync.md`.

- As of 2026-09-26, CAL has release tags (`v0.4.0`, `v0.5.0`) and EB has none. ADR-015's tagged-release gate is met for CAL only.
- Reusing EB's benchmark conventions (§6.2) involves no code dependency and does not trigger ADR-015.
- EB integration belongs at ingest/provenance boundaries only when a stable tagged release and real adapter exist.
- CAL integration belongs at semantic answer-audit boundaries only when a stable tagged contract fits this use.
- Do not vendor dormant submodules.
- Do not let either component silently replace this project's controlled-document policy.

---

# 8. Public demo UX

The demo should teach the architecture rather than imitate a chat product. Answers follow the evidence-bundle shape: claims, the evidence for each claim, conditions, gaps, exclusions, and a trace.

Illustrative layout (not a recorded run):

```text
Answer                                        recorded run · reviewed <date>
------
Generated synthesis with inline markers [1][2]

Conditions & exceptions
  qualifier passages the answer depends on
Not stated in approved documents
  "CAL-ENG-005 requires the daily check to stay within an acceptance range
   but does not state the range." [3]
Excluded by document control
  SOP-QA-009 v0.8 (Obsolete): never model context

Evidence: 3 approved/effective passages · Gates G1–G7: passed
Semantic support audit: advisory / not enabled · Model: <label>, prompt <hash>

[Show evidence] [Show excluded sources] [Show trace]
```

Evidence drawer, using MindGraph's progressive disclosure: claim → verbatim quote, highlighted at its exact source offsets → section → full document. For each source it answers what the source is, why it was nominated, whether it is current, what authority it carries, and what expanding it will show.

Failure states should be first-class UX:

- "I found related material, but not enough approved evidence to answer."
- "The approved documents mention this but do not state it."
- "Generation failed validation; showing the retrieved source passages instead."

Never disguise fallback as successful synthesis.

Example chips: the obsolete-document trap, off-topic refusal, a **missing-fact trap**, a paraphrase, a table lookup, and a cross-reference.

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

Recorded runs pin the provider, model version, prompt template hash, and parameters. Regenerating them with a new model is a new release and needs a new review.

For public synthetic data, a hosted model is acceptable if no secrets are exposed. Demo generation runs from the maintainer's machine or a manually triggered job. Future private/client data requires a separate deployment/data-governance decision.

---

# 10. Model and system lifecycle record

Each public release should record:

- repository commit/tree;
- corpus manifest hash;
- corpus generator identity and the benchmark freeze-receipt hash;
- index identity;
- embedding model/version;
- retrieval config ID;
- generator provider/model;
- prompt template hash;
- semantic-auditor identity/version;
- evaluation dataset version;
- decisive report identity;
- recorded-run manifest hash;
- known limitations.

Any material change to retrieval, prompt, model, corpus parsing, policy, or evaluator must create a new candidate identity and rerun the relevant gates.

---

# 11. Decisions to record as ADRs when implementation starts

Do not silently convert this plan into accepted architecture.

Proposed ADR sequence:

1. **ADR-018 — corpus v2 and benchmark v2 policy:** generation provenance, span gold, case families, apertures, splits, controls, decision rules, and the `doc_type` authority precedence that B13 needs.
2. **ADR-019 — structure-aware representation:** index-time enrichment and section roles over verbatim stored spans.
3. **ADR-020 — retrieval method promoted after the frozen comparison.**
4. **ADR-021 — nominations and the EvidencePacket v1 authority boundary.**
5. **ADR-022 — bounded generative synthesis contract:** the claim schema, gates G1–G7, the disposition policy, and the ADR-009 outcome amendment.
6. **ADR-023 — semantic-support audit semantics:** CAL-aligned verdicts, advisory until calibrated.
7. **ADR-024 — RAG prompt-injection / untrusted-context boundary.**
8. **ADR-025 — public demo as reviewed recorded runs, with no standing paid endpoint.**

Numbers are provisional if the repository gains ADRs first. These are asset ADRs. ADR-015's "ADR-022" refers to a workspace-level decision, so write "workspace ADR-022" when citing that one.

---

# 12. What not to build yet

Explicitly deferred unless a measured failure activates them:

- custom biotech embedding fine-tuning;
- custom reranker training, or integrating a general reranker (MindGraph's gain did not replicate);
- GraphRAG / knowledge graph as the primary retriever;
- autonomous quality agents;
- workflow writes;
- model-generated document lifecycle/status;
- free-form agent tool use;
- live web search mixed into controlled-document answers;
- patient/clinical decision support;
- real client or employer documents;
- a single scalar "trust score";
- a live public generation endpoint;
- multi-turn conversation or query rewriting;
- a retrieval threshold tuned to refuse near-miss questions.

Bounded, authored cross-reference admission is in scope as a Slice 3 arm, following MindGraph's result. Graph retrieval as the primary retriever stays a separate falsifiable experiment after simpler retrieval is qualified.

---

# 13. Stop conditions

Stop or narrow the programme if any of these are observed:

- the benchmark cannot be made to fail both lexical and dense shortcuts;
- semantic retrieval gains disappear on frozen/prospective data;
- the refusal threshold requires unacceptable unsupported-answer risk;
- structure-aware parsing breaks provenance without compensating measurable gain;
- a reranker improves headline ranking while losing qualifier/exception evidence;
- the deterministic gates drop most generated claims on DEV, leaving little synthesis (narrow the claim schema or the scope before continuing);
- a semantic auditor cannot outperform a weak control on human-reviewed support cases;
- LLM judge agreement with human reviewers is too weak for the proposed use;
- blinded preference does not favour generated answers over extractive ones within the unsupported-claim ceiling;
- recorded-run generation cost per release makes regular updates impractical;
- security qualification exposes a source-policy bypass that cannot be deterministically contained.

A negative result is a successful experiment if it removes unnecessary architecture.

---

# 14. First execution wave

1. **Slice 0:** baseline freeze, the ADR-014 harness note, and the near-miss fixture.
2. **Owner action:** generate corpus v2 with the local generator against Appendix A and open the import PR (Slice 1).
3. **In parallel with step 2:** Slice 4 (nominations + packet on BM25 and the v1 corpus) and the Slice 5 gate suite with scripted generators. Neither needs a live model or a key.
4. **Slice 2** on the frozen corpus. Do not continue until the two-sided discrimination gate passes.
5. **Slice 3** retrieval arms.
6. **Slice 5** DEV-only live pass → freeze the rubric → **Slice 6** on TEST.
7. **Slices 7 and 8.**

A first public milestone can come before full qualification, because recorded runs are reviewed before publication. After Slice 5, a small curated set may be published, labelled as curated examples, with traps and at least one fallback included. Benchmark claims wait for Slice 6.

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

Adjacent public projects:

- Evidence Bundler, `eb-challenge-corpus-v1`: https://github.com/camerontjs-dot/evidence-bundler/tree/main/benchmarks/eb-challenge-corpus-v1
- Evidence Bundler, retrieval evaluator assurance RC1 results: https://github.com/camerontjs-dot/evidence-bundler/blob/main/docs/research/results-07-eb-retrieval-evaluator-assurance-rc1.md
- Evidence Bundler, retrieval assurance RC2 results: https://github.com/camerontjs-dot/evidence-bundler/blob/main/docs/research/results-13-eb-retrieval-assurance-rc2.md
- MindGraph, vNext retrieval plan: https://github.com/camerontjs-dot/MindGraph/blob/main/docs/VNEXT_RETRIEVAL_PLAN.md
- MindGraph, bounded graph admission decision: https://github.com/camerontjs-dot/MindGraph/blob/main/DECISIONS.md
- Claim Audit Lab v0.5.0: https://github.com/camerontjs-dot/claim-audit-lab/tree/v0.5.0

---

# 16. Research disposition

**Supported with bounds:** the industry and recent research support adding generative synthesis, semantic retrieval, fine-grained attribution, stronger evaluation, and a server-side trust boundary.

**Not established:** that semantic retrieval beats BM25 or hybrid at scale (ADR-014 is directional), or that hybrid/RRF, reranking, GraphRAG, agentic query planning, or custom model training improve this project's corpus.

**Strongest next evidence-producing step:** generate and freeze corpus v2 and benchmark v2, and show that the evaluator fails both lexical and dense shortcuts, before changing the public answer path. In parallel, build the EvidencePacket and the deterministic claim gates, which need no model to test.

---

# Appendix A — Corpus v2 specification

This is the contract for the externally generated corpus. The generator, its configuration, and its prompts stay outside this public repository. Only the generated corpus, its manifests, and its receipts are imported.

## A.1 Layout

```text
benchmarks/controlled-docs-v2/
  README.md                  synthetic-data boundary; runtime/evaluator split
  corpus/                    runtime; loads with `biotech-rag validate-corpus`
    documents/<DOC-ID>-<slug>.md
    metadata/<DOC-ID>-<slug>.yaml
  cases/                     runtime-visible questions
    dev_cases.jsonl
    test_cases.jsonl
  evaluator_only/            never mounted into a runtime
    gold/dev_relevance.jsonl
    gold/test_relevance.jsonl
    families.json            case -> case family, process area, tags
    relationships.json       supersedes / references / lags edges
    lexical_overlap.json     per-case overlap diagnostics
  adversarial/               separate corpus bundle for Slice 7
    corpus/documents/
    corpus/metadata/
    cases.jsonl
    evaluator_only/gold.jsonl
  corpus_manifest.json       generator identity, seed, as-of date, document list, counts
  SHA256SUMS
  freeze_receipt.json        tree hash, file hashes, PROSPECTIVE commitment
```

## A.2 Document contract

These rules match this repository's loader (`models.py`, `corpus.py`, `chunking.py`):

- Markdown, UTF-8 without BOM, LF line endings, trailing newline. No YAML front matter, no HTML, and no hidden or zero-width Unicode (the adversarial bundle excepted).
- `# <doc_title>` first; blank lines between paragraphs; `##` and `###` headings; tables and lists as contiguous blocks. The chunker splits on blank lines and headings.
- Sidecars contain exactly `doc_id`, `doc_title`, `doc_type`, `version` (quoted string), `status`, `effective_date`, optional `review_due_date` (not earlier than `effective_date`), `department`, `source_file_path` (relative to `corpus/`), and `source_hash` (`sha256:` plus the hex digest of the exact file bytes). The loader rejects extra fields, so family and relationship data go in `evaluator_only/`.
- `doc_type` is one of `SOP`, `Policy`, `TrainingNote`, `DeviationExample`, `CalibrationNote`, `Specification`, `TechnicalNote`. `status` is one of `Approved`, `Effective`, `Draft`, `Obsolete`, `Superseded`.
- At most one `Approved`/`Effective` version per `doc_id` (ADR-013). Predecessors are `Superseded` or `Obsolete`.
- New document IDs only; do not reuse v1 IDs.

## A.3 Content

- **Process areas (14):** environmental monitoring; deviations; CAPA; change control; document control; training and gowning qualification; equipment calibration; water systems; cleaning and line clearance; batch record review and QA disposition; supplier qualification and incoming materials; stability; temperature-controlled storage and shipping; complaints and returns.
- **Documents:** 2–4 retrievable documents per process area (an SOP plus a specification, work-instruction SOP, training note, or technical note), 40–45 in total; at least 10 superseded predecessors with changed values; 4 drafts proposing new values; 4 obsolete documents.
- **Length:** most SOPs 800–2,000 words; 3–4 long SOPs of at least 3,500 words and 20 sections; shorter training and technical notes.
- **Structure:** at least 15 Markdown tables across the corpus (limits, frequencies, tolerances, sampling plans, stability pull points, responsibilities); numbered procedures; nested sections; definitions; references; revision-history tables that mention superseded values.
- **Quantities:** on average at least 20 explicit quantities per process area (limits, ranges, durations, frequencies, counts, temperatures, percentages), each with units.
- **Near-miss seeds:** at least 2 named-but-unstated parameters per process area, for example "within the site-defined review period" or "the acceptance criteria in the product specification" where that specification is not in the corpus.
- **Identifiers:** document, equipment, room (with cleanroom grade), form, and material codes, used consistently across documents.
- **Cross-references:** at least 20 authored references between retrievable documents, 3 references to documents that exist only as Obsolete or Superseded, and 3 to documents absent from the corpus.
- **Authority lag:** at least 3 training notes that state an older value than their governing SOP.
- **Hard distractors:** paired concepts that share vocabulary (alert vs action limit, Grade A vs Grade B, purified water vs WFI, dirty vs clean hold time).
- **Conditions and negations:** "unless", "except", "only if", "is not required", "must not".
- **Synthetic boundary:** no organization, product, person, or site names that could be real; no values attributed to real regulations or guidance; no text from private repositories, employer documents, or client material; no workstation paths or usernames.

## A.4 Cases and gold

- About 40 DEV and 80 TEST cases committed; about 30 PROSPECTIVE cases sealed outside the repository, with only their SHA-256 committed.
- Case-family targets from the §6.2 table, with every family present in DEV and TEST.
- Runtime case fields: `case_id`, `split`, `question`, `query_style` (`natural`, `keyword`, or `identifier`), `aperture_id`, `top_k`, `schema_version`. Runtime files carry no family labels, gold, or rationales.
- Gold fields as in §6.2, with `offset_unit: "python_char"` and `span_text == text[char_start:char_end]`.

## A.5 Provenance and freeze

- `corpus_manifest.json` records the generator identity (name plus version or content hash), seed, as-of date, and a configuration hash. It contains no filesystem paths.
- If a language model assisted generation, record the provider, model ID, and a prompt hash. The frozen bytes are the corpus; regeneration is not required to reproduce them.
- `SHA256SUMS` covers every committed file. `freeze_receipt.json` records the tree hash and the PROSPECTIVE commitment.
- Corrections after freeze create `controlled-docs-v2.1`. Do not edit the frozen tree.

## A.6 Acceptance checklist for the import PR

- [ ] `biotech-rag validate-corpus benchmarks/controlled-docs-v2/corpus` passes (hashes, ADR-013), and so does the adversarial corpus.
- [ ] Every gold span round-trips, and every `required_facts` value appears in its span.
- [ ] Every `answer` case has a decisive span in a retrievable document; every `not_stated` case has material context and no decisive span in retrievable documents; every `refusal` case has neither.
- [ ] Every `forbidden_facts` value appears only in non-retrievable documents, revision-history sections, or distractor passages.
- [ ] Case-family counts and lexical-overlap caps meet §6.2, and no process area crosses splits.
- [ ] Runtime files contain no gold, family labels, or rationales.
- [ ] The publication-safety scan is clean: no paths, usernames, emails, real organization names, secrets, or hidden Unicode outside the adversarial bundle.
- [ ] `SHA256SUMS` verifies, the freeze receipt is committed, and PROSPECTIVE is sealed.
- [ ] Deviations from this appendix are listed in the README rather than silently absorbed.
