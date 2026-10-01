---
title: "Semantic adjudication v1 isolation stop"
domain: "ai-systems"
type: "experiment"
status: "aborted"
updated: "2026-10-01"
source: "issue #31; frozen PR #30 preparation; supervisor prelaunch probes"
tags: ["research-infrastructure", "adjudication", "apparatus-invalid"]
structural_type: "project-log"
lifecycle_scope: "workbench"
owner_surface: "qualifier-grounding-semantic-adjudication-v1"
authority: "project-status"
privacy: "public-safe"
volatility: "stable"
source_of_truth: true
update_rule: "immutable terminal evidence; publication records append only"
verification: ["frozen preparation validator; terminal artifact hash/custody check"]
do_not_use_for: ["semantic rubric validity", "accepted labels", "assessor qualification"]
---

# Semantic adjudication v1 isolation stop

> **Binds:** custodians of this execution record
> **Tier:** T0
> **Check:** none for semantic validity or role independence; hash/structure checks are separate observations
> **Escape:** preserve this terminal attempt and use a separately identified successor for execution

**APPARATUS_INVALID**, before case authoring. The proposed local execution adapter
failed its leaf-file isolation preflight: a harmless outside sentinel remained readable
when its exact file was explicitly denied. No case-author, adjudicator, semantic-assessor
or project-generation model was invoked. This attempt provides no evidence about the
rubric's semantic validity.

Execution authority: [issue #31](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/31).
Frozen preparation: [PR #30](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/30),
closed without merge at `d1e092b7cdb878d064735d597e8c3b2d6c710157`, tree
`2e20396777f4bb5d074b4ce8aeb5d89f0685750e`. The exact rubric, package and predecessor
bytes remain unchanged. This execution adds records in a separate directory.

## Observed isolation boundary

Seven exact allowlisted case-author files were copied into a plain isolated directory.
Three deterministic initialization renders were supervisor diagnostics. The first
included automatic generic skill metadata; explicit per-skill overrides suppressed
that catalogue in later renders. The last render showed only generic permissions,
the isolated environment and the frozen neutral instruction, with memory and project
instructions disabled. A rendered prompt is neither a role launch nor an audit of a
complete model request.

The physical sandbox checks then exposed a different limitation:

- [Probe 1](runtime/probe-1.json) used the wrong working-root option placement and
  is an invalid probe; it is preserved rather than used to decide the stop.
- [Probe 2](runtime/probe-2.json) read both the local rubric and the outside sentinel
  under the proposed minimal-read/isolated-write profile.
- [Probe 3](runtime/probe-3.json) still read the outside sentinel with an added root deny.
- [Probe 4](runtime/probe-4.json) printed `READ_DENIAL_SENTINEL` and `inside=0 outside=0`
  despite an explicit deny entry for that exact outside file.

The [relative reproduction template](runtime/probe-template.json) identifies the tested
CLI 0.154.0 command and permission settings. [Preflight summary](runtime/preflight-summary.json)
records what was observed and what remains unknown. Curl DNS failures in early probes
are not treated as proof of network isolation. The private diagnostic originals contain
local paths and remain preserved separately; safe derived records and hashes are public.
There is no author/adjudicator raw response or transcript to publish.

## Terminal interpretation

The supervisor withheld every role launch because the proposed adapter did not establish
the required aperture. This is a bounded execution-machinery failure under the frozen
`APPARATUS_INVALID` rule for incomplete required adjudication machinery. It does not
establish that every possible adapter is incapable of providing fresh contexts.

No role received forbidden material, so no role contamination is asserted. The broad
supervisor's existing conversation, workspace and memory were never impersonated as a
fresh author or adjudicator. [Independence dimensions](independence.json) record the
unachieved/unknown boundaries separately; no independent human judgment occurred.

## Downstream evidence

| Surface | Observed state |
| --- | --- |
| Input-only corpus | NOT_AUTHORED; 0 packets; hash null, against 44 planned |
| Case-author/A/B/C | NOT_RUN; zero role launches; no fabricated execution receipts |
| Raw A/B agreement | [NOT_TESTED by dimension and category](raw-agreement-NOT_RUN.json) |
| Complete disagreements | NOT_RUN; count null rather than an asserted zero |
| Reconciliation / open adjudication | NOT_RUN / NOT_ENTERED |
| All eight invariance and eight mutation relations | [All 16 NOT_RUN](relations-NOT_RUN.json) |
| Seed/category/guard/shared-error assurance | [NOT_TESTED](assurance-NOT_RUN.json) |
| Required expectations | All unadjudicated; no accepted expectation freeze or hash |

The [role records](roles/) distinguish the materialized author aperture from the
unmaterialized A/B/C apertures. Author hypotheses and endpoint relations were never
created or revealed. Zero denominators carry no perfect-agreement claim.

## Custody and remaining work

[START.json](START.json) preserves the initial experiment manifest.
[EXPERIMENT.json](EXPERIMENT.json) records the aborted attempt.
[TERMINAL.json](TERMINAL.json) binds the terminal artifacts and disposition.
[Receipts](receipts/) preserve live GitHub authority and the physical frozen preparation
checks. [Deviations](deviations.json) preserve setup failures separately from the blocking
probe. No predecessor evidence or executable source was modified.

The smallest next evidence-producing step is a separately identified adapter preflight
that demonstrates and inventories an auditable fresh role aperture, including denial of
an outside sentinel read. Only after that succeeds should a newly identified execution
attempt launch the unchanged sealed author/A/B/reconciliation/assurance sequence.

No semantic assessor, reducer, project generation, G1-G7 replay, Wave B,
TEST/PROSPECTIVE access, CAL integration, ADR-018 change, promotion, merge or release
occurred. **Wave B remains LOCKED.**
