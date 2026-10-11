"""Recover original76/5/9 modal routes and95 war display, statically only.

No native process, emulator, tests, builds, DB writer or runtime installer.
Keeps schema53 alliance authority separate from unknown war gameplay policy.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE
from .beast_panel_contract import section_rows

MESSAGE = 'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/message.csvZ'
MESSAGE_PIN = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
MESSAGE_DECODED = '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
        message = reader.read(MESSAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped source identity changed')
    label_ids = struct.unpack_from('<8H', raw, 0x197ea8)
    labels = section_rows('Data2/Patch/Comm/message.csvZ', b'ProgramMsg',
                          set(label_ids), compressed=message, path_label=MESSAGE)
    if labels['compressed_sha256'] != MESSAGE_PIN or labels['decoded_sha256'] != MESSAGE_DECODED:
        raise ValueError('Original message identity changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    functions = []
    for start, end, purpose in [
        (0xebf92, 0xebfdb, 'ProgramMsg table initializer: ID table197EA8 -> pointers197EC0 stride8'),
        (0xee560, 0xee5c8, 'modal result7..10 -> same cached17-byte76 producer'),
        (0xee6bc, 0xee7d6, 'declare prompt writes cached subtype5; existing exact raw6 blocks prompt'),
        (0xee7d6, 0xee8c7, 'remove prompt: exact raw1..3 ->8; exact raw4..7 ->9'),
        (0xf0d50, 0xf0eff, 'relation render masks7F; renders three BYTEs using month/day/hour format'),
        (0xf0fb0, 0xf1163, '95 complete24-byte body cache, cap50 and duplicate append/replace behavior'),
        (0x68c54, 0x68c78, 'world95 and96 body dispatch toF0FB0/F11F0'),
    ]:
        code = raw[start:end]
        functions.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                          'purpose': purpose, 'bytes_hex': code.hex(),
                          'sha256': hashlib.sha256(code).hexdigest(),
                          'instructions': [{'rva': f'{i.address-BASE:X}',
                                            'instruction': f'{i.mnemonic} {i.op_str}'}
                                           for i in md.disasm(code, BASE+start)]})
    literals = []
    for rva, length, purpose in [
        (0x197ea8, 16, '8 ProgramMsg WORD keys indexed by raw_type&7F'),
        (0x197ec0, 64, '8 runtime label-pointer/color pairs; file pointers0 are initialization, not absent labels'),
        (0x1966c4, 15, 'date display format literal'),
        (0xee5c8, 32, '8 modal-result jump-table targets: result3..10'),
    ]:
        code = raw[rva:rva+length]
        literals.append({'rva': f'{rva:X}', 'length': length, 'purpose': purpose,
                         'bytes_hex': code.hex(), 'sha256': hashlib.sha256(code).hexdigest()})
    lengths = []
    for opcode in (0x95, 0x96):
        leaf = struct.unpack_from('<I', raw, 0x1324+opcode*4)[0]-BASE
        lengths.append({'opcode': f'{opcode:02X}', 'leaf_rva': f'{leaf:X}',
                        'bytes_hex': raw[leaf:leaf+6].hex(),
                        'logical_size': struct.unpack_from('<i', raw, leaf+1)[0]})
    return {
        'format': 'god2-static-guild-war-contract-v1',
        'status': 'NATIVE_CLIENT_FORMAT_AND_UI_INTENT_RECOVERED_SERVER_WAR_ROUTE_OPEN',
        'method': 'STATIC_PINNED_DISASSEMBLY_AND_ORIGINAL_PROGRAMMSG_ROWS',
        'tests_builds_emulator_client_execution': False,
        'database_mutation_installation_deployment': False,
        'mapped_image': {'path': IMAGE, 'sha256': PIN, 'base': BASE},
        'source_codec': 'src/relations53/RelationsRawCodec.h',
        'functions': functions, 'literal_tables': literals, 's2c_lengths': lengths,
        'label_source': labels,
        'display_kinds': [
            {'raw_low7': n, 'programmsg': key, 'label': title}
            for n, key, title in zip(range(8), label_ids,
                ['EMPTY', 'ALLIANCE', 'ALLIANCE_INVITATION', 'INVITED_TO_ALLIANCE',
                 'DEFENSE', 'ATTACK', 'WAR_DECLARATION', 'DECLARED_AGAINST'])],
        'date_display': {
            'logical_offsets': {'6': 'monthBYTE', '7': 'dayBYTE', '8': 'hourBYTE'},
            'body_offsets': {'5': 'monthBYTE', '6': 'dayBYTE', '7': 'hourBYTE'},
            'format_literal_rva': '1966C4', 'format': '%2d/%2d %02d:00',
            'consumer_rva': 'F0DF3..F0E1C',
            'limits': 'DISPLAY_ONLY; no year/minute/timezone/timer/server schedule policy recovered'},
        'c2s': {
            'logical_size': 18, 'layout': '76 subtypeBYTE name16',
            'declare': {'subtype': 5, 'prompt': 'EE6F8..EE782', 'modal_result': 8},
            'remove': {'subtype': 9, 'prompt': 'EE7ED..EE8AE', 'modal_result': 10,
                       'allowed_exact_raw_types': [4, 5, 6, 7],
                       'high_bit_masked_for_this_decision': False},
            'dispatch': 'EE560 result7..10 ->EE5AF cachedUI+C6CC body17 ->132E0'},
        'native_consumer_limits': {
            'capacity': '50 BEFORE duplicate lookup',
            'duplicate_types6_7': 'append another row with same DWORD identity',
            'replacement_types4_5': 'replace first identity row; scan later matching6/7 with swap-delete',
            'opaque_id': 'client relation identity only; durable guild join is server CUSTOM0084 authority',
            'raw_high_bit': 'F0E26 chooses an icon; never proven consent or SQL authorization'},
        'server_frontier': {
            'current': 'schema53 admits only1/8; state0/1/2 and event constraints remain immutable',
            'required': ['separate additive war state/event policy with explicit provenance',
                         'authoritative two-guild owner/WORLD/read-set/CAS admission',
                         'qualified or documented CUSTOM schedule/consent/cancel/economics',
                         'shared95/96 projection and capacity/cache reconciliation',
                         'transfer/disband/character lifecycle integration',
                         'war activity/combat consequences and comprehensive later-phase acceptance'],
            'not_recovered': 'Native original war permission, fees, scheduling, duration, rewards and combat rules'},
    }


def main():
    target = SERVER/'artifacts/integration/packet-connections-20261006/guild-war-static-contract.json'
    if target.exists():
        raise FileExistsError('Keep immutable v1 evidence; use a new version for changed analysis')
    target.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(target), 'method': 'STATIC_ONLY',
                      'tests_builds_client_execution_database_mutation': False}))


if __name__ == '__main__':
    main()
