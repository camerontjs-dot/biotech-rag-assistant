---
title: "Semantic assessor controls v1 preparation"
domain: "ai-systems"
type: "experiment"
status: "designed"
updated: "2026-10-01"
source: "issue #29; PR #28 frozen qualification lineage"
tags: ["research-infrastructure", "preregistration", "semantic-assessment"]
---

# Semantic assessor controls v1 preparation

This package preregisters a 44-packet synthetic semantic-assessment screen and its
independent annotation assurance. The experiment is **designed / NOT_RUN**. No case
author, adjudicator, semantic assessor, project generator or reducer ran in preparation.
No accepted natural-language labels exist yet.

The unresolved question is whether an assessor can identify material claim obligations
and their bindings, judge admitted BODY support/contradiction/silence/ambiguity, represent
complete material content, and judge the six guards for a proposed partial-support core.
The [v2 reducer qualification](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/28)
supports its tested symbolic ledger contract only. This package preserves that candidate
and every predecessor artifact without retesting them.

```text
claim + authorized BODY text
    ↓  THIS FUTURE SCREEN
semantic assessment
    ↓  declared projection; no new semantic inference
assessment ledger
    ↓  qualified v2 reducer (unchanged)
decision record
```

## Frozen design

- [Rubric](rubric.md): explicit material assertions/facets, scoped BODY relations,
  coverage and tri-state decomposition guards. Its separate freeze precedes case design.
- [Case construction](case-construction.md) and [inventory](case-design.json): 28 anchors,
  eight invariance variants and eight material mutations; author hypotheses remain sealed.
- [Adjudication and assurance](adjudication.md): separate A/B fresh contexts, preserved
  raw judgments, explicit disagreement ledger, optional blind C and attributed open
  adjudication; raw agreement, seeds, mutations and invariance all constrain acceptance.
- [Future qualification](qualification.md): dimension scores, exact endpoint requirements,
  safety vetoes, unresolved-denominator rules, frozen candidate and one call per packet.
- [Ledger projection](ledger-projection.md): no downstream semantic oracle or BODY authority
  from QUERY/HEADING/METADATA; composite BODY proofs retain source constituents.
- [Schemas/validator limits](SCHEMAS.md): six closed machine formats and mechanical
  structure/custody checks. No semantic scorer, author/adjudicator launcher or assessor.
- [Experiment](EXPERIMENT.json), `package-manifest.json`, `rubric-freeze.json` and
  append-only `freeze.json`/`TERMINAL.json` bind preparation identities and checks.

The [six launch packets](launches/) cover case author, A, B, reconciliation,
assessor implementation and qualification reveal. Each has exact allowed files,
forbidden data, freeze/contamination conditions and required receipt. Future artifact
slots are explicitly unmaterialized, with null hashes. They must be identity-bound
before a separately authorized launch; their presence grants no execution authority.

## Structural verification

From a checkout of the frozen preparation, using Python >=3.11:

```sh
python -m pip install -r research/semantic-assessor-preparation-requirements.txt
python -m unittest discover -s research -p test_semantic_assessor_preparation.py -v
python research/check_semantic_assessor_preparation.py --root . --check --require-freeze --receipt preparation-check-new.json
```

Use a new receipt filename each time. These commands run the real pinned JSON Schema
backend and custody checks only. Their structural-token fixtures do not create semantic
control expectations. The dedicated hosted preparation job checks the new source and
package separately from inherited repository CI findings. Frozen predecessor lint is
preserved; no semantic disposition may be inferred from a green structural job.

## Decision and next evidence

Preparation readiness means the rubric, protocols, schemas, inventory and apertures
are frozen and structurally checkable. Semantic accuracy, independently adjudicated
labels, assessor performance, human independence and training-history independence
remain unestablished. Agreement can still reflect shared error. All future judgments
and their evaluator are under test.

Execution authority for this preparation is [issue #29](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/29).
The next task is a separately authorized sealed case-author/A/B/reconciliation/assurance
sequence. Stop before assessor implementation if that apparatus is inconclusive,
contaminated or invalid. Wave B remains **LOCKED**. No generation/G1-G7 replay,
TEST/PROSPECTIVE access, CAL, ADR-018 change, promotion, merge or release is authorized.
