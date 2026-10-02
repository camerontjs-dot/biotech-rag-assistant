---
title: "Request-bound semantic adjudication v2 terminal result"
domain: "ai-systems"
type: "experiment"
status: "completed"
updated: "2026-10-02"
source: "issue #37; frozen PR #30; TERMINAL.json"
tags: ["semantic-adjudication", "apparatus-invalid", "request-custody"]
---

# Request-bound semantic adjudication v2 result

The experiment terminated **APPARATUS_INVALID** during the first case-author
request. The harmless structured-output canary passed. The first frozen author
partition then timed out at 1,800 seconds without a provider response. There is
no frozen 44-packet corpus or adjudicated expectation set. The question about
PR #30's semantic design remains unresolved.

The [terminal record](TERMINAL.json), [timeout receipt](calls/author-01/receipt.json),
[exact author request](calls/author-01/request.json), and
[call counts](call-counts.json) preserve the observation. There was one canary
attempt and one author attempt, with zero retries. The remaining 27 author
partitions were not called. Seven slots were requested in the first partition;
zero packets were received or materialized. A/B/C, raw comparison, reconciliation,
and every seeded/invariance/mutation assurance check remain **NOT_RUN**.

## Frozen apparatus and authority

Live GitHub reconciliation verified the requested branch at exactly PR #30's
publication head `d1e092b7cdb878d064735d597e8c3b2d6c710157`, before any additions.
The package's 31 artifact hashes, six launches, rubric and manifest matched the
frozen preparation. Failed predecessors #32/#34/#36 were closed without merge
and contributed no execution mechanism to this runner.

The [apparatus freeze](APPARATUS-FREEZE.json) binds source commit
`e73eb5ac55380dea3b0d958bd523546db05d88ba`, tree
`0f93d6947e28beef3f9ef0822501672f395ad4ca`, and 68 artifact hashes. The
[semantic execution freeze](SEMANTIC-EXECUTION-FREEZE.json) binds the verified
canary before the first semantic request. The pre-run README remains a preserved
description of that preparation; this result and TERMINAL.json govern disposition.

Provider: local Ollama `0.34.4`, `/api/generate`. Author/canary model:
`qwen3-coder:30b`, provider-reported digest
`06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`.
Parameters: temperature 0, seed 37030, top_k 1, top_p 1.0, repeat_penalty 1.0,
num_ctx 65536, num_predict 16384; raw=true, stream=false, keep_alive=0.
Live provider metadata observed the same digest and context length during the
author call. The model was absent from `/api/ps` after the timeout and client close.

The [request custody check](request-custody-check.json) reconstructed both sent
requests byte-for-byte, verified the raw canary response and preserved the author
response's absence. Eight fake-transport/adversarial controls and pinned Ruff
0.16.5 passed before freeze. These checks establish their stated transport and
structure properties; they do not establish semantic adequacy.

## Failure, deviations and limits

The [failure ledger](failures-and-deviations.json) records the timeout. No raw
author response hash or parsed output hash exists because the runner received
neither. Provider-side progress and the cause of the latency remain UNKNOWN.
Increasing the timeout, changing model, revising the partition or repairing an
output was not attempted. Any such change needs a separately authorized experiment.

Pre-freeze supervisor permission, lint and receipt-collector corrections are
preserved in [the deviation record](pre-freeze-deviations.json). The semantic
design and exact request aperture did not change after freeze. Complete local
model-inventory metadata contains unrelated machine paths and remains preserved
locally with exact hashes under the declared publication exclusions. All decisive
serialized requests, the returned canary response, the timeout receipt and the
selected provider/model identity are public artifacts.

There is no conclusion about materiality, entailment, contradiction, silence,
ambiguity, coverage, guards, shared errors or relation fidelity. Hidden provider
context, training independence and independent human validation remain UNKNOWN.
No semantic assessor was implemented or qualified; no v2 reducer, project
generation or G1-G7 replay ran. No Wave B/TEST/PROSPECTIVE access, CAL integration,
ADR-018 change, promotion, merge or release. **Wave B remains LOCKED.**
