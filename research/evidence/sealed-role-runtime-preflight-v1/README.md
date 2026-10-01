---
title: "Sealed-role runtime isolation preflight v1"
domain: "ai-systems"
type: "research"
status: "designed"
source: "issue #33; installed runtime; deterministic supervisor probes"
tags: ["runtime", "information-aperture", "apparatus-qualification"]
updated: "2026-10-01"
structural_type: "verification"
lifecycle_scope: "workbench"
owner_surface: "research/evidence/sealed-role-runtime-preflight-v1"
authority: "deterministic-source"
privacy: "public-safe"
volatility: "stable"
source_of_truth: true
update_rule: "append-only"
verification: ["construction-checks.json", "CANDIDATE.json", "PROTOCOL.json"]
related_surfaces: ["issue #33", "PR #32"]
do_not_use_for: ["semantic acceptance", "production sandbox claims"]
---

# Sealed-role runtime isolation preflight v1

This package tests one installed Codex CLI 0.154.0 sandbox mechanism with an
explicit named permission profile. The predecessor stopped before research roles
because an explicitly denied outside sentinel remained readable. This successor
qualifies the runtime boundary directly on unrelated random fixtures.

The frozen candidate and probe plan are in `CANDIDATE.json` and `PROTOCOL.json`.
The exact policy is supplied through `-c` and selected through sandbox `-P`.
The loaded base user configuration has a legacy sandbox setting; its relevant
value and private snapshot custody are recorded explicitly. Profile selection
is an input under test, not an assumption that denial is enforced.

`adapter.py` physically invokes the installed runtime. `run_probes.py` checks
candidate/fixture custody, writes every raw result before classification, and
stops at the first required-property failure. Mutation and filename controls
have separately identified policy hashes fixed before execution.

No semantic material is in the temporary fixture. The role root has no Git
history, project files, memory or sibling evidence. No research context or
model is launched. Initial model-request content and other unobservable client
behavior remain `UNKNOWN`; shell sandbox success alone cannot establish clean
model initialization.

> **Binds:** this candidate and its one deterministic qualification run
> **Tier:** T0 (preregistered research boundary; no generic role-launch gate)
> **Check:** persisted physical probe receipts and exact candidate/fixture hashes
> **Escape:** preserve failure; report FALSIFIED, INCONCLUSIVE or APPARATUS_INVALID; do not launch a research role or alter this frozen candidate

This package is append-only after freeze. Results and terminal/publication
receipts are added separately. The entire predecessor remains unchanged.
Private bindings, raw initialization/configuration snapshots and absolute local
paths stay in supervisor custody; public paths are logical fixture-relative
identities with raw-stream hashes. Nothing here supports semantic independence,
training-history independence, network isolation, OS-wide security or production
sandbox suitability. Wave B remains LOCKED.
