# Engineering review of automatic citation span candidate

## Disposition

**Do not qualify candidate `093fcd031138b8219722f4e9c888dec2d7ebc354` as the requested automatic enclosing-sentence selector.** The frozen contract probes passed 30 of 32 cases. Both failures cross paragraph boundaries. Post-freeze exploration also reproduces the material abbreviation-truncation family with `Coord.` and `Prof.`. The candidate implements a documented bounded punctuation policy, but that policy does not provide the stronger requested guarantees of complete enclosing sentences and no paragraph crossing.

This is an ordinary engineering review with knowledge of the historical failures. It is not a claim of semantic adjudication, clean-room construction, or training independence. The 32 probes were frozen before candidate documentation or implementation was read. Later exploration is separately labeled and stored.

## Subject and evidence identity

- Commit: `093fcd031138b8219722f4e9c888dec2d7ebc354`
- Git tree: `d7a96fe4bae53f30dbdcf1f179b3710bd1a5b5cf`
- `src/biotech_rag_assistant/citation_spans.py` SHA-256: `386749546e2cafaf237e69936dae894982b6d9592d0efc0594a2f8d83a2c4df5`
- `docs/citation-span-selection.md` SHA-256: `8477fbc9c883c1b07502da0ec0fa16c4edb0be663dbd361c3b3ad4d9f4775adc`
- Frozen 32-probe source SHA-256: `3666cec6252e3e3d074d49667cdc0f608c1bb8a5b907d39aa1db70de537fb101`
- Post-freeze six-probe source SHA-256: `f11f7de4bb738700d4b0e3729f02ede50c5a89492c09e72e65811ce772e3074b`

Both execution adapters asserted the subject commit before loading the module directly from its path. The frozen adapter additionally asserted the git tree and original probe hash. The environment was `/workspace/scratch/7b8946fc1488/biotech-test-env/bin/python`. No provider calls, GitHub writes, or modifications to the candidate were made by this reviewer. The final file does not make claims about a later author working tree.

## Frozen probe results

The set requires 7 ordinary exact selections, 9 refusals, and 16 complete-span-or-refusal outcomes. All 7 required ordinary selections passed. The original overlapping occurrence and `No. 7` limiting-clause regressions also passed. Quote matching remained exact and results retained body-relative Unicode codepoint offsets, including a preceding non-BMP character and CRLF paragraph offsets.

| Frozen failure | Body and quote | Actual result | Contract impact |
| --- | --- | --- | --- |
| `cross_paragraph_quote` | Body `Release is blocked\n\nuntil QA approval.`; quote `blocked\n\nuntil` | `selected`, whole body, `[0, 38)` | A quote spanning paragraphs is accepted. No single allowed paragraph-bounded sentence can enclose it. |
| `unpunctuated_first_paragraph` | Body `Release is permitted\n\nOnly after QA approval.`; quote `Release is permitted` | `selected`, whole body, `[0, 45)` | The selector silently adds the second paragraph to the first fragment. Expected either exactly the first fragment or refusal. |

The cause is structural: `_next_nonspace` treats every `isspace()` character alike (source lines 33–36), and the scan has no paragraph-boundary guard (lines 75–133). The candidate documentation explicitly says newlines are whitespace rather than sentence boundaries (lines 63–64). This is a conflict between the stated intended no-cross-paragraph contract and the candidate's narrower punctuation policy, not an undocumented implementation deviation.

## Post-freeze exploration

These probes were created only after the frozen 32 were executed and the code/policy read. They are additional counterexamples, not part of the preimplementation score.

| Case | Exact input | Actual selected result |
| --- | --- | --- |
| Limiting-clause truncation, root supplied | Body `Release is allowed only after Coord. Smith signs the authorization.`; quote `Release is allowed` | `Release is allowed only after Coord.` at `[0, 36)` |
| Sentence-prefix loss, root supplied | Body `Prof. Vale must approve release. Retain the record.`; quote `must approve release` | `Vale must approve release.` at `[6, 32)` |
| Limiting-clause truncation, reviewer exploration | Body `Release is allowed by Prof. Vale only after QA approval.`; quote `Release is allowed` | `Release is allowed by Prof.` at `[0, 27)` |
| Blank-line variants | LF blank line, CRLF blank line, and Unicode U+2029 paragraph separator between `Release is permitted` and `Only after QA approval.` | Every variant selects across the paragraph boundary. |

For the first three examples, a complete enclosing sentence or safe refusal is acceptable; the actual shortened span is neither. Period decisions accept tokens longer than three letters unless they occur in a finite uncertainty list (source lines 115–127). An unknown abbreviation followed by an uppercase word therefore creates a false sentence boundary. Documentation lines 51–57 and 68–73 acknowledge this residual ambiguity, which is an honest limitation but does not fulfill the requested no-truncation guarantee. Expanding the denylist to include these exact tokens would leave the failure mechanism intact.

## Scope and positive findings

The helper only receives `body` and `quote`; it does not fetch sources, consult headings, authorize text, or claim semantic support. A quote absent from the authorized body is refused even when the fixture separately describes matching heading text. This verifies absence of fallback, not the authority of caller-supplied text. Markdown headings already included in the input body receive no special treatment; the candidate explicitly documents that limit.

Source reference inspection found no consumer of `select_enclosing_sentence` or `sentence_spans` elsewhere in `src`. The helper is unconnected to API and CLI behavior. The author suite's reported 181 passes were not independently rerun here because the decisive local counterexamples already resolve the review; its passing count should remain labeled author/parent execution evidence. The historical known probes are useful regression evidence, not new semantic or independent qualification.

## Recommended minimal mechanical capability

A useful enforceable successor is an explicitly named authorized-span validator: require caller-supplied body-relative bounds, refuse when bounds are missing or invalid, require one globally unique exact quote including overlapping-occurrence detection, require the quote to lie inside the supplied span, return precisely the authorized source slice, and mechanically refuse paragraph-crossing spans. Do not trim, widen, normalize, or infer sentence boundaries.

Correctness and completeness of the supplied sentence boundary, and authority to use it, must remain caller preconditions. This helper cannot prove them. This is a changed contract and should have a fresh probe set. Supplying expected spans to the original automatic-selector tests would not constitute a passing replay of their old expectations. Preserve this rejected candidate, the original frozen 30/32 result, and the post-freeze counterexamples unchanged.

## Reproduction commands

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/7b8946fc1488/biotech-test-env/bin/python /workspace/scratch/7b8946fc1488/citation-review/run_frozen_candidate.py
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/7b8946fc1488/biotech-test-env/bin/python /workspace/scratch/7b8946fc1488/citation-review/run_postfreeze_candidate.py
```

The adapters intentionally reject any other HEAD. A later author revision must not overwrite these results or be described as the same reviewed subject.

## Artifacts

- `preimplementation_probes.json`, `preimplementation_probes.sha256`, `probe_freeze_record.txt`: frozen contract-derived input and expectations.
- `score_probes.py`, `run_frozen_candidate.py`: target-independent scoring and frozen target adapter.
- `frozen_candidate_outcomes.json`, `frozen_candidate_report.json`: exact raw outputs and 30/32 evaluation.
- `postfreeze_probes.json`, `postfreeze_probes.sha256`, `run_postfreeze_candidate.py`, `postfreeze_candidate_report.json`: separately labeled exploratory evidence.
