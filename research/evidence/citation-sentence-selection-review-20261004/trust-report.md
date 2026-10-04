# Biotech RAG Assistant trust-layer report

This report measures retrieval behavior and structural citation resolution over synthetic fixtures. `citation_resolves_to_retrieved_chunk` means a cited `chunk_id` appeared in retrieved results. It does not measure semantic support.

## Summary

- Suite: `synthetic-controlled-docs-trust-layer`
- Trust layer status: pass
- Cases passed: 24/24
- Overall status: pass

## Corpus/config

- Corpus directory: `<REVIEW_WORKSPACE>/review-citation-50/examples/synthetic-controlled-docs`
- Metadata files seen: 10
- Documents valid: 10
- Documents retrievable: 8
- Documents excluded by status: 2
- Retrieval method: `bm25`
- Top k: per_case
- Score floor: 0.0

## Metrics

- `case_pass_rate`: 24/24
- `retrieval_expectation_match_rate`: 24/24
- `stale_document_exclusion_rate`: 24/24
- `refusal_expectation_match_rate`: 6/6
- `citation_resolves_to_retrieved_chunk_rate`: 3/6
- `citation_expectation_match_rate`: 6/6
- `generated_answer_outcome_match_rate`: 24/24
- `generated_answer_citation_validation_rate`: 24/24

## Case table

| Case | Passed | Outcome | Hits | Fixture citation issues | Generated citation check | Issues |
|---|---:|---|---|---|---:|---|
| `valid-env-containment` | true | answer | SOP-QA-001_v1_0_chunk_002, SOP-QA-001_v1_0_chunk_003, SOP-QA-001_v1_0_chunk_001 | none | true | none |
| `missing-citation-env-containment` | true | answer | SOP-QA-001_v1_0_chunk_002, SOP-QA-001_v1_0_chunk_003, SOP-QA-001_v1_0_chunk_001 | missing_answer_citation | true | none |
| `hallucinated-citation-env-containment` | true | answer | SOP-QA-001_v1_0_chunk_002, SOP-QA-001_v1_0_chunk_003, SOP-QA-001_v1_0_chunk_001 | unresolved_citation | true | none |
| `obsolete-sterility-excluded` | true | refusal | none | none | true | none |
| `draft-cleaning-excluded` | true | refusal | none | none | true | none |
| `refusal-with-citation-is-caught` | true | refusal | none | refusal_has_citation, unresolved_citation | true | none |
| `water-action-limit` | true | answer | SPEC-QC-006_v3_0_chunk_002, SOP-QA-001_v1_0_chunk_002, SPEC-QC-006_v3_0_chunk_001 | n/a | true | none |
| `line-clearance-independent-check` | true | answer | SOP-OPS-007_v1_2_chunk_002, SOP-OPS-007_v1_2_chunk_001, SOP-QA-001_v1_0_chunk_003 | n/a | true | none |
| `env-investigation-record` | true | answer | SOP-QA-001_v1_0_chunk_003, SOP-QA-001_v1_0_chunk_002, SOP-QA-002_v1_1_chunk_003 | n/a | true | none |
| `deviation-major-escalation` | true | answer | SOP-QA-002_v1_1_chunk_002, SOP-QA-002_v1_1_chunk_001, SOP-QA-001_v1_0_chunk_002 | n/a | true | none |
| `deviation-closure-rule` | true | answer | SOP-QA-002_v1_1_chunk_003, SOP-QA-001_v1_0_chunk_002, SOP-QA-001_v1_0_chunk_003 | n/a | true | none |
| `document-current-version-rule` | true | answer | POL-DOC-003_v2_0_chunk_001, SOP-QA-001_v1_0_chunk_001, SOP-OPS-007_v1_2_chunk_002 | n/a | true | none |
| `document-draft-obsolete-rule` | true | answer | POL-DOC-003_v2_0_chunk_002, NOTE-TS-008_v1_0_chunk_002, SOP-OPS-007_v1_2_chunk_002 | n/a | true | none |
| `gowning-training-scope` | true | answer | TRN-QA-004_v1_0_chunk_001, TRN-QA-004_v1_0_chunk_002, SOP-QA-001_v1_0_chunk_001 | n/a | true | none |
| `gowning-requalification-trigger` | true | answer | TRN-QA-004_v1_0_chunk_002, TRN-QA-004_v1_0_chunk_001 | n/a | true | none |
| `balance-daily-check` | true | answer | CAL-ENG-005_v1_0_chunk_001, SPEC-QC-006_v3_0_chunk_002, SOP-OPS-007_v1_2_chunk_001 | n/a | true | none |
| `balance-calibration-failure` | true | answer | CAL-ENG-005_v1_0_chunk_002, SOP-QA-002_v1_1_chunk_002, SOP-OPS-007_v1_2_chunk_002 | n/a | true | none |
| `customer-requirement-intake` | true | answer | NOTE-TS-008_v1_0_chunk_001, NOTE-TS-008_v1_0_chunk_002 | n/a | true | none |
| `customer-conflict-review` | true | answer | NOTE-TS-008_v1_0_chunk_002, NOTE-TS-008_v1_0_chunk_001, POL-DOC-003_v2_0_chunk_002 | n/a | true | none |
| `water-sampling-missed-sample` | true | answer | SPEC-QC-006_v3_0_chunk_001, SOP-QA-001_v1_0_chunk_003, NOTE-TS-008_v1_0_chunk_002 | n/a | true | none |
| `line-clearance-pre-run` | true | answer | SOP-OPS-007_v1_2_chunk_001, SOP-OPS-007_v1_2_chunk_002, SOP-QA-002_v1_1_chunk_001 | n/a | true | none |
| `unsupported-lyophilizer-purge` | true | refusal | none | n/a | true | none |
| `unsupported-endotoxin-method` | true | refusal | none | n/a | true | none |
| `obsolete-and-draft-combined-trap` | true | refusal | none | n/a | true | none |

## Limits

This report exercises a synthetic corpus and deterministic BM25 retrieval. The generated answer is extractive: it copies retrieved spans and tags them with citations. It does not verify regulatory compliance, measure semantic support, or test an LLM.
