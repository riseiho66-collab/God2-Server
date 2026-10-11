"""Recover beast panel wire/source evidence statically; no client execution.

This writes analysis evidence only. It is not a test runner, acceptance oracle,
save importer, build tool or native gameplay-completion claim.
"""
import hashlib
import json
import struct
from pathlib import Path

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE
from tools.strike_lab.omega_assets import decode_csvz


def digest(data):
    return hashlib.sha256(data).hexdigest()


def section_rows(relative, tag, selected, *, compressed=None, path_label=None):
    path = SERVER.parent / 'God2' / relative
    if compressed is None:
        compressed = path.read_bytes()
    decoded = decode_csvz(compressed)
    lines = decoded.splitlines(keepends=True)
    rows = []
    remaining = 0
    offset = 0
    section = None
    for line_number, raw in enumerate(lines, 1):
        line = raw.rstrip(b'\r\n')
        fields = line.split(b',')
        if fields[0] == tag:
            remaining = int(fields[1])
            section = {'tag': tag.decode('ascii'), 'line': line_number,
                       'decoded_offset': offset, 'declared_records': remaining}
        elif remaining:
            remaining -= 1
            if selected is None or int(fields[0]) in selected:
                # Decode selected exact rows strictly. The complete gamedata
                # resource is not uniformly CP950-decodable.
                rows.append({'id': int(fields[0]), 'line': line_number,
                             'decoded_offset': offset, 'raw_hex': line.hex(),
                             'row_sha256': digest(line), 'cp950_text': line.decode('cp950')})
        offset += len(raw)
    return {'path': path_label or str(path), 'compressed_sha256': digest(compressed),
            'decoded_sha256': digest(decoded), 'section': section, 'rows': rows,
            'record_hash_convention': 'exact row bytes excluding CR/LF',
            'authority': 'SOURCE_TEXT_ONLY_NOT_INSTANCE_OR_GAMEPLAY_AUTHORITY'}


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if digest(raw) != PIN:
        raise ValueError('Selected mapped native source changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    functions = []
    for start, size, purpose in [
            (0x97ee0, 0x2e, 'C2S6C WORD/BYTE/constant1 producer'),
            (0xd8f50, 0x31, 'C2S9D WORD/BYTE/constant1 producer'),
            (0x972f0, 0x2f, 'shared C2S6B producer; BYTE arg3,arg2,arg1'),
            (0xa0470, 0x5a, 'food control11 ->6B lane0 inventory slot and selector'),
            (0xa04d0, 0xec, 'controls7/8 ->6C/9D dispatcher'),
            (0xa0840, 0x127, 'S2C4C body16 selected snapshot'),
            (0xa0970, 0x11d, 'S2C4D body8 partial panel and inventory update'),
            (0xa0ae0, 0x1a1, 'snapshot display field widths and masks'),
            (0xa0700, 0x8c, 'body6 WORD percent display: FLOAT0.01, format%6.2f%s, ProgramMsg362'),
            (0xa0240, 0xb9, 'snapshot bit27 changes control7'),
            (0xa0300, 0xb9, 'snapshot bit28 and kind2 change control8'),
            (0x9faa0, 0x9e, 'three kind labels645/646/647; separate food label96'),
            (0xa0a90, 0x3f, 'S2CC6 linked state consumer; special value4 closes'),
            (0x9fb40, 0x87, 'S2C4B panel signal, selector BYTE1; BYTE2 unconsumed'),
            (0xd8490, 0x8c, 'S2CC5 copies308 bytes, derives both page counts'),
            (0xd8610, 0x62, 'C2S9F closes visible exploration panel with old context DWORD'),
            (0xd8750, 0x24, 'select zero-based option in six-entry page'),
            (0xd8780, 0x8a, 'C2S9E operation2 with zero-based selected index'),
            (0xd8810, 0x6b, 'C2S9E operation0/1 with one-based selected index'),
            (0xd8b70, 0x1ee, 'C5 template50 cap, source/item arguments and raw option count')]:
        code = raw[start:start + size]
        functions.append({'rva': f'{start:X}', 'size': size, 'purpose': purpose,
                          'sha256': digest(code), 'bytes_hex': code.hex(),
                          'instructions': [{'rva': f'{i.address-BASE:X}', 'instruction': f'{i.mnemonic} {i.op_str}'}
                                           for i in md.disasm(code, BASE + start)]})
    receivers = []
    for opcode in (0x4b, 0x4c, 0x4d, 0xc5, 0xc6):
        leaf = struct.unpack_from('<I', raw, 0x1324 + opcode * 4)[0] - BASE
        dispatch = struct.unpack_from('<I', raw, 0x6b5d4 + opcode * 4)[0] - BASE
        receivers.append({'opcode': f'{opcode:02X}', 'length_leaf_rva': f'{leaf:X}',
                          'length_leaf_bytes': raw[leaf:leaf+6].hex(),
                          'logical_size': struct.unpack_from('<i', raw, leaf+1)[0],
                          'dispatcher_rva': f'{dispatch:X}',
                          'dispatcher_bytes': raw[dispatch:dispatch+18].hex()})
    return {
        'format': 'god2-static-beast-panel-contract-v4',
        'status': 'WIRE_CODEC_RECOVERED_GAMEPLAY_ROUTE_INCOMPLETE',
        'method': 'STATIC_DISASSEMBLY_AND_SELECTED_ASSET_ROWS',
        'tests_client_execution_builds': False,
        'runtime_route_installed': False,
        'mapped_image': {'path': IMAGE, 'sha256': PIN, 'base': BASE},
        'source_codec': 'src/protocol/RecoveredBeastPanel.h',
        'exploration_codec': 'src/protocol/RecoveredBeastExploration.h',
        'correction_to_prior_analysis': 'C5 dispatch69D76 callsD8490 with body308; C6 dispatch69D88 callsA0A90 with body6. Prior C5-toA0A90 annotation was incorrect; retained prior analysis is not acceptance evidence.',
        'c2s': {'6C': {'control': 7, 'logical_size': 5}, '9D': {'control': 8, 'logical_size': 5},
                '6B/0': {'control': 11, 'logical_size': 4,
                         'layout': '6B constant0 inventorySlotBYTE selectedSelectorBYTE',
                         'scope': 'beast food only; shared combat-pet lanes1/3 remain distinct'},
                '9E': {'logical_size': 7, 'layout': 'contextDWORD operationBYTE selectionBYTE',
                       'branches': 'operation0 from state0 or1 from state2 uses one-based selected index; operation2 uses zero-based selected index orFF when none'},
                '9F': {'logical_size': 5, 'layout': 'old open contextDWORD'},
                'layout': 'opcode, selected key:u16LE, selector:u8, constant1:u8',
                'selected_source': 'UI+86888 primary+448C lowWORD and primary+448E BYTE'},
        's2c': receivers,
        'snapshot_fields_body_relative': {
            '0': 'metadata key WORD', '2': 'selected selector BYTE',
            '3': 'percentage display BYTE', '4': 'carried item key WORD',
            '6': 'percentage WORD raw: A0700 FLOAT0.01 and %6.2f%s with ProgramMsg362; prior lifetime name was unsupported',
            '8': 'DWORD: numerator bits0..10; denominator11..21; kind22..23; control7 bit27; control8 bit28 plus kind2; status29..31',
            '12': 'opaque DWORD; consumer uses BYTE12 in carried-item projection'},
        'delta_fields_body_relative': {
            '0': 'inventory slot BYTE, 24-byte native stride', '1': 'selected percentage BYTE',
            '2': 'inventory palette low3 accepted1..6 only for class5 inventory cell; distinct from panel selector',
            '3': 'full inventory BYTE9/classic level; selected panel retains low3bits; date definitions share byte domain',
            '4': 'numerator WORD masked7FF', '6': 'selected percent-display WORD raw, not a qualified lifetime unit'},
        'exploration_fields_body_relative': {
            '0': 'context DWORD: lowWORD metadata key, BYTE2 selector, BYTE3 opaque',
            '4': 'state BYTE', '5': 'template count BYTE, consumer clamps50',
            '6': '50 WORD SystemMessage keys', '106': '50 WORD item-argument keys',
            '206': 'selected index BYTE', '207': 'option count BYTE, independent of template count',
            '208': '50 BYTE argument1 values', '258': '50 BYTE argument2 values'},
        'functions': functions,
        'inventory_offset_correction': 'UI85610 already metadata0. Native4D writes metadata10 low3 palette, metadata9 fullBYTE, metadata12 WORD. Earlier6/5/8 analysis retained; see beast-inventory-fields-static.json.',
        'inventory_fields_evidence': 'beast-inventory-fields-static.json',
        'source_rows': [
            section_rows('Data2/Patch/Comm/message.csvZ', b'ProgramMsg', {96, 362, 529, 645, 646, 647}),
            section_rows('Data2/Patch/Comm/gamedata.csvZ', b'PET', {5301})],
        'related_next_trace': {
            '4B': 'logical3, dispatcher69D50 ->9FB40, BYTE1 selected selector; BYTE2 unconsumed there',
            'C5': 'logical309, dispatcher69D76 ->D8490; source data/bindings and operation rules remain open',
            'C6': 'logical7, dispatcher69D88 ->A0A90; bodyDWORD+0 copiedUI88654; bodyBYTE+4 state or4 closes with old context9F',
            'appearance': 'DA ->61270/63780: recover PET-to-Drv authority, do not reuse historical mounted sample as owned state'},
        'open': [
            'owned PET beast acquisition/selection and persistent instance authority',
            'exact control7/control8 operation semantics for every beast kind',
            'native lifetime units, food/growth/cost rules and timers',
            'PET resource to actor appearance mapping and remote/self refresh',
            'Application routing, SQLite/C++ state and Lua rules',
            'comprehensive phase2 client tests after ALL game routes are connected']}


def main():
    target = SERVER / 'artifacts/integration/packet-connections-20261006/beast-panel-static-contract.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    prior = target.with_name('beast-panel-static-contract-v1-prior-analysis.json')
    if target.exists() and not prior.exists():
        prior.write_bytes(target.read_bytes())
    target.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(target), 'status': 'WIRE_CODEC_RECOVERED_GAMEPLAY_ROUTE_INCOMPLETE',
                      'client_execution_tests_builds': False}))


if __name__ == '__main__':
    main()
