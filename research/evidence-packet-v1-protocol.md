# Slice 4 — RetrievalNomination + EvidencePacket v1 protocol

Status: implementation protocol after terminal Slice 3 retrieval selection.

## Objective

Create the hard evidence seam before any generative model is introduced.

The retained retrieval baseline is `bm25_current`. Slice 3 challengers are research evidence only
and do not change this contract.

## Core objects

### RetrievalNomination v1

A nomination records why a source span was proposed before policy admission.

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
- `nomination_kind`
- `retrieval_reasons`
- `representation_level`
- `authority_class`
- `token_estimate`
- `expansion_handle`

Optional:
- `parent_context_id`
- `authorization_scope`
- `section_role`

Raw scores are diagnostics only. They are never treated as support/confidence and are excluded from
packet identity.

### EvidencePacket v1

An immutable packet assembled after deterministic admission.

Fields:
- `schema_version = "ep1"`
- normalized query + stable `query_id`
- `corpus_identity`
- `retrieval_config_id`
- optional evaluation `aperture_id`
- ordered admitted nominations
- exclusion summary by mechanical reason
- evidence budget
- `packet_id = ep1:<sha256>`
- diagnostics outside the identity payload

No generated content belongs in a packet.

## Stable identities

Canonical JSON:
- UTF-8
- sorted keys
- compact separators
- no timestamps

Query normalization:
- trim leading/trailing whitespace;
- collapse internal whitespace to one ASCII space;
- preserve case and punctuation.

`query_id`:
`q1:<sha256(canonical normalized query UTF-8)>`

`retrieval_config_id`:
`rc1:<sha256(canonical RetrievalConfig JSON)>`

`nomination_id`:
`nom1:<sha256(canonical query/chunk/signal/config/corpus identity fields)>`

Packet identity hashes exactly:
- schema version;
- normalized query;
- corpus identity;
- retrieval config ID;
- aperture ID;
- ordered admitted item tuples:
  `(chunk_id, doc_id, version, status, source_hash, char_start, char_end, nomination_kind)`;
- exclusion summary.

Scores, ranks, token estimates, authority labels and diagnostics remain outside that hash.

## Corpus identity

For corpora containing `corpus_manifest.json`:
- hash the exact manifest bytes;
- identity: `cm1:file:<sha256>`.

For legacy corpora without a manifest:
- derive a canonical manifest containing sorted validated document records:
  `(doc_id, version, status, source_hash, source_file_path)`;
- identity: `cm1:derived:<sha256>`.

The two namespaces are intentionally distinct. The derived legacy identity is compatibility support,
not a claim that a historical manifest file existed.

## Authority class v1

This is a deterministic ordering/admission label, not a statement that a source is true.

- Policy: `policy`
- Specification: `specification`
- SOP: `procedure`
- TechnicalNote: `technical_note`
- CalibrationNote: `calibration_note`
- TrainingNote: `training_note`
- DeviationExample: `example`

No cross-document conflict resolution is introduced in Slice 4. Authority class is carried forward
for later policy and inspection.

## Admission policy v1

Input nominations are ranked nominations from the status-gated retriever.

Mechanical admission:
1. reject any nomination whose status is not Approved/Effective;
2. suppress duplicate source spans by
   `(source_hash, char_start, char_end)`;
3. preserve nomination order;
4. admit while both budgets hold:
   - max items, default 3;
   - max context characters, default 12,000;
5. exclusions are counted by reason:
   - `status_not_retrievable`
   - `duplicate_source_span`
   - `item_budget_exhausted`
   - `context_budget_exhausted`

`token_estimate` is a deterministic model-agnostic estimate:
`ceil(len(text.encode("utf-8")) / 4)`.
It is diagnostic and excluded from packet identity.

## Expansion

Section expansion is implemented behind an explicit disabled-by-default flag.

It must be tested independently from ranking and must preserve exact source provenance.
No cross-reference expansion is admitted in Slice 4.

## Inspection surfaces

Add:
- CLI `evidence-packet` command;
- API `POST /evidence-packet`.

Both surfaces call the same core builder and return the same packet projection.

## Gate

For identical corpus/query/config/admission settings:
- Python 3.11, 3.12 and 3.13 produce the same `packet_id`;
- changing raw scores without changing admitted identities does not change `packet_id`;
- changing admitted source identity does change `packet_id`;
- CLI and API JSON are equal apart from transport-only audit behavior;
- stale/non-retrievable content cannot enter an admitted packet;
- generated content is absent by schema.

This slice does not add generation and does not claim semantic support.
