"""Lightweight same-VM map loader/binder proofs; no battle asset preload."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import UC_HOOK_CODE
from unicorn import x86_const as x86
from tools.strike_lab import current_owner_map_metadata as maps
from tools.strike_lab.current_item_metadata import NativeItemMetadata
from tools.strike_lab.current_indoor_resources import NativeIndoorResources
from tools.strike_lab.recover_companion_growth import fields

OWNER, CHARACTER, STACK, SP = 0x30000000, 0x8520000, 0x6500000, 0x657f000
REGISTERS = tuple(getattr(x86, 'UC_X86_REG_' + name) for name in
                  ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP', 'ESP', 'EIP',
                   'EFLAGS', 'FPCW', 'FPSW', 'FPTAG', 'XMM0', 'XMM7'))


class Host:
    allocate = NativeIndoorResources.allocate

    def __init__(self, vm):
        self.vm = vm
        self.heap, self.heap_limit, self.allocations = 0x9000000, 0x11000000, {}


def caller(vm):
    return (tuple(vm.reg_read(reg) for reg in REGISTERS),
            bytes(vm.mem_read(STACK, 0x80000)))


class CurrentOwnerMapMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item = item = NativeItemMetadata()
        index = next(i for i, row in enumerate(item.sections['MIS']['records'])
                     if fields(row)[0] == b'4660')
        item.item_row('MIS', index, retain=True)
        cls.vm = vm = item.vm
        for address, size in ((OWNER, 0x240000), (CHARACTER, 0x5000), (STACK, 0x80000),
                              (0x31000000, 0x2a3000), (0x31400000, 0x291000),
                              (0x20000000, 4096), (0x2b000000, 4096)):
            vm.mem_map(address, size)
            vm.mem_write(address, b'\xa5' * size)
        vm.mem_write(OWNER + maps.OWNER_TABLE, struct.pack('<I', item.TABLE))
        vm.reg_write(x86.UC_X86_REG_ESP, SP - 0xf4)
        vm.reg_write(x86.UC_X86_REG_EIP, maps.BASE + 0xc328b)
        vm.reg_write(x86.UC_X86_REG_EBX, CHARACTER)
        vm.reg_write(x86.UC_X86_REG_ESI, OWNER)
        vm.reg_write(x86.UC_X86_REG_EBP, 0)
        vm.reg_write(x86.UC_X86_REG_EFLAGS, 0x602)
        vm.reg_write(x86.UC_X86_REG_XMM0, 0x123456789abcdef)
        cls.before_caller = caller(vm)
        cls.before_table = bytes(vm.mem_read(item.TABLE, 0x100000))
        cls.before_item = bytes(vm.mem_read(item.RECORD, 0x1ac))
        cls.before_rommaps = bytes(vm.mem_read(item.MAPS, 0x2000))
        cls.before_owner = bytes(vm.mem_read(OWNER, 0x240000))
        cls.host = Host(vm)
        cls.old_services = []

        def old_service(vm, address, size, context):
            cls.old_services.append(address)
            raise AssertionError(f'Host CRT hook consumed sidecar CRT call {address - maps.BASE:X}')

        cls.service_hooks = [vm.hook_add(UC_HOOK_CODE, old_service,
                                         begin=maps.BASE + pc, end=maps.BASE + pc)
                             for pc in maps.SERVICES]
        cls.n = maps.attach_and_load(cls.host, owner=OWNER)
        cls.after_load_caller = caller(vm)
        cls.after_load_owner = bytes(vm.mem_read(OWNER, 0x240000))

    def test_complete_native_source_loader_and_image_binder(self):
        n = self.n
        self.assertIs(n.vm, self.item.vm)
        self.assertEqual(n.table, self.item.TABLE)
        self.assertEqual(n.provenance['decoded_span'], (2462531, 2483449))
        self.assertEqual(n.provenance['decoded_sha256'], maps.PLAIN_SHA)
        self.assertEqual(n.traces[0]['source_reads'][0]['raw_span'], (0, 719032))
        for pc, count in ((0x565ec, 1), (0x59a80, 1), (0x51a90, 144),
                          (0x51be0, 144), (0x59d55, 144)):
            self.assertEqual(n.load_trace['pcs'][pc], count)
        for pc, count in ((0x818dc, 1), (0x67ef0, 1), (0x67f04, 143),
                          (0x59e70, 143), (0x59ecc, 143)):
            self.assertEqual(n.bind_trace['pcs'][pc], count)
        self.assertEqual(len(n.load_trace['source_reads']), 144)
        self.assertEqual(n.load_trace['source_reads'][0]['source_line'], 21020)
        self.assertEqual(n.load_trace['source_reads'][-1]['decoded_span'][1], 2483449)
        self.assertFalse(self.old_services)
        n._verify_records(bound=True)
        writes = [(pc, address, value) for pc, address, size, value in n.bind_trace['writes']]
        self.assertEqual(len(writes), 143)
        self.assertTrue(all(pc == 0x59ecc for pc, _, _ in writes))
        self.assertEqual(n.u32(OWNER + maps.OWNER_TABLE), self.item.TABLE)

    def test_all_144_native_lookups_and_unbound_original_row(self):
        before = caller(self.vm)
        for index, row in enumerate(self.n.rows):
            with self.subTest(area=row['area'], scene=row['scene']):
                result = self.n.lookup(row['area'], row['scene'])
                self.assertEqual(result['record'], self.n.records + index * maps.STRIDE)
                self.assertEqual(result['source_line'], row['source_line'])
                self.assertIn(0x59d80, result['trace']['pcs'])
        island = self.n.lookup(2, 0)
        self.assertEqual((island['metadata'], island['panel_words']), (0x58b804, (47, 1)))
        missing = self.n.lookup(2, 15)
        self.assertEqual((missing['record'], missing['source_line']), (0, None))
        old = self.n.lookup(7, 3)
        self.assertNotEqual(old['record'], 0)
        self.assertEqual(old['metadata'], 0)
        self.assertEqual(caller(self.vm), before)

    def test_c3080_root_arguments_native_cache_and_record_1a0_read(self):
        for area, scene in ((2, 15), (2, 0), (1, 12)):
            with self.subTest(area=area, scene=scene):
                self.vm.mem_write(CHARACTER + 0x14, struct.pack('<HHHH', scene, 0xdead, area, 0xbeef))
                before = caller(self.vm)
                trace = self.n.probe_c3080(character=CHARACTER)
                self.assertEqual(caller(self.vm), before)
                self.assertEqual(trace['frontier'], 0xc32fd)
                self.assertEqual(trace['pcs'][0x59d80], 2)
                self.assertEqual(trace['pcs'][0xc32b6], 1)
                self.assertEqual(trace['pcs'][0xc32cd], 1)
                expected = self.n.lookup(area, scene)['record']
                area_record = self.n.lookup(area, 0)['record']
                self.assertEqual(self.n.u32(OWNER + 0x8aa4c), expected)
                self.assertEqual(trace['registers']['EAX'], area_record)
                self.assertIn((0xc32da, area_record + 0x1a0, 4,
                               self.n.u32(area_record + 0x1a0)), trace['reads'])
                self.assertIn((0xc328b, CHARACTER + 0x14, 2, scene), trace['reads'])
                self.assertIn((0xc328f, CHARACTER + 0x18, 2, area), trace['reads'])
                self.assertTrue(any(pc == 0xc3294 and addr == OWNER + maps.OWNER_TABLE
                                    for pc, addr, _, _ in trace['reads']))
        self.vm.mem_write(CHARACTER + 0x14, struct.pack('<HHHH', 1, 0, 63, 0))
        trace = self.n.probe_c3080(character=CHARACTER)
        self.assertEqual(trace['frontier'], 0xc32e2)
        self.assertNotIn(0x2c70, trace['pcs'])

    def test_item_bank_cpu_stacks_and_disjoint_allocations_survive(self):
        self.assertEqual(self.before_caller, self.after_load_caller)
        self.assertEqual(self.before_owner, self.after_load_owner)
        table = bytearray(self.vm.mem_read(self.item.TABLE, 0x100000))
        table[maps.COUNT:maps.POINTER + 4] = self.before_table[maps.COUNT:maps.POINTER + 4]
        self.assertEqual(bytes(table), self.before_table)
        self.assertEqual(bytes(self.vm.mem_read(self.item.RECORD, 0x1ac)), self.before_item)
        self.assertEqual(bytes(self.vm.mem_read(self.item.MAPS, 0x2000)), self.before_rommaps)
        self.assertEqual(bytes(self.vm.mem_read(maps.BASE, len(self.n.image))), self.n.image)
        for pointer, length in self.n.allocations:
            self.assertIn(pointer, self.host.allocations)
            for lo, hi in maps.RESERVED:
                self.assertFalse(pointer < hi and lo < pointer + length)
        for pointer, length in ((0x31000000, 0x2a3000), (0x31400000, 0x291000),
                                (0x20000000, 4096), (0x2b000000, 4096)):
            self.assertEqual(bytes(self.vm.mem_read(pointer, length)), b'\xa5' * length)

    def test_changed_code_data_binding_and_repeated_load_rejected(self):
        before = caller(self.vm)
        with self.assertRaises(ValueError):
            self.n.load()
        for address in (maps.BASE + 0x59d80, maps.BASE + maps.STATIC_RVA):
            original = bytes(self.vm.mem_read(address, 1))
            try:
                self.vm.mem_write(address, bytes([original[0] ^ 1]))
                with self.assertRaises(ValueError):
                    if address == maps.BASE + 0x59d80:
                        self.n.lookup(2, 0)
                    else:
                        self.n._static_bindings()
            finally:
                self.vm.mem_write(address, original)
        original = bytes(self.vm.mem_read(OWNER + maps.OWNER_TABLE, 4))
        try:
            self.vm.mem_write(OWNER + maps.OWNER_TABLE, bytes(4))
            with self.assertRaises(ValueError):
                self.n.lookup(2, 0)
        finally:
            self.vm.mem_write(OWNER + maps.OWNER_TABLE, original)
        self.assertEqual(caller(self.vm), before)

    def test_failure_preserves_cpu_stack_and_removes_temporary_hooks(self):
        before = caller(self.vm)
        scratch = bytes(self.vm.mem_read(self.n.stack, 0x10000))

        def interrupt(vm, address, size, context):
            raise RuntimeError('Explicit interrupted lookup')

        hook = self.vm.hook_add(UC_HOOK_CODE, interrupt,
                                begin=maps.BASE + 0x59dab, end=maps.BASE + 0x59dab)
        try:
            with self.assertRaisesRegex(RuntimeError, 'interrupted lookup'):
                self.n.lookup(2, 0)
        finally:
            self.vm.hook_del(hook)
        self.assertEqual(caller(self.vm), before)
        self.assertEqual(bytes(self.vm.mem_read(self.n.stack, 0x10000)), scratch)
        self.assertEqual(self.n.lookup(2, 0)['metadata'], 0x58b804)

    def test_unqualified_source_and_allocator_are_rejected_before_loading(self):
        # A separate empty bank qualifies failure paths without another decode.
        address = 0x38000000
        self.vm.mem_map(address, 0xe0000)
        original = bytes(self.vm.mem_read(OWNER + maps.OWNER_TABLE, 4))
        try:
            self.vm.mem_write(OWNER + maps.OWNER_TABLE, struct.pack('<I', address))
            n = maps.NativeOwnerMapMetadata(self.host, owner=OWNER)
            with patch.object(maps, 'music_source', side_effect=ValueError('Pinned source changed')):
                with self.assertRaisesRegex(ValueError, 'Pinned source changed'):
                    n.load()
            self.assertFalse(n.attempted)
            self.assertEqual(bytes(self.vm.mem_read(address + maps.COUNT, 6)), bytes(6))
            with patch.object(self.host, 'allocate', return_value=0x20001000):
                with self.assertRaisesRegex(ValueError, 'overlaps'):
                    maps.NativeOwnerMapMetadata(self.host, owner=OWNER)
        finally:
            self.vm.mem_write(OWNER + maps.OWNER_TABLE, original)
            self.vm.mem_unmap(address, 0xe0000)


if __name__ == '__main__':
    unittest.main()
