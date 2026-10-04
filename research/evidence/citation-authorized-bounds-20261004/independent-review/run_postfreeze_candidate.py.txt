from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/scratch/7b8946fc1488/biotech-citation')
expected='093fcd031138b8219722f4e9c888dec2d7ebc354'
commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
assert commit==expected,commit
source=ROOT/'src/biotech_rag_assistant/citation_spans.py'
spec=importlib.util.spec_from_file_location('reviewed_citation_spans',source)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
probe_path=HERE/'postfreeze_probes.json'
raw=probe_path.read_bytes()
data=json.loads(raw)
results=[]
for c in data['cases']:
    actual=module.select_enclosing_sentence(c['body'],c['quote']).model_dump()
    results.append({**c,'actual':actual})
report={'commit':commit,'probe_sha256':hashlib.sha256(raw).hexdigest(),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'phase':data['phase'],'results':results}
(HERE/'postfreeze_candidate_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(HERE/'postfreeze_probes.sha256').write_text(report['probe_sha256']+'  postfreeze_probes.json\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
