"""Bounded original S2C3B inventory update to C2S28 pending-message gate.

This proves a reachable receive branch in a synthetic world/UI fixture. It
stops before the original message renderer; no request/reply association or
server item transaction is inferred.
"""
from pathlib import Path
import struct

from . import current_companion_instance as instance
from .current_item_metadata import NativeItemMetadata


ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
TABLE = 0x18000000
DEFINITION = 0x18100000
SLOT = 30
ITEM = 9301
CALL = 0x98f33
NO_CALL = 0x98f82


def run_case(image: bytes, definition: bytes, pending: int, item: int = ITEM) -> dict:
    if (pending not in (0, 1) or len(definition) != 0x18c or
            not definition[0x11a] & 4 or definition[0x11b] & 1 or
            not 0 < item < 0x7f58):
        raise ValueError('Expected qualified flag-4 metadata and a Boolean pending state')
    native = instance.NativeInstance(image)
    vm = native.vm
    vm.mem_map(TABLE, 0x100000, instance.uc.UC_PROT_READ | instance.uc.UC_PROT_WRITE)
    vm.mem_map(DEFINITION, 0x1000, instance.uc.UC_PROT_READ | instance.uc.UC_PROT_WRITE)
    vm.mem_write(DEFINITION, definition)
    vm.mem_write(TABLE + 0xb2d40 + 4 * item, struct.pack('<I', DEFINITION))
    vm.mem_protect(TABLE, 0x100000, instance.uc.UC_PROT_READ)
    vm.mem_protect(DEFINITION, 0x1000, instance.uc.UC_PROT_READ)
    native.put32(native.OWNER + 0xcff70, TABLE)
    native.put32(native.OWNER + 0x866a4, 1)  # Explicit synthetic UI mode.
    native.put32(native.OWNER + 0xcff5c, native.UI)

    # Original primary S2C3B dispatch and 20-byte slot store, retaining the
    # same VM, call stack and registers for the continuation.
    record = struct.pack('<H', item) + bytes(18)
    prefix = native.packet_store(SLOT, record)
    if prefix['stop_rva'] != 0x98e2d or not prefix['copied']:
        raise AssertionError('Original S2C3B did not reach its slot store')
    pending_address = native.OWNER + 0x85608
    native.put32(pending_address, pending)
    count_address = native.OWNER + 0x8560c + 24 * SLOT
    native.stops = {CALL, NO_CALL}
    native.allowed_code = [(0x98e2d, 0x98f38), (0x59a60, 0x59a7e)]
    native.allowed_writes = [(count_address, count_address + 1)]
    native.reads, native.writes, native.pcs = [], [], []
    native.active = True
    try:
        vm.emu_start(instance.BASE + 0x98e2d, 0, count=300, timeout=1000000)
    finally:
        native.active = False
    stop = native.reg('EIP') - instance.BASE
    expected = CALL if pending else NO_CALL
    if stop != expected:
        raise AssertionError(f'Original pending branch stopped at {stop:x}, expected {expected:x}')
    if (0x59a60 not in native.pcs or 0x98f1e not in native.pcs or
            [read for read in native.reads if read[0] == 0x98f1e] !=
            [[0x98f1e, pending_address, 4]]):
        raise AssertionError('Original definition lookup or pending-field read missing')
    if native.writes != [[0x98e7f, count_address, 1, 1]]:
        raise AssertionError('Unexpected inventory or pending mutation before message callback')
    if bytes(vm.mem_read(pending_address, 4)) != struct.pack('<I', pending):
        raise AssertionError('Pending state changed before the original callback')
    if bytes(vm.mem_read(count_address, 1)) != b'\x01':
        raise AssertionError('Original slot count projection changed')
    if pending:
        if (image[CALL] != 0xe8 or
                CALL + 5 + struct.unpack_from('<i', image, CALL + 1)[0] != 0x4e140 or
                image[0x98f38:0x98f42] != bytes.fromhex('c7850856080000000000')):
            raise AssertionError('Message call or conditional pending-clear continuation changed')
        if native.reg('ECX') != native.UI or struct.unpack('<I', vm.mem_read(native.reg('ESP'), 4))[0] != 0x29d:
            raise AssertionError('Original message callback arguments changed')
    return {'slot': SLOT, 'item': item, 'pending_input': pending,
            'stop_rva': stop, 'message_callback_rva': 0x4e140 if pending else None,
            'pending_before_callback': pending, 'slot_count_before_callback': 1,
            'executed_instruction_count': len(native.pcs),
            'message_callback_executed': False}


def run() -> list[dict]:
    image = instance.qualified_image(IMAGE)
    metadata = NativeItemMetadata()
    rows = [('EGG', ITEM, b'\xe4\x00'), ('WPN', 1, b'\xf4\x02'),
            ('EQU', 1001, b'\xf4\x02')]
    results = []
    for section, item, flags in rows:
        definition = metadata.item_row(section, 0)
        if definition['key'] != item or definition['record'][0x11a:0x11c] != flags:
            raise AssertionError(f'Current {section} item definition changed')
        for pending in (0, 1):
            result = run_case(image, definition['record'], pending, item)
            result['source_section'] = section
            results.append(result)
    return results


if __name__ == '__main__':
    import json
    print(json.dumps(run(), indent=2))
