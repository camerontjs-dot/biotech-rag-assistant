---
title: "Semantic preparation schemas and validator boundary"
domain: "ai-systems"
type: "workflow"
status: "preregistered"
updated: "2026-10-01"
source: "issue #29; rubric v1"
tags: ["schemas", "custody", "research-preparation"]
structural_type: "verification"
privacy: "public-safe"
update_rule: "immutable after preparation freeze"
---

# Semantic preparation schemas and validator boundary

**Trigger:** mechanical package or future packet checks, without semantic execution.
**Stop state:** PASS_PREPARATION_STRUCTURE_ONLY / PASS_STRUCTURE_ONLY,
STRUCTURAL_INVALID, or CHECK_UNAVAILABLE. These are structural check states.
**Owner surface:** `qualifier-grounding-semantic-assessor-controls-v1`.

## Schema and custody rules

> **Binds:** custodians and consumers of these machine formats
> **Tier:** T1
> **Check:** `research/check_semantic_assessor_preparation.py --check`; its structural falsifier tests
> **Escape:** preserve STRUCTURAL_INVALID or CHECK_UNAVAILABLE; do not supply invented labels or hashes

All six schemas use JSON Schema draft 2020-12. They are separate files so a clean
implementation or adjudicator packet need not expose sealed design/relation formats.

| Schema | Content |
| --- | --- |
| case.schema.json | Input-only case, exact claim/BODY custody, optional nonauthority distractors and core/gap projection; no extra fields. |
| annotation.schema.json | Explicit node IDs/kinds/claim/scope anchors, parent/dependency graph, MATERIAL/UNKNOWN, complete atomic BODY relation matrix and optional joint proofs, COMPLETE/UNKNOWN coverage, uncertainty/exclusions and applicable guards with justifications. |
| author-design.schema.json | Sealed 44-slot assignment, categories, seed hypotheses and guard opportunities; excluded from adjudicator inputs. |
| relations.schema.json | Sealed 16 endpoint/family relations with anchor maps, changed ranges and author hypotheses; excluded from adjudicator inputs. |
| disagreements.schema.json | Raw A/B hashes, pointers, values and evidence, dimension, mechanical-resolution eligibility and explicit reconciliation state. |
| launch-receipt.schema.json | Context/initialization/exposure/output identity, role/tool/human identity, each independence dimension, counts and deviations. |

Hash exact text as UTF-8 without normalization. `input_sha256` is the case object's
canonical JSON UTF-8 hash: keys sorted, no extra whitespace, Unicode unescaped,
separators comma and colon. Separately hash complete raw JSONL files, including
line endings and frozen case order. Offsets are Unicode code points, not UTF-8 byte
offsets. No duplicate JSON keys or NaN/Infinity constants are permitted.

The validator physically imports pinned jsonschema, compiles the schemas locally and
checks field types/unknown fields, hashes, exact evidence spans, allowed BODY references,
node references/cycles, atomic matrix completeness, structural applicability fields,
and supplied corpus slot/endpoint assignments. It rejects external schema references
before resolution. It imports no project generation, provider, reducer, scorer or
adjudicator code. No natural-language interpretation occurs.

`validate_corpus` checks in-memory future cases/design/relations against the frozen
inventory; the CLI's --kind checks single artifacts. Future corpus freezing must call
this structural function in a separately recorded mechanical harness. No author or
adjudicator launcher, semantic scorer or automated semantic alignment is shipped here.

The validator does not prove: materiality, sentence/clause count, privacy, meaningful
boundary selection, complete semantic coverage, inference validity, mutation semantics,
guard truth, honest exposure receipts, actual context isolation or independent human
judgment. False-but-well-typed labels can pass. Those dimensions require the separately
preregistered apparatus assurance. Structural selftests contain only uninterpreted
tokens and symbolic labels, not authored natural-language evaluation controls.

Exit 0 is the named structural pass; exit 1 means structural findings; exit 2 means
the check could not run (including unavailable backend or input). Every CLI invocation
requires a new receipt path and writes it exclusively, preserving prior receipts.
Fresh experiment stage/call counts remain zero even when structural checks run.
