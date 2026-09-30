"""Pure reduction of reviewed assessments under qualifier-grounding-policy-v1.

This module has no imports or I/O. It does not assess natural-language meaning.
Profile: deterministic-operation; public-safe; frozen per candidate commit.
Owner: qualifier-grounding-offline-qualification-v1. Verify with sibling unit tests.
"""

_GUARDS = (
    "core_independently_supported",
    "bindings_preserved",
    "required_context_retained",
    "removal_independent",
    "no_missing_presupposition",
    "gap_explicit",
)
_SURFACES = {"BODY", "QUOTE", "QUERY", "HEADING", "METADATA"}
_APERTURES = {"Q", "N", "P"}


def _ids(value, allowed=None):
    return (
        isinstance(value, list)
        and all(isinstance(x, str) and x for x in value)
        and len(value) == len(set(value))
        and (allowed is None or set(value) <= allowed)
    )


def _valid(assessment):
    if not isinstance(assessment, dict) or set(assessment) != {"case_id", "ledger"}:
        return False
    if not isinstance(assessment["case_id"], str) or not assessment["case_id"]:
        return False
    ledger = assessment["ledger"]
    if not isinstance(ledger, dict) or set(ledger) != {
        "coverage",
        "integrity",
        "obligations",
        "witnesses",
        "proposal",
    }:
        return False
    if ledger["coverage"] not in ("COMPLETE", "UNKNOWN") or ledger["integrity"] not in (
        "VALID",
        "CUSTODY_INVALID",
        "ASSESSOR_UNAVAILABLE",
        "EXECUTION_FAILURE",
    ):
        return False
    obligations = ledger["obligations"]
    if not isinstance(obligations, list) or not obligations:
        return False
    for obligation in obligations:
        if not isinstance(obligation, dict) or set(obligation) != {"id", "materiality"}:
            return False
        if not isinstance(obligation["id"], str) or not obligation["id"]:
            return False
        if obligation["materiality"] not in ("MATERIAL", "UNKNOWN"):
            return False
    obligation_ids = [x["id"] for x in obligations]
    if len(obligation_ids) != len(set(obligation_ids)):
        return False
    obligation_set = set(obligation_ids)
    witnesses = ledger["witnesses"]
    if not isinstance(witnesses, list):
        return False
    witness_ids = []
    for witness in witnesses:
        if not isinstance(witness, dict) or set(witness) != {
            "id",
            "surface",
            "apertures",
            "entails",
            "contradicts",
            "ambiguous",
        }:
            return False
        if not isinstance(witness["id"], str) or not witness["id"]:
            return False
        if not isinstance(witness["surface"], str) or witness["surface"] not in _SURFACES:
            return False
        if not _ids(witness["apertures"], _APERTURES):
            return False
        if not all(
            _ids(witness[key], obligation_set) for key in ("entails", "contradicts", "ambiguous")
        ):
            return False
        witness_ids.append(witness["id"])
    if len(witness_ids) != len(set(witness_ids)):
        return False
    proposal = ledger["proposal"]
    if proposal is None:
        return True
    if not isinstance(proposal, dict) or set(proposal) != {
        "core_ids",
        "gap_ids",
        "body_witness_ids",
        "guards",
    }:
        return False
    if not all(_ids(proposal[key], obligation_set) for key in ("core_ids", "gap_ids")):
        return False
    if not _ids(proposal["body_witness_ids"], set(witness_ids)):
        return False
    guards = proposal["guards"]
    return (
        isinstance(guards, dict)
        and set(guards) == set(_GUARDS)
        and all(
            guards[key] is True or guards[key] is False or guards[key] is None for key in _GUARDS
        )
    )


def _aperture(ledger, aperture, obligations):
    surface = "QUOTE" if aperture == "Q" else "BODY"
    authorized = [
        w for w in ledger["witnesses"] if w["surface"] == surface and aperture in w["apertures"]
    ]
    entails = {x for w in authorized for x in w["entails"]}
    contradicts = {x for w in authorized for x in w["contradicts"]}
    ambiguous = {x for w in authorized for x in w["ambiguous"]}
    if contradicts:
        label = "UNSUPPORTED"
    elif ambiguous:
        label = "INCONCLUSIVE"
    elif obligations <= entails:
        label = "SUPPORTED"
    elif entails:
        label = "OVER_BROAD"
    else:
        label = "UNSUPPORTED"
    return label, entails, contradicts, ambiguous, authorized


def decide(assessment_ledger):
    """Return decision-only state. case_id is copied, never used in a decision."""
    case_id = assessment_ledger.get("case_id", "") if isinstance(assessment_ledger, dict) else ""
    record = {
        "case_id": case_id if isinstance(case_id, str) else "",
        "assessment_status": "APPARATUS_FAILURE",
        "apertures": {a: "NOT_ASSESSED" for a in ("Q", "N", "P")},
        "grounding": "NOT_ASSESSED",
        "citation": "NOT_ASSESSED",
        "finding": "APPARATUS_FAILURE",
        "action": "STOP",
        "core_ids": [],
        "gap_ids": [],
        "witness_ids": [],
        "reason": "Ledger structure or assessment integrity does not permit reduction.",
    }
    if not _valid(assessment_ledger):
        return record
    ledger = assessment_ledger["ledger"]
    if ledger["integrity"] != "VALID":
        return record
    if ledger["coverage"] == "UNKNOWN" or any(
        x["materiality"] == "UNKNOWN" for x in ledger["obligations"]
    ):
        record.update(
            assessment_status="INCONCLUSIVE",
            apertures={a: "INCONCLUSIVE" for a in ("Q", "N", "P")},
            grounding="INCONCLUSIVE",
            citation="INCONCLUSIVE",
            finding="INCONCLUSIVE",
            action="WITHHOLD",
            reason="Coverage or materiality is unknown; no affirmative support is established.",
        )
        return record

    obligations = {x["id"] for x in ledger["obligations"]}
    views = {a: _aperture(ledger, a, obligations) for a in ("Q", "N", "P")}
    record["assessment_status"] = "COMPLETE"
    record["apertures"] = {a: views[a][0] for a in views}
    if views["Q"][0] == "SUPPORTED":
        record["citation"] = "SUFFICIENT"
    elif "INCONCLUSIVE" in (views["Q"][0], views["N"][0]):
        record["citation"] = "INCONCLUSIVE"
    elif views["N"][0] == "SUPPORTED":
        record["citation"] = "QUOTE_INSUFFICIENT"
    else:
        record["citation"] = "NOMINATION_INSUFFICIENT"

    label, supported, contradicted, ambiguous, body = views["P"]
    missing = obligations - supported
    record["witness_ids"] = sorted(
        w["id"] for w in body if w["entails"] or w["contradicts"] or w["ambiguous"]
    )
    record["grounding"] = "PACKET_LEVEL_GROUNDING_DEFECT"
    record["gap_ids"] = sorted(missing)
    if contradicted:
        record.update(
            finding="CONTRADICTED_CLAIM",
            action="REJECT_COMPLETE",
            reason="Packet BODY contradicts a material obligation; no trimming is permitted.",
        )
        return record
    if ambiguous:
        record.update(
            assessment_status="INCONCLUSIVE",
            grounding="INCONCLUSIVE",
            finding="INCONCLUSIVE",
            action="WITHHOLD",
            gap_ids=[],
            reason="An authorized packet BODY assessment is ambiguous; no claim is emitted.",
        )
        return record
    if label == "SUPPORTED":
        record["grounding"] = "FULL_BODY_SUPPORT"
        if record["citation"] == "SUFFICIENT":
            record.update(
                finding="FULL_BODY_SUPPORT",
                action="KEEP_FULL",
                reason="All material obligations have packet BODY and sufficient quote support.",
            )
        else:
            record.update(
                finding="CITATION_SPAN_INSUFFICIENCY",
                action="HOLD_FOR_CITATION",
                reason="Packet BODY supports all conditions; the citation is insufficient.",
            )
        return record

    proposal = ledger["proposal"]
    if not supported or proposal is None or not proposal["core_ids"]:
        record.update(
            finding="NO_SUPPORTED_CORE",
            action="REJECT_COMPLETE",
            reason="Packet support is incomplete and no supported core is proposed.",
        )
        return record
    if any(proposal["guards"][key] is None for key in _GUARDS):
        record.update(
            assessment_status="INCONCLUSIVE",
            finding="INCONCLUSIVE",
            action="WITHHOLD",
            reason="Decomposition safety is unknown; withhold the proposed core.",
        )
        return record
    core = set(proposal["core_ids"])
    gaps = set(proposal["gap_ids"])
    chosen = [w for w in body if w["id"] in proposal["body_witness_ids"]]
    chosen_support = {x for w in chosen for x in w["entails"]}
    safe = (
        all(proposal["guards"][key] is True for key in _GUARDS)
        and core == supported
        and gaps == missing
        and not core & gaps
        and core | gaps == obligations
        and core <= chosen_support
        and len(chosen) == len(proposal["body_witness_ids"])
    )
    if not safe:
        record.update(
            finding="UNSAFE_DECOMPOSITION",
            action="REJECT_COMPLETE",
            reason="Core fails safety, BODY support, gap coverage, or supported-content retention.",
        )
        return record
    record.update(
        finding="UNSUPPORTED_MATERIAL_QUALIFIER",
        action="PROPOSE_CORE_WITH_GAP",
        core_ids=sorted(core),
        gap_ids=sorted(gaps),
        witness_ids=sorted(w["id"] for w in chosen),
        reason="Core retains BODY-supported obligations; all guards hold and gaps are explicit.",
    )
    return record
