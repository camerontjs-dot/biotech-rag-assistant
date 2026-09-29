# controlled-docs-v2.1 PROSPECTIVE authoring specification

## Objective

Author a new sealed PROSPECTIVE set for `controlled-docs-v2.1`.

The set is a fresh held-out evaluation object. It is authored from the controlled-document corpus
and this specification only. Do not run retrieval models, inspect retrieval scores, or tune questions
against system output while authoring.

The sealed bytes remain outside Git. Only a commitment and bounded provenance may be imported later.

## Information aperture

Allowed:
- `benchmarks/controlled-docs-v2.1/corpus/**`
- `benchmarks/controlled-docs-v2.1/corpus_manifest.json`
- committed DEV/TEST files only as schema/format examples
- this specification
- `research/controlled_docs_v21_prospective_acceptance.py`

Do not inspect:
- any prior sealed PROSPECTIVE directory or its questions/gold;
- pull requests, issue discussion or experiment artifacts;
- retrieval-model output, scores, ranks or comparison reports;
- benchmark discriminator results;
- candidate retrieval implementations for the purpose of tuning cases.

If prior sealed questions or model results are exposed, stop and report contamination.

## Sealed layout

Create a directory outside the repository containing exactly:

```text
cases.jsonl
families.json
gold.jsonl
```

Do not commit these files.

### Runtime cases

Each line in `cases.jsonl` contains only:

- `case_id`
- `split` = `PROSPECTIVE`
- `question`
- `query_style` = `natural`, `keyword` or `identifier`
- `aperture_id` = `full`
- `top_k` = 3
- `schema_version` = `2.1`

Use IDs `C-PROS21-0001` through `C-PROS21-0030`.

### Evaluator-only families

`families.json` maps each case ID to:

- `case_id`
- `family`
- `family_name`
- `process_area`
- `tags`

### Evaluator-only gold

Use the existing span-gold schema from DEV/TEST. Character offsets are Python-character offsets over
the exact UTF-8-decoded source text and every non-null `span_text` must equal
`raw_text[char_start:char_end]`.

## Held-out process areas

Use only these three process areas, which do not appear in committed DEV/TEST questions:

- complaints-and-returns
- document-control
- training-and-gowning-qualification

Author exactly 10 cases in each process area.

Do not move any committed DEV/TEST case into PROSPECTIVE and do not reuse a committed question.

## Family counts

Use this exact 30-case distribution:

| Family | Kind | Cases |
| --- | --- | ---: |
| B01 | lexical direct | 2 |
| B02 | paraphrase, low overlap | 4 |
| B03 | identifier lookup | 2 |
| B04 | numeric threshold | 4 |
| B05 | table cell | 2 |
| B06 | condition / exception | 2 |
| B07 | negation / polarity | 1 |
| B08 | multi-passage | 2 |
| B09 | supersession / stale value | 2 |
| B10 | fact not stated | 3 |
| B11 | out of scope / uncovered | 2 |
| B12 | hard lexical distractor | 2 |
| B13 | authority conflict | 1 |
| B14 | long-document burial | 1 |

Mix question styles. The acceptance checker requires at least 15 natural, 5 keyword and 5
identifier-led questions.

## General authoring rules

- Questions are written from the process need and document structure, not by copying decisive prose.
- A case has one primary family. Secondary properties belong in tags.
- Answer cases must have decisive evidence in Approved/Effective documents.
- `not_stated` cases have relevant approved context but no decisive answer in the retrievable corpus.
- Refusal cases have no supported answer under the prospective corpus aperture.
- Stale/draft/obsolete facts may appear only as evaluator-only traps. They never become admissible
  answer evidence.
- Keep runtime files free of family labels, gold, rationales and answer values not naturally present
  in the question.
- Do not write meta-text announcing which passage is correct or which case is adversarial.
- Do not change corpus or metadata bytes.

## Family-specific constraints

### B01 lexical direct

Coverage of the question against its decisive span(s), using the repository's `coverage()`, must be
at least 0.60.

### B02 paraphrase

Coverage against decisive span(s) must be at most 0.30.

### B03 identifier lookup

The question must require resolving an opaque document, room, form, equipment, material or other
identifier rather than relying only on a descriptive phrase.

### B04 numeric threshold: numeric-collision rule

Every B04 case must:

1. have exactly one decisive Approved/Effective span containing the requested numeric fact;
2. omit the answer value from the question;
3. have at least three Approved/Effective numeric `hard_negative` spans;
4. have at least one numeric hard negative in the same governing document as the decisive span;
5. make the alternatives differ materially by value, unit, condition, grade, material, instrument,
   alert/action role, duration type, sample type or another authority-bearing qualifier;
6. contain enough condition/context in the question for exactly one target to be correct.

Use multiple collision shapes. Do not repeat one table template for all four cases.

### B05 table cell

The decisive evidence must be a Markdown table row or table cell.

### B06 condition / exception

The decisive evidence must include a condition, exception or qualifier material to the answer.

### B07 negation / polarity

The answer depends on preserving a negative or prohibitive meaning.

### B08 multi-passage

The answer requires at least two decisive passages, represented by a non-null joint group.

### B09 supersession / stale value

Include evaluator-only stale/draft/obsolete evidence whose value conflicts with or could distract
from the current governing evidence.

### B10 fact not stated

Expected disposition is `not_stated`. Include material approved context but no decisive answer
span.

### B11 out of scope / uncovered

Expected disposition is `refusal`; do not manufacture an answer span.

### B12 hard lexical distractor

Include at least one Approved/Effective `hard_negative` with strong topical overlap.

### B13 authority conflict

The decisive evidence must come from the governing source and at least one Approved/Effective
training-note or lower-authority passage must conflict or lag.

### B14 long-document burial

The decisive span must be deep inside an SOP of at least 3,500 words.

## Independence and freeze discipline

Do not run BM25, dense retrieval, semantic retrieval, hybrid retrieval, reranking, generation,
answerability scoring or the Slice 2 discriminator while authoring.

Do not alter cases after seeing any retrieval-model result. If the first frozen prospective object
later fails a discriminator, preserve it and create another separately identified candidate rather
than editing it in place.

## Commitment

After the structural acceptance checker passes, compute the sealed-directory commitment as SHA-256
over the text of one SHA256SUM-style line for each of the three files, sorted by filename byte order:

```text
<sha256>  cases.jsonl
<sha256>  families.json
<sha256>  gold.jsonl
```

Each line ends in LF. The acceptance checker prints this digest.

Do not create or edit the v2.1 benchmark freeze receipt in this authoring task.

## Required local verification

Run with repository imports available without modifying the checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python research/controlled_docs_v21_prospective_acceptance.py \
  --benchmark benchmarks/controlled-docs-v2.1 \
  --prospective <sealed-directory>
```

The checker must return `PASS_FOR_V21_PROSPECTIVE_SEAL` before handoff.

## Return receipt

Return:

1. final repository HEAD used for authoring;
2. sealed-directory path, redacted for public reporting if necessary;
3. disposition;
4. commitment SHA-256;
5. case count, family counts, process-area counts and query-style counts;
6. B04 case IDs and hard-negative counts;
7. full checker JSON;
8. sealed file SHA-256 values;
9. post-run repository cleanliness;
10. explicit contamination status.

Stop after the receipt. Do not run any retrieval experiment or modify supervisor branches/pull requests.
