"""Current opcode 72 record oracle. Original bounded x86, synthetic inputs only.

No imports of earlier NPC recovery work, game stubs, assets, or world policy.
Outputs evidence to stdout only. Slice results are not live playable proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
import unicorn as uc
from unicorn import x86_const as x86

BASE = 0x400000
RANGES = {
    'length_wrapper': (0x1000, 0x1013),
    'length_switch': (0x1200, 0x1216),
    'length_72': (0x127c, 0x1282),
    'dispatch': (0x68b4c, 0x68b68),
    'selectors': (0x6a68b, 0x6a72f),
    'new_actor_scalars': (0xcc621, 0xcc690),
    'existing_actor_position': (0xcc41a, 0xcc447),
    'receive_opcode_length': (0x134c3, 0x134ee),
    'receive_length_wrapper': (0x15840, 0x15850),
    'receive_length_guard': (0x13558, 0x13560),
    'receive_logical_loop': (0x13497, 0x13592),
    'receive_byte': (0x12520, 0x12554),
    'queue_empty': (0x10b50, 0x10b68),
    'queue_read': (0x10af0, 0x10b4a),
    'alternate_new_position': (0xcc04f, 0xcc069),
    'alternate_existing_position': (0xcbdef, 0xcbe1c),
}
STATIC_RANGES = {
    'record_argument_and_call': (0x6aa63, 0x6aa8e),
    'actor_record_argument': (0xcc380, 0xcc3c3),
    'existing_actor_entry': (0xcc3c3, 0xcc41a),
    'new_actor_entry': (0xcc5db, 0xcc621),
    'existing_actor_coordinate_apply': (0xcc499, 0xcc4b0),
    'new_actor_coordinate_repeat': (0xcc7d2, 0xcc809),
    'alternate_record_call': (0x6a990, 0x6a9c5),
    'alternate_record_argument': (0xcbd70, 0xcbd98),
}


def qualified_image(path=IMAGE):
    image = Path(path).read_bytes()
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
        raise ValueError('Pinned current native image mismatch')
    return image


def bindings(image):
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
        raise ValueError('Pinned current native image mismatch')
    for table, target in ((0x1324, 0x127c), (0x6b5d4, 0x6a68b)):
        if struct.unpack_from('<I', image, table + 4 * 0x72)[0] != BASE + target:
            raise AssertionError('Opcode 72 dispatch binding changed')
    for pc, target in ((0x100a, 0x1200), (0x15845, 0x1000), (0x134c8, 0x15840),
                       (0x134b6, 0x12520), (0x13576, 0x12520),
                       (0x12529, 0x10b50), (0x12544, 0x10af0), (0x6aa89, 0xcc380),
                       (0x6a9c0, 0xcbd70)):
        if image[pc] != 0xe8 or pc + 5 + struct.unpack_from('<i', image, pc + 1)[0] != target:
            raise AssertionError('Native call binding changed')
    return {name: {'start_rva': a, 'end_rva_exclusive': z,
                   'sha256': hashlib.sha256(image[a:z]).hexdigest()}
            for name, (a, z) in {**RANGES, **STATIC_RANGES}.items()}


class NativeNpcRecord:
    STACK, PAGE, RESOURCE, ACTOR = 0x10000000, 0x11000000, 0x12000000, 0x13000000
    WORLD = 0x20000000
    SP = STACK + 0x800
    RETURN = BASE + 0x1282
    RECEIVE = 0x14000000
    QUEUE_DATA = RECEIVE + 0x1368
    QUEUE_END = RECEIVE + 0x1f68
    QUEUE_CURSOR = RECEIVE + 0x1f6c

    def __init__(self, image):
        self.evidence = bindings(image)
        self.vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        extent = (len(image) + 4095) & ~4095
        self.vm.mem_map(BASE, extent)
        self.vm.mem_write(BASE, image)
        self.vm.mem_protect(BASE, extent, uc.UC_PROT_READ | uc.UC_PROT_EXEC)
        self.owner_pointer = self.WORLD + 0xaa36480
        self.count_pointer = self.RESOURCE + 0x121e8
        for page in (self.STACK, self.PAGE, self.ACTOR,
                     self.RECEIVE + 0x1000, self.RECEIVE + 0x2000,
                     self.owner_pointer & ~4095, self.count_pointer & ~4095):
            self.vm.mem_map(page, 4096, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        self.put(self.owner_pointer, '<I', self.RESOURCE)
        self.active = False
        self.vm.hook_add(uc.UC_HOOK_CODE, self._code)
        self.vm.hook_add(uc.UC_HOOK_MEM_READ | uc.UC_HOOK_MEM_WRITE, self._memory)
        self.vm.hook_add(uc.UC_HOOK_MEM_INVALID, self._invalid)

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def reg(self, name, value=None):
        register = getattr(x86, 'UC_X86_REG_' + name)
        if value is None:
            return self.vm.reg_read(register)
        self.vm.reg_write(register, value)

    def _code(self, vm, address, size, context):
        if address in self.stops:
            vm.emu_stop()
            return
        pc = address - BASE
        if not any(a <= pc < pc + size <= z for a, z in self.allowed_code):
            raise AssertionError(f'Unexpected native instruction RVA {pc:x}')
        self.pcs.append(pc)

    def _memory(self, vm, access, address, size, value, context):
        if not self.active:
            return
        write = access == uc.UC_MEM_WRITE
        ranges = self.write_ranges if write else self.read_ranges
        self.events.append((self.reg('EIP') - BASE, write, address, size))
        # Truncation probes intentionally attempt a read through the guard page.
        if not any(a <= address < address + size <= z for a, z in ranges):
            raise AssertionError(f'Unexpected native memory access {address:x}/{size}')

    def _invalid(self, vm, access, address, size, value, context):
        self.fault = {'rva': self.reg('EIP') - BASE, 'address': address, 'size': size}
        return False

    def prepare(self, logical):
        if not 0 <= len(logical) <= 22:
            raise ValueError('Oracle input bound is 0..22 bytes')
        self.message = self.PAGE + 4096 - len(logical)
        self.vm.mem_write(self.PAGE, b'\xcd' * 4096)
        if logical:
            self.vm.mem_write(self.message, logical)
        self.vm.mem_write(self.STACK, b'\xa5' * 4096)
        self.vm.mem_write(self.ACTOR, b'\xa5' * 4096)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.reg(name, 0xa5a5a5a5)
        self.reg('ESP', self.SP)
        self.reg('EFLAGS', 2)

    def run(self, start, stops, names, actor_writes=(), extra_reads=(), limit=160):
        self.stops = set(stops)
        self.allowed_code = [RANGES[n] for n in names]
        stack = (self.SP - 0x40, self.SP + 0x40)
        self.write_ranges = [stack, *actor_writes]
        self.read_ranges = [stack, (self.message, self.message + 21),
                            (self.RECEIVE + 0x2cc0, self.RECEIVE + 0x2cc5),
                            (self.owner_pointer, self.owner_pointer + 4),
                            (self.count_pointer, self.count_pointer + 2),
                            (0x4014ec, 0x4014f0), (0x46b79c, 0x46b7a0),
                            (self.ACTOR + 0x10, self.ACTOR + 0x14), *extra_reads]
        self.pcs, self.events, self.fault = [], [], None
        self.active = True
        try:
            self.vm.emu_start(BASE + start, 0, count=limit, timeout=1000000)
        except uc.UcError:
            if self.fault is None:
                raise
        finally:
            self.active = False
        if self.fault is None and self.reg('EIP') not in self.stops:
            raise AssertionError('Native slice exceeded instruction/time bound')
        return {'stop_rva': self.reg('EIP') - BASE, 'fault': self.fault,
                'instructions': len(self.pcs), 'events': self.events[:]}

    def logical_length(self):
        self.prepare(b'\x72')
        self.put(self.SP, '<II', self.RETURN, 0x72)
        result = self.run(0x1000, (self.RETURN,),
                          ('length_wrapper', 'length_switch', 'length_72'))
        if result['fault'] or self.reg('ESP') != self.SP + 4:
            raise AssertionError('Native length call failed')
        return self.reg('EAX')

    def receive_length(self, buffered):
        """Execute real opcode callback, then probe original buffered-size guard.

        Stops before byte acquisition (12520) or the completed-read epilogue.
        Buffered count is explicit synthetic state; no socket data is invented.
        """
        if not 0 <= buffered <= 22:
            raise ValueError('Receive guard probe bound is 0..22')
        self.prepare(b'\x72')
        self.put(self.RECEIVE + 0x2cc0, '<IB', 0, 0x72)
        self.reg('ESI', self.RECEIVE)
        self.reg('EDI', self.RECEIVE + 0x2cc4)
        result = self.run(0x134c3, (BASE + 0x13558,),
                          ('receive_opcode_length', 'receive_length_wrapper',
                           'length_wrapper', 'length_switch', 'length_72'),
                          ((self.RECEIVE + 0x2cc0, self.RECEIVE + 0x2cc4),))
        if result['fault'] or self.reg('EDI') != 21:
            raise AssertionError('Native receive length callback failed')
        count, = struct.unpack('<I', self.vm.mem_read(self.RECEIVE + 0x2cc0, 4))
        if count != 1 or self.reg('ESP') != self.SP:
            raise AssertionError('Native opcode accounting failed')
        self.put(self.RECEIVE + 0x2cc0, '<I', buffered)
        guard = self.run(0x13558, (BASE + 0x13560, BASE + 0x135c9),
                         ('receive_length_guard',))
        return {'length': self.reg('EDI'), 'opcode_count': count,
                'buffered': buffered, 'needs_byte': guard['stop_rva'] == 0x13560,
                'callback': result, 'guard': guard}

    def receive_record(self, available):
        """Original logical assembly and queue reads, after outer transport gates.

        Queue contents are explicit synthetic decoded bytes. No encryption,
        socket, or world handler is invoked. A 22nd byte must remain queued.
        """
        self.prepare(available)
        self.vm.mem_write(self.RECEIVE + 0x1000, b'\xa5' * 8192)
        if available:
            self.vm.mem_write(self.QUEUE_DATA, available)
        self.put(self.QUEUE_END, '<II', len(available), 0)
        self.put(self.RECEIVE + 0x2cc0, '<I', 0)
        before = bytes(self.vm.mem_read(self.RECEIVE + 0x1000, 8192))
        self.reg('ESI', self.RECEIVE)
        writes = ((self.QUEUE_CURSOR, self.QUEUE_CURSOR + 4),
                  (self.RECEIVE + 0x2cc0, self.RECEIVE + 0x2cc4 + 21))
        result = self.run(0x13497, (BASE + 0x13592, BASE + 0x135af),
                          ('receive_logical_loop', 'receive_length_wrapper',
                           'length_wrapper', 'length_switch', 'length_72',
                           'receive_byte', 'queue_empty', 'queue_read'), writes,
                          ((self.QUEUE_END, self.QUEUE_CURSOR + 4),
                           (self.QUEUE_DATA, self.QUEUE_DATA + len(available))), limit=2500)
        after = bytes(self.vm.mem_read(self.RECEIVE + 0x1000, 8192))
        for i, (a, b) in enumerate(zip(before, after)):
            if a != b and not any(lo <= self.RECEIVE + 0x1000 + i < hi for lo, hi in writes):
                raise AssertionError('Receive canary changed')
        consumed, = struct.unpack('<I', self.vm.mem_read(self.QUEUE_CURSOR, 4))
        count, = struct.unpack('<I', self.vm.mem_read(self.RECEIVE + 0x2cc0, 4))
        result.update(consumed=consumed, count=count,
                      complete=result['stop_rva'] == 0x13592,
                      buffer_hex=bytes(self.vm.mem_read(self.RECEIVE + 0x2cc4, count)).hex())
        return result

    def selectors(self, logical, catalog_max):
        if not -32768 <= catalog_max <= 32767:
            raise ValueError('Catalog maximum is a signed native word')
        self.prepare(logical)
        self.put(self.count_pointer, '<h', catalog_max)
        self.reg('EAX', self.message)
        self.reg('EBP', self.WORLD)
        result = self.run(0x68b4c, (BASE + 0x6a72f, BASE + 0x6b517),
                          ('dispatch', 'selectors'))
        if result['fault'] is None:
            primary, = struct.unpack('<I', self.vm.mem_read(self.SP + 0x14, 4))
            secondary, = struct.unpack('<I', self.vm.mem_read(self.SP + 0x24, 4))
            result.update(primary_pointer=primary, selected_pointer=secondary,
                          selected=result['stop_rva'] == 0x6a72f)
        return result

    def position(self, logical, existing=False, alternate=False):
        self.prepare(logical)
        self.reg('EDI', self.message + 1)
        self.reg('ESI', self.ACTOR)
        self.reg('EBX', 0x5a5a)
        before = bytes(self.vm.mem_read(self.ACTOR, 4096))
        if existing:
            start, stop, name = 0xcc41a, 0xcc447, 'existing_actor_position'
            writes = ((self.ACTOR + 0x180, self.ACTOR + 0x190),)
        else:
            start, stop, name = 0xcc621, 0xcc690, 'new_actor_scalars'
            writes = ((self.ACTOR, self.ACTOR + 10),
                      (self.ACTOR + 0x10, self.ACTOR + 0x18))
        if alternate:
            self.reg('EBX', self.message + 1)
            start, stop, name = ((0xcbdef, 0xcbe1c, 'alternate_existing_position')
                                 if existing else (0xcc04f, 0xcc069, 'alternate_new_position'))
            if not existing:
                writes = ((self.ACTOR + 0x10, self.ACTOR + 0x18),)
        result = self.run(start, (BASE + stop,), (name,), writes)
        after = bytes(self.vm.mem_read(self.ACTOR, 4096))
        for i, (a, b) in enumerate(zip(before, after)):
            if a != b and not any(lo <= self.ACTOR + i < hi for lo, hi in writes):
                raise AssertionError('Actor canary changed')
        if result['fault'] is None:
            offset = 0x180 if existing else 0x10
            result['x'], result['y'] = struct.unpack_from('<II', after, offset)
            if existing:
                result['duplicate_position'] = struct.unpack_from('<II', after, 0x188)
            elif not alternate:
                result['primary_selector'], = struct.unpack_from('<I', after)
                result['direction_slice'], = struct.unpack_from('<H', after, 8)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=IMAGE)
    args = parser.parse_args()
    native = NativeNpcRecord(qualified_image(args.image))
    print(json.dumps({'image_sha256': IMAGE_SHA, 'logical_length': native.logical_length(),
                      'ranges': native.evidence, 'live_playable_proof': False}, indent=2))


if __name__ == '__main__':
    main()
