"""Pinned SpecialEnyInfo and bounded 1C variant identity qualification.

Original loader/parser/lookup/consumer instructions run with bounded CRT
adapters. EnyName descriptors are independently staged from the shared source
inventory, NOT a second original EnyName load. No original stats are inferred.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))

from .current_monster_base_stats import (  # noqa: E402
    IMAGE, IMAGE_SHA256, GAME_FILE, GAME_SHA256, GAME_DECODED_SHA256,
    _LookupFixture, BATTLE, MANAGER, PACKET)
from .current_monster_inventory import FIELDS, parse_enemy_catalog  # noqa: E402
from .current_indoor_resources import BASE, SP, RETURN  # noqa: E402
from .current_world_actor import MESSAGES  # noqa: E402
from .omega_assets import decode_csvz  # noqa: E402
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
    UC_X86_REG_EIP, UC_X86_REG_EFLAGS)

SECTION_START, SECTION_END = 2781781, 2781824
SECTION = b'SpecialEnyInfo,1\r\n1,IGS_SPECIAL,0,0,149,1\r\n'
SECTION_SHA = 'c3d480f60ba45441c3dfc40fe2c61e420a9e79f32570a5b640f08b82652cc4ad'
SPECIAL = 0x25001000  # Previous page is unmapped, exposing selector-zero underflow.
DIAGNOSTIC = 0x26000000
RESULT = MESSAGES + 0xd2e30
SPANS = {
    'loader': (0x5a560, 0x5a860),
    'lookup': (0x5a120, 0x5a198),
    'row_reader': (0x51a90, 0x51ad8),
    'field_accessors': (0x51b50, 0x51bdc),
    'row_parser': (0x51be0, 0x51cd2),
    'stack_probe': (0x147b50, 0x147b7f),
    'consumer': (0x115c90, 0x115e77),
    'normal_lookup': (0x5a0a0, 0x5a11c),
    'participant_lookup': (0x11e6e0, 0x11e76a),
    'dispatch_table': (0x11662c, 0x11663c),
}
SERVICES = {
    0x15b406: ('allocation', {0x5a582}),
    0x147a95: ('fgets', {0x51ab0}),
    0x1489a0: ('strchr', {0x51c0c, 0x51c1d}),
    0x147b80: ('memcpy', {0x51c4d, 0x5a184}),
    0x148810: ('strncmp', {0x5a5c2}),
    0x1480b4: ('sscanf_decimal', {0x51bc9}),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def current_source():
    path = ROOT.parent / 'God2' / GAME_FILE
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('Current source size bound')
    raw = path.read_bytes()
    if sha(raw) != GAME_SHA256:
        raise ValueError('Current source hash changed')
    plain = decode_csvz(raw, limit=4 * 1024 * 1024)
    if sha(plain) != GAME_DECODED_SHA256:
        raise ValueError('Current decoded hash changed')
    if (plain[SECTION_START:SECTION_END] != SECTION
            or plain.count(b'SpecialEnyInfo,') != 1 or sha(SECTION) != SECTION_SHA):
        raise ValueError('Current SpecialEnyInfo envelope changed')
    return plain


class VariantIdentityProbe:
    """Explicit source descriptor fixture; one original special row, no live VM.

    Only stage_diagnostic_base maps an EnyName payload page. All other EnyName
    payload pages stay unmapped; alternate joins stop before payload access.
    """
    def __init__(self, *, allocation_poison=0xa5):
        if type(allocation_poison) is not int or not 0 <= allocation_poison <= 255:
            raise ValueError('Allocation poison must be a byte')
        self.image = IMAGE.read_bytes()
        if sha(self.image) != IMAGE_SHA256:
            raise ValueError('Current image hash changed')
        self.plain = current_source()
        self.catalog = parse_enemy_catalog(self.plain)
        self.native = _LookupFixture(self.image, self.catalog)
        self.vm = self.native.vm
        self.record_base = self.native.u32(MESSAGES + 0xd2e24)
        for address, size in ((BATTLE, 4096), (MANAGER & ~4095, 0x2000),
                              (SPECIAL, 4096), (DIAGNOSTIC, 4096)):
            self.native._map_rw(address, size)
        self.vm.mem_write(BATTLE + 0x28, struct.pack('<I', MESSAGES))
        self.vm.mem_write(MANAGER + 0x38, bytes(28 * 24))
        self.poison = allocation_poison
        self.stream = SECTION.split(b'\r\n', 1)[1].replace(b'\r\n', b'\n')
        self.stream_position = 0
        self.allocations = []
        self.staged = {}
        self.vm.mem_write(MESSAGES + 4, struct.pack('<IH', 0x80030000, 6))
        self.loader_trace = self.call(0x5a560, 1, loader=True)
        if (self.loader_trace['eax'] != 1 or self.stream_position != len(self.stream)
                or self.allocations != [(26, SPECIAL)]
                or self.native.u32(MESSAGES + 0xd2e2c) != 1
                or self.native.u32(MESSAGES + 0xd2e28) != SPECIAL):
            raise AssertionError('Original SpecialEnyInfo loader contract')
        self.loaded_record = bytes(self.vm.mem_read(SPECIAL, 26))

    def _cstring(self, address, limit=4096):
        value = bytearray()
        for offset in range(limit):
            byte = bytes(self.vm.mem_read(address + offset, 1))
            if byte == b'\0':
                return bytes(value)
            value.extend(byte)
        raise AssertionError('CRT string bound')

    def _run(self, start, stops, *, loader=False, budget=20000):
        vm = self.vm
        trace = {'visits': [], 'packet_reads': [], 'packet_writes': [],
                 'special_writes': [], 'services': []}
        writable = [(SP - 0x3000, SP + 0x100), (RESULT, RESULT + 26)]
        if loader:
            writable += [(MESSAGES + 0xc, MESSAGES + 0x10),
                         (MESSAGES + 0x78, MESSAGES + 0x78 + 6 * 380),
                         (MESSAGES + 0xd2e28, MESSAGES + 0xd2e30),
                         (SPECIAL, SPECIAL + 26)]
        else:
            writable += [(PACKET + 5, PACKET + 7)]

        def checked_write(address, value):
            if not any(lo <= address and address + len(value) <= hi for lo, hi in writable):
                raise AssertionError(f'CRT write outside qualified memory: {address:x}')
            vm.mem_write(address, value)

        def service(rva):
            sp = vm.reg_read(UC_X86_REG_ESP)
            ret = self.native.u32(sp)
            arg = lambda i: self.native.u32(sp + 4 + 4 * i)
            name, callers = SERVICES[rva]
            if ret - BASE not in callers or (not loader and rva != 0x147b80):
                raise AssertionError('Unqualified CRT caller')
            trace['services'].append({'rva': rva, 'caller': ret - BASE, 'name': name})
            if name == 'allocation':
                if arg(0) != 26 or self.allocations:
                    raise AssertionError('Special allocation bound')
                checked_write(SPECIAL, bytes((self.poison,)) * 26)
                self.allocations.append((26, SPECIAL))
                result = SPECIAL
            elif name == 'fgets':
                if arg(1) != 4096 or arg(2) != 0x80030000 or self.stream_position:
                    raise AssertionError('Special fgets bound')
                checked_write(arg(0), self.stream + b'\0')
                self.stream_position = len(self.stream)
                result = arg(0)
            elif name == 'strchr':
                if arg(1) not in (10, 44):
                    raise AssertionError('Parser delimiter bound')
                offset = self._cstring(arg(0)).find(bytes((arg(1),)))
                result = 0 if offset < 0 else arg(0) + offset
            elif name == 'memcpy':
                limit = 16 if ret - BASE == 0x5a184 else 379
                if not 0 <= arg(2) <= limit:
                    raise AssertionError('Copy bound')
                if ret - BASE == 0x5a184 and (arg(2) != 16 or arg(0) != RESULT + 2
                        or arg(1) not in (DIAGNOSTIC + 2, *(ptr + 2 for ptr in self.staged))):
                    raise AssertionError('Inherited name must use explicit diagnostic payload')
                checked_write(arg(0), bytes(vm.mem_read(arg(1), arg(2))))
                result = arg(0)
            elif name == 'strncmp':
                if arg(1) != BASE + 0x18a16c or arg(2) != 11:
                    raise AssertionError('Special sentinel comparison bound')
                left, right = self._cstring(arg(0))[:11], self._cstring(arg(1))[:11]
                result = (left > right) - (left < right)
            else:
                value = self._cstring(arg(0))
                if self._cstring(arg(1)) != b'%d' or value not in (b'0', b'149', b'1'):
                    raise AssertionError('Pinned numeric parser bound')
                checked_write(arg(2), struct.pack('<I', int(value)))
                result = 1
            vm.reg_write(UC_X86_REG_EAX, result & 0xffffffff)
            vm.reg_write(UC_X86_REG_ESP, sp + 4)
            vm.reg_write(UC_X86_REG_EIP, ret)

        def code(vm, address, size, context):
            rva = address - BASE
            if rva in stops:
                vm.emu_stop()
                return
            trace['visits'].append(rva)
            if rva in SERVICES:
                service(rva)
            elif not any(lo <= rva and rva + size <= hi for name, (lo, hi) in SPANS.items()
                         if name != 'dispatch_table'):
                raise AssertionError(f'Outside qualified instruction ranges: {rva:x}')

        def write(vm, access, address, size, value, context):
            if not any(lo <= address and address + size <= hi for lo, hi in writable):
                raise AssertionError(f'Unexpected native write: {address:x}')
            if SPECIAL <= address < SPECIAL + 26:
                trace['special_writes'].append((address - SPECIAL, size))
            if PACKET <= address < PACKET + 45:
                trace['packet_writes'].append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                                               address - PACKET, size))

        def read(vm, access, address, size, value, context):
            if PACKET <= address < PACKET + 4096:
                if address + size > PACKET + 45:
                    raise AssertionError('Packet read bound')
                trace['packet_reads'].append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                                              address - PACKET, size))
            if SPECIAL - 26 <= address < SPECIAL:
                raise AssertionError('Original special selector zero underflows record arena')
            if self.record_base <= address < self.record_base + 26 * 7815:
                if not any(ptr <= address and address + size <= ptr + 26 for ptr in self.staged):
                    raise AssertionError('Unstaged EnyName payload read')

        hooks = [vm.hook_add(UC_HOOK_CODE, code), vm.hook_add(UC_HOOK_MEM_WRITE, write),
                 vm.hook_add(UC_HOOK_MEM_READ, read)]
        try:
            vm.emu_start(BASE + start, RETURN, count=budget)
            stop = vm.reg_read(UC_X86_REG_EIP) - BASE
            if stop not in stops:
                raise AssertionError('Native instruction budget exhausted')
        finally:
            for hook in hooks:
                vm.hook_del(hook)
        trace.update(stop_rva=stop, eax=vm.reg_read(UC_X86_REG_EAX),
                     edx=vm.reg_read(UC_X86_REG_EDX))
        return trace

    def _reset(self, *args, poison=0xa5):
        self.vm.mem_write(SP - 0x3000, bytes((poison,)) * 0x3100)
        self.vm.mem_write(SP, struct.pack('<' + 'I' * (len(args) + 1), RETURN, *args))
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_EFLAGS, 2)
        for reg in (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP):
            self.vm.reg_write(reg, poison * 0x01010101)

    def call(self, rva, *args, loader=False):
        self._reset(*args)
        self.vm.reg_write(UC_X86_REG_ECX, MESSAGES)
        trace = self._run(rva, {RETURN - BASE}, loader=loader)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP + 4 + 4 * len(args):
            raise AssertionError('Native stack cleanup mismatch')
        return trace

    def lookup(self, selector, *, header=0xab, name=b'DiagnosticBase'):
        if (type(selector) is not int or not 0 <= selector <= 65535
                or type(header) is not int or not 0 <= header <= 255
                or type(name) is not bytes or len(name) > 15 or b'\0' in name):
            raise ValueError('Special diagnostic lookup bounds')
        self.vm.mem_write(DIAGNOSTIC, bytes((header, 0x5a)) + name.ljust(16, b'\0') + b'\x39' * 8)
        trace = self.call(0x5a120, DIAGNOSTIC, selector)
        trace['result_hex'] = bytes(self.vm.mem_read(trace['eax'], 26)).hex()
        return trace

    def stage_diagnostic_base(self, source_record_index, *, header=0xab, name=b'DiagnosticBase'):
        if (type(source_record_index) is not int or not 0 <= source_record_index < 7815
                or not self.catalog['records'][source_record_index]['lookup_visible']
                or type(header) is not int or not 0 <= header <= 255
                or type(name) is not bytes or len(name) > 15 or b'\0' in name):
            raise ValueError('Diagnostic base payload bounds')
        pointer = self.record_base + 26 * source_record_index
        start = pointer & ~4095
        end = (pointer + 26 + 4095) & ~4095
        regions = list(self.vm.mem_regions())
        for page in range(start, end, 4096):
            if not any(lo <= page <= hi for lo, hi, _ in regions):
                self.native._map_rw(page, 4096)
        payload = bytes((header, 0x5a)) + name.ljust(16, b'\0') + b'\x39' * 8
        self.vm.mem_write(pointer, payload)
        self.staged[pointer] = source_record_index
        return pointer

    def join(self, area, scene, ordinal_word, variant_word, *, poison=0xa5):
        if (any(type(v) is not int for v in (area, scene, ordinal_word, variant_word, poison))
                or not 0 <= area < 17 or not 0 <= scene <= 65535
                or not 0 <= ordinal_word <= 65535 or not 0 <= variant_word <= 65535
                or not 0 <= poison <= 255):
            raise ValueError('Variant packet bounds')
        packet = bytearray(45)
        packet[:3] = bytes((0x1c, 14, 23))
        struct.pack_into('<HHH', packet, 3, 0x1234, variant_word, ordinal_word)
        packet[9] = area
        struct.pack_into('<H', packet, 11, scene)
        self.vm.mem_write(PACKET, bytes(packet))
        self._reset(PACKET, poison=poison)
        self.vm.reg_write(UC_X86_REG_ECX, BATTLE)
        trace = self._run(0x115c90, {0x115e77, 0x116037, 0x116149, 0x11608b})
        if self.vm.reg_read(UC_X86_REG_ESP) != SP - 0x1a8:
            raise AssertionError('Consumer prefix stack mismatch')
        trace['packet_before_hex'] = packet.hex()
        trace['packet_after_hex'] = bytes(self.vm.mem_read(PACKET, 45)).hex()
        trace['metadata_hex'] = bytes(self.vm.mem_read(SP - 0x1a8 + 0x3c, 56)).hex()
        trace['input_authority'] = 'synthetic_diagnostic_only'
        return trace

    def evidence(self):
        alternate = []
        for row in self.catalog['records']:
            if row['lookup_visible'] and row['area'] == 0 and row['scene'] in (2, 3, 13):
                flags = {2: 0, 3: 0x8000, 13: 0x4000}[row['scene']]
                trace = self.join(16, 65535, flags | row['ordinal'], 0x4001)
                pointer = self.record_base + 26 * row['source_record_index']
                if (trace['edx'] != pointer or 0x115e70 not in trace['visits']
                        or 0x115e25 in trace['visits'] or trace['packet_writes']):
                    raise AssertionError('Alternate native routing mismatch')
                alternate.append({**row, 'native_pointer': pointer,
                                  'variant_word': 0x4001, 'ordinal_word': flags | row['ordinal'],
                                  'monster_classification': None, 'runtime_eligible': False})
        base = next(r for r in self.catalog['records'] if r['lookup_visible'])
        pointer = self.stage_diagnostic_base(base['source_record_index'])
        selectors = []
        for selector in range(256):
            trace = self.join(base['area'], base['scene'], base['ordinal'], 0x1c00 | selector)
            expected = RESULT if selector == 1 else pointer
            if trace['edx'] != expected or (0x115e25 in trace['visits']) != bool(selector):
                raise AssertionError('Special selector native routing mismatch')
            after = struct.unpack_from('<H', bytes.fromhex(trace['packet_after_hex']), 5)[0]
            if after != (0x1c00 if selector == 0 else (0x400 if selector == 1 else 0x1400) | selector):
                raise AssertionError('Original variant rewrite mismatch')
            if selector == 1:
                special_consumer = trace
            selectors.append({'selector': selector, 'record_pointer': trace['edx'],
                              'special_lookup_called': bool(selector),
                              'variant_after': struct.unpack_from('<H',
                                  bytes.fromhex(trace['packet_after_hex']), 5)[0]})
        row_raw = SECTION.split(b'\r\n', 1)[1]
        return {
            'schema': 'current-monster-variant-identity-v1',
            'image': {'file': str(IMAGE), 'sha256': IMAGE_SHA256, 'base': BASE,
                      'rva_equals_file_offset': True},
            'source': {'file': GAME_FILE, 'sha256': GAME_SHA256,
                       'decoded_sha256': GAME_DECODED_SHA256,
                       'decoded_offset': SECTION_START, 'end_offset_exclusive': SECTION_END,
                       'section_sha256': SECTION_SHA},
            'native_spans': {name: {'source_offset': lo, 'end_offset_exclusive': hi,
                                   'sha256': sha(self.image[lo:hi]), 'source_sha256': IMAGE_SHA256}
                             for name, (lo, hi) in SPANS.items()},
            'authority': {
                'special': 'original_5A560_with_bounded_CRT_adapters',
                'enyname': 'independently_staged_shared_source_descriptors; no_5A1A0_rerun',
                'enyname_payload': 'unmapped_except_explicit_diagnostic_pages; only_staged_records_readable',
                'diagnostic_payload_indices': list(self.staged.values()),
                'allocation_poison': self.poison,
                'packets': 'synthetic_diagnostic_only',
                'crt_adapters': {hex(rva): name for rva, (name, _) in SERVICES.items()},
            },
            'special_records': [{
                'bank': 'SpecialEnyInfo', 'source_record_index': 0, 'lookup_ordinal': 1,
                'source_label_raw': '1', 'decoded_offset': SECTION_START + len(b'SpecialEnyInfo,1\r\n'),
                'source_line': self.plain[:SECTION_START].count(b'\n') + 2,
                'raw_record_hex': row_raw.hex(), 'record_sha256': sha(row_raw),
                'native_record_hex': self.loaded_record.hex(),
                'native_initialized_byte_offsets': list(range(6)),
                'native_uninitialized_byte_offsets': list(range(6, 26)),
                'monster_classification': None, 'fields': dict.fromkeys(FIELDS),
                'runtime_eligible': False}],
            'loader_trace': self.loader_trace,
            'special_consumer': {
                'base_identity': {key: base[key] for key in
                                  ('source_record_index', 'area_generation', 'area', 'scene', 'ordinal')},
                'special_lookup_ordinal': 1,
                'base_payload_authority': 'independently_staged_synthetic_header_and_name',
                'trace': special_consumer,
                'lookup_trace': self.lookup(1),
            },
            'alternate_records': alternate, 'selector_counterfactuals': selectors,
            'coverage': {'special_source_rows': 1, 'special_native_rows_loaded': 1,
                         'alternate_lookup_records': len(alternate),
                         'alternate_scenes': {str(scene): sum(r['scene'] == scene for r in alternate)
                                              for scene in (2, 3, 13)},
                         'low_byte_selectors_checked': 256,
                         'verified_stat_skill_drop_assignments': 0,
                         'all_monster_systems_enumerated': False,
                         'all_monsters_including_boss_denominator': None,
                         'boss_record_count': None},
            'remaining_frontier': [
                'Original sender of 1C variant/ordinal/identity fields and classifier evidence.',
                'Dispatch field values 0x2000 -> 116149 and 0x6000 -> 11608B; stopped at entries.',
                'Continuation 115E77 onward and identity-bound base stats, skills and drop producers.',
                'Special combined with every real base payload requires attached original loader output; '
                'diagnostic inherited bytes do not qualify monster attributes.'],
            'runtime_eligible': False,
        }


def main():
    print(json.dumps(VariantIdentityProbe().evidence(), ensure_ascii=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
