# Sealed-role runtime preflight v2

This package freezes one new no-model sandbox candidate after v1 returned an
explicitly denied outside file. v1 remains FALSIFIED in [PR #34](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/34).
[Issue #35](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/35) authorizes
configuration discovery and this preflight only.

> **Binds:** this frozen runtime preflight and its publication.
> **Tier:** T0 publication procedure; runtime enforcement is under test.
> **Check:** candidate-local tests, exact hashes and persisted runner receipts.
> **Escape:** preserve partial evidence and use an explicit terminal failure state.

At this source freeze the experiment is designed / NOT_RUN. Later observations
belong in `probe-run.json`, `RESULTS.md` and `TERMINAL.json`; this entry preserves
the pre-execution state.

The candidate uses the same installed CLI binary, a dedicated subprocess config
home, an explicit default named profile, and a separately identified primary-read
mutation. The original user configuration is preserved. `configuration-discovery.json`
distinguishes observed field precedence from inference and unresolved v1 cause.

`effective-prefreeze.json` binds actual runtime configuration/layer responses and
the doctor's resolved filesystem summary. Original local paths and streams are
retained privately; public templates and receipts use explicit logical path
redactions. Exact original byte hashes are distinct from public-copy hashes.
This diagnostic binding does not expose the compiled Seatbelt/kernel rule set.
Enforcement is the subsequent test question.

The frozen `PROTOCOL.json` orders P0–P6 and stops on the first non-PASS. The
runner persists raw stdout/stderr before scoring and refuses a second run.
`adapter.py` delegates reads to native Codex and cat; it does not intercept access.
Construction tests exercise scoring failures and a missing runtime, not sentinel
qualification. Run only under a separately recorded exact private binding.

## Structural profile

- Owner: this experiment, issue #35.
- Authority: frozen research procedure and deterministic runner.
- Privacy: public-safe source and logical-path receipts; raw local configuration
  and stream custody are private.
- Update rule: no candidate/configuration edit after freeze; append results.
- Verification: 11 construction tests, candidate-local Ruff, hash/custody checks.

> **Binds:** this experiment package.
> **Tier:** T0 publication procedure.
> **Check:** runner guards and persisted receipts; no generic platform guarantee.
> **Escape:** preserve partial results; INCONCLUSIVE or APPARATUS_INVALID instead
> of inventing effective state or a denial.

No case author, adjudicator, assessor, reducer or project generation is launched.
Hidden model initialization and network confinement remain untested.
Wave B remains LOCKED. No merge, release or promotion.
