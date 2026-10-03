# Evidence Room-guided semantic grounding recovery

status: active research plan (not production authority)

Tracking:
- parent programme: #39
- semantic-control recovery: #41
- A08 citation sufficiency: #42
- A07 packet completeness: #43
- CI observability: #40

## Why this plan exists

The promoted Evidence Room changes the working diagnosis for Biotech RAG.

The strongest current evidence does **not** support reopening retrieval selection as the next move.
Biotech's retained BM25 baseline remains the clean experimental control:

- DEV reranking produced descriptive gains;
- TEST reranking also improved point estimates;
- the preregistered TEST promotion boundary still retained BM25;
- cross-project MindGraph evidence includes a bounded reranking gain and a disjoint non-replication.

The active problem is downstream of retrieval:

```text
retrieval relevance
→ packet/source authority
→ material proposition completeness
→ citation sufficiency
→ semantic support assessment
→ generation
```

Frozen Wave A evidence separates two failure classes:

- **A07**: packet-level grounding defect. The admitted BODY evidence does not contain the complete
  material proposition.
- **A08**: citation-span insufficiency. The packet BODY contains the missing condition, but the
  quoted citation does not.

These must not be repaired in one combined experiment.

## Preserved research lineage

Do not rewrite these records:

- PR #19: accepted bounded heading-authority decision.
- PR #20: `MIXED`; A07 packet defect and A08 citation insufficiency.
- PR #24: falsified qualifier reducer v1.
- PR #28: v2 symbolic reducer `SUPPORTED_FOR_LEDGER_CONTRACT`.
- PR #30: frozen semantic-control design; semantic experiment NOT_RUN.
- PR #32: filesystem isolation apparatus invalid before semantic authoring.
- PR #34: denied outside sentinel readable; runtime candidate falsified.
- PR #36: second runtime candidate falsified on the same required denial.
- PR #38: request-bound successor `APPARATUS_INVALID`; canary passed, first seven-slot author
  request timed out after 1,800 s, zero authored packets, later stages NOT_RUN.

An apparatus failure is not a product-semantic failure.

## Sequence

### 1. Recover the semantic-control corpus (#41)

Keep PR #30's semantic design fixed.

Use request-bound role isolation rather than filesystem/sandbox isolation.

The execution successor may change only what is required to obtain the frozen controls:

- provider/model/runtime;
- request partition size/layout;
- timeout policy, frozen before decisive author calls.

Preflight response/output budget with a small representative request, then freeze the complete
partition schedule. Do not repeat the known seven-slot/1,800-second failure without changing the
responsible factor.

Each role call is stateless and receives only its authorized serialized request. Preserve request
bytes, response bytes, hashes, model/provider/runtime identity and all timeouts/malformed outputs.

Do not implement a production semantic assessor until this phase reaches a terminal corpus/
expectation result.

### 2. Test A08 citation sufficiency (#42)

One factor only: citation span.

Hold the exact claim, packet membership, source identity, authority/status rules, BM25 baseline and
ADR-018 heading authority fixed.

Compare the historical quote with the smallest larger authorized BODY span that contains the
pre-run condition.

Primary question: can the exact claim become quote-supported without changing packet evidence?

A positive result supports citation-span selection/expansion only.

### 3. Test A07 packet completeness (#43)

One factor only: bounded same-section BODY expansion.

Hold BM25, query/case, source authority, status/current-version gates, EvidencePacket provenance and
heading authority fixed.

Do not use the heading as implicit semantic evidence.

Required controls include:

- historical A07 aperture;
- bounded same-section BODY expansion;
- a same-section negative control where the missing proposition remains absent;
- stale/held-out trap;
- provenance reconstruction for every added span.

If same-section BODY expansion fails, an explicit heading-semantic grant is a **new experiment**,
not a repair inside #43.

## CAL boundary

Current CAL must not be used as the answer-grounding solution for this plan.

Live CAL pressure evidence at plan creation:

- convergence candidate #186: `6bb0d60f3e2286123f56de5657de4e97d6374c63`;
- pressure record PR #189 head:
  `6d1e673e9446710f0f4bbe196945f2f023420f1c`;
- terminal pressure disposition: `PRESSURE_FALSIFIED_CRITICAL_SEMANTIC_FAILURE`;
- critical counterexample: a positive comparison claim was returned `supported` from admitted
  evidence containing explicit negation.

CAL integration may resume only after a separately qualified semantic successor clears the
relevant failure, followed by a new Biotech-specific integration experiment.

EB remains a separate ingest/onboarding opportunity.

## CI signal (#40)

Research CI should preserve independent signals.

Do not waive Ruff. Split lint from pytest/compile/corpus smoke so inherited lint debt cannot prevent
those checks from physically running and producing evidence.

A bulk lint cleanup is separate maintenance.

## Experiment outcomes to retain

For every successor preserve:

- exact candidate/base/tree identities;
- protocol and frozen changed factor;
- request/source/corpus hashes;
- model/provider/runtime identity where material;
- positive, negative, inconclusive, timeout and NOT_RUN results;
- machine result separate from semantic review;
- author/independent roles separate where independence matters;
- nonclaims;
- Evidence Room intake-ready terminal receipt.

## Promotion boundary

Wave B remains locked until the relevant prerequisite actually passes.

No TEST/PROSPECTIVE access, CAL integration, retrieval-method promotion or public generative-answer
promotion is authorized by this plan.

## Decision after #41–#43

Use the evidence to choose one next product lane:

1. citation-span selection/expansion;
2. packet BODY expansion;
3. semantic-assessor implementation;
4. continued refusal/abstention because support is not safely recoverable.

Do not preselect the winner.
