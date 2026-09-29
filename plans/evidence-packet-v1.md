# EvidencePacket v1 implementation protocol

Status: bounded implementation protocol for Slice 4 on maintained BM25 `main`.

## Objective

Create a deterministic authority boundary between retrieval and any future generator without
changing the public answer path.

Deliver:

- typed `RetrievalNomination` records;
- deterministic `EvidencePacket` assembly with `ep1:` identity;
- mechanical admission, deduplication and evidence-budget handling;
- optional same-section expansion behind an explicit flag;
- CLI and API packet-inspection surfaces with parsed-object parity;
- cross-version deterministic identity tests on Python 3.11, 3.12 and 3.13.

No generator, semantic support claim, CAL integration, or public answer replacement belongs in this
slice.

## Maintained retrieval authority

This slice uses the maintained `bm25` retrieval path on current `main`.

The frozen retrieval programme in PRs #7/#8 did not qualify a replacement retrieval method under
its preregistered TEST gate. BM25 therefore remains the maintained retrieval authority for this
slice.

## v1 corpus identity adaptation

The generative-RAG plan describes corpus identity as a corpus-manifest hash. The maintained v1
corpus has no committed corpus manifest.

Do not invent a file and call it authoritative.

For v1, compute:

`corpus1:<sha256>`

over canonical JSON of the validated corpus's sorted document records. Each record contains only
portable, authority-bearing metadata:

- `doc_id`
- `doc_type`
- `version`
- `status`
- `effective_date`
- `review_due_date`
- `department`
- repository-relative `source_file_path`
- verified `source_hash`

Local filesystem roots and wall-clock values are excluded.

Future manifest-backed corpora may supply their manifest hash as the corpus identity without changing
the EvidencePacket schema.

## Query and retrieval configuration identities

Normalize a query by:

1. Unicode NFC normalization;
2. trimming leading/trailing whitespace;
3. collapsing internal whitespace to one ASCII space;
4. case-folding.

Stable query ID:

`q1:<sha256(normalized-query UTF-8)>`

Retrieval configuration ID:

`rc1:<sha256>`

over canonical JSON of the full `RetrievalConfig` record. No runtime timestamp is included.

## RetrievalNomination v1

Required fields:

- `nomination_id`
- `query_id`
- `chunk_id`
- `doc_id`
- `version`
- `status`
- `source_hash`
- `char_start`
- `char_end`
- `section_heading`
- `retrieval_signal`
- `raw_score`
- `rank`
- `retrieval_config_id`
- `corpus_identity`
- optional `parent_context_id`
- optional `authorization_scope`
- `nomination_kind`
- `retrieval_reasons`
- `representation_level`
- `section_role`
- `authority_class`
- `token_estimate`
- `expansion_handle`

For the maintained path:
- retrieval signal = `bm25`;
- nomination kind = `chunk`;
- representation level = `chunk`.

Scores and ranks are diagnostics. They do not represent evidentiary support or confidence and do not
participate in packet identity.

### Authority classes

`authority_class` is descriptive and does not create a universal trust score:

| doc_type | authority_class |
| --- | --- |
| Policy | `controlled_policy` |
| SOP | `controlled_procedure` |
| Specification | `controlled_specification` |
| CalibrationNote | `technical_record` |
| TechnicalNote | `technical_record` |
| TrainingNote | `training_aid` |
| DeviationExample | `worked_example` |

Slice 4 does not reorder, suppress or admit evidence based on this class. Later conflict-resolution
policy must be separately justified.

### Section roles

Deterministic heading labels only:

- heading containing `revision` or `history` -> `revision_history`
- heading containing `reference` -> `references`
- heading containing `definition` -> `definitions`
- heading containing `responsibilit` -> `responsibilities`
- otherwise -> `normative`

This is mechanical metadata, not semantic validation.

## Admission and budget

Default packet policy:

- only Approved/Effective nominations may be admitted;
- exact source-span duplicates are suppressed;
- preserve retrieval order;
- default max admitted items = retrieval `top_k`;
- default token budget = 2,000 estimated tokens;
- deterministic token estimate uses a repository-local regex approximation, not a provider
  tokenizer;
- a candidate that would exceed the token budget is excluded with reason
  `evidence_budget`;
- excluded reasons are counted mechanically.

No score threshold is introduced beyond the existing retrieval configuration.

## Optional same-section expansion

Off by default.

When enabled, after a retrieved chunk is admitted:
- inspect other retrievable chunks with the same `doc_id`, version and section heading;
- order them by chunk index;
- suppress duplicates;
- admit only while item and token budgets allow;
- set `nomination_kind=section_expansion`;
- set `parent_context_id` to the parent nomination ID;
- expansion does not change or erase the retrieval nomination that caused it.

No cross-reference expansion is implemented in Slice 4.

## EvidencePacket v1

Packet fields:

- `schema_version = "1"`
- original query
- normalized query
- stable query ID
- corpus identity
- retrieval config ID
- optional aperture ID
- admitted evidence records with admission provenance
- excluded-candidate summary
- evidence budget
- diagnostics
- packet identity

Packet identity:

`ep1:<sha256>`

over canonical compact sorted-key JSON containing only:

- schema version;
- normalized query;
- corpus identity;
- retrieval config ID;
- aperture ID;
- ordered admitted source identities as
  `(chunk_id, doc_id, version, status, source_hash, char_start, char_end, nomination_kind)`;
- excluded-candidate summary;
- evidence budget.

Raw scores, ranks and other diagnostics are excluded from the hash.

No generated content belongs in the packet.

## Inspection surfaces

CLI command:

`biotech-rag inspect-packet <corpus> --query ...`

API route:

`POST /evidence-packet`

The API is pure transport over the same packet builder. Parsed API JSON must equal parsed CLI JSON
for the same input.

Neither surface is generation.

## Acceptance

Required:

1. identical corpus/query/config/policy inputs produce the same `ep1:` identity repeatedly;
2. an exact pinned fixture identity matches on Python 3.11, 3.12 and 3.13 CI;
3. changing only raw scores leaves packet identity unchanged;
4. changing source identity, admitted order, query, retrieval config, exclusion summary or budget
   changes packet identity;
5. local absolute corpus path does not affect corpus or packet identity;
6. duplicate nominations are deterministically suppressed;
7. budget exclusions are deterministic;
8. section expansion is off by default and explicit when enabled;
9. every packet item remains Approved/Effective;
10. CLI/API packet inspection parity passes;
11. all existing retrieval, answer, evaluation and Pages parity tests remain green.

A pass establishes a deterministic evidence boundary only. It does not establish semantic support,
generation quality, or regulated-system validation.
