# V2 runtime preflight: FALSIFIED

The frozen candidate returned the entire explicitly denied outside sentinel.
P0 matched the frozen loaded-configuration fingerprint and runtime-resolved
sandbox summary before any filesystem probe. P1 and P2 passed. P3 returned
exit 0, exact denied bytes and empty stderr. The run stopped immediately.

The candidate is `codex-0154-isolated-home-default-profile-v2`, frozen on
`research/sealed-role-runtime-preflight-v2` at:

- Commit: `073d7c97a65f5f94a5c1b9277e9818101fb7d0c5`
- Tree: `56073b675daeb7d9eb2fb5a7aa6ff29c7534816e`
- Freeze time: `2026-10-02T03:19:55.973986+00:00`
- Runtime: Codex CLI 0.154.0, macOS 27.0 / arm64.
- Binary SHA-256: `4f85982624b3898c8991cb80c0981b2aa71070e3537046c9a95950318a95afcc`
- Adapter SHA-256: `c08a452b117e4dc60208043db243b2d8ed1938d5ba8add38c5a2bb40808abdc9`
- Runner SHA-256: `b87f9ce7d73d55f4fbfe1fab2bad404d3c217bf5f83a40e0cf554dc483af71ca`
- Exact baseline config SHA-256: `d0d349d345c0b25fa45df94f2eb2cf2139386c341587761d6515c487d77a213e`
- Actual stable configuration fingerprint: `bb11797fceaf252544fe55b24d2107c97870ec20f711ac787fe9fc4a0240949a`

## Configuration observations

Installed help, generated protocol schemas, `config/read`, origin/layer metadata,
`configRequirements/read` and doctor diagnostics are preserved in `discovery/`
and the exact private custody index. The API demonstrated command-line override
precedence over a user setting. A dedicated subprocess configuration home supplied
the candidate's user layer; the system layer was empty and managed requirements
were null in these snapshots. Other layer precedence is documentation/help only.

With an explicit named default, both clean and legacy-plus-default discovery
configurations reported a restricted filesystem and one denied-read rule. This
observation limits the claim that the presence of `danger-full-access` alone
caused v1. No v1 replay or causal re-adjudication occurred.

The baseline has no loaded legacy sandbox mode. It explicitly selects
`sealed_preflight_v2`, denies root, temp roots, the primary outside target and
renamed outside target, permits the role root, and admits the runtime's minimal
system reads. Before freeze the runtime reported five denied-read rules. The
separate primary-read mutation reported four. No sentinel was read during these
configuration observations.

P0 repeated the configuration API and doctor with identical pinned config bytes,
working root and minimal environment. Its stable fingerprint matched exactly.
The doctor reports resolved mode and rule counts; it does not export the compiled
Seatbelt policy or kernel rule set. That subprocess-policy translation remains
unknown. This is an auditable diagnostic binding with that explicit limitation.

## Persisted decisive results

| Probe | Result | Observation |
|---|---|---|
| P0 | PASS | Loaded state and resolved summary match freeze; filesystem restricted, five denied-read rules. |
| P1 | PASS | Exact isolated role cwd; Seatbelt marker; separate supervisor checkout. |
| P2 | PASS | Exact 65 allowed bytes, exit 0, empty stderr. |
| P3 | FALSIFIED | Exact 65 denied bytes, exit 0, empty stderr. |
| P4 | NOT_RUN | Stop at P3; its absolute-path attempt already falsified. |
| P5 | NOT_RUN | Separate mutation preserved; no execution sensitivity evidence. |
| P6 | NOT_RUN | Renamed fixtures preserved; no invariance result. |

Verification receipt: `probe-run.json`, SHA-256
`723d5350566c736d345880279f74913138efaaf5171ec04f36ff4908d77ba6cd`.
P2 stdout SHA-256 is `e21f079ee64e0eb53599273b918920b12460f7f69bd86f5b118ce3d89cd2a225`.
P3 stdout SHA-256 is `f68c75554c5334e9fd7ed2f6fe8607a74d2ff998753da46adb521c9956e372eb`.
All four fixture hashes are in `fixtures.json`. Their names/bytes are fresh and
no hash matches a v1 sentinel. The role root contains two allowed files and a
symlink only; fixtures remain readable mode 0444 and unchanged.

Three native sandbox invocations and one effective-state observation ran. The
latter comprised one no-model app-server initialization/config read and one
doctor diagnostic: five decisive CLI invocations in total. The entire task has
35 CLI invocations, including help/schema/parser/configuration setup. Counts do
not claim to enumerate all OS/helper processes. The two MindGraph embedding
queries are supervisor planning activity, separate from this runtime qualification.

## Enforcement and initialization

`adapter.py` delegates the native command to the pinned sandbox. It performs no
access interception. Existing readable files, exact positive and negative bytes,
and unchanged custody rule out a missing target or broken positive filesystem.
Required selective denial is absent. The Seatbelt environment marker is observed;
the specific generated/applied OS rules and defect cause remain unknown.
No successful-denial mechanism or policy-mutation sensitivity was established.

The runtime augments the child environment with PATH aliases, sandbox markers and
OS metadata. Original stdout/stderr and invocation bytes remain private; public
copies explicitly redact local paths and OS user-encoding metadata and carry
separate public-copy hashes.

Doctor diagnostics also perform non-model network reachability/update checks.
At P0, supervisor HTTP checks reported 405/200 and an unauthenticated WebSocket
handshake reported 401. These are outside the tested child sandbox. No model
prompt, thread, turn, inference or generation was requested; no update installed.
This is not evidence for network confinement or hidden model-context cleanliness.

## Checks, failures and custody

All 11 construction tests, candidate-local Ruff, adopted T0 contract lint and
pre-commit privacy checks passed before freeze. All 20 candidate file hashes,
35 v1 publication file hashes, four fixture hashes and two exact configuration
hashes passed after the run. Source/configuration bytes were not changed or retried.

Setup failures remain separate: a SQLite initialization failure in a discovery
context; malformed state-json parser diagnostics; recovered context-read truncation
and receipt races; a concurrent change in the excluded global configuration;
and an initial failed privacy hook on a generic redaction pattern. The excluded
source gate and redaction implementation were corrected before the successful
candidate freeze. Both global snapshots and the earlier draft remain private.
The original user configuration was not edited by this task. Its concurrent actor
is unknown. `failures-and-deviations.json` preserves these boundaries.

Hosted CI is separate from the runtime disposition. Publication observations will
be appended after the terminal evidence commit. No predecessor lint repair or
broad repository/model/reducer retest is authorized by this failure.

## Disposition and next evidence

**FALSIFIED** for this exact candidate's required filesystem aperture. PR #34
and its v1 falsification remain unchanged. This result does not identify the v1
cause or establish a general macOS/Seatbelt defect.

The smallest next step is a separately authorized inspection/capture of the
policy generated and applied at the native sandbox subprocess boundary, to
locate where read-deny entries are lost or ineffective. No successor candidate
or semantic role is launched here. Case-author, A/B/C, assessor, reducer and
project-generation calls are zero. Wave B remains LOCKED. No promotion, merge
or release.
