# Slice 5A — scripted shadow generator and deterministic claim-gate protocol

Status: preregistered before any live model output is observed.

## Objective

Implement the structured generation boundary and prove that deterministic gates G1–G7 catch their named scripted failure modes while leaving /answer unchanged.

No live provider or model is used in this slice.

## Authority

Parent:
- PR #11 EvidencePacket v1
- qualified head: e851b868966fb0b572b0f6c349e2987ccf938c23
- fixed ep1 receipt: ep1:2515e0d41c890d2115c8abd54eeb2394277681c43ea1ad4930239a09c2c54559

Generation receives only an EvidencePacket. It has no retriever, filesystem, web, tool, or corpus handle.

## Structured generator output

The generator returns JSON-compatible structured data matching:
- disposition: answered, partially_answered, not_stated, insufficient_evidence
- claims: claim_id, text, citations of {chunk_id, quote}, optional qualifier, optional limitation
- gaps: asked_about, statement, topic_citation of {chunk_id, quote}

Unknown fields are forbidden.

## Generator interface

Generator.generate(packet) -> object

The production interface is provider-neutral. Slice 5A supplies only ScriptedGenerator fixtures.
A generator is never called for an empty packet.

## Blocking gates

### G1 schema

Pydantic validation with extra="forbid".
Failure -> extractive_fallback.

### G2 packet membership

Every claim citation and every gap topic citation must reference an admitted chunk_id.
A claim with an out-of-packet citation is dropped.
A gap with an out-of-packet topic citation makes the overall disposition invalid under G7 and falls back.

### G3 quote containment

Normalize quote and source chunk with:
- Unicode NFC;
- collapse all whitespace runs to one ASCII space;
- trim.

The normalized quote must be a non-empty exact substring of the normalized admitted chunk text.
Claim failure -> drop claim.
Gap failure -> disposition invalid -> fallback.

### G4 quantity grounding

The normalizer is deliberately conservative.

It recognizes:
- Arabic numbers with optional decimal/sign;
- number words zero through twenty plus tens through ninety and one hundred;
- ranges expressed with to, hyphen, or through;
- nearby units from a fixed controlled vocabulary covering time, temperature, concentration, percentage, mass, volume, count and common corpus units.

Number words are normalized to numerals before comparison.

Every recognized quantity atom in claim text must occur in the normalized concatenation of that claim's accepted quotes.
If extraction or matching is ambiguous, fail closed and drop the claim.

### G5 identifier grounding

Recognize uppercase controlled-document/site identifiers such as SOP-QA-101, FRM-QA-201, EQ-0417, RM-301, MAT-2231, CH-04, and PT-21.

Every recognized identifier in claim text must appear in either:
- the claim's accepted quotes; or
- metadata of an admitted cited nomination: doc_id, chunk_id, section heading, source path.

Otherwise drop the claim.

### G6 section role

This gate remains syntactic until a semantic authority layer exists.

A claim is treated as a current-requirement claim only when it contains deterministic requirement language such as must, shall, required, requires, limit, within, no more than, or at least.

Such a claim cannot be supported only by citations whose section_role is revision_history or references.
Otherwise drop the claim.

### G7 disposition consistency

- answered: at least one surviving claim.
- partially_answered: at least one surviving claim and at least one valid gap.
- not_stated: zero claims and at least one valid gap with topic citation.
- insufficient_evidence: zero claims; gaps may describe related material.
- empty packet: generator not called; public disposition refusal.
- generator not_stated or insufficient_evidence with claims: invalid -> fallback.
- refusal is represented by the wrapper/public disposition, never by a generator claim.

G1 or G7 failure -> extractive_fallback.
If all material claims are dropped by G2–G6 -> extractive_fallback.

## Public shadow result

The shadow wrapper keeps existing binary outcome semantics and adds:
- disposition: generated, generated_with_gaps, not_stated, extractive_fallback, or refusal;
- accepted claims;
- accepted gaps;
- per-claim gate results;
- packet ID;
- generator metadata.

/answer remains unchanged.
Add internal/shadow POST /synthesize.

## Scripted adversaries

CI must include distinct fixtures for:
- G1 schema breaker;
- G2 out-of-packet citer;
- G3 quote forger;
- G4 number fabricator;
- G5 code fabricator;
- G6 revision-history-only current requirement;
- G7 not-stated or insufficient-evidence with claims;
- G7 not-stated without valid topic citation;
- injection follower that repeats an instruction from evidence as an unsupported claim.

Each fixture must be blocked by the intended gate. If another gate also fires, report it, but the named gate must still be observed.

## Gate

Slice 5A passes only if:
- every scripted adversary is caught by its named gate;
- a valid scripted answer survives;
- a valid not_stated gap survives;
- generator call count stays zero on an empty packet;
- generation never cites outside the packet;
- /answer behavior remains unchanged;
- ordinary CI is green on Python 3.11–3.13.

This establishes deterministic structural grounding only. It does not establish semantic support or live-model quality.
