"""Lane E: current battle item-result consumer, never a monster award table.

Only pinned current inputs are read. JSON goes to stdout. Counterfactual records
are explicit synthetic probes; no observed loot or probabilities are generated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from . import current_monster_inventory as inventory
from .current_item_metadata import NativeItemMetadata
from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
MESSAGE = 'Data2/Patch/Comm/message.csvZ'
MESSAGE_SHA = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
MESSAGE_PLAIN_SHA = '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'
BASE, BATTLE, PACKET = 0x400000, 0x5000000, 0x3800000
KEY = 4660
FIELDS = ('drop_items', 'drop_rates', 'quantity', 'conditions', 'group_weights',
          'rate_denominator', 'rate_unit', 'monster_drop_join')
IDENTITY = ('source_record_index', 'area_generation', 'area', 'scene', 'ordinal')
SPANS = {
    'item_row_producer': (0x59420, 0x59960),
    'item_index_store': (0x59a20, 0x59a27),
    'item_lookup': (0x59a60, 0x59a7e),
    'item_icon_lookup': (0x9b720, 0x9b768),
    'result_item_slot_writer': (0x853d0, 0x85451),
    'control_icon_setter': (0x1068c0, 0x106930),
    'item_name_list_consumer': (0x850fa, 0x85194),
    'item_name_separator': (0x18f1f4, 0x18f1f6),
    'item_slot_clear': (0x85052, 0x85066),
    'result_item_loop': (0x118bf0, 0x118c6f),
    'loss_header_selection': (0x118cc3, 0x118ccb),
    'other_selector_branches': (0x118ccb, 0x118cfc),
    'selector_table': (0x118e3c, 0x118e4c),
    'message_binding': (0x11125f, 0x1112a5),
    'message_binding_ids': (0x19be68, 0x19be7c),
    'receive_dispatch': (0x1193c4, 0x1193e7),
    'receive_map_89': (0x119a8d, 0x119a8e),
    'receive_target_24': (0x119968, 0x11996c),
    'receive_queue': (0x1195cc, 0x1195ea),
    'queue_dispatch': (0x114332, 0x114358),
    'queue_map_89': (0x1146c9, 0x1146ca),
    'queue_target_8': (0x114654, 0x114658),
    'queue_consumer_call': (0x114582, 0x11459f),
    'size_entry_89': (0x1548, 0x154c),
    'size_return_57': (0x1240, 0x1246),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path, expected, limit=4 * 1024 * 1024):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or sha(raw) != expected:
        raise ValueError('Pinned current source changed: ' + str(path))
    return raw


def message_rows():
    plain = decode_csvz(pinned(CLIENT / MESSAGE, MESSAGE_SHA))
    if sha(plain) != MESSAGE_PLAIN_SHA:
        raise ValueError('Decoded message source changed')
    rows, offset, active, remaining = {}, 0, False, 0
    for line, raw in enumerate(plain.splitlines(keepends=True), 1):
        columns = raw.rstrip(b'\r\n').split(b',', 1)
        if columns[0] == b'ProgramMsg':
            active, remaining = True, int(columns[1])
        elif active and remaining:
            key = int(columns[0])
            rows[key] = {'id': key, 'source_line': line, 'decoded_offset': offset,
                         'raw_record_hex': raw.hex(), 'row_sha256': sha(raw),
                         'text_hex': columns[1].hex() if len(columns) == 2 else None}
            remaining -= 1
        offset += len(raw)
    return rows


class NativeLootResult:
    """Original item producer and consumer on one VM; no game-call substitutes.

    UI handle -1 is an explicit disabled-control precondition. Its real native
    early return allows slot writes without rendering. Active-control probes
    stop before the renderer call; no return value is fabricated.
    """
    def __init__(self):
        pinned(IMAGE, IMAGE_SHA)
        pinned(CLIENT / inventory.SOURCE, inventory.SOURCE_SHA)
        self.metadata = m = NativeItemMetadata()
        if sha(m.decoded) != inventory.PLAIN_SHA:
            raise ValueError('Decoded item source changed')
        rows = m.sections['MIS']['records']
        indices = [i for i, row in enumerate(rows)
                   if bytes.fromhex(row['raw_record_hex']).split(b',', 1)[0] == str(KEY).encode()]
        if len(indices) != 1:
            raise ValueError('Expected unique current MIS item key')
        self.item = m.item_row('MIS', indices[0], retain=True)
        self.item_source = rows[indices[0]]
        self.vm, self.uc, self.regs = m.vm, m.uc, m.x86
        for address, size in ((BATTLE, 4096), (PACKET, 4096),
                              (BATTLE + 0xa9ea000, 4096),
                              (m.OWNER + 0x232000, 4096),
                              (m.OWNER + 0x23d000, 4096)):
            self.vm.mem_map(address, size, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        self.vm.mem_write(BATTLE + 0x20, struct.pack('<I', m.OWNER))
        self.vm.mem_write(BATTLE + 0x28, struct.pack('<I', m.TABLE))
        self.messages = message_rows()
        self.bind_messages()
        self.item_snapshot = bytes(self.vm.mem_read(m.RECORD, 0x1ac))

    def reg(self, name, value=None):
        key = getattr(self.regs, 'UC_X86_REG_' + name)
        return self.vm.reg_read(key) if value is None else self.vm.reg_write(key, value)

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def get(self, address, fmt):
        return struct.unpack(fmt, self.vm.mem_read(address, struct.calcsize(fmt)))

    def run(self, entry, ranges, stops, allowed_writes=()):
        self.trace, self.reads, self.writes, self.icon_calls = [], [], [], []
        self.stop = None

        def code(vm, address, size, _):
            rva = address - BASE
            if rva in stops:
                self.stop = rva
                vm.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in ranges):
                raise AssertionError(f'Unqualified loot instruction: {rva:x}')
            self.trace.append(rva)
            if rva == 0x8543b:
                self.icon_calls.append(list(self.get(self.reg('ESP'), '<4I')))

        def read(vm, access, address, size, value, _):
            if PACKET <= address < PACKET + 4096:
                if address + size > PACKET + 57:
                    raise AssertionError('Result read exceeded logical record')
                self.reads.append([self.reg('EIP') - BASE, address - PACKET, size])

        def write(vm, access, address, size, value, _):
            m = self.metadata
            if m.STACK <= address < address + size <= m.STACK + 0x10000:
                return
            if not any(lo <= address < address + size <= hi for lo, hi in allowed_writes):
                raise AssertionError(f'Unexpected loot write: {address:x}+{size}')
            self.writes.append([self.reg('EIP') - BASE, address, size, value])

        hooks = [self.vm.hook_add(self.uc.UC_HOOK_CODE, code),
                 self.vm.hook_add(self.uc.UC_HOOK_MEM_READ, read),
                 self.vm.hook_add(self.uc.UC_HOOK_MEM_WRITE, write)]
        try:
            self.vm.emu_start(BASE + entry, 0xffffffff, count=20000, timeout=1000000)
            if self.stop is None:
                raise AssertionError('Loot execution exhausted its bound')
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)

    def bind_messages(self):
        m = self.metadata
        self.put(m.TABLE + 0xb2c6c, '<H', max(self.messages))
        self.put(m.TABLE + 0xb2c68, '<I', m.OUTPUT)
        offset = 0x2000
        ids = struct.unpack_from('<10H', m.image, 0x19be68)
        for key in ids:
            text = bytes.fromhex(self.messages[key]['text_hex']) + b'\0'
            self.put(m.OUTPUT + (key - 1) * 4, '<I', m.OUTPUT + offset)
            self.vm.mem_write(m.OUTPUT + offset, text)
            offset += len(text)
        self.reg('ECX', BATTLE)
        self.reg('ESP', m.SP)
        self.vm.mem_protect(0x5b8000, 4096, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        try:
            self.run(0x11125f, [SPANS['message_binding']], {0x1112a5},
                     ((0x5b8b48, 0x5b8b70),))
        finally:
            self.vm.mem_protect(0x5b8000, 4096, self.uc.UC_PROT_READ)
        pointer = self.get(0x5b8b5c, '<I')[0]
        text = bytes.fromhex(self.messages[298]['text_hex'])
        if bytes(self.vm.mem_read(pointer, len(text) + 1)) != text + b'\0':
            raise AssertionError('Native ProgramMsg 298 binding failed')
        self.binding_rvas = sorted(set(self.trace))

    def consume(self, record, *, previous_slots, spectator, active_control=False):
        if type(record) is not bytes or len(record) != 57 or record[0] != 0x89:
            raise ValueError('Expected exact 57-byte logical 89 record')
        if (type(previous_slots) is not tuple or len(previous_slots) != 4 or
                any(type(v) is not int or not 0 <= v <= 65535 for v in previous_slots)
                or type(spectator) is not bool or type(active_control) is not bool):
            raise ValueError('Explicit four WORD slots and boolean context required')
        m = self.metadata
        self.vm.mem_write(PACKET, record)
        self.vm.mem_protect(PACKET, 4096, self.uc.UC_PROT_READ)
        self.vm.mem_write(m.STACK, b'\xa5' * 0xf000)
        self.put(m.SP, '<II', m.RETURN, PACKET)
        self.put(m.OWNER + 0x23d616, '<6H', 0xa5a5, *previous_slots, 0xa5a5)
        self.put(m.OWNER + 0x232df0, '<H', 0 if active_control else 65535)
        # Panel/element flags are synthetic control preconditions, not loot conditions.
        self.put(m.OWNER + 0xe2170 + 0x818, '<H', 1)
        self.put(m.OWNER + 0xe2170 + 0x81c, '<H', 0)
        self.put(m.OWNER + 0xe2170 + 8, '<I', 0x12340000)
        for index in range(4):
            self.put(m.OWNER + 0xe2170 + 0x8b8 + 100 * index, '<B', 1)
        self.put(BATTLE + 0xa9ea4c8, '<I', int(spectator))
        self.reg('ESP', m.SP)
        self.reg('ECX', BATTLE)
        self.reg('EFLAGS', 2)
        names = ('result_item_loop', 'loss_header_selection', 'other_selector_branches',
                 'result_item_slot_writer', 'item_icon_lookup', 'item_lookup', 'control_icon_setter')
        stops = {0x118c5a, 0x118c6f, 0x118cd9, 0x118cf2, 0x118cfc,
                 0x118d48, 0x106927}
        try:
            self.run(0x118bf0, [SPANS[k] for k in names], stops,
                     ((m.OWNER + 0x23d618, m.OWNER + 0x23d620),))
        finally:
            self.vm.mem_protect(PACKET, 4096, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        if self.get(m.OWNER + 0x23d616, '<H') != (0xa5a5,) or self.get(
                m.OWNER + 0x23d620, '<H') != (0xa5a5,):
            raise AssertionError('Slot canary changed')
        if bytes(self.vm.mem_read(m.RECORD, 0x1ac)) != self.item_snapshot:
            raise AssertionError('Item source record changed during result consumption')
        selected_message = None
        if self.stop == 0x118c5a:
            pointer = self.get(self.reg('ESP') + 12, '<I')[0]
            ids = struct.unpack_from('<10H', m.image, 0x19be68)
            matches = [key for index, key in enumerate(ids)
                       if self.get(0x5b8b48 + index * 4, '<I')[0] == pointer]
            if len(matches) != 1:
                raise AssertionError('Formatter argument has no unique bound message')
            selected_message = matches[0]
        return {'input_authority': 'synthetic_counterfactual_not_original_loot',
                'record_hex': record.hex(), 'previous_slots': list(previous_slots),
                'spectator_precondition': spectator, 'active_control_precondition': active_control,
                'stop_rva': self.stop, 'slot_keys': list(self.get(m.OWNER + 0x23d618, '<4H')),
                'packet_reads': self.reads, 'slot_writes': self.writes,
                'icon_call_raw_arguments': self.icon_calls,
                'executed_rvas': sorted(set(self.trace)),
                'selected_program_message': selected_message}

    def name_list(self):
        """Independent original text-loop checkpoint, using retained native slots."""
        m = self.metadata
        self.vm.mem_write(m.SP, bytes(0x300))
        self.put(m.SP + 0x10, '<II', m.OWNER + 0x23d618, 4)
        self.reg('ESP', m.SP)
        self.reg('EBX', m.OWNER)
        self.reg('EFLAGS', 2)
        self.run(0x850fa, [SPANS['item_name_list_consumer'], SPANS['item_lookup']], {0x85194})
        raw = bytes(self.vm.mem_read(m.SP + 0x18, 512)).split(b'\0', 1)[0]
        return {'authority': 'native_display_name_list_not_monster_join',
                'text_hex': raw.hex(), 'executed_rvas': sorted(set(self.trace)),
                'stop_rva': self.stop}


def synthetic_record(entries, *, selector=0):
    """Explicit test input only. Each entry is raw (DWORD, WORD, WORD)."""
    if len(entries) != 4:
        raise ValueError('Four explicit counterfactual entries required')
    raw = bytearray(57)
    raw[0] = 0x89
    struct.pack_into('<I', raw, 49, selector)
    for index, entry in enumerate(entries):
        struct.pack_into('<IHH', raw, 17 + 8 * index, *entry)
    return bytes(raw)


def counterfactuals(native):
    base = [(KEY, 0, 0)] * 4
    cases = [('four_positive', base, 0, False, False),
             ('loss_marker', [(KEY, 65535, 0)] + base[1:], 0, False, False),
             ('unused_tail', [(KEY, 0, 65535)] * 4, 0, False, False),
             ('high_word_alias', [(0x10000 + KEY, 0, 0)] * 4, 0, False, False),
             ('signed_gate', [(0, 65535, 0), (0x80000000 + KEY, 65535, 0),
                              (0xffffffff, 65535, 0), (KEY, 0, 0)], 0, False, False),
             ('lookup_upper_bound', [(0x7f58, 0, 0)] * 4, 0, False, False),
             ('fixture_uninstalled_key', [(1, 0, 0)] * 4, 0, False, False),
             ('spectator_loss_marker', [(KEY, 65535, 0)] * 4, 0, True, False),
             ('active_control_boundary', base, 0, False, True)]
    cases += [('selector_' + str(v), base, v, False, False) for v in (1, 2, 3, 4, 0xffffffff)]
    result = []
    for name, entries, selector, spectator, active in cases:
        value = native.consume(synthetic_record(entries, selector=selector),
                               previous_slots=(0xa501, 0xa502, 0xa503, 0xa504),
                               spectator=spectator, active_control=active)
        value['case'] = name
        if name == 'four_positive':
            value['name_consumer'] = native.name_list()
        result.append(value)
    return result


def build_report():
    catalog = inventory.pinned_catalog()
    native = NativeLootResult()
    m = native.metadata
    records = []
    for row in catalog['records']:
        records.append({'identity': {k: row[k] for k in IDENTITY},
            'lookup_visible': row['lookup_visible'],
            'source': {'path': inventory.SOURCE, 'sha256': inventory.SOURCE_SHA,
                       'decoded_sha256': inventory.PLAIN_SHA, 'line': row['source_line'],
                       'decoded_offset': row['source_offset'], 'raw_record_hex': row['raw_record_hex'],
                       'row_sha256_including_line_ending': row['record_sha256']},
            'monster_classification': None, 'variant_identity': None,
            'native_values': dict.fromkeys(FIELDS), 'authority': 'unresolved'})
    return {
        'schema': 'god2-current-monster-drop-rules-v1', 'runtime_eligible': False,
        'requested_scope': ['normal', 'boss', 'elite', 'event', 'quest', 'summoned'],
        'scope': 'Complete pinned EnyName occurrences; not unique species or ALL-boss denominator',
        'sources': {
            'image': {'path': str(IMAGE), 'sha256': IMAGE_SHA, 'base': BASE,
                      'rva_equals_file_offset': True},
            'gamedata': {'path': inventory.SOURCE, 'sha256': inventory.SOURCE_SHA,
                         'decoded_sha256': inventory.PLAIN_SHA},
            'message': {'path': MESSAGE, 'sha256': MESSAGE_SHA,
                        'decoded_sha256': MESSAGE_PLAIN_SHA}},
        'native_spans': {name: {'offset': lo, 'end_exclusive': hi,
                              'sha256': sha(m.image[lo:hi]), 'raw_hex': m.image[lo:hi].hex()}
                         for name, (lo, hi) in SPANS.items()},
        'current_source_item_probe': {'authority': 'item_definition_only_not_monster_drop',
            'source': {'path': inventory.SOURCE, 'file_sha256': inventory.SOURCE_SHA,
                       'decoded_sha256': inventory.PLAIN_SHA, 'record': native.item_source},
            'key': KEY, 'section': 'MIS',
            'native_record_hex': native.item['record'].hex(),
            'native_icon_group': native.item['group'], 'native_icon_action': native.item['action'],
            'producer_executed_rvas': sorted(m.executed)},
        'loss_message': native.messages[298],
        'loss_message_binding': {'program_message_id': 298, 'global_rva': 0x1b8b5c,
                                 'executed_rvas': native.binding_rvas},
        'consumer_contract': {
            'opcode': 0x89, 'logical_bytes': 57, 'selector_offset': 49,
            'item_branch_selector': 0, 'entry_offsets': [17, 25, 33, 41],
            'entry_stride': 8, 'signed_dword_positive_gate': True,
            'item_key': 'low WORD of positive entry DWORD',
            'loss_marker': 'entry+4 WORD == 0xffff, tested only for positive DWORD entries',
            'tail_entry_bytes': 'entry+6..7 unread within this bounded item consumer',
            'display_state': 'UI+0x23d618 + 2*slot',
            'nonpositive_entry_effect': 'Preserves previous slot; does not clear it',
            'item_lookup_bound': 'unsigned low WORD < 0x7f58',
            'lookup_miss_icon': [65, 65535],
            'quantity': None, 'rate': None, 'monster_identity': None,
            'award_producer': None, 'full_drop_table': None},
        'counterfactuals': counterfactuals(native),
        'coverage': {'source_occurrences': len(records),
                     'source_groups': len(catalog['loaded_groups']),
                     'visible_occurrences': sum(r['lookup_visible'] for r in records),
                     'visible_groups': len(catalog['groups']),
                     'superseded_occurrences': sum(not r['lookup_visible'] for r in records),
                     'verified_monster_drop_joins': 0,
                     'unique_species_denominator': None, 'all_boss_denominator': None,
                     'all_monster_systems_enumerated': False},
        'field_coverage': {k: {'verified_source_occurrences': 0,
                               'unresolved_source_occurrences': len(records),
                               'unresolved_visible_occurrences': sum(r['lookup_visible'] for r in records)}
                           for k in FIELDS},
        'remaining_frontier': {
            'original_award_producer': None, 'monster_variant_to_award_join': None,
            'full_candidate_item_sets': None, 'quantity_rule': None,
            'condition_evaluator': None, 'group_selection_arithmetic': None,
            'probability_unit_and_denominator': None},
        'records': records,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args(argv)
    report = build_report()
    if args.summary:
        report = {'schema': report['schema'], 'coverage': report['coverage'],
                  'counterfactual_cases': len(report['counterfactuals']),
                  'remaining_frontier': report['remaining_frontier']}
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
