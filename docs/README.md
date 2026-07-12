# Static demo (GitHub Pages)

A fully **client-side** version of the Biotech RAG Assistant chat demo — no backend. It runs the
same deterministic retrieval the Python core runs (tokenize → BM25Okapi → `score_floor` →
deterministic tie-break → the ADR-012 coverage relevance gate → extractive answer), entirely in
the browser, over a status-gated snapshot of the synthetic corpus. Type any question: on-topic
questions answer with cited Approved/Effective passages; off-topic or unsupported questions refuse.

This exists so the demo can be published on GitHub Pages (static hosting) from a private repo.
The corpus is synthetic and public-by-design (ADR-003), so nothing sensitive is embedded.

## Files

- `index.html` — the page (trust-forward UI: doc-id, version, Approved badge, cited section, refusal).
- `retrieval.js` — the deterministic retrieval port (browser + node).
- `corpus-data.json` — status-gated chunks exported from the Python corpus.
- `.nojekyll` — serve as plain static files (no Jekyll processing).

## Faithfulness (do not let it drift)

`corpus-data.json` and the JS are verified to match the Python core. Regenerate + re-verify with:

```bash
python scripts/build_pages_demo.py
```

It re-exports `corpus-data.json`, then runs `retrieval.js` under node over the full eval battery
(24 trap + 13 natural-language + adversarial) and asserts the JS outcome, top document, and top
chunk match Python exactly (currently 40/40). Re-run after any corpus or retrieval change, then
re-push.

## Preview locally

```bash
cd docs && python3 -m http.server 8098   # then open http://127.0.0.1:8098/
```

(Open over HTTP, not `file://` — the page fetches `corpus-data.json`.)

## Boundary

Not a validated GxP/quality system. It does not certify compliance, verify truth, or make
regulated decisions. Retrieval nominates passages; a qualified human decides.
