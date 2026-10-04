#!/usr/bin/env python3
"""Portable reproduction of two distinct citation-review contracts.

Usage:
  python reproduce_review.py --probe-set authorized --checkout PATH --output PATH

Loads only the reviewed module from the checkout. Requires Python >=3.11 and the
project's Pydantic dependency. No package startup, providers, API or CLI runs.
Frozen fixture hashes, tree identity and source/document hashes are enforced.
Exit 1 means at least one raw frozen expectation mismatched; the authorized set
intentionally retains two documented refusal-name overconstraints (49/51 raw).
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

SUBJECTS = {
    'automatic': {
        'tree':'d7a96fe4bae53f30dbdcf1f179b3710bd1a5b5cf',
        'source_sha256':'386749546e2cafaf237e69936dae894982b6d9592d0efc0594a2f8d83a2c4df5',
        'contract_sha256':'8477fbc9c883c1b07502da0ec0fa16c4edb0be663dbd361c3b3ad4d9f4775adc',
        'reviewed_local_commit':'093fcd031138b8219722f4e9c888dec2d7ebc354',
        'published_commit':'8ddd2a8969869be5e5dfe339b45087f1ee7e8803',
    },
    'authorized': {
        'tree':'4ff09a40a38c41a20d64d436ff67463750a254cd',
        'source_sha256':'e3c1198b900aa075edd2bf04575783419dc0de87d63ab2e640ed6309a5ae94d1',
        'contract_sha256':'50bb6d702abc65583e339d1c05e9b97c583849d752863ddd7c2a790c9399c29e',
        'reviewed_local_commit':'786a09421c95c55506a3e82f96006449e064b4d7',
        'published_commit':'897e22827fe9848d460734f1b2432c6f6babc45d',
    },
}
PROBES = {
    'automatic': ('preimplementation_probes.json',
                  '3666cec6252e3e3d074d49667cdc0f608c1bb8a5b907d39aa1db70de537fb101'),
    'automatic-extra': ('postfreeze_probes.json',
                        'f11f7de4bb738700d4b0e3729f02ede50c5a89492c09e72e65811ce772e3074b'),
    'authorized': ('explicit_bounds_preimplementation_probes.json',
                   '22460e1fe41a0b0a3875d15e56552ee473e1ad36ae80e771c51333699e4f8659'),
}
REFUSALS = {
    'automatic': {'not_found','ambiguous','boundary_uncertain'},
    'authorized': {'not_found','ambiguous','bounds_required','invalid_bounds'},
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(['git','-C',str(checkout),*args],text=True).strip()


def expected_for(case: dict, probe_set: str) -> tuple[set[str], dict | None]:
    if probe_set == 'authorized':
        expected = case['expected']
        return set(expected['outcomes']), (
            {k:expected[k] for k in ('text','start','end')}
            if 'text' in expected else None
        )
    if probe_set == 'automatic-extra':
        key, body = case['id'], case['body']
        if key == 'prof_sentence_start_loss':
            text = 'Prof. Vale must approve release.'
        elif key in {'root_paragraph_merge','crlf_blank_paragraph_merge',
                     'unicode_paragraph_separator_merge'}:
            text = 'Release is permitted'
        else:
            text = body
        start = body.index(text)
        return {'selected',*REFUSALS['automatic']}, {
            'text':text,'start':start,'end':start+len(text)
        }
    mode = case['expected_outcome']
    allowed = ({'selected'} if mode == 'exact' else
               REFUSALS['automatic'] if mode == 'refuse' else
               {'selected',*REFUSALS['automatic']})
    return set(allowed), case.get('expected_sentence')


def evaluate(case: dict, actual: dict, probe_set: str, contract: str) -> dict:
    failures = []
    allowed, expected_span = expected_for(case, probe_set)
    outcome = actual.get('outcome')
    if set(actual) != {'outcome','text','start','end'}:
        failures.append('output fields differ from declared contract')
    if outcome not in allowed:
        failures.append('outcome differs from frozen expected outcome names')
    span_ok = False
    valid_refusal = False
    if outcome == 'selected':
        start,end,text = actual.get('start'),actual.get('end'),actual.get('text')
        if type(start) is not int or type(end) is not int:
            failures.append('offsets are not plain integer codepoints')
        elif not 0 <= start < end <= len(case['body']):
            failures.append('offsets are outside the supplied body')
        elif case['body'][start:end] != text:
            failures.append('text does not equal the exact source slice')
        if not isinstance(text,str) or case['quote'] not in text:
            failures.append('exact quote is not contained in selected text')
        if expected_span is None or any(actual.get(k)!=v for k,v in expected_span.items()):
            failures.append('selected span differs from the complete expected exact span')
        if contract == 'authorized' and (start,end) != (
            case['kwargs'].get('authorized_start'),case['kwargs'].get('authorized_end')
        ):
            failures.append('selected offsets differ from caller-supplied bounds')
        span_ok = not failures
    elif outcome in REFUSALS[contract]:
        valid_refusal = all(actual.get(k) is None for k in ('text','start','end'))
        if not valid_refusal:
            failures.append('refusal contains non-null text or offsets')
    else:
        failures.append('unknown outcome or unexpected exception')
    result = {'id':case['id'],'pass':not failures,
              'expected_outcomes':sorted(allowed),'actual':actual,'failures':failures}
    if contract == 'authorized':
        required_selected = allowed == {'selected'}
        result['required_behavior'] = 'exact_selection' if required_selected else 'refusal'
        result['required_behavior_observed'] = span_ok if required_selected else valid_refusal
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-set',required=True,choices=tuple(PROBES))
    parser.add_argument('--checkout',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--probe-directory',type=Path,default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    contract = 'authorized' if args.probe_set == 'authorized' else 'automatic'
    subject = SUBJECTS[contract]
    checkout = args.checkout.resolve()
    commit,tree = git(checkout,'rev-parse','HEAD'),git(checkout,'rev-parse','HEAD^{tree}')
    if tree != subject['tree']:
        raise RuntimeError(f'Unexpected source tree: {tree}')
    if git(checkout,'status','--porcelain','--untracked-files=no'):
        raise RuntimeError('Tracked checkout files differ from the declared source tree')
    source = checkout/'src/biotech_rag_assistant/citation_spans.py'
    document = checkout/'docs/citation-span-selection.md'
    if sha256(source.read_bytes()) != subject['source_sha256']:
        raise RuntimeError('Reviewed implementation bytes differ')
    if sha256(document.read_bytes()) != subject['contract_sha256']:
        raise RuntimeError('Reviewed contract bytes differ')
    filename,probe_hash = PROBES[args.probe_set]
    probe_path = args.probe_directory/filename
    raw = probe_path.read_bytes()
    if sha256(raw) != probe_hash:
        raise RuntimeError('Frozen probe source differs')
    spec = importlib.util.spec_from_file_location('portable_reviewed_citation_spans',source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    select = (module.select_authorized_span if contract == 'authorized'
              else module.select_enclosing_sentence)
    results = []
    for case in json.loads(raw)['cases']:
        try:
            actual = select(case['body'],case['quote'],**case.get('kwargs',{})).model_dump()
        except Exception as exc:
            actual = {'exception':f'{type(exc).__name__}: {exc}'}
        results.append(evaluate(case,actual,args.probe_set,contract))
    report = {'probe_set':args.probe_set,'commit':commit,'tree':tree,
              'subject_identity':subject,'probe_sha256':probe_hash,
              'python':sys.version,'command':sys.argv,
              'total':len(results),'passed':sum(r['pass'] for r in results),
              'failed':sum(not r['pass'] for r in results),'results':results}
    if contract == 'authorized':
        report['required_exact_selections_observed'] = sum(
            r['required_behavior']=='exact_selection' and r['required_behavior_observed'] for r in results
        )
        report['required_refusals_observed'] = sum(
            r['required_behavior']=='refusal' and r['required_behavior_observed'] for r in results
        )
        report['adjudication'] = (
            'The frozen missing_start_bound and missing_end_bound probes expected '
            'bounds_required before the docs were read. The documented contract '
            'classifies incomplete bounds as invalid_bounds. Both are safe refusals; '
            'raw expectations are preserved, not edited or relabeled as passing.'
        )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'results','subject_identity','command','python'}},indent=2))
    return int(bool(report['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
