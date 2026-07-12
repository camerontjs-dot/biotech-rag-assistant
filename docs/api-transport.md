# HTTP transport contract

The transport layer (`biotech_rag_assistant.api`) exposes the existing CLI core over HTTP
without changing any core logic. Each route calls the same function the matching CLI command
calls and serializes the same `to_cli_record()` output, so API JSON equals CLI `--json` for the
same input. This is enforced by parity tests in `tests/test_api.py`, not by inspection. See
ADR-010 in `DECISIONS.md` for the decision record.

## Running the service

```bash
.venv/bin/biotech-rag serve            # reads config from the environment
.venv/bin/uvicorn biotech_rag_assistant.api:app   # equivalent, module-level app
```

Both build the app from `ApiConfig.from_env()`. The default bind is `127.0.0.1:8000` and the
default corpus allowlist is `synthetic=examples/synthetic-controlled-docs`.

## Security posture

- Binds to `127.0.0.1` by default (`BIOTECH_RAG_HOST` / `BIOTECH_RAG_PORT` to change).
- Optional `X-API-Key` auth: when `BIOTECH_RAG_API_KEY` is set, every route except `/health`
  requires a matching header, otherwise 401.
- Corpus access is a name -> path allowlist resolved at startup. **No request body ever
  supplies a filesystem path**; requests select a bundle by name and an unknown name is 404.
- Invalid bundles fail the server closed at startup (same validation as `load_corpus`).
- Request bodies are Pydantic models with `extra="forbid"`, so unknown fields (including any
  attempt to inject a path field) are 422. CORS is closed by default.

## Traceability

Every non-health request receives a uuid4 request id, returned as the `X-Request-ID` response
header and written to one structured audit record: timestamp, request id, route, method, corpus
name, query, a result summary (hit chunk ids, outcome, citation validity, review recommendation),
and status code. Records go to Python logging and, when `BIOTECH_RAG_AUDIT_LOG` is set, are
appended as JSON lines to that path.

## Configuration (environment variables)

| Env var | Purpose | Default |
|---|---|---|
| `BIOTECH_RAG_CORPORA` | Allowlist registry; comma-separated `name=path` pairs (relative paths resolve against the asset root) | `synthetic=examples/synthetic-controlled-docs` |
| `BIOTECH_RAG_DEFAULT_CORPUS` | Bundle name used when a request omits `corpus` | the single registry entry |
| `BIOTECH_RAG_API_KEY` | If set, required as `X-API-Key` on every route except `/health` | unset (auth disabled) |
| `BIOTECH_RAG_AUDIT_LOG` | If set, append-only JSONL audit-log path | unset (Python logging only) |
| `BIOTECH_RAG_HOST` | Bind host | `127.0.0.1` |
| `BIOTECH_RAG_PORT` | Bind port | `8000` |
| `BIOTECH_RAG_LOW_SCORE_MARGIN` | Margin for the `low_top_score` review trigger | `0.0` |

## Endpoints

The file-path arguments the CLI takes become inline JSON payloads. `corpus` is optional on every
route that takes it and defaults to `BIOTECH_RAG_DEFAULT_CORPUS`.

| Method / path | Mirrors CLI | Request body | 200 response | Errors |
|---|---|---|---|---|
| `GET /health` | — | — | `{status, version, corpora:[names], default_corpus}` | — |
| `POST /validate-corpus` | `validate-corpus` | `{corpus?}` | `IngestReport` fields + `valid` (200 even when `valid:false`) | 401, 404 |
| `POST /retrieve` | `retrieve --json` | `{query, top_k=5, corpus?}` | `{query, retrievable_documents, hits:[…]}` | 401, 404, 422 |
| `POST /answer` | `answer` | `{query, top_k=3, corpus?}` | answer record **plus** `review_recommendation` | 401, 404, 422, 500 |
| `POST /validate-citations` | `validate-citations --json` | `{retrieved_results, answer_fixture}` | citation result (200 even when invalid) | 401, 422 |
| `POST /evaluate` | `evaluate --json` | `{suite, corpus?}` | trust-layer report | 401, 404, 422 |

Notes:

1. `/validate-corpus` builds its response dict explicitly (`IngestReport` has no `to_cli_record()`
   and `valid` is a property). It reports the result and returns 200 even when `valid` is false,
   mirroring the CLI (which reports, then exits nonzero).
2. `/answer` returns the answer record from `to_cli_record()` plus a sibling
   `review_recommendation` object (below). Parity tests compare the response **minus that key**
   against the CLI `answer` output.
3. `/validate-citations` parses the two JSON payloads the CLI reads from files
   (`RetrievedResultsPayload`, `AnswerFixture`) inline and calls the same validator. It returns the
   failure result with 200 for a bad fixture; it does not 500.
4. `/evaluate` parses the request `suite` into the existing `EvaluationSuite` and passes the
   server-bound corpus path into `run_evaluation_suite`. No server-side report files are written.

## Review-routing mini-spec

`/answer` attaches an advisory routing signal an orchestrator (e.g. n8n) can route on. It does not
change the answer contract: outcomes stay exactly `answer` and `refusal` (ADR-009) and the signal
carries no semantic-support assessment.

```json
"review_recommendation": { "review_recommended": true, "reasons": ["..."] }
```

Triggers are mechanical. Implemented now:

- `refusal_no_supporting_documents` — the answer outcome is a refusal.
- `low_top_score` — `top_score <= score_floor + low_score_margin`. The margin comes from
  `BIOTECH_RAG_LOW_SCORE_MARGIN` (default `0.0`), so by default it fires only at the score floor;
  operators raise the margin per corpus.

Specified for later (not implemented):

- `ambiguous_top_results` — near-tied top scores across different `doc_id`s.
- `citation_validation_failed` — defensive; deterministic extractive answers should not reach it.
