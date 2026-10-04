# Independent CI review: product #45 and proof #46

## Disposition

**Product #45: QUALIFIED_READY_FOR_OPERATOR_PROMOTION.** No blocking technical defect was found in the bounded CI change at `bc457271bc9a29fbe5561dfcba6b3b398df09616`.

**Proof #46: SUPPORTED_FOR_PROMOTION**, limited to independent CI evidence surfaces. On its frozen research tree, failing Ruff and physically executed pytest, compile, corpus, and parity commands coexist in one completed workflow.

The explicit operator promotion gate on [PR #45](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/45) remains. This review does not authorize a merge. Appending evidence to [PR #46](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/46) preserves the identity of its earlier decisive run. [Issue #40](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/40) defines the acceptance boundary.

## Hosted observations

The review read run metadata, actual job/step states, and decoded logs for **26 jobs: 4 predecessor + 11 proof + 11 product**, on 2026-10-04. All three runs are completed pull-request events, attempt 1.

| Run | Aggregate result | Physical observations |
| --- | --- | --- |
| [37023159772: predecessor](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/runs/37023159772) | Failure | Ruff found 298 errors on each Python version. Tests, Compile, and Corpus smoke were skipped on 3.11/3.12/3.13. Independent parity passed 40/40. |
| [37137560112: proof #46](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/runs/37137560112) | Failure | Ruff found 298 errors and exited 1. All ten other jobs succeeded. pytest reported 189 passed and 1 warning on each Python version; compile/corpus ran on all three; parity passed 40/40. |
| [37137557939: product #45](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/runs/37137557939) | Success | All eleven jobs succeeded. Ruff was clean. pytest reported 113 passed and 1 warning on each Python version; compile/corpus ran on all three; parity passed 42/42. |

Every corpus execution reported 10 valid documents, 2 excluded by status, and validation passed. Every compile execution logged `python -m compileall src` and source-directory traversal. [hosted-receipts.json](hosted-receipts.json) preserves selected original log lines, step states, job/source URLs, and SHA-256 hashes for the excerpts.

The proof timing is additionally discriminating: Ruff exited 1 at **16:38:19 UTC**; the Python 3.11 corpus job checked out at **16:38:51 UTC** and completed validation at **16:39:02 UTC**. Other jobs had already completed. The claim concerns independence within the same workflow, not simultaneous execution of every command.

Product and research counts belong to different trees. The research test results do not validate its scientific or semantic conclusions.

## Exact identity and change boundary

| Role | Reviewed head | Hosted synthetic merge checkout |
| --- | --- | --- |
| Product #45 | `bc457271bc9a29fbe5561dfcba6b3b398df09616` | `13e0d253d37071839709b9e86bf2f09dde7c1d11` |
| Proof #46 | `7196aec48378932e2dde235b560ddaff56a814dc` | `0a04fb6f606cd0633f6e07f79bf6302b4e5e2e67` |
| Research predecessor | `1e3d79a53f181c79bdeeb6137e88ae2897797106` | `21f3c854c8c3b2055c4d9c16c8ad8b078a7c2355` |

All three hosted checkout trees equal their respective head trees exactly; every job log confirms the relevant checkout. [identities.json](identities.json) preserves full tree hashes, parents, run metadata, and GitHub metadata endpoints.

The product is one commit directly on `main@cd9ba8bc4351ac0cb4cf022ec1ddf449671454c3`; proof is one commit directly on the research predecessor. Both diffs change only `.github/workflows/ci.yml`: **51 insertions, 4 deletions**. The before workflow blob is identical on both bases, `bf31d9543919847171ab5eaf39fdb82221bb5eb2`; the after blob is identical on both candidates, `e6a9886621e36f255ad6e9f9e88b9e9bfdb7a00d`.

## Implementation and compatibility

The maintained change preserves all original verification commands, installation steps, triggers, and the entire parity job. There is no `continue-on-error`, `needs`, conditional `if`, or concurrency cancellation setting. pytest, compile, and corpus matrices retain `fail-fast: false` and Python 3.11/3.12/3.13. Structural comparisons and `git diff --check` passed; [static-verification.json](static-verification.json) records the checks.

Five job definitions expand to eleven jobs, compared with four before. Repeated environment setup produces independent results without custom orchestration, a lint waiver, or research-code promotion. This is the narrow maintained change surface justified by the separate evidence results; it is not a claim of the shortest possible YAML spelling.

Ruff environment execution is explicitly consolidated to Python 3.11. Its existing `target-version = "py311"` and rules remain unchanged. Cross-version Ruff installation execution is consolidated; pytest, compile, and corpus retain all three versions. CI check names change. Product source, package configuration, corpus, tests, and semantic behavior are unchanged by #45.

## Operator gate

The live records reserve promotion:

- [PR #45 comment 5971207812](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/45#issuecomment-5971207812): “This PR stays Draft until an operator promotes it to main.”
- [Issue #40 qualification comment 5971207277](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/40#issuecomment-5971207277): “Merging #45 onto main is an operator promotion, not part of this qualification.”
- [Issue #40 closure comment 5971207409](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/40#issuecomment-5971207409): “Merge of #45 is a separate promotion.”

At the review observation, #45 was open/Draft with no submitted reviews or inline threads. Main's branch endpoint reported protection disabled and required-check enforcement off with empty contexts/checks; repository rulesets were empty. [authority.json](authority.json) preserves the dated observation. That configuration does not clear the explicit operator gate.

**Recommendation:** authorize the bounded #45 promotion, refreshing head/base/check state if either moves before the decision. Until authorized, retain #45 as Draft. Closing the completed proof unmerged is consistent with preserving the evidence.

## Reconstruction

[summary.json](summary.json) separates observations, review inference, and merge authority. `SHA256SUMS` covers every other file. Run `sha256sum -c SHA256SUMS` from this directory to verify it.

The [before workflow](workflow-before.yml), [after workflow](workflow-after.yml), and [product diff](product-diff.patch) allow direct comparison. `git hash-object workflow-before.yml` and `git hash-object workflow-after.yml` reproduce the recorded blob IDs. The immutable Git identities and hosted endpoints support further reconstruction.

This review does not repair Ruff debt, qualify research semantics, authorize a production feature/release, or establish that the split workflow is already on main.
