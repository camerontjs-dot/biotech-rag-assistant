---
title: "Independent ledger reducer implementation aperture"
domain: "research"
type: "experiment"
status: "active"
source: "issue #23 and frozen policy/interface"
tags: ["grounding", "offline", "qualification"]
updated: "2026-09-30"
---

The implementation reduces declared assessments only. It has no imports and no
runtime dependency on any repository file. The case identifier is an opaque
passthrough; the implementation checks its type and presence, never its content.

The implementation context read issue #23, policy.json, interface.json,
CANDIDATE.json, and experiment identity/state fields. GitHub PR #22's prose was
filtered out; only identity, status, and lineage metadata were exposed. Required
workspace operating contracts and ordinary project configuration were read.
MindGraph was queried with lexical retrieval only; only grouped path metadata was
exposed. Broad project coordination text, historical anchors, controls,
expectations, pair definitions, preparation checker/tests, and prior outcome
traces were deferred. Frozen artifact bytes were hashed without parsing or
displaying their payloads to reconcile the supplied authority.

Implementation choices made before reveal:

- QUOTE witnesses authorize Q; BODY witnesses authorize N/P only when the
  corresponding aperture is declared. Every obligation is assessed, including
  declared attachment or presupposition obligations.
- Contradiction takes precedence over entailment. Ambiguous packet BODY
  assessments withhold. Unknown coverage/materiality withholds. Invalid integrity
  or structure stops with apparatus failure.
- Support for every obligation in P separates packet grounding from citation
  sufficiency. Incomplete quote/nomination coverage holds for a citation witness
  while retaining packet support.
- A core proposal requires every declared guard to be true, exhaustive disjoint
  core/gap sets, authorized BODY witnesses covering the core, and retention of
  every supported obligation. Unknown guards withhold; false guards or inconsistent
  proposals reject decomposition.
- core_ids identifies an accepted core proposal. A complete claim is represented
  by KEEP_FULL/HOLD_FOR_CITATION rather than a newly manufactured core proposal.
  Rejected proposals do not populate core_ids. gap_ids records known missing
  packet support, except when coverage/materiality or BODY ambiguity is unknown.
- Identifier lists are normalized by sorting. All output state follows ledger
  structure and declared assessments; no natural-language judgments are inferred.

The ordinary local tests use synthetic one-obligation and core/gap ledgers
derived from these declarations. They do not import the qualification apparatus.
The decisive controls and scoring have not run at this checkpoint.

Operating deviations: MainFrame's broad README/log/decision reads were deferred
under the explicit information aperture. Its hygiene initializer rejects Git
worktrees because .git is a file; the existing staged-only hook template is
activated per commit through core.hooksPath without changing another checkout's
configuration. The initial cached-linter call hit sandbox cache permissions;
the cached linter was then run with approved access. No oracle material was read
to resolve either environment issue.
