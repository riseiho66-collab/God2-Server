"""Pinned ACTMIS bytes -> native parser -> category-20 requirement consumer.

Offline, bounded x86 slices only. No game function is replaced. File I/O,
allocation and the producer of the input instance are outside this oracle.
Run with python -B -m tools.strike_lab.current_quest_requirements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .omega_assets import decode_csvz
from .recover_quests import parse_table

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
CLIENT = ROOT.parent / 'God2'
SOURCE = 'Data2/Patch/Comm/ActMis.csvZ'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_SHA = 'e1e35ee689d12ef265be8620b21f856709976896a46edeb9f31c15622041accf'
DECODED_SHA = '10f76969d60d3a46fdd937510f1b480bc12a07b4a07b7f98774fa6df9df97548'
BASE, RESOURCE, STACK, SP = 0x400000, 0x2000000, 0x3000000, 0x3008000
ROWS, LABELS, INPUT, INSTANCE, NAMES, UI = (
    0x4000000, 0x4001000, 0x5000000, 0x5001000, 0x5002000, 0x6000000)
RETURN = STACK + 0xf000
COUNT, STRIDE = 169, 20
LOOKUP_FIXTURE_NAME = b'lookup-fixture'


def pinned(raw, expected, label):
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Pinned ' + label + ' changed; requalification required')
    return raw


def evidence(client=CLIENT, image=IMAGE):
    image_bytes = pinned(Path(image).read_bytes(), IMAGE_SHA, 'image')
    root = Path(client).resolve()
    source = (root / SOURCE).resolve()
    if not source.is_relative_to(root):
        raise ValueError('ACTMIS source escapes client root')
    raw = pinned(source.read_bytes(), SOURCE_SHA, 'ACTMIS source')
    decoded = pinned(decode_csvz(raw), DECODED_SHA, 'decoded ACTMIS')
    table = parse_table('requirements', decoded)
    if table['declared_records'] != COUNT or len(table['records']) != COUNT:
        raise ValueError('Changed ACTMIS count')
    table.update(source_sha256=SOURCE_SHA, decoded_sha256=DECODED_SHA)
    return image_bytes, table


def source_row(row):
    return (b','.join(bytes.fromhex(f) for f in row['raw_fields_hex'])
            + bytes.fromhex(row['line_ending_hex']))


class NativeRequirements:
    """Real parser/consumer code with explicit memory input and output boundaries."""

    def __init__(self, image):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
        from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
        from unicorn import x86_const
        pinned(image, IMAGE_SHA, 'image')
        self.reg = x86_const
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.image = image
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095)
        self.vm.mem_write(BASE, image)
        self.vm.mem_protect(BASE, (len(image) + 4095) & ~4095,
                            UC_PROT_READ | UC_PROT_EXEC)
        for address, size in ((RESOURCE, 0xe0000), (STACK, 0x10000),
                              (ROWS, 0x20000), (INPUT, 0x20000), (UI, 0x100000)):
            self.vm.mem_map(address, size)
        self.write(RESOURCE + 8, '<H', 10)  # Native tokenizer column capacity.
        self.write(RESOURCE + 0xb2c5c, '<I', ROWS)
        self.write(UI + 0xcff70, '<I', RESOURCE)
        self.stops = set()
        self.mode = None
        self.reads, self.lookups, self.formats = [], [], []
        self.vm.hook_add(UC_HOOK_CODE, self._code)
        self.vm.hook_add(UC_HOOK_MEM_READ, self._read)

    def write(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def read(self, address, fmt):
        return struct.unpack(fmt, self.vm.mem_read(address, struct.calcsize(fmt)))

    def setreg(self, name, value):
        self.vm.reg_write(getattr(self.reg, 'UC_X86_REG_' + name), value)

    def getreg(self, name):
        return self.vm.reg_read(getattr(self.reg, 'UC_X86_REG_' + name))

    def _code(self, vm, address, size, context):
        if address in self.stops:
            vm.emu_stop()
            return
        if not BASE <= address < BASE + len(self.image):
            raise AssertionError('Execution escaped pinned image')
        if address - BASE in (0x51a90, 0x147973, 0x147e23):
            raise AssertionError('Unexpected file I/O or allocation')
        if self.mode == 'consumer' and address == BASE + 0x59a60:
            self.lookups.append(self.read(self.getreg('ESP') + 4, '<H')[0])
        if self.mode == 'consumer' and address == BASE + 0x147af7:
            _, dest, fmt, name, quantity = self.read(self.getreg('ESP'), '<5I')
            self.formats.append({'format_rva': fmt - BASE, 'quantity': quantity,
                                 'name_hex': self.cstring(name).hex()})

    def _read(self, vm, access, address, size, value, context):
        if self.mode == 'consumer' and ROWS <= address < ROWS + COUNT * STRIDE:
            self.reads.append({'rva': self.getreg('EIP') - BASE,
                               'row_offset': address - ROWS, 'size': size})

    def run(self, start, *stops):
        self.stops = set(stops)
        self.vm.emu_start(BASE + start, 0, count=200000)
        end = self.getreg('EIP')
        if end not in self.stops:
            raise AssertionError('Native slice exceeded instruction bound')
        return end

    def cstring(self, address, limit=1024):
        raw = bytes(self.vm.mem_read(address, limit))
        if b'\0' not in raw:
            raise AssertionError('Unterminated native string')
        return raw.split(b'\0', 1)[0]

    def load_row(self, raw):
        """Tokenize exact row bytes; execute key check and all four pair stores.

        Start after file read, stop before malloc, provide its storage as the
        next slice's input. Neither allocator nor file reader is hooked/stubbed.
        """
        fields = raw.rstrip(b'\r\n').split(b',')
        if (len(fields) != 10 or b'\0' in raw or not raw.endswith(b'\n')
                or len(raw) > 4095 or any(len(f) >= 380 for f in fields)):
            raise ValueError('Row outside bounded tokenizer fixture')
        self.mode = 'loader'
        self.vm.mem_write(INPUT, raw + b'\0')
        self.setreg('ESP', SP)
        self.setreg('ECX', RESOURCE)
        self.write(SP, '<II', RETURN, INPUT)
        self.run(0x51be0, RETURN)
        if self.getreg('EAX') != 10:
            raise AssertionError('Native tokenizer did not read ten columns')
        self.setreg('ESP', SP)
        self.setreg('EBP', RESOURCE)
        self.setreg('ESI', COUNT)
        end = self.run(0x587c4, BASE + 0x58807, BASE + 0x588e7)
        if end == BASE + 0x588e7:
            return None  # Native signed key bounds rejected this record.
        index = self.read(SP + 0x10, '<I')[0]
        label = LABELS + index * 512
        self.setreg('EAX', label)
        self.run(0x5880c, BASE + 0x588e7)
        packed = bytes(self.vm.mem_read(ROWS + STRIDE * index, STRIDE))
        pointer, *values = struct.unpack('<I4B4HB3x', packed)
        return {'serial': index + 1, 'native_hex': packed.hex(),
                'label_hex': self.cstring(pointer).hex(),
                'quantities_u8': values[:4], 'item_keys_u16': values[4:8],
                'nonzero_pair_count': values[8]}

    def consume(self, serial, lookup_keys=(), header=20 << 16):
        """Run native type dispatch and text assembly to RVA BBBCE.

        Lookup slots are either null or point at an explicitly synthetic name.
        The real 59A60 resolver and CRT formatter execute unmodified. This
        tests the ACTMIS key/quantity contract, not an item catalog join.
        """
        if not 0 <= serial <= 0xffff or not 0 <= header <= 0xffffffff:
            raise ValueError('Input record fields exceed native widths')
        return self.consume_instance(struct.pack('<I4xH10x', header, serial), lookup_keys)

    def consume_instance(self, instance, lookup_keys=()):
        """Consume exact 20-byte instance output from the native storage slice."""
        if len(instance)!=20:
            raise ValueError('Native instance must contain exactly 20 bytes')
        header=struct.unpack_from('<I',instance)[0]
        if (header >> 16) & 63 != 20:
            raise ValueError('Only category-20 consumer is in this slice')
        self.vm.mem_write(RESOURCE + 0xb2d40, bytes(0x7f58 * 4))
        self.vm.mem_write(NAMES + 8, LOOKUP_FIXTURE_NAME + b'\0')
        for key in lookup_keys:
            if not 0 <= key < 0x7f58:
                raise ValueError('Lookup fixture key outside native table')
            self.write(RESOURCE + 0xb2d40 + 4 * key, '<I', NAMES)
        self.vm.mem_write(INSTANCE, bytes(instance))
        self.write(SP + 0x11ac, '<I', INSTANCE)
        self.vm.mem_write(SP + 0x3bc, b'\0')
        self.setreg('ESP', SP)
        self.setreg('EBP', UI)
        self.setreg('EAX', header)
        self.mode = 'consumer'
        self.reads, self.lookups, self.formats = [], [], []
        self.run(0xb6424, BASE + 0xbbbce)
        return {'text_hex': self.cstring(SP + 0x3bc).hex(),
                'lookup_keys': self.lookups.copy(), 'format_calls': self.formats.copy(),
                'record_reads': self.reads.copy()}


def build_report(client=CLIENT, image=IMAGE):
    image_bytes, table = evidence(client, image)
    native = NativeRequirements(image_bytes)
    records = []
    for row in table['records']:
        record = native.load_row(source_row(row))
        if record is None:
            raise AssertionError('Native loader rejected pinned source row')
        records.append({'source_line': row['source_line'], **record})
    for record in records:
        keys = record['item_keys_u16'][:record['nonzero_pair_count']]
        result = native.consume(record['serial'], keys)
        expected = bytes.fromhex(record['label_hex']) + b''.join(
            b'\n' + LOOKUP_FIXTURE_NAME + b' x ' + str(q).encode('ascii')
            for q in record['quantities_u8'][:len(keys)])
        if result['lookup_keys'] != keys or bytes.fromhex(result['text_hex']) != expected:
            raise AssertionError('Source record disagrees with native consumer')
        record['consumer'] = result
    return {'schema': 'current-actmis-native-consumer-v1', 'image_sha256': IMAGE_SHA,
            'source_table': table, 'records': records,
            'qualification': 'Native requirement presentation slice; no server rule',
            'lookup_fixture': 'Synthetic name only; no item catalog join claimed',
            'proven_key': 'category=(instance.dword[0]>>16)&63 == 20; '
                          'instance.u16[8] -> ACTMIS serial -> row[serial-1]',
            'boundaries': {'file_read': 'Input is decoded original row bytes',
                           'allocation': 'Preallocated table and per-row label storage',
                           'consumer_entry_rva': 0xb6424,
                           'consumer_exit_rva': 0xbbbce,
                           'input_record': 'Staged instance, not a captured server packet'},
            'next_rule_gap': 'Native logical 3B -> instance.u16[8] is covered by '
                             'current_quest_instance; original server serial selection, '
                             'live category-20 UI and turn-in validation/consumption '
                             'remain unproven. This reader only assembles text.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=CLIENT)
    parser.add_argument('--image', type=Path, default=IMAGE)
    parser.add_argument('--json', action='store_true', help='Print reversible evidence and read traces')
    args = parser.parse_args(argv)
    report = build_report(args.client, args.image)
    result = report if args.json else {
        'native_rows_verified': len(report['records']), 'image_sha256': IMAGE_SHA,
        'proven_key': report['proven_key'], 'next_rule_gap': report['next_rule_gap']}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
