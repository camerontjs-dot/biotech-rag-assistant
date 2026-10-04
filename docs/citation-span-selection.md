# Citation span selection: bounded successor contract

This candidate follows rejected PR #50. It adds a pure, unconnected helper in
`biotech_rag_assistant.citation_spans`. It does not change any API, CLI, retrieval,
chunking, source-status rule, heading permission, or semantic gate.

## Authority and outputs

The caller supplies one already authorized `body` and an exact `quote`. The helper
has no source lookup, packet lookup, file access, model call, or claim input. It
cannot authorize the supplied body. Offsets use Python Unicode string indices,
with an inclusive `start` and exclusive `end`; they are not UTF-8 byte offsets.

The output has exactly `outcome`, `text`, `start`, and `end`:

| Outcome | Meaning |
| --- | --- |
| `selected` | Exactly one literal quote occurrence is enclosed in one span under the policy below; `text == body[start:end]`. |
| `not_found` | Empty/whitespace-only or missing quote, or the unique quote crosses a supported span boundary. |
| `ambiguous` | More than one occurrence, including overlapping occurrences. |
| `boundary_uncertain` | The body's punctuation is outside the supported policy; no span is returned. |

Every refusal has null text and offsets. Occurrence checks precede boundary
parsing. No normalization, case folding, trimming of the quote, or source-text
rewriting occurs. Leading/trailing whitespace around spans is excluded. A final
unpunctuated fragment is permitted. A full-span quote remains unchanged.

`sentence_spans(body)` exposes the same syntactic policy: a list of offset pairs,
or `None` when any boundary is uncertain. Uncertainty anywhere in the supplied
body refuses the whole selection, even if another sentence appears ordinary.

## Supported punctuation policy

This is a conservative policy for controlled English prose, not a general
natural-language sentence segmenter. A span ends at a single ASCII `.`, `!`, or
`?`, followed by whitespace or the end of the body. A matching ASCII closing
double quote may immediately follow the terminator and is included in the span.
The next non-whitespace character must not be an ASCII lowercase letter or a
digit. Non-ASCII letters (including scientific labels such as `αβ:`) retain their
original offsets without an English capitalization inference. Decimal periods
directly between digits are internal punctuation.

The only recognized abbreviations are case-sensitive:

| Abbreviation | Required continuation; period remains inside the span |
| --- | --- |
| `No.` | Whitespace, then an ASCII digit, as in `lot No. 7 only after QA approval.` |
| `Dr.` | Whitespace, then an ASCII capitalized name, as in `Dr. Vale must approve release.` |
| `a.m.` / `p.m.` | Whitespace, then lowercase continuation, as in `5 p.m. unless QA grants an exception.` |

These abbreviations in other positions produce `boundary_uncertain`, including a
time abbreviation at end of body or before an uppercase continuation. Unknown
internal dots, numeric terminal tokens, tokens of three or fewer letters before
a period with following text, and these common ambiguous abbreviations are also
refused: `approx`, `art`, `cf`, `dept`, `e.g`, `est`, `etc`, `fig`, `i.e`, `inc`,
`ref`, `resp`, `rev`, `sec`, `vol`, `vs`. The list is a bounded detection policy;
it does not establish that every other word is linguistically unambiguous.

Ellipses, repeated/mixed terminators, brackets or parentheses, angle brackets,
unbalanced double quotes, punctuation inside a quote before its closing quote,
single/smart quotation marks, CJK sentence terminators, and non-whitespace ASCII
control characters are refused. Apostrophes strictly between alphabetic
characters are permitted. Newlines and tabs are whitespace, not independent
sentence boundaries. Markdown headings receive no special interpretation.

## Limits and historical evidence

Selection establishes literal containment and this declared punctuation policy.
It does not establish that a quote is true, complete, relevant, sufficient,
current, or supportive of a claim. A condition may live in another sentence,
section, or document. An unrecognized domain abbreviation can still look like
an ordinary full stop. Arbitrary-language coverage and corpus-wide incidence of
refusals are unmeasured. A future caller must retain source/packet identity and
its existing support and authorization gates.

Original source subject:
[`9685872827b37b55c981b88ad3177a2ed3b13533`](https://github.com/camerontjs-dot/biotech-rag-assistant/commit/9685872827b37b55c981b88ad3177a2ed3b13533).
Independent review publication:
[`4191e9b7809f76956330f0c01312ccdb09f8055e`](https://github.com/camerontjs-dot/biotech-rag-assistant/commit/4191e9b7809f76956330f0c01312ccdb09f8055e).
PR #50's rejected source and counterexample JSON are retained byte-for-byte in
`tests/fixtures/citation-span-selection-pr50/`. Its five author tests and 24
independent probes are retained byte-for-byte as
`tests/test_citation_spans_pr50_author.py` and
`tests/test_citation_spans_pr50_independent.py`; their assertions are unchanged.
The successor tests pin all four SHA-256 identities. Replaying known probes is
regression evidence, not a new independent review or semantic adjudication.

Run the successor and unchanged historical expectations with:

```bash
PYTHONPATH=src python -m pytest -q tests/test_citation_spans_*.py
```

A passing run does not retroactively qualify #50 and does not promote this
candidate. Wiring the helper into an answer or citation consumer is a separate
behavioral change requiring its own authority and verification.
