"""Run a fresh frozen probe set for the distinct explicit-bounds API."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/scratch/7b8946fc1488/biotech-citation')
EXPECTED_COMMIT='786a09421c95c55506a3e82f96006449e064b4d7'
EXPECTED_TREE='4ff09a40a38c41a20d64d436ff67463750a254cd'
EXPECTED_PROBES='22460e1fe41a0b0a3875d15e56552ee473e1ad36ae80e771c51333699e4f8659'
commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
tree=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD^{tree}'],text=True).strip()
assert (commit,tree)==(EXPECTED_COMMIT,EXPECTED_TREE),(commit,tree)
probe_path=HERE/'explicit_bounds_preimplementation_probes.json'
raw=probe_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()==EXPECTED_PROBES
source=ROOT/'src/biotech_rag_assistant/citation_spans.py'
spec=importlib.util.spec_from_file_location('reviewed_explicit_citation_spans',source)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
results=[]
for p in json.loads(raw)['cases']:
    failures=[]
    try:
        actual=module.select_authorized_span(p['body'],p['quote'],**p['kwargs']).model_dump()
        if set(actual)!={'outcome','text','start','end'}:
            failures.append('output fields differ from declared contract')
        if actual['outcome'] not in p['expected']['outcomes']:
            failures.append('outcome differs from frozen expected outcome names')
        if actual['outcome']=='selected':
            start,end,text=actual['start'],actual['end'],actual['text']
            if type(start) is not int or type(end) is not int:
                failures.append('selected offsets are not plain integer codepoints')
            elif not 0 <= start < end <= len(p['body']):
                failures.append('selected offsets outside authorized body')
            elif p['body'][start:end]!=text:
                failures.append('selected text does not equal exact body slice')
            if not isinstance(text,str) or p['quote'] not in text:
                failures.append('selected text does not contain exact quote')
            if (start,end)!=(p['kwargs'].get('authorized_start'),p['kwargs'].get('authorized_end')):
                failures.append('selected bounds differ from caller-supplied bounds')
            for key in ('text','start','end'):
                if key not in p['expected'] or actual[key]!=p['expected'][key]:
                    failures.append(f'selected {key} differs from exact expected span')
        elif any(actual.get(k) is not None for k in ('text','start','end')):
            failures.append('refusal contains non-null text or offsets')
    except Exception as exc:
        actual={'exception':f'{type(exc).__name__}: {exc}'}
        failures.append('unexpected exception is not safe refusal')
    results.append({'id':p['id'],'pass':not failures,'expected':p['expected'],
                    'actual':actual,'failures':failures})
report={'commit':commit,'tree':tree,'probe_sha256':EXPECTED_PROBES,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'contract_sha256':hashlib.sha256((ROOT/'docs/citation-span-selection.md').read_bytes()).hexdigest(),
        'python':sys.executable,'total':len(results),
        'passed':sum(r['pass'] for r in results),'failed':sum(not r['pass'] for r in results),
        'results':results}
(HERE/'explicit_bounds_candidate_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
print(json.dumps({'failures':[r for r in results if not r['pass']]},ensure_ascii=False,indent=2))
