"""Literal fresh controls. No policy-to-decision function or reducer is present.

The author supplies each expected value. Constructors only encode objects,
clones only copy authored values, and identifier transforms only rename them.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parent
SET_ID = "qg-v2-fresh-acceptance-20260930-v4n8"
AUTHOR_ID = "fresh_acceptance_v2"
GUARDS = ["core_independently_supported", "bindings_preserved", "required_context_retained", "removal_independent", "no_missing_presupposition", "gap_explicit"]
FIELDS = ["assessment_status", "apertures.Q", "apertures.N", "apertures.P", "grounding", "citation", "finding", "action", "core_ids", "gap_ids", "witness_ids", "diagnostics.local_apertures.Q", "diagnostics.local_apertures.N", "diagnostics.local_apertures.P", "diagnostics.missing_packet_ids", "diagnostics.contradicted_packet_ids", "diagnostics.ambiguous_ids", "diagnostics.conflicting_ids", "diagnostics.considered_witness_ids", "diagnostics.uncertainty_sources", "diagnostics.proposal_status", "diagnostics.apparatus_code"]
inputs, expectations, controls, pairs = [], [], [], []
by_id = {}

def utc():
    return datetime.now(timezone.utc).isoformat()

def W(i, surface, apertures, entails=(), contradicts=(), ambiguous=()):
    return dict(id=i, surface=surface, apertures=list(apertures), entails=list(entails), contradicts=list(contradicts), ambiguous=list(ambiguous))

def L(ids, witnesses, proposal=None, coverage="COMPLETE", integrity="VALID", unknown=()):
    return dict(coverage=coverage, integrity=integrity, obligations=[dict(id=i, materiality="UNKNOWN" if i in unknown else "MATERIAL") for i in ids], witnesses=witnesses, proposal=proposal)

def P(core, gap, witness, guards):
    return dict(core_ids=list(core), gap_ids=list(gap), body_witness_ids=list(witness), guards=dict(zip(GUARDS, guards)))

def A(values):
    return dict(zip(["Q", "N", "P"], values))

def E(status, auth, grounding, citation, finding, action, core, gap, witness,
      local, missing, contradicted, ambiguous, conflicting, considered,
      sources, proposal_status, apparatus_code, reason):
    # Each argument is explicitly selected by the author, never computed from L.
    return dict(assessment_status=status, apertures=A(auth), grounding=grounding,
                citation=citation, finding=finding, action=action,
                core_ids=sorted(core), gap_ids=sorted(gap), witness_ids=sorted(witness),
                diagnostics=dict(local_apertures=A(local), missing_packet_ids=sorted(missing),
                                 contradicted_packet_ids=sorted(contradicted), ambiguous_ids=sorted(ambiguous),
                                 conflicting_ids=sorted(conflicting), considered_witness_ids=sorted(considered),
                                 uncertainty_sources=sorted(sources), proposal_status=proposal_status,
                                 apparatus_code=apparatus_code), reason=reason)

def add(cid, ledger, expected, purpose, tags, strategies, invalid=False):
    expected = deepcopy(expected)
    expected["case_id"] = cid
    inp = dict(case_id=cid, ledger=deepcopy(ledger))
    inputs.append(inp)
    expectations.append(expected)
    controls.append(dict(case_id=cid, purpose=purpose, tags=tags, negative_strategies=strategies, invalid_input=invalid))
    by_id[cid] = (inp, expected)
    return cid

def get(cid):
    inp, expected = by_id[cid]
    return deepcopy(inp["ledger"]), deepcopy(expected)

def put(obj, path, value):
    keys = path.split(".")
    for key in keys[:-1]:
        obj = obj[key]
    obj[keys[-1]] = deepcopy(value)

def variant(cid, parent, ledger_edits, expected_edits, purpose, tags, strategies, invalid=False):
    ledger, expected = get(parent)
    for path, value in ledger_edits.items():
        put(ledger, path, value)
    for path, value in expected_edits.items():
        put(expected, path, value)
    expected["reason"] = purpose
    return add(cid, ledger, expected, purpose, tags, strategies, invalid)

def invariant(left, right, purpose):
    pairs.append(dict(pair_id="i" + str(len(pairs) + 1).zfill(3), left=left, right=right,
                      relation="INVARIANT", purpose=purpose, compare_fields=FIELDS,
                      must_change=[], renaming={}))

def sensitivity(left, right, diff, purpose):
    # The changed paths are manual hypotheses; the check compares expected rows.
    pairs.append(dict(pair_id="s" + str(len(pairs) + 1).zfill(3), left=left, right=right,
                      relation="SENSITIVITY", purpose=purpose,
                      compare_fields=[p for p in FIELDS if p not in diff],
                      must_change=diff, renaming={}))

def renamed(cid, parent, maps, purpose):
    ledger, expected = get(parent)
    om, wm = maps["obligation_ids"], maps["witness_ids"]
    for obligation in ledger["obligations"]:
        obligation["id"] = om[obligation["id"]]
    for witness in ledger["witnesses"]:
        witness["id"] = wm[witness["id"]]
        for key in ["entails", "contradicts", "ambiguous"]:
            witness[key] = [om[x] for x in witness[key]]
    if ledger["proposal"] is not None:
        for key in ["core_ids", "gap_ids"]:
            ledger["proposal"][key] = [om[x] for x in ledger["proposal"][key]]
        ledger["proposal"]["body_witness_ids"] = [wm[x] for x in ledger["proposal"]["body_witness_ids"]]
    for key in ["core_ids", "gap_ids"]:
        expected[key] = sorted(om[x] for x in expected[key])
    expected["witness_ids"] = sorted(wm[x] for x in expected["witness_ids"])
    for key in ["missing_packet_ids", "contradicted_packet_ids", "ambiguous_ids", "conflicting_ids"]:
        expected["diagnostics"][key] = sorted(om[x] for x in expected["diagnostics"][key])
    expected["diagnostics"]["considered_witness_ids"] = sorted(wm[x] for x in expected["diagnostics"]["considered_witness_ids"])
    expected["reason"] = purpose
    add(cid, ledger, expected, purpose, ["opaque-identifiers", "renaming"], ["identifier_lookup", "noncanonical_output"])
    pairs.append(dict(pair_id="r" + str(len(pairs) + 1).zfill(3), left=parent, right=cid,
                      relation="RENAMED_INVARIANT", purpose=purpose, compare_fields=FIELDS,
                      must_change=[], renaming=maps))

def reverse_arrays(ledger):
    ledger["obligations"].reverse()
    ledger["witnesses"].reverse()
    for witness in ledger["witnesses"]:
        for key in ["apertures", "entails", "contradicts", "ambiguous"]:
            witness[key].reverse()
    if ledger["proposal"] is not None:
        for key in ["core_ids", "gap_ids", "body_witness_ids"]:
            ledger["proposal"][key].reverse()
    return ledger

S, O, U, I, X = "SUPPORTED", "OVER_BROAD", "UNSUPPORTED", "INCONCLUSIVE", "NOT_ASSESSED"
T = [True] * 6

# Three obligations, partial nominated witnesses combining by union, a redundant
# packet contributor, two partial quote witnesses, and a silent BODY witness.
full_ledger = L(["u8", "c2", "x5"], [W("m7", "BODY", ["N", "P"], ["u8", "c2"]), W("a4", "BODY", ["P", "N"], ["x5"]), W("z0", "BODY", ["P"], ["c2"]), W("s1", "QUOTE", ["Q"], ["u8", "x5"]), W("v9", "QUOTE", ["Q"], ["c2"]), W("e6", "BODY", ["N", "P"])])
full_expected = E("COMPLETE", [S,S,S], "FULL_BODY_SUPPORT", "SUFFICIENT", "FULL_BODY_SUPPORT", "KEEP_FULL", ["c2","u8","x5"], [], ["a4","m7","z0"], [S,S,S], [], [], [], [], ["a4","m7","s1","v9","z0"], [], "NOT_REQUIRED", "NONE", "Partial authorized witnesses unite to cover the complete obligation set; every contributing BODY witness is retained.")
full = add("k7r3", full_ledger, full_expected, full_expected["reason"], ["full-retention", "union", "silent-witness", "redundancy"], ["always_reject", "always_inconclusive", "minimal_witness_selection", "diagnostic_as_retained"])
l, e = get(full)
l["witnesses"] += [W("h3", "METADATA", [], ["u8","c2","x5"], ["c2"], ["x5"]), W("j2", "QUERY", [], [], ["u8"], ["c2"]), W("l4", "HEADING", [], ["x5"], ["u8","x5"], ["u8"])]
add("p9x2", l, e, "All three unauthorized surfaces remain excluded despite their declared support, contradiction and ambiguity.", ["unauthorized-surfaces", "invariance"], ["unauthorized_surface_import"])
invariant(full, "p9x2", "Unauthorized metadata/query/heading additions change no required output field.")
l, e = get(full)
add("n0v6", reverse_arrays(l), e, "Reverse obligation, witness, aperture and assessment array orders without changing identity or authority.", ["ordering", "invariance"], ["input_order_dependence", "noncanonical_output"])
invariant(full, "n0v6", "Input ordering is not semantic.")
renamed("t8a4", full, dict(case_ids={full:"t8a4"}, obligation_ids={"c2":"Ω2", "u8":"a0", "x5":"Z7"}, witness_ids={"m7":"β4","a4":"q1","z0":"A2","s1":"é8","v9":"k3","e6":"n9"}), "Complete namespace bijections also change Unicode sort order while preserving every decision field after mapping.")
variant("g2m9", full, {"proposal":P([], ["u8","c2","x5"], ["s1"], [None,False,None,False,None,False])}, {}, "A proposal with unknown and false guards and unsuitable support is not applicable to full packet support.", ["proposal-applicability", "full-retention"], ["blanket_guard_uncertainty", "blanket_qualifier_trimming"])
invariant(full, "g2m9", "Irrelevant proposal guards cannot withhold a full-supported record.")
l,e = get(full)
for w in l["witnesses"]:
    if w["surface"] == "QUOTE":
        w["entails"] = []
for path,value in {"apertures.Q":U,"citation":"QUOTE_INSUFFICIENT","finding":"CITATION_SPAN_INSUFFICIENCY","action":"HOLD_FOR_CITATION","diagnostics.local_apertures.Q":U,"diagnostics.considered_witness_ids":["a4","m7","z0"]}.items():
    put(e,path,value)
add("j4w1",l,e,"The nominated BODY remains complete when both selected quotes are silent; retain all content and hold for citation.",["quote-insufficiency","retained-identifiers"],["citation_grounding_conflation","blanket_qualifier_trimming"])
sensitivity(full,"j4w1",["apertures.Q","citation","finding","action","diagnostics.local_apertures.Q","diagnostics.considered_witness_ids"],"Removing quote assessments changes citation authority while leaving packet grounding and retained content fixed.")

nominated_ledger=L(["p6","d9","t3","r2"],[W("q3","QUOTE",["Q"],["p6","d9","t3","r2"]),W("f4","BODY",["N","P"],["p6","d9"]),W("c8","BODY",["P"],["t3","r2"]),W("x1","BODY",["P"],["p6"])])
nom_expected=E("COMPLETE",[S,O,S],"FULL_BODY_SUPPORT","NOMINATION_INSUFFICIENT","CITATION_SPAN_INSUFFICIENCY","HOLD_FOR_CITATION",["d9","p6","r2","t3"],[],["c8","f4","x1"],[S,O,S],[],[],[],[],["c8","f4","q3","x1"],[],"NOT_REQUIRED","NONE","Other packet BODY witnesses complete a claim that the nominated BODY only partially supports.")
nom=add("b6q0",nominated_ledger,nom_expected,nom_expected["reason"],["nomination-insufficiency","quote-full","packet-full"],["citation_grounding_conflation","always_support"])
l,e=get(nom)
l["witnesses"][0]["entails"]=["d9"]
put(e,"apertures.Q",O);put(e,"diagnostics.local_apertures.Q",O)
add("s2c5",l,e,"A deficient nomination takes precedence whether the quote is full or partial.",["citation-precedence"],["quote_first_citation"])
sensitivity(nom,"s2c5",["apertures.Q","diagnostics.local_apertures.Q"],"Quote coverage changes while nomination insufficiency and complete retention stay fixed.")
one=L(["n0"],[W("y6","BODY",["P"],["n0"]),W("k4","QUOTE",["Q"],["n0"])])
add("v1k8",one,E("COMPLETE",[S,U,S],"FULL_BODY_SUPPORT","NOMINATION_INSUFFICIENT","CITATION_SPAN_INSUFFICIENCY","HOLD_FOR_CITATION",["n0"],[],["y6"],[S,U,S],[],[],[],[],["k4","y6"],[],"NOT_REQUIRED","NONE","A singleton packet-supported obligation is retained despite the absence of nominated BODY support."),"Singleton packet support and absent nomination.",["singleton","nomination-absent"],["full_quote_import_into_body","always_reject"])
cross=L(["u1","a5"],[W("t7","BODY",["N","P"],["u1","a5"]),W("s4","QUOTE",["Q"],[],["a5"])])
cross_exp=E("COMPLETE",[U,S,S],"FULL_BODY_SUPPORT","QUOTE_INSUFFICIENT","CITATION_SPAN_INSUFFICIENCY","HOLD_FOR_CITATION",["a5","u1"],[],["t7"],[U,S,S],[],[],[],[],["s4","t7"],[],"NOT_REQUIRED","NONE","Pure QUOTE contradiction disagrees with BODY across apertures but introduces no overlap within an authorized aperture.")
cross_id=add("h9d3",cross,cross_exp,cross_exp["reason"],["cross-aperture","pure-quote-contradiction"],["cross_aperture_conflict_invention","quote_body_conflation"])

# Four obligations with a three-obligation safe core supplied jointly by two
# BODY witnesses; N is only a two-obligation nominated subset.
projection_ledger=L(["d2","h7","b1","s6"],[W("p8","BODY",["N","P"],["d2","h7"]),W("c4","BODY",["P"],["b1"]),W("m0","QUOTE",["Q"],["d2","h7","b1"])],P(["d2","h7","b1"],["s6"],["p8","c4"],T))
projection_expected=E("COMPLETE",[O,O,O],"PACKET_LEVEL_GROUNDING_DEFECT","NOMINATION_INSUFFICIENT","UNSUPPORTED_MATERIAL_QUALIFIER","PROPOSE_CORE_WITH_GAP",["b1","d2","h7"],["s6"],["c4","p8"],[O,O,O],["s6"],[],[],[],["c4","m0","p8"],[],"SAFE","NONE","The exact packet-supported core is proposed with its explicit unsupported companion and declared safe guards.")
safe=add("v4n8",projection_ledger,projection_expected,projection_expected["reason"],["safe-projection","material-qualifier","diagnostic-retained-separation"],["always_support","always_reject","always_inconclusive","blanket_qualifier_trimming","diagnostic_as_retained"])
l,e=get(safe)
l["witnesses"][2]["entails"]=["d2","h7","b1","s6"]
put(e,"apertures.Q",S);put(e,"diagnostics.local_apertures.Q",S)
add("q0s6",l,e,"QUOTE support for the missing packet obligation changes Q only; the complete claim remains packet-deficient.",["quote-body-separation","safe-projection"],["unauthorized_surface_import","citation_grounding_conflation"])
sensitivity(safe,"q0s6",["apertures.Q","diagnostics.local_apertures.Q"],"Quote-only support cannot fill the packet gap or repair nomination.")
unsafe_expected=deepcopy(projection_expected)
for path,value in {"finding":"UNSAFE_DECOMPOSITION","action":"REJECT_COMPLETE","core_ids":[],"gap_ids":[],"witness_ids":[],"diagnostics.proposal_status":"UNSAFE"}.items():
    put(unsafe_expected,path,value)
def unsafe(cid, proposal, purpose, tags):
    l,_=get(safe);l["proposal"]=proposal
    return add(cid,l,unsafe_expected,purpose,["unsafe-decomposition"]+tags,["blanket_qualifier_trimming","diagnostic_as_retained","always_support"])
unsafe("y7f2",P(["d2","b1"],["h7","s6"],["p8","c4"],T),"A projection may not discard the supported material obligation h7.",["supported-content-discard"])
unsafe("c9a5",P(["d2","h7","b1"],["h7","s6"],["p8","c4"],T),"Overlapping proposed core and gap are unsafe despite all declared guards.",["overlapping-partition"])
unsafe("m1u7",P(["d2","h7","b1"],[],["p8","c4"],T),"An omitted gap companion cannot authorize removal of unsupported material content.",["nonexhaustive-partition"])
variant("l6e4",safe,{"proposal":None},{"finding":"UNSAFE_DECOMPOSITION","action":"REJECT_COMPLETE","core_ids":[],"gap_ids":[],"witness_ids":[],"diagnostics.proposal_status":"ABSENT"},"Partial packet support with no proposal does not authorize a smaller claim.",["proposal-absent","diagnostic-retained-separation"],["blanket_qualifier_trimming","diagnostic_as_retained"])
for cid, index in [("r8t0",0),("p3g9",1),("w5b1",2),("a6z2",3),("e0h8",4),("d4j7",5)]:
    guards=T.copy();guards[index]=False
    unsafe(cid,P(["d2","h7","b1"],["s6"],["p8","c4"],guards),"The declared guard "+GUARDS[index]+" is false, so no core is retained.",["false-guard",GUARDS[index]])
    sensitivity(safe,cid,["finding","action","core_ids","gap_ids","witness_ids","diagnostics.proposal_status"],"Only this guard is changed from true to false; diagnostic packet support stays descriptive.")
for cid,guards in [("f2w9",[True,False,True,None,True,True]),("u5r0",[True,True,True,None,True,True])]:
    l,_=get(safe);l["proposal"]=P(["d2","h7","b1"],["s6"],["p8","c4"],guards)
    exp=E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[O,O,O],["s6"],[],[],[],["c4","m0","p8"],["DECOMPOSITION_UNKNOWN"],"UNKNOWN","NONE","An applicable null guard precedes a false guard or an otherwise safe structure; local diagnostics retain no authority.")
    add(cid,l,exp,exp["reason"],["unknown-guard","uncertainty-precedence"],["false_before_unknown","local_support_leak","diagnostic_as_retained"])
invariant("f2w9","u5r0","A false guard has no further output effect when another applicable guard is unknown.")
sensitivity(safe,"u5r0",["assessment_status","apertures.Q","apertures.N","apertures.P","grounding","citation","finding","action","core_ids","gap_ids","witness_ids","diagnostics.uncertainty_sources","diagnostics.proposal_status"],"A single applicable guard becomes null; descriptive IDs stay fixed and authoritative IDs clear.")
unsafe("z3m8",P(["d2","h7","b1"],["s6"],["p8"],T),"Proposed support witnesses omit the BODY contributor needed for b1.",["incomplete-core-witness-coverage"])
unsafe("k0q4",P(["d2","h7","b1"],["s6"],["p8","c4","m0"],T),"Including a QUOTE as proposal BODY support is a valid reference but unsafe witness selection.",["unauthorized-proposal-witness"])
l,_=get(safe);l["witnesses"].append(W("w9","BODY",["P"]));l["proposal"]["body_witness_ids"].append("w9")
add("n7s1",l,unsafe_expected,"A listed silent BODY witness entails no core ID and fails proposal suitability.",["unsafe-decomposition","silent-proposal-witness"],["unused_witness_admission","diagnostic_as_retained"])
unsafe("t6v3",P(["d2","h7","b1"],["s6"],[],T),"An empty proposal support list cannot authorize the core.",["empty-core-witness-set"])
unsafe("x2a8",P([],["d2","h7","b1","s6"],["p8","c4"],T),"An empty core is an unsafe partition, not an input apparatus error.",["empty-core"])
unsafe("b5l0",P(["d2","h7","b1","s6"],[],["p8","c4"],T),"Adding the unsupported obligation s6 to the core cannot produce a safe projection.",["unsupported-core-content"])
l,e=get(safe)
add("j8p6",reverse_arrays(l),e,"Reverse proposal partition/support and all ledger array orders on a safely projected record.",["ordering","safe-projection"],["input_order_dependence","noncanonical_output"])
invariant(safe,"j8p6","Ordering invariance includes accepted proposal identifiers.")
renamed("h4c7",safe,dict(case_ids={safe:"h4c7"},obligation_ids={"d2":"η8","h7":"L1","b1":"p0","s6":"A9"},witness_ids={"p8":"z2","c4":"é1","m0":"B8"}),"Rename an accepted projection including core, gap, proposal support and diagnostic namespaces.")
sensitivity(safe,"y7f2",["finding","action","core_ids","gap_ids","witness_ids","diagnostics.proposal_status"],"A complete packet-supported core cannot be replaced by a narrower supported subset.")
sensitivity(safe,"l6e4",["finding","action","core_ids","gap_ids","witness_ids","diagnostics.proposal_status"],"Deleting a proposal preserves diagnostic support but removes authorization of a projection.")

quoteonly=L(["z7","o3"],[W("b6","QUOTE",["Q"],["z7","o3"]),W("s9","METADATA",[],["z7","o3"])])
quote_exp=E("COMPLETE",[S,U,U],"PACKET_LEVEL_GROUNDING_DEFECT","NOMINATION_INSUFFICIENT","NO_SUPPORTED_CORE","REJECT_COMPLETE",[],[],[],[S,U,U],["o3","z7"],[],[],[],["b6"],[],"NOT_REQUIRED","NONE","Full selected quote and metadata support provide no authorized BODY-supported core.")
quoteid=add("p8e2",quoteonly,quote_exp,quote_exp["reason"],["zero-packet-support","full-quote","metadata"],["quote_body_conflation","unauthorized_surface_import","diagnostic_as_retained"])
variant("g9x5",quoteid,{"proposal":P(["z7"],["o3"],["b6"],[None]*6)},{},"A null-guard proposal is not applicable where no packet obligation is supported.",["proposal-applicability","zero-support"],["blanket_guard_uncertainty","quote_body_conflation"])
invariant(quoteid,"g9x5","No packet core means proposal guards and quote support cannot authorize projection or uncertainty.")
empty=L(["n5"],[])
empty_exp=E("COMPLETE",[U,U,U],"PACKET_LEVEL_GROUNDING_DEFECT","NOMINATION_INSUFFICIENT","NO_SUPPORTED_CORE","REJECT_COMPLETE",[],[],[],[U,U,U],["n5"],[],[],[],[],[],"NOT_REQUIRED","NONE","No witnesses means no supported core, with the original obligation present only in diagnostic missing IDs.")
add("a2t7",empty,empty_exp,empty_exp["reason"],["empty-witnesses","singleton","diagnostic-retained-separation"],["always_support","diagnostic_as_retained"])
l,e=get("a2t7")
l["witnesses"]=[W("d0","QUERY",[],["n5"],["n5"],["n5"]),W("v2","HEADING",[],["n5"],["n5"],["n5"]),W("a9","METADATA",[],["n5"],["n5"],["n5"])]
add("s0k6",l,e,"Unauthorized surfaces remain irrelevant even when all assessment sets overlap.",["unauthorized-surfaces","invariance"],["unauthorized_surface_import","unauthorized_ambiguity_import"])
invariant("a2t7","s0k6","No authoritative or diagnostic witness set imports unauthorized evidence.")

contr=L(["j2","v6","a9"],[W("r5","BODY",["N","P"],["j2","v6"]),W("f8","BODY",["P"],[],["a9"]),W("l0","QUOTE",["Q"],["j2","v6","a9"])],P(["j2","v6"],["a9"],["r5"],T))
contr_exp=E("COMPLETE",[S,O,U],"PACKET_LEVEL_GROUNDING_DEFECT","NOMINATION_INSUFFICIENT","CONTRADICTED_CLAIM","REJECT_COMPLETE",[],[],[],[S,O,U],["a9"],["a9"],[],[],["f8","l0","r5"],[],"NOT_REQUIRED","NONE","Pure packet contradiction rejects the complete claim and makes even a structurally safe trimming proposal irrelevant.")
contrid=add("d3v9",contr,contr_exp,contr_exp["reason"],["pure-contradiction","proposal-precedence","diagnostic-retained-separation"],["contradiction_as_gap","blanket_qualifier_trimming","diagnostic_as_retained"])
variant("w8j1",contrid,{"proposal":P([],["j2","v6","a9"],["l0"],[None,False,None,False,None,False])},{},"Contradiction precedence makes unknown or false proposal guards inapplicable.",["proposal-applicability","contradiction"],["blanket_guard_uncertainty","false_before_unknown"])
invariant(contrid,"w8j1","A contradicted packet cannot be rescued or made semantically uncertain by proposal guards.")
add("n6q4",L(["t1","p9"],[W("u4","BODY",["P"],[],["t1"]),W("b2","QUOTE",["Q"],["t1","p9"])],P(["t1"],["p9"],["u4"],[None]*6)),E("COMPLETE",[S,U,U],"PACKET_LEVEL_GROUNDING_DEFECT","NOMINATION_INSUFFICIENT","CONTRADICTED_CLAIM","REJECT_COMPLETE",[],[],[],[S,U,U],["p9","t1"],["t1"],[],[],["b2","u4"],[],"NOT_REQUIRED","NONE","A pure contradiction precedes the no-supported-core finding even when packet entailment is empty."),"Contradiction over zero packet entailment with ignored unknown proposal.",["pure-contradiction","zero-support","precedence"],["no_core_before_contradiction","quote_body_conflation"])

# Uncertainty collapses authority but deliberately preserves computable local
# diagnostics, including locally complete BODY support.
inc_full=E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[S,S,S],[],[],[],[],["a4","m7","s1","v9","z0"],["COVERAGE_UNKNOWN"],"NOT_ASSESSED","NONE","Unknown coverage withholds despite locally complete Q/N/P support; diagnostic IDs do not authorize retained content.")
l,_=get(full);l["coverage"]="UNKNOWN"
add("m0b7",l,inc_full,inc_full["reason"],["coverage-unknown","global-uncertainty","local-supported"],["local_support_leak","diagnostic_as_retained","always_support"])
sensitivity(full,"m0b7",["assessment_status","apertures.Q","apertures.N","apertures.P","grounding","citation","finding","action","core_ids","witness_ids","diagnostics.uncertainty_sources","diagnostics.proposal_status"],"Coverage uncertainty removes all retained authority while local diagnostics remain identical.")
l,e=get("m0b7");l["coverage"]="COMPLETE"
for ob in l["obligations"]:
    if ob["id"]=="c2":ob["materiality"]="UNKNOWN"
e["diagnostics"]["uncertainty_sources"]=["MATERIALITY_UNKNOWN"]
add("q5z3",l,e,"Unknown materiality preserves local support calculations but requires global withholding.",["materiality-unknown","local-supported"],["local_support_leak","unknown_materiality_as_nonmaterial"])
sensitivity("m0b7","q5z3",["diagnostics.uncertainty_sources"],"Materiality and coverage uncertainty have the same authority result but distinct source diagnostics.")
l,_=get(safe);l["coverage"]="UNKNOWN";l["obligations"][3]["materiality"]="UNKNOWN";l["proposal"]["guards"]["removal_independent"]=None
add("r1h6",l,E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[O,O,O],["s6"],[],[],[],["c4","m0","p8"],["COVERAGE_UNKNOWN","MATERIALITY_UNKNOWN"],"NOT_ASSESSED","NONE","Base uncertainty prevents proposal applicability, so its null guard is not an additional decomposition-unknown source."),"Base uncertainty precedence over an otherwise applicable null guard.",["base-uncertainty","proposal-not-assessed","multiple-sources"],["inapplicable_guard_import","local_support_leak"])
split=L(["e7","p2","w5"],[W("a1","BODY",["N","P"],["e7","p2","w5"]),W("z6","BODY",["P"],[],["p2"]),W("q8","QUOTE",["Q"],["e7","p2","w5"])])
add("v9c0",split,E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[S,S,I],[],["p2"],[],["p2"],["a1","q8","z6"],["AUTHORIZED_CONFLICT"],"NOT_ASSESSED","NONE","Two authorized BODY witnesses disagree in P; complete nominated and quote diagnostics cannot retain any claim."),"Conflicting authorized BODY witnesses.",["body-disagreement","global-uncertainty","local-supported"],["contradiction_preempts_conflict","local_support_leak","diagnostic_as_retained"])
add("e4s8",L(["s3","b6"],[W("q2","BODY",["N","P"],["s3","b6"],["b6"]),W("x7","QUOTE",["Q"],["s3","b6"])]),E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[S,I,I],[],["b6"],[],["b6"],["q2","x7"],["AUTHORIZED_CONFLICT"],"NOT_ASSESSED","NONE","Overlap within one authorized witness is a declared conflict, not a malformed assessment array."),"Within-witness entailment/contradiction overlap.",["authorized-conflict","within-witness","schema-valid-overlap"],["overlap_as_apparatus","contradiction_preempts_conflict"])
l,_=get(cross_id);l["witnesses"][1]["entails"]=["u1","a5"]
add("f7a2",l,E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[I,S,S],[],[],[],["a5"],["s4","t7"],["AUTHORIZED_CONFLICT"],"NOT_ASSESSED","NONE","Entailment added to the contradicting QUOTE creates a conflict within Q, globally withholding despite full BODY support."),"Q-only conflict propagates globally.",["quote-conflict","global-uncertainty","local-supported"],["quote_uncertainty_ignored","local_support_leak"])
sensitivity(cross_id,"f7a2",["assessment_status","apertures.Q","apertures.N","apertures.P","grounding","citation","finding","action","core_ids","witness_ids","diagnostics.local_apertures.Q","diagnostics.conflicting_ids","diagnostics.uncertainty_sources","diagnostics.proposal_status"],"Cross-aperture disagreement becomes actual within-Q conflict when Q entailment is added.")
l,_=get(cross_id);l["witnesses"][1]=W("s4","QUOTE",["Q"],[],[],["a5"])
add("k3u5",l,E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[I,S,S],[],[],["a5"],[],["s4","t7"],["AUTHORIZED_AMBIGUITY"],"NOT_ASSESSED","NONE","Authorized ambiguity in Q alone propagates globally while complete BODY support remains diagnostic."),"Q ambiguity cannot be ignored just because packet support is complete.",["authorized-ambiguity","quote","global-uncertainty"],["quote_uncertainty_ignored","local_support_leak"])
l,_=get(full);l["witnesses"].append(W("o9","BODY",["P"],[],[],["x5"]))
add("t0n9",l,E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[S,S,I],[],[],["x5"],[],["a4","m7","o9","s1","v9","z0"],["AUTHORIZED_AMBIGUITY"],"NOT_ASSESSED","NONE","Packet BODY ambiguity is sufficient for global withholding; diagnostic complete Q/N support is not retained."),"P-only authorized ambiguity with complete nominated and quote diagnostics.",["authorized-ambiguity","body","global-uncertainty"],["ambiguity_without_missing_support_ignored","local_support_leak"])
combo=L(["d8","t4","y0"],[W("m2","BODY",["N","P"],["d8","t4"]),W("b7","BODY",["P"],[],["t4"]),W("n3","QUOTE",["Q"],["d8"],[],["y0"])],P(["d8"],["t4","y0"],["m2"],[None,False,True,True,True,True]),coverage="UNKNOWN",unknown=["y0"])
add("b7p4",combo,E("INCONCLUSIVE",[I,I,I],"INCONCLUSIVE","INCONCLUSIVE","INCONCLUSIVE","WITHHOLD",[],[],[],[I,O,I],["y0"],["t4"],["y0"],["t4"],["b7","m2","n3"],["AUTHORIZED_AMBIGUITY","AUTHORIZED_CONFLICT","COVERAGE_UNKNOWN","MATERIALITY_UNKNOWN"],"NOT_ASSESSED","NONE","All four computable base sources are recorded; null proposal guards are not assessed under base uncertainty."),"Combined base uncertainty sources with canonically sorted diagnostics.",["multiple-sources","global-uncertainty","precedence"],["first_uncertainty_only","inapplicable_guard_import","diagnostic_as_retained"])

def stopped(code):
    return E("APPARATUS_FAILURE",[X,X,X],"NOT_ASSESSED","NOT_ASSESSED","APPARATUS_FAILURE","STOP",[],[],[],[X,X,X],[],[],[],[],[],[],"NOT_ASSESSED",code,"Apparatus failure clears all semantic diagnostics and retained IDs; only the failure code is preserved.")
l,_=get(full);l["integrity"]="UNKNOWN"
add("x9g1",l,stopped("INTEGRITY_UNKNOWN"),"Unknown integrity precedes complete local support and stops assessment.",["integrity-unknown","apparatus-precedence"],["integrity_as_semantic_uncertainty","diagnostic_as_retained"])
l,_=get("r1h6");l["integrity"]="CUSTODY_INVALID"
add("a0m6",l,stopped("INTEGRITY_NOT_VALID"),"Invalid custody precedes unknown coverage/materiality and a null applicable-looking proposal.",["custody-invalid","apparatus-precedence"],["uncertainty_before_apparatus","untrusted_diagnostics_leak"])
l,_=get(full);l["integrity"]="ASSESSOR_UNAVAILABLE"
add("c5r8",l,stopped("INTEGRITY_NOT_VALID"),"Unavailable assessor stops rather than producing an ordinary semantic decision.",["assessor-unavailable","apparatus"],["simulated_semantic_completeness","untrusted_diagnostics_leak"])
l,_=get(contrid);l["integrity"]="EXECUTION_FAILURE"
add("s6d2",l,stopped("INTEGRITY_NOT_VALID"),"Execution failure stops before a ledger contradiction can become a semantic finding.",["execution-failure","apparatus-precedence"],["contradiction_before_apparatus","untrusted_diagnostics_leak"])
invariant("a0m6","c5r8","Different non-valid integrity categories and very different ledgers share the required cleared STOP fields.")
invariant("a0m6","s6d2","Semantic ledger content cannot appear in stopped diagnostics.")
sensitivity("x9g1","c5r8",["diagnostics.apparatus_code"],"Unknown integrity and explicit integrity failure differ only in the apparatus code.")

def invalid(cid, ledger, purpose, tags):
    return add(cid,ledger,stopped("INVALID_INPUT"),purpose,["invalid-input"]+tags,["silent_malformed_discard","malformed_as_semantic","untrusted_diagnostics_leak"],True)
l,_=get(full);l["extra"]=False
invalid("p1w7",l,"An unknown ledger field is rejected before semantic assessment.",["unknown-field"])
l,_=get(full);l["witnesses"][0]["apertures"]=["Q","P"]
invalid("m8t2",l,"BODY is never authorized in Q; illegal aperture assignment is apparatus invalid.",["illegal-body-aperture"])
l,_=get(full);l["witnesses"][0]["entails"].append("z9")
invalid("g4a0",l,"An undeclared obligation assessment is an input-reference failure.",["unknown-assessment-reference"])
l,_=get(full);l["obligations"].append(deepcopy(l["obligations"][0]))
invalid("u7n5",l,"Duplicate obligation IDs violate referential identity even when records match.",["duplicate-obligation-id"])
l,_=get(full);l["witnesses"].append(deepcopy(l["witnesses"][0]))
invalid("e2q9",l,"Duplicate witness IDs violate referential identity.",["duplicate-witness-id"])
l,_=get(full);l["coverage"]="PARTIAL";l["integrity"]="UNKNOWN"
invalid("z6b3",l,"Invalid coverage enum takes precedence over unknown integrity.",["invalid-enum","apparatus-code-precedence"])
l,_=get(full);l["witnesses"][0]["entails"].append("u8")
invalid("k5r0",l,"A duplicate assessment ID violates the unique-array schema.",["duplicate-assessment-id"])
l,_=get(safe);del l["proposal"]["guards"]["gap_explicit"]
invalid("b9c4",l,"Missing guard declaration is invalid input; no guard default is allowed.",["missing-guard"])
l,_=get(safe);l["proposal"]["body_witness_ids"]=["a0"]
invalid("r2v8",l,"Unknown proposal witness ID is apparatus invalid, unlike a known but unsuitable QUOTE witness.",["unknown-proposal-reference"])
l,_=get("s0k6");l["witnesses"][0]["apertures"]=["P"]
invalid("n3s7",l,"QUERY cannot acquire authority by declaring a packet aperture.",["illegal-query-aperture"])
l,_=get(full);l["witnesses"][3]["apertures"]=["Q","N","P"]
invalid("w0h5",l,"QUOTE cannot import nominated or packet BODY authority by listing those apertures.",["illegal-quote-aperture"])
l,_=get(safe);l["proposal"]["guards"]["bindings_preserved"]=1
invalid("d7p1",l,"The integer 1 is not the boolean true guard declaration.",["guard-type"])
l,_=get(safe);l["proposal"]["core_ids"].append("x0")
invalid("f8m2",l,"Unknown proposed obligation IDs are input-reference errors.",["unknown-proposal-obligation"])
l,_=get(full);l["obligations"]=[]
invalid("q4j6",l,"The obligation set must be nonempty.",["empty-obligations"])
l,_=get(full);del l["coverage"]
invalid("a7z9",l,"Coverage must be explicitly declared; there is no COMPLETE default.",["missing-coverage"])
invariant("p1w7","z6b3","INVALID_INPUT diagnostics are cleared regardless of whether invalidity coexists with unknown integrity.")
invariant("m8t2","w0h5","Illegal BODY and QUOTE authority assignments are both apparatus failures.")
sensitivity("x9g1","z6b3",["diagnostics.apparatus_code"],"Schema invalidity wins over the integrity-unknown apparatus code.")
sensitivity("k0q4","r2v8",["assessment_status","apertures.Q","apertures.N","apertures.P","grounding","citation","finding","action","diagnostics.local_apertures.Q","diagnostics.local_apertures.N","diagnostics.local_apertures.P","diagnostics.missing_packet_ids","diagnostics.considered_witness_ids","diagnostics.proposal_status","diagnostics.apparatus_code"],"Known unsuitable proposal support is unsafe semantics; an unknown support reference stops the apparatus.")

overlap=L(["m5"],[W("m5","BODY",["N","P"],["m5"]),W("r4n2","QUOTE",["Q"],["m5"])])
add("r4n2",overlap,E("COMPLETE",[S,S,S],"FULL_BODY_SUPPORT","SUFFICIENT","FULL_BODY_SUPPORT","KEEP_FULL",["m5"],[],["m5"],[S,S,S],[],[],[],[],["m5","r4n2"],[],"NOT_REQUIRED","NONE","Case, obligation and witness namespaces may overlap; each explicit namespace retains its own role."),"Legal cross-namespace identifier overlap.",["namespace-overlap","opaque-identifiers"],["global_id_uniqueness","identifier_lookup"])
renamed("m5","r4n2",dict(case_ids={"r4n2":"m5"},obligation_ids={"m5":"r4n2"},witness_ids={"m5":"x0","r4n2":"m5"}),"Complete renaming maps are namespace-specific even where their source strings overlap.")

def dump(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")

def jsonl(name,rows):
    (ROOT/name).write_text("".join(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for row in rows),encoding="utf-8")

jsonl("inputs.jsonl",inputs)
jsonl("expectations.jsonl",expectations)
dump("controls.json",dict(schema_version="qualifier-grounding-controls/v2",set_id=SET_ID,controls=controls))
dump("pairs.json",dict(schema_version="qualifier-grounding-pairs/v2",set_id=SET_ID,pairs=pairs))
allowlist=[]
actual_reads=[]
for name,initial_bytes,initial_hash,initial_time in [
    ("policy.json",17085,"96fcb4cb34378d768a4870f284e0d61c7f40a9f73a923170454fc9994c481f14","2026-09-30T20:16:05.297240+00:00"),
    ("interface.json",17008,"1ab5683435afd17976f4f093e1a07740f540fc6700e9f615b1d5fbb2e773b387","2026-09-30T20:16:05.297521+00:00"),
    ("SCHEMA.md",3537,"e46a99a1676d2b1499093dbef1b5a0521fe4b5ed57c921000d2d507149b1801d","2026-09-30T20:16:05.297669+00:00")]:
    read_at=utc();data=(ROOT.parent/name).read_bytes();sha=hashlib.sha256(data).hexdigest()
    if sha!=initial_hash or len(data)!=initial_bytes:raise RuntimeError("Frozen allowlist identity changed: "+name)
    allowlist.append(dict(source_name=name,bytes=len(data),sha256=sha))
    actual_reads.append(dict(source_name=name,operation="read_bytes and complete UTF-8 content display",read_at_utc=initial_time,sha256=initial_hash,bytes=initial_bytes,output_recovery="Combined tool result truncated part of interface.json; policy.json and SCHEMA.md were complete in displayed content."))
    actual_reads.append(dict(source_name=name,operation="draft artifact hash recheck only",read_at_utc=read_at,sha256=sha,bytes=len(data)))
actual_reads.insert(3,dict(source_name="interface.json",operation="complete separate cat content display to recover truncation",read_at_utc=None,sha256="1ab5683435afd17976f4f093e1a07740f540fc6700e9f615b1d5fbb2e773b387",bytes=17008,timestamp_limit="Occurred after the timestamped combined read and before build_controls.py creation; tool did not return a wall-clock timestamp for that recovery."))
author=dict(schema_version="qualifier-grounding-author/v2",set_id=SET_ID,author_identity=AUTHOR_ID,created_at_utc=utc(),
            context_creation=dict(fork_turns="none",delegation="Human explicitly authorized context-free fresh author delegation.",parent_conversation_supplied=False,task_directive="Author symbolic acceptance controls from the three clean frozen normative allowlist copies only."),
            normative_identity=dict(commit="ae754348d4ec8a8c6515d9dd4c67a77b07666428",tree="99b2c5b6ed7d084e8a73d802684f17a8904eba2c",identity_provenance="Supplied delegation identity, not independently verified by repository/history access."),
            input_allowlist=allowlist,actual_reads=actual_reads,
            startup_context_exposure=dict(generic_instruction_classes=["system/developer agent and tool conventions","MainFrame global operating contract","skill catalog without skill content reads","workspace paths, date, permissions, and multi-agent role conventions"],incidental_memory_subject_classes=["MainFrame operations and Supervisor Desk","Conduit","MindGraph","ERS and CAL Pipeline","biotech evaluation","decision authority qualification","Evidence Room governance","Conduit lifecycle lineage","Brain research and gate experiment"],incidental_memory_use="Inventory only; unrelated project facts were not used as normative authority, not retrieved, and not incorporated into cases.",predecessor_assessment_ledger_material_observed=False),
            forbidden_exposure=dict(status="NO_FORBIDDEN_QUALIFICATION_EXPOSURE_OBSERVED",contamination_status="CLEAR_RESTRICTED_APERTURE",prohibited_classes=["predecessor ledger controls","predecessor expectations or pair relations","reducer source","per-case predecessor decisions/results/terminal labels","historical anchor material","exact predecessor case IDs or answer patterns"],active_existing_content_reads_outside_allowlist=[],repository_history_reads=0,memory_retrievals=0,session_open_calls=0,mindgraph_calls=0,project_model_provider_calls=0,external_service_calls=0,reducer_implementations=0,reducer_calls=0),
            expectation_provenance=dict(evaluator="agent_llm",status="needs-audit",authority="Manually authored hypotheses from frozen declared symbolic assessments.",natural_language_claims_generated=False,decision_reason_text="Short contract-rationale annotations only; no domain claims or answer prose."),
            method=["Read the complete normative contract and exact schemas through the three-file aperture; recover interface truncation.","Design original opaque symbolic structures, then explicitly author each expected enum, array and diagnostic field.","Encode manual rows with object constructors and canonical sorting; copy manually asserted invariants, or perform explicit namespace renaming, without evaluating ledger policy in code.","State complete invariants and precise sensitivity equal/different field partitions.","Validate schemas and referential structure plus canonical outputs, provenance metadata and expected pair relations only; never invoke a reducer.","Seal authored outputs, drafting helper, structural checker and check receipt before reporting."],
            limitations=["Finite symbolic controls do not establish real-world truth, semantic assessor competence, or correctness for all possible ledgers.","Expected decisions remain needs-audit hypotheses; schema and pair checks are structural, not independent semantic qualification.","No predecessor comparison was performed; originality is authored without access to predecessor material, not asserted from a fixture-diff proof.","Isolation evidence covers supplied context inventory and deliberate tool content reads, not an OS-enforced content sandbox or a claim about model-training history.","Installed jsonschema and Python standard-library imports are ordinary runtime machinery; no additional API documentation or project content was consulted.","Clean normative commit/tree identities were supplied; only allowlist byte hashes were locally verified.","The complete cat recovery was not separately wall-clock timestamped by the tool."],
            material_contract_ambiguities=[],deviations=["The task destination acceptance-controls/ overrides SCHEMA.md's suggested new-directory name fresh-controls/; encoding is unchanged."],
            authored_artifact_counts=dict(inputs=len(inputs),expectations=len(expectations),controls=len(controls),pairs=len(pairs)),
            artifact_source_names=["inputs.jsonl","expectations.jsonl","controls.json","pairs.json","AUTHOR.json","build_controls.py","check_controls.py","checks.json","freeze_controls.py","freeze.json"],unsealed_drafting_artifacts=[])
dump("AUTHOR.json",author)
print(json.dumps(dict(set_id=SET_ID,inputs=len(inputs),expectations=len(expectations),controls=len(controls),pairs=len(pairs),author=AUTHOR_ID)))
