# Biotech RAG: GitHub work and local execution

This is the 2026-10-04 handoff snapshot for [programme #39](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/39). The issue and successor PR discussions own subsequent status. The [closed convergence archive](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/52) preserves the preceding programme; it is not a branch to merge.

## Prepared successors

| Candidate | Exact publication | Status and use |
| --- | --- | --- |
| [Citation #53](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/53) | `a3250910cf7ad3b67f37b5fd27e977c840fefd40` | Draft; explicit authorized bounds only. Full final CI passes 164 tests per Python version and 42/42 Pages parity. |
| [Authoring #54](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/54) | Source `513cf0629b20a8d876e161f32f8bc6c6549e2012`; tree `6428495c4f3b373cd07bdebcc7916834c157da3f` | Draft; source for the fresh local authoring task. The PR's later evidence/workflow head preserves these three source/protocol/test files byte-for-byte. |

Authoring source SHA-256: `74e16e97341bb90d8845ba9f7bd78c03257b97ec79ff6a575b299ca7d3f97450`. The local reviewed commit is `d1b256347d320e6268506b00978168c2d32b65ce`; publication metadata differs, while the whole source tree is identical. Read [the copyable local supervisor task](local-authoring-task-20261004.md) and the final #54 CI receipt before execution.

## Objective and current product boundary

The maintained assistant is a controlled-document retrieval and extractive-answer pilot. Its source-status, version, hash, provenance, refusal, API and CLI controls are useful independently of generation. The present work prepares two bounded successors needed by the generative research programme. It does not declare that programme finished or introduce a production semantic assessor.

| Work | Owner and execution surface | Completion boundary |
| --- | --- | --- |
| Validate citation selection using explicit authorized offsets | Citation successor PR; Chat/GitHub | Exact quote/body contract, preserved automatic-selector failures, separate review, maintained regression and CI |
| Enforce frozen author assignments | Research successor PR; Chat/GitHub | Exact case/design/relation schema and structural acceptance; offline transport and corruption tests; dedicated CI |
| Recover runtime and available capacity | Local supervisor | Actual provider/model/digest, resource headroom and schema-feature canary recorded before author calls |
| Author a new corpus | Local request-bound runtime | One frozen response per partition; exact source custody and complete 44-case/16-relation freeze, or preserved terminal failure |
| Blind A/B adjudication, reconciliation and semantic assurance | Separately prepared isolated requests after corpus freeze | Frozen PR #30 protocol, full denominators and uncertainty; no current execution claim |
| Heading-grant experiment | Issue #49 after an adequate semantic route | Separate preregistration with heading/body/source binding and mutation controls |
| Semantic assessor and generated-answer successor | Later bounded research/product work | Separate implementation, evaluator and actual interface evidence |
| Biotech integration with EB/CAL | Later explicitly pinned integration experiment | Producer/contract/consumer evidence; upstream success alone is insufficient |
| CI PR #45 promotion | Operator gate on #45 | Explicit authorization followed by refreshed exact-head checks and normal merge |

## Immutable starting evidence

- Main inspected at `cd9ba8bc4351ac0cb4cf022ec1ddf449671454c3`.
- [#52 convergence publication](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/21bc5a583016a6b5e5178f4534016c6101c9a6b1/research/evidence/programme-convergence-20261004): `21bc5a583016a6b5e5178f4534016c6101c9a6b1`.
- [#50 rejection evidence](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/4191e9b7809f76956330f0c01312ccdb09f8055e/research/evidence/citation-sentence-selection-review-20261004): original subject `9685872827b37b55c981b88ad3177a2ed3b13533`; publication `4191e9b7809f76956330f0c01312ccdb09f8055e`; `NOT_QUALIFIED`.
- [#51 failed corpus freeze](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/7556badf6077bac2edd20f163faa5af0ef1b95d1/research/evidence/semantic-control-memory-bounded-20261003/corpus-freeze-20261004): `7556badf6077bac2edd20f163faa5af0ef1b95d1`; 44 rows, 33 unique assigned slots, 11 missing, ten failed materializations; `APPARATUS_INVALID`.
- Research successor base: `1e3d79a53f181c79bdeeb6137e88ae2897797106`. It retains the frozen #30 package and #38 apparatus without inheriting a repaired #51 corpus.
- [#30 frozen rubric and protocols](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/6f6e90b75f160370116a22c1c342231d9d14008d/research/evidence/qualifier-grounding-semantic-assessor-controls-v1) remain semantic authority. Their artifact hashes are checked by the existing preparation validator.

The PR discussions pin the prepared successor commits and their verification receipts. A source qualification and a later documentation/evidence commit are distinct identities; do not call a later tip the tested source unless its relevant bytes were checked.

The automatic citation successor at published `8ddd2a8969869be5e5dfe339b45087f1ee7e8803` (local equivalent `093fcd031138b8219722f4e9c888dec2d7ebc354`) also failed separate review: two of 32 frozen probes crossed paragraphs, and six further probes reproduced abbreviation-driven condition truncation and paragraph crossing. The replacement helper requires explicit `authorized_start` / `authorized_end` bounds; without them it refuses. It validates exact containment, not linguistic completeness. An upstream boundary provider and maintained caller integration remain unqualified. The historical automatic tests are preserved as their original contract, not relabeled as passing explicit-bound tests. [Draft #53](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/53) retains the final review and a portable reproducer: 15 exact selections and 36 safe refusals, with the raw 49/51 label score and its two documented reviewer expectation errors preserved.

## Local supervisor task

Use a clean new worktree from the exact research candidate cited by its PR handoff. Execute the commands in the [authoring protocol](../research/semantic-author-slot-boundary-v1-protocol.md). Inspect worktree status and running work before making local changes. Preserve unrelated dirty files and active sessions. This task neither takes over nor stops the EB thread. If its work occupies the required provider or memory, record the conflict and wait for a free execution slot; do not kill its process.

The supervisor may inspect this plan, code and historical evidence. The semantic author is a different role and receives only the frozen request bytes through the no-tool local runner. Do not send this plan, the chat, GitHub discussion, old authored rows, prior outcomes or a repository checkout to that role.

### 1. Verify the prepared source

Fetch the PR branch, resolve the exact handoff commit and check its ancestry and working-tree state. Run the new structural suite and frozen preparation/custody checks using the documented dependency pins. Preserve stdout, stderr, exit status, source commit/tree and dependency/runtime identities. A recreated local failure is evidence; do not silently replace the prepared candidate and label the changed code the same qualification.

### 2. Establish the actual local runtime

The previous run's runtime is a lead, not a current fact: Ollama `0.35.1`, `qwen3.5:9b`, digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. That run used more than one context/output configuration, including 16,384 and 18,432 context tokens. Earlier 14B/30B attempts and large allocations failed; do not launch the inherited #38 30B configuration by default.

Inventory the current selected provider/model, loaded context, available memory, resident use and swap. Keep a complete private inventory local; publish only the selected configuration and bounded resource receipts. Define the admissible memory/context/output/time budget before decisive calls. The changed schema changes request size, so old prompt-token measurements cannot qualify the new requests.

Before any provider generation, including the canary, use `prepare` and commit/publish the complete generated configuration, requests, assignment plan and `EXECUTION-FREEZE.json` as required by the protocol. Then run the new nonsemantic schema-feature canary and measure request/context/output headroom. A syntactically valid one-field response does not demonstrate support for the successor schema's positional constraints. Reported prompt token counts also do not prove the provider consumed untruncated input; preserve separate runtime evidence or retain visibility as `UNKNOWN` and semantic readiness as `NOT_READY`. Keep canary outputs separate from authoring. Preserve any timeout, malformed response, unsupported feature or resource stop; do not increase memory/context limits to make the same failed run pass.

### 3. Freeze and execute fresh authoring

Follow the successor protocol and its executable commands. The exact configuration, all prospective requests, assignment plan and source/apparatus identities must already have been frozen and published before the canary. Use a new run directory. After that canary succeeds, preserve one request and one returned response per assigned partition, including raw bytes and hashes. No retry, response editing, row renaming, reassignment, merging with #51 output, or favorable selection between attempts.

After each response, require the new structural acceptance receipt before advancing. A transport-only pass is insufficient. A structural or custody failure terminates this run and leaves downstream work `NOT_RUN`.

Only after every required partition succeeds may assembly reconstruct all 44 cases and 16 relations, check exact correspondence against the unchanged inventory, and freeze the three corpus files with hashes. A partial file set or legal row count is not a valid full freeze. The complete freeze establishes corpus structure and custody only; semantic validity is still unknown.

### 4. Stop at the next scientific boundary

Return a verified new corpus freeze or a durable terminal blocker. Keep A/B/C, reconciliation, semantic assurance and assessor qualification `NOT_RUN` in this authoring task. Prepare the next isolated adjudication handoff under the exact frozen #30 apertures; do not improvise a scorer, synthesize expected labels, or use the supervisor as a blind adjudicator.

At every outcome, preserve BM25, A07's negative result, A08's bounded result, heading exclusion, Wave B lock, TEST/PROSPECTIVE restrictions and unrun Biotech integration. No merge, release, branch deletion, history rewrite or product promotion belongs to this local task.

## Required return

Post one concise receipt on the research successor PR and link it from #39. Include source and apparatus identities; actual model/runtime/configuration; canary and resource results; request/response/attempt counts; complete, missing and invalid partition counts; all raw artifact hashes; corpus freeze identities or explicit nulls; deviations and first failure; each downstream `NOT_RUN` state; achieved and unknown independence dimensions; and the next evidence-producing action.

Retain public-safe machine evidence in a new bounded repository evidence directory. Do not publish credentials, local user paths, unrelated runtime inventories or private documents. Preserve complete private raw evidence locally where required and identify any hash-only publication limit honestly.

## Promotion note

[#45's explicit gate](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/45#issuecomment-5971207812) reserves promotion for the operator. The qualified head is `bc457271bc9a29fbe5561dfcba6b3b398df09616`; no authorization to merge it is inferred from the request to prepare local testing. This gate does not block work on the two successor branches.
