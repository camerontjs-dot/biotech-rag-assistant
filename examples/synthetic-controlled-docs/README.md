# Synthetic controlled-document corpus

This corpus is fictional. It exists to exercise the retrieval pilot without using client records, patient data, batch records, or real controlled documents.

The metadata sidecars model the fields that matter for controlled retrieval: document ID, title, version, status, source path, and source hash. Draft and obsolete documents are included so the status gate can be tested, but they must not enter retrieval context.

Malformed metadata fixtures live under `tests/fixtures/`, not here. This public demo corpus should validate cleanly.
