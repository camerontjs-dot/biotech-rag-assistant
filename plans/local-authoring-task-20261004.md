# Local task: Biotech authoring apparatus and fresh corpus

This task is for a local supervisor with repository and runtime access. The semantic author receives only the frozen request bytes. Programme owner: [#39](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/39). Candidate: [Draft #54](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/54).

## Copyable instruction

Continue Biotech RAG from the prepared authoring candidate. Preserve the active EB work and unrelated local changes. If EB occupies the selected provider or required memory, record the conflict and wait for a free slot; do not stop or take over its process.

Fetch `camerontjs-dot/biotech-rag-assistant`. Read live #39, #54's final verification receipt, `plans/biotech-github-local-handoff-20261004.md`, and `research/semantic-author-slot-boundary-v1-protocol.md`. Use a clean new worktree pinned to source commit **`513cf0629b20a8d876e161f32f8bc6c6549e2012`**, tree **`6428495c4f3b373cd07bdebcc7916834c157da3f`**. The later PR head adds the handoff, evidence and dedicated CI; read those instructions from that head while executing the pinned source. Verify the boundary module SHA-256 is **`74e16e97341bb90d8845ba9f7bd78c03257b97ec79ff6a575b299ca7d3f97450`**. Preserve frozen #30/#38 authority and all historical #50/#51 failures.

Create an isolated Python environment and run the documented new and inherited structural tests plus the frozen preparation validator. Keep command output, exit statuses and runtime/dependency identities. These are offline token/fake-HTTP checks, not model or semantic evidence.

Inventory the actual local provider, model digest and resource headroom. Historical qwen3.5:9b/Ollama settings are leads only; there is no inherited model default. Declare a finite context/output/time/memory budget from current evidence. Keep unrelated inventory private. If the required runtime is unavailable, return the exact blocker without substituting unapproved remote transport.

Use `prepare` and `verify` from the protocol with an explicit new runtime config and a new `semantic-author-slot-bound-v1-*` run directory. Commit and publish the complete prospective configuration, assignment plan, 28 requests, canary and `EXECUTION-FREEZE.json` **before any provider generation, including the canary**. Then run the nonsemantic schema-feature/capacity canary. Preserve actual resource and context evidence. Reported prompt counts alone do not establish untruncated input; retain `UNKNOWN` and `NOT_READY` where that evidence is unavailable.

After the accepted canary, execute `author-01` through `author-28` once each, in order, through the stateless request-bound wrapper. The author sees only each frozen allowed request. Do not expose this task, the repository, conversation, historical rows, peer results or previous responses. Do not retry, repair, rename rows, repartition, tune a failed attempt, or select a favorable result. Stop at the first failed, interrupted or invalid call and preserve the terminal evidence.

Only after all 28 structural acceptances may `freeze-corpus` validate and write a complete 44-case/16-relation corpus. Perform the custodian privacy, synthetic-provenance and historical-separation check before publishing the bounded result. Return either the complete structural freeze or a durable blocker, with source/runtime/config identities, all artifact hashes, exact attempt and partition denominators, first failure, deviations and explicit null corpus hashes where appropriate.

Post a public-safe receipt on #54 and link it from #39. Keep A/B/C adjudication, semantic assessor, reducer, heading-grant #49, Wave B and Biotech–CAL/EB integration `NOT_RUN`. Stop before semantic adjudication, product promotion, merge or release. Prepare the next frozen adjudication handoff only after a valid corpus and required local/custodian evidence exist.

## Setup commands

Choose a new worktree path that does not already exist. Run from the existing Biotech clone; these commands create a new local branch without changing the checked-out branch or existing worktree files. Use Python 3.11 or newer; inspect `python3 --version` first and select an existing compatible interpreter if necessary.

```sh
git fetch origin research/semantic-author-slot-boundary-20261004
git worktree add -b local/biotech-authoring-20261004 ../biotech-authoring-local-20261004 513cf0629b20a8d876e161f32f8bc6c6549e2012
cd ../biotech-authoring-local-20261004
git rev-parse HEAD HEAD^{tree}
git status --short
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r research/semantic-assessor-preparation-requirements.txt
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic*.py' -v
python research/check_semantic_assessor_preparation.py --root . --check --require-freeze --receipt /tmp/biotech-local-preparation-check.json
```

If a branch or directory already exists, inspect it and choose a new unused name. Never remove it to make these commands succeed. The protocol gives the exact `prepare`, `verify`, `canary`, `run` and `freeze-corpus` CLI syntax. The local configuration must come from current runtime evidence; this handoff intentionally does not fabricate one.

The qualified CI-only #45 remains a separate explicit operator-promotion gate. Its unmerged status does not block this isolated local task.
