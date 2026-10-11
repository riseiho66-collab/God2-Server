"""Same-VM native item loader -> lookup/store -> target-mask stages.

Loader retains its existing decimal CRT adapter. Consumer stages contain no
replacement calls. These are declared offline entries, not a live battle.
"""
import json
import struct

from .current_item_metadata import NativeItemMetadata, growth
from .current_battle_entry import BATTLE, BASE, IMAGE_SHA256


def source_to_reach(section='WPN', index=0, *, missing=False):
    if section not in ('WPN', 'EQU', 'TWP', 'TEQ') or type(missing) is not bool:
        raise ValueError('Expected qualified equipment section and missing flag')
    n = NativeItemMetadata()
    row = n.item_row(section, index, retain=True)
    values = growth.fields(n.sections[section]['records'][index])
    source_value = growth.decimal(values[29])
    vm, uc, reg = n.vm, n.uc, n.x86
    vm.mem_map(BATTLE, 0x200000)
    vm.mem_map((BATTLE + 0xa9e9c38) & ~4095, 4096)

    def put32(address, value):
        vm.mem_write(address, struct.pack('<I', value))

    def get32(address):
        return struct.unpack('<I', vm.mem_read(address, 4))[0]

    put32(BATTLE + 0x20, n.OWNER)
    put32(BATTLE + 0x28, n.TABLE)
    # Invalid original lookup key exercises the native null branch without
    # clearing or replacing the pointer created by the native row loader.
    key = 0x7f58 if missing else row['key']
    vm.mem_write(n.OWNER + 0x85940, struct.pack('<H', key))
    put32(BATTLE + 0x64, 0xa5a5a5a5)
    n.reg('ESI', BATTLE)
    n.reg('ESP', n.SP)
    n.reg('EAX', 0xa5a50000)
    stages = []

    def execute(start, stop, ranges):
        visits, writes, reads = [], [], []

        def code(vm, address, size, data):
            rva = address - BASE
            if rva == stop:
                vm.emu_stop()
                return
            if not any(a <= rva and rva + size <= b for a, b in ranges):
                raise AssertionError(f'Unqualified native reach PC {rva:X}')
            visits.append(rva)

        def write(vm, access, address, size, value, data):
            if not (n.STACK <= address and address + size <= n.STACK + 0x10000):
                writes.append([vm.reg_read(reg.UC_X86_REG_EIP) - BASE, address, size, value])

        def read(vm, access, address, size, value, data):
            if n.RECORD + 16 <= address < n.RECORD + 16 + 0x18c:
                reads.append([vm.reg_read(reg.UC_X86_REG_EIP) - BASE, address - n.RECORD - 16, size])

        hooks = [vm.hook_add(uc.UC_HOOK_CODE, code),
                 vm.hook_add(uc.UC_HOOK_MEM_WRITE, write),
                 vm.hook_add(uc.UC_HOOK_MEM_READ, read)]
        try:
            vm.emu_start(BASE + start, BASE + stop, count=5000)
            if vm.reg_read(reg.UC_X86_REG_EIP) != BASE + stop:
                raise AssertionError('Native reach stage did not reach stop')
        finally:
            for hook in hooks:
                vm.hook_del(hook)
        stages.append(dict(start_rva=start, stop_rva=stop, instructions=len(visits),
                           outside_stack_writes=writes, metadata_reads=reads))

    execute(0x117940, 0x11796b, ((0x117940, 0x11796b), (0x59a60, 0x59a7e)))
    reach = get32(BATTLE + 0x64)
    if vm.reg_read(reg.UC_X86_REG_ESP) != n.SP:
        raise AssertionError('Metadata stage unbalanced stack')
    # Explicit separate caller entry, retaining the just-produced field64.
    put32(BATTLE + 0xa9e9c38, 1)
    put32(BATTLE + 0xa9e9c3c, 0)
    vm.mem_write(BATTLE + 0x51, b'\x00\x0d')
    put32(BATTLE + 0x68, 255)
    vm.mem_write(BATTLE + 0x144938 + 0x2f4, struct.pack('<2I', 0x3fff, 0x3fff))
    n.reg('ESI', BATTLE)
    n.reg('ESP', n.SP)
    execute(0x114a35, 0x114a5e, ((0x114a35, 0x114a5e), (0x1156e0, 0x11571c),
                                (0x11ec70, 0x11ee84)))
    if vm.reg_read(reg.UC_X86_REG_ESP) != n.SP:
        raise AssertionError('Target stage unbalanced stack')
    unchanged = bytes(vm.mem_read(n.RECORD + 16, 0x18c)) == row['record']
    if not unchanged:
        raise AssertionError('Consumer changed native item record')
    return dict(authority='NATIVE_ITEM_REACH_STAGED_NOT_DAMAGE_FORMULA',
                image_sha256=IMAGE_SHA256, section=section, key=row['key'],
                source_line=row['source_line'], source_column_0based=29,
                source_value=source_value, metadata_byte120=row['record'][0x120],
                missing=missing, battle_reach=reach, source_unchanged=unchanged,
                target_masks=list(struct.unpack('<2I', vm.mem_read(BATTLE + 0x434, 8))),
                stages=stages, loader_decimal_adapter=True)


if __name__ == '__main__':
    print(json.dumps([source_to_reach(s) for s in ('WPN', 'EQU', 'TWP', 'TEQ')] +
                     [source_to_reach(missing=True)], sort_keys=True))
