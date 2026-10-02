---
title: "Request-bound semantic adjudication v2"
domain: "ai-systems"
type: "experiment"
status: "designed"
updated: "2026-10-02"
source: "issue #37; frozen PR #30"
tags: ["semantic-adjudication", "request-custody", "research"]
---

# Request-bound semantic adjudication v2

Issue [#37](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/37)
authorizes this experiment. Frozen [PR #30](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/30)
supplies its semantic authority at publication head
`d1e092b7cdb878d064735d597e8c3b2d6c710157`. The semantic design is unchanged.
Failed execution predecessors [#32](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/32),
[#34](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/34), and
[#36](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/36) are preserved.

The runner sends one serialized JSON request to local Ollama. The model receives
the frozen role instruction, literal allowlisted artifact content, assigned data
and the output schema. `raw=true`, `stream=false`, `keep_alive=0`; no tools,
sessions, retries, external schema resolution, proxy or redirect handling.
Provider-hidden context and training independence remain UNKNOWN. This claims
reconstructable request exposure, with no OS-level denial claim.

`author-partition.json` fixes 28 stateless requests covering exactly 44 slots:
28 anchors, eight invariance variants, eight material mutations. Every anchor
stays with all its dependent variants. The largest partition contains seven
packets. Order, UUIDs, wording instructions and output schemas freeze before
any semantic call. An invalid partition stops the sequence; there is no repair.

The transport draft omits mechanical custody fields. The custodian assigns
pre-frozen opaque IDs by slot and position, computes exact UTF-8 hashes and
complete-source code-point lengths, and locates model-selected exact anchor
text only when it occurs once. It does not revise semantic text, selected
anchors, hypotheses, guard opportunities or alignment maps. Materialized
packets/design/relations must satisfy the original frozen schemas and validator.
The two representations and exact transformation source remain auditable.

Raw model responses, requests and receipts are preserved exclusively. Full
local model inventories contain unrelated machine paths and remain on disk
under the narrow .gitignore entries, with their exact hashes in receipts.
The selected model identity is public; inventory bytes are never sent to roles.

Apparatus checks are separate from semantic acceptance. No assessor implementation,
v2 reducer call, generation replay, Wave B/TEST/PROSPECTIVE access, CAL, ADR-018
change, promotion, merge or release. **Wave B remains LOCKED.**
