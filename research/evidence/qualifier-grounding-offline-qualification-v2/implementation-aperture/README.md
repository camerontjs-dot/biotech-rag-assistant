---
title: "Minimal ledger v2 implementation aperture"
domain: "research"
type: "handoff"
status: "designed"
source: "frozen qualifier-grounding-policy-v2 and qualifier-grounding-interface-v2"
tags: ["ledger", "implementation", "aperture"]
updated: "2026-09-30"
---

Use a genuinely fresh implementation context. Give it only `CANDIDATE.json`
from this directory and byte-identical copies of the two normative files named
there, plus ordinary engineering conventions. Copy the allowed sources into a
plain isolated directory; do not give it the whole source checkout or its
history, which contains public qualification answers.

The separately authorized task is to implement one smallest deterministic pure
`decide(assessment_ledger) -> decision_record` under that frozen contract.
Decisions depend on structure and supplied declared assessments only. No
models/providers, external services, hidden prose, fixture reads, expected
answers, historical case material, identifier lookup, environment/path answer
injection or manufactured semantic judgments are allowed.

Before revealing controls or expectations, complete ordinary implementation
checks, inspect dependencies and runtime access, commit, record exact
commit/tree and file hashes/environment/exposure status, and verify a clean
checkout. Do not modify the reducer after reveal and qualify it as the same
candidate. Stop on contamination or missing authority.

This packet deliberately provides no acceptance cases, answers, outcome
patterns, predecessor reducer, preparation checker or scorer. Its unbound
candidate fields state NOT_IMPLEMENTED / NOT_RUN. A later qualification owner
may read the full preregistration only after the implementation freeze. This
preparation task performs no implementation or qualification run.

The result can establish only the tested ledger contract. Materiality, semantic
support and decomposition-safety assessment of natural-language source text
remain unqualified. Wave B remains LOCKED. No generation/G1-G7, protected
payloads, CAL, ADR-018 changes, promotion, merge or release.

> **Binds:** future separately authorized v2 implementation owner
> **Tier:** T0 (information aperture instruction; no OS isolation claimed)
> **Check:** record supplied file hashes, actual exposure and clean candidate freeze
> **Escape:** stop with CONTAMINATED or missing-authority disposition; do not substitute another answer source
