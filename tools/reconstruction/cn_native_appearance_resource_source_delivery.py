"""File-only primary CN appearance table readers and row/path source delivery."""
import csv
import hashlib
import json
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT, PIN
from tools.strike_lab.omega_assets import decode_csvz

NAME = 'cn-native-appearance-resource-source-01'
ROUND = '20261007-cn-native-appearance-resource-source'
SOURCES = (
    'src/cn/assets/CnAppearanceResources.h', 'src/cn/assets/CnAppearanceResources.cpp',
    'src/cn/assets/CnSceneAssets.h', 'src/cn/assets/CnSceneAssets.cpp',
    'tools/reconstruction/cn_native_appearance_resource_source_delivery.py',
    'docs/research/cn-native-appearance-resource-source-20261007.md',
)
FUNCTIONS = (
    '00423960', '004237f0', '00423920', '00423950', '00423cb0', '00423ed0', '00423c80',
    '00488da0', '00488c30', '004882e0', '00488480', '00487f70', '00487e20', '00488080',
    '004885b0', '00488f70', '00488b70', '00423140', '004231b0', '00423270', '004232d0',
    '00423350', '00423390', '00423480', '004234f0', '00482c90',
)
LITERALS = (
    ('head-family-table-and-adjacent-byte', 0x7ede9c, 16),
    ('face-family-table-and-adjacent-byte', 0x7edeac, 4),
    ('slot-letters-and-padding', 0x886130, 8),
    ('key-formatter', 0x7edf48, 12), ('csv-integer-format', 0x7ed65c, 4),
    ('hero-rom-prefix', 0x7ef9a0, 21), ('driver-rom-prefix', 0x7f1be8, 16),
    ('auxiliary-loader-path', 0x7f1bf8, 26), ('auxiliary-other-prefix', 0x7f1c60, 16),
    ('auxiliary-field3-divisor', 0x7f1cec, 4),
)
REMAINING = [
    'Current DrvDoll.csvZ exceeds native declared decoded length in bounded file decoding; auxiliary table/selected resource and alternate-key validity/fallback remain unqualified.',
    'Actual original004197E0 ROM/ACT/cache/counter/bank/current-context/palette/later lifecycle input and issuer profile/revision/world binding remain missing; path/CSV rows are not loaded resources.',
    'Authoritative common equipment-to-input, full native6F unknown fields/issuer/observer policies and configured Application/native/WS providers/hosting remain incomplete.',
    'TW-origin/CN/CF/alternate/later appearance, semantic replay/recovery, all gameplay/numeric source chains and exhaustive direction/phase/state/variant/indirect/deferred denominator remain open; levels unchanged.',
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    base = ROOT / 'artifacts/integration/packet-connections-20261006'
    out = base / NAME
    if not (out / 'before-manifest.json').exists() or (out / 'findings.json').exists():
        raise RuntimeError('Fresh before receipt required')
    def save(rel, data):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    def dump(rel, value):
        save(rel, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    preserved = []
    for row in json.loads((out / 'before-manifest.json').read_text(encoding='utf-8')):
        old = (out / row['snapshot']).read_bytes()
        if sha(old) != row['sha256']:
            raise RuntimeError('Before bytes differ')
        if row['path'] not in SOURCES and row['path'] not in (
            'docs/PACKET_CONNECTION_GOAL_20261006.md',
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json',
        ):
            if old != (ROOT / row['path']).read_bytes():
                raise RuntimeError('Frozen context changed: ' + row['path'])
            preserved.append(row)
    primary = Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
    raw = primary.read_bytes()
    if sha(raw) != PIN:
        raise RuntimeError('CN primary pin differs')
    pe = pefile.PE(data=raw, fast_load=True)
    view = FileView(pe, raw)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    recovery = Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    metadata = (recovery / 'functions.tsv').read_bytes()
    rows = {r['address']: r for r in csv.DictReader(metadata.decode('utf-8').splitlines(), delimiter='\t')}
    envelopes = []
    for address in FUNCTIONS:
        row = rows[address]
        size = int(row['bytes'])
        path = (recovery / row['file']).resolve()
        if not path.is_relative_to(recovery.resolve()):
            raise RuntimeError('Recovery outside source root')
        source = path.read_bytes()
        code = view.read(int(address, 16) - pe.OPTIONAL_HEADER.ImageBase, size)
        instructions = list(decoder.disasm(code, int(address, 16)))
        listing = ('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions) + '\n').encode()
        for ext, data in (('.bin', code), ('.asm', listing), ('.c', source)):
            save('native/' + address + ext, data)
        envelopes.append({'address': address, 'bytes': size, 'native_sha256': sha(code),
                          'recovery_source': str(path), 'recovery_source_sha256': sha(source),
                          'metadata': row, 'decoded_instruction_bytes': sum(i.size for i in instructions),
                          'native_executed': False})
    dump('native/function-envelopes.json', {'primary': str(primary), 'sha256': PIN,
        'recovery_metadata_sha256': sha(metadata), 'ranges': envelopes, 'native_executed': False})
    literals = []
    for label, va, size in LITERALS:
        data = view.read(va - pe.OPTIONAL_HEADER.ImageBase, size)
        save('native/literal-' + label + '.bin', data)
        row = {'label': label, 'va': f'{va:08x}', 'bytes': size, 'raw_hex': data.hex(), 'sha256': sha(data)}
        if label == 'auxiliary-field3-divisor':
            row['file_float32'] = struct.unpack('<f', data)[0]
        literals.append(row)
    pe.close()
    dump('native/literals.json', literals)
    client = primary.parent
    resource_rows = []
    records = {}
    for name in ('HeroDoll.csvZ', 'Drv.csvZ', 'DrvDoll.csvZ'):
        path = client / 'Data2/Patch' / name
        data = path.read_bytes()
        save('resources/' + name, data)
        resource = {'path': str(path), 'snapshot': name, 'encoded_bytes': len(data), 'encoded_sha256': sha(data),
                    'wrapper_declared_plain_bytes': int.from_bytes(data[2:6], 'little'), 'native_executed': False}
        try:
            decoded = decode_csvz(data, limit=1000000) # Pure file decoding; no native/C++ parser execution.
        except ValueError as error:
            if name != 'DrvDoll.csvZ':
                raise
            resource.update(decoded=False, error_type=type(error).__name__, error=str(error),
                            bounds_relaxed=False, substituted_data=False)
        else:
            save('resources/' + name + '.decoded', decoded)
            lines = decoded.splitlines()
            header = lines[0].split(b',')
            first = int(header[2])
            rows_in_file = []
            for line, text in enumerate(lines[first-1:], first):
                columns = text.split(b',')
                if not columns[0] or (name == 'HeroDoll.csvZ' and not columns[1]):
                    continue
                record = {'source_line': line, 'native_row': len(rows_in_file), 'raw_line_hex': text.hex()}
                if name == 'HeroDoll.csvZ':
                    record.update(key=(columns[0]+columns[1]).decode('ascii').lower(),
                                  filename=columns[3].decode('ascii').lower(), field5_byte=int(columns[5]) & 255)
                else:
                    record.update(declared_id=columns[0].decode('ascii'), filename=columns[1].decode('ascii'),
                                  fields2_to7=[int(c) & 65535 for c in columns[2:8]])
                rows_in_file.append(record)
            records[name] = rows_in_file
            dump('resources/' + name + '.rows.json', rows_in_file)
            resource.update(decoded=True, decoded_bytes=len(decoded), decoded_sha256=sha(decoded),
                            header_raw_hex=lines[0].hex(), first_data_line=first, accepted_rows=len(rows_in_file))
            if name == 'HeroDoll.csvZ':
                resource['declared_rows'] = int(header[4])
                if len(rows_in_file) != int(header[4]):
                    raise RuntimeError('Actual HeroDoll count differs')
                resource['duplicate_keys'] = len(rows_in_file) - len({r['key'] for r in rows_in_file})
        resource_rows.append(resource)
    dump('resources/source-files.json', resource_rows)
    prior = base / 'web-ui-registration-handoff-01'
    manifest_bytes = (prior / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    if not manifest['sealed']:
        raise RuntimeError('Previous handoff not sealed')
    pins = {r['path']: r['sha256'] for r in manifest['files']}
    save('retained-peer/manifest.json', manifest_bytes)
    for rel in ('server-file-source-receipt.json', 'server-ACK-sent.json', 'round-report.json'):
        data = (prior / rel).read_bytes()
        if sha(data) != pins[rel]:
            raise RuntimeError('Previous sealed receipt differs')
        save('retained-peer/' + rel, data)
    facts = {
        'round': ROUND, 'cn_native_sha256_context': PIN,
        'previous_goal_turn_classification': 'progress: actual UI registration source handoff saved, current CN bytes read, prior UI poll ACK confirmation recorded',
        'cn_actual_appearance_table_profiles_added': 1, 'cn_scene_appearance_row_preparation_edges_added': 2,
        'actual_hero_rows_read': len(records['HeroDoll.csvZ']), 'actual_driver_rows_read': len(records['Drv.csvZ']),
        'driver_native_slot_capacity': 92, 'driver_selector_is_ordinal_not_declared_id': True,
        'hero_duplicate_key_map_last_row_wins': True,
        'native_function_envelopes_read': len(envelopes), 'native_function_bytes_read': sum(r['bytes'] for r in envelopes),
        'native_literals_read': len(literals), 'auxiliary_resource_recovered': False,
        'DrvDoll_declared_bounds_relaxed': False, 'ROM_ACT_handles_or_rendering_recovered': False,
        'authoritative_equipment_to_appearance_recovered': False, 'formal_application_hosted': False,
        'new_packet_values': 0, 'new_native_phase_source_bindings': 0, 'new_source_owner_chains': 0,
        'new_tw_source_owner_chains': 0, 'new_complete_bidirectional_routes': 0,
        'whole_game_route_total': None, 'whole_game_completed_routes': None, 'whole_game_completion_percent': None,
        'levels_changed': False, 'build_run': False, 'tests_run': False, 'runtime_run': False,
        'database_access': False, 'deployed': False, 'preserved_contexts': preserved, 'remaining': REMAINING,
    }
    dump('findings.json', facts)
    for rel in SOURCES:
        data = (ROOT / rel).read_bytes()
        name = Path(rel).name
        save('source/' + name, data)
    dump('source/source-origins.json', [{'path': rel, 'snapshot': Path(rel).name,
        'sha256': sha((ROOT / rel).read_bytes())} for rel in SOURCES])
    ledger_path = base / 'packet-route-ledger.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    ledger['cn_native_appearance_resource_source'] = dict(facts, evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append({
        'name': 'CN actual HeroDoll/Drv immutable table profile -> normal2A/ordinary6F row/path selection',
        'version_scope': 'cn-ordinary-appearance-resource-rows-only',
        'status': 'Actual selected resource bytes/CP936 preserved -> native CSV keyed HeroDoll and ordinal Drv rows -> slot1 head-dependent variant/mounted weapon/body/face/head ActType -> selected original paths; auxiliary/ROM/ACT/equipment/issuer/current revision/host open',
        'source_paths': list(SOURCES), 'native_c2s_by_phase': {}, 'native_s2c_by_phase': {},
        'source_owner_chains_added': 0, 'tw_source_owner_chains_added': 0, 'formal_application_hosted': False,
        'complete_gameplay_routes_added': 0, 'cn_actual_appearance_table_profiles_added': 1,
        'cn_scene_appearance_row_preparation_edges_added': 2, 'evidence': out.relative_to(ROOT).as_posix(),
        'remaining': REMAINING,
    })
    plan = ledger['dual_client_execution_plan']
    plan['latest_work_round'] = ROUND
    plan['next_source_frontier'] = ('Recover original004197E0 ROM/ACT/bank/cache/counter and actual profile/revision/connection/world appearance qualification, plus DrvDoll declared-length discrepancy without relaxing bounds; continue auxiliary/alternate validity and authoritative equipment-to-native inputs/full6F issuer/observer policies. Normal2A/ordinary6F actual HeroDoll/Drv row/path sources are now explicit but unhosted, not loaded resources or gameplay. All native PC/web providers/hosting/numeric/gameplay/denominator remain open; levels unchanged, PHASE1 file-only.')
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (ROOT / 'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a', encoding='utf-8') as stream:
        stream.write('\n\n## CN original appearance table row/path sources (' + ROUND + ')\n\n'
            'Actual selected HeroDoll/Drv file bytes -> immutable native-key/ordinal row profile -> full normal2A/ordinary6F getters -> original ActType/body/face/head/weapon and head-dependent face variant -> selected RoleDoll/Drv paths. Profile1/scene preparation edges2; new opcode/phase/owner/full route0. HeroDoll918 rows, Drv92 slots/rows (machine bound0x5B, not assertion text91). Current DrvDoll exceeds declared length in file-only decoding; exact encoded source/error retained, no bounds relaxation or fabricated auxiliary. ROM/ACT/cache/current profile/issuer/world, equipment/full6F/rules/observer/host and all gameplay remain open. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-native-appearance-resource-source-20261007.md.\n')
    print(json.dumps({k: facts[k] for k in ('round', 'actual_hero_rows_read', 'actual_driver_rows_read',
        'native_function_envelopes_read', 'native_function_bytes_read', 'cn_scene_appearance_row_preparation_edges_added',
        'new_complete_bidirectional_routes')}))

if __name__ == '__main__':
    main()
