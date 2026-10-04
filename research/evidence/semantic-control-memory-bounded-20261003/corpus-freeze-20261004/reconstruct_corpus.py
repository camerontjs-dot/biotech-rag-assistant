"""Read-only custody reconstruction and frozen materializer replay for PR #51.

This script never invokes a provider, adjudicator, reducer or project runtime. All
output is exclusive, outside the source checkout. It selects by completion/schema
status and call time, never semantic quality, and invokes the unchanged materializer.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

EXPECTED_HEAD = 'bf07ea3b16854830a9a2ec5a0c9725488bb02f17'
PACKAGE = Path('research/evidence/qualifier-grounding-semantic-assessor-controls-v1')
RUN = Path('research/evidence/semantic-adjudication-request-bound-v2')
SUCCESSOR = Path('research/evidence/semantic-control-memory-bounded-20261003')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def enc(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode('utf-8') + b'\n'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(enc(value))


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output or output.is_relative_to(source):
        raise ValueError('Output must be outside immutable source checkout')
    head = git(source, 'rev-parse', 'HEAD')
    if head != EXPECTED_HEAD:
        raise ValueError(f'Unexpected source head {head}')
    if git(source, 'status', '--porcelain', '--untracked-files=no'):
        raise ValueError('Source tracked tree is dirty')
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(source / 'research'))
    runner = importlib.import_module('run_semantic_request_once')
    frozen = importlib.import_module('check_semantic_assessor_preparation')
    builder = importlib.import_module('build_semantic_author_requests')
    if importlib.metadata.version('jsonschema') != '4.25.1':
        raise ValueError('jsonschema version drift')
    read = lambda path: runner.decoded(path.read_bytes())
    fixed_sources = [Path('research/build_semantic_author_requests.py'),
                     Path('research/check_semantic_assessor_preparation.py'),
                     Path('research/run_semantic_request_once.py')]
    source_receipt = {
        'source_head': head, 'source_tree': git(source, 'rev-parse', 'HEAD^{tree}'),
        'sources': {str(p): sha((source / p).read_bytes()) for p in fixed_sources},
        'python_version': sys.version, 'jsonschema_version': importlib.metadata.version('jsonschema'),
        'mechanical_harness_sha256': sha(Path(__file__).read_bytes()),
        'model_calls': 0, 'semantic_review': 'NOT_RUN', 'adjudication': 'NOT_RUN',
    }
    write(output / 'reconstruction-environment.json', source_receipt)
    freeze_rows = []
    for name in ('FREEZE.json', 'FREEZE-room-18432.json', 'FREEZE-author01-attempt-2.json'):
        freeze_path = source / SUCCESSOR / name
        freeze = read(freeze_path)
        runner.verify_freeze(source, freeze)
        freeze_rows.append({'path': str(SUCCESSOR / name), 'sha256': sha(freeze_path.read_bytes()),
                            'artifact_count': len(freeze['artifacts']), 'all_hashes_match': True})
    write(output / 'apparatus-freeze-check.json', freeze_rows)
    partition = read(source / RUN / 'author-partition.json')
    inventory = read(source / PACKAGE / 'case-design.json')
    expected_slots = partition['corpus_order']
    runner.require(len(expected_slots) == 44 and len(set(expected_slots)) == 44,
                   'Partition order is not 44 unique slots')
    runner.require(len(partition['partitions']) == 28, 'Not 28 frozen partitions')
    config_names = ('author-config.json', 'author-config-room-18432.json',
                    'author-config-author01-attempt-2.json')
    configs = {name: read(source / SUCCESSOR / name) for name in config_names}
    attempts = []
    missing_inventory = []
    for call in sorted((source / SUCCESSOR / 'calls').iterdir()):
        match = re.fullmatch(r'(author-\d\d)(?:-attempt-(\d+)|-budget)?', call.name)
        runner.require(match is not None and call.is_dir(), 'Unknown attempt directory')
        group = match.group(1)
        request_path = call / 'request.json'
        before = read(call / 'before-send.json')
        request = read(request_path)
        config_matches = [name for name, cfg in configs.items()
                          if cfg['options'] == request['options'] and cfg['model'] == request['model']]
        runner.require(len(config_matches) == 1, 'Ambiguous configuration mapping')
        config_name = config_matches[0]
        spec = read(source / RUN / 'requests' / f'{group}.spec.json')
        request_raw, prompt_raw = runner.build_request(spec, configs[config_name])
        runner.require(request_raw == request_path.read_bytes(), f'{call.name}: request reconstruction mismatch')
        runner.require(prompt_raw == (call / 'prompt.txt').read_bytes(), f'{call.name}: prompt mismatch')
        runner.require(sha(request_raw) == before['request_sha256'] and sha(prompt_raw) == before['prompt_sha256'],
                       f'{call.name}: before-send hash mismatch')
        sent = read(call / 'send-started.json')
        runner.require(sent['request_sha256'] == sha(request_raw) and sent['generation_attempts'] == 1,
                       f'{call.name}: send marker mismatch')
        files = {p.name: sha(p.read_bytes()) for p in sorted(call.iterdir()) if p.is_file()}
        receipt_path = call / 'receipt.json'
        receipt = read(receipt_path) if receipt_path.exists() else None
        status = 'INTERRUPTED_BEFORE_RESPONSE' if receipt is None else receipt['status']
        row = {'partition': group, 'directory': call.name, 'path': str(call.relative_to(source)),
               'started_at_utc': before['started_at_utc'], 'send_started_at_utc': sent['at_utc'],
               'status': status, 'files': files, 'config_path': str(SUCCESSOR / config_name),
               'config_sha256': sha((source / SUCCESSOR / config_name).read_bytes()),
               'spec_path': str(RUN / 'requests' / f'{group}.spec.json'),
               'spec_sha256': sha((source / RUN / 'requests' / f'{group}.spec.json').read_bytes()),
               'request_reconstructed_byte_identical': True, 'complete_schema_valid': False,
               'runtime_identity': {key: before[key] for key in
                                    ('model', 'model_digest', 'provider_version', 'parameters',
                                     'tools', 'session_reuse', 'aperture', 'hidden_provider_context')}}
        if receipt is None:
            runner.require(call.name == 'author-20', 'Unexpected absent receipt')
            runner.require(not (call / 'provider-response.raw.json').exists(), 'Unreceipted response exists')
            row['response_sha256'] = None
            row['response_absence'] = 'No bytes preserved; NOT the SHA-256 of an empty response'
        else:
            fields = {'request_sha256': 'request.json', 'prompt_sha256': 'prompt.txt',
                      'provider_discovery_sha256': 'provider-discovery.raw.json',
                      'raw_response_sha256': 'provider-response.raw.json',
                      'parsed_output_sha256': 'parsed-output.json'}
            for key, name in fields.items():
                digest = receipt.get(key)
                if digest is not None:
                    runner.require(files.get(name) == digest, f'{call.name}: {key} mismatch')
            discovery = read(call / 'provider-discovery.raw.json')
            runner.require(discovery['version'] == receipt['provider_version'], 'Provider version mismatch')
            row['models_discovery_sha256'] = receipt.get('models_discovery_sha256')
            if (call / 'models-discovery.raw.json').exists():
                runner.require(files['models-discovery.raw.json'] == receipt['models_discovery_sha256'],
                               'Models discovery hash mismatch')
                row['model_inventory_verification'] = 'VERIFIED'
            else:
                row['model_inventory_verification'] = 'HASH_ONLY_INTENTIONALLY_UNPUBLISHED'
                missing_inventory.append({'directory': call.name,
                                          'sha256': receipt.get('models_discovery_sha256')})
            raw = read(call / 'provider-response.raw.json')
            row.update(done=raw.get('done'), done_reason=raw.get('done_reason'),
                       eval_count=raw.get('eval_count'), prompt_eval_count=raw.get('prompt_eval_count'),
                       response_sha256=receipt['raw_response_sha256'])
            if status == 'PASS_REQUEST_PATH_ONLY':
                runner.require(raw.get('done') is True and raw.get('done_reason') == 'stop',
                               'Passing response did not stop naturally')
                runner.require(raw['model'] == before['model'], 'Response model mismatch')
                runner.require(raw['response'].encode() == (call / 'response-text.txt').read_bytes(),
                               'Response text reconstruction mismatch')
                parsed = runner.decoded(raw['response'])
                runner.require(runner.encoded(parsed) + b'\n' == (call / 'parsed-output.json').read_bytes(),
                               'Parsed output reconstruction mismatch')
                runner.check_schema(spec['output_schema']).validate(parsed)
                row['complete_schema_valid'] = True
                row['response_reconstructed_byte_identical'] = True
            else:
                runner.require(raw.get('done_reason') == 'length', 'Unexpected preserved failure')
        attempts.append(row)
    write(output / 'attempt-custody.json', {'attempts': attempts, 'absent_private_inventory': missing_inventory,
          'private_inventory_limitation': 'Raw local model listings intentionally unpublished in PR #38/51 lineage; '
             'hash-only selected-model discovery is not independently reconstructed from inventory bytes.'})
    policy = {
        'schema_version': 'semantic-control-canonical-attempt-policy/v1',
        'source_head': head, 'selection_basis': 'Earliest completed schema-valid response by recorded start time '
        'within each frozen partition in the PR #51 successor; only prospectively recorded capacity/runtime '
        'corrections may precede a later complete response. Never compare semantic quality or re-author.',
        'failed_attempts': 'Preserve all requests, returned raw bytes, receipts and explicit no-response states.',
        'author03_budget': 'The sole first complete author-03 response; acknowledged in SCHEDULE.json, '
        'ONE-SLOT-REQUEST-PATH.json and AUTHOR-REQUEST-PATH.json. Initial semantic_use NONE remains no '
        'semantic acceptance; current user Part 3 authorizes mechanical corpus freeze.',
        'semantic_acceptance': False, 'adjudication': 'NOT_RUN',
    }
    write(output / 'canonical-attempt-policy.json', policy)
    selections = []
    for group in partition['partitions']:
        group_attempts = sorted([a for a in attempts if a['partition'] == group['id']],
                                key=lambda a: datetime.fromisoformat(a['started_at_utc']))
        complete = [a for a in group_attempts if a['complete_schema_valid']]
        runner.require(len(complete) == 1, f'{group["id"]}: expected one complete response')
        chosen = complete[0]
        runner.require(all(not a['complete_schema_valid'] for a in group_attempts if a != chosen),
                       'Unaccounted complete response')
        selections.append({'partition': group['id'], 'slots': group['slots'],
                           'relation_slots': group['relation_slots'], 'canonical_directory': chosen['directory'],
                           'canonical_path': chosen['path'], 'canonical_request_sha256': chosen['files']['request.json'],
                           'canonical_raw_response_sha256': chosen['files']['provider-response.raw.json'],
                           'canonical_parsed_output_sha256': chosen['files']['parsed-output.json'],
                           'all_attempt_directories': [a['directory'] for a in group_attempts],
                           'configuration': chosen['config_path']})
    write(output / 'canonical-attempt-map.json', {'policy_sha256': sha((output / 'canonical-attempt-policy.json').read_bytes()),
                                                'partitions': selections})
    observed = []
    for selection in selections:
        parsed = read(source / selection['canonical_path'] / 'parsed-output.json')
        observed.extend(c['slot'] for c in parsed['cases'])
    counts = Counter(observed)
    missing = sorted(set(expected_slots) - set(observed))
    duplicate = {slot: count for slot, count in sorted(counts.items()) if count != 1}
    unexpected = sorted(set(observed) - set(expected_slots))
    proof = {'planned_partitions': 28, 'planned_slots': 44, 'observed_slots': len(observed),
             'missing': missing, 'duplicates': duplicate, 'unexpected': unexpected,
             'all_44_planned_slots_exactly_once': not missing and not duplicate and not unexpected and len(observed) == 44,
             'partition_manifest': selections, 'frozen_order': expected_slots}
    write(output / 'slot-proof.json', proof)
    # A failed slot proof forbids corpus assembly; replay per-partition materialization
    # diagnostically to preserve the frozen builder's own failures without any repairs.
    # Exact copies supply only the filesystem locations the unchanged frozen builder expects.
    stage = output / 'sealed-materializer-staging'
    shutil.copytree(source / PACKAGE, stage / PACKAGE)
    (stage / RUN).mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / RUN / 'author-partition.json', stage / RUN / 'author-partition.json')
    shutil.copytree(source / RUN / 'requests', stage / RUN / 'requests')
    for selected in selections:
        dst = stage / RUN / 'calls' / selected['partition'] / 'parsed-output.json'
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / selected['canonical_path'] / 'parsed-output.json', dst)
    materialization = []
    for group in partition['partitions']:
        try:
            result = builder.materialize(stage, group['id'])
            path = stage / RUN / 'author-materialized' / f'{group["id"]}.json'
            materialization.append({'partition': group['id'], 'status': 'PASS_STRUCTURE_ONLY',
                                    'cases': len(result['cases']), 'sha256': sha(path.read_bytes())})
        except Exception as error:
            materialization.append({'partition': group['id'], 'status': 'STRUCTURAL_INVALID',
                                    'error_type': type(error).__name__, 'error': str(error)})
    write(output / 'materialization-check.json', materialization)
    failures = [row for row in materialization if row['status'] != 'PASS_STRUCTURE_ONLY']
    artifact_hashes = None
    assembly_error = None
    if not failures and proof['all_44_planned_slots_exactly_once']:
        try:
            artifact_hashes = builder.assemble(stage)
            (output / 'input-only').mkdir()
            (output / 'sealed').mkdir()
            shutil.copy2(stage / RUN / 'cases.jsonl', output / 'input-only/cases.jsonl')
            for name in ('design.json', 'relations.json'):
                shutil.copy2(stage / RUN / name, output / 'sealed' / name)
        except Exception as error:
            assembly_error = {'error_type': type(error).__name__, 'error': str(error)}
    receipt = {**source_receipt,
        'status': 'CORPUS_STRUCTURE_FROZEN_WITH_DISCOVERY_HASH_ONLY' if artifact_hashes else 'AUTHOR_CORPUS_NOT_READY',
        'canonical_partition_count': len(selections), 'authored_row_count': len(observed),
        'unique_planned_slots_present': len(set(observed) & set(expected_slots)),
        'slot_completeness_passed': proof['all_44_planned_slots_exactly_once'],
        'missing_slots': missing, 'duplicate_slots': duplicate,
        'materialized_partition_count': len(materialization) - len(failures),
        'materialization_failures': failures, 'assembly_error': assembly_error,
        'artifact_hashes': artifact_hashes,
        'selected_model_inventory': 'HASH_ONLY_INTENTIONALLY_UNPUBLISHED',
        'provider_hidden_context': 'UNKNOWN', 'semantic_acceptance': False,
        'author_design_revealed_to_adjudicator': False, 'adjudication': 'NOT_RUN',
        'model_calls': 0, 'reducer_calls': 0,
        'receipt_artifacts': {p.name: sha(p.read_bytes()) for p in output.glob('*.json')},
    }
    write(output / 'corpus-freeze-attempt-receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'canonical_partitions': len(selections),
                      'authored_rows': len(observed), 'unique_slots': len(set(observed)), 'materialized_partitions': receipt['materialized_partition_count'],
                      'materialization_failures': failures, 'assembly_error': assembly_error,
                      'artifact_hashes': artifact_hashes}, indent=2))


if __name__ == '__main__':
    main()
