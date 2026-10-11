"""Preserve branch/argument producer evidence omitted by the generic census.

Reads the pinned mapped image into memory; never executes native instructions.
The historical generic candidate set is retained, not replaced by this union.
"""
import hashlib
import json
import struct
import capstone
from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN

ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'


def main():
    out = ROOT / 'tw-supplemental-producers-01'
    if out.exists():
        raise RuntimeError('Preserve prior evidence')
    archive = ArchivedInputs()
    try:
        raw = archive.read(IMAGE)
    finally:
        archive.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise RuntimeError('Native build changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    ranges = {
        'trade-confirm-local': (0x83ddd, 0x83e1e),
        'trade-cancel': (0x9dd40, 0x9de2f),
        'trade-control-wrapper': (0x97a60, 0x97a82),
        'guild-input-dispatch': (0xee5f0, 0xee612),
        'guild-create': (0xee950, 0xee9a5),
        'guild-join': (0xee9a5, 0xee9fa),
        'guild-shared-queue': (0xeee1a, 0xeee39),
        'teleport-context-selector': (0xf6da0, 0xf6deb),
        'teleport-submit': (0xf72b0, 0xf7336),
    }
    slices = []
    for name, (start, end) in ranges.items():
        data = raw[start:end]
        slices.append({'name': name, 'rva_start': f'{start:X}', 'rva_end_exclusive': f'{end:X}',
                       'sha256': hashlib.sha256(data).hexdigest(), 'hex': data.hex(),
                       'instructions': [{'va': f'{i.address:08X}', 'bytes': i.bytes.hex(),
                                         'mnemonic': i.mnemonic, 'operands': i.op_str}
                                        for i in md.disasm(data, 0x400000 + start)]})
    rows = [
        {'opcode': '2C', 'branch': 'trade-confirm-local', 'payload_bytes': 1,
         'wrapper_call_va': '00483E08', 'queue_call_va': '00497A7A',
         'flow': ['00483E03 push ebx (control)', '00483E04 push 2C',
                  '00483E08 call 497A60', '00497A6E load opcode from argument',
                  '00497A76 push payload size 1', '00497A79 push eax', '00497A7A call 4132E0'],
         'conditions': 'Local block reached; EBX control provenance and complete upstream UI branches remain outside this slice.',
         'source_paths': ['src/protocol/RecoveredTrade.h', 'src/handlers/OwnedInstanceTradeService.cpp'],
         'omission': 'Opcode is a wrapper argument, not an immediate at the queue call.'},
        {'opcode': '2D', 'branch': 'trade-cancel', 'payload_bytes': 1,
         'wrapper_call_va': '0049DD87', 'queue_call_va': '00497A7A',
         'flow': ['0049DD81 push control 0', '0049DD83 push 2D', '0049DD87 call 497A60',
                  '00497A6E load opcode from argument', '00497A7A call 4132E0'],
         'conditions': 'Signed dialog index owner+232DAE >=0, indexed dialog flags bit20 set, explicit close argument nonzero.',
         'source_paths': ['src/protocol/RecoveredTrade.h', 'src/handlers/OwnedInstanceTradeService.cpp'],
         'omission': 'Opcode is a wrapper argument, not an immediate at the queue call.'},
    ]
    for mode, branch, push, jump in [(4, 'guild-create', '004EE99E', '004EE9A0'),
                                     (5, 'guild-join', '004EE9F3', '004EE9F5')]:
        target = struct.unpack_from('<I', raw, 0xeee3c + mode * 4)[0]
        rows.append({'opcode': '6F', 'branch': branch, 'payload_bytes': 22,
                     'queue_call_va': '004EEE20', 'mode': mode,
                     'selector_table_rva': 'EEE3C', 'selector_target_va': f'{target:08X}',
                     'flow': ['004EE5FB read owner+D26C', '004EE60B indexed jump',
                              f'{push} push 6F', f'{jump} jump 4EEE1A', '004EEE20 call 4132E0'],
                     'conditions': f'Input mode {mode}; owner+8688C selected actor pointer dereferenced. Full opening/lifetime qualification remains required.',
                     'fields': 'context WORD, selected-actor hint WORD, name slot16, operation byte 0/1, opaque tail byte; native string copy is not a server length validator.',
                     'source_paths': ['src/protocol/RecoveredGuildMembership.h', 'src/relations53/GuildAdmission53Application.h'],
                     'omission': 'Opcode/payload pushes jump to a distant shared queue block.'})
    for op, condition, push in [('99', 'context not in 061E..0622', '004F72FA'),
                                ('A9', 'context in 061E..0622', '004F72EE')]:
        rows.append({'opcode': op, 'branch': 'teleport-submit-' + op, 'payload_bytes': 4,
                     'queue_call_va': '004F7305',
                     'flow': ['004F72DE call 4F6DA0', '004F72E3 compare AL to 1',
                              '004F72E5 push payload size 4', f'{push} push {op}', '004F7305 call 4132E0'],
                     'conditions': 'Signed owner+790E0 >0 and ' + condition,
                     'fields': 'context WORD, selected destination byte, opaque stack byte; no server destination/fee/permission inferred.',
                     'source_paths': ['src/protocol/RecoveredTeleport.h', 'src/handlers/RecoveredWorldService.cpp'],
                     'omission': 'Payload length and opcode pushes are separated by conditional/unconditional branch edges.'})
    baseline_paths = [ROOT / 'static-packet-index.json', ROOT / 'c2s-wrapper-census-v1.json']
    baseline = [json.loads(p.read_text(encoding='utf-8')) for p in baseline_paths]
    historical = set(baseline[0]['direct_argument_opcode_candidates']) | {
        int(x, 16) for x in baseline[1]['wrapper_argument_opcode_candidates']}
    recovered = {int(row['opcode'], 16) for row in rows}
    summary = {'native_image': IMAGE, 'native_sha256': PIN,
               'historical_generic_candidate_count': len(historical),
               'supplemental_opcode_values': sorted(f'{x:02X}' for x in recovered),
               'supplemental_native_branch_records': len(rows),
               'new_to_generic_census': sorted(f'{x:02X}' for x in recovered - historical),
               'generic_plus_supplemental_opcode_union': len(historical | recovered),
               'all_producer_variants_exhausted': False, 'phase_assignment_complete': False,
               'new_source_connections': 0, 'new_complete_bidirectional_routes': 0,
               'whole_game_route_total': None, 'whole_game_completion_percent': None,
               'build_run': False, 'tests_run': False, 'runtime_run': False, 'deployed': False}
    out.mkdir()
    def dump(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    dump('summary.json', summary)
    dump('producers.json', rows)
    dump('native-slices.json', slices)
    dump('source-manifest.json', [{'path': rel, 'sha256': hashlib.sha256((SERVER / rel).read_bytes()).hexdigest()}
                                  for rel in sorted({p for row in rows for p in row['source_paths']})])
    dump('baseline-manifest.json', [{'path': p.relative_to(SERVER).as_posix(),
                                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in baseline_paths])
    (out / 'tool.py').write_bytes(__import__('pathlib').Path(__file__).read_bytes())
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
