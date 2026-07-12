# EB + CAL integration & sync — ready plan

status: plan (not executed; gated). The *decision* is recorded — this is the operational detail it points to.

Authority (do not restate or contradict these here):
- **Workspace policy:** root `ADR-022` (MainFrame `DECISIONS.md`) — shared components are reused via
  pinned git submodules under `workbench/components/<name>`, canonical = each component's
  projects-root working copy (= its GitHub repo), kept current by Dependabot `gitsubmodule` bump-PRs.
- **This asset's application:** `DECISIONS.md` `ADR-015` — when the integration phase needs them,
  vendor `evidence-bundler` (EB) and `claim-audit-lab` (CAL) here per ADR-022; supersedes the
  by-reference-only stance of ADR-001/ADR-006 for the integration phase.

This doc adds the operational layer: where they plug in, the concrete steps, the open decisions, and
the order — so the work is ready to execute once the gates clear.

## Integration points (the why)

- **EB → client-corpus onboarding / ingest.** EB already does deterministic ingest into chunk
  records, provenance preservation, review sidecars, finalization, and coverage reports that surface
  gaps. The onboarding slice (ADR-011) is a bespoke version of exactly this. Target: refactor the
  onboarding layer to consume EB behind the existing `onboard-corpus` contract — same
  `mapped_cleanly/excluded/needs_review/rejected` states out, EB doing the ingest/provenance work.
- **CAL → answer-grounding auditor (generative phase).** Today's citation check is *structural*
  (`citation_resolves_to_retrieved_chunk`, ADR-007/009). When an LLM writes answers (deferred; see
  the ADR-014 semantic slice), CAL provides the *semantic* check — supported / overstated /
  missing-source / limitation. It sits behind the answer contract; outcomes stay `answer`/`refusal`.

The contract boundary is unchanged: EB/CAL sit at the ingest and answer-grounding *edges*; the
deterministic trust controls (status gating, citation validation, refusal, current-version
invariant, audit) remain this asset's own. ADR-001's "local controlled-document models" still hold.

## Concrete steps (when gates clear)

1. Publish `workbench/` to its own **private GitHub repo** (also the Pages prerequisite — see
   `docs/DEPLOY.md`). Required before submodules/Dependabot can run (ADR-022 §5).
2. Add the **EB submodule** at `workbench/components/evidence-bundler`, pinned to a release **tag**
   (ADR-022 §3), mirroring `scaffold-claims-study/workbench/components/`.
3. Make EB importable: `pip install -e components/evidence-bundler` (or add its path), and refactor
   the onboarding layer onto it. Keep the trust suite green (`pytest`, 24-case trap suite, the
   natural-language suite). This reverses ADR-006's "no package dependency" → record it in the ADR
   that wires the submodule (ADR-015 is the direction; the wiring commit is the new record).
4. Add `.github/dependabot.yml` (`package-ecosystem: "gitsubmodule"`) so EB bumps arrive as
   reviewable PRs (ADR-022 §4). **No auto-merge** — review + green trust suite before merge.
5. Add the **CAL submodule** with the generative phase, not before (ADR-015 gate 3: no dormant
   submodules). Wire CAL as the grounding auditor behind the answer contract.

## Open decisions (resolve at execution)

- **EB first** (now-relevant; the onboarding slice exists to refactor) vs CAL first (gated behind the
  deferred generative phase). Lean: EB first.
- **Pin granularity:** release tag (ADR-022 target state) — needs EB/CAL to cut tags. Until tagged,
  do not vendor (gate 2).
- **Onboarding refactor scope:** thin adapter over EB vs deeper replacement of the bespoke slice.
  Lean: thin adapter first, keep `onboard-corpus`'s output contract identical so tests are the
  regression guard.

## Gates (don't vendor yet)

Per ADR-015, all three must hold before wiring: (1) this asset is on GitHub; (2) EB and CAL are
stable and **tagged** (they are mid-revision now — "Im currently also fixing those"); (3) there is
real consuming code (no dormant submodules). Also: `scaffold-claims-study` should gain a Dependabot
config and move its EB pin from `main` to a tag (ADR-022 consequence) — do that alongside, so both
consumers follow one policy.

Until the gates clear, the assistant keeps reusing EB/CAL discipline by reference (ADR-001).
