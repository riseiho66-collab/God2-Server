"""Bounded current MIS:4660 resource binding, with original game callees.

Standalone stages share one VM with NativeItemMetadata. This is not the full
client constructor or battle bootstrap. The renderer's bank-binding prefix is
an explicit stage; file/allocator/decimal adapters are the existing CRT model.
"""
import hashlib
import json
import struct

from .current_role_doll_resources import NativeRoleDollResources, BANK, BASE, STRIDE
from .current_indoor_resources import SP, STACK, SCRATCH, SURFACE, RETURN
from .current_item_metadata import NativeItemMetadata
from .current_npc_resources import NativeNpcResources
from .recover_combat_rules import CLIENT, IMAGE, IMAGE_SHA256, read_pinned
from .recover_companion_growth import fields
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP,
                              UC_X86_REG_EIP)

KEY, ICON, GROUP, SLOT = 4660, 51123, 37, 102
RENDERER = 0x6800000
ASSET = 'data2/itmimg/mis03.romz'
ASSET_SHA = '01b319617e60c4bcf478af7a5798b275a61fce0ee28c785176de801639895970'
PLAIN_SHA = 'ac9c2649e68bd8e699e296a9c5e7ac3e1afa06d79d095179ee1d5da993f086a7'
BINDING_CODE = ((0x81700, 0x817c0), (0x1ae70, 0x1aebf))


def bind_existing(native, *, owner, table, record):
    """Execute 81700 in an existing resource VM with a sparse MIS:4660 index.

    Caller supplies original-parser/index-store output and the owner renderer
    binding. No record, resource handle, resolver return or index is seeded here.
    Only this one-row profile is qualified; other catalog entries are rejected.
    """
    vm = native.vm
    image = read_pinned(IMAGE, IMAGE_SHA256)
    for low, high in BINDING_CODE:
        if bytes(vm.mem_read(BASE + low, high - low)) != image[low:high]:
            raise ValueError('Original binding code changed')
    if native.u32(owner + 0xcff70) != table:
        raise ValueError('Owner must already reference the same native catalog')
    pointers = struct.unpack('<32599I', vm.mem_read(table + 0xb2d44, 32599 * 4))
    if [(i + 1, p) for i, p in enumerate(pointers) if p] != [(KEY, record)]:
        raise ValueError('Only a sparse original MIS:4660 index is qualified')
    renderer = native.u32(owner + 0xcff60)
    bank = native.u32(renderer + 0xc)
    resource = bank + SLOT * STRIDE
    count = native.u32(resource + 0x108c)
    if native.u32(resource) == 0xffffffff or not 0 < count <= 256:
        raise ValueError('MIS03 must already be loaded by the native ROM loader')
    ids = [native.u32(native.u32(resource + 0x1090 + i * 4)) for i in range(count)]
    if ids.count(ICON) != 1:
        raise ValueError('Expected one source-backed ROM action for icon 51123')
    expected_action = ids.index(ICON)
    initial = bytes(vm.mem_read(record, 0x18c))
    icon, group, action = struct.unpack_from('<3H', initial, 0x114)
    done = native.u32(table + 0xd2aa0)
    if icon != ICON or (done, group, action) not in (
            (0, GROUP, 0xffff), (1, SLOT, expected_action)):
        raise ValueError('Expected initial or already-bound current MIS:4660 metadata')
    guards = (bytes(vm.mem_read(record - 16, 16)), bytes(vm.mem_read(record + 0x18c, 16)))
    writes, calls, executed = [], [], set()

    def code(vm, address, size, context):
        pc = address - BASE
        if address == RETURN:
            return
        if not any(low <= pc < high for low, high in BINDING_CODE):
            raise AssertionError(f'Unexpected item binding instruction: {pc:x}')
        executed.add(pc)
        if pc == 0x1ae70:
            sp = vm.reg_read(UC_X86_REG_ESP)
            calls.append((vm.reg_read(UC_X86_REG_ECX),
                          *struct.unpack('<2I', vm.mem_read(sp + 4, 8))))

    def write(vm, access, address, size, value, context):
        if STACK <= address < address + size <= STACK + 0x80000:
            return
        pc = vm.reg_read(UC_X86_REG_EIP) - BASE
        allowed = {(0x81749, record + 0x116, 2),
                   (0x81763, record + 0x118, 2),
                   (0x817b3, table + 0xd2aa0, 4)}
        if (pc, address, size) not in allowed:
            raise AssertionError(f'Unexpected item binding write: {pc:x} -> {address:x}')
        writes.append((pc, address, size, value))

    hooks = [vm.hook_add(UC_HOOK_CODE, code), vm.hook_add(UC_HOOK_MEM_WRITE, write)]
    try:
        native.call(0x81700, this=owner)
    finally:
        for hook in hooks:
            vm.hook_del(hook)
    final = bytes(vm.mem_read(record, 0x18c))
    expected = bytearray(initial)
    struct.pack_into('<HH', expected, 0x116, SLOT, expected_action)
    if final != expected or guards != (bytes(vm.mem_read(record - 16, 16)),
                                       bytes(vm.mem_read(record + 0x18c, 16))):
        raise AssertionError('Original binding bytes/canaries differ')
    if native.u32(table + 0xd2aa0) != 1:
        raise AssertionError('Original catalog completion flag missing')
    if calls != ([] if done else [(renderer, SLOT, ICON)]):
        raise AssertionError('Original resolver arguments differ')
    return {'initial_group': group, 'initial_action': action, 'group': SLOT,
            'action': struct.unpack_from('<H', final, 0x118)[0],
            'resolver_calls': calls, 'writes': writes, 'executed': sorted(executed)}


class NativeItemActionBinding(NativeRoleDollResources):
    """One current ROM and one original metadata record, in a single offline VM."""

    def __init__(self):
        super().__init__()
        raw = read_pinned(CLIENT / ASSET, ASSET_SHA)
        plain = decode_csvz(raw, limit=1024 * 1024)
        if hashlib.sha256(plain).hexdigest() != PLAIN_SHA:
            raise ValueError('Pinned MIS03 decode changed')
        # Base initialization reads its pinned RoleDoll assets, but loads none.
        self.files, self.decoded = {ASSET: raw}, {ASSET: plain}
        self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._decimal,
                                          begin=BASE + 0x1480b4, end=BASE + 0x1480b4))
        self.metadata = m = NativeItemMetadata(vm=self.vm)
        matches = [i for i, row in enumerate(m.sections['MIS']['records'])
                   if fields(row)[0] == str(KEY).encode()]
        if len(matches) != 1:
            raise ValueError('Expected unique current MIS:4660 row')
        self.parsed = m.item_row('MIS', matches[0], retain=True)
        self.record = m.RECORD + 16
        if (self.parsed['group'], self.parsed['action']) != (GROUP, 0xffff):
            raise AssertionError('Original initial metadata changed')
        path = self.string(m.MAPS + GROUP * 0x84 + 4)
        if path.decode('ascii').replace('\\', '/').lower() + 'z' != ASSET:
            raise AssertionError('Original RomMaps row selected another resource')
        self.vm.mem_write(SCRATCH, path + b'\0')
        self.active_name = ASSET
        # Explicit single-row preload: original 650E5/64820 establish 65+index.
        # The complete 57-ROM preload loop is outside this bounded proof.
        self.load_result = self.call(0x29820, SCRATCH, SLOT, this=BANK)
        if self.load_result < 0 or self.load_result == 0xffffffff:
            raise AssertionError('Original MIS03 ROM loader failed')
        self.vm.mem_map(RENDERER, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(RENDERER, b'\xa5' * 4096)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_ECX, RENDERER)
        self.vm.mem_write(SP + 0x14, struct.pack('<3I', SURFACE, 0, BANK))
        # Original constructor prefix stores the supplied bank at renderer+0C.
        self.run(0x1aa26, 0x1aa44)
        if self.u32(RENDERER + 0xc) != BANK:
            raise AssertionError('Original renderer bank binding failed')
        self.vm.mem_write(m.OWNER + 0xcff60, struct.pack('<I', RENDERER))
        self.resource = BANK + SLOT * STRIDE
        self.action_count = self.u32(self.resource + 0x108c)

    def _decimal(self, vm, address, size, context):
        sp = vm.reg_read(UC_X86_REG_ESP)
        if self.u32(sp) != BASE + 0x51bc9:
            raise AssertionError('Unqualified item decimal adapter caller')
        NativeNpcResources._crt(self, vm, address, size, context)

    def _service(self, vm, address, size, context):
        if address != BASE + 0x14716f:
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(UC_X86_REG_ESP)
        path = self.string(self.u32(sp + 4)).decode('ascii').replace('\\', '/').lower()
        if path not in (ASSET[:-1], ASSET) or self.string(self.u32(sp + 8)) != b'rb':
            raise AssertionError('Unqualified item ROM open: ' + path)
        self.attempts.append(path)
        result = 0
        if path in self.files:
            self.opens.append(path)
            result = 0x80000000 + 4 * len(self.opens)
            self.handles[result] = [self.files[path], 0]
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp + 4)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))

    def bind(self):
        return bind_existing(self, owner=self.metadata.OWNER,
                             table=self.metadata.TABLE, record=self.record)

    def consume(self):
        m = self.metadata
        m.vm.mem_write(m.OUTPUT, b'\xa5' * 16)
        m.call(0x9b720, KEY, m.OUTPUT + 4, m.OUTPUT + 8, this=m.OWNER,
               allowed=((m.OUTPUT + 4, m.OUTPUT + 6), (m.OUTPUT + 8, m.OUTPUT + 10)))
        result = bytes(m.vm.mem_read(m.OUTPUT, 16))
        expected = bytearray(b'\xa5' * 16)
        struct.pack_into('<H', expected, 4, SLOT)
        action = struct.unpack('<H', m.vm.mem_read(self.record + 0x118, 2))[0]
        struct.pack_into('<H', expected, 8, action)
        if result != expected:
            raise AssertionError('Original metadata consumer differs after binding')
        return SLOT, action


def main():
    native = NativeItemActionBinding()
    result = native.bind()
    print(json.dumps({'source_line': native.parsed['source_line'],
                      'load_result': native.load_result,
                      'rom_action_count': native.action_count,
                      'binding': result, 'consumer': native.consume()}, indent=2))


if __name__ == '__main__':
    main()
