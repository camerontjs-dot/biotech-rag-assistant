# Citation sentence-selection review evidence — original PR #50

**Disposition: NOT_QUALIFIED. This evidence supports rejecting and closing the original implementation unmerged.** Passing maintained checks do not supersede the independent counterexamples. The mechanical overlap correction is clear; the broader sentence-boundary policy remains a separately identified successor question under [#39](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/39). This bundle makes no successor implementation or semantic-support decision.

| Reviewed identity | Value |
| --- | --- |
| Repository / original PR | `camerontjs-dot/biotech-rag-assistant` / [#50](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/50) |
| Original source HEAD | `9685872827b37b55c981b88ad3177a2ed3b13533` |
| Original source tree | `68a241ea95194929f4b1ac631eebe4962dd32cae` |
| Compared base | `cd9ba8bc4351ac0cb4cf022ec1ddf449671454c3` |
| Publication status | Evidence prepared after exact-head review; any later evidence-only commit is not the reviewed source HEAD |

Start with [REVIEW.md](REVIEW.md). [counterexamples.json](counterexamples.json) contains the exact inputs, occurrence offsets, and observed outputs. [results.json](results.json) indexes the validation receipts. [source-identity.json](source-identity.json) binds the source archive to the original Git object.

The original independent test bytes are archived as [contract-probes.py.txt](contract-probes.py.txt), outside pytest's normal collection names. Its SHA256 is **`48818936a0b317d23eed48ef507e9516bb0de9c67cf29a02592338175711444a`**. No expectations or probe bytes were changed for publication. [review-original.md](review-original.md) preserves the original review narrative with only the declared workspace-prefix substitution; its older absolute-path reproduction commands are archival. Use the portable commands below.

## Integrity and transformations

From this bundle directory, run:

```bash
sha256sum -c SHA256SUMS
```

[SHA256SUMS](SHA256SUMS) covers every other file in this directory. [provenance.json](provenance.json) records original raw-file hashes, published hashes, and every transformation. Published receipt logs and structured reports retain their original bytes except for literal replacement of the ephemeral absolute scratch workspace prefix with `<REVIEW_WORKSPACE>`. No assertion, result, warning, test name, traceback detail, or count was removed. Files without that prefix remain byte-identical.

[dependencies.txt](dependencies.txt) is the original version inventory. Its editable source entry reflects the historical local worktree layout and is not a portable install target. [environment-requirements.txt](environment-requirements.txt) is derived by removing only that one editable-source line; all dependency versions remain pinned. Install the exact source checkout separately, as below. [versions.json](versions.json) records the Python, Node, and installed-package versions. Build-isolation dependency resolution is not preserved as a lockfile.

## Reproduce the original failures

These Bash instructions assume the bundle is the current directory, Python 3.12 and Git are available, and the repository is readable. The recorded run used Python 3.12.14. They create a separate checkout and leave the bundle unchanged.

```bash
review_bundle="$(pwd)"
review_run="$(mktemp -d)"
git clone --no-checkout https://github.com/camerontjs-dot/biotech-rag-assistant.git "$review_run/repo"
git -C "$review_run/repo" checkout --detach 9685872827b37b55c981b88ad3177a2ed3b13533
test "$(git -C "$review_run/repo" rev-parse 'HEAD^{tree}')" = 68a241ea95194929f4b1ac631eebe4962dd32cae
python3.12 -m venv "$review_run/venv"
review_python="$review_run/venv/bin/python"
"$review_python" -m pip install -r "$review_bundle/environment-requirements.txt"
"$review_python" -m pip install --no-deps -e "$review_run/repo"
cp "$review_bundle/contract-probes.py.txt" "$review_run/contract_probes.py"
cmp "$review_bundle/contract-probes.py.txt" "$review_run/contract_probes.py"
cd "$review_run/repo"
"$review_python" -m pytest -vv "$review_run/contract_probes.py" --tb=short
```

**Expected independent result: exit 1, 14 passed and 10 failed.** These failures are the preserved engineering evidence. Do not weaken the probes to produce a green result. Seven cases in the sentence-stability group include six abbreviation/punctuation failures and one leading-whitespace limitation; the other three failures concern overlapping repeated quotes.

## Reproduce maintained checks and trust receipts

Continue with the variables and checkout established above. The independent failure is expected; if your shell uses `set -e`, run the next block separately after inspecting that result.

```bash
"$review_python" -m pytest -q
"$review_python" -m pytest -q tests/test_citation_spans.py tests/test_api.py
"$review_run/venv/bin/ruff" check .
"$review_python" -m compileall src
"$review_run/venv/bin/biotech-rag" validate-corpus examples/synthetic-controlled-docs
"$review_run/venv/bin/biotech-rag" evaluate examples/synthetic-controlled-docs examples/synthetic-controlled-docs/evaluation/golden-questions.json --json
cp "$review_bundle/pages-parity-harness.py.txt" "$review_run/pages_parity.py"
"$review_python" "$review_run/pages_parity.py" "$review_run/repo" "$review_run/pages-output"
```

Expected results: 118 full-suite passes; 21 citation/API passes; Ruff and compilation pass; 10 valid documents, 8 retrievable and 2 excluded; 24/24 trust cases; 42/42 JS/Python parity cases. The parity check needs Node; the recorded version was v24.19.0. The portable [Pages harness](pages-parity-harness.py.txt) loads the exact committed program and redirects only its `DOCS` directory to a copied output directory. The [original Pages wrapper](pages-parity-original.py.txt) is retained as a prefix-sanitized historical artifact, not a runnable portable script.

## Receipt index

| Check | Log | Machine/detail receipt |
| --- | --- | --- |
| Maintained full suite | [full-pytest.log](full-pytest.log) | [full-junit.xml](full-junit.xml) |
| Citation/API focused suite | [focused-pytest.log](focused-pytest.log) | [focused-junit.xml](focused-junit.xml) |
| Independent contract probes | [independent-pytest.log](independent-pytest.log) | [independent-junit.xml](independent-junit.xml) |
| Ruff | [ruff.log](ruff.log) | — |
| Compile | [compileall.log](compileall.log) | — |
| Corpus validation | [validate-corpus.log](validate-corpus.log) | — |
| Trust suite | [trust-evaluation.log](trust-evaluation.log) | [trust-report.json](trust-report.json), [trust-report.md](trust-report.md) |
| Pages parity | [pages-parity.log](pages-parity.log) | — |

The bundle excludes the virtual environment and generated Pages output. It does not alter product code, original author tests, the original probes, or the original review verdict.
