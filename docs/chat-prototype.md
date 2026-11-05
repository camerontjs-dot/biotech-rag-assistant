# Conversational prototype (experimental)

An opt-in chat surface that explains Approved/Effective passages with an OpenAI model, keeps a
bounded conversation, and shows every supplied passage with its document identity, version,
status, and citation reference. It is a reversible product prototype composed **beside** the
maintained deterministic `/answer` contract, which is unchanged and remains the regression
baseline (ADR-009, ADR-010). Decision record: ADR-019 in `DECISIONS.md`.

It is not part of the grounding-recovery research programme tracked in issue #39, does not use
or change its frozen objects or gates, and none of its tests count toward that programme.

Live OpenAI behavior has **not** been verified yet (see [Verification status](#verification-status)).

## What you can do with it

- Ask a question and get a short explanation built only from admitted passages, with each
  statement linked to the passage it quotes, and the exact source text shown beside it.
- Ask follow-ups such as “who is responsible?”, “explain that step”, or “turn the stated
  procedure into a checklist”; they reuse the passages of the question they refer to.
- Correct yourself (“No, I meant the purified water loop sampling”) or change topic; the
  interface shows how each message was interpreted and exactly what was searched.
- See when the documents do not state something (for example the analytical-balance acceptance
  range), with an explanation of what they do say and, where useful, a follow-up question.
- Get the same retrieval, status gate, and refusals as `/answer`: questions only a retired SOP
  answers are refused without calling a model, naming the held-out document by identity only.

## Quick start without OpenAI

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[chat]"
.venv/bin/biotech-rag chat
```

Open <http://127.0.0.1:8000/chat>. With no provider configured, every question still retrieves
and shows the admitted passages; the explanation area says the provider is unavailable. No model
is ever contacted in this mode. `/answer`, the deterministic demo at `/`, and every other
maintained route are served by the same process.

## Enable OpenAI explanations

1. Provide the key to the **server process only**, as `OPENAI_API_KEY`. Never put it in browser
   code, committed files, logs, fixtures, or issue/PR text. Options:
   - a local shell: `export OPENAI_API_KEY=...` from your secret manager;
   - a local `.env` file: `cp .env.example .env`, fill it in (`.env` is gitignored), then
     `set -a; . ./.env; set +a`;
   - a Claude Code cloud environment: add `OPENAI_API_KEY` in the environment's settings
     (Network secrets or environment variables) **and** allow `api.openai.com` under Network
     access; a new session picks both up.
2. Opt in to paid calls: `export BIOTECH_RAG_CHAT_PROVIDER=openai`.
3. Start: `.venv/bin/biotech-rag chat`. The startup line states whether the provider is
   available (for example `OpenAI Responses API, model gpt-5.5, store=false`).

Equivalent factory form: `uvicorn --factory biotech_rag_assistant.chat.app:create_chat_app_from_env`.
The server binds to `127.0.0.1` by default; set `BIOTECH_RAG_API_KEY` to require `X-API-Key` on
every route except `/health` and the static pages (the chat page prompts for the key).

### Configuration

| Variable | Purpose | Default |
|---|---|---|
| `BIOTECH_RAG_CHAT_PROVIDER` | `none` or `openai`. Only `openai` makes paid calls. | `none` |
| `OPENAI_API_KEY` | OpenAI credential, read by the server process only. | unset |
| `BIOTECH_RAG_OPENAI_MODEL` | Model requested. The served model is recorded per turn. | `gpt-5.5` |
| `BIOTECH_RAG_OPENAI_REASONING_EFFORT` | `none`…`max`, or `omit` to send no `reasoning` (for non-reasoning models). | `low` |
| `BIOTECH_RAG_OPENAI_MAX_OUTPUT_TOKENS` | Per-request cap, including reasoning tokens (256–16000). | `3000` |
| `BIOTECH_RAG_OPENAI_TIMEOUT_S` | SDK timeout per attempt (1–300). Replaces the SDK's 10-minute default. | `60` |
| `BIOTECH_RAG_OPENAI_MAX_RETRIES` | SDK retries for connection errors, 408/409/429/5xx (0–3). Replaces the SDK default of 2. | `1` |
| `BIOTECH_RAG_OPENAI_MAX_REQUESTS` | Logical model requests per server process; then the provider reports `budget_exhausted` until restart. | `50` |
| `BIOTECH_RAG_CHAT_MAX_SESSIONS` | Conversations kept in memory; least recently used is evicted. | `100` |
| `BIOTECH_RAG_CHAT_MAX_TURNS` | Turns per conversation. | `30` |
| `BIOTECH_RAG_CHAT_SESSION_TTL_S` | Idle time before a conversation is forgotten. | `3600` |
| `BIOTECH_RAG_CHAT_HISTORY_TURNS` | Earlier turns re-sent to the model as context. | `6` |
| `BIOTECH_RAG_CHAT_TOP_K` | Passages retrieved per query (same as `/answer`'s default). | `3` |
| `BIOTECH_RAG_CHAT_MAX_EVIDENCE` | Passages supplied per turn when a follow-up merges two queries. | `6` |

All transport variables (`BIOTECH_RAG_CORPORA`, `BIOTECH_RAG_API_KEY`, `BIOTECH_RAG_AUDIT_LOG`, …)
apply unchanged (`docs/api-transport.md`). Invalid values fail the server at startup.

**Spending bound.** Each user turn makes at most one logical request, and only when admitted
evidence exists. With the defaults, one logical request is at most 2 HTTP attempts (1 retry),
each capped at 3000 output tokens, and a process makes at most 50 logical requests. Input is
bounded by the instructions, at most 6 earlier turns (user text ≤ 2000 characters, re-rendered
replies ≤ 1500 characters), and at most 6 passages. Model pricing was not consulted for this
prototype; check it before raising the bounds.

## OpenAI request and data handling

Checked against the official `openai` Python SDK 3.x (generated from OpenAI's OpenAPI spec; the
developer documentation site was not reachable from the build environment):

- Each turn is one `client.responses.create` call with `instructions` (static, versioned rules),
  `input` (bounded history plus one JSON payload message), `text.format` =
  `{"type": "json_schema", "strict": true, ...}`, `max_output_tokens`, optional
  `reasoning.effort`, and **`store: false`**. No `previous_response_id`, `conversation`, tools, or
  sampling parameters are sent; the application keeps conversation state itself.
- The SDK documents that `store` **defaults to true** when omitted and that stored responses are
  kept for at least 30 days, which is why it is always sent as `false`.
- `store: false` is **not** a zero-retention guarantee. OpenAI's data-controls guide
  (<https://developers.openai.com/api/docs/guides/your-data>) states that abuse-monitoring logs,
  which can include prompts and responses, are kept for up to 30 days by default, and that Zero
  Data Retention or Modified Abuse Monitoring require OpenAI's approval. The SDK reference also
  documents prompt-cache retention (for `gpt-5.5`, the `24h` policy). This summary was taken from
  the SDK's docstrings and a search summary of that guide, not a direct read; confirm the current
  terms for your organization before sending anything other than this synthetic corpus.
- The application stores conversations only in server memory (bounded, idle-expiring, lost on
  restart). If `BIOTECH_RAG_AUDIT_LOG` is set, each turn's audit record includes the user's
  message (as `/answer` records its query), a hashed session reference, and the model identity
  and usage; it never includes the API key or raw model output.

## How a turn works

1. **Interpretation (deterministic).** The message is classified as a standalone question, a
   follow-up (it refers back, “that”, “the stated procedure”, or is too short to search on its
   own, “who is responsible?”), a topic change, a correction (“no, I meant…”), a request that
   needs clarification, or not found. History only decides *which queries to run*: a follow-up
   re-runs the earlier question's retrieval. Leading correction/discourse words and a fixed list of
   conversational task words (“explain”, “summarize”, “checklist”…) are left out of the search
   query **only when the corpus never uses them**, so a word that could describe document content
   is always searched. The user's message itself is never rewritten.
2. **Retrieval.** The maintained path: status gate, BM25, `score_floor`, and the 0.6 coverage gate
   with `RetrievalConfig` defaults. A plain question retrieves exactly what `/answer` retrieves.
3. **Evidence.** Hits become passages `S1…Sn`, grouped by document in source order. Status,
   source hash, and the exact-span invariant are re-verified against the loaded corpus; any
   mismatch fails the turn with no answer. Section headings are shown to you but never sent to the
   model, so a heading cannot supply a fact the body text lacks.
4. **No evidence, no model.** If nothing is admitted, the reply is deterministic, and any held-out
   document that a status-blind run would have used, or that you named, is reported by identity
   and status only (never its text).
5. **Generation.** One request as described above. The final message is a JSON payload with your
   verbatim question, the interpretation, the passages, and the identity of any named
   non-admitted documents. Passage text is quoted data in a user-role message, never part of the
   instructions. The schema limits citation refs to this turn's refs.
6. **Checks.** Output that is not valid JSON under the contract is rejected, not repaired. Each
   statement is shown only if (a) every cited ref was supplied this turn, (b) at least one
   quotation of three or more words is found verbatim in its passage (case, whitespace, curly
   quotes, and dashes are folded), and (c) every number in it (digits or number words) appears in
   a cited passage. Otherwise it is **withheld**, with the reason, and its text is excluded from
   later history. Advisory notes flag a cited sentence's condition that the answer may not
   reflect, steps out of source order, a frequency word found only in a heading, and verification
   language.
7. **Record.** The turn record keeps the verbatim question, the interpretation and every
   retrieval attempt (query, origin, hits, top coverage), the passages actually supplied, held-out
   pointers, the corpus snapshot id, the requested and served model, usage, latency, a hash of the
   exact request, the raw unvalidated output, and the check results.

Displayed quotations always come from the application's source text, located by offsets; the
model's quote string is used only to find the span. The interface renders every model and
document string as text (no HTML), and never shows a “verified” or “supported” badge.

### What the checks do and do not establish

They establish that a shown statement cites a passage supplied for this turn, that its quotation
is really in that passage, and that its numbers appear there. They do **not** establish that the
passage supports the statement: a correct quotation beside a wrong paraphrase passes. Semantic
support assessment remains deferred (ADR-007, ADR-009) and is the subject of issue #39's separate
programme. Every answer carries `support_scope: "mechanical_only"`.

## Corpus snapshot

Each turn names the corpus snapshot it used: a fingerprint of every valid document's id,
version, status, and hash, as loaded and validated at server start. Status or content changes on
disk take effect only after a restart; a running conversation does not track revocations and
the interface says so.

## API

All routes below except `GET /chat` require `X-API-Key` when `BIOTECH_RAG_API_KEY` is set, and
every request gets an `X-Request-ID` and one audit record, like the maintained routes.

| Method / path | Purpose |
|---|---|
| `GET /chat` | The chat page (static). |
| `GET /chat/status` | Provider availability (`available`, `reason`, `model`, `store`), bounds, corpus snapshots. |
| `POST /chat` | `{message, session_id?, corpus?, new_topic?}` → `{session_id, turn, corpus_snapshot, provider_status, turns_used, max_turns}`. |
| `GET /chat/sessions/{id}` | The conversation's turn records. There is no route that lists sessions. |
| `DELETE /chat/sessions/{id}` | Forget a conversation. |
| `GET /chat/documents/{doc_id}` | Full text of an *admitted* document, for viewing a passage in context. Held-out documents are 404. |

Errors: 401 (API key), 404 (unknown corpus, document, or expired conversation), 409 (turn already
in progress, turn limit reached, or corpus mismatch), 422 (invalid body: message 1–2000
characters, unknown fields), 500 (evidence re-verification failed; no answer is produced).

`turn.outcome` is one of `model_answer`, `no_admitted_evidence`, `clarification_needed`,
`courtesy`, `provider_unavailable` (`not_configured`, `missing_credentials`, `sdk_unavailable`,
`budget_exhausted`), `provider_error` (`timeout`, `rate_limited`, `connection_error`,
`auth_failed`, `bad_request`, `upstream_error`, `refused`, `incomplete`), or `malformed_output`.
In every state with admitted evidence the passages are returned and shown.

## Verification status

| What | How | Status |
|---|---|---|
| Application behavior: interpretation, evidence boundary, checks, isolation, bounds, failure states | `tests/test_chat_*.py` (CI, no credentials, no network) | Passing |
| OpenAI adapter request/response/error mapping | The real `openai` SDK against an in-process `httpx2.MockTransport` (`tests/test_chat_openai_provider.py`, end-to-end case in `tests/test_chat_api.py`) | Passing |
| Live smoke harness: request bound, transcript, PASS/FAIL lines, exit codes, vacuous-run detection | The real `openai` SDK against an in-process stand-in returning scripted answers (`tests/test_chat_live_smoke.py`) | Passing |
| Maintained contracts on the composed app | `/answer` and `/retrieve` CLI parity, maintained suites unchanged | Passing |
| Browser UI states and safe rendering | `python scripts/chat_ui_check.py` (needs Node + Playwright; not in CI) | Passing when run for this change |
| Example conversations | `docs/chat-examples.md`, generated through the real app with **scripted** model outputs; drift-checked in CI | Current |
| **Live OpenAI behavior and answer quality** | `scripts/chat_live_smoke.py --live` | **NOT_RUN** (see below) |

Mocked and scripted runs establish what the application does with model output. They say nothing
about how a live model behaves: whether it finds gaps, keeps conditions, resists embedded
instructions, or produces faithful paraphrases.

### Running the live smoke

```bash
export OPENAI_API_KEY=...   # server-side secret; see "Enable OpenAI explanations"
.venv/bin/python scripts/chat_live_smoke.py --live
```

It refuses to run without `--live` and a key. It makes at most 8 logical requests (7 expected;
hard cap 12), each bounded as configured, and replays fixed conversations (supported question and
follow-ups, the balance gap, a user-supplied value, a retired-document request, an embedded
instruction) through the real app. It writes the complete turn records, the endpoint, and the
served model to `build/chat-live-smoke.json`, then prints two groups of PASS/FAIL lines:

- **Application guarantees** hold whatever the model does: `store: false` on every request, the
  served model recorded, no model call and no retired text for the retired-document request, and
  the chat-introduced 0.5 mg never shown as document content.
- **Run validity** checks that a model was actually exercised: all 7 expected calls were made,
  each returned a schema-valid answer, and the supported question shows at least one checked
  statement. A run in which every call is rejected, malformed, or refused fails here.

It then prints the model's observed behavior for a person to judge against the passages; passing
lines do not establish semantic support. Exit codes: 0 every expectation passed, 1 an expectation
failed, 2 not run (nothing sent), 3 blocked (every call failed with a connection or auth error).
The harness itself is tested offline in CI (`tests/test_chat_live_smoke.py`).

## Known limitations

- **Live behavior unverified.** No live OpenAI call has been made. Default model `gpt-5.5` was
  taken from the official SDK's usage examples; availability and pricing for your account were
  not checked.
- **Inherited refusal bias.** The unchanged coverage gate refuses some on-topic phrasings, for
  example “Explain how a major deviation is escalated” or “What happens if a calibration check
  fails?”. Rephrasing with the document's wording works (“How are major deviations escalated to
  the quality council?”). Lowering the gate was deliberately not done (ADR-012, ADR-014).
- **Deterministic interpretation is heuristic.** Short messages after a topic are treated as
  follow-ups; a short unrelated question can be misread as one (the model then sees the earlier
  passages and should report that they do not cover it). The interface shows the interpretation,
  and “Start a new topic” or “New conversation” override it.
- **Checks are mechanical.** A correct quotation beside an unsupported paraphrase passes. A model
  that obeys an instruction embedded in an admitted passage, and quotes it accurately, is only
  flagged by the verification-language note. Number words “one”, “once”, and “single” are not
  checked (too often non-numeric); units are not compared, only values. Advisory notes can miss
  a dropped condition or flag a faithful paraphrase.
- **Single process, in-memory state.** Conversations do not survive a restart and are not shared
  across worker processes. There are no user accounts; the optional API key is shared.
- **Snapshot at startup.** Status changes need a restart; mid-conversation revocation is not
  tracked.
- **No streaming.** Each turn waits for the full response (bounded by the timeout).
