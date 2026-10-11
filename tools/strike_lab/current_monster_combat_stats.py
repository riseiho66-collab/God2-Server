"""Current-only lane B coverage and native ChangeDollCard authority boundary.

Read-only sources, offline x86 execution, JSON stdout. Card values are never
promoted to wild-monster stats. Inventory keys retain source allocation identity.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

from .omega_assets import decode_csvz
from .current_monster_inventory import pinned_catalog

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CARD = 'Data2/Patch/Comm/ChangeDollCard.csvZ'
GAME = 'Data2/Patch/Comm/gamedata.csvZ'
PINS = {
    CARD: ('4d51b22d51c14bc98b6ec96c16a40384a226e9fa1f90543ea58a36fb4b56ebd2',
           '0f04cc27292e4b3bc08c030dce8b2564e2fad52bf0d87f227414d63f4ca6acef'),
    GAME: ('70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
           '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'),
}
# name: zero-based source column, record offset, native store, signed display read.
FIELDS = {
    'physical_attack': (10, 0x16, 0x5bd02, 0xbae27),
    'physical_defense': (11, 0x18, 0x5bd20, 0xbaeb9),
    'magical_attack': (12, 0x1a, 0x5bd3e, 0xbafac),
    'magical_defense': (13, 0x1c, 0x5bd5c, 0xbb09b),
    'metal': (18, 0x26, 0x5bdf2, 0xbb172),
    'wood': (19, 0x28, 0x5be10, 0xbb203),
    'water': (20, 0x2a, 0x5be2e, 0xbb2f5),
    'fire': (21, 0x2c, 0x5be4c, 0xbb3e6),
    'earth': (22, 0x2e, 0x5be68, 0xbb4d0),
}
FORMAT_CALLS = dict(zip(FIELDS, (0xbae40, 0xbaed2, 0xbafc5, 0xbb0b4,
                               0xbb18b, 0xbb21c, 0xbb30e, 0xbb3ff, 0xbb4e9)))
SLICES = {
    'header_dispatch': (0x56e3a, 0x56e85),
    'card_loader': (0x5bb10, 0x5bea7),
    'tokenizer': (0x51be0, 0x51cd2),
    'field_conversion': (0x51ae0, 0x51bdc),
    'card_lookup': (0x5c060, 0x5c0a9),
    'card_guard': (0x5c100, 0x5c119),
    'card_text_consumer': (0xbac21, 0xbb572),
    'participant_kind_card_join': (0x1177c0, 0x117879),
    'enemy_lookup_frontier': (0x5a0a0, 0x5a11c),
    'enemy_area_replace_reference': (0x5a21e, 0x5a22d),
}
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_WRITE,
                     UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE)
from unicorn import x86_const as reg

BASE, OWNER, STACK, INPUT, TABLE, LABELS, CONTEXT, INSTANCE = (
    0x400000, 0x2000000, 0x3000000, 0x4000000, 0x4100000,
    0x4200000, 0x5000000, 0x6000000)
SP, RETURN = STACK + 0x8000, STACK + 0xff00


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path, digest, limit=64 * 1024 * 1024):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or sha(raw) != digest:
        raise ValueError('Pinned current source changed: ' + str(path))
    return raw


def source_rows(relative):
    raw_sha, decoded_sha = PINS[relative]
    plain = decode_csvz(pinned(CLIENT / relative, raw_sha), limit=4 * 1024 * 1024)
    if sha(plain) != decoded_sha:
        raise ValueError('Decoded source changed')
    result, offset = [], 0
    for line, raw in enumerate(plain.splitlines(keepends=True), 1):
        result.append({'line': line, 'offset': offset, 'raw': raw,
                       'fields': next(csv.reader([raw.decode('cp950')], strict=True))})
        offset += len(raw)
    return result


def provenance(relative, row):
    raw = row['raw'].rstrip(b'\r\n')
    return {'path': relative, 'sha256': PINS[relative][0],
            'decoded_sha256': PINS[relative][1], 'line': row['line'],
            'decoded_offset': row['offset'], 'length': len(raw), 'row_sha256': sha(raw)}


def inventory():
    """Project main's pinned inventory once; retain its exact occurrence keys."""
    catalog = pinned_catalog(CLIENT)
    records, groups = [], {}
    for row in catalog['records']:
        identity = {key: row[key] for key in
                    ('source_record_index', 'area_generation', 'area', 'scene', 'ordinal')}
        record = {'identity': identity, 'lookup_visible': row['lookup_visible'],
            'source': {'path': GAME, 'sha256': PINS[GAME][0], 'decoded_sha256': PINS[GAME][1],
                       'line': row['source_line'], 'decoded_offset': row['source_offset'],
                       'row_sha256_including_line_ending': row['record_sha256']},
            'source_fields_hex': row['fields_hex'], 'name_bytes_hex': row['name_bytes_hex'],
            'monster_classification': None, 'bank_or_variant_identity': None,
            'fields': {name: {'value': None, 'authority': 'unresolved',
                             'producer_rva': None, 'source': None} for name in FIELDS},
            'card_reference_ids': []}
        records.append(record)
        if row['lookup_visible']:
            groups.setdefault((row['area'], row['scene']), []).append(record)
    return records, groups, {'allocated_records': len(records),
        'lookup_visible_records': sum(len(g) for g in groups.values()),
        'allocated_groups': len(catalog['loaded_groups']), 'lookup_visible_groups': len(groups),
        'area_declarations': len({r['identity']['area_generation'] for r in records}),
        'superseded_records': sum(not r['lookup_visible'] for r in records),
        'verified_wild_monster_count': None, 'all_monster_systems_enumerated': False}


class NativeCard:
    def __init__(self, image):
        if sha(image) != IMAGE_SHA:
            raise ValueError('Pinned image changed')
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        for address, size in ((OWNER, 0xe0000), (STACK, 0x10000), (INPUT, 0x1000),
                              (TABLE, 0x2000), (LABELS, 0x10000),
                              (CONTEXT, 0xe0000), (INSTANCE, 0x1000)):
            self.vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_protect(RETURN & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(RETURN, b'\xf4')
        self.put(OWNER + 8, '<H', 39)
        self.put(OWNER + 0xd2aac, '<I', TABLE)
        self.put(CONTEXT + 0xcff70, '<I', OWNER)
        self.put(CONTEXT + 0x28, '<I', OWNER)
        self.put(OWNER + 0xb2c6c, '<H', 0x20b)
        self.put(OWNER + 0xb2c68, '<I', LABELS)
        for slot in (0x81c, 0x820, 0x824, 0x828, 0x12c, 0x130, 0x134, 0x138, 0x13c):
            self.put(LABELS + slot, '<I', LABELS + 0x1000)
        self.vm.mem_write(LABELS + 0x1000, b'label-fixture\0')
        self.trace, self.columns, self.writes, self.reads, self.formats = [], [], [], [], []
        self.loaded = set()
        self.stops, self.phase = set(), ''
        self.vm.hook_add(UC_HOOK_CODE, self.code)
        self.vm.hook_add(UC_HOOK_MEM_WRITE, self.write)
        self.vm.hook_add(UC_HOOK_MEM_READ, self.read)

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def get(self, address, fmt):
        return struct.unpack(fmt, self.vm.mem_read(address, struct.calcsize(fmt)))

    def register(self, name, value=None):
        key = getattr(reg, 'UC_X86_REG_' + name)
        return self.vm.reg_read(key) if value is None else self.vm.reg_write(key, value)

    def code(self, vm, address, size, data):
        if address in self.stops:
            vm.emu_stop()
            return
        rva = address - BASE
        ranges = (*SLICES.values(), (0x147000, 0x16f000))
        if (rva in (0x51a90, 0x147973, 0x147e23) or
                not any(lo <= rva and rva + size <= hi for lo, hi in ranges)):
            raise AssertionError(f'Unqualified instruction {rva:x}')
        self.trace.append(rva)
        if self.phase == 'loader' and rva == 0x51b60:
            self.columns.append(self.get(self.register('ESP') + 4, '<I')[0])
        if self.phase == 'consumer' and rva in FORMAT_CALLS.values():
            _, fmt, _, color, number = self.get(self.register('ESP'), '<4Ii')
            self.formats.append({'field': next(k for k, v in FORMAT_CALLS.items() if v == rva),
                                 'call_rva': hex(rva), 'format_rva': hex(fmt - BASE),
                                 'color_argument': color, 'value': number})

    def write(self, vm, access, address, size, value, data):
        if TABLE <= address < TABLE + 0x2000:
            self.writes.append((self.register('EIP') - BASE, address - TABLE, size, value))

    def read(self, vm, access, address, size, value, data):
        if self.phase == 'consumer' and SP + 0x24 <= address < SP + 0x54:
            self.reads.append((self.register('EIP') - BASE, address - SP - 0x24, size))

    def run(self, rva, *stops):
        self.stops = set(stops)
        self.vm.emu_start(BASE + rva, 0, count=100000, timeout=1000000)
        if self.register('EIP') not in self.stops:
            raise AssertionError('Native execution exceeded budget')
        return self.register('EIP') - BASE

    def tokenize(self, raw):
        if type(raw) is not bytes:
            raise ValueError('Exact bytes required')
        raw = raw.replace(b'\r\n', b'\n')
        if (not raw.endswith(b'\n') or b'\0' in raw or len(raw) >= 4096 or
                raw.count(b',') != 38 or any(len(f) >= 380 for f in raw[:-1].split(b','))):
            raise ValueError('Card row outside tokenizer bounds')
        self.phase = 'tokenizer'
        self.vm.mem_write(INPUT, raw + b'\0')
        self.put(SP, '<2I', RETURN, INPUT)
        self.register('ESP', SP)
        self.register('ECX', OWNER)
        self.run(0x51be0, RETURN)
        if self.register('EAX') != 39 or self.register('ESP') != SP + 8:
            raise AssertionError('Native tokenizer result')

    def header(self):
        # Declared post-header-parse live-ins; original dispatch and calloc args run.
        self.register('ESP', SP)
        self.register('EDI', OWNER)
        self.put(SP + 0xc, '<I', 101)
        self.vm.mem_write(SP + 0x18, b'ChangeDollCount\0')
        self.run(0x56e3a, BASE + 0x5bb3f)
        return {'allocation_arguments': list(self.get(self.register('ESP'), '<2I')),
                'stop_rva': '0x5bb3f', 'header_count_live_in': 101}

    def load(self, raw):
        self.tokenize(raw)
        self.phase = 'loader'
        self.columns.clear()
        self.writes.clear()
        self.trace.clear()
        self.register('ESP', SP)
        self.register('EBP', OWNER)
        self.register('EBX', 101)
        stop = self.run(0x5bb6c, BASE + 0x5bbfb, BASE + 0x5be84)
        index, = self.get(SP + 0x10, '<i')
        if stop != 0x5bbfb or not 0 <= index < 101:
            raise ValueError('Rejected card index/name')
        requested, = self.get(self.register('ESP'), '<I')
        if requested > 256:
            raise ValueError('Card label allocation bound')
        self.register('EAX', LABELS + 0x2000 + index * 256)
        self.run(0x5bc00, BASE + 0x5be84)
        if self.register('ESP') != SP:
            raise AssertionError('Loader stack imbalance')
        packed = bytes(self.vm.mem_read(TABLE + index * 48, 48))
        self.loaded.add(index)
        return {'index': index, 'record_hex': packed.hex(),
                'columns_read': sorted(set(self.columns)),
                'writes': [{'rva': hex(r), 'record_offset': a - index * 48,
                            'width': s, 'bits': v} for r, a, s, v in self.writes],
                'values': {name: struct.unpack_from('<h', packed, spec[1])[0]
                           for name, spec in FIELDS.items()}}

    def consume(self, index, selector=0x188d):
        if type(index) is not int or index not in self.loaded:
            raise ValueError('Loaded card index required')
        if type(selector) is not int or not 0 <= selector <= 65535:
            raise ValueError('Selector bound')
        self.phase = 'consumer'
        self.formats.clear()
        self.reads.clear()
        self.trace.clear()
        self.put(INSTANCE + 4, '<I', index)
        self.put(SP + 0x11ac, '<I', INSTANCE)
        self.vm.mem_write(SP + 0x3bc, b'\0' * 1024)
        self.register('ESP', SP)
        self.register('EBP', CONTEXT)
        self.register('ESI', selector)
        stop = self.run(0xbac21, BASE + 0xbb572, BASE + 0xbbbce)
        if self.register('ESP') != SP:
            raise AssertionError('Consumer stack imbalance')
        text = bytes(self.vm.mem_read(SP + 0x3bc, 1024)).split(b'\0', 1)[0]
        return {'stop_rva': hex(stop), 'lookup_executed': 0x5c060 in self.trace,
                'formats': list(self.formats), 'text_hex': text.hex(),
                'record_reads': [{'rva': hex(r), 'offset': o, 'width': s}
                                 for r, o, s in self.reads]}

    def participant_join(self, index, kind=1):
        if type(index) is not int or not 0 <= index < 101 or type(kind) is not int or not 0 <= kind <= 255:
            raise ValueError('Participant fixture bound')
        if index not in self.loaded:
            raise ValueError('Loaded card index required')
        self.phase = 'participant'
        self.trace.clear()
        self.vm.mem_write(INSTANCE, bytes(16))
        self.put(INSTANCE + 2, '<B', kind)
        self.put(INSTANCE + 12, '<H', index)
        self.put(SP, '<2I', RETURN, INSTANCE)
        self.register('ESP', SP)
        self.register('ECX', CONTEXT)
        stop = self.run(0x1177c0, BASE + 0x117874, BASE + 0x11890b,
                        BASE + 0x118a79, BASE + 0x1182b9)
        args = self.get(self.register('ESP'), '<3I') if stop == 0x117874 else None
        return {'record_kind_fixture': kind, 'card_index_fixture': index,
                'stop_rva': hex(stop), 'card_lookup_executed': 0x5c060 in self.trace,
                'enemy_lookup_arguments_raw': list(args) if args else None,
                'join': {'area': args[0] & 255, 'scene': args[1] & 65535,
                         'ordinal': args[2] & 65535} if args else None,
                'wild_actor_type_authority': None}


def evidence():
    image = pinned(IMAGE, IMAGE_SHA)
    card_rows = source_rows(CARD)
    if card_rows[4]['fields'] != ['ChangeDollCount', '101'] or len(card_rows) != 106:
        raise ValueError('Card section envelope changed')
    if [int(r['fields'][0]) for r in card_rows[5:]] != list(range(101)):
        raise ValueError('Card identity sequence changed')
    records, groups, counts = inventory()
    native = NativeCard(image)
    header = native.header()
    cards = []
    for row in card_rows[5:]:
        loaded = native.load(row['raw'])
        index = loaded['index']
        consumer = native.consume(index)
        participant = native.participant_join(index)
        join = participant['join']
        target = None
        if join:
            group = groups.get((join['area'], join['scene']), [])
            if 1 <= join['ordinal'] <= len(group):
                target = group[join['ordinal'] - 1]
                target['card_reference_ids'].append(index)
        source = provenance(CARD, row)
        fields = {}
        raw_fields = row['raw'].rstrip(b'\r\n').split(b',')
        for name, (column, offset, writer, reader) in FIELDS.items():
            fields[name] = {'value': loaded['values'][name],
                'authority': 'card_record_signed_display_value_only',
                'source': source, 'column': column,
                'column_header': card_rows[3]['fields'][column],
                'decoded_field_offset': row['offset'] + sum(len(v) + 1 for v in raw_fields[:column]),
                'source_text': raw_fields[column].decode('ascii'), 'record_offset': offset,
                'width': 2, 'store_rva': hex(writer), 'signed_consumer_rva': hex(reader),
                'image_sha256': IMAGE_SHA, 'wild_monster_value': None}
        cards.append({'card_index': index, 'source': source,
                      'source_identity': dict(zip(('island', 'area_id', 'name_index'),
                                                 map(int, row['fields'][3:6]))),
                      'item_name': row['fields'][2], 'fields': fields,
                      'native_loader': loaded, 'native_consumer': consumer,
                      'native_participant_join': participant,
                      'joined_enemy_identity': target['identity'] if target else None,
                      'join_authority': 'resource_identity_reference_only'})
    counts.update(card_records_executed=len(cards),
                  card_records_joined=sum(c['joined_enemy_identity'] is not None for c in cards),
                  field_domain=list(FIELDS), verified_wild_stat_records=0,
                  unresolved_visible_field_cells=counts['lookup_visible_records'] * len(FIELDS))
    return {'schema': 'current-monster-combat-stats-v1', 'image_sha256': IMAGE_SHA,
            'requested_scope': ['normal', 'boss', 'elite', 'quest', 'event', 'summoned'],
            'identity_scope': 'Main EnyName occurrence inventory; not all monster systems',
            'runtime_eligible': False,
            'field_coverage': {name: {'verified_lookup_records': 0,
                                     'unresolved_lookup_records': counts['lookup_visible_records'],
                                     'unresolved_source_occurrences': len(records)} for name in FIELDS},
            'coverage': counts, 'records': records, 'cards': cards, 'header': header,
            'field_authority': {name: {'authority': 'unresolved', 'value': None,
                'reason': 'No wild-actor producer binding. Card data is not base-stat authority.'}
                                for name in FIELDS},
            'slices': {name: {'start_rva': hex(lo), 'end_rva_exclusive': hex(hi),
                             'sha256': sha(image[lo:hi])} for name, (lo, hi) in SLICES.items()},
            'boundaries': [
                'EnyName identity projection reuses established area-replacement semantics; full loader is not rerun.',
                'Source decompression and CRT CRLF-to-LF translation happen outside VM.',
                'Header count 101 is a source-checked live-in; stop before calloc.',
                'Rows resume after file read; stop before malloc, resume with explicit label allocation.',
                'Text selector, context, item instance and message labels are fixtures; original formatter executes.',
                'Participant record kind/index are counterfactual fixtures, not captured wild-monster state.',
                'Participant execution stops before 5A0A0; joins use its inspected argument widths and existing table semantics.'],
            'remaining_frontier': {
                'card_identity_call': '0x117874 -> 0x5a0a0; identity lookup, not combat-stat producer',
                'wild_type': '1177FF reads record+2; kind 1 takes card path; semantic wild discriminator remains unproved',
                'needed': 'Original producer binding all nine combat fields to each exact wild actor identity; no such edge qualified here',
                'bounded_absence_only': True}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true', help='Omit per-record arrays from stdout')
    args = parser.parse_args()
    result = evidence()
    if args.summary:
        result.pop('records')
        result.pop('cards')
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
