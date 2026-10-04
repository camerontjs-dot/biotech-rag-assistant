# Independent engineering verdict for original PR #50

**NOT_QUALIFIED. Reject this exact implementation unmerged.** The maintained checks pass, but the new sentence-selection helper fails two independently reproduced requirements. The original source HEAD is `9685872827b37b55c981b88ad3177a2ed3b13533`, tree `68a241ea95194929f4b1ac631eebe4962dd32cae`, compared with base `cd9ba8bc4351ac0cb4cf022ec1ddf449671454c3`. The exact checked source is archived in [source-citation-spans.py.txt](source-citation-spans.py.txt), with Git and SHA256 identities in [source-identity.json](source-identity.json).

This review concerns span mechanics within an already authorized body. It is not a semantic-support adjudication. The accepted requirement was to select the enclosing sentence of a unique quote inside a body already authorized by the caller; no external acceptance authority narrowed "sentence" to a period immediately before whitespace/EOS.

## Finding 1 — P2: overlapping repeated quotes bypass ambiguity refusal

**Original source line 54.** `body.count(quote)` counts nonoverlapping matches. A second overlapping occurrence is therefore missed, and the function selects the first location.

```python
select_enclosing_sentence(
    "Notify QA QA QA before release.",
    "QA QA",
).model_dump()
```

The quote occurs at offsets **7 and 10**, but the actual result is:

```json
{"outcome":"selected","text":"Notify QA QA QA before release.","start":0,"end":31}
```

Expected: `ambiguous`, with no selected text or offsets. The original probes also reproduce this with `CAGCAG` inside `CAGCAGCAG` and `aaa` inside `aaaaa`. These are one root cause.

**Minimum mechanical correction:** after finding the first occurrence, search for a second beginning at `first_match + 1`; reject repetition as ambiguous. This correction does not require a semantic-policy or sentence-grammar decision. The original tests and their expectations remain fixed.

## Finding 2 — P2: delimiter segmentation can truncate a sentence before its condition

**Original source lines 31–34.** Treating every period followed by whitespace as a sentence end cuts ordinary abbreviations into separate spans.

```python
select_enclosing_sentence(
    "Release is allowed for lot No. 7 only after QA approval.",
    "Release is allowed",
).model_dump()
```

Actual result:

```json
{"outcome":"selected","text":"Release is allowed for lot No.","start":0,"end":30}
```

The selection excludes the lot identifier and `only after QA approval`, although both are inside the same enclosing sentence and supplied body. Identifying this omission requires no judgment about whether the sentence supports an answer claim.

The same parser root cause also rejects the complete unique quote `Hold until 5 p.m. unless QA grants an exception.` as `not_found`, and expands `QA must approve!` to include the neighboring `Operators may proceed.` sentence. Question marks and terminal periods followed by closing quotes likewise merge neighbors. See the exact [machine counterexamples](counterexamples.json) and [original probe receipt](independent-pytest.log).

The implementation docstring describes its delimiter rule; it does not provide authority to narrow the accepted complete-sentence requirement.

**Successor scope:** the broader sentence-boundary policy is a separately identified successor question under [#39](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/39). A future proposal must specify its authorized input grammar, handle that grammar consistently, and preserve source offsets. This evidence does not silently define a narrower grammar, approve a replacement parser, or qualify the original head. Where boundaries are unresolved under an authorized grammar, a fragment must not be certified as the enclosing sentence.

## Boundary checks and limits

The diff adds only the helper and its author tests. The helper has no production caller or import. Existing retrieval, answer construction, API, CLI, chunking, structural citation validation, and packet/source membership are unchanged. The reviewed function has no filesystem, network, retrieval, heading, stale-source, or held-out-source access.

Successful outputs are direct `body[start:end]` slices within the supplied body. Independent passing probes cover an interior quote; exact period-terminated sentence stability; a final sentence without punctuation; CRLF, Unicode, and decimal handling; missing, empty, and external-source sentinel quotes; ordinary nonoverlapping repetition; cross-sentence refusal; and composition of body-relative offsets into an unchanged source record. Authorization and source identity remain caller preconditions because the helper receives no source identifier.

One further original probe fails because leading whitespace is included in a complete first-sentence selection. This remains an explicitly recorded stability limitation, not a third material finding.

No source files, original author tests, or independent probe expectations were changed. The reviewed checkout remained clean before and after validation. No `AGENTS.md` instructions were found in the checkout or its ancestors.

## Validation and qualification

| Check | Observed result | Receipt |
| --- | --- | --- |
| Maintained full pytest | **118 passed**, exit 0 | [full-pytest.log](full-pytest.log) |
| Citation-span and API tests | **21 passed**, exit 0; includes four API/CLI parity comparisons | [focused-pytest.log](focused-pytest.log) |
| Independent contract probes | **14 passed, 10 failed**, exit 1 | [independent-pytest.log](independent-pytest.log) |
| Ruff | Passed | [ruff.log](ruff.log) |
| Compilation | Passed | [compileall.log](compileall.log) |
| Controlled corpus | 10 valid, 8 retrievable, 2 status-excluded | [validate-corpus.log](validate-corpus.log) |
| Trust suite | **24/24 passed** | [trust-report.json](trust-report.json) |
| Pages JS/Python parity | **42/42 passed** | [pages-parity.log](pages-parity.log) |

The original 24 independent probes were drafted before reading the author tests. Their ten failures are three overlap cases, six abbreviation/punctuation cases, and one whitespace-stability case. The archived [contract-probes.py.txt](contract-probes.py.txt) is byte-identical to the executed original. Results and provenance are machine-indexed in [results.json](results.json) and [provenance.json](provenance.json).

The recorded environment used Python 3.12.14, pytest 9.1.1, Ruff 0.16.10, Pydantic 2.13.5, and Node v24.19.0. Local review did not run the Python 3.11 and 3.13 CI matrix. Both maintained pytest runs emitted one Starlette/FastAPI test-client deprecation warning about future `httpx2` use. The warning did not cause a failure. All package versions are recorded in [versions.json](versions.json).

The green maintained receipts establish continued behavior of the existing runtime and its structural trust checks. The absence of production callers limits current exposure to the new utility's API contract; it does not negate that contract's failures. **The original head remains NOT_QUALIFIED and should be closed unmerged.** Portable reproduction and integrity verification are in [README.md](README.md). The historical review is retained as [review-original.md](review-original.md); publication did not weaken its findings or change its verdict.
