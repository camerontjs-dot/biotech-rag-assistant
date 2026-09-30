"""Schema/reference/pair checks only. No policy evaluation or reducer call."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
from collections import Counter
import hashlib
import json
import jsonschema

ROOT=Path(__file__).resolve().parent
started=datetime.now(timezone.utc).isoformat()
data=(ROOT.parent/"interface.json").read_bytes()
interface=json.loads(data)
author=json.loads((ROOT/"AUTHOR.json").read_text(encoding="utf-8"))
author["actual_reads"].append(dict(source_name="interface.json",operation="structural checker reads exact input/output schemas and referential constraints",read_at_utc=started,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
checks=[]
failures=[]

def check(condition,name,detail=""):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    if not condition:failures.append(dict(check=name,detail=detail))

def rows(name):
    return [json.loads(line) for line in (ROOT/name).read_text(encoding="utf-8").splitlines()]

inputs=rows("inputs.jsonl")
expectations=rows("expectations.jsonl")
controls=json.loads((ROOT/"controls.json").read_text(encoding="utf-8"))
pairs=json.loads((ROOT/"pairs.json").read_text(encoding="utf-8"))

control_schema={"type":"object","required":["schema_version","set_id","controls"],"additionalProperties":False,"properties":{"schema_version":{"const":"qualifier-grounding-controls/v2"},"set_id":{"type":"string","minLength":1},"controls":{"type":"array","minItems":1,"items":{"type":"object","required":["case_id","purpose","tags","negative_strategies","invalid_input"],"additionalProperties":False,"properties":{"case_id":{"type":"string","minLength":1},"purpose":{"type":"string","minLength":1},"tags":{"type":"array","items":{"type":"string","minLength":1},"minItems":1,"uniqueItems":True},"negative_strategies":{"type":"array","items":{"type":"string","minLength":1},"minItems":1,"uniqueItems":True},"invalid_input":{"type":"boolean"}}}}}}
pair_schema={"type":"object","required":["schema_version","set_id","pairs"],"additionalProperties":False,"properties":{"schema_version":{"const":"qualifier-grounding-pairs/v2"},"set_id":{"type":"string","minLength":1},"pairs":{"type":"array","minItems":1,"items":{"type":"object","required":["pair_id","left","right","relation","purpose","compare_fields","must_change","renaming"],"additionalProperties":False,"properties":{"pair_id":{"type":"string","minLength":1},"left":{"type":"string","minLength":1},"right":{"type":"string","minLength":1},"relation":{"enum":["INVARIANT","RENAMED_INVARIANT","SENSITIVITY"]},"purpose":{"type":"string","minLength":1},"compare_fields":{"type":"array","items":{"type":"string","minLength":1},"uniqueItems":True},"must_change":{"type":"array","items":{"type":"string","minLength":1},"uniqueItems":True},"renaming":{"type":"object"}}}}}}

for name,schema,obj in [("controls",control_schema,controls),("pairs",pair_schema,pairs)]:
    errors=list(jsonschema.Draft202012Validator(schema).iter_errors(obj))
    check(not errors,name+".schema", "; ".join(e.message for e in errors))
check(controls["set_id"]==pairs["set_id"]==author["set_id"],"set_identity.consistent")

def index_by_id(items,field,name):
    ids=[x[field] for x in items]
    check(len(ids)==len(set(ids)),name+".unique_ids")
    return {x[field]:x for x in items}

ii=index_by_id(inputs,"case_id","inputs")
ee=index_by_id(expectations,"case_id","expectations")
cc=index_by_id(controls["controls"],"case_id","controls")
check(set(ii)==set(ee)==set(cc),"case_sets.exactly_equal")
check(all(isinstance(cid,str) and len(cid)>0 for cid in ii),"inputs.outer_case_id_valid")

def reference_issues(inp):
    # No E/C/A unions, aperture aggregation, guard logic, or decision inference.
    out=[]
    ledger=inp.get("ledger")
    if not isinstance(ledger,dict):return ["ledger not object"]
    obs=ledger.get("obligations",[])
    ws=ledger.get("witnesses",[])
    if not isinstance(obs,list) or not isinstance(ws,list):return ["reference collections not arrays"]
    if not all(isinstance(x,dict) for x in obs+ws):return ["reference items not objects"]
    oids=[x.get("id") for x in obs]
    wids=[x.get("id") for x in ws]
    if len(oids)!=len(set(oids)):out.append("duplicate obligation IDs")
    if len(wids)!=len(set(wids)):out.append("duplicate witness IDs")
    for w in ws:
        for key in ["entails","contradicts","ambiguous"]:
            values=w.get(key,[])
            if isinstance(values,list) and any(x not in oids for x in values):out.append("unknown witness obligation reference")
        ap=w.get("apertures",[])
        surf=w.get("surface")
        legal=(surf=="QUOTE" and ap==["Q"]) or (surf=="BODY" and ap in [["P"],["N","P"],["P","N"]]) or (surf in ["QUERY","HEADING","METADATA"] and ap==[])
        if not legal:out.append("illegal surface/aperture assignment")
    p=ledger.get("proposal")
    if isinstance(p,dict):
        for key in ["core_ids","gap_ids"]:
            if isinstance(p.get(key),list) and any(x not in oids for x in p[key]):out.append("unknown proposal obligation reference")
        if isinstance(p.get("body_witness_ids"),list) and any(x not in wids for x in p["body_witness_ids"]):out.append("unknown proposal witness reference")
    return sorted(set(out))

invalid_observations=[]
input_validator=jsonschema.Draft202012Validator(interface["input_schema"])
output_validator=jsonschema.Draft202012Validator(interface["output_schema"])
for cid,inp in ii.items():
    schema_errors=list(input_validator.iter_errors(inp))
    ref_errors=reference_issues(inp)
    valid=not schema_errors and not ref_errors
    expected_invalid=cc[cid]["invalid_input"]
    check(valid != expected_invalid,"input.validity_annotation."+cid,"schema="+str([e.message for e in schema_errors])+"; refs="+str(ref_errors))
    if expected_invalid:
        invalid_observations.append(dict(case_id=cid,schema_errors=[dict(path=list(e.absolute_path),message=e.message) for e in schema_errors],referential_errors=ref_errors))
        out=ee[cid]
        check(out["assessment_status"]=="APPARATUS_FAILURE" and out["action"]=="STOP" and out["finding"]=="APPARATUS_FAILURE" and out["diagnostics"]["apparatus_code"]=="INVALID_INPUT","input.invalid_expected_stop."+cid)
    output_errors=list(output_validator.iter_errors(ee[cid]))
    check(not output_errors,"output.schema."+cid,"; ".join(e.message for e in output_errors))
    check(ee[cid]["case_id"]==cid,"output.case_id."+cid)

def array_paths(schema,prefix=""):
    result=[]
    if schema.get("type")=="array":result.append(prefix)
    elif schema.get("type")=="object":
        for key,value in schema["properties"].items():result+=array_paths(value,key if not prefix else prefix+"."+key)
    return result

def leaves(schema,prefix=""):
    if schema.get("type")=="object":
        result=[]
        for key,value in schema["properties"].items():result+=leaves(value,key if not prefix else prefix+"."+key)
        return result
    return [prefix]

fields=[x for x in leaves(interface["output_schema"]) if x not in ["case_id","reason"]]
arrays=array_paths(interface["output_schema"])
def at(obj,path):
    for part in path.split("."):obj=obj[part]
    return obj

for cid,out in ee.items():
    for path in arrays:
        values=at(out,path)
        check(values==sorted(values) and len(values)==len(set(values)),"output.canonical."+cid+"."+path)
    if out["action"] in ["REJECT_COMPLETE","WITHHOLD","STOP"]:
        check(out["core_ids"]==out["gap_ids"]==out["witness_ids"]==[],"output.nonretaining_lists_empty."+cid)
    if out["assessment_status"]=="INCONCLUSIVE":
        check(out["apertures"]==dict(Q="INCONCLUSIVE",N="INCONCLUSIVE",P="INCONCLUSIVE") and out["grounding"]==out["citation"]=="INCONCLUSIVE","output.authority_collapsed."+cid)
    if out["action"]=="STOP":
        diag=out["diagnostics"]
        check(diag["local_apertures"]==dict(Q="NOT_ASSESSED",N="NOT_ASSESSED",P="NOT_ASSESSED") and all(diag[x]==[] for x in ["missing_packet_ids","contradicted_packet_ids","ambiguous_ids","conflicting_ids","considered_witness_ids","uncertainty_sources"]) and diag["proposal_status"]=="NOT_ASSESSED","output.stopped_diagnostics_clear."+cid)
    if not cc[cid]["invalid_input"]:
        oids={x["id"] for x in ii[cid]["ledger"]["obligations"]}
        wids={x["id"] for x in ii[cid]["ledger"]["witnesses"]}
        op=["core_ids","gap_ids","diagnostics.missing_packet_ids","diagnostics.contradicted_packet_ids","diagnostics.ambiguous_ids","diagnostics.conflicting_ids"]
        wp=["witness_ids","diagnostics.considered_witness_ids"]
        check(all(set(at(out,p))<=oids for p in op) and all(set(at(out,p))<=wids for p in wp),"output.declared_references."+cid)

def rename_output(out,maps):
    out=deepcopy(out)
    out["case_id"]=maps["case_ids"][out["case_id"]]
    for path in ["core_ids","gap_ids","diagnostics.missing_packet_ids","diagnostics.contradicted_packet_ids","diagnostics.ambiguous_ids","diagnostics.conflicting_ids"]:
        obj=out;keys=path.split(".")
        for key in keys[:-1]:obj=obj[key]
        obj[keys[-1]]=sorted(maps["obligation_ids"][x] for x in obj[keys[-1]])
    for path in ["witness_ids","diagnostics.considered_witness_ids"]:
        obj=out;keys=path.split(".")
        for key in keys[:-1]:obj=obj[key]
        obj[keys[-1]]=sorted(maps["witness_ids"][x] for x in obj[keys[-1]])
    return out

def rename_input(inp,maps):
    inp=deepcopy(inp)
    inp["case_id"]=maps["case_ids"][inp["case_id"]]
    l=inp["ledger"]
    for o in l["obligations"]:o["id"]=maps["obligation_ids"][o["id"]]
    for w in l["witnesses"]:
        w["id"]=maps["witness_ids"][w["id"]]
        for key in ["entails","contradicts","ambiguous"]:w[key]=[maps["obligation_ids"][x] for x in w[key]]
    if l["proposal"] is not None:
        for key in ["core_ids","gap_ids"]:l["proposal"][key]=[maps["obligation_ids"][x] for x in l["proposal"][key]]
        l["proposal"]["body_witness_ids"]=[maps["witness_ids"][x] for x in l["proposal"]["body_witness_ids"]]
    return inp

def normalize_input(inp):
    inp=deepcopy(inp);l=inp["ledger"]
    l["obligations"].sort(key=lambda x:x["id"]);l["witnesses"].sort(key=lambda x:x["id"])
    for w in l["witnesses"]:
        for key in ["apertures","entails","contradicts","ambiguous"]:w[key].sort()
    if l["proposal"] is not None:
        for key in ["core_ids","gap_ids","body_witness_ids"]:l["proposal"][key].sort()
    return inp

pair_ids=[p["pair_id"] for p in pairs["pairs"]]
check(len(pair_ids)==len(set(pair_ids)),"pairs.unique_ids")
pair_results=[]
for pair in pairs["pairs"]:
    pid=pair["pair_id"];left=pair["left"];right=pair["right"]
    check(left!=right and left in ii and right in ii,"pair.endpoints."+pid)
    selected=pair["compare_fields"];different=pair["must_change"]
    check(all(x in fields for x in selected+different),"pair.paths."+pid)
    check(not set(selected)&set(different),"pair.disjoint_paths."+pid)
    le=ee[left];re=ee[right]
    if pair["relation"] in ["INVARIANT","RENAMED_INVARIANT"]:
        check(set(selected)==set(fields) and not different,"pair.complete_invariant_fields."+pid)
    if pair["relation"]=="RENAMED_INVARIANT":
        maps=pair["renaming"]
        check(set(maps)=={"case_ids","obligation_ids","witness_ids"},"pair.renaming_namespaces."+pid)
        expected_sets={"case_ids":({left},{right}),"obligation_ids":({x["id"] for x in ii[left]["ledger"]["obligations"]},{x["id"] for x in ii[right]["ledger"]["obligations"]}),"witness_ids":({x["id"] for x in ii[left]["ledger"]["witnesses"]},{x["id"] for x in ii[right]["ledger"]["witnesses"]})}
        for ns,(domain,codomain) in expected_sets.items():
            check(set(maps[ns])==domain and set(maps[ns].values())==codomain and len(set(maps[ns].values()))==len(maps[ns]),"pair.complete_bijection."+pid+"."+ns)
        check(normalize_input(rename_input(ii[left],maps))==normalize_input(ii[right]),"pair.input_alpha_equivalence."+pid)
        le=rename_output(le,maps)
        check(le["case_id"]==re["case_id"],"pair.renamed_case_id."+pid)
    else:check(pair["renaming"]=={},"pair.empty_renaming."+pid)
    if pair["relation"]=="SENSITIVITY":
        check(bool(different),"pair.nonempty_sensitivity."+pid)
        check(set(selected+different)==set(fields),"pair.complete_sensitivity_partition."+pid)
    equals=[p for p in selected if at(le,p)!=at(re,p)]
    unchanged=[p for p in different if at(le,p)==at(re,p)]
    passed=not equals and not unchanged
    check(passed,"pair.expected_relation."+pid,"unexpected differences="+str(equals)+"; expected changes absent="+str(unchanged))
    pair_results.append(dict(pair_id=pid,relation=pair["relation"],passed=passed,unexpected_differences=equals,expected_changes_absent=unchanged))

check(author["expectation_provenance"]["evaluator"]=="agent_llm" and author["expectation_provenance"]["status"]=="needs-audit","author.expectation_provenance")
check(author["context_creation"]["fork_turns"]=="none","author.fresh_context_flag")
check(author["forbidden_exposure"]["reducer_calls"]==0 and author["forbidden_exposure"]["reducer_implementations"]==0,"author.no_reducer")
check(not author["forbidden_exposure"]["active_existing_content_reads_outside_allowlist"],"author.allowlist_reads_only")
ended=datetime.now(timezone.utc).isoformat()
receipt=dict(schema_version="qualifier-grounding-structural-checks/v2",set_id=controls["set_id"],started_at_utc=started,completed_at_utc=ended,status="PASS" if not failures else "FAIL",checks_run=len(checks),failures=failures,
             validation_engine="installed jsonschema.Draft202012Validator; reference/canonical/pair checks authored locally",
             counts=dict(inputs=len(inputs),expectations=len(expectations),controls=len(cc),pairs=len(pairs["pairs"]),deliberately_invalid_inputs=len(invalid_observations),pair_relations=dict(Counter(p["relation"] for p in pairs["pairs"])),expected_actions=dict(Counter(o["action"] for o in expectations))),
             check_scope=["exact interface input/output JSON schemas","encoding schemas for controls and pairs","input validity annotations including deliberate malformed controls","referential identity and surface/aperture constraints","canonical expected output arrays","output structural consistency without input-policy inference","complete expected invariant comparisons","complete bijections and renamed input/output comparisons","sensitivity equality/difference assertions","author provenance and stated aperture"],
             no_reducer_implemented=True,no_reducer_invoked=True,no_policy_to_decision_function=True,
             semantic_qualification="NOT_RUN",expectation_status="needs-audit",invalid_input_observations=invalid_observations,pair_results=pair_results,checks=checks)
author["checks"]=dict(receipt="checks.json",status=receipt["status"],checks_run=len(checks),semantic_qualification="NOT_RUN",pair_expected_relations_passed=sum(x["passed"] for x in pair_results),material_failures=failures)
author["last_structural_check_at_utc"]=ended
(ROOT/"AUTHOR.json").write_text(json.dumps(author,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
(ROOT/"checks.json").write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status=receipt["status"],checks_run=len(checks),counts=receipt["counts"],failures=failures),ensure_ascii=False))
raise SystemExit(0 if not failures else 1)
