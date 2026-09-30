# Wave A support-aperture adjudication

Status: preregistered before successor adjudication.

Issue: #16

## Objective

Determine whether the accepted A07 and A08 Wave A claims are supported at three distinct evidence apertures before any Wave B generation is authorized.

This successor makes no model calls.

## Frozen parent

Parent PR: #15

Parent tested head:
`2bcd4094d5538dc679db73ddba5ff7e329b9ccfc`

The completed Wave A generation and deterministic replay remain historical evidence. Their outputs must not be repaired or regenerated under this successor.

## Claim-support apertures

For each exact accepted claim, adjudicate separately:

1. **Q — quote**
   - authority: exact selected citation quote only.

2. **N — nomination**
   - authority: the cited `RetrievalNomination`, using only fields whose semantic authority is justified by the repository contract.
   - metadata such as `section_heading` must not be treated as semantic support merely because it is present.

3. **P — packet**
   - authority: the full admitted EvidencePacket source authority.
   - the user question identifies what is being asked; it must not supply missing evidence for the answer.

Each aperture receives one of:
- `SUPPORTED`
- `OVER_BROAD`
- `UNSUPPORTED`
- `INCONCLUSIVE`

Record the minimal unsupported proposition for every non-supported classification.

## Interpretation

The successor must distinguish:

- `CITATION_SPAN_INSUFFICICIENCY`: authorized nomination/packet evidence supports the claim, but the selected quote does not;
- `PACKET_LEVEL_GROUNDING_DEFECT`: material claim content is absent from authorized packet evidence;
- `MIXED`: the two cases exhibit different material failure types;
- `APERTURE_AUTHORITY_UNDEFINED`: the result turns on an authority question not established by current repository contracts.

Do not silently choose an aperture to obtain a preferred result.

## Protected boundary

- no Ollama or other model call;
- no prompt tuning;
- no modification of frozen A07/A08 outputs;
- no Wave B read, generation, or evaluation;
- no TEST or PROSPECTIVE access;
- no public generation promotion;
- no CAL vendoring or CAL integration;
- no new deterministic semantic gate solely to fit these two observations.

Offline deterministic tooling and tests are allowed if they make the adjudication reconstructable without changing the underlying evidence.

## Evidence preservation

The successor must import only the frozen local evidence required to reconstruct the adjudication.

Preserve:
- exact first-run output values;
- artifact hashes;
- generation/replay freeze identities;
- enough packet evidence to reproduce Q/N/P classification.

Do not commit local absolute paths, credentials, caches, daemon state, or unrelated workstation artifacts.

## Wave B rule

Wave B remains locked during this successor.

A later Wave B successor may be proposed only if:
- neither A07 nor A08 exhibits a packet-level grounding defect; and
- any remaining quote-sufficiency limitation is explicitly bounded for exploratory DEV interpretation.

If a packet-level grounding defect is found, stop and define the smallest separately frozen grounding successor.

If aperture authority is undefined and changes the result, stop with `APERTURE_AUTHORITY_UNDEFINED`.

## Required receipt

The terminal receipt must include:
- exact base/head/tree;
- frozen artifact hashes;
- exact A07/A08 claims and citations;
- Q/N/P evidence and classification for each case;
- observation versus inference;
- terminal disposition;
- explicit Wave B authorization status;
- any deviation;
- preserved evidence location.

No merge or release is authorized by this protocol.
