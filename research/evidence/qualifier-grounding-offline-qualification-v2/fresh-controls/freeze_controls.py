"""Seal all authored artifacts after passing structural checks."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parent
author=json.loads((ROOT/"AUTHOR.json").read_text(encoding="utf-8"))
checks=json.loads((ROOT/"checks.json").read_text(encoding="utf-8"))
if checks["status"]!="PASS":raise SystemExit("Structural checks did not pass; freeze refused.")
if author["forbidden_exposure"]["contamination_status"]!="CLEAR_RESTRICTED_APERTURE":raise SystemExit("Contamination boundary not clear; freeze refused.")
names=["inputs.jsonl","expectations.jsonl","controls.json","pairs.json","AUTHOR.json","build_controls.py","check_controls.py","checks.json","freeze_controls.py"]
unexpected=sorted(p.name for p in ROOT.iterdir() if p.name not in names+["freeze.json"])
if unexpected:raise SystemExit("Unsealed drafting artifacts exist: "+repr(unexpected))
files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
freeze=dict(schema_version="qualifier-grounding-freeze/v2",set_id=author["set_id"],freeze_at=datetime.now(timezone.utc).isoformat(),files=files,
            contamination_status=author["forbidden_exposure"]["contamination_status"],author_identity=author["author_identity"],
            normative_identity=author["normative_identity"],checks_status=checks["status"],expectation_provenance=author["expectation_provenance"],
            unsealed_drafting_artifacts=[],self_hash_excluded=True)
(ROOT/"freeze.json").write_text(json.dumps(freeze,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(freeze,ensure_ascii=False,sort_keys=True))
