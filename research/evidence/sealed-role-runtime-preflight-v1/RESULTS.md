---
title: "Sealed-role runtime preflight: explicit denial falsified"
domain: "agent-operations"
type: "lab-report"
status: "completed"
lab_report_id: "2026-10-01-sealed-role-runtime-preflight-v1"
study_type: "confirmatory"
disposition: "reject"
source: "persisted deterministic sandbox probes"
tags: ["runtime", "apparatus-qualification", "negative-result"]
updated: "2026-10-01"
---

# Sealed-role runtime preflight: explicit denial falsified

**FALSIFIED.** The pinned Codex CLI sandbox candidate started in the intended
root and read the allowed file exactly, then read the explicitly denied outside
sentinel with exit code 0, empty stderr and its exact bytes on stdout. The run
stopped there. No research role or model request occurred.

## Question and decision

Can one concrete local runtime enforce the restricted initialization/file
aperture required for future sealed semantic roles? The preregistered decision
keeps those roles stopped when an explicit outside-file deny fails. This tests
execution machinery on random fixtures, not semantic validity.

## Candidate and procedure

Candidate `codex-0154-native-named-profile-v1` uses installed Codex CLI 0.154.0
on macOS 27.0, build 26A428, arm64. Its explicit sandbox `-P` profile declares
root/temp denial, minimal runtime reads, role-root writes and exact outside-file
denial, with network disabled. The loaded base user configuration's legacy
`sandbox_mode=danger-full-access` is recorded as material. Explicit profile
selection and actual enforcement are tested rather than assumed.

Freeze commit `511d016c9840ce77fc8be284d9c4f5202b910820`, tree
`b3a1f315da48e686b5475f35285b418f476a7d7b`, preceded every decisive probe.
`freeze.json` records clean checkout, source/config/protocol hashes and zero
prior decisive probes. The baseline exact policy SHA-256 is
`178a9b33f6e3d6be5d4c77ecbb5f06b9b457e384081c08a3b9998c7d746cad40`.

The intended aperture contains two random allowed files and a symlink to a
random denied sibling. All four fixture hashes were frozen; sentinel bytes were
absent from child argv, config, environment and expected-output text. The same
installed runtime command physically ran each probe. The supervisor supplied
only PATH and LANG; the CLI/shell added other variables recorded in P7.

One baseline configuration was exercised, with one call per completed probe.
The independent factor is the declared file access rule. Separately identified
mutation/name controls were frozen in advance and never executed after the
denial failure. No average overrides that failure.

## Direct results

| Probe | Calls | Observed | Result |
| --- | ---: | --- | --- |
| P7, root/environment | 1 | Exact role root, exit 0 | PASS for start directory |
| P1, allowed read | 1 | Exit 0, exact frozen bytes/hash | PASS |
| P2, explicit absolute outside read | 1 | Exit 0, exact denied bytes/hash, empty stderr | FALSIFIED |
| P3, traversal/sibling/symlink/temp alias | 0 | Stopped after P2 | NOT_RUN |
| P4, allow-rule mutation | 0 | Stopped after P2 | NOT_RUN |
| P5, opaque-name invariance | 0 | Stopped after P2 | NOT_RUN |
| P6, full model initialization | 0 | No model/canary request | UNKNOWN / NOT_RUN |
| P8, enforcement review | 0 further calls | Static invocation plus persisted output | Required denial not enforced |

The exact allowed stdout SHA-256 is
`aa2d6e24dd7584f5d0cea82a2bc4ca7fa624b4411b195eef3eac25af2716a3d9`.
The exact denied stdout SHA-256 is
`ade99ce766cf90c6147f66ed6b56c515f6cdb4ed399f778befc9973d1e05cefd`,
matching the denied fixture frozen before execution. This demonstrates an actual
read/leak, rather than a guessed value or an unrelated read failure.

**Verification receipts:** `probes/P1.json`, `probes/P2.json`, `probes/P7.json`,
`probe-run.json` and `custody-check-after-run.json`. Raw streams/config/fixture
bytes remain in private custody; `private-custody-index.json` binds their hashes.
P7's public stream substitutes private paths/operator metadata before publication
and preserves the original stream and receipt hashes. P1/P2 stdout bytes are
public-safe random sentinels. No frozen source or policy was rewritten.

## Irregularities

Pre-freeze discovery used an obsolete `sandbox macos --help` shape; the outer
sandbox refused its attempted nested sandbox application. This supplied no
fixtures and is not a file-isolation result. Actual installed help established
the generic command used by the frozen adapter. Its combined setup output and
separate-stream observability limit are preserved in `setup-discovery-attempt.json`.

Other setup deviations concern session-router option use, restricted GitHub/uv
access, one automatic-review timeout, and two source style findings repaired
before freeze. `deviations-before-freeze.json` preserves them. Six construction
checks, candidate-only Ruff and structural contract lint passed before freeze.
There was no post-freeze source/configuration repair, valid-probe retry, model
canary or scientific rerun.

## Interpretation and limits

Observed: the required outside deny failed with valid unchanged fixtures and
unchanged candidate/runtime/configuration. All 15 frozen candidate files and all
36 predecessor records passed physical hash checks afterward.

Disposition: **FALSIFIED** for this entire pinned runtime/configuration. The
failure is not reclassified as apparatus-invalid because another configuration
might work. Root start-directory success establishes only the start directory.

Cause remains UNKNOWN. Interaction with the loaded legacy setting and policy
selection/translation are possible explanations; this experiment does not
identify an OS-wide Seatbelt defect. The child reports `CODEX_SANDBOX=seatbelt`,
which does not establish effective deny-rule enforcement. No real-model context,
training-history independence, semantic independence, network isolation or
production sandbox suitability is supported. Planning-only MindGraph retrieval
was confined to the broad-context owner and supplied no data to the fixture.

## Disposition and next experiment

Keep case author, A/B/C, semantic assessor and ledger reducer stopped. The
smallest next evidence-producing step is a separately frozen runtime candidate
with auditable effective configuration, including resolved legacy-setting
precedence, followed by fresh sentinel preflight. Do not retry this identity as
if unchanged settings could erase the failure. PR #30's semantic sequence remains
unchanged and unexecuted.

No project generation, G1-G7 replay, protected payload access, CAL integration,
ADR-018/rubric change, promotion, merge or release occurred. Wave B remains LOCKED.
