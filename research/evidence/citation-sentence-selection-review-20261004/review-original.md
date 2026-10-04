# Independent engineering review: PR #50

**Disposition: NOT_QUALIFIED — changes required.** The maintained validation gates pass, but the submitted helper violates the unique-quote and complete-sentence contracts. This is an engineering review of span mechanics, not a semantic-support adjudication.

## Exact revision and scope

- Repository: `camerontjs-dot/biotech-rag-assistant`
- PR: `#50`
- Reviewed HEAD: `9685872827b37b55c981b88ad3177a2ed3b13533`
- Reviewed tree: `68a241ea95194929f4b1ac631eebe4962dd32cae`
- Compared base: `cd9ba8bc4351ac0cb4cf022ec1ddf449671454c3`
- Checkout: `<REVIEW_WORKSPACE>/review-citation-50`
- Tracked working tree clean before and after review; no product, author-test, or remote changes made.
- No `AGENTS.md` instructions found at checkout root, beneath it, or in ancestors.
- Diff consists only of new `src/biotech_rag_assistant/citation_spans.py` (73 lines) and new `tests/test_citation_spans.py` (77 lines).

The root reviewer confirmed the live PR body requires selecting the enclosing sentence of a unique quote inside a body already authorized by the caller. It does not externally authorize redefining a sentence as a period immediately followed by whitespace/EOS. Live PR metadata was confirmed by the root reviewer; this reviewer independently verified the local exact revision and tree.

## Finding 1: overlapping occurrences bypass ambiguity refusal

**Priority: P2. Location: `src/biotech_rag_assistant/citation_spans.py:54–60`.**

`body.count(quote)` counts nonoverlapping matches. Repeated quote occurrences can overlap, so the subsequent first-match selection can return `selected` for a repeated quote.

```python
from biotech_rag_assistant.citation_spans import select_enclosing_sentence

select_enclosing_sentence(
    "Notify QA QA QA before release.",
    "QA QA",
).model_dump()
```

The quote occurs at offsets 7 and 10. Actual result:

```json
{"outcome":"selected","text":"Notify QA QA QA before release.","start":0,"end":31}
```

Expected: `ambiguous`, with no selected text or offsets. Independent probes also reproduced the defect with a repeated sequence (`CAGCAG` inside `CAGCAGCAG`) and repeated characters (`aaa` inside `aaaaa`). These are one root cause, not three separate findings.

**Minimum correction:** locate the first occurrence and search for a second occurrence starting at the first offset plus one character. Refuse as `ambiguous` when that second occurrence exists. This needs no semantic or sentence-grammar decision. Preserve the independent overlap expectations; do not weaken them to nonoverlapping-only uniqueness.

## Finding 2: delimiter-only segmentation can truncate the enclosing sentence

**Priority: P2. Location: `src/biotech_rag_assistant/citation_spans.py:31–34`.**

Every period followed by whitespace ends a span. Ordinary abbreviations therefore cut complete sentences into fragments. A successful selection can omit the remainder of the same sentence, including its qualifying condition.

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

The lot identifier and `only after QA approval` are within the same supplied-body sentence but outside the returned selection. Recognizing that omission is a span-completeness check; this review makes no decision about whether the sentence supports an answer claim.

Two other observations demonstrate the same parser root cause:

- A complete unique quote, `Hold until 5 p.m. unless QA grants an exception.`, inside a body containing that sentence and a following sentence returns `not_found`.
- A complete quote ending in `!`, such as `QA must approve!` in `QA must approve! Operators may proceed.`, returns both sentences. `?` and a terminal period followed by a closing quote likewise pull in neighboring sentences.

The helper docstring states its delimiter rule, but that implementation description does not narrow the externally authorized complete-sentence contract.

**Required correction or explicit scope decision:** provide sentence-boundary handling consistent with the authorized input grammar, including ordinary abbreviations and terminal punctuation, while retaining exact source offsets. If the intended supported grammar is narrower, that restriction requires explicit acceptance authority and input handling consistent with it; silently redefining all period/whitespace fragments as complete sentences does not qualify this head. Where a boundary cannot be resolved under the authorized grammar, avoid certifying a fragment as an enclosing sentence. This review does not supply a replacement grammar or semantic policy.

## Boundary findings that passed

The new helper has no production import or caller. Searches for `citation_spans`, `select_enclosing_sentence`, `sentence_spans`, and `SpanSelection` outside its author tests find only the new module's own definitions and internal call. It is not integrated into retrieval, CLI, API, answer construction, or citation validation in this revision.

The function has no filesystem, network, retrieval, heading, packet, status, or held-out source access. It only receives a string supplied by the caller. It does not decide semantic support or alter source/packet membership. It slices selected text directly from `body[start:end]`, with offsets bounded by that body. Missing and empty quotes fail closed. Nonoverlapping repeated quotes are refused. A quote crossing separately recognized sentences fails closed instead of widening across them.

Independent passing probes cover a unique interior quote, exact complete period-terminated quote stability, a final sentence without terminal punctuation, CRLF and Unicode offsets, a decimal number, missing/empty/external-source sentinel quotes, ordinary repetition, a cross-sentence quote, and composition of body-relative offsets into an unchanged source record. The existing chunker keeps headings separate from verbatim body text. Authorization and source identity remain caller responsibilities: this utility does not receive a source ID and cannot certify that a caller selected the correct body.

The sentence-complete test with leading whitespace also fails because initial whitespace is included in the selected span. This is retained in the independent test record as a stability limitation, not promoted as an additional material finding.

## Validation results

Environment: Python `3.12.14`, pytest `9.1.1`, Ruff `0.16.10`, Pydantic `2.13.5`, Node `v24.19.0`. Dependencies were installed from the project's `.[dev]` bounds in a review-only virtual environment. Full dependency versions are in `dependencies.txt`.

| Check | Result | Evidence |
| --- | --- | --- |
| Maintained full pytest | **118 passed**, exit 0 | `full-pytest.log`, `full-junit.xml` |
| Maintained citation-span + API suite | **21 passed**, exit 0; includes all four API/CLI parity comparisons | `focused-pytest.log`, `focused-junit.xml` |
| Independent contract probes, drafted before reading author tests | **14 passed, 10 failed**, exit 1; failures group into overlap, sentence boundary, and whitespace stability | `test_independent_contract.py`, `independent-pytest.log`, `independent-junit.xml` |
| `ruff check .` | All checks passed | `ruff.log` |
| `python -m compileall src` | Passed | `compileall.log` |
| Controlled corpus validation | 10 valid; 8 retrievable; 2 status-excluded | `validate-corpus.log` |
| Trust evaluation | **24/24** cases; status `pass`; stale exclusion 24/24; expected refusal/citation traps passed | `trust-evaluation.log`, `trust-report.json`, `trust-report.md` |
| Maintained Pages parity program | **42/42** JS/Python matches for outcome, top document, top chunk, held-out hits | `check_pages_parity.py`, `pages-parity.log` |
| Final HEAD/tree/status | Reviewed hashes unchanged; tracked worktree clean | Independently checked after validation |

The Pages program was loaded unmodified from the reviewed checkout; only its `DOCS` output directory was redirected to a copied asset directory beneath the review evidence path so the committed product files were not rewritten.

Both maintained pytest runs produced one dependency deprecation warning from the installed Starlette/FastAPI test client about future `httpx2` use. It did not cause a failure. This review ran one local Python version, not the CI matrix for Python 3.11 and 3.13.

## Reproduction commands

Run from the exact reviewed checkout. The independent test file and its expectations have not been modified after the initial probe execution.

```bash
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/python -m pytest -q
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/python -m pytest -q tests/test_citation_spans.py tests/test_api.py
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/python -m pytest -vv <REVIEW_WORKSPACE>/evidence/citation-review/test_independent_contract.py --tb=short
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/ruff check .
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/python -m compileall src
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/biotech-rag validate-corpus examples/synthetic-controlled-docs
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/biotech-rag evaluate examples/synthetic-controlled-docs examples/synthetic-controlled-docs/evaluation/golden-questions.json --json
<REVIEW_WORKSPACE>/evidence/citation-review/venv/bin/python <REVIEW_WORKSPACE>/evidence/citation-review/check_pages_parity.py
```

`counterexamples.json` records exact HEAD/tree, inputs, all overlapping occurrence offsets, and actual Pydantic result objects for the two material findings and related complete-sentence failures.

## Qualification limit

The passing maintained suite establishes that the existing runtime behavior and its structural trust controls remain intact in this exact revision. It does not override independently reproduced defects in the newly introduced public helper. The absence of production callers limits the immediate impact to that helper's API contract; it does not make the submitted behavior qualified. Original PR #50 at this exact head should not be promoted as satisfying the accepted contract.
