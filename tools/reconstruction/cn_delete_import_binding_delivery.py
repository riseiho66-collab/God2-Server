"""Seal pinned CN declared IAT bindings and bounded call-reference navigation.

Static PE/source reads only. No native execution, builds, tests, DB or network.
The previous character-mutation artifact remains immutable, including its
incorrect file-thunk-as-VA interpretation, now explicitly superseded.
"""
import csv
import hashlib
import json
import re
from pathlib import Path
import pefile
from .cn_wrapper_route_frontier import CN, ROOT, PIN, RECOVERY
from .cn_pe_import_directory import import_directory, FileView


def main():
    root = ROOT/'artifacts/integration/packet-connections-20261006'
    out = root/'cn-delete-import-binding-01'
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require new before snapshot; preserve sealed prior delivery')
    image = CN.parent/'XJZ-CN/God2_opt.exe'
    raw = image.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise RuntimeError('Pinned CN image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    parsed = import_directory(pe, raw)
    view = FileView(pe, raw)
    bindings = {}
    for row in parsed['bindings']:
        bindings.setdefault(row['iat_va'], []).append(row)
    selected = bindings.get('00aaf25c', [])
    if len(selected) != 1:
        raise RuntimeError('Primary descriptor lacks unique target declaration')
    binding = selected[0]
    descriptor = parsed['descriptors'][binding['descriptor_index']]
    files = []

    def save(rel, data, original=None):
        p = out/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        files.append({'path': rel, 'original': original, 'bytes': len(data),
                      'sha256': hashlib.sha256(data).hexdigest()})

    def dump(rel, obj):
        save(rel, (json.dumps(obj, indent=2)+'\n').encode())

    dump('declared-import-directory.json', parsed)
    save('native/descriptor883.bin', view.read(int(descriptor['descriptor_rva'], 16), 20))
    save('native/lookup-rva006af254.bin', view.read(0x6af254, 8))
    save('native/iat-rva006af25c.bin', view.read(0x6af25c, 8))
    save('native/dll-name-rva006af238.bin', view.read(0x6af238, len(binding['dll'])+1))
    save('native/import-name-rva006af246.bin', view.read(0x6af246, 2+len(binding['name'])+1))
    save('native/delete-call-and-following.bin', view.read(0x47eb51-0x400000, 0x47eb70-0x47eb51))
    prior = root/'cn-character-mutation-contract-01'
    previous_manifest = json.loads((prior/'native-manifest.json').read_text())
    calls = []
    for function in previous_manifest['functions']:
        stem = function['entry']
        asm = prior/'native'/(stem+'.asm')
        save('bounded-primary/'+stem+'.asm', asm.read_bytes(), str(asm))
        # Addresses below remain metadata-linear candidates. ExactFF15 bytes
        # identify an import declaration, not reachability/phase/game semantics.
        for line in asm.read_text().splitlines():
            match = re.match(r'^([0-9a-f]{8})\s+(ff15[0-9a-f]{8})\s+call\s', line)
            if not match:
                continue
            slot = int.from_bytes(bytes.fromhex(match[2])[2:], 'little')
            calls.append({'function': stem, 'site': match[1], 'bytes': match[2],
                          'iat_va': f'{slot:08x}', 'declared_bindings': bindings.get(f'{slot:08x}', []),
                          'reachability_and_state_proven_by_this_index': False,
                          'loaded_binding_observed': False})
    dump('bounded-iat-call-reference-index.json', calls)
    # Preserve existing upstream declaration evidence; it is corroboration,
    # not a new native discovery or a program executed in this task.
    imports = RECOVERY.parent/'reports/imports.tsv'
    with imports.open(encoding='utf-8-sig') as f:
        retained = [r for r in csv.DictReader(f, delimiter='\t') if r['iat_va'].lower() == '00aaf25c']
    dump('retained-import-record.json', {'original': str(imports),
        'source_sha256': hashlib.sha256(imports.read_bytes()).hexdigest(), 'rows': retained})
    save('reference-inputs/prior-boundary.json', (prior/'delete-indirect-call-boundary.json').read_bytes())
    save('reference-inputs/prior-findings.json', (prior/'findings.json').read_bytes())
    for rel in ['tools/reconstruction/cn_pe_import_directory.py',
                'tools/reconstruction/cn_delete_import_binding_delivery.py',
                'tools/reconstruction/cn_character_mutation_contract_delivery.py',
                'src/cn/protocol/CnCharacterDeleteReply.h']:
        save('source/'+rel, (ROOT/rel).read_bytes(), str(ROOT/rel))
    findings = {'round': '20261007-cn-delete-import-binding',
        'native_sha256': PIN, 'declared_descriptor_count': parsed['descriptor_count'],
        'declared_binding_count': parsed['binding_count'], 'target_descriptor': descriptor,
        'target_binding': binding, 'bounded_primary_functions': len(previous_manifest['functions']),
        'bounded_ff15_call_references': len(calls),
        'bounded_references_with_declared_binding': sum(bool(c['declared_bindings']) for c in calls),
        'corrects_prior': 'cn-character-mutation-contract-01/delete-indirect-call-boundary.json',
        'correction': '006AF246 is a file IMAGE_IMPORT_BY_NAME RVA, not loaded callable VA; descriptor883 declares kernel32.dll!DeleteFileA. Partial general parser result did not prove absence.',
        'previous_goal_turn_classification': 'progress: four main-server read-only protocol views and qualified control8 CFG were saved; its import interpretation requires this additive correction',
        'gameplay_source_handlers_added': 0, 'new_complete_bidirectional_routes': 0,
        'new_packet_values': 0, 'loaded_binding_observed': False,
        'complete_delete_wrapper_outcome_proven': False,
        'remaining': ['0047EB5E..62 instruction/exception boundary and full0047E960 wrapper result remain unresolved.',
                      'Imported API identity is not native gameplay semantics or authority; current loaded resolution not observed.',
                      'Native character mutations still lack real common storage/rules/permissions/native reply suppliers and hosting.',
                      'Whole-game indirect/deferred/state/variant denominator remains open.'],
        'whole_game_completion_percent': None, 'build_run': False, 'tests_run': False,
        'runtime_run': False, 'deployed': False, 'database_access': False}
    dump('findings.json', findings)
    dump('native-source-manifest.json', {'files': files, 'native_sha256': PIN,
        'build_run': False, 'tests_run': False, 'runtime_run': False, 'deployed': False})
    print(json.dumps({k: findings[k] for k in ['round', 'declared_descriptor_count',
        'declared_binding_count', 'bounded_ff15_call_references', 'bounded_references_with_declared_binding',
        'new_complete_bidirectional_routes']}))


if __name__ == '__main__':
    main()
