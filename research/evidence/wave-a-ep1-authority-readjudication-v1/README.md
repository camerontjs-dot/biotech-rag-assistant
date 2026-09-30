# Frozen Wave A successor receipt

Terminal disposition: **MIXED**. A07 has a packet-level grounding defect;
A08 has citation-span insufficiency. Wave B remains **LOCKED**.

This is `wave-a-ep1-authority-readjudication-v1`, a separately preregistered
retrospective policy successor to PR #17's `APERTURE_AUTHORITY_UNDEFINED`.
Only the accepted ep1 authority rule changes. The original claims, citations,
provider responses, packets, public dispositions, and G1-G7 results are unchanged.
Judgments are `agent_llm`, moderate confidence, `needs-audit`; no independent
human review or deterministic semantic oracle is claimed.

## Identity and custody

- Predecessor PR #17: `457be991da5835f642195ffcf289d8f271e5f51b`, tree
  `4545e4e464150f5e658390421d7c4c085f8f3940`.
- Accepted ADR-018 source on Draft PR #19:
  `97beb5d81492b196affda7da03276dbc7b14246d`, tree
  `a2734664694a9e760aaf490cd5501c0308f086b8`.
- Separate preregistration published on Draft PR #20 before successor judgments:
  `e5ad140fced202ce4c0bf3dec6ce92ed0838e7e9`, tree
  `982a912187dff9f5728f2ea519d91885b1cf72f4`.
- Execution after the historical-custody apparatus correction:
  `ce831b5898be46175ce10f3d57d232e5db12fcf1`, tree
  `b1ccd07c42ad152bf8486340c1da270f52c8081d`.
- Final publication SHA/tree are recorded in PR #20's terminal GitHub receipt;
  a commit cannot contain its own hash.

Protocol SHA-256:
`97120d8e6e1fc09036be92a096ec2c0c0d6ef99fd5cd35c345097147db3036b4`.
Inherited evidence-manifest SHA-256:
`214aaf9723db10a3ccbcba43ecae0fede5cafa4f3ad5fc25bcbe598340bf8307`.
Unchanged predecessor adjudication SHA-256:
`a131e5573afdb0d9e120fcb208dea28ef11073751dce01c205a0722bbcc2e0c1`.

The protocol and `EXPERIMENT.json` pin all eleven original preserved files.
`custody-check.json` verifies their byte hashes, first-run values,
provider/output/replay bindings and original source authority. All six admitted
body spans across the two packets were verified against native source hashes
and character spans. `support-surfaces.json` preserves exact Q/N/P evidence.
`adjudication.json` preserves each exact claim, citation, quote, missing
proposition, reasoning and import requirement. `freeze.json` hashes this
successor's records and helper. No original evidence was repaired or normalized.

## Observed evidence and interpretation

Q is the selected quote. N is the cited nomination's admitted body. P is all
admitted packet body/source spans. ADR-018 excludes heading-only proposition
support under ep1. Identity/provenance metadata locates evidence and does not
supply missing propositions; the question identifies the fact being requested.

| Frozen claim | Q | N | P | Case disposition |
| --- | --- | --- | --- | --- |
| A07 | OVER_BROAD | OVER_BROAD | OVER_BROAD | PACKET_LEVEL_GROUNDING_DEFECT |
| A08 | OVER_BROAD | SUPPORTED | SUPPORTED | CITATION_SPAN_INSUFFICIENCY |

A07's exact claim is "The analyst uses two traceable weights for the daily
balance check." Its quote says "The analyst verifies the balance with two
traceable weights before use." The admitted body adds the out-of-range stop-use
condition; no other admitted body supplies daily-check scope. The minimal
missing proposition is that the two-weight verification is the daily balance
check. The authentic model-visible heading says "Daily check" and the question
also supplies that scope. The full claim therefore needs an unauthorized scope
bridge under ADR-018. Its causal origin cannot be distinguished between query,
excluded heading, or another source from this single frozen output. This is not
a claim that the full source document or daily-check fact is false.

A08's exact claim is "Both operations and QA must sign the clearance record
before the run starts." Its quote, "both operations and QA sign the clearance
record", omits the necessity/timing condition. The admitted body explicitly
says "The run cannot start until both operations and QA sign the clearance
record." Thus Q is over-broad while N/P support the full claim without evidence
imported from the question or heading.

Both claims survived the original deterministic gates with no fired gates.
Those historical results remain fixed. The successor finding is a qualitative
adjudication under resolved authority, bounded to these two frozen DEV claims.

## Qualification and limitations

The ADR qualification constructed a native valid ep1 packet and changed only
`section_heading` from `Daily check` to `Weekly check`. Its packet ID and eight
identity-bearing fields remained unchanged; validity and adapter request
preparation still passed. No transport was invoked. The challenge also found
body-only mutation remains valid, so ep1 validity is not complete source
authentication. ADR-018 is an ep1 policy rule, not a universal linguistic claim
or an integrity repair. Native loading/chunking and frozen-file hashes provide
additional provenance in their own paths; no stronger general heading semantic
grant or independent heading verification at the generation boundary was found.

The offline artifact checker verifies exact bindings without assigning support
labels. A copied claim changed and rehashed by a falsifier was rejected for
claim drift. Thirteen focused custody/heading tests and helper lint passed.

Deviations are preserved: hosted CI first exposed a historical DECISIONS hash
being compared to the later file. The unchanged PR #17 decision bytes are now
explicitly archived, without modifying frozen evidence or the accepted rule.
The equivalent correction was added after preregistration without rewriting
its commit or protocol. An initial surface projection used the wrong replay
field name and stopped before judgments. An initial verification script assumed
direct SourceDocument fields and stopped before writing a receipt; repository
native fields were then used. These are apparatus corrections, not rerolls.
PR #17 retains the original preservation limits recorded in its evidence
manifest, including selective raw-response custody and the path-free original
receipt projection; this successor does not reconstruct omitted artifacts.

## Terminal next step

Wave B has no execution authorization and no Wave B successor was created.
The A07 packet defect defeats the no-packet-defect prerequisite. The smallest
durable follow-up is to define and separately freeze a discriminator for material
query/metadata qualifiers absent from authorized body evidence, retaining A08
as a body-supported condition control. It must address qualifier-level evidence
authority without adding a semantic gate solely to force these two outcomes.
No repair or successor experiment is performed here.

Zero model/provider calls, generation reruns, G1-G7 replays, retries, prompt
changes, or output repairs occurred in this task. Wave B payloads were not
opened/read/evaluated. TEST and PROSPECTIVE were not accessed. CAL was not
integrated. Public generation was not promoted. No merge or release occurred.
Decision and research PRs remain Draft; issue #18's authority question is closed.
