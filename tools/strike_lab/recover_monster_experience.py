"""Bounded current-original EXP evidence; stdout JSON, no runtime integration.

Run as python -B -m tools.strike_lab.recover_monster_experience --client PATH
--image PATH. No other evidence roots are accepted or read.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from .omega_assets import decode_csvz


IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CLIENT_SHA256 = {
    'Data2/Patch/Comm/gamedata.csvZ': '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
    'Data2/Patch/Comm/message.csvZ': '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
    'Data2/Patch/eny.csvZ': '6aa84aeb0399e39e0db27eeebf9bb0f8b274fcbd609e1b83be3542a5d53f294c',
    'Data2/Patch/FightEny.csvZ': '887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a',
}
LIMIT = 16 * 1024 * 1024
BASE = 0x400000
UNKNOWN = (
    'monster_base_exp_table', 'monster_base_exp', 'current_monster_identity_binding',
    'player_level_difference_penalty', 'party_split', 'event_multiplier',
    'item_multiplier', 'modifier_stacking_order', 'rounding_and_clamping',
    'received_reward_to_persistent_xp', 'player_xp_thresholds', 'pet_xp_thresholds',
    'companion_xp_thresholds', 'pet_and_cave_split_rule',
)
# RVA equals byte offset in this pinned mapped image. Ends are exclusive.
NATIVE_SPANS = {
    'size_dispatch': (0x1209, 0x1216),
    'opcode_89_size_entry': (0x1548, 0x154c),
    'size_return': (0x1240, 0x1246),
    'receive_dispatch': (0x1193c4, 0x1193e7),
    'receive_map_89': (0x119a8d, 0x119a8e),
    'receive_target_24': (0x119968, 0x11996c),
    'receive_queue_call': (0x1195cc, 0x1195ea),
    'queue_dispatch': (0x114332, 0x114358),
    'queue_map_89': (0x1146c9, 0x1146ca),
    'queue_target_8': (0x114654, 0x114658),
    'consumer_call': (0x114597, 0x11459f),
    'message_binding_loop': (0x11125f, 0x1112a5),
    'message_id_array': (0x19be68, 0x19be7c),
    'consumer': (0x118bf0, 0x118e3a),
    'consumer_branch_table': (0x118e3c, 0x118e4c),
    'format_call_prefix': (0x852b0, 0x852cf),
}
DISPLAY_FIELDS = (
    ('character_received_exp_display', (5,), 295, 0x1b8b50, 0x118c6f, 0x118c82),
    ('companion_received_exp_display', (9,), 296, 0x1b8b54, 0x118c87, 0x118c9a),
    ('pet_cave_received_exp_display', (13, 53), 297, 0x1b8b58, 0x118c9f, 0x118cb6),
)
MESSAGE_SELECTION = {
    'ProgramMsg': (295, 296, 297),
    'SystemMessage': (512, 513, 1480, 1521, 1645),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned_read(path, expected):
    with Path(path).open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Input exceeds bounded source size')
    if digest(raw) != expected:
        raise ValueError('Source SHA-256 changed; re-audit required: ' + str(path))
    return raw


def records(raw):
    """Physical LF records with exact CRLF and byte offsets preserved."""
    offset = 0
    for number, line in enumerate(raw.split(b'\n'), 1):
        if offset == len(raw):
            break
        line += b'\n' if offset + len(line) < len(raw) else b''
        yield {'line': number, 'offset': offset, 'size': len(line),
               'sha256': digest(line), 'raw_hex': line.hex()}
        offset += len(line)


def fields(row):
    return bytes.fromhex(row['raw_hex']).rstrip(b'\r\n').split(b',')


def message_rows(plain):
    rows = list(records(plain))
    selected = {}
    for section, wanted in MESSAGE_SELECTION.items():
        headers = [i for i, row in enumerate(rows)
                   if fields(row)[0] == section.encode('ascii')]
        if len(headers) != 1:
            raise ValueError('Missing or duplicate message section')
        start = headers[0]
        count = int(fields(rows[start])[1])
        if start + count >= len(rows):
            raise ValueError('Truncated message section')
        found = {}
        for row in rows[start + 1:start + 1 + count]:
            columns = fields(row)
            identity = int(columns[0])
            if identity in wanted:
                if identity in found:
                    raise ValueError('Duplicate selected message')
                found[identity] = {**row, 'id': identity,
                    'fields_hex': [column.hex() for column in columns],
                    'text_cp950': columns[-1].decode('cp950'),
                    'authority': 'current_client_display_text'}
        if set(found) != set(wanted):
            raise ValueError('Missing selected message')
        selected[section] = {'header': rows[start], 'declared_count': count,
                             'records': [found[i] for i in wanted]}
    return selected


def native_evidence(image):
    if digest(image) != IMAGE_SHA256:
        raise ValueError('Pinned current image changed')
    spans = {name: {'rva_start': start, 'rva_end_exclusive': end,
                   'raw_hex': image[start:end].hex(), 'sha256': digest(image[start:end])}
             for name, (start, end) in NATIVE_SPANS.items()}
    ids = struct.unpack_from('<10H', image, 0x19be68)
    return {
        'base': BASE, 'rva_equals_file_offset': True,
        'instruction_spans': spans, 'message_ids': list(ids),
        'opcode': 0x89, 'logical_record_size': 57,
        'receive_map_index': image[0x119a04 + 0x89],
        'receive_handler_rva': struct.unpack_from('<I', image, 0x119908 + 24 * 4)[0] - BASE,
        'queue_map_index': image[0x11465c + 0x89 - 0x1c],
        'queue_handler_rva': struct.unpack_from('<I', image, 0x114634 + 8 * 4)[0] - BASE,
        'consumer_rva': 0x118bf0, 'branch_selector_record_offset': 49,
        'display_fields': [
            {'meaning': meaning, 'record_offsets': list(offsets), 'width_each': 4,
             'program_message_id': mid, 'format_global_rva': global_rva,
             'load_rva': start, 'format_call_rva': call,
             'numeric_format': '%d', 'server_award_formula': None}
            for meaning, offsets, mid, global_rva, start, call in DISPLAY_FIELDS],
        'boundary': 'Packet/display consumer only; no monster base EXP or XP threshold authority.',
    }


def build_evidence(client, image_path):
    root = Path(client).resolve()
    sources, decoded = {}, {}
    for relative, expected in sorted(CLIENT_SHA256.items()):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Source escapes client root')
        raw = pinned_read(path, expected)
        plain = decode_csvz(raw)
        sources[relative] = {'path': path.as_posix(), 'sha256': digest(raw),
            'size': len(raw), 'decoded_sha256': digest(plain), 'decoded_size': len(plain)}
        decoded[relative] = plain
    image_path = Path(image_path).resolve()
    image = pinned_read(image_path, IMAGE_SHA256)
    sources['image'] = {'path': image_path.as_posix(), 'sha256': digest(image), 'size': len(image)}
    definitions = []
    for relative in ('Data2/Patch/eny.csvZ', 'Data2/Patch/FightEny.csvZ'):
        rows = list(records(decoded[relative]))
        start = int(fields(rows[0])[2]) - 1
        definitions.append({'source': relative, 'header': rows[start - 1],
            'record_count': sum(bool(bytes.fromhex(r['raw_hex']).strip()) for r in rows[start:]),
            'authority': 'visual_definition_only', 'monster_base_exp': None,
            'monster_identity_binding': None})
    game_rows = list(records(decoded['Data2/Patch/Comm/gamedata.csvZ']))
    markers = [row for row in game_rows if re.match(
        rb'^[A-Za-z][A-Za-z0-9_]*,[0-9]+(?:,|\r|\n|$)', bytes.fromhex(row['raw_hex']))]
    return {
        'schema': 'god2-current-monster-experience-evidence-v1',
        'sources': sources, 'native': native_evidence(image),
        'messages': message_rows(decoded['Data2/Patch/Comm/message.csvZ']),
        'visual_definition_audit': definitions,
        'gamedata_marker_inventory': {'authority': 'lexical_markers_only_no_numeric_semantics',
                                      'records': markers},
        'monster_awarded_experience_records': [],
        'proven_monster_base_exp_record_count': 0,
        'unknowns': {name: None for name in UNKNOWN},
        'runtime_eligible': False,
        'scope': 'Four pinned current CSVZ files and one pinned current mapped image only. '
                 'No exhaustive absence claim. Empty evidence is not zero EXP. '
                 'No visual, card, PET, or enemy identity joins. '
                 'Received display values are not base/credited stages or level thresholds.',
    }


def serialize(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    args = parser.parse_args(argv)
    print(serialize(build_evidence(args.client, args.image)), end='')


if __name__ == '__main__':
    main()
