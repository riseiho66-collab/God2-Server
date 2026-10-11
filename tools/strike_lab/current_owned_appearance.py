"""Current-source preview/world resource selection, bounded before ROM loading.

Runs unchanged instruction slices from 99E0 and 61270. Deliberately does not
produce handles, run a complete preview, or construct a world packet.
"""
from dataclasses import asdict, dataclass
import json
import struct

from .current_appearance_resources import (
    AppearanceResources, BASE, BANK, TABLE, RECORDS, STACK, SP, STOP, INPUT,
    IMAGE_SHA, SOURCE_SHA, DECODED_SHA, DRV_SOURCE_SHA, DRV_DECODED_SHA,
)
from unicorn import UC_HOOK_CODE, UC_PROT_READ
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI,
    UC_X86_REG_ESP, UC_X86_REG_ESI,
)

PREVIEW, MANAGER, CACHE = 0x4000000, 0x4200000, 0x4500000
PROFILE = PREVIEW + 0x15280
COMPONENTS = PREVIEW + 0x15e38
BLOCK = INPUT + 0x4000

# Instruction bytes identify each layout/mask at its original consumer, not
# from resource filenames. The inherited oracle also checks the entire image.
INSTRUCTIONS = {
    0x4225: '68e8475800',           # preview HeroDoll filename
    0x425b: '8d8d8c0d0000',         # preview table +D8C
    0x63c28: 'bfe8475800',          # world same HeroDoll filename
    0x63c54: '8db2782d0100',        # world HeroDoll +12D78
    0x63270: '688ca85800',          # Drv filename
    0x99e0: '81ec1c01000053555657', # original preview frame
    0x9a10: '89542410',
    0x9a1e: '89542414',             # both halves initialized by original code
    0x9a2c: '668b8fa4520100',       # WORD at C[36]
    0x9a37: 'c1e905',
    0x9a42: '0c80',
    0x9a4a: '8a87a0520100',         # C[32]
    0x9a58: 'c0e005',
    0x9a71: '8a97a1520100',         # C[33]
    0x9a81: '240f32c1',            # replace low nibble
    0x9ab4: '8a402a',              # actual derived record byte
    0x9b4d: '81c7385e0100',
    0x9b9c: 'c0ea05',
    0x61273: '8b8118ce1600',        # resource-manager bank index
    0x6127a: '69c010d60a00',
    0x6128e: '8db0e0820600',        # actual world bank offset
    0x61369: '8a4f04',              # completed component 2 binary
    0x61394: 'e8f7280000',          # derived lookup 63C90
    0x613f1: 'e8ea290000',          # primary lookup/cache wrapper 63DE0
    0x613fa: '4383fb04',            # original loop increment/comparison
    0x63e1c: 'e89fe8feff',          # cache lookup 526C0
    0x526d9: 'e882fdffff',          # actual record lookup 52460
    0x526de: '85c0',               # stop before consuming cache WORD
    0x63785: '663b81f6210100',      # Drv count
    0x63794: '668b84080a220100',    # +121F8 + selector*32 +12
    0x52442: '8a402a',
    0x684d6: '8d542438',            # body +12, after one push
    0x684eb: 'e8808dffff',          # normal consumer calls 61270
    0x6852d: 'c0e905',             # variant extraction
    0xffa34: '88544108',            # component variant storage
}


@dataclass(frozen=True)
class Identity:
    source_line: int
    record_pointer: int
    key: str
    filename: str
    derived: int


@dataclass(frozen=True)
class Selection:
    block: bytes
    primary: tuple
    derived: tuple
    lookups: tuple
    variants: tuple
    driver_actions: tuple = ()


def validate_profile(profile):
    if (len(profile) != 40 or profile[33] not in (0, 1)
            or (profile[32] & 7) > 6 or profile[36] >> 5 > 6):
        raise ValueError('Expected 40-byte profile: binary 0/1, variants 0..6')


def validate_block(block):
    if (len(block) != 8 or block[0] not in (0, 1)
            or block[2] != block[0] or block[4] != block[0]
            or block[6] != (0x80 | block[0]) or block[5] or block[7]
            or block[1] & 31 or block[3] & 31
            or block[1] >> 5 > 6 or block[3] >> 5 > 6):
        raise ValueError('Expected a fresh zero-index preview component block')


def project_owned_bits(block, profile):
    """Conditional block relation only; no arbitrary-body/default serializer."""
    validate_block(block)
    validate_profile(profile)
    result = bytearray(block)
    for offset in (0, 2, 4, 6):
        result[offset] = (result[offset] & 0xf0) | (profile[33] & 0x0f)
    result[1] = (result[1] & 0x1f) | ((profile[32] & 7) << 5)
    result[3] = (result[3] & 0x1f) | (profile[36] & 0xe0)
    return bytes(result)


class OwnedAppearance(AppearanceResources):
    def __init__(self):
        super().__init__()
        self.validate_instructions()
        v = self.vm
        for address, size in ((PREVIEW, 0x180000), (MANAGER, 0x170000), (CACHE, 4096)):
            v.mem_map(address, size)
        v.mem_write(PREVIEW+0xd8c, bytes(v.mem_read(TABLE, 0x121f8)))
        v.mem_write(MANAGER+0x682e0, bytes(v.mem_read(BANK, 0x60000)))
        # Bank zero is an explicit harness topology, not a game-state default.
        self.put32(MANAGER+0x16ce18, 0)
        v.mem_protect(MANAGER, 0x170000, UC_PROT_READ)
        self.put32(PREVIEW+0x178cdc, CACHE)
        self.baseline = bytes(v.mem_read(RECORDS, len(self.rows)*44))
        self.derived_records, self.driver_actions = [], []
        for rva in (0x9ab4, 0x52442, 0x63780, 0x6379c,
                    0x9b0d, 0x4b70, 0x29820, 0x63640, 0x63ad0):
            v.hook_add(UC_HOOK_CODE, self._observe, begin=BASE+rva, end=BASE+rva)

    def validate_instructions(self):
        for rva, expected in INSTRUCTIONS.items():
            raw = bytes.fromhex(expected)
            if bytes(self.vm.mem_read(BASE+rva, len(raw))) != raw:
                raise AssertionError(f'Original instruction changed at {rva:X}')
        for rva, expected in ((0x1847e8, b'HeroDoll.csv'),
                              (0x18a88c, b'\\Data2\\Patch\\Drv.csv')):
            if self.string(BASE+rva) != expected:
                raise AssertionError('Original table reference changed')

    def identity(self, pointer):
        record = self.record(pointer)
        ordinal = (pointer-RECORDS)//44
        row = self.rows[ordinal]
        key = record[32:42].split(b'\0')[0].decode('ascii')
        filename = record[:30].split(b'\0')[0].decode('ascii')
        if (key != (row[0]+row[1]).lower() or filename != row[3].lower()
                or record[42] != int(row[5]) or record[30:32] != b'\xff\xff'):
            raise AssertionError('Native identity differs from current source row')
        return Identity(26+ordinal, pointer, key, filename, record[42])

    def _observe(self, vm, address, size, context):
        rva = address-BASE
        if rva in (0x9ab4, 0x52442):
            self.derived_records.append(self.identity(vm.reg_read(UC_X86_REG_EAX)))
        elif rva == 0x63780:
            if (self.u32(vm.reg_read(UC_X86_REG_ESP)+4) != 0
                    or vm.reg_read(UC_X86_REG_ECX) != MANAGER+0x682e0):
                raise AssertionError('Outside actual source selector-zero path')
        elif rva == 0x6379c:
            self.driver_actions.append(vm.reg_read(UC_X86_REG_EAX) & 0xffff)
        else:
            raise AssertionError(f'Outside bounded resource selection at {rva:X}')

    def _reset(self, poison):
        if not isinstance(poison, int) or not 0 <= poison <= 255:
            raise ValueError('Byte poison required')
        self.vm.mem_write(STACK, bytes([poison])*0x10000)
        self.events.clear()
        self.derived_records.clear()
        self.driver_actions.clear()

    def _unchanged(self):
        if bytes(self.vm.mem_read(RECORDS, len(self.baseline))) != self.baseline:
            raise AssertionError('Source records changed')

    def _variants(self, poison):
        data = bytes(self.vm.mem_read(COMPONENTS, 0x2c))
        offsets = (8, 14, 20, 26)
        if any(value != poison for i, value in enumerate(data) if i not in offsets):
            raise AssertionError('Variant setter changed an unrelated component byte')
        return tuple(data[i] for i in offsets)

    def preview(self, profile, *, poison=0xa5):
        validate_profile(profile)
        self._reset(poison)
        v = self.vm
        v.mem_write(PROFILE, bytes(profile))
        v.mem_write(COMPONENTS, bytes([poison])*0x2c)
        v.reg_write(UC_X86_REG_ESP, SP+0x12c)
        v.reg_write(UC_X86_REG_ECX, PREVIEW)
        self.run(0x99e0, 0x99f0)
        if v.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Original preview prologue frame changed')
        # Omit cache/bank reset calls 99F0..9A08; all records are already FFFF.
        self.run(0x9a08, 0x9b00)
        primary = []
        for component in range(4):
            if v.reg_read(UC_X86_REG_EBX) & 255 != component:
                raise AssertionError('Original preview loop changed')
            primary.append(self.identity(v.reg_read(UC_X86_REG_EAX)))
            # Stop before ROM/cache/animation consumers. Execute the original
            # EDI adjustment and variant setter, without inventing any handle.
            self.run(0x9b4d, 0x9b53)
            self.run(0x9b97, 0x9ba6)
            self.run(0x9ba6, 0x9b00 if component < 3 else 0x9bbb)
        block = bytes(v.mem_read(SP+0x10, 8))
        variants = self._variants(poison)
        if v.reg_read(UC_X86_REG_ESP) != SP or bytes(v.mem_read(PROFILE, 40)) != profile:
            raise AssertionError('Preview stack/profile changed')
        self._unchanged()
        return Selection(block, tuple(primary), tuple(self.derived_records),
                         tuple(self.events), variants)

    def world(self, block, *, selector, poison=0x5a):
        validate_block(block)
        if type(selector) is not int or selector != 0:
            raise ValueError('Only explicitly selected source row zero is qualified')
        self._reset(poison)
        v = self.vm
        v.mem_write(BLOCK, bytes(block))
        # The second selector and output address are never consumed: execution
        # ends before the accessory tail and omits cache-handle output stores.
        v.mem_write(SP, struct.pack('<5I', STOP, selector, 0xcccccccc, BLOCK, 0xcccccccc))
        v.reg_write(UC_X86_REG_ESP, SP)
        v.reg_write(UC_X86_REG_ECX, MANAGER)
        self.run(0x61270, 0x613f1)
        primary = []
        for component in range(4):
            if v.reg_read(UC_X86_REG_EBX) != component:
                raise AssertionError('Original world loop changed')
            # Execute the real 63DE0 -> 526C0 -> 52460 chain up to its record
            # result. Roll back execution state, not events, before ROM/cache
            # consumption; no fabricated result is returned to native code.
            context = v.context_save()
            stack = bytes(v.mem_read(STACK, 0x10000))
            pending_sp = v.reg_read(UC_X86_REG_ESP)
            self.run(0x613f1, 0x526de)
            primary.append(self.identity(v.reg_read(UC_X86_REG_EAX)))
            v.context_restore(context)
            v.mem_write(STACK, stack)
            v.reg_write(UC_X86_REG_ESP, pending_sp+7*4)
            self.run(0x613fa, 0x613fe)
            self.run(0x61403, 0x613f1 if component < 3 else 0x61409)
        if v.reg_read(UC_X86_REG_ESP) != SP-0x1c or bytes(v.mem_read(BLOCK, 8)) != block:
            raise AssertionError('World stack/input changed')
        # Original normal-world variant consumer, entered after its optional
        # override branch. No override flag or world-body defaults are supplied.
        v.mem_write(COMPONENTS, bytes([poison])*0x2c)
        for component in range(4):
            v.mem_write(SP+0x14, struct.pack('<I', BLOCK+1+2*component))
            v.reg_write(UC_X86_REG_ESP, SP)
            v.reg_write(UC_X86_REG_ESI, component)
            v.reg_write(UC_X86_REG_EDI, COMPONENTS)
            self.run(0x68527, 0x68539)
            if v.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('World variant setter stack changed')
        variants = self._variants(poison)
        self._unchanged()
        return Selection(bytes(block), tuple(primary), tuple(self.derived_records),
                         tuple(self.events), variants, tuple(self.driver_actions))


def qualify():
    oracle = OwnedAppearance()
    cases = []
    for binary in (0, 1):
        for first in range(7):
            for second in range(7):
                profile = bytearray([0xa5]*40)
                profile[32], profile[33], profile[36] = first, binary, second << 5
                preview = oracle.preview(bytes(profile))
                world = oracle.world(preview.block, selector=0)
                cases.append({
                    'binary': binary, 'variants': [first, second],
                    'block': preview.block.hex(),
                    'same_primary_records': preview.primary == world.primary,
                    'same_variants': preview.variants == world.variants,
                    'preview': {**asdict(preview), 'block': preview.block.hex()},
                    'world': {**asdict(world), 'block': world.block.hex()},
                })
    return {
        'scope': 'source record selection only; no ROM/render/world-state claim',
        'image_sha256': IMAGE_SHA,
        'HeroDoll_sha256': [SOURCE_SHA, DECODED_SHA],
        'Drv_sha256': [DRV_SOURCE_SHA, DRV_DECODED_SHA],
        'cases': cases,
    }


if __name__ == '__main__':
    print(json.dumps(qualify(), indent=2))
