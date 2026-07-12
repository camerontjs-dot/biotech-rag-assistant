# Trust-layer evaluation baseline

The trust-layer evaluation suite lives at `examples/synthetic-controlled-docs/evaluation/golden-questions.json`.

It has 24 synthetic cases. The cases exercise expected source retrieval, unsupported-query refusal, draft and obsolete document exclusion, current-version lookup, missing citations, hallucinated citations, and a refusal answer that incorrectly includes a citation.

The report uses the metric `citation_resolves_to_retrieved_chunk`. This metric means a cited `chunk_id` appeared in the retrieved result set. It does not mean the cited chunk supports the answer.

Current expected smoke result:

```text
trust_layer_status: pass
case_pass_rate: 24/24
retrieval_expectation_match_rate: 24/24
stale_document_exclusion_rate: 24/24
refusal_expectation_match_rate: 6/6
citation_resolves_to_retrieved_chunk_rate: 3/6
citation_expectation_match_rate: 6/6
generated_answer_outcome_match_rate: 24/24
generated_answer_citation_validation_rate: 24/24
```

The `3/6` citation-resolution rate is expected. The suite includes missing-citation, hallucinated-citation, and refusal-with-citation traps. The more important harness signal is `citation_expectation_match_rate`, which should stay at `6/6` for the fixture traps.

The generated answer gates are separate. `biotech-rag answer` copies retrieved spans, tags each block with `[source: N]`, and validates those structured citations inside answer assembly. It does not use an LLM or measure semantic support.

The Markdown report has these sections:

- Summary
- Corpus/config
- Metrics
- Case table
- Limits

Run it with:

```bash
.venv/bin/biotech-rag evaluate \
  examples/synthetic-controlled-docs \
  examples/synthetic-controlled-docs/evaluation/golden-questions.json \
  --markdown-out build/evaluation-report.md \
  --json-out build/evaluation-report.json
```
