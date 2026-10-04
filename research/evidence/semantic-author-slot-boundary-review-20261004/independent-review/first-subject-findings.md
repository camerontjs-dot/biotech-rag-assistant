# Exact-commit engineering review: fae7520

## Subject

- Local subject: `fae7520a8d2b5e5b45a91efa5ad5e8d90f1237c8`.
- Tree: `8f5b337065d88e2a3827006ab193c1bac2d8d43f`.
- Wrapper source SHA-256: `facefd417bba3548420498a036de2bb3da36062a1942851c417206883dc5d4e0`.
- Exact source snapshot: `successor-fae7520/` beside this report.
- Parent-reported API publication: `d5c7e146c1edd79434495eb9fe9ad157653dba1a`, with the same tree. The executed subject remains the local commit/source above; the reviewer made no GitHub requests.

Only three research files were added relative to the inherited base. The historical semantic package, runner, materializer, and failure corpus remain unchanged. This is separate engineering review with historical context, not blind semantic adjudication or model/training independence.

## Focused reproduction

Command:

```sh
<scratch>/biotech-test-env/bin/python <scratch>/boundary-review/review_successor_probes.py --subject <scratch>/boundary-review/successor-fae7520 --result <scratch>/boundary-review/successor-fae-probe-results.json
```

The command completed with exit status 1: six expectations passed and six failed. No real provider/network calls occurred. Every test used uninterpreted structural tokens and fake HTTP in a disposable source copy. No broad test suite was rerun.

The passing checks cover the historical design-only malformed identifier, historical plausible relation alias, an unused reserved source/distractor UUID collision, exact Unicode/authored-content preservation through materialization, a valid canary plus first partition, and a later structural word-limit failure that preserves exact raw bytes and prevents both retry and the next network action.

## Proven custody findings at this subject

Every corruption below was introduced after a valid fake canary and valid author-01. The next valid author-02 was incorrectly accepted and performed three additional fake HTTP operations: GET version, GET tags, POST generate. Expected behavior is denial before any of those operations.

| Corruption | Receipt edits needed | Result at fae7520 |
| --- | --- | --- |
| Replace author-01 `materialized.json` with non-JSON bytes and update its boundary materialized hash | One matching boundary hash | Next partition accepted |
| Replace canary `response-text.txt` | None | Next partition accepted |
| Delete canary `models-discovery.raw.json` | None | Next partition accepted |
| Change the canary discovery model's digest while retaining its original receipt hash | None | Next partition accepted |
| Delete canary `send-started.json` | None | Next partition accepted |
| Change canary boundary request identity and adjudication state to contradictory values | Boundary metadata only; all existing hashes unchanged | Next partition accepted |

The materialization finding is a contradiction in retained accepted evidence: the final corpus still derives from the original raw draft. It does not directly permit edited prose into the corpus. The other reproduced defects permit missing or altered provenance evidence to survive replay, even without updating any stored digest.

`checked_call()` at this commit checks raw/parsed/request/prompt custody, but omits several successful-call artifacts and accepts unchecked receipt metadata. It verifies saved materialization only against its mutable boundary hash; the subsequently recomputed materialization is not compared with the saved file.

The requested correction is a complete deterministic replay of these retained relationships: exact response text and canonical parsed bytes from raw; recorded discovery hashes/content and runtime metadata from the frozen configuration; before/send markers from the recorded one-attempt request; accepted boundary identity/stage fields; and exact canonical materialization from the raw-derived draft. Hash equality remains useful but cannot replace reconstruction. Coordinated rewriting of all records and an external trusted publication remains outside what local hashes can authenticate.

## Additional static observation

The final corpus receipt's `source_acceptance_receipts` includes only the 28 author entries because it iterates over `drafts`. The mandatory canary is checked during freezing but omitted from that final commitment. Include the canary acceptance receipt in the final source commitments. This observation was communicated for the same focused correction, without an additional 28-partition review run.

## Original twelve-probe coverage assessment

| Prepared probe | Assessment at fae7520 |
| --- | --- |
| BR-01: exact case slots/order | Source binds positional constants and repeats explicit exact-list validation; author suite covers duplicate, foreign, and reordered cases. |
| BR-02: exact design assignments/order | Source binds positions, role/category and anchor seed. Independent historical design-only alias rejected. Variant seed remains open as inherited. |
| BR-03: exact relation identity/order/recipe | Source binds identifiers, family/mode, and both endpoint slots. Independent historical relation alias rejected. |
| BR-04: immutable complete plan | Exact 28/44/16 plan is derived from the frozen inventory; final cases/design/relations each use explicit inventory order. |
| BR-05: unique frozen IDs | Global 528-ID pool is checked, including unused positions. Independent cross-kind unused collision rejected. |
| BR-06: freeze/request/config authority | Pinned inherited freeze and executing-source identity, regenerated request specs, explicit config, and per-call freeze checks are present. Retained runtime discovery replay requires correction above. |
| BR-07: invalid raw preservation | Unchanged strict runner plus independent later structural failure preserves exact received bytes. Captured response-text custody requires correction above. |
| BR-08: no semantic repair | Content-preserving mechanical conversion verified with Unicode and independent reverse projection. Reference checks reject missing/nonunique anchors; no semantic certification branch found. |
| BR-09: failure stops sequence | Independent late structural failure blocks retry and next HTTP action. Missing/corrupted accepted provenance requires correction above. |
| BR-10: fresh paths | Namespace, exclusive writes, ancestor/member symlink rejection, and interrupted-call checks are present. Parent reports focused symlink/root-mismatch fixes tested. |
| BR-11: inherited corpus validator | All drafts are reconstructed and `frozen.validate_corpus` is required before corpus bytes are written. Corpus result explicitly retains NOT_ASSESSED/NOT_RUN and pending local context/custodian review. |
| BR-12: reconstruction defeats hand edits | Raw-derived final corpus content is protected. Exact saved materialization and complete custody/metadata replay require correction above. |

## Local handoff review

The separate handoff draft was captured as `handoff-reviewed-20261004.md`, SHA-256 `94ab3004666be11e9e5ffbd0f948d3f8155f5dbc7de32c12a30c089406e1071f`. It is not part of the fae7520 commit.

It provides an actionable route through exact source checkout, pinned dependencies, live runtime/configuration inventory, new paths, a feature/capacity canary, ordered authoring, full corpus freeze, and the next scientific stop. It preserves unrelated files/sessions and the EB thread, explicitly refusing to kill its process to obtain resources. It separates supervisor knowledge from author exposure and keeps semantic adjudication, assessor/reducer work, promotion, and integration unrun. It also correctly qualifies provider token counts and model/context measurements as insufficient proof of untruncated exposure.

One sequencing clarification was sent to the parent: section 2's canary instruction should explicitly require preparing and publishing the prospective configuration/request/plan/freeze first, because section 3 introduces the freeze while the protocol correctly requires it before every provider call, including the canary.

## Disposition

The assignment boundary addresses the historical row-count/slot defect. This exact subject still needs the focused custody corrections above before its retained evidence can support the stated complete reconstruction claim. Author-reported later revisions are not silently substituted as this review's subject. A new exact source identity and a rerun of the focused probes are required for the final disposition.
