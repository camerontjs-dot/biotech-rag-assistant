# Retrieval baseline

The first baseline is BM25 over approved/effective document chunks.

The retriever indexes only chunks from documents whose metadata status is `Approved` or `Effective`. Draft, obsolete, and superseded documents can remain in the corpus for trap tests, but they do not enter the BM25 corpus.

The current score is a nomination signal. A high score means the chunk matched the query better than other indexed chunks under BM25. It does not mean the answer is true, compliant, or sufficient for a regulated decision.

## Fixed pilot query

The current smoke query is:

```text
viable excursion affected product lots immediate containment
```

Expected top chunk:

```text
SOP-QA-001_v1_0_chunk_002
```

That query exercises the status gate and chunk traceability without invoking answer generation.
