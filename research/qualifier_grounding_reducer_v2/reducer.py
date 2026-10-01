"""Pure implementation of the frozen qualifier-grounding ledger contract v2."""

_GUARDS = (
    "core_independently_supported", "bindings_preserved",
    "required_context_retained", "removal_independent",
    "no_missing_presupposition", "gap_explicit",
)
_ASSESSMENTS = ("entails", "contradicts", "ambiguous")
_APERTURES = ("Q", "N", "P")


def _fields(value, names):
    return type(value) is dict and set(value) == set(names)


def _identifier(value):
    return type(value) is str and bool(value)


def _ids(value):
    return (type(value) is list and all(_identifier(x) for x in value)
            and len(value) == len(set(value)))


def _valid(value):
    if not _fields(value, ("case_id", "ledger")) or not _identifier(value["case_id"]):
        return False
    ledger = value["ledger"]
    if not _fields(ledger, ("coverage", "integrity", "obligations", "witnesses", "proposal")):
        return False
    if ledger["coverage"] not in ("COMPLETE", "UNKNOWN"):
        return False
    if ledger["integrity"] not in (
        "VALID", "UNKNOWN", "CUSTODY_INVALID", "ASSESSOR_UNAVAILABLE", "EXECUTION_FAILURE",
    ):
        return False
    obligations = ledger["obligations"]
    if type(obligations) is not list or not obligations:
        return False
    if not all(_fields(o, ("id", "materiality")) and _identifier(o["id"])
               and o["materiality"] in ("MATERIAL", "UNKNOWN") for o in obligations):
        return False
    material = {o["id"] for o in obligations}
    if len(material) != len(obligations):
        return False
    witnesses = ledger["witnesses"]
    if type(witnesses) is not list:
        return False
    for witness in witnesses:
        if not _fields(witness, ("id", "surface", "apertures", *_ASSESSMENTS)):
            return False
        if not _identifier(witness["id"]) or not _ids(witness["apertures"]):
            return False
        surface, apertures = witness["surface"], set(witness["apertures"])
        if surface == "QUOTE":
            legal = apertures == {"Q"}
        elif surface == "BODY":
            legal = apertures in ({"P"}, {"N", "P"})
        else:
            legal = surface in ("QUERY", "HEADING", "METADATA") and not apertures
        if not legal:
            return False
        if not all(_ids(witness[k]) and set(witness[k]) <= material for k in _ASSESSMENTS):
            return False
    witness_ids = {w["id"] for w in witnesses}
    if len(witness_ids) != len(witnesses):
        return False
    proposal = ledger["proposal"]
    if proposal is None:
        return True
    if not _fields(proposal, ("core_ids", "gap_ids", "body_witness_ids", "guards")):
        return False
    if not all(_ids(proposal[k]) and set(proposal[k]) <= material
               for k in ("core_ids", "gap_ids")):
        return False
    if not _ids(proposal["body_witness_ids"]) or not set(proposal["body_witness_ids"]) <= witness_ids:
        return False
    return (_fields(proposal["guards"], _GUARDS)
            and all(v is None or type(v) is bool for v in proposal["guards"].values()))


def decide(assessment_ledger):
    """Return one decision derived solely from a JSON-compatible input value."""
    case_id = (assessment_ledger.get("case_id") if type(assessment_ledger) is dict else None)
    if not _identifier(case_id):
        case_id = None
    empty_apertures = {a: "NOT_ASSESSED" for a in _APERTURES}
    diagnostics = {
        "local_apertures": empty_apertures.copy(), "missing_packet_ids": [],
        "contradicted_packet_ids": [], "ambiguous_ids": [], "conflicting_ids": [],
        "considered_witness_ids": [], "uncertainty_sources": [],
        "proposal_status": "NOT_ASSESSED", "apparatus_code": "NONE",
    }
    result = {
        "case_id": case_id, "assessment_status": "APPARATUS_FAILURE",
        "apertures": empty_apertures, "grounding": "NOT_ASSESSED",
        "citation": "NOT_ASSESSED", "finding": "APPARATUS_FAILURE", "action": "STOP",
        "core_ids": [], "gap_ids": [], "witness_ids": [], "diagnostics": diagnostics,
        "reason": "Input or integrity prevents assessment.",
    }
    if not _valid(assessment_ledger):
        diagnostics["apparatus_code"] = "INVALID_INPUT"
        return result
    ledger = assessment_ledger["ledger"]
    if ledger["integrity"] != "VALID":
        diagnostics["apparatus_code"] = (
            "INTEGRITY_UNKNOWN" if ledger["integrity"] == "UNKNOWN" else "INTEGRITY_NOT_VALID"
        )
        return result
    material = {o["id"] for o in ledger["obligations"]}
    aggregate = {a: {k: set() for k in _ASSESSMENTS} for a in _APERTURES}
    considered, packet_witnesses = set(), {}
    for witness in ledger["witnesses"]:
        if witness["surface"] not in ("QUOTE", "BODY"):
            continue
        if any(witness[k] for k in _ASSESSMENTS):
            considered.add(witness["id"])
        for aperture in witness["apertures"]:
            for kind in _ASSESSMENTS:
                aggregate[aperture][kind].update(witness[kind])
        if witness["surface"] == "BODY":
            packet_witnesses[witness["id"]] = set(witness["entails"])
    local, ambiguous, conflicting = {}, set(), set()
    for aperture, states in aggregate.items():
        entails, contradicts, unclear = (states[k] for k in _ASSESSMENTS)
        conflict = entails & contradicts
        ambiguous.update(unclear)
        conflicting.update(conflict)
        if unclear or conflict:
            finding = "INCONCLUSIVE"
        elif contradicts:
            finding = "UNSUPPORTED"
        elif entails == material:
            finding = "SUPPORTED"
        elif entails:
            finding = "OVER_BROAD"
        else:
            finding = "UNSUPPORTED"
        local[aperture] = finding
    supported = aggregate["P"]["entails"]
    contradicted = aggregate["P"]["contradicts"]
    missing = material - supported
    sources = set()
    if ledger["coverage"] == "UNKNOWN":
        sources.add("COVERAGE_UNKNOWN")
    if any(o["materiality"] == "UNKNOWN" for o in ledger["obligations"]):
        sources.add("MATERIALITY_UNKNOWN")
    if ambiguous:
        sources.add("AUTHORIZED_AMBIGUITY")
    if conflicting:
        sources.add("AUTHORIZED_CONFLICT")
    diagnostics.update({
        "local_apertures": local, "missing_packet_ids": sorted(missing),
        "contradicted_packet_ids": sorted(contradicted), "ambiguous_ids": sorted(ambiguous),
        "conflicting_ids": sorted(conflicting), "considered_witness_ids": sorted(considered),
    })
    proposal = ledger["proposal"]
    if not sources:
        if contradicted or not supported or supported == material:
            diagnostics["proposal_status"] = "NOT_REQUIRED"
        elif proposal is None:
            diagnostics["proposal_status"] = "ABSENT"
        elif any(v is None for v in proposal["guards"].values()):
            diagnostics["proposal_status"] = "UNKNOWN"
            sources.add("DECOMPOSITION_UNKNOWN")
        else:
            chosen = set(proposal["body_witness_ids"])
            witnesses_safe = bool(chosen) and all(
                w in packet_witnesses and bool(packet_witnesses[w] & supported) for w in chosen
            )
            covered = set()
            if witnesses_safe:
                for witness_id in chosen:
                    covered.update(packet_witnesses[witness_id])
            safe = (all(v is True for v in proposal["guards"].values())
                    and set(proposal["core_ids"]) == supported
                    and set(proposal["gap_ids"]) == missing
                    and witnesses_safe and supported <= covered)
            diagnostics["proposal_status"] = "SAFE" if safe else "UNSAFE"
    if sources:
        diagnostics["uncertainty_sources"] = sorted(sources)
        result.update({
            "assessment_status": "INCONCLUSIVE", "action": "WITHHOLD",
            "finding": "INCONCLUSIVE", "grounding": "INCONCLUSIVE",
            "citation": "INCONCLUSIVE", "apertures": {a: "INCONCLUSIVE" for a in _APERTURES},
            "reason": "Declared uncertainty withholds all content authority.",
        })
        return result
    citation = ("NOMINATION_INSUFFICIENT" if local["N"] != "SUPPORTED" else
                "QUOTE_INSUFFICIENT" if local["Q"] != "SUPPORTED" else "SUFFICIENT")
    result.update({
        "assessment_status": "COMPLETE", "apertures": local.copy(), "citation": citation,
        "grounding": "PACKET_LEVEL_GROUNDING_DEFECT", "action": "REJECT_COMPLETE",
    })
    if contradicted:
        result["finding"] = "CONTRADICTED_CLAIM"
    elif supported == material:
        result.update({
            "grounding": "FULL_BODY_SUPPORT", "core_ids": sorted(material),
            "witness_ids": sorted(w for w, ids in packet_witnesses.items() if ids & material),
            "action": "KEEP_FULL" if citation == "SUFFICIENT" else "HOLD_FOR_CITATION",
            "finding": "FULL_BODY_SUPPORT" if citation == "SUFFICIENT" else "CITATION_SPAN_INSUFFICIENCY",
        })
    elif not supported:
        result["finding"] = "NO_SUPPORTED_CORE"
    elif diagnostics["proposal_status"] == "SAFE":
        result.update({
            "action": "PROPOSE_CORE_WITH_GAP", "finding": "UNSUPPORTED_MATERIAL_QUALIFIER",
            "core_ids": sorted(supported), "gap_ids": sorted(missing),
            "witness_ids": sorted(proposal["body_witness_ids"]),
        })
    else:
        result["finding"] = "UNSAFE_DECOMPOSITION"
    result["reason"] = result["action"] + ": reduced declared assessments under frozen v2 policy."
    return result
