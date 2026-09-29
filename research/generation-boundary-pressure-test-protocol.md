# Slice 5C — deterministic boundary pressure test

Status: preregistered before successor fixes.

## Objective

Attempt to falsify the qualified EvidencePacket + G1-G7 boundary on edge cases not exercised by the
initial scripted suite. Preserve failures before repair. No live model is used in this first stage.

## Frozen predecessor

- Wave A replay apparatus repair head:
  `d195b689ea51cf34cf952d572c6557b87fcd1f1e`
- Slice 5A scripted gates previously passed G1-G7 under their named fixtures.
- This successor probes stronger invariants and may legitimately turn CI red.

## Falsifiers

### P1 packet identity integrity

Mutating any field included in the ep1 identity payload while retaining the old `packet_id` must
be detected before generation.

The generator must not be called on a packet whose declared ID does not match its canonical
identity payload.

This is a boundary-integrity invariant, not a new semantic claim gate.

### P2 quantity exactness

G4 must distinguish numeric atoms exactly.

A claim saying `5 days` must not be grounded by a quote saying `15 days`.

Similarly, a claim quantity must not pass merely because its characters occur as a substring of a
different number.

### P3 quantity unit binding

A claim saying `5 hours` must not be grounded by a quote saying `5 days`.

### P4 identifier case robustness

Controlled identifiers are compared canonically. A fabricated lower-case rendering such as
`eq-9999` must not bypass G5 merely because the detector only recognizes uppercase text.

### P5 mixed valid/invalid claims

When an `answered` output contains one valid claim and one G2-G6-invalid claim, the invalid claim
is dropped but the valid claim may survive. The entire output must not become generated solely from
an invalid claim, and gate receipts must preserve the dropped claim failure.

### P6 packet membership after section expansion

Section-expansion citations are valid only when the expanded nomination is actually admitted to the
packet. A same-section chunk that exists in the corpus but was excluded by budget must still fail
G2.

## First-run rule

Add the falsifier tests before repairing any observed failure. Run ordinary CI once and preserve the
first result.

A failing falsifier is evidence of a boundary defect, not a reason to weaken the test.

## Successor rule

Repairs must be the smallest change that enforces the failed invariant, with the first failing
candidate preserved in PR history.

## Next live-model step

Only after these deterministic invariants pass should the live generator be given an Ollama
JSON-Schema-constrained output channel. The prompt/evidence policy remains separate from the
transport constraint.
