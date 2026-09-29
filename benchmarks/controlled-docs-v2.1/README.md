# controlled-docs-v2.1


> **Construction state.** This directory is not frozen and must not be used for benchmark claims yet. It was forked from frozen `controlled-docs-v2` after PR #6 showed that the naive dense control achieved 11/11 B04 decisive-span recall@3. The v2 corpus bytes are retained, while fresh-context numeric-collision cases and a new freeze/prospective identity are still pending. The predecessor remains authoritative at `benchmarks/controlled-docs-v2/`.

controlled-docs-v2.1 is an under-construction successor benchmark based on the frozen controlled-docs-v2 synthetic corpus of 65 controlled documents for a fictional aseptic manufacturing site, with 120 committed questions and span-level gold. It is built to test whether a retrieval and answering pipeline finds the passage that governs, reads document status correctly, and declines to answer when the corpus does not say. The text is synthetic, so a result on it says nothing about how a system behaves on real controlled documents.

No real organizations, products, persons or sites appear. No value is attributed to a real regulation or guidance, and no text comes from private repositories, employer documents or client material. Identifiers such as `EQ-0417`, `RM-289` and `FRM-QA-501` are opaque codes.

This successor does not replace or rewrite frozen controlled-docs-v2. Its purpose is the bounded B04 numeric-collision repair defined in `../../research/controlled-docs-v2.1-b04-hardening-protocol.md`. The inherited checksum and freeze-receipt files are deliberately absent until a new v2.1 candidate is complete.

## What is in the tree

| Path | Contents | Mounted into a runtime |
| --- | --- | --- |
| `corpus/documents/`, `corpus/metadata/` | 65 documents and their sidecars | yes |
| `cases/dev_cases.jsonl`, `cases/test_cases.jsonl` | 40 DEV and 80 TEST questions, runtime fields only | yes |
| `adversarial/corpus/`, `adversarial/cases.jsonl` | a separate bundle: 9 documents, 3 questions | yes, in its own runtime |
| `evaluator_only/` | gold spans, case families, relationships, lexical overlap | no |
| `adversarial/evaluator_only/` | gold for the adversarial questions | no |
| `corpus_manifest.json`, `SHA256SUMS`, `freeze_receipt.json` | document list and counts, file hashes, tree hash, PROSPECTIVE commitment | not applicable |

A runtime case carries `case_id`, `split`, `question`, `query_style`, `aperture_id`, `top_k` and `schema_version`, and nothing else. Family labels, gold, rationales and overlap diagnostics stay under `evaluator_only/` and must not be mounted into the system under test.

The PROSPECTIVE set is not in the repository. It has 30 questions with gold, covering all 14 families, in the three process areas that appear in no committed question. Only its SHA-256 is committed, in `freeze_receipt.json`.

## The corpus

- 65 documents: 44 Effective (the only retrievable ones), 13 Superseded, 4 Draft and 4 Obsolete. By type: 36 SOPs, 10 specifications, 12 training notes, 3 technical notes, 2 policies, 1 calibration note, 1 worked deviation example.
- 14 process areas, each with 2 to 4 retrievable documents.
- 17 regular SOPs of 996 to 1,685 words. Four long SOPs, `SOP-MF-207`, `SOP-QC-214`, `SOP-QC-236`, `SOP-TR-021`, run 4,278 to 4,594 words with 44 to 53 sections grouped under part headings. Every other document is flat.
- 104 tables in the retrievable documents. Every process area states at least 26 distinct quantities with units.
- 123 references from one retrievable document to another, 6 to documents that exist only as superseded, draft or obsolete versions, and 91 to documents that are not in the corpus. Every process area defers at least 2 parameters to such an absent document, for example "the interval comes from the qualification report" with the report's code and nothing else.
- 9 training notes state an earlier value than the SOP that governs them, and none says so. Old values also sit in revision-history tables and in the 13 superseded predecessors. Each predecessor is a full document, at least 74 percent of its successor's length.
- Current versions take effect between 2025-03-03 and 2026-07-06. The four drafts are dated 2026-12-07 to 2027-02-01, after the as-of date of 2026-09-26.

## Questions and gold

The committed questions are split by process area, so no area appears in more than one split. DEV covers CAPA, environmental monitoring, equipment calibration and temperature-controlled storage and shipping. TEST covers batch record review and QA disposition, change control, cleaning and line clearance, deviations, stability, supplier qualification and incoming materials and water systems.

| Family | Case kind | DEV | TEST | Committed |
| --- | --- | --- | --- | --- |
| B01 | lexical direct | 3 | 7 | 10 |
| B02 | paraphrase, low overlap | 4 | 8 | 12 |
| B03 | identifier lookup | 3 | 5 | 8 |
| B04 | numeric threshold | 4 | 7 | 11 |
| B05 | table cell | 3 | 5 | 8 |
| B06 | condition or exception | 3 | 5 | 8 |
| B07 | negation or polarity | 2 | 3 | 5 |
| B08 | multi-passage | 3 | 7 | 10 |
| B09 | supersession, stale value | 3 | 7 | 10 |
| B10 | fact not stated | 3 | 11 | 14 |
| B11 | out of scope | 3 | 5 | 8 |
| B12 | hard lexical distractor | 2 | 4 | 6 |
| B13 | authority conflict | 2 | 3 | 5 |
| B14 | long-document burial | 2 | 3 | 5 |

Committed and sealed questions together meet or exceed the family targets in the plan. Of the 120 committed questions, 98 have an answer, 14 are not stated, and 8 are refusals: 5 off-domain and 3 in-domain but uncovered. By query style, 78 are natural, 18 identifier and 24 keyword. Typos appear in 15 questions (12 committed, 3 sealed), none of them in the lexical-direct or paraphrase families, whose overlap caps a typo would move.

Each case has one gold row per relevant passage, classed as `decisive_support`, `decisive_exception`, `material_context`, `hard_negative`, `stale_trap` or `distractor`. Offsets are Python character offsets (`offset_unit: python_char`), and `span_text` equals `text[char_start:char_end]` for the document version named in the row. A `required_facts` value is at most 60 characters and appears in its span. A `forbidden_facts` value is an earlier or wrong value that occurs only in non-retrievable documents, revision-history sections or passages labelled as distractors. A refusal has one row with null fields. `evaluator_only/lexical_overlap.json` holds `coverage(question, decisive spans joined by newline)`, or the material-context spans for a not-stated case, computed on the final question text.

## How it was made

A language model drafted the text: Anthropic `claude-sonnet-5`, in an interactive coding session with no separate API calls. The work went in passes. Fourteen per-area briefs came first. The 44 current documents and the 4 obsolete ones were each written in their own step from their brief. Questions were drafted from the briefs, personas and titles, and gold was adjudicated against the documents afterwards. The PROSPECTIVE set was written last, in a separate pass, and sealed.

The questions were not kept blind to the documents. After the first drafts, some were reworded to meet the overlap bands and to name something distinctive, and about a third were rewritten as keyword or identifier-led queries, with the documents in view. Ten paragraphs gained a sentence after the gold was adjudicated, each stating a quantity other than the one a question asks for. Their gold rows were re-anchored, and the cases were not adjudicated again. The sealed questions had the same adjustments.

Deterministic code produced identifiers, sidecars, file names, offsets, hashes, relationships, receipts and checks, and applied the authored edit lists for revisions. It did not generate prose. The briefs and prompt templates stay outside the repository. There were no separate model calls, so there are no verbatim prompts: the 9 templates are the written instructions for each kind of step, recorded after most documents were drafted, and `corpus_manifest.json` holds the SHA-256 of each along with the provider, the model ID and a configuration hash. This repository cannot regenerate the tree, and the frozen bytes are the corpus.

## Verifying the tree

From the benchmark root:

```
sha256sum -c SHA256SUMS
find . -type f ! -name SHA256SUMS ! -name freeze_receipt.json | sed 's|^./||' | LC_ALL=C sort | xargs sha256sum | sha256sum
biotech-rag validate-corpus corpus
biotech-rag validate-corpus adversarial/corpus
```

The second command must print the `tree_sha256` in `freeze_receipt.json`. The PROSPECTIVE commitment uses the same recipe over the sealed directory, which holds `cases.jsonl`, `families.json` and `gold.jsonl`; the receipt spells out both recipes.

The tree was also run through an independent acceptance script, `check_corpus_v2.py`, which is not part of the tree. It reports 0 failures across 44 checks with the sealed directory supplied through `--prospective`, and the full output is in the description of the import pull request. That script checks mechanics and a set of shortcuts: duplicate or templated questions, self-announcing near-miss text, a single phrase that separates not-stated passages from answerable ones, and BM25 missing lexical-direct questions.

## Deviations from the plan

Appendix A of the corpus v2 plan, `plans/public-generative-rag-v2.md`, is the specification. This tree departs from it, or reads it narrowly, in these ways.

1. **Predecessors and drafts are copy-and-edit.** The 13 superseded predecessors and the 4 drafts were made by copying the current version and applying an authored edit list: changed values, changed wording, a rewritten revision-history table. They were not written from scratch in separate steps. Their unchanged text is therefore identical to the current version's, which is also how a real revision reads. The 4 obsolete documents were written separately.
2. **The adversarial bundle is round 1's, unchanged.** `adversarial/` is byte-identical to the round-1 tree: 9 documents and 3 questions. It was not regenerated or extended. It is loaded, hashed and scanned for private paths like the rest of the tree, but the length, quantity, cross-reference and shared-sentence checks apply to `corpus/` only.
3. **Nesting is limited.** Only the four long SOPs have `###` sections under part headings. The other documents use `##` sections alone.
4. **File names carry version and status for non-current versions.** Appendix A gives `<DOC-ID>-<slug>.md`, which would collide for two versions of one ID, so a superseded, draft or obsolete version is named `<DOC-ID>-v<major>-<minor>-<status>-<slug>.md`.
5. **`relationships.json` has an extra key and a fuller `references` list.** Besides `supersedes` and `lags` it holds `proposed_revisions` for the drafts. `references` lists every document code that a retrievable document cites, including codes of documents that are not in the corpus, each with a `kind` of `retrievable`, `non_retrievable_only` or `absent`. Round 1 left it empty.
6. **The manifest records more than Appendix A requires.** It adds counts by type, status, area, family and split, and the provenance fields above.
7. **Documents are plain ASCII.** Units and symbols are spelled out (`degrees C`, `uS/cm`, `plus or minus`), so a scan for hidden Unicode has no legitimate non-ASCII text to allow for.
8. **Some questions have typos.** They are query noise and part of the design, not transcription errors.

## What this does not establish

- Performance on real controlled documents. The documents, questions and gold came from one authoring process, and the questions were adjusted with the documents in view, so their vocabulary likely lines up with the documents more closely than it would in field data.
- That the gold is right beyond one adjudication. It was adjudicated once and checked mechanically, and no second coder reviewed it. The ten late sentences were checked against the questions in their areas, not adjudicated case by case.
- That the benchmark separates good systems from poor ones. The acceptance script rules out specific shortcuts, and the tree was corrected against its output, so a pass shows those shortcuts are closed and nothing more. Separating systems needs baselines run against this tree, and that has not been done.
- Held-out documents. PROSPECTIVE holds out questions and process areas, and its documents are in the same runtime corpus as DEV and TEST.
