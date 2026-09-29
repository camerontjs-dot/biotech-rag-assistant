# Slice 5B — exploratory live generation on DEV only

Status: apparatus protocol before the first live-model generation output.

## Objective

Use a real model to discover generation failure types on DEV-only evidence packets before freezing
the generation rubric.

This is exploratory. It cannot promote generation or establish TEST performance.

## Parent authority

Slice 5A:
- PR #12
- qualified head: 2f5bfb966963ed4f8fcc8dd147acfc75a78e8f5c
- disposition: PASS_SCRIPTED_GENERATION_GATES
- scripted receipt artifact: 11062800411
- scripted receipt digest:
  sha256:4063dc4f0ab6e585dc177c548a8118d44b218e8748690d1fe12ca14509dbf7e8

The live model receives only serialized EvidencePacket objects plus the fixed generation prompt.
It receives no corpus, gold, family labels, evaluator rationales, retrieval implementation, or web
access.

## Two waves

### Wave A: code-grounded probes

Nine probes from the plan's section 1.8:

1. analytical-balance acceptance range near-miss;
2. gowning-requalification absence near-miss;
3. controlled-copy use-period near-miss;
4. environmental-monitoring action-limit near-miss;
5. deviation-closure interval retrieval refusal;
6. purified-water action-limit retrieval refusal;
7. supported control: daily balance check weight count;
8. supported control: line-clearance signatories;
9. obsolete membrane-filtration trap.

Wave A is the first live pass.

### Wave B: benchmark DEV

All 44 committed v2.1 DEV questions, using their runtime fields only.

Wave B is exported now but is not run until Wave A outputs are reconciled and the live-generation
apparatus is shown to preserve the packet boundary.

## Generation prompt

For each case, the model is told:

- use only the supplied EvidencePacket;
- do not use outside knowledge;
- do not infer a missing value;
- return exactly the GeneratedAnswer JSON schema;
- citations must copy exact substrings from admitted chunk text;
- use not_stated + a topic-cited gap when the approved evidence names the topic but omits the
  requested fact;
- use insufficient_evidence when the packet contains related material but cannot support the
  requested answer;
- answer only with claims supported by the packet;
- output JSON only.

The prompt text and SHA-256 are frozen in the exported bundle.

## Empty packets

Cases with zero admitted nominations are marked generator_should_be_called=false.

The live generator must not be invoked for those cases and must not produce an output row for them.
The evaluator records the public result as refusal.

## Isolation

Preferred execution:
- export the bundle from the exact apparatus head;
- copy it to a scratch directory containing no repository checkout;
- run generation from that scratch directory;
- do not grant the generation context filesystem access outside the bundle;
- do not grant retriever, web, shell or other tools to the generation model where the provider
  supports disabling them.

For this exploratory pass, a local agent may orchestrate provider calls, but the model-facing
context must contain only the per-case packet and frozen prompt.

Record provider, exact model ID, parameters/effort, client/runtime identity, and whether each case
used a fresh model context.

## Output

The live run writes outside Git:

- outputs.jsonl:
  - case_id
  - raw_output: the model's JSON-compatible object
- run_metadata.json:
  - provider
  - model_id
  - parameters/effort
  - prompt_sha256
  - bundle_manifest_sha256
  - isolation notes
  - per-case fresh-context policy

Raw provider text may additionally be archived locally but is not required in the public repo.

## Evaluation

The repository evaluator:
- verifies bundle and prompt hashes;
- rejects output rows for empty packets;
- replays every model output through the exact G1-G7 engine;
- reports public disposition, accepted/dropped claims, gate issues and fallback reason;
- for Wave A only, compares the structural/public disposition with the preregistered probe class;
- preserves raw failures.

No semantic-support score is frozen in Slice 5B. Human inspection of accepted claims is the purpose
of the pass.

## Stop rule

After Wave A:
- preserve all raw outputs and gate results;
- classify observed failure types;
- do not repair model outputs;
- do not tune the prompt and call the same run comparable;
- decide whether apparatus/prompt changes are required before Wave B.

TEST and sealed PROSPECTIVE remain untouched.
