"""Pinned static enemy visibility map; no VM, network, database write or tests.

This is a consumer/dataflow inventory, not an official-monster data dump.
Unknown server values stay unknown, even when a local fixture assigns a value.
"""
import hashlib
import json
import struct
from pathlib import Path

import capstone
import pefile

from tools.reconstruction.archive_inputs import ArchivedInputs
from tools.strike_lab.omega_assets import decode_csvz

IMAGE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
DATA = 'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/gamedata.csvZ'
DATA_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'

SPANS = {
    'socket_raw_frame_receiver': (0x10bc0, 0x10d00),
    'recv_import_thunk': (0x143d56, 0x143d5c),
    'frame_decoder_and_checksum': (0x10a10, 0x10a8b),
    'logical_receiver_source_binding': (0x13420, 0x1349d),
    'logical_pointer_accessor': (0x13650, 0x13665),
    'world_logical_acquisition': (0x68b1c, 0x68b63),
    'battle_logical_acquisition': (0x119370, 0x1193e7),
    'identity_and_variant': (0x115c90, 0x115e78),
    'field2000_metadata_copy': (0x116149, 0x11616b),
    'actor_lookup': (0x11e6e0, 0x11e71b),
    'action_skill_cache': (0x116cf5, 0x116df6),
    'skill_consumer': (0x12c731, 0x12c7d8),
    'side1_hp_dispatch': (0x11736a, 0x11739a),
    'mp_side_gate': (0x1173a0, 0x1173dd),
    'hp_actor_copy': (0x12d840, 0x12d88d),
    'mp_actor_copy': (0x12d970, 0x12d9b3),
    'selector87_wrapper': (0x117540, 0x117557),
    'selector87_prefix': (0x11c520, 0x11c615),
    'own_companion_skill34': (0xaa660, 0xaa7bf),
    'pet2_fb_copy': (0xa52a0, 0xa52f5),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    inputs = ArchivedInputs()
    try:
        image = inputs.read(IMAGE)
        gamedata = inputs.read(DATA)
    finally:
        inputs.close()
    if sha(image) != IMAGE_SHA or sha(gamedata) != DATA_SHA:
        raise ValueError('Selected original inputs differ from the specified build')
    plain = decode_csvz(gamedata)
    if sha(plain) != PLAIN_SHA:
        raise ValueError('Original decoded resource identity differs')
    pe_path = Path(__file__).resolve().parents[2].parent / 'God2/God2.unpacked.exe'
    pe_raw = pe_path.read_bytes()
    pe_hash = sha(pe_raw)
    if pe_hash != '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
        raise ValueError('The selected unpacked PE version differs')
    pe = pefile.PE(data=pe_raw)
    imports = [(entry.dll.decode('ascii'), imp.name.decode('ascii'))
               for entry in pe.DIRECTORY_ENTRY_IMPORT for imp in entry.imports
               if imp.address == 0x570820 and imp.name]
    if imports != [('ws2_32.dll', 'recv')]:
        raise ValueError('Expected recv import binding differs')
    dis = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans = {}
    for name, (lo, hi) in SPANS.items():
        raw = image[lo:hi]
        spans[name] = {'rva_start': hex(lo), 'rva_end_exclusive': hex(hi),
                       'sha256': sha(raw), 'bytes_hex': raw.hex(),
                       'instructions': [{'rva': hex(i.address), 'bytes_hex': i.bytes.hex(),
                                         'mnemonic': i.mnemonic, 'operands': i.op_str}
                                        for i in dis.disasm(raw, lo)]}
    # This is DATA, not linear disassembly. The first switch handles actions1..23.
    action_targets = struct.unpack_from('<10I', image, 0x1171ac)
    action_indexes = image[0x1171d4:0x1171eb]
    actions = [{'action_decimal': n + 1, 'action_hex': hex(n + 1),
                'target_rva': hex(action_targets[index] - 0x400000)}
               for n, index in enumerate(action_indexes)]
    return {
        'scope': 'STATIC_NATIVE_CONSUMER_MAP', 'date': '2026-10-06',
        'execution': {'native_or_emulated_code': False, 'network': False,
                      'client_or_server': False, 'tests': False, 'save_mutation': False},
        'pins': {'mapped_image': {'path': IMAGE, 'sha256': IMAGE_SHA, 'base_va': '0x400000'},
                 'gamedata': {'path': DATA, 'compressed_sha256': DATA_SHA,
                              'decoded_sha256': PLAIN_SHA},
                 'unpacked_pe_imports': {'path': str(pe_path), 'sha256': pe_hash,
                                        'iat_va': '0x570820', 'module': imports[0][0], 'name': imports[0][1]}},
        'address_convention': 'Code addresses are hex RVAs; add0x400000 for VA. Packet offsets are decimal and include opcode unless explicitly body offsets.',
        'native_spans': spans,
        'action_first_switch': actions,
        'capture_entrypoints': {
            'raw_wire': {'native_receiver_rva': '0x10bc0',
                         'api': 'ws2_32.dll!recv', 'thunk_rva': '0x143d56', 'iat_va': '0x570820',
                         'call_rvas': ['0x10be0', '0x10c1e', '0x10c99'],
                         'return_rvas': ['0x10be5', '0x10c23', '0x10c9e'],
                         'stdcall_entry_stack': '[ESP+4]=socket,[ESP+8]=buffer,[ESP+C]=requested length,[ESP+10]=flags',
                         'returned_eax': 'actual received count; preserve only positive bytes from that recv buffer',
                         'ownership': 'outer logical receiverN owns streamR at N+758; each reference is a process address, not a global absolute',
                         'stream_fields_hex': {'raw_frame_start': '0x1818', 'collected_bytes': '0x2418',
                                               'declared_frame_length': '0x241c', 'socket': '0x2558'},
                         'limit': 'TCP segments can split/coalesce. Raw bytes alone are not decoded monster fields. Do not collect authentication or keys.'},
            'decoded_frame': {'entry_rva': '0x10a30', 'registers_before_call': 'EDI=frame start,EBX=frame length,ESI=streamR',
                              'decrypt_call_rva': '0x106f0', 'checksum_callsite_rva': '0x10a39',
                              'checksum_return_rva': '0x10a3e', 'accepted_only_if': 'EAX!=0 after checksum',
                              'limit': 'In-place decode occurs before checksum. Frame acceptance is not logical packet acceptance; compressed payload takes10820 branch.'},
            'pre_dispatch_logical': {'accessor_rva': '0x13650', 'pointer_instruction_rva': '0x1365d',
                                     'return_eax': 'N+2CC4', 'length_dword': 'N+2CC0',
                                     'world_callsite_rva': '0x68b47', 'world_return_rva': '0x68b4c',
                                     'battle_callsite_rva': '0x1193bd', 'battle_return_rva': '0x1193c2',
                                     'battle_queue_copy': 'B+A9E9CB0 before114332 dispatch',
                                     'limit': 'Copy before handlers, before next13670 reset/record assembly.1C variantWORD is mutable at115E47.'},
            'actor_memory': {'manager': 'M=B+144938', 'type0_pointer': 'DWORD[M+38+24*packedPosition]',
                             'lookup_rva': '0x11e6e0', 'position_domain': '0..27;side=position//14,slot=position%14',
                             'metadata': 'actor+DB0 length38 hex',
                             'current_hp': 'DWORD actor+DE8', 'current_mp': 'DWORD actor+DEC',
                             'maximum_hp': 'DWORD actor+DF0', 'maximum_mp': 'DWORD actor+DF4',
                             'skill_cache': 'actor+DF8 array51 DWORD pointers to definitions',
                             'current_skill': 'DWORD actor+EC4',
                             'limit': 'Resolve runtime bases freshly; no old PID/VA. Every value needs observed producer provenance. ResetCDCDCDCD, stale memory and null actor are not server values.'},
            'read_only_options': [
                'Offline packet/memory dump analysis preserves client and uses explicit build/base/offset/length identities.',
                'ReadProcessMemory on an authorized own process can read these already-discovered buffers/objects without injecting or changing client instructions; it can miss overwritten transient records.',
                'Authorized debugger hardware execution breakpoints at post-acquisition or writer addresses can stop long enough for read-only copying; they alter thread debug state/timing. Software INT3 breakpoints change code and do not satisfy an unchanged-instruction capture claim.',
                'External packet capture sees wire bytes only. Plaintext extraction must rely on a qualified original client decoder path rather than invented encryption/field assumptions.',
                'If process access is blocked, stop that path; no bypass/protection removal is part of this plan. No capture or official login performed here.']},
        'native_fields': {
            '1C': {'logical_bytes': 45, 'consumer_rva': '0x115c90',
                   'position': {'offset': 1, 'width': 1, 'side': 'value//14', 'slot': 'value%14'},
                   'displayed_level': {'offset': 2, 'width': 1, 'prepared_metadata_offset_hex': '0x7'},
                   'identity_word': {'offset': 3, 'width': 2, 'server_template_semantics': None},
                   'variant_word': {'offset': 5, 'width': 2, 'kind_mask': '0x6000',
                                    'mutable_in_client': True, 'rewrite_rva': '0x115e47'},
                   'normal_enyname': {'ordinal_offset': 7, 'ordinal_width': 2, 'area_offset': 9,
                                     'scene_offset': 11, 'scene_width': 2, 'lookup_rva': '0x115e07'},
                   'alternate_enyname': {'area': 0, 'ordinal': 'WORD+7 &0x3fff',
                                        'scene': '3 if WORD+7&0x8000 else13 if WORD+7&0x4000 else2',
                                        'lookup_rva': '0x115e70'},
                   'opaque_blocks': [[9, 16], [25, 16]],
                   'flags_dword_offset': 41,
                   'classification_limit': 'Side1 is an enemy SIDE, not proof of a wild monster;0x2000 and0x6000 are metadata/appearance families, not four-dimension vectors.'},
            '86': {'logical_bytes': 17, 'subtype_offset': 1, 'position_offset': 2,
                   'maximum_dword_offset': 5, 'current_dword_offset': 9,
                   'subtype0': {'resource': 'HP', 'current_actor_offset_hex': '0xde8',
                                'maximum_actor_offset_hex': '0xdf0', 'copy_rvas': ['0x12d86c', '0x12d875'], 'native_sides': [0, 1]},
                   'subtype1': {'resource': 'MP', 'current_actor_offset_hex': '0xdec',
                                'maximum_actor_offset_hex': '0xdf4', 'copy_rvas': ['0x12d99c', '0x12d9a5'], 'native_sides': [0],
                                'side1_skip_rva': '0x1173d7',
                                'limit': 'A received subtype1 side1 raw record can still be retained if observed; client actor memory does not prove it was applied. No received record does not mean zeroMP.'}},
            '83': {'logical_bytes': 15, 'action_offset': 1, 'position_offset': 2,
                   'marker_offset': 3, 'target_mask_word_offsets': [5, 7],
                   'skill_id_offset': 11, 'skill_bank_offset': 12,
                   'cache_branches_action_hex': ['0x3', '0x17'],
                   'cache_base_actor_offset_hex': '0xdf8', 'nominal_cache_pointers': 51,
                   'cache_write_rva': '0x116dc1', 'selected_cache_slot_actor_offset_hex': '0x1df',
                   'current_definition_actor_offset_hex': '0xec4', 'current_definition_write_rva': '0x12c7d2',
                   'limit': 'Pair association observed in an incoming action is not a full repertoire, permission, AI condition, cost or intrinsic stat.0x17 shares cache producer, but its action semantics are unresolved.'},
            '87': {'logical_bytes': 3, 'consumer_rva': '0x11754c',
                   'owner': 'battle+A9DC198 local selector',
                   'limit': 'WORD+1 updates selectable local bank entries, not a side1 actor repertoire.'},
            '34': {'logical_bytes': 4, 'consumer_rva': '0xaa660',
                   'key_offset': 1, 'bank_offset': 2, 'entry_offset': 3,
                   'owner': 'matching owned-companion row selected by key; count+1F0 and pointers+258',
                   'limit': 'Owned learned skills do not provide a PK enemy or wild-monster complete skill list.'},
            'FB': {'logical_bytes': 73, 'consumer_rva': '0xa52a0', 'owner': 'world+232EBC owned pet2 panel;slots42..44',
                   'original_labels': ['\u7269\u653b', '\u7269\u9632', '\u9b54\u653b', '\u9b54\u9632'],
                   'label_authority': 'Original petegg.romZ background plus control-coordinate mapping;docs/research/current-pet2-stat-labels-20260920.md,not enemy labels',
                   'body_attack_defense_word_offsets_hex': ['0x10', '0x12', '0x14', '0x16'],
                   'body_four_dimensions_word_offsets_hex': ['0x24', '0x26', '0x28', '0x2a'],
                   'body_elements_word_offsets_hex': ['0x18', '0x1a', '0x1c', '0x1e', '0x20'],
                   'limit': 'These are received owned-pet2 instance values, without a proven value-preserving wild-to-pet join.'},
            '2C': {'logical_bytes': 61, 'consumer_rva': '0xe6600',
                   'body_combat_dword_offsets_hex': ['0x2c', '0x30', '0x34', '0x38'],
                   'owner': 'receiving session role, via world+86888',
                   'limit': 'Battle forwarding keeps the same owner. Opponent PK stats are not revealed merely by appearing in battle.'}},
        'official_value_status': {
            'hp': 'DIRECT_RECEIVED_VALUE_IF_REAL_SESSION_LIFETIME_BOUND_86_0_EXISTS',
            'mp': 'RAW_RECEIVED_IF_PRESENT;SIDE1_ACTOR_UPDATE_UNSUPPORTED_FOR86_1',
            'level': 'RECEIVED_DISPLAY_LEVEL_ONLY',
            'four_dimensions': None, 'five_elements': None,
            'physical_and_magical_attack_defense': None,
            'observed_skill_pairs': 'LIFETIME_BOUND_INCOMING83_ASSOCIATIONS',
            'complete_carried_skill_list': None,
            'ai_permissions_conditions_probabilities': None},
        'requested_value_origin_classification': [
            {'requested': 'enemy_four_dimensions', 'classification': 'NOT_FOUND_IN_ENEMY_SENDER_PATH', 'values': None},
            {'requested': 'enemy_five_elements', 'classification': 'NOT_FOUND_IN_ENEMY_SENDER_PATH', 'values': None},
            {'requested': 'enemy_two_attacks_two_defenses', 'classification': 'NOT_FOUND_IN_ENEMY_SENDER_PATH', 'values': None,
             'original_owned_panel_labels': ['\u7269\u653b', '\u7269\u9632', '\u9b54\u653b', '\u9b54\u9632']},
            {'requested': 'enemy_HP', 'classification': 'DIRECT_RECEIVED86_0_IF_CAPTURED_AND_IDENTITY_BOUND', 'values': None},
            {'requested': 'enemy_MP', 'classification': 'RAW86_1_IF_PRESENT_BUT_NATIVE_SIDE1_APPLY_UNSUPPORTED', 'values': None},
            {'requested': 'enemy_observed_skill', 'classification': 'DIRECT_INCOMING83_PAIR_IF_CAPTURED_AND_IDENTITY_BOUND', 'values': None},
            {'requested': 'enemy_complete_carried_skills', 'classification': 'NO_AUTHORITATIVE_ENUMERATION_FOUND', 'values': None},
            {'requested': 'local_known_custom_fixture_values', 'classification': 'CONTROLLED_CUSTOM_ONLY_NOT_OFFICIAL', 'values': None}],
        'blackbox_plan': [
            'Use two CONTROLLED source-labelled actors; authoring known stats establishes experiment truth, never original truth.',
            'Compare the same controlled actor as side0 versus side1, preserving authored HP/MP and skill pairs; inspect actual copied memory and raw received records separately.',
            'Vary one four-dimension/element/attack/defense value with all other server inputs fixed. If no independent field is sent, outcomes only calibrate the custom rule, not an official server inverse.',
            'Compare source-authored repertoire before play versus cache after zero, one and repeated skill uses. Cache growth demonstrates observed use; no-use cannot demonstrate absent skill.',
            'Restore lifecycle binding on every1C replacement and battle/session boundary; reuse of packed position is not reuse of entity identity.',
            'Original official values require same-build actual received records or an authoritative source with identity join; keep absent fields null.'],
        'passive_observation_plan': [
            'Only record the users own authorized gameplay session, after native transport decode and before dispatcher writes; no credential collection or arbitrary requests.',
            'Store raw record plus current build hash, session/battle identity, monotonic record index, packet direction, received timestamp and participant lifecycle generation.',
            'Bind86 position+2 and83 position+2 to the latest valid1C position+1 generation in that battle. Preserve original variantWORD before115E47 mutation.',
            'Use exact source-versioned appearance namespace and branch/variant context; never merge by display name or art. Keep server template identity unknown unless independently proved.',
            'Store observed skill pair unions as lower-bound observations, separately from full repertoire; absence across encounters is not proof of absent skills.',
            'Do not infer four dimensions, five elements or damage coefficients from HP deltas without original formulas, rounding, buffs, resistance and randomness.'],
        'research_references': [
            'docs/research/current-monster-side-initialization-20260920.md',
            'docs/research/current-monster-other-identity-20260920.md',
            'docs/research/current-monster-variant-identity-20260920.md',
            'docs/research/current-battle-vitals-20260920.md',
            'docs/research/current-monster-skill-assignments-20260920.md',
            'docs/research/current-skill-selection-20260919.md',
            'docs/research/current-battle-learned-skills-20260920.md',
            'docs/research/current-monster-inspect-identity-20260920.md',
            'docs/research/current-attack-defense-producer-search-20260920.md',
            'docs/research/current-battle-speed-backtrace-20260920.md'],
    }


def main():
    root = Path(__file__).resolve().parents[2]
    target = root / 'artifacts/research/enemy-native-fields-20261006'
    target.mkdir(parents=True, exist_ok=True)
    report = build()
    output = target / 'static-native-map.json'
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(output), 'scope': report['scope'],
                      'native_spans': len(report['native_spans']),
                      'official_monster_stat_tuples_recovered': 0,
                      'native_execution': False}, ensure_ascii=True))


if __name__ == '__main__':
    main()
