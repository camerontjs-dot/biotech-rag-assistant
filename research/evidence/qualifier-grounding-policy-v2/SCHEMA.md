---
title: "Ledger v2 control encoding"
domain: "research"
type: "spec"
status: "frozen"
source: "qualifier-grounding-policy-v2 and qualifier-grounding-interface-v2"
tags: ["ledger", "schema", "controls"]
updated: "2026-09-30"
---

This is encoding guidance. `policy.json` defines semantics; `interface.json`
defines the exact input and output schemas and referential constraints. Those
two files govern any disagreement. No natural-language claims are needed.

The author writes these artifacts in a new `fresh-controls/` directory:

- `inputs.jsonl`: one input object per line, with `case_id` and `ledger`.
- `expectations.jsonl`: one complete decision record per input, keyed by the
  same case ID. Include every required diagnostic field and a nonempty reason.
- `controls.json`: object with `schema_version: qualifier-grounding-controls/v2`,
  `set_id`, and `controls`. Each entry has `case_id`, `purpose`, `tags`,
  `negative_strategies`, and `invalid_input` (boolean). A deliberately malformed
  ledger is allowed only when marked `invalid_input: true`, and its expectation
  must be an apparatus failure. Keep the outer case ID valid for scoring.
- `pairs.json`: object with `schema_version: qualifier-grounding-pairs/v2`,
  `set_id`, and `pairs`. Each pair has `pair_id`, `left`, `right`, `relation`,
  `purpose`, `compare_fields`, `must_change`, and `renaming`.
- `AUTHOR.json`: context creation, input allowlist and SHA-256 identities,
  actual reads, forbidden exposure declaration, method and limitations.
- `freeze.json`: set ID, timestamp, SHA-256 of the five files above, and the
  author's contamination status. Do not include this file in its own hash map.

Every ID is an opaque string. Use original structures, different numbers of
obligations and combinations of witnesses. Input array order is unconstrained;
output arrays must be sorted and unique. All positive full-claim records retain
all material obligation IDs, as specified in the policy.

Pair relations have these exact encodings:

| Relation | Required comparison |
| --- | --- |
| `INVARIANT` | Every path in `compare_fields` equals across endpoints. Ignore case ID and reason. `must_change` is empty; `renaming` is empty. |
| `RENAMED_INVARIANT` | Map every left-side case/obligation/witness ID using `renaming`, then sort identifier arrays and compare every selected field. `renaming` contains `case_ids`, `obligation_ids`, `witness_ids` objects; `must_change` is empty. Enum values and reasons are never renamed. |
| `SENSITIVITY` | Every path in `must_change` differs and every path in `compare_fields` remains equal. `renaming` is empty. Do not compare unspecified fields. |

Paths are dot-separated object keys, such as `apertures.P` or
`diagnostics.local_apertures.N`. Select whole arrays by their field name.
Invariant pairs should compare every required output field except `case_id` and
`reason`. A pair must have two distinct existing endpoints and a nonempty
purpose. Pair relations supplement exact per-control correctness and never
replace it.

Expectations are authored hypotheses from declared symbolic assessments, with
`evaluator=agent_llm` and `needs-audit` provenance. Schema validation does not
establish semantic truth or qualify a reducer. No reducer or answer generator
belongs in this package.

Structural profile: workbench encoding specification; public-safe; owner is
the v2 normative package; source of truth for encoding only; immutable after
normative freeze; syntax/custody checks plus author review are its verification.
