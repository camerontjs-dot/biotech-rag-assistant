# Shadow generation + deterministic claim gates protocol

Status: preregistered Slice 5 implementation protocol, stacked on qualified EvidencePacket v1.

## Objective

Add a provider-neutral **shadow generation** path that can consume only an `EvidencePacket v1`,
then deterministically validate the returned structure before anything is displayed as generated
synthesis.

This slice does not replace `/answer`. It does not expose a live model on pull requests.

Deliver:
- typed `GeneratedAnswer`, `GeneratedClaim`, citation, and gap records;
- a minimal generator protocol whose only request authority is the packet;
- `ScriptedGenerator` for deterministic CI;
- blocking gates G1-G7;
- explicit fallback/refusal disposition policy;
- a shadow `POST /synthesize` route injectable with a generator in tests;
- scripted adversarial fixtures for every G1-G7 failure mode.

## Upstream authority

Required predecessor:
- EvidencePacket v1 candidate: PR #9
- qualified head: `6425dc504069e62a168f1a713b118ecd364766b9`
- disposition: `PASS_FOR_EVIDENCE_PACKET_V1_BOUNDARY`

The generator receives an EvidencePacket object. The generator interface exposes no retriever,
filesystem, corpus loader, web client, or tool registry.

This is an interface authority boundary, not a claim that arbitrary Python provider code is
physically incapable of opening files. Provider adapters remain trusted code and require separate
review.

## GeneratedAnswer schema

Raw generator output must validate against a strict schema with unknown fields rejected.

Dispositions:
- `answered`
- `partially_answered`
- `not_stated`
- `insufficient_evidence`

Claim:
- `claim_id`
- `text`
- one or more citations
- optional `qualifier`
- optional `limitation`

Citation:
- `chunk_id`
- `quote`

Gap:
- `asked_about`
- `statement`
- `topic_citation` with the same citation shape

No Markdown contract is accepted from the generator.

## Blocking gates

### G1 schema

The raw output must validate exactly. Unknown fields and malformed structures fail G1.

On failure: `extractive_fallback`.

### G2 packet membership

Every claim citation must name an admitted packet chunk.

On failure: drop that claim.

### G3 quote containment

Every claim quote must be a non-empty substring of its cited admitted chunk after Unicode NFC and
whitespace normalization.

On failure: drop that claim.

### G4 quantity grounding

Every quantity token in a claim must be grounded in that claim's accepted quotes.

The deterministic normalizer:
- removes recognized controlled-document identifiers before quantity parsing;
- normalizes Unicode NFC and case;
- normalizes percent symbols to `percent`;
- normalizes common English number words to digits;
- extracts numeric values;
- extracts recognized unit/duration tokens associated with quantities.

This gate is deliberately conservative. When grounding cannot be established, drop the claim.

It does not decide whether the quoted quantity semantically answers the question.

### G5 identifier grounding

Controlled-document identifiers matching the repository code shape, such as `SOP-QA-001`,
`EQ-0417`, `RM-301`, `FRM-QA-201`, or `MAT-3101`, must appear in the claim's quotes or in
metadata of the cited packet items.

On failure: drop the claim.

### G6 section role

A generated claim cannot rest only on citations whose mechanical section role is
`revision_history` or `references`.

On failure: drop the claim.

This is intentionally narrower than semantic authority resolution.

### G7 disposition consistency

Global output consistency must hold:
- `answered` contains at least one claim;
- `partially_answered` contains at least one claim and at least one gap;
- `not_stated` contains no claims and at least one gap;
- `insufficient_evidence` contains no claims;
- every gap topic citation belongs to the packet and its quote is contained;
- quantities and controlled-document identifiers asserted in a gap statement must be grounded in
  its topic quote.

On any G7 failure: `extractive_fallback`.

## Post-gate disposition policy

Empty packet:
- outcome `refusal`
- disposition `refusal`
- generator is not called.

Provider error or timeout:
- outcome `answer`
- disposition `extractive_fallback`
- packet passages are returned as labelled fallback evidence.

G1 or G7 failure:
- same extractive fallback.

If raw `answered` / `partially_answered` loses every claim to G2-G6:
- extractive fallback.

Valid `not_stated`:
- outcome `answer`
- disposition `not_stated`
- gaps are shown with topic citations.

Valid `insufficient_evidence`:
- outcome `refusal`
- disposition `refusal`
- admitted passages may be shown as related material, not as answer citations.

Otherwise:
- `generated` when claims remain and there are no gaps;
- `generated_with_gaps` when claims and gaps remain.

Existing binary `answer` / `refusal` outcome remains intact.

## ScriptedGenerator

CI uses a provider-neutral scripted adapter with:
- fixed provider/model/prompt identity;
- a configured raw output or configured exception;
- call count.

Required adversarial cases:
- G1: schema breaker;
- G2: out-of-packet citer;
- G3: quote forger;
- G4: fabricated quantity/unit;
- G5: fabricated controlled-document identifier;
- G6: claim supported only by revision-history/reference material;
- G7: insufficient-evidence-with-claims;
- G7: not-stated-with-unsupported-value.

Also require:
- valid answered output passes;
- valid not-stated output passes;
- empty packet never calls the generator;
- provider exception falls back;
- existing `/answer` output remains unchanged.

Prompt-injection semantic obedience is **not** claimed to be solved by G1-G7. That belongs to the
later security slice. Deterministic gates may catch concrete fabricated quantities/codes or schema
escapes, but a semantically misleading claim that faithfully quotes malicious context remains a
known residual.

## Shadow transport

`POST /synthesize` is a shadow route.

The normal app has no live generator configured. When none is configured, a non-empty-packet
synthesis request returns 503.

Tests may inject a ScriptedGenerator into `create_app`.

The route:
1. resolves the allowlisted corpus;
2. builds the maintained BM25 EvidencePacket;
3. runs shadow synthesis;
4. returns the validated/fallback record;
5. records packet identity, generator identity, disposition, dropped claims, and gate codes in the
   audit record.

It never changes `/answer`.

## Acceptance

Required before any real-model DEV run:
1. all scripted G1-G7 adversaries are caught by the intended gate;
2. valid answer and valid not-stated controls pass;
3. empty packet does not call the generator;
4. provider exception produces labelled fallback;
5. every displayed generated citation is packet-bound and quote-contained;
6. every displayed generated quantity/code passes its deterministic grounding gate;
7. fallback is never labelled generated;
8. API request schema rejects filesystem/corpus-path injection;
9. normal `create_app` exposes no configured live generator;
10. existing answer/retrieval/packet/evaluation tests and Pages parity remain green.

A pass authorizes a separately preregistered **DEV-only live-model shadow run**. It does not
authorize TEST evaluation, public generation, or semantic-support claims.
