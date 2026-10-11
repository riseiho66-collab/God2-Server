"""Pinned role-growth evidence extraction, not a gameplay implementation."""
import argparse
import json
from pathlib import Path
import re
import struct
import sys

from .omega_assets import decode_csvz
from .recover_companions import digest, parse_sections, read_source, record, serialize

GAME = 'Data2/Patch/Comm/gamedata.csvZ'
MESSAGES = 'Data2/Patch/Comm/message.csvZ'
CLIENT_SHA256 = {
    GAME: '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
    MESSAGES: '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
    'God2Con.csvZ': '8a498103d8a391ac80d49c16572c1140c485f3fcd48a8ec7798ce00cac9284fe',
    'God2Con2.csvZ': '576cda6b3a4712ac583141d0bc79feeddb565fbb9675cb2d99e654157e058fc7',
    'Data2/Client.csvZ': '7ba020c3963bbd20dfdca89f05cd2d9b08c16c0e796f43850dd46e1fc1fa4f93',
    'Data/Patch/God.csvZ': 'fa6673ce89374d135d3109bb1381a1fb0755b18f898af3988f34e1995ad8af44',
    'Data/Patch/Skill.csvZ': '1dc049cb4ac19fd753c17af64932c40f4e833a1dac92a8d0d33a44529a9a7e16',
}
IMAGE_RELATIVE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
DEFAULT_IMAGE = Path(__file__).resolve().parents[2] / IMAGE_RELATIVE
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
NATIVE_SPANS = {
    's2c22_length': (0x1258, 0x125e),
    's2c2b_length': (0x127c, 0x1282),
    's2c22_dispatch_entry': (0x6b65c, 0x6b660),
    's2c2b_dispatch_entry': (0x6b680, 0x6b684),
    's2c22_dispatch': (0x69ef0, 0x69f02),
    's2c2b_dispatch': (0x69eb0, 0x69ecc),
    's2c22_scalar_prefix': (0xe6b40, 0xe6bd4),
    's2c2b_scalar_prefix': (0xe6390, 0xe63c5),
    'exp_display_arithmetic_prefix': (0xe6c90, 0xe6cd1),
    'exp_display_message_lookup': (0xe6ce1, 0xe6cfe),
    'exp_display_formatter_arguments': (0xe6d02, 0xe6d25),
    'exp_display_scale_f32': (0x171204, 0x171208),
}
MESSAGE_IDS = {
    'SystemMessage': (330, 331, 332, 333, 334, 335, 336, 337, 623, 624,
                      644, 645, 840, 844, 1548, 1585, 1746, 1898, 1899, 1900, 1901),
    'ProgramMsg': (58, 84, 162, 215, 295, 907, 927, 930),
}
UNKNOWN_RULES = (
    'role_exp_requirements', 'exp_total_or_per_level', 'exp_rounding_and_overflow',
    'exp_award_modifiers', 'level_transition', 'level_cap_and_unlocks',
    'rebirth_and_class_modifiers', 'birth_hp_mp_attributes', 'hp_growth', 'mp_growth',
    'automatic_attribute_growth', 'manual_attribute_points',
    'attribute_to_hp_mp_conversion', 'stat_rounding_and_clamping',
)


def pinned_source(root, relative, expected):
    raw = read_source(root, relative)
    if digest(raw) != expected:
        raise ValueError('Source SHA-256 changed; re-audit required: ' + relative)
    return raw


def source_record(raw):
    return {'sha256': digest(raw), 'size': len(raw)}


def line_records(raw):
    # LF alone defines a physical record; CR bytes and all trailing fields survive.
    offset = 0
    for number, part in enumerate(raw.split(b'\n'), 1):
        if offset == len(raw):
            break
        line = part + (b'\n' if offset + len(part) < len(raw) else b'')
        yield number, offset, line
        offset += len(line)


def native_evidence(image_path):
    path = Path(image_path)
    raw = pinned_source(path.parent, path.name, IMAGE_SHA256)
    spans = {}
    for label, (start, end) in NATIVE_SPANS.items():
        data = raw[start:end]
        spans[label] = {'rva': start, 'file_offset': start, 'raw_hex': data.hex(),
                        **source_record(data)}
    return {
        'source': {**source_record(raw), 'capture_name': Path(IMAGE_RELATIVE).name,
                   'layout': 'mapped PE image; file offset equals RVA', 'image_base': 0x400000},
        'evidence_class': 'current_original_native_static_bytes',
        'runtime_verified': False, 'runtime_eligible': False,
        'spans': spans,
        'display_consumer_rva': 0xe6c90,
        'display_input': {'actor_offset': 0x58, 'width': 2, 'signed': False},
        'display_scale': {'source_rva': 0x171204, 'raw_hex': raw[0x171204:0x171208].hex(),
                          'float32_value': struct.unpack_from('<f', raw, 0x171204)[0]},
        'message_binding': {'source_file': MESSAGES, 'section': 'ProgramMsg', 'id': 162},
        'qualification': 'Static display path only. Offline native tests do not verify original server growth.',
    }


def build_role_growth(client_root, native_image=DEFAULT_IMAGE):
    sources, decoded, marker_inventory = {}, {}, {}
    for relative, expected in sorted(CLIENT_SHA256.items()):
        raw = pinned_source(client_root, relative, expected)
        plain = decode_csvz(raw)
        sources[relative] = {**source_record(raw), 'decoded_sha256': digest(plain),
                             'decoded_size': len(plain)}
        decoded[relative] = plain
        # Lexical candidates only: e.g. Quickkm and EnyName subheaders also match.
        marker_inventory[relative] = [record(line, number, offset)
            for number, offset, line in line_records(plain)
            if re.match(rb'^[A-Za-z][A-Za-z0-9_]*,[0-9]+(?:,|\r|\n|$)', line)]

    tables = parse_sections(decoded[GAME], ('InitSettingMacro', 'GodLevel'))
    for table in tables.values():
        table.update(source_file=GAME, evidence_class='current_client_opaque_table',
                     runtime_verified=False, runtime_eligible=False,
                     field_semantics=None)
    messages = {}
    for name, table in parse_sections(decoded[MESSAGES], tuple(MESSAGE_IDS)).items():
        rows = []
        for message_id in MESSAGE_IDS[name]:
            matches = [row for row in table['records']
                       if row['fields_hex'][0] == str(message_id).encode('ascii').hex()]
            if len(matches) != 1:
                raise ValueError('Missing or duplicate message: ' + str(message_id))
            rows.append(matches[0])
        messages[name] = {
            'source_file': MESSAGES, 'header': table['header'],
            'source_declared_count': table['declared_count'], 'selected_ids': list(MESSAGE_IDS[name]),
            'records': rows, 'evidence_class': 'current_client_display_text_only',
            'runtime_verified': False, 'runtime_eligible': False,
            'trigger_consumer': None,
        }

    return {
        'schema': 'god2-role-growth-evidence-v1',
        'scope': 'Pinned static sources only; no original server growth rule established.',
        'runtime_verified': False, 'runtime_eligible': False,
        'sources': sources, 'lexical_marker_inventory': marker_inventory,
        'opaque_tables': tables, 'display_evidence': messages,
        'native_display_evidence': native_evidence(native_image),
        'original_server_rules': {name: {
            'status': 'unknown', 'value': None, 'runtime_verified': False,
            'runtime_eligible': False,
            'reason': 'No original rule/consumer or causal server sample established in this audit.',
        } for name in UNKNOWN_RULES},
        'native_exp_table_audit': {
            'status': 'not_identified_in_bounded_audit', 'rows': None,
            'single_level_thresholds': {'status': 'unknown', 'value': None,
                'reason': 'Inspected native paths copy a packet WORD to actor+0x58; no next-level EXP threshold lookup identified.'},
            'cumulative_thresholds': {'status': 'unknown', 'value': None,
                'reason': 'No total-EXP accumulator, prefix-sum table or total-to-level lookup established.'},
            'cap': {'status': 'unknown', 'value': None,
                'reason': 'WORD width and percent formatting do not establish a level cap; message 927 is display text only.'},
            'growth_consumer_rva': None,
            'scope': 'Selected current CSVZ sources and pinned native packet/scalar/display spans. Not proof of global table absence.',
        },
        'policy': [
            'Unknown is null, never numeric zero. Empty recovered-rule coverage is not a zero-valued rule.',
            'Physical lines are one-based; offsets and fields are zero-based. CSV offsets address decoded bytes.',
            'CP950 is display only. Raw record bytes, hashes and positional fields are authoritative.',
            'GodLevel is preserved as four opaque name/value rows, not a role EXP or growth table.',
            'Message numbers and embedded display values do not prove caps, formulas or runtime behavior.',
            'Lexical marker inventory is not an exhaustive search for hidden or server-only rules.',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', required=True, type=Path)
    parser.add_argument('--native-image', type=Path, default=DEFAULT_IMAGE)
    parser.add_argument('--output', type=Path, help='Default: ASCII JSON on stdout')
    parser.add_argument('--check', action='store_true', help='Compare --output without writing')
    args = parser.parse_args(argv)
    if args.check and args.output is None:
        parser.error('--check requires --output')
    if args.output is not None:
        target = args.output.resolve()
        if target.is_relative_to(args.client_root.resolve()) or target == args.native_image.resolve():
            parser.error('Output must not overwrite client sources or native image')
    result = serialize(build_role_growth(args.client_root, args.native_image))
    if args.output is None:
        sys.stdout.buffer.write(result)
    elif args.check:
        if args.output.read_bytes() != result:
            raise SystemExit('Artifact differs')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(result)
    if args.output is not None:
        print(json.dumps({'sha256': digest(result), 'checked': args.check,
                          'original_server_rules_established': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
