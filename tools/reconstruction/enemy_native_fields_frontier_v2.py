"""Targeted static inspect/repertoire frontier, preserving the v1 evidence.

No native replay, UI, debugger, network, DB, test or source gameplay change.
"""
import hashlib
import json
import re
import struct
from pathlib import Path

import capstone
from capstone.x86_const import X86_OP_MEM

from tools.reconstruction.archive_inputs import ArchivedInputs
from tools.strike_lab.omega_assets import decode_csvz

IMAGE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
ROOT = Path(__file__).resolve().parents[2]
SPANS = {
    'own_role_cache_1c_gate_and_copy': (0x11634b, 0x11646c),
    'local_selector_getter': (0x11b8c0, 0x11b8fa),
    'actor_pool_initializer': (0x11fc40, 0x11fd30),
    'actor_fill_reset_prefix': (0x11fde0, 0x11fe15),
    'actor_explicit_skill_zeroing': (0x11ff12, 0x11ff2c),
    'all_sides_types_skill_reset': (0x120300, 0x1203b1),
    'skill_cache_render_coherence_reader': (0x1241a0, 0x124245),
    'selected_role_ui_request': (0x66229, 0x66283),
    'selected_role_request_producer6e': (0x97d40, 0x97d71),
    'pk_request8a_receiver': (0x6ad80, 0x6ae12),
    'pk_dialog_context_copy': (0x84620, 0x84707),
    'combat_label_string_parser_prefix': (0x11de40, 0x11debb),
    'combat_label_string_parser_stats': (0x11e1ae, 0x11e252),
    'combat_label_string_parser_render': (0x11e344, 0x11e3af),
}
TERMS = ['檢視', '偵察', '偵查', '探查', '圖鑑', '探知', '洞察', '觀察', '看破', '知己', '查看']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def selected_rows(raw):
    result, offset = [], 0
    for number, row in enumerate(raw.splitlines(keepends=True), 1):
        # Exact CP950 byte matches; Unicode replacement is not used to decide hits.
        matched = [term for term in TERMS if term.encode('cp950') in row]
        if matched:
            result.append({'line': number, 'offset': offset, 'row_sha256': sha(row),
                           'raw_hex': row.hex(), 'cp950_display': row.decode('cp950', 'replace'),
                           'keywords': matched, 'consumer_binding': None})
        offset += len(row)
    return result


def build():
    a = ArchivedInputs()
    try:
        image = a.read(IMAGE)
        sources = {
            name: a.read('artifacts/capture_work/host-20260918-1430/client/' + path)
            for name, path in {
                'message': 'Data2/Patch/Comm/message.csvZ',
                'gamedata': 'Data2/Patch/Comm/gamedata.csvZ',
                'skills': 'Data2/Fight/Spg/cbspec2.bin',
            }.items()}
    finally:
        a.close()
    if sha(image) != PIN:
        raise ValueError('Original mapped image differs')
    expected = {'message': '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
                'gamedata': '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
                'skills': '7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51'}
    for name, raw in sources.items():
        if sha(raw) != expected[name]:
            raise ValueError('Selected original source differs')
    decoded = {name: decode_csvz(sources[name]) for name in ('message', 'gamedata')}
    c = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans = {}
    for name, (lo, hi) in SPANS.items():
        spans[name] = {'start_rva': hex(lo), 'end_rva_exclusive': hex(hi),
                       'sha256': sha(image[lo:hi]), 'bytes_hex': image[lo:hi].hex(),
                       'instructions': [{'rva': hex(i.address), 'bytes': i.bytes.hex(),
                                         'mnemonic': i.mnemonic, 'operands': i.op_str}
                                        for i in c.disasm(image[lo:hi], lo)]}
    c.detail, c.skipdata = True, True
    candidates, skipped = [], 0
    # A direct displacement candidate sweep, not all-alias/global writer proof.
    for i in c.disasm(image[0x1000:0x170000], 0x1000):
        if not i.id:
            skipped += i.size
            continue
        matches = [{'disp': hex(o.mem.disp), 'base': i.reg_name(o.mem.base),
                    'index': i.reg_name(o.mem.index), 'width': o.size, 'access': o.access}
                   for o in i.operands if o.type == X86_OP_MEM and o.mem.disp in (0xdf8, 0xec4)]
        if matches:
            candidates.append({'rva': hex(i.address), 'bytes': i.bytes.hex(),
                               'mnemonic': i.mnemonic, 'operands': i.op_str, 'matches': matches,
                               'qualification': 'CANDIDATE_ONLY_OBJECT_PROVENANCE_REQUIRED'})
    labels = []
    for addr in (0x19cdf8, 0x19cdf0, 0x19cde8, 0x19cde0):
        end = image.index(0, addr)
        text = image[addr:end]
        refs = [hex(m.start() + 0x1000) for m in re.finditer(
            re.escape(struct.pack('<I', 0x400000 + addr)), image[0x1000:0x170000])]
        labels.append({'literal_rva': hex(addr), 'bytes_hex': text.hex(),
                       'original_cp950': text.decode('cp950'), 'literal_operand_candidates': refs})
    message_lines = []
    in_program = False
    offset = 0
    for number, row in enumerate(decoded['message'].splitlines(keepends=True), 1):
        if row.startswith(b'ProgramMsg,'):
            in_program = True
        if in_program and row.split(b',', 1)[0] in (b'222', b'666', b'696', b'733'):
            message_lines.append({'line': number, 'offset': offset, 'bytes_hex': row.hex(),
                                  'sha256': sha(row), 'text': row.decode('cp950').strip()})
        offset += len(row)
    return {
        'scope': 'STATIC_TARGETED_INSPECT_AND_REPERTOIRE_FRONTIER_V2',
        'v1_preserved': 'artifacts/research/enemy-native-fields-20261006/static-native-map.json',
        'image_pin': PIN, 'source_pins': expected,
        'execution': {'native_or_VM': False, 'network': False, 'client': False,
                      'tests': False, 'gameplay_source_mutation': False},
        'new_spans': spans,
        'cache_reference_candidates': {'range_rva': ['0x1000', '0x170000'],
                                       'exact_displacements': ['0xdf8', '0xec4'],
                                       'linear_skipdata_bytes': skipped, 'hits': candidates,
                                       'limit': 'Linear decoding can cross tables. Rebased writes, whole-copy aliases, vtables and indirectly obtained pointers are not exhaustively proved.'},
        'qualified_cache_paths': [
            {'path': '1C_SELF_PRIMARY_SKILLS_INIT', 'new_writer_rva': '0x11645c',
             'source': 'local selector B+A9DC198;11B8C0 accesses current bank pointers+CC',
             'destination': 'actor+DF8+4*i,i0..49',
             'gates': ['side BYTE==0 at11635F/116363', 'packetWORD+3==B+48 local ID at116369..116374', '1C variant kind==2000 at116210..116220'],
             'identity_class': 'LOCAL_MAIN_ACTOR_ONLY',
             'source_qualification': 'Existing local-selector data,not a new opponent skill-list packet',
             'unknown': 'No complete opponent/wild repertoire source established by this branch'},
            {'path': 'POOL_AND_ACTOR_RESET',
             'arena': 'M+A7FBDAC embedded pool with actor strideECC;11FC40 assigns pointer table then calls11FDE0',
             'actor_reset': '11FDFE fills ECC bytes CDCDCDCD;11FF12..11FF26 separately clear skills',
             'clear_all': '120339..120341 zero51ptr and current skill;all2sides x14slots x6types',
             'source_qualification': 'Client constructor/reset constants,not received skills or absent-enemy-skill proof'},
            {'path': 'ACTION_ASSOCIATION', 'writer_rva': '0x116dc1',
             'source_qualification': 'v1 incoming83 action3/17 pair remains observed association;not repeated here'},
            {'path': 'CURRENT_ACTION_CONSUMER', 'writer_rva': '0x12c7d2',
             'source_qualification': 'Selects already-associated definition pointer;not repertoire allocation'}],
        'inspect_and_pk_candidates': [
            {'candidate': 'Selected player UI interaction C2S6E',
             'producer_rva': '0x97d40', 'caller_rva': '0x66274',
             'request': 'logical9:opcode6E,selectorBYTE+1,opaque stack bytes+2..4,targetDWORD+5',
             'identity': 'world-role collection via FAC70;actor/NPC/monster namespaces kept separate',
             'response': 'S2C6E length5 itself dispatches default consume;no justified direct request-response join',
             'status': 'OPEN_SELECTOR_MEANING_AND_RESPONSE;not automatically inspect/scan'},
            {'candidate': 'S2C8A PK peer information', 'logical_bytes': 45,
             'consumer_rva': '0x6ad80', 'fields_used': ['DWORD+1', 'DWORD+5', 'NUL string+9', 'NUL string+25'],
             'destinations': ['worldUI+23D5B0 DWORD', 'worldUI+23D5B4 DWORD', 'worldUI+23D5B8 string', 'worldUI+23D5C8 string'],
             'message': 'ProgramMsg733 says %s wants toPK,agree?',
             'exclusion': 'This concrete path stores invitation/dialog context and strings,no13-field abilities or skill-count/list. Unread tail41..44 remains opaque,not padding or statistics.'},
            {'candidate': 'right-click inspection labels',
             'original_labels': message_lines,
             'exclusion': 'These original labels identify whisper target/cancel/close,not an enemy-stat inspect request. No global right-click absence claim.'},
            {'candidate': 'Original combat stat label xrefs', 'original_labels': labels,
             'consumer_rva': '0x11de40',
             'exclusion': '11E1AE..11E252 compares text tokens and chooses glyph style IDs28..31;11E387 calls1F040 renderer. It does not read enemy base-stat fields. Raw name match is not a capability producer.'}],
        'lexical_targeting': {
            'terms': TERMS, 'exact_pinned_message_hits': selected_rows(decoded['message']),
            'exact_pinned_gamedata_hits': selected_rows(decoded['gamedata']),
            'skill_binary_exact_term_offsets': {term: [m.start() for m in re.finditer(
                re.escape(term.encode('cp950')), sources['skills'])] for term in TERMS},
            'limit': 'Scoped label/name search only. Art-embedded labels, synonymous features, other resources and runtime-generated text remain OPEN. Matching NPC name or quest item does not create scan producer.'},
        'requested_original_enemy_values': {
            'four_dimensions': None, 'five_elements': None, 'two_attacks_two_defenses': None,
            'complete_carried_skills': None, 'authoritative_monster_definition_join': None},
        'per_requested_enemy_field': [
            {'original_label': name, 'value': None, 'packet_offset': None,
             'enemy_actor_offset': None, 'enemy_memory_writer': None,
             'classification': 'UNKNOWN_ENEMY_PRODUCER_NOT_QUALIFIED',
             'not_a_substitute': excluded}
            for name, excluded in [
                ('物攻', 'Owned pet2FB body10hex/current role2C/card additions/text glyphs are different proven owners'),
                ('魔攻', 'Owned pet2FB body14hex/current role2C/card additions/text glyphs are different proven owners'),
                ('物防', 'Owned pet2FB body12hex/current role2C/card additions/text glyphs are different proven owners'),
                ('魔防', 'Owned pet2FB body16hex/current role2C/card additions/text glyphs are different proven owners'),
                ('力', 'Owned pet2FB body24hex/owned companion/role fields have no enemy-value join'),
                ('體', 'Owned pet2FB body26hex/owned companion/role fields have no enemy-value join'),
                ('智', 'Owned pet2FB body28hex/owned companion/role fields have no enemy-value join'),
                ('速', 'Owned pet2FB body2Ahex/owned companion/role fields;action order is not a proven numeric inverse'),
                ('金', 'Owned pet2FB body18hex/card additions/skill attribute labels are not wild elemental values'),
                ('木', 'Owned pet2FB body1Ahex/card additions/skill attribute labels are not wild elemental values'),
                ('水', 'Owned pet2FB body1Chex/card additions/skill attribute labels are not wild elemental values'),
                ('火', 'Owned pet2FB body1Ehex/card additions/skill attribute labels are not wild elemental values'),
                ('土', 'Owned pet2FB body20hex/card additions/skill attribute labels are not wild elemental values')]],
        'next_edges': [
            'Trace C2S6E selector/action registrations and exact server response using controlled own-client captures;do not invent6E->stat response.',
            'Observe battle hover/other context-menu events and exact newly received records on controlled own server;art labels alone are not sufficient.',
            'Follow all rebased whole-actor copies and vtable/indirect aliases if new pointer provenance evidence appears;the exact-disp sweep is not complete all-writer coverage.',
            'Original full repertoire remains dependent on actual authoritative sender/source or a directly observed enumeration,independent from local self-selector bootstrap.',
            'Owned pet2/card/role fields stay separate until a wild-to-owned conversion and value-preservation join is independently proved.']}


def main():
    report = build()
    path = ROOT / 'artifacts/research/enemy-native-fields-20261006/frontier-v2.json'
    path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(path), 'new_spans': len(report['new_spans']),
                      'cache_candidates': len(report['cache_reference_candidates']['hits']),
                      'new_original_enemy_values': 0}, ensure_ascii=True))


if __name__ == '__main__':
    main()
