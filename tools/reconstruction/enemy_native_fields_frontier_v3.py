"""Pinned, read-only static PK/observer UI frontier; no VM or tests."""
import hashlib
import json
import struct
from pathlib import Path
import capstone
from tools.reconstruction.archive_inputs import ArchivedInputs
from tools.strike_lab.omega_assets import decode_csvz

IMAGE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
MESSAGE = 'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/message.csvZ'
MESSAGE_PIN = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
ROOT = Path(__file__).resolve().parents[2]
SPANS = {
    'cursor_registration': (0x1a860, 0x1a8e1),
    'cursor_mode_setter': (0x83530, 0x83553),
    'cursor_pk_trade_selection': (0x835dc, 0x8364b),
    'cursor_watch_selection': (0x83884, 0x838b8),
    'selection_to_context_action': (0x81f70, 0x82059),
    'context_action_dispatch_and_pk': (0x65fa0, 0x6602a),
    'context_trade_request': (0x66068, 0x660a7),
    'context_observer_request': (0x66229, 0x66285),
    'world_context_action_caller': (0x66f58, 0x66f72),
    'pk69_zero_initialized_producer': (0x970a0, 0x9713d),
    'pk69_uninitialized_legacy_candidate': (0x97070, 0x9709f),
    'pk_dialog_event': (0x83c80, 0x83ddd),
    'pk8a_world_invitation': (0x6ad80, 0x6ae12),
    'pk_dialog_copy_and_busy_reply': (0x84620, 0x84707),
    'pk_dialog_open_type_storage': (0x84768, 0x847b0),
    'role_list_alternative_action': (0xdcf80, 0xdd0f0),
    'trade29_wrapper': (0x9de30, 0x9de41),
    'generic_word_pair_producer': (0x97250, 0x97286),
    'observer6e_producer': (0x97d40, 0x97d71),
    'observer_exit': (0x113080, 0x1130c5),
    'world82_transition': (0x6ae12, 0x6ae45),
    'battle_observer_flag': (0x1113ba, 0x1113cc),
    'c2s8b_list_a': (0x75a90, 0x75b09),
    'c2s8b_list_b': (0x75b10, 0x75b89),
    'c2s8c_state_pair': (0xd3310, 0xd3380),
    'battle_dispatch': (0x1193c2, 0x1193e7),
    'world69_status': (0x6ac58, 0x6ac6c),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    a = ArchivedInputs()
    try:
        b, message = a.read(IMAGE), a.read(MESSAGE)
    finally:
        a.close()
    if sha(b) != PIN or sha(message) != MESSAGE_PIN:
        raise ValueError('Selected original pin differs')
    c = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans = {}
    for name, (lo, hi) in SPANS.items():
        raw = b[lo:hi]
        spans[name] = {'start_rva': hex(lo), 'end_rva_exclusive': hex(hi),
                       'sha256': sha(raw), 'bytes_hex': raw.hex(),
                       'instructions': [{'rva': hex(i.address), 'bytes': i.bytes.hex(),
                                         'mnemonic': i.mnemonic, 'operands': i.op_str}
                                        for i in c.disasm(raw, lo)]}
    tables = {}
    for name, address, count in [('selection_action', 0x8205c, 15),
                                  ('context_action', 0x6643c, 20),
                                  ('dialog_type', 0x84520, 64),
                                  ('role_list_action', 0xdd0f4, 15)]:
        raw = b[address:address + count * 4]
        tables[name] = {'rva': hex(address), 'sha256': sha(raw), 'bytes_hex': raw.hex(),
                        'target_rvas': [hex(x - 0x400000) for x in struct.unpack('<' + 'I' * count, raw)]}
    cursors = []
    for mode in range(26):
        p = struct.unpack_from('<I', b, 0x185a48 + mode * 4)[0] - 0x400000
        raw = b[p:b.index(0, p)]
        cursors.append({'mode': mode, 'filename_rva': hex(p), 'raw_hex': raw.hex(),
                        'filename': raw.decode('ascii'), 'sha256': sha(raw)})
    direct_calls = {}
    for target in [0x970a0, 0x97070, 0x97d40, 0x65fa0]:
        hits = [hex(i) for i in range(0x1000, 0x170000 - 5)
                if b[i] == 0xe8 and i + 5 + struct.unpack_from('<i', b, i + 1)[0] == target]
        direct_calls[hex(target)] = {'candidate_rvas': hits,
                                     'scope': 'E8 exact-target scan, not exhaustive indirect callers'}
    dispatch = []
    for op in [0x69, 0x6e, 0x82, 0x8a, 0x8b, 0x8c]:
        lengthleaf = struct.unpack_from('<I', b, 0x1324 + op * 4)[0] - 0x400000
        battleindex = b[0x119a04 + op]
        dispatch.append({'opcode': hex(op), 'length_leaf_rva': hex(lengthleaf),
                         'length_leaf_bytes': b[lengthleaf:lengthleaf+6].hex(),
                         'world_target_rva': hex(struct.unpack_from('<I', b, 0x6b5d4 + op*4)[0]-0x400000),
                         'battle_switch_index': battleindex,
                         'battle_target_rva': hex(struct.unpack_from('<I', b, 0x119908+battleindex*4)[0]-0x400000)})
    plain, rows, section, offset = decode_csvz(message), [], '', 0
    for row in plain.splitlines(keepends=True):
        first = row.split(b',', 1)[0]
        if first and not first.isdigit():
            section = first.decode('ascii', 'replace')
        if (section == 'ProgramMsg' and first in [b'47', b'48', b'51', b'733', b'750']) or (section == 'Msg' and first == b'881'):
            rows.append({'section': section, 'offset': offset, 'sha256': sha(row),
                         'raw_hex': row.hex(), 'cp950': row.decode('cp950').strip()})
        offset += len(row)
    return {
        'scope': 'STATIC_PK_AND_OBSERVER_FRONTIER_V3',
        'execution': {'tests': False, 'VM_native_execution': False, 'network': False,
                      'client': False, 'formal_DB_or_source_write': False},
        'pins': {'mapped_image': PIN, 'mapped_image_path': IMAGE, 'base_va': '0x400000',
                 'message_raw': MESSAGE_PIN, 'message_decoded': sha(plain)},
        'convention': 'RVA/file offsets hex; logical packet offsets decimal, including opcode.',
        'native_spans': spans, 'data_tables': tables, 'cursor_registration_data': cursors,
        'direct_calls': direct_calls, 'dispatch_data': dispatch, 'original_message_rows': rows,
        'qualified_ui_paths': [
            {'name': 'PK_REQUEST', 'chain': 'cursor3 pk.ani ->835DC mode3 returns selection2 ->8205C[1] 81FD4 returns action-5 ->6643C[19]65FC5 ->65FF8 call970A0',
             'logical': '69 length45: DWORD+1 localID,DWORD+5 targetID,16-byte string regions+9/+25,BYTE+41 control0,+42..44 zero',
             'source': '970A0 zeroes44 bodybytes before fields; control1/2/3 use same producer'},
            {'name': 'PK_INVITATION_REPLY', 'chain': 'S2C8A6AD80 ->84620 copy ->84710 dialogtype13 ->83C80 event ->84520[13]83DA9',
             'context': '8A DWORD+5->UI23D5B0,DWORD+1->23D5B4;string+25->23D5B8,string+9->23D5C8',
             'accept': 'optionWORD0 at83CE7 ->83DC9 control1',
             'decline': 'optionWORD1 ->83D60..83D7F control2;ECX constant2 established83C8B and not clobbered on this branch',
             'busy': '846FE control3 if preexisting active dialog guard',
             'reply_identity': 'C2S69 DWORD+1=context23D5B0,DWORD+5=context23D5B4;thus recipient,theninviter',
             'reply_strings': 'C2S69+9=context23D5B8 (8A+25),+25=context23D5C8 (8A+9)'},
            {'name': 'TRADE_REQUEST', 'chain': 'cursor4 trade.ani ->83617 returns selection3 ->8205C[2]81FDD action-6 ->66068 ->9DE30 ->97250 opcode29',
             'logical': '29 length5:WORD+1 low16 targetID,WORD+3 zero'},
            {'name': 'OBSERVER_REQUEST', 'chain': 'cursor10 watch.ani ->83884 returns selection10 ->8205C[9]82013 action-17 ->66229 ->66274 call97D40(selector1,targetID)',
             'logical': '6E length9:BYTE+1 selector1,+2..4 uninitialized stack bytes,DWORD+5 targetID',
             'classification': 'Observer UI branch,not opponent ability inspect'},
            {'name': 'OBSERVER_EXIT', 'chain': '82 lowBYTE(secondDWORD)==FF ->1113BF..1113C6 B+A9EA4C8=1 ->113080 right-click exit ->1130A8 call97D40(selector2,target0)',
             'limit': 'Connects observer UI request and marked battle exit;actual server82 field authority/room assignment remains OPEN'},
        ],
        'other_visible_opcodes': [
            {'opcode': 'C2S8B', 'producer': ['75AEA','75B6A'], 'logical_length': 2, 'byte1': 1,
             'source': 'selected list record+8 equals original literal gm at18470C;not69 PKdialog producer', 'meaning': 'OPEN'},
            {'opcode': 'C2S8C', 'producer': 'D3362..D336B', 'logical_length': 3,
             'byte1': 'UI+5D59D','byte2': 'UI+5D59C', 'gates': 'both bytes!=FF;time delta>1000', 'meaning': 'OPEN'},
            {'opcode': 'S2C8B/8C', 'logical_length': 2,
             'world': '6B517 defaultconsume', 'battle': '1198A1 defaultconsume',
             'limit': 'These visible modes establish no accept/decline/status effects;not proof for other modes/builds'},
        ],
        'enemy_abilities': {field: {'classification': 'UNKNOWN', 'packet_offset': None,
                                    'enemy_memory_writer': None}
                            for field in ['物攻','魔攻','物防','魔防','力','體','智','速','金','木','水','火','土','完整攜帶技能']},
        'next_source_route': 'Implement69 pending invitation/control0 ->8A peer invitation ->69 control1/2/3. On mutually accepted authoritative PK room creation,use existing82/1C/86/83 native consumer contracts. RoomID,server82 meanings,rules and1C participants remain separate source/authority obligations;do not label controlled values official.',
        'open': ['Server69 routing/authorization andPK matching policy', '82 DWORD gameplay meanings andtruePK battle setup authority',
                 'Other6E selectors beyond emitted1/2', 'Indirect caller completeness andothernet modes',
                 'Actual observer server response andwatching-room lifecycle', 'Official enemy dualattack/dualdefense/fullskill values remain unreceived inthis static research'],
    }


if __name__ == '__main__':
    output = ROOT / 'artifacts/research/enemy-native-fields-20261006/frontier-v3.json'
    output.write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(output))
