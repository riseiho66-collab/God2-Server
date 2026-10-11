"""Inventory current-original combat evidence; never evaluate server rules.

Read-only inputs and JSON on stdout. No legacy corpus, database, game process,
network, graphics, runtime mutation, or generated artifact is required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .current_skill_identity import decode_definitions
from .omega_assets import decode_csvz
from .recover_combat_skills import parse_skills

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SKILLS = 'Data2/Patch/Comm/gamedata.csvZ'
EFFECTS = 'Data2/Patch/Comm/ChangeDollEffect.csvZ'
IDENTITIES = 'Data2/Fight/Spg/cbspec2.bin'
SOURCE_HASHES = {
    SKILLS: '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
    EFFECTS: '535a1c1a690e7f78be7d6e27cf8d212e89ed5230e5c7213c0e4fbe1d3a7d8ef1',
    IDENTITIES: '7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51',
}
MAX_BYTES = 64 * 1024 * 1024
RULES = ('damage', 'hit', 'crit', 'five_element_coefficients', 'resource_cost')
# Search labels only: these do not interpret numeric columns or stacking rules.
DESCRIPTION_TERMS = {
    'damage': ('\u50b7\u5bb3',),
    'hit': ('\u547d\u4e2d',),
    'crit': ('\u66b4\u64ca', '\u7206\u64ca', '\u6703\u5fc3'),
    'five_element_coefficients': ('\u91d1\u5c6c\u6027', '\u6728\u5c6c\u6027',
                                  '\u6c34\u5c6c\u6027', '\u706b\u5c6c\u6027',
                                  '\u571f\u5c6c\u6027', '\u4e94\u884c'),
    'resource_cost': ('\u6d88\u8017', 'mp'),
}

# End RVAs are exclusive. These are mapped-image offsets, not PE file offsets.
NATIVE_SLICES = (
    ('display_scale', 0x108e70, 0x108f48,
     '09157fd5b0162b966b551c07d5b69e7f05847207c6997ca90189ddb2047c3c52',
     'display_arithmetic',
     '108EAB/108F0F load zero-extended DWORD numerators with FILD qword; '
     '108EC1/108F1F multiply by signed WORD width at record+A7A4; '
     '108ECD/108F23 divide by signed DWORD at A7A8/A7AC. '
     '149630 truncates; EAX becomes an extent passed to 1BDC0. '
     'No zero-divisor guard in this slice. No HP/MP field identity asserted.'),
    ('display_clamp', 0x108f50, 0x108fb1,
     '390ccd500da18e3bec4b58ff81d9515dc3c8430593948e30b9f949d07b0f8c13',
     'display_arithmetic',
     'Low WORD handle must be below 1000h; high WORD ignored. '
     'Record = this+1Ch+(handle & FFFFh)*A7E0h. '
     'A7B0=min_unsigned(arg2,A7A8); A7B4=min_unsigned(arg3,A7AC); '
     'then calls 108E70. This clamps display inputs, not server damage.'),
    ('display_divisors', 0x108fc0, 0x108ffe,
     'a762c17f1641215c7c6f61e552d7325e794e8fc8d294224d1a1b9ef0a1281774',
     'display_state',
     'Same handle/record calculation; copies supplied DWORDs into A7A8/A7AC '
     'and calls 108E70. Supplied values are not computed combat formulas.'),
    ('truncate_x87', 0x149630, 0x149657,
     'd0a2aca68648a0ae9d5cbfae1b276d4a64d4f797fc0c60f28b64096cdfa3148c',
     'numeric_conversion',
     'Saves x87 control word, ORs AH with 0Ch for truncation, FISTP qword, '
     'restores control word, returns EDX:EAX. Not a server rounding rule.'),
    ('supplied_value_caller', 0x1173a0, 0x117472,
     '6239c4b7175d313bda46166704cb7b507d3901c7d95706173cdc5b73a80daf80',
     'supplied_result_path',
     '1173F9/1173FC load caller-buffer DWORDs +5/+9, passed to 12D970 '
     'at 11740A. Buffer+2 is split by 14 for addressing. '
     'Dispatch opcode, buffer provenance and HP/MP meanings remain unproved.'),
    ('supplied_value_consumer', 0x12d970, 0x12d9e5,
     '5d1ed07aaedeec218a3c890f68a59adf3fcf711998efbb6c3ed4d1a93546d261',
     'supplied_result_path',
     'After 11E6E0 lookup, stores supplied DWORDs at actor+DEC/DF4. '
     'Calls display divisor setter 108FC0 at 12D9BE and display clamp '
     '108F50 at 12D9DB; no damage computation established.'),
    ('supplied_companion_consumer', 0x12d840, 0x12d8b5,
     'c3d5d8a6a016118515ea33a9cd375b6c33ec59f38cb5a90e7d4f2e20ac793fa3',
     'supplied_result_path',
     'Stores supplied DWORDs at actor+DE8/DF0; calls 108FC0 at 12D88E '
     'and 108F50 at 12D8AB. No stat-to-damage transformation proved.'),
    ('selection_producer', 0x11c520, 0x11c7bf,
     'f07f20f890df718aee5d4cfd5fce0c3924bf27f5db10414ee597e8b5f908c64f',
     'identity_only',
     'Existing current_skill_identity recovery: selection pointer from '
     'cbspec2 (kind, ID), not skill-book item ID or cost.'),
    ('selected_command_identity', 0x11913d, 0x11914f,
     '1b4ad92cc98999440dbb468c44726d590904a7f45d1c0e7741d337234f6ea2c2',
     'identity_only',
     'Copies selected entry byte 0 into CL and kind into CH. '
     'Command packing is not resource deduction or skill damage arithmetic.'),
)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def serialize(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n'


def read_pinned(path, expected):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Input exceeds recovery bound')
    if sha256(raw) != expected:
        raise ValueError('Current-original source SHA-256 mismatch: ' + str(path))
    return raw


def raw_evidence(raw, offset, **metadata):
    return {**metadata, 'offset': offset, 'length': len(raw),
            'raw_hex': raw.hex(), 'sha256': sha256(raw)}


def text_rows(decoded):
    offset = 0
    for line, encoded in enumerate(decoded.splitlines(keepends=True), 1):
        raw = encoded.rstrip(b'\r\n')
        yield raw_evidence(raw, offset, line=line,
                           fields=[v.decode('cp950') for v in raw.split(b',')])
        offset += len(encoded)


def matched_categories(text):
    lowered = text.lower()
    return [name for name in RULES
            if any(term in lowered for term in DESCRIPTION_TERMS[name])]


def parse_effects(decoded):
    """Preserve all card-effect rows, not monster stats or executable rules."""
    rows = list(text_rows(decoded))
    expected_header = ['Index', '\u985e\u578b\u5340\u5225',
                       '\u7279\u6b8a\u80fd\u529b\u4ee3\u78bc',
                       '\u57fa\u672c\u503c', '\u7279\u6b8a\u80fd\u529b\u8aaa\u660e']
    if len(rows) < 5 or rows[2]['fields'] != expected_header:
        raise ValueError('Unsupported current effect header')
    marker = rows[3]['fields']
    if (len(marker) != 2 or marker[0] != 'ChangeDollEffectCount'
            or not re.fullmatch(r'[0-9]+', marker[1])):
        raise ValueError('Invalid current effect count')
    count = int(marker[1])
    if not 0 < count <= 65535 or len(rows) != count + 4:
        raise ValueError('Effect count mismatch or truncated source')
    seen = set()
    for row in rows[4:]:
        fields = row['fields']
        if len(fields) != 5 or not re.fullmatch(r'[0-9]+', fields[0]):
            raise ValueError('Invalid current effect row')
        identity = int(fields[0])
        if identity in seen:
            raise ValueError('Duplicate effect index')
        seen.add(identity)
        row.update(index=identity, authority='description_only',
                   description_column=4, matched_categories=matched_categories(fields[4]))
    return {'header': rows[2], 'marker': rows[3], 'records': rows[4:],
            'declared_records': count,
            'numeric_column_policy': 'Columns 1 and 3 stay raw; no units, rates or divisors inferred.'}


def native_evidence(image):
    if sha256(image) != IMAGE_SHA256:
        raise ValueError('Current-original mapped image SHA-256 mismatch')
    result = []
    for name, start, end, expected, authority, observation in NATIVE_SLICES:
        raw = image[start:end]
        if sha256(raw) != expected:
            raise ValueError('Native evidence slice changed: ' + name)
        result.append(raw_evidence(raw, start, id=name, rva_start=start,
                                   rva_end_exclusive=end, authority=authority,
                                   observation=observation))
    return result


def build_inventory(client_root=CLIENT, image_path=IMAGE):
    root = Path(client_root).resolve()
    sources, inputs = {}, {}
    for relative, expected in SOURCE_HASHES.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Current source escapes client root')
        raw = read_pinned(path, expected)
        inputs[relative] = decode_csvz(raw) if relative.endswith('.csvZ') else raw
        sources[relative] = {'sha256': expected, 'bytes': len(raw),
                             'decoded_sha256': sha256(inputs[relative]),
                             'decoded_bytes': len(inputs[relative])}
    image = read_pinned(image_path, IMAGE_SHA256)
    sources['mapped_image'] = {'sha256': IMAGE_SHA256, 'bytes': len(image),
                               'layout': 'mapped image; offset equals RVA; base VA 00400000'}
    # Reuse only the current-table parser, never its separate catalog builder.
    skills = parse_skills(inputs[SKILLS])
    for row in skills['definitions']:
        row['authority'] = 'description_only'
        row['matched_categories'] = matched_categories(' '.join(row['fields'][7:13]))
        claim = row['description_claims'].get('mp_cost')
        row['displayed_mp_cost'] = None if claim is None else claim['value']
        row['server_resource_cost'] = None
    effects = parse_effects(inputs[EFFECTS])
    identities = [raw_evidence(value.raw, value.source_offset,
                                id=value.id, kind=value.kind, authority='identity_only')
                  for _, value in sorted(decode_definitions(inputs[IDENTITIES]).items())]
    native = native_evidence(image)
    rules = []
    for name in RULES:
        books = [row['item_id'] for row in skills['definitions']
                 if name in row['matched_categories']]
        effect_ids = [row['index'] for row in effects['records']
                      if name in row['matched_categories']]
        rules.append({'id': name, 'status': 'unknown', 'server_formula': None,
                      'server_coefficients': None, 'runtime_enabled': False,
                      'skill_book_description_ids': books,
                      'card_effect_description_indices': effect_ids,
                      'description_search_terms': list(DESCRIPTION_TERMS[name]),
                      'native_evidence_ids': ([row['id'] for row in native]
                                              if name in ('damage', 'resource_cost') else []),
                      'boundary': 'Descriptions, identity and supplied/display values do not prove this server rule.'})
    return {
        'schema_version': 1, 'scope': 'current_original_client_only',
        'sources': sources, 'rules': rules, 'skill_books': skills,
        'card_effects': effects, 'selection_definitions': identities,
        'native_evidence': native,
        'indexing': 'Lines one-based; columns/offsets/RVAs zero-based; table offsets refer to decoded bytes.',
        'counts': {'skill_books': len(skills['definitions']),
                   'displayed_mp_costs': sum(row['displayed_mp_cost'] is not None
                                             for row in skills['definitions']),
                   'card_effects': len(effects['records']),
                   'selection_definitions': len(identities),
                   'native_slices': len(native), 'recovered_server_formulas': 0},
        'unknowns': [
            'Damage: attack/defense transformation, minimum, randomness, rounding, caps and stacking.',
            'Hit: probability, evasion, state hit, random source and comparison boundaries.',
            'Crit: trigger probability, multiplier, stacking and result-flag semantics.',
            'Five elements: authoritative coefficient table, order and stat-to-modifier mapping.',
            'Resources: actual deduction, timing, refunds, HP/item costs and server validation.',
            'No proved skill-book item ID to cbspec2 selection identity mapping.',
            'No proved dispatch/packet provenance or HP/MP labels for supplied-value display path.',
            'Description searches are bounded clues, not exhaustive proof of absence of formulas.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, default=CLIENT)
    parser.add_argument('--image', type=Path, default=IMAGE)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    inventory = build_inventory(args.client_root, args.image)
    if args.summary:
        print(serialize({'scope': inventory['scope'], 'counts': inventory['counts'],
                         'inventory_sha256': sha256(serialize(inventory).encode('ascii')),
                         'rules': {row['id']: row['status'] for row in inventory['rules']}}), end='')
    else:
        print(serialize(inventory), end='')


if __name__ == '__main__':
    main()
