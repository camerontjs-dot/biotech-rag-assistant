# Chat adversarial fixture corpus

Synthetic, test-only. Used by `tests/test_chat_*.py` and `scripts/chat_ui_check.py`.

- `SOP-ADV-001` (Approved) contains an ordinary procedure paragraph and a "reviewer note"
  paragraph with embedded instructions aimed at a model, plus HTML/script markup. It checks that
  passage text reaches a model only as quoted data and is rendered as inert text.
- `SOP-ADV-002` (Obsolete) is a retired practice that only a status-blind search would use.
- `SOP-ADV-003`..`SOP-ADV-006` (Approved) are unrelated filler procedures. They exist because
  BM25 IDF degenerates on a two-chunk index (every score falls to the floor), so a realistic
  index size is needed for retrieval to behave as it does on the synthetic corpus.

If a document changes, recompute its SHA-256 and update the sidecar's `source_hash`;
`biotech-rag validate-corpus tests/fixtures/chat-adversarial` must pass.
