# Frozen Wave A re-adjudication under accepted ep1 authority

Status: preregistered before this successor's offline adjudication.

Experiment ID: `wave-a-ep1-authority-readjudication-v1`.

## Question and lineage

Re-adjudicate only the exact frozen accepted A07/A08 claims under ADR-018.
The outputs and predecessor findings are already known; this is a retrospective
policy successor, not a blinded or fresh performance experiment.

Predecessor: PR #17 at `457be991da5835f642195ffcf289d8f271e5f51b`,
tree `4545e4e464150f5e658390421d7c4c085f8f3940`, terminal
`APERTURE_AUTHORITY_UNDEFINED`. Its protocol, classifications, inputs, and
receipts remain unchanged.

Accepted authority: PR #19 at `97beb5d81492b196affda7da03276dbc7b14246d`,
tree `a2734664694a9e760aaf490cd5501c0308f086b8`.
`DECISIONS.md` SHA-256: `8d2645c83864cf436d5312d8335843441c5dad8f84ca19e0002b317919383c95`.
The decision is accepted on the Draft decision branch; no merge is implied.

## One changed factor

Use the accepted ep1 semantic-authority rule: `section_heading` cannot supply a
material proposition absent from admitted body/source spans. All generated
claims, citations, quotes, questions, packets, provider envelopes, and original
G1-G7 results stay fixed. No generator or G1-G7 replay is run.

## Frozen evidence

Evidence is inherited unchanged at `research/evidence/wave-a-support-aperture-v1`.
Evidence manifest SHA-256:
`214aaf9723db10a3ccbcba43ecae0fede5cafa4f3ad5fc25bcbe598340bf8307`.
Predecessor adjudication SHA-256:
`a131e5573afdb0d9e120fcb208dea28ef11073751dce01c205a0722bbcc2e0c1`.

Every exact preserved file remains pinned:

```text
frozen/bundle/manifest.json  80a582477de420bbf4655a8936be6067fd8cad85df2ea21f61fec6efc1945903
frozen/bundle/wave-a-probes.jsonl  6ed0bfbbc070e1953fae643e9ab98b477eff84df832e4f352b4439e946635c50
frozen/generation-freeze.json  046cc15ecd58b5667599e4b83c4e7331f3bff3ff950a80e8615e0ffc37d81bd5
frozen/replay-freeze.json  0ef347bc5d727fd8e06ef3ea8e050279a51cf07fed9bada2f341a9842226a664
frozen/structured-replay/wave-a-gated-results.json  6792435fd914b5aa72b515b3c16e6a56810e387e7d66241780d6fc9c6d55666d
frozen/structured-run/outputs.jsonl  a85b1aac79e92288bf9cfe29d3235aa17ec6ba6a7f51d58fb11d98675718b29b
frozen/structured-run/raw-manifest.json  e65e48b95dc28416245675bc6611f15cd2443028b5ce8cb03653484615fb9c03
frozen/structured-run/raw/A07-balance-weight-count.json  5c498ea264779b6b1fec2110ef60d7c882bd58f493232129ddf3264de12ac660
frozen/structured-run/raw/A08-line-clearance-signatories.json  56a68e8dff2fa9521239b33af00799c279a7a808fefd9f654af5a66550300427
frozen/structured-run/run_metadata.json  1a224f910b2ca81bb78a6da6a56fb4a6ce90cf9f6354dc900b919101b99b0d15
original-receipt-projection.json  ae3fba389fcac55307f58aa35ca0b8567d9f083dee0b5af7f5be9ec474014bb0
```

Case IDs: `A07-balance-weight-count`, `A08-line-clearance-signatories`.
Each has exactly one accepted claim with one citation. Hash all inherited
preserved files before parsing. Verify raw/provider/output/replay bindings with
the predecessor custody checker against its pinned historical source authority.
Verify every admitted A07/A08 body against its source hash and character span.
Stop as `APPARATUS_FAILURE` on drift, missing evidence, changed accepted-claim
shape, or broken binding. Do not reconstruct, normalize, or repair outputs.

## Apertures and classification

Unit: one exact accepted claim at each of Q, N, P (two cases, six judgments).
Primary outcome: qualitative support classification and minimal missing
proposition, rather than a new numeric semantic metric.

- Q: only the exact selected citation quote.
- N: the cited nomination's exact admitted body text. Identity fields locate and
  verify its source; retrieval/display metadata supplies no missing proposition.
- P: all admitted body/source spans in that exact packet, with IDs/hash/spans for
  provenance. No unadmitted source paragraph or heading is added.

Headings, expansion handles, inferred roles, authority labels, ranking scores,
query text, corpus names, and document titles are not affirmative proposition
support. G5 identifier membership remains a narrow structural check, not a
semantic bridge. The query identifies the requested fact and may be compared
with a missing qualifier, but never supplies evidence for it. Source documents
may be inspected only for span/provenance verification; surrounding source
context may not expand P.

For each aperture preserve the exact claim, citation, quote, evidence actually
used, one of these classifications, the minimal missing proposition, and any
required import from a query or another unauthorized surface:

- `SUPPORTED`: all material content is entailed by the aperture.
- `OVER_BROAD`: a supported core is strengthened by an unsupported material
  qualifier, condition, obligation, scope, or timing.
- `UNSUPPORTED`: the material assertion lacks a supported core or conflicts with
  the authorized source evidence.
- `INCONCLUSIVE`: remaining ambiguity prevents a support judgment. Record it;
  never choose a favorable aperture silently.

Qualitative judgments are labeled `evaluator: agent_llm`, with confidence and
counterevidence. No independent human review or deterministic semantic oracle
is claimed. Packet-ID validity alone is not full source authentication; the
frozen byte hashes and exact source-span checks establish custody here.

## Terminal interpretation

For each case:

1. P missing a material proposition => `PACKET_LEVEL_GROUNDING_DEFECT`.
2. N/P support the full claim but Q does not => `CITATION_SPAN_INSUFFICIENCY`.
3. All apertures support => `NO_OBSERVED_SUPPORT_DEFECT`.
4. An authority ambiguity changes the result => `APERTURE_AUTHORITY_UNDEFINED`.

Overall: `MIXED` if the cases have different material failure types; otherwise
report their common terminal type. An unresolved authority question takes
precedence. A packet defect is still reported when Q is also insufficient.
No case outcome is preassigned by this protocol.

Presence of a missing qualifier in the query is observable. Its causal origin
cannot be inferred uniquely when the same qualifier is also in excluded
model-visible metadata. Preserve that distinction without another model call.

## Wave B decision and stop state

Wave B stays locked throughout. If either P has a grounding defect, retain the
lock and create only the smallest durable follow-up to define and freeze its
engineering discriminator. If neither P has a defect and only quote sufficiency
remains, record that bounded conclusion and, if justified, create a separately
identified Wave B successor proposal without executing it. This protocol grants
no model-call or Wave B execution authority.

Complete by publishing this preregistration before recording judgments, then
preserving a successor result, exact start/final identities and receipt hashes,
observations versus inference, deviations, and the next engineering question.
Do not rewrite PR #17 or its evidence.

## Protected boundary and authority

No model/provider calls, generation reruns, prompt changes, output repair,
Wave B payload reads/evaluation, TEST/PROSPECTIVE access, CAL integration,
public-generation promotion, merge, or release.

> **Binds:** this offline re-adjudication only.
> **Tier:** T0 (operator/protocol scope; custody failures are detected by the existing checker).
> **Check:** frozen hashes, raw/output/replay and source-span binding receipts; explicit qualitative aperture records.
> **Escape:** `APPARATUS_FAILURE` or `INCONCLUSIVE` with preserved evidence; no reconstruction or boundary expansion.
