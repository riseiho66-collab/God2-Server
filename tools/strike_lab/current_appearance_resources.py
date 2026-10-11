"""Source-backed HeroDoll table oracle, not a runtime appearance serializer.

Executes pinned native CSV tokenization, record loading, key conversion, hash
lookup and derived-value consumers. Adapts only bounded CRT/CString operations.
No process, socket, UI, asset handle fabrication or production mutation.
"""
import csv
import hashlib
import io
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_PROT_READ,
                     UC_PROT_EXEC, UC_MEM_READ, UC_MEM_WRITE)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                              UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_ESI,
                              UC_X86_REG_ESP, UC_X86_REG_EIP)
from tools.strike_lab.omega_assets import decode_csvz

BASE, STACK, TABLE, RECORDS, INDEX, NODES, STRINGS, INPUT = (
    0x400000, 0x3000000, 0x3100000, 0x3200000, 0x3300000,
    0x3400000, 0x3500000, 0x3600000)
SP, STOP = STACK + 0x8000, BASE + 0x1000
BANK = 0x3700000
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_SHA = 'df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359'
DECODED_SHA = '0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2'
DRV_SOURCE_SHA = '9af4b2ed4d5b007bfde12f2cff4e9895715903a8ffaf5a356aee011f3fb98f2e'
DRV_DECODED_SHA = '72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0'


def source_rows(client_root=ROOT.parent / 'God2'):
    raw = (Path(client_root) / 'Data2/Patch/HeroDoll.csvZ').read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Current HeroDoll CSVZ changed')
    decoded = decode_csvz(raw, limit=1024*1024)
    if hashlib.sha256(decoded).hexdigest() != DECODED_SHA:
        raise ValueError('Decoded HeroDoll changed')
    # Latin-1 preserves every byte; no localization/encoding substitutions.
    rows = list(csv.reader(io.StringIO(decoded.decode('latin1'))))
    start, count = int(rows[0][2]), int(rows[0][4])
    selected = rows[start-1:]
    if start != 26 or count != 918 or len(selected) != count:
        raise ValueError('Unexpected current table boundaries')
    keys = [row[0] + row[1] for row in selected]
    if len(set(keys)) != count or any(len(row) not in (6, 7) for row in selected):
        raise ValueError('Invalid source rows')
    return decoded.splitlines(keepends=True)[start-1:], selected


class AppearanceResources:
    def __init__(self, client_root=ROOT.parent / 'God2'):
        image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                 'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
            raise ValueError('Pinned client image changed')
        self.lines, self.rows = source_rows(client_root)
        self.vm = v = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (len(image)+4095) & ~4095
        v.mem_map(BASE, size)
        v.mem_write(BASE, image)
        v.mem_protect(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
        for address, length in ((STACK, 0x10000), (TABLE, 0x20000),
                                (RECORDS, 0x10000), (INDEX, 0x10000),
                                (NODES, 0x10000), (STRINGS, 0x10000), (INPUT, 0x10000),
                                (BANK, 0x60000), (0, 4096)):
            v.mem_map(address, length)
        v.mem_write(0, struct.pack('<I', 0xffffffff))
        v.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._seh, begin=0, end=4095)
        for rva in (0x1480b4, 0x157f67, 0x158e89, 0x15ad35):
            v.hook_add(UC_HOOK_CODE, self._stdlib, begin=BASE+rva, end=BASE+rva)
        self.events = []
        v.hook_add(UC_HOOK_CODE, self._lookup_event, begin=BASE+0x52460, end=BASE+0x52460)
        self.put32(TABLE+0x121ec, RECORDS)
        self.put32(TABLE+0x78, len(self.rows))
        v.mem_write(TABLE+4+8, struct.pack('<H', 7))
        self.by_key = {}
        for ordinal, (line, row) in enumerate(zip(self.lines, self.rows)):
            if len(line) >= 4096 or len(row[3].encode('latin1')) > 29:
                raise ValueError('Source field exceeds native bounds')
            v.mem_write(INPUT, line+b'\0')
            self.call(0x51be0, INPUT, this=TABLE+4)
            self.put32(TABLE+0x121f0, ordinal)
            v.reg_write(UC_X86_REG_ESP, SP)
            v.reg_write(UC_X86_REG_EBP, TABLE)
            v.reg_write(UC_X86_REG_EBX, TABLE+4)
            self.run(0x5201c, 0x521a2)
            if v.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Native record loader stack mismatch')
            ptr = RECORDS+ordinal*44
            self.by_key[(row[0]+row[1]).lower()] = ptr
        # Native CMapStringToPtr node/bucket layout from 15A60C/15A6A6.
        # Only the container allocation/insertion is reconstructed; values are
        # original loader output, and original hash/comparison/lookup executes.
        buckets = 1103
        self.put32(INDEX+4, INDEX+0x100)
        self.put32(INDEX+8, buckets)
        for i, (key, ptr) in enumerate(self.by_key.items()):
            raw = key.encode('ascii')
            h = 0
            for byte in raw:
                h = (h*33+byte) & 0xffffffff
            bucket = h % buckets
            head = INDEX+0x100+bucket*4
            node, string = NODES+i*16, STRINGS+i*32
            v.mem_write(string, raw+b'\0')
            v.mem_write(node, struct.pack('<4I', self.u32(head), bucket, string, ptr))
            self.put32(head, node)
        self.put32(TABLE+0x121f4, INDEX)
        self.put32(TABLE+0x121f0, len(self.rows))
        v.mem_protect(RECORDS, 0x10000, UC_PROT_READ)
        self._load_driver_table(client_root)

    def _load_driver_table(self, client_root):
        raw = (Path(client_root) / 'Data2/Patch/Drv.csvZ').read_bytes()
        if hashlib.sha256(raw).hexdigest() != DRV_SOURCE_SHA:
            raise ValueError('Current Drv CSVZ changed')
        decoded = decode_csvz(raw, limit=1024*1024)
        if hashlib.sha256(decoded).hexdigest() != DRV_DECODED_SHA:
            raise ValueError('Decoded Drv changed')
        rows = list(csv.reader(io.StringIO(decoded.decode('latin1'))))
        start = int(rows[0][2])
        self.driver_rows = rows[start-1:]
        if (start != 10 or len(self.driver_rows) != 92
                or [int(row[0]) for row in self.driver_rows] != list(range(92))):
            raise ValueError('Unexpected current Drv boundaries')
        self.vm.mem_write(BANK+8, struct.pack('<H', 8))
        for ordinal, (line, row) in enumerate(zip(
                decoded.splitlines(keepends=True)[start-1:], self.driver_rows)):
            if len(line) >= 4096 or len(row[1].encode('ascii')) >= 16:
                raise ValueError('Drv source exceeds native field bounds')
            self.vm.mem_write(INPUT, line+b'\0')
            self.call(0x51be0, INPUT, this=BANK)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_ESI, BANK)
            # Original first-field check, record writes and count increment.
            self.run(0x632c5, 0x633e5)
            if (self.vm.reg_read(UC_X86_REG_ESP) != SP
                    or self.driver_count != ordinal+1):
                raise AssertionError('Native Drv loader contract changed')
        # Share native-produced HeroDoll records through the world's real bank
        # offsets; no action result, record value or cached ROM is synthesized.
        self.vm.mem_write(BANK+0x12d78+0x121ec,
                          bytes(self.vm.mem_read(TABLE+0x121ec, 12)))

    @property
    def driver_count(self):
        return struct.unpack('<H', self.vm.mem_read(BANK+0x121f6, 2))[0]

    def driver_action(self, selector):
        # 63780 uses a signed WORD comparison, so negative WORDs must never be
        # admitted by this bounded oracle's public API.
        if not isinstance(selector, int) or not 0 <= selector <= 0x7fff:
            raise ValueError('Nonnegative signed WORD selector required')
        return self.call(0x63780, selector, this=BANK) & 0xffff

    def put32(self, address, value):
        self.vm.mem_write(address, struct.pack('<I', value & 0xffffffff))

    def u32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]

    def string(self, address, limit=4096):
        result = bytearray()
        for i in range(limit):
            byte = self.vm.mem_read(address+i, 1)[0]
            if not byte:
                return bytes(result)
            result.append(byte)
        raise ValueError('Unterminated native string')

    def run(self, start, stop=0x1000):
        # A prior run may have cached a basic block crossing this slice's end.
        # An exact hook keeps repeated slices from continuing into ROM loading.
        end_hook = self.vm.hook_add(
            UC_HOOK_CODE, lambda vm, address, size, data: vm.emu_stop(),
            begin=BASE+stop, end=BASE+stop)
        try:
            self.vm.emu_start(BASE+start, BASE+stop, timeout=1000000, count=100000)
        finally:
            self.vm.hook_del(end_hook)
        if self.vm.reg_read(UC_X86_REG_EIP) != BASE+stop:
            raise AssertionError('Native instruction bound reached')

    def call(self, rva, *args, this=TABLE):
        self.vm.mem_write(SP, struct.pack('<'+'I'*(len(args)+1), STOP, *args))
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_ECX, this)
        self.run(rva)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP+4+len(args)*4:
            raise AssertionError('Native call stack mismatch')
        return self.vm.reg_read(UC_X86_REG_EAX)

    def lookup(self, *key):
        if len(key) != 5 or any(not 0 <= n <= 255 for n in key):
            raise ValueError('Five byte lookup arguments required')
        if key[1] > 3 or key[4] > 2:
            raise ValueError('Outside native component/action bounds')
        return self.call(0x52460, *key)

    def record(self, ptr):
        if ptr not in self.by_key.values():
            raise ValueError('Not a source-backed record')
        return bytes(self.vm.mem_read(ptr, 44))

    def _lookup_event(self, vm, address, size, context):
        sp = vm.reg_read(UC_X86_REG_ESP)
        self.events.append(tuple(n & 255 for n in struct.unpack('<5I', vm.mem_read(sp+4, 20))))

    def _seh(self, vm, access, address, size, value, context):
        pc = vm.reg_read(UC_X86_REG_EIP)-BASE
        allowed = {
            0x52467: (UC_MEM_READ, b'\x64\xa1\0\0\0\0'),
            0x5246e: (UC_MEM_WRITE, b'\x64\x89\x25\0\0\0\0'),
            0x5251b: (UC_MEM_WRITE, b'\x64\x89\x0d\0\0\0\0'),
            0x52541: (UC_MEM_WRITE, b'\x64\x89\x0d\0\0\0\0'),
        }
        expected = allowed.get(pc)
        if (address != 0 or size != 4 or expected is None or access != expected[0]
                or bytes(vm.mem_read(BASE+pc, len(expected[1]))) != expected[1]):
            raise AssertionError('Non-SEH low-page access')

    def _stdlib(self, vm, address, size, context):
        sp = vm.reg_read(UC_X86_REG_ESP)
        rva, cleanup, result = address-BASE, 0, 0
        if rva == 0x1480b4:
            source, fmt, output = (self.u32(sp+4*i) for i in (1, 2, 3))
            if self.string(fmt) != b'%d':
                raise AssertionError('Unexpected sscanf format')
            text = self.string(source).strip()
            if not text.isdigit():
                raise AssertionError('Non-decimal source field')
            self.put32(output, int(text))
            result = 1
        elif rva == 0x157f67:
            ptr = self.u32(sp+4)
            text = self.string(ptr)
            if not text.isascii():
                raise AssertionError('Unexpected non-ASCII key/file')
            vm.mem_write(ptr, text.lower()+b'\0')
            result = ptr
        elif rva == 0x158e89:
            dest, fmt, binary, component, category, ordinal = struct.unpack('<6I', vm.mem_read(sp+4, 24))
            if self.string(fmt) != b'r%d%c%d%02d':
                raise AssertionError('Unexpected CString format')
            text = f'r{binary}{chr(component)}{category}{ordinal:02d}'.encode('ascii')
            vm.mem_write(INPUT+0x2000, text+b'\0')
            self.put32(dest, INPUT+0x2000)
        elif rva == 0x15ad35:
            # Scratch CString owns no emulated heap allocation.
            if self.u32(vm.reg_read(UC_X86_REG_ECX)) != INPUT+0x2000:
                raise AssertionError('Unexpected CString destruction')
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
