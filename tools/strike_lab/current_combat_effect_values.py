"""Pinned ChangeDollEffect row -> native record -> native text consumer.

File/decompression and allocation are explicit boundaries. Original tokenizer,
numeric conversion, loader stores, lookup and formatting execute without stubs.
No effect coefficient is inferred from a description or a skipped CSV column.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from . import recover_combat_rules as pins
from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_WRITE,
                     UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE)
from unicorn import x86_const as reg

BASE, RESOURCE, STACK, INPUT, ROWS, LABELS, CONTEXT, INSTANCE, NAMES = (
    0x400000, 0x2000000, 0x3000000, 0x4000000, 0x4100000,
    0x4200000, 0x5000000, 0x6000000, 0x6100000)
SP, RETURN = STACK + 0x8000, STACK + 0xff00
DECODED_SHA256 = '565620cfafa678e13b76b833631d7c13fb55abeb30f5e0981dc24b15b317de08'
STRIDE, FIELD_STRIDE = 8, 0x17c
FIXTURE_LABEL = b'effect-fixture'
SLICES = {
    'header_dispatch': (0x56e85, 0x56ed0),
    'loader': (0x5beb0, 0x5bff4),
    'tokenizer': (0x51be0, 0x51cd2),
    'field_access_and_integer_conversion': (0x51ae0, 0x51bdc),
    'record_lookup': (0x5c0b0, 0x5c0f8),
    'index_check': (0x5c120, 0x5c139),
    'text_consumer': (0xbb8b4, 0xbb97c),
}
RANGES = (*SLICES.values(), (0x147000, 0x16f000))


def sources():
    image = pins.read_pinned(pins.IMAGE, pins.IMAGE_SHA256)
    decoded = decode_csvz(pins.read_pinned(pins.CLIENT / pins.EFFECTS,
                                          pins.SOURCE_HASHES[pins.EFFECTS]))
    if pins.sha256(decoded) != DECODED_SHA256:
        raise ValueError('Pinned decoded effect source changed')
    lines = decoded.splitlines(keepends=True)
    if lines[3].rstrip(b'\r\n') != b'ChangeDollEffectCount,1202':
        raise ValueError('Unexpected current section marker')
    rows, offset = [], sum(map(len, lines[:4]))
    for line, raw in enumerate(lines[4:], 5):
        rows.append({'line': line, 'offset': offset, 'raw': raw,
                     'sha256': pins.sha256(raw.rstrip(b'\r\n'))})
        offset += len(raw)
    if len(rows) != 1202:
        raise ValueError('Incomplete current effect source')
    return image, rows


class NativeEffectValues:
    def __init__(self, image):
        if pins.sha256(image) != pins.IMAGE_SHA256:
            raise ValueError('Pinned image changed')
        self.image = image
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        for address, size in ((RESOURCE, 0xe0000), (STACK, 0x10000),
                              (INPUT, 0x1000), (ROWS, 0x4000), (LABELS, 0xa0000),
                              (CONTEXT, 0xe0000), (INSTANCE, 0x1000), (NAMES, 0x2000)):
            self.vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_protect(RETURN & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(RETURN, b'\xf4')
        self.vm.mem_write(ROWS, b'\xa5' * (1203 * STRIDE))
        self.put(RESOURCE + 8, '<H', 5)
        self.put(RESOURCE + 0xd2ab4, '<I', ROWS)
        self.put(RESOURCE + 0xd2ab8, '<H', 0)
        self.stops, self.phase = set(), ''
        self.trace, self.columns, self.token_reads, self.writes = [], [], [], []
        self.vm.hook_add(UC_HOOK_CODE, self.code)
        self.vm.hook_add(UC_HOOK_MEM_READ, self.read_hook)
        self.vm.hook_add(UC_HOOK_MEM_WRITE, self.write_hook)

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def get(self, address, fmt):
        return struct.unpack(fmt, self.vm.mem_read(address, struct.calcsize(fmt)))

    def register(self, name, value=None):
        key = getattr(reg, 'UC_X86_REG_' + name)
        if value is None:
            return self.vm.reg_read(key)
        self.vm.reg_write(key, value)

    def code(self, vm, address, size, data):
        if address in self.stops:
            vm.emu_stop()
            return
        rva = address - BASE
        if not any(lo <= rva and rva + size <= hi for lo, hi in RANGES):
            raise AssertionError(f'Outside qualified native ranges: {rva:X}')
        if rva in (0x51a90, 0x147973, 0x147e23):
            raise AssertionError('File reader or allocator must not execute')
        self.trace.append(rva)
        if self.phase == 'row' and rva == 0x51b60:
            self.columns.append(self.get(self.register('ESP') + 4, '<I')[0])

    def read_hook(self, vm, access, address, size, value, data):
        if self.phase == 'row' and RESOURCE + 0x78 <= address < RESOURCE + 0x78 + 5 * FIELD_STRIDE:
            self.token_reads.append((self.register('EIP') - BASE,
                                     (address - RESOURCE - 0x78) // FIELD_STRIDE, size))

    def write_hook(self, vm, access, address, size, value, data):
        if not STACK <= address < STACK + 0x10000:
            self.writes.append((self.register('EIP') - BASE, address, size, value))

    def run(self, start, *stops):
        self.stops = set(stops)
        self.vm.emu_start(BASE + start, 0, count=100000, timeout=1000000)
        if self.register('EIP') not in self.stops:
            raise AssertionError('Native slice exceeded instruction/time budget')
        return self.register('EIP')

    def cstring(self, address, limit=2048):
        raw = bytes(self.vm.mem_read(address, limit))
        if b'\0' not in raw:
            raise AssertionError('Unterminated native output')
        return raw.split(b'\0', 1)[0]

    def tokenize(self, raw):
        if type(raw) is not bytes:
            raise ValueError('Native tokenizer input must be exact bytes')
        # Declared CRT text-mode boundary: CRLF becomes LF before the tokenizer.
        raw = raw.replace(b'\r\n', b'\n')
        if (not raw.endswith(b'\n') or b'\0' in raw or
                len(raw) >= 4096 or raw.count(b',') >= 5 or
                any(len(f) >= FIELD_STRIDE for f in raw[:-1].split(b','))):
            raise ValueError('Outside bounded native tokenizer inputs')
        self.phase = 'tokenizer'
        self.vm.mem_write(INPUT, raw + b'\0')
        self.put(SP, '<2I', RETURN, INPUT)
        self.register('ESP', SP)
        self.register('ECX', RESOURCE)
        self.run(0x51be0, RETURN)
        if self.register('ESP') != SP + 8:
            raise AssertionError('Tokenizer stack imbalance')
        return self.register('EAX')

    def header(self):
        self.tokenize(b'ChangeDollEffectCount,1202\r\n')
        self.put(SP, '<2I', RETURN, 1)
        self.register('ESP', SP)
        self.register('ECX', RESOURCE)
        self.run(0x51ba0, RETURN)
        count = self.register('EAX')
        self.register('ESP', SP)
        self.register('EDI', RESOURCE)
        self.put(SP + 0xc, '<I', count)
        self.vm.mem_write(SP + 0x18, self.cstring(RESOURCE + 0x78) + b'\0')
        self.trace.clear()
        self.run(0x56e85, BASE + 0x5bedf)
        # Stop before original calloc; its actual arguments establish row stride.
        return {'native_count': count, 'allocation_arguments': list(self.get(self.register('ESP'), '<2I')),
                'loader_reached': 0x5beb0 in self.trace, 'stop_rva': '0x5bedf'}

    def load_row(self, raw):
        if self.tokenize(raw) != 5:
            raise ValueError('Expected exactly five source fields')
        self.phase = 'row'
        self.columns.clear()
        self.token_reads.clear()
        self.writes.clear()
        self.trace.clear()
        self.register('ESP', SP)
        self.register('EBP', RESOURCE)
        self.register('EBX', 1202)
        stop = self.run(0x5bf0c, BASE + 0x5bf77, BASE + 0x5bfd1)
        index = self.get(SP + 0x10, '<i')[0]
        if stop != BASE + 0x5bf77:
            raise ValueError('Row rejected or empty description: outside qualified source subset')
        requested, = self.get(self.register('ESP'), '<I')
        pointer = LABELS + index * 512
        if not 0 <= index < 1202 or requested > 512:
            raise ValueError('Native row outside prepared memory')
        # Independent post-allocation live-in. Neither allocator is stubbed.
        self.register('EAX', pointer)
        self.run(0x5bf7c, BASE + 0x5bfd1)
        if self.register('ESP') != SP:
            raise AssertionError('Loader continuation stack imbalance')
        packed = bytes(self.vm.mem_read(ROWS + index * STRIDE, STRIDE))
        return {'index': index, 'native_record_hex': packed.hex(),
                'description_hex': self.cstring(pointer).hex(),
                'allocation_bytes': requested, 'columns_requested': list(self.columns),
                'token_columns_read': sorted({col for _, col, _ in self.token_reads}),
                'record_writes': [{'rva': hex(rva), 'offset': address - ROWS - index * STRIDE,
                                   'bytes': size} for rva, address, size, _ in self.writes
                                  if ROWS + index * STRIDE <= address < ROWS + (index + 1) * STRIDE]}

    def consume(self, index):
        if type(index) is not int or not 1 <= index < 1202:
            raise ValueError('Qualified first consumer slot requires nonzero current effect ID')
        self.phase = 'consumer'
        self.put(CONTEXT + 0xcff70, '<I', RESOURCE)
        self.put(INSTANCE + 4, '<I', index << 16)
        self.put(RESOURCE + 0xb2c6c, '<H', 0x249)
        self.put(RESOURCE + 0xb2c68, '<I', NAMES)
        self.put(NAMES + 0x920, '<I', NAMES + 0x1000)
        self.vm.mem_write(NAMES + 0x1000, FIXTURE_LABEL + b'\0')
        self.put(SP + 0x11ac, '<I', INSTANCE)
        self.vm.mem_write(SP + 0x3bc, b'\0' * 512)
        self.register('ESP', SP)
        self.register('EBP', CONTEXT)
        self.trace.clear()
        self.run(0xbb8b4, BASE + 0xbb935, BASE + 0xbb97c)
        if self.register('EIP') != BASE + 0xbb935:
            raise ValueError('Native index guard rejected effect')
        dest, fmt, label, description = self.get(self.register('ESP'), '<4I')
        arguments = {'format_hex': self.cstring(fmt).hex(), 'format_rva': hex(fmt - BASE),
                     'description_pointer': description, 'description_hex': self.cstring(description).hex(),
                     'label_hex': self.cstring(label).hex()}
        # Continue at the real CALL, through original CRT formatter and append.
        self.run(0xbb935, BASE + 0xbb97c)
        if self.register('ESP') != SP:
            raise AssertionError('Consumer stack imbalance')
        return {**arguments, 'text_hex': self.cstring(SP + 0x3bc).hex(),
                'native_lookup_executed': 0x5c0b0 in self.trace,
                'native_formatter_executed': 0x147af7 in self.trace,
                'next_stop_rva': '0xbb97c'}


def evidence():
    image, rows = sources()
    native = NativeEffectValues(image)
    header = native.header()
    examples = []
    for index in (2, 302, 936, 1201):
        row = rows[index]
        loaded = native.load_row(row['raw'])
        examples.append({'source_line': row['line'], 'decoded_offset': row['offset'],
                         'row_sha256': row['sha256'],
                         'raw_code_hex': row['raw'].split(b',')[2].hex(),
                         'raw_basic_value': row['raw'].split(b',')[3].decode('ascii'),
                         'loaded': loaded, 'consumer': native.consume(index)})
    return {'source': pins.EFFECTS, 'source_sha256': pins.SOURCE_HASHES[pins.EFFECTS],
        'decoded_sha256': DECODED_SHA256, 'image_sha256': pins.IMAGE_SHA256,
        'source_records': len(rows), 'sampled_records_executed': len(examples),
        'boundaries': [
            'Pinned csvZ decoded outside VM; CRLF converted to LF before original tokenizer.',
            'Header stops before calloc; row execution resumes with prepared table owner.',
            'Each row stops before malloc; continuation receives an explicit fixture allocation pointer.',
            'Consumer item high-WORD effect ID, resource owner and label pointer are fixtures.',
            'Original lookup, sprintf and append execute; no file IO, allocator or live gameplay executed.'],
        'header': header, 'examples': examples,
        'slices': {name: {'start_rva': hex(lo), 'end_rva_exclusive': hex(hi),
                          'sha256': hashlib.sha256(image[lo:hi]).hexdigest()}
                   for name, (lo, hi) in SLICES.items()},
        'result': 'This loader retains an index WORD and description pointer. '
            'Category, effect-code and basic-value columns remain tokenizer text and '
            'are not selected by this row loader. The traced consumer formats the description.',
        'authority': 'No attack/defense/hit/crit/element coefficient producer proved by this edge.'}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(evidence(), ensure_ascii=True, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
