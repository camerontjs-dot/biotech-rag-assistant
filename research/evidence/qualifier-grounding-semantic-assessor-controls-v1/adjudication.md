---
title: "Independent semantic adjudication and apparatus assurance v1"
domain: "ai-systems"
type: "workflow"
status: "preregistered"
updated: "2026-10-01"
source: "issue #29; rubric v1"
tags: ["adjudication", "independence", "apparatus-assurance"]
structural_type: "workflow"
privacy: "public-safe"
update_rule: "immutable after preparation freeze"
---

# Independent semantic adjudication and apparatus assurance v1

**Trigger:** separately authorized A/B launches after corpus freeze.
**Stop state:** an immutable expectation set acceptable for the bounded screen,
INCONCLUSIVE, CONTAMINATED, or APPARATUS_INVALID. Execution is NOT_RUN here.
**Owner surface:** `qualifier-grounding-semantic-assessor-controls-v1`.

## Rules and sequence

> **Binds:** future adjudicators, reconciler, custodian and qualification owner
> **Tier:** T0
> **Check:** none for independence or semantic accuracy; structural/custody checks are separately specified
> **Escape:** record unknown independence or unresolved judgments; withhold apparatus acceptance

1. Verify rubric/package freeze, corpus custody, packet purity, and the authorization
   for this later stage. Materialized launch manifests replace named future slots with
   exact file hashes. Reject missing slots; do not widen their allowlists.
2. Initialize A and B as separate fresh contexts with no copied conversation, memory
   retrieval, repository/history access, or automatic project-context load. Each sees
   only its own launch, rubric, individual frozen case packets, and annotation schema.
   Store initialization instructions and actual exposures. Root/system/tool context
   must be inventoried; 'fresh' by label alone is not adequate.
3. Have each annotate all 44 cases once, including explicit uncertainty. Do not expose
   design notes, relations, categories, seeds, expected actions, or the other's output.
   Persist raw outputs, per-case structured annotations, transcript and receipt hashes
   before any comparison. Invalid/missing output remains evidence; no silent repair.
4. Compute the raw A/B agreement measures below. IDs provide references only.
   Canonical node keys are (kind, sorted claim anchors, sorted scope anchors, parent
   ASSERTION anchor key). Compare scope dependencies through those keys. Evidence
   anchor text/offsets must validate. Reasons and alternative valid proof groups do
   not need identical wording, but each proof must pass later evidence review.
5. Preserve a disagreement ledger over the union of node keys and dimensions. An
   unmatched node is extraction disagreement, not a dropped denominator row. Record
   A/B values, anchors each relied on, dimension, rubric clause, mechanical resolution
   eligibility, outcome, and need for third/operator judgment.
6. Mechanical reconciliation may normalize opaque IDs, ordering and exact duplicate
   reference spelling only. It cannot infer semantic equivalence, choose a preferred
   boundary or witness, or majority-vote. Freeze its map and preserve raw values.
7. For semantic disputes, launch a third fresh adjudicator only under later explicit
   authorization. The default blind C receives the same rubric/case/schema and no
   A/B reasoning, design notes or desired result. Persist C before opening reasoning.
   A C judgment matching one side is evidence, not an automatic 2-to-1 verdict.
8. A named reconciler may then enter the preregistered OPEN_ADJUDICATION phase,
   seeing preserved A/B/C reasoning and the rubric/case. Every accepted resolution
   needs a clause-based explanation and actual BODY anchors; unresolved dimensions
   remain UNRESOLVED. Record if the resolver is an agent or human. Operator judgment
   is explicit and attributed; an absent human cannot be recorded as human agreement.
9. Only after judgments/resolutions freeze reveal sealed author design and
   relation hypotheses to an apparatus reviewer. Compare intended contrasts to the
   independently derived labels and evidence. Author intent never overrides judgments.
   Semantic equivalence and mutation maps need explicit review, even when A/B agree.
10. Freeze accepted expectations, exclusions, alignment maps, individual judgments,
    raw agreement, seed/family checks and independence limitations before launching
    any future assessor implementation. No candidate implementation participates in
    annotation, reconciliation or expectation selection.

## Agreement measures and denominators

Report counts, not just rates, both over all packets and each sealed semantic category.
Ignore only opaque ID/order differences and unrestricted reasons. For raw agreement:

| Dimension | Measure |
| --- | --- |
| Overall | Exact case agreement on node keys/scope graph, materiality, single-span relation matrix, coverage, applicability, projection partitions and applicable six guards; denominator 44. |
| Obligation boundaries | Symmetric node agreement: 2 times shared node keys / total A plus B node keys; plus counts of unmatched nodes and split/merge disputes. |
| Materiality | Equal MATERIAL/UNKNOWN labels over union keys; unmatched keys are disagreement. |
| BODY relation | Equal labels over union obligation keys × admitted atomic witnesses. Missing cells disagree. Report four-class symmetric agreement 2 times same-class cells / (A class count + B class count), confusion counts, aggregate conflict and ambiguity separately. |
| Coverage | Exact COMPLETE/UNKNOWN agreement; denominator all 44. |
| Decomposition | Applicability exact over cases with supplied projection; per-guard exact TRUE/FALSE/UNKNOWN agreement over union REQUIRED cases, with missing/inapplicable on one side counted as disagreement. Report each guard and each value count. |
| Semantic category | Exact cases and each dimension within the category; variants inherit anchor category and may also be counted under their mutation family. These groups overlap and are not pooled as independent samples. |

A zero denominator is NOT_TESTED, never perfect agreement. Obligation matching does
not score free-text meaning by string similarity. Evidence review rejects a rationale
that changes the structured proposition's bindings even if labels happen to match.

Raw thresholds are design choices for this finite screen, not validated estimates:
overall >= 0.90; node/boundary, materiality, atomic relation, coverage and each applicable
guard agreement >= 0.90; each semantic category >= 0.80; each relation class >= 0.90.
All safety-explicit anchors require exact A/B agreement and evidence-confirmed intended
distinction. Missing mandatory category/class/guard opportunities is INCONCLUSIVE.
Do not recalculate raw agreement after C/reconciliation to hide disagreement.

## Assurance beyond agreement

Require 44 structurally valid A/B annotations, all category opportunities, all relation
classes observed, at least one COMPLETE and UNKNOWN coverage, TRUE and FALSE opportunities
for every guard, at least one justified UNKNOWN guard, and no silently skipped projection.
Review explicit seeded contrasts using exact BODY/claim anchors. Shared error or an
unfaithful seed remains a failed apparatus check even if agreement is 100 percent.

Evaluate all eight invariance relations and eight mutation relations using preserved
annotations and the resolved alignment maps, never by re-invoking an adjudicator.
For invariance, the specified semantic labels and scope graph must be unchanged under
the entity/anchor mapping. For mutation, the intended feature and its downstream
semantic relation or obligation inventory must change as preregistered; unaffected
dimensions must remain unchanged. Both endpoints must be independently adjudicated.
Duplicate and paraphrase consistency are separately reported. Every relation must
hold in accepted labels and be evidence-confirmed. A failed family cannot be averaged
away or removed. Conflicting witnesses must remain conflicting, not order-resolved.

Accept the apparatus for bounded assessor evaluation only if custody/apertures are
valid, raw agreement thresholds pass, all seed and family checks pass, every required
dimension of every case is accepted (including a justified UNKNOWN/AMBIGUOUS label),
and evidence review finds no shared semantic error. 'Accepted annotation set' is the
label; 'gold' or independently human-validated requires actual human verification.

INCONCLUSIVE: valid custody but semantic rubric ambiguity, insufficient agreement,
failed seed/family semantics, unresolved expectations, or absent required opportunities.
CONTAMINATED: a required clean context sees forbidden data before its freeze, or A/B
judgments leak between contexts. Preserve the exposure; dependent stages are NOT_RUN.
APPARATUS_INVALID: drift, missing source/custody, malformed packets/output, broken
comparison implementation, false receipts, or incomplete required adjudication.
A malformed later assessor response is candidate evidence, not retroactive invalidity
of a valid adjudication apparatus. A materially ambiguous rubric gets a successor.

## Independence receipt

Record context, implementation, model/tool, data and human independence separately.
Distinct fresh transcripts may support context separation if actual exposures prove it.
Separate implementation means no assessor/scorer code or candidate adaptation was used
to create labels; no implementation is created here. Record provider/model/version,
tools, shared system context, author, adjudicators and resolver for later runs.
Same-model A/B contexts do not establish model/training-history independence. Common
corpus/rubric intentionally means data is shared between A/B. The corpus is separately
authored from historical controls, not an independent population sample. Two agents
do not establish independent human judgment. Training exposure remains UNKNOWN.
Preparation ownership is one agent context; no independence achievement is claimed now.
