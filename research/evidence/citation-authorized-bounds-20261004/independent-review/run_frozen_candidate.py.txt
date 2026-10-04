"""Adapter for frozen candidate 093fcd0; no provider clients or source rewrites."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/scratch/7b8946fc1488/biotech-citation')
EXPECTED_COMMIT='093fcd031138b8219722f4e9c888dec2d7ebc354'
EXPECTED_TREE='d7a96fe4bae53f30dbdcf1f179b3710bd1a5b5cf'
EXPECTED_PROBES='3666cec6252e3e3d074d49667cdc0f608c1bb8a5b907d39aa1db70de537fb101'
commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
tree=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD^{tree}'],text=True).strip()
assert (commit,tree)==(EXPECTED_COMMIT,EXPECTED_TREE),(commit,tree)
probe_path=HERE/'preimplementation_probes.json'
assert hashlib.sha256(probe_path.read_bytes()).hexdigest()==EXPECTED_PROBES
source=ROOT/'src/biotech_rag_assistant/citation_spans.py'
spec=importlib.util.spec_from_file_location('reviewed_citation_spans',source)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
results=[]
for p in json.loads(probe_path.read_text())['cases']:
    try:
        result=module.select_enclosing_sentence(p['body'],p['quote']).model_dump()
        if result['outcome']=='selected':
            outcome={'id':p['id'],'status':'success','text':result['text'],'start':result['start'],'end':result['end'],'raw':result}
        elif result['outcome'] in {'not_found','ambiguous','boundary_uncertain'} and all(result[k] is None for k in ('text','start','end')):
            outcome={'id':p['id'],'status':'refused','reason':result['outcome'],'raw':result}
        else:
            outcome={'id':p['id'],'status':'error','reason':'malformed refusal or unknown outcome','raw':result}
    except Exception as exc:
        outcome={'id':p['id'],'status':'error','reason':f'{type(exc).__name__}: {exc}'}
    results.append(outcome)
metadata={'commit':commit,'tree':tree,'probe_sha256':EXPECTED_PROBES,
          'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'contract_sha256':hashlib.sha256((ROOT/'docs/citation-span-selection.md').read_bytes()).hexdigest(),
          'python':sys.executable,'outcomes':results}
(HERE/'frozen_candidate_outcomes.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
from score_probes import evaluate
report=evaluate(probe_path,HERE/'frozen_candidate_outcomes.json')
(HERE/'frozen_candidate_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'commit':commit,'tree':tree,'probe_sha256':EXPECTED_PROBES,'total':report['total'],'passed':report['passed'],'failed':report['failed'],'failures':[r for r in report['results'] if not r['pass']]},ensure_ascii=False,indent=2))
