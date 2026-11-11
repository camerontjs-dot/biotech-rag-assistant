# Citation selection from explicit authorized bounds

This unconnected utility validates a quote inside a span whose BODY offsets the
caller has already authorized. It makes no sentence-boundary inference. API, CLI,
retrieval, chunking, source status, headings and semantic gates are unchanged.

## Why the contract changed

Rejected [PR #50](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/50)
accepted overlapping repeated quotes and truncated a condition after `No.`.
The automatic successor at
[`8ddd2a8969869be5e5dfe339b45087f1ee7e8803`](https://github.com/camerontjs-dot/biotech-rag-assistant/commit/8ddd2a8969869be5e5dfe339b45087f1ee7e8803)
passed all 29 historical author/probe cases, but a separately frozen 32-case
review found two paragraph-crossing failures. Additional review reproduced the
condition-truncation failure with an unfamiliar abbreviation:

> Release is allowed only after Coord. Smith signs the authorization.

The automatic selector returned only `Release is allowed only after Coord.`.
An abbreviation list cannot establish that every other full stop is a sentence
ending. The failed automatic candidate remains an immutable ancestor; it is not
qualified by the narrower utility below.

## Input and output contract

```python
select_authorized_span(
    body,
    quote,
    authorized_start=...,
    authorized_end=...,
)
```

The caller provides one authorized BODY, an exact literal quote, and a previously
authorized range within that BODY. `start` is inclusive and `end` exclusive.
Offsets use Python Unicode string indices, not UTF-8 bytes. They must be plain
integers; booleans, floating-point values and strings are invalid.

| Outcome | Meaning |
| --- | --- |
| `selected` | The exact authorized slice contains the sole literal quote occurrence. |
| `not_found` | The quote is empty, whitespace-only, or absent from BODY. |
| `ambiguous` | More than one occurrence exists anywhere in BODY, including overlapping occurrences. |
| `bounds_required` | A unique quote exists, but neither authorized bound was supplied. |
| `invalid_bounds` | The range is incomplete, invalid, outside BODY, does not fully contain the quote, or crosses a paragraph break. |

Every refusal has null `text`, `start` and `end`. Quote presence and global
uniqueness are checked before bounds. The helper does not resolve a repeated
quote merely because one occurrence falls within the supplied range.

A selected result always satisfies `text == body[start:end]`. No trimming,
normalization, case folding, punctuation analysis, offset repair or inferred
expansion occurs. Single line breaks may wrap a span; blank lines (LF, CRLF or
CR, including whitespace-only intervening lines) and Unicode U+2029 separate
paragraphs. Bounds may select within one paragraph of a larger supplied BODY.

## Authority the helper does not supply

The correctness and linguistic completeness of the caller's range are input
preconditions. A caller can supply a syntactically valid but incomplete range;
this utility cannot detect that semantic mistake. It also cannot verify source
status, source hashes, packet membership, truth, relevance or claim support.

There is deliberately no automatic fallback. Supplying no bounds for the
`Coord.` example returns `bounds_required`; it never chooses the shorter span.
An upstream mechanism that simply supplies unchecked punctuation-parser offsets
would reintroduce the same unresolved problem. Qualifying such an upstream
mechanism, and wiring this utility into a maintained consumer, remain separate
work under [programme #39](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/39).

A08's frozen authorized sentence can be supplied explicitly with unchanged
BODY/source identity. That establishes the bounded selection operation; it does
not generalize A08's semantic judgment or supply authority for A07 headings.

## Historical evidence and verification

The original #50 source, five author tests, 24 independent probes and
counterexample JSON remain byte-for-byte in
`tests/fixtures/citation-span-selection-pr50/`. The historical automatic tests
are `.py.txt` archives: they describe a different contract and are not relabeled
as passing tests of this explicit-bounds API. The earlier automatic successor
and its tests are reconstructable at publication commit `8ddd2a8969869be5e5dfe339b45087f1ee7e8803`. The [publication map](../research/evidence/citation-authorized-bounds-20261004/publication-map.json) preserves the distinct original local commit identities and identical trees.

Run the maintained utility tests with:

```bash
PYTHONPATH=src python -m pytest -q tests/test_authorized_citation_spans.py
```

The separate engineering review records first-candidate failures and evaluates
this changed contract independently. No provider call or semantic adjudication
is part of utility qualification. Nothing is promoted by adding this helper.
