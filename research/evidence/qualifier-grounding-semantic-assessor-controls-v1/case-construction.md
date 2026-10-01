---
title: "Semantic control construction protocol v1"
domain: "ai-systems"
type: "workflow"
status: "preregistered"
updated: "2026-10-01"
source: "issue #29; rubric v1"
tags: ["controls", "research-preparation"]
structural_type: "workflow"
privacy: "public-safe"
update_rule: "immutable after preparation freeze"
---

# Semantic control construction protocol v1

**Trigger:** separate authorization to launch the sealed case-author packet.
**Stop state:** a frozen corpus and sealed author hypotheses, or an invalidity/
contamination receipt. No case author is launched by this preparation.
**Owner surface:** `qualifier-grounding-semantic-assessor-controls-v1`.

## Rules and procedure

> **Binds:** the future case author and corpus custodian
> **Tier:** T0
> **Check:** none for semantic case quality; `check_semantic_assessor_preparation.py` checks structure/custody
> **Escape:** preserve incomplete authoring as NOT_READY; changed recipes require a successor before adjudication

Author exactly 44 packets: 28 distinct anchors, eight invariance variants, and eight
material mutation variants. The frozen `case-design.json` assigns every slot and
relation endpoint recipe. This is a compact discrimination screen; family dependence
and one anchor per category preclude population reliability estimates.

Use synthetic public-safe material only. No patient, client, operator or private
document content. Use commonplace activities and invented names, objects and events;
no predecessor wording, scenario structure, historical model output, or A07/A08 labels.
The custodian checks historical separation after corpus freeze without revealing
predecessor content to its author. The author receives no repository,
history, memory, historical evidence, provider output, or assessor implementation.
Record synthetic provenance; no external retrieval is needed or allowed.

Keep each claim at most 60 whitespace-delimited words and three assertion clauses.
Keep total admitted BODY at most 180 words and at most four spans. Distractors total
at most 60 words. The limits permit combined-span controls without domain inference.
Use explicit names, event labels, time windows and units where they carry the contrast.
Use no unstated regulatory, medical, causal or probabilistic rule. Ambiguous controls
must describe the ambiguity in sealed design notes, not smuggle it into every case.

Each packet contains only an opaque UUID case ID; exact claim and its UTF-8 hash;
one to four authorized BODY spans with opaque witness/source IDs, exact text/hash and
source-span custody; optional explicitly nonauthoritative QUERY/HEADING/METADATA text;
and an optional proposed core with a supplied explicit gap. A BODY span is a complete
synthetic source fragment, with source start 0 and end equal to its code-point length.
Its source hash equals its text hash. Source admission is fixed by the packet, not
inferred from a descriptive header. IDs cannot encode categories or desired labels.

Do not include design category, seed flag, mutation family, partner ID, author intent,
expected relation, final action, reducer output, or prior result in an adjudicator input.
The neutral packet schema rejects additional fields. The presence of a distractor
identifies its nonauthority; it does not identify a desired answer.

Construct the 28 anchors first. Every safety distinction designated explicit in the
inventory must be stated overtly, with no competing reading depending on hidden facts.
These are seeded opportunities for the rubric to fail, not author-certified answers.
Record an author hypothesis and exact contrast anchors in a separate sealed design file.
The author must not create accepted expectations or run the reducer/adjudicators.

For invariance, rename all linked entities by a bijection; reorder whole independent
sentences or BODY witnesses; use a truth-conditional paraphrase; or duplicate exact text
under new opaque IDs. For mutation, change only the designated claim feature, leaving
BODY fixed unless the recipe explicitly requires a bound renaming. Record every changed
range, old/new text, obligation alignment hypothesis, and the intended semantic difference.
Check variant length limits. No post-adjudication editing, replacement, cherry-picking,
or silent case deletion is permitted. A failed recipe gets a successor corpus.

Separate an input-only `cases.jsonl` from sealed `design.json` and `relations.json`.
The latter contains endpoint IDs, family, a bijective anchor/obligation correspondence
for invariance or a changed-feature map for mutation, and explicit relation dimensions.
These maps are hypotheses until adjudicated; they cannot force labels. Require at
least two instances of each invariance family, and one of each mutation family.
All variants and endpoint maps are frozen before A/B receive any cases.

The author/custodian records the complete transcript hash, allowed-file hashes,
case/design/relation hashes, case count and order, receipt, implementation identity
if any mechanical builder is used, and contamination status. Random UUIDs and one
fixed corpus order are frozen once. Preserve provenance describing who selected cases.
Tests of this package use uninterpreted structural tokens only; they are not controls.

## Guard and uncertainty coverage

The safe-core anchor must allow all six TRUE guards. Negative projections across
binding, antecedent, exception, dependent-removal, unsupported-core and incomplete-gap
anchors must supply an explicit FALSE opportunity for each of the six guards; a guard
can co-fail another when logic requires it. Record those opportunities in sealed design.
The guard-unknown anchor must have determinate original partial support but genuinely
uncertain proposed-core semantics, allowing at least one UNKNOWN guard. The coverage-
unknown anchor must expose unresolved claim extraction/binding while the distinct
genuine-ambiguity anchor concerns BODY interpretation. These additional anchors avoid
conflating uncertainty about claim coverage, BODY support and a proposed projection.

## Verification and outputs

Future structural validation checks packet/schema purity, unique IDs, hashes, exact
spans, inventory counts, relation endpoints and authorized evidence references. It does
not establish materiality, semantic mutation/invariance, or privacy by itself. The
custodian reviews provenance and exact text for privacy and historical-copy violations.
The resulting corpus identity is FUTURE_NOT_AUTHORED in this preparation. Accepted
annotations remain FUTURE_NOT_ADJUDICATED. Hashes remain null until real artifacts exist.
