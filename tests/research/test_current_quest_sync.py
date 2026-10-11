"""C++ logical journal -> pinned native dispatcher, slot writer and page count.

Synthetic closed-widget state only; no stubs, UI, processes, network or gameplay.
Malformed indices stop at the original assertion call, not a fabricated return.
"""
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

import test_current_route_advertisement as routes
from unicorn import UcError, UC_PROT_READ, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[2]
WORLD, RESOURCE = 0x4000000, 0x3800000
UI = WORLD + 0xa7f2f6c
PACKET_PAGE = 0x3900000


def build_fixture(directory):
    source = ROOT / 'tests/test_recovered_quest_sync.cpp'
    executable = directory / ('quest.exe' if os.name == 'nt' else 'quest')
    compiler = next((shutil.which(n) for n in ('cl', 'clang++', 'g++', 'c++')
                     if shutil.which(n)), None)
    environment = None
    if not compiler and os.name == 'nt':
        vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / (
            'Microsoft Visual Studio/Installer/vswhere.exe')
        installation = subprocess.check_output([str(vswhere), '-latest', '-products', '*',
            '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
            '-property', 'installationPath'], text=True, timeout=30).strip()
        if not installation:
            raise RuntimeError('Standalone quest test requires a C++20 compiler')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(v for k, v in environment.items() if k.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('Standalone quest test requires a C++20 compiler')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'quest.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


class CurrentQuestSyncTests(unittest.TestCase):
    run_to = routes.CurrentRouteAdvertisementTests.run_to
    call = routes.CurrentRouteAdvertisementTests.call

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned native image changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-quest-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))
        cls.logical = bytes.fromhex(subprocess.check_output(
            [str(cls.executable), '--dump'], text=True, timeout=5).strip())
        cls.clears = [bytes.fromhex(line) for line in subprocess.check_output(
            [str(cls.executable), '--dump-clears'], text=True, timeout=5).splitlines()]

    def vm(self, suppress_open=0):
        vm = routes.CurrentRouteAdvertisementTests.vm(self)
        vm.mem_map(UI & ~4095, 0x240000)
        vm.mem_map(RESOURCE, 0xd3000)
        vm.mem_map((WORLD + 0x1539ad80) & ~4095, 4096)
        vm.mem_map(PACKET_PAGE, 4096)
        vm.mem_write(UI + 0xcff70, struct.pack('<I', RESOURCE))
        vm.mem_write(RESOURCE + 0xd2ac0, struct.pack('<I', 418))
        vm.mem_write(UI + 0xc2100, b'\xa5' * 0x50)
        vm.mem_write(UI + 0xc2144, struct.pack('<hh', 2, 3))
        vm.mem_write(UI + 0x232e5a, b'\xff\xff')  # Closed/uncreated widget.
        vm.mem_write(UI + 0x232eb0, struct.pack('<I', suppress_open))
        return vm

    def dispatch(self, vm, record, stop=0x6b517):
        packet = PACKET_PAGE + 4096 - len(record)
        vm.mem_write(packet, record)
        vm.mem_protect(PACKET_PAGE, 4096, UC_PROT_READ)
        vm.reg_write(UC_X86_REG_EBP, WORLD)
        vm.reg_write(UC_X86_REG_EBX, packet)
        vm.reg_write(UC_X86_REG_EAX, record[0])
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        self.run_to(vm, 0x68b61, stop)
        if stop == 0x6b517:
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP)

    def test_cpp_strict_decoder(self):
        subprocess.run([str(self.executable)], check=True, timeout=5)

    def encode(self, slot, subtype, value):
        result = subprocess.run([str(self.executable), '--encode', str(slot), str(subtype), str(value)],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = bytes.fromhex(result.stdout)
        self.assertEqual(record, bytes([0xdb, subtype, 0, 0, 0]) + struct.pack('<II', slot, value))
        return record

    def test_cpp_opaque_encoder_rejects_bounds_and_wide_subtypes(self):
        cases = [(slot, subtype, 0xffffffff)
                 for slot, subtype in ((15, 4), (0xffffffff, 5), (0, 0x104), (14, 0x105))]
        for args in cases:
            with self.subTest(args=args):
                result = subprocess.run([str(self.executable), '--encode', *map(str, args)],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, '', ''))
        # The fixture must not truncate text outside the helper's u32 input domain.
        for args in ((0, 5, -1), (0, 5, 0x100000000), (0, 0x100000004, 1)):
            with self.subTest(args=args):
                result = subprocess.run([str(self.executable), '--encode', *map(str, args)],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (2, '', ''))

    def test_cpp_opaque_updates_catalog_boundary_and_malformed_page_state(self):
        # C96C4 uses the low word for catalog eligibility, but C9699 stores all bits.
        # C9728 compares signed page words: a negative page is preserved, not repaired.
        for subtype in (4, 5):
            vm = self.vm(suppress_open=1)
            vm.mem_write(RESOURCE + 0xd2ac4, struct.pack('<I', RESOURCE + 0x1000))
            vm.mem_write(UI + 0xc2104, bytes(60))
            vm.mem_write(UI + 0x232eb8, struct.pack('<I', 0x76543210))
            for value, initial_page, expected_page, expected_count in (
                    (0x123401a2, 2, 2, 3),   # Last eligible catalog index, final slot.
                    (0x123401a3, 2, 0, 1),   # First out-of-catalog low word is still stored.
                    (0xffff0000, 2, 0, 1),   # Nonzero opaque value with zero low word.
                    (0xffffffff, 32767, 0, 1),
                    (0x80000001, -1, -1, 3)):
                with self.subTest(subtype=subtype, value=value, initial_page=initial_page):
                    vm.mem_write(UI + 0xc2144, struct.pack('<hh', initial_page, -7))
                    self.dispatch(vm, self.encode(14, subtype, value))
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)),
                                     bytes(56) + struct.pack('<I', value))
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2144, 4)),
                                     struct.pack('<hh', expected_page, expected_count))
                    self.assertEqual(bytes(vm.mem_read(UI + 0x232eb8, 4)),
                                     struct.pack('<I', value if subtype == 5 else 0x76543210))
                    for at in (0xc2100, 0xc2140, 0xc2148):
                        self.assertEqual(bytes(vm.mem_read(UI + at, 4)), b'\xa5'*4)

    def test_cpp_duplicate_final_slot_updates_repeat_native_refresh(self):
        for subtype, expected_calls in ((4, (0, 1, 2)), (5, (1, 2, 3))):
            vm = self.vm(suppress_open=1)
            vm.mem_write(RESOURCE + 0xd2ac4, struct.pack('<I', RESOURCE + 0x1000))
            vm.mem_write(UI + 0xc2104, bytes(60))
            vm.mem_write(UI + 0x232eb8, struct.pack('<I', 0x76543210))
            refresh_calls = []
            refresh = routes.BASE + 0xc9170
            hook = vm.hook_add(UC_HOOK_CODE,
                               lambda uc, address, size, context: refresh_calls.append(address),
                               begin=refresh, end=refresh)
            try:
                # Replay twice, then replace the same slot with another opaque value.
                for value, calls in zip((0x123401a2, 0x123401a2, 0x80000001), expected_calls):
                    self.dispatch(vm, self.encode(14, subtype, value))
                    self.assertEqual(len(refresh_calls), calls)
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)),
                                     bytes(56) + struct.pack('<I', value))
                    self.assertEqual(bytes(vm.mem_read(UI + 0x232eb8, 4)),
                                     struct.pack('<I', value if subtype == 5 else 0x76543210))
                    self.assertEqual(bytes(vm.mem_read(UI + 0x232eb0, 4)),
                                     struct.pack('<I', 0 if subtype == 4 else 1))
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2144, 4)), struct.pack('<hh', 2, 3))
            finally:
                vm.hook_del(hook)

    def test_cpp_clear_integer_inputs_preserve_native_verified_records(self):
        for subtype in (4, 5):
            for slot in range(15):
                with self.subTest(subtype=subtype, slot=slot):
                    result = subprocess.run([str(self.executable), '--clear', str(slot), str(subtype)],
                                            capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(bytes.fromhex(result.stdout), self.clears[(subtype-4)*15 + slot])

    def test_cpp_clear_rejects_invalid_integer_inputs_without_output(self):
        # These are internal encoder inputs, not additional on-wire subtypes.
        subtypes = (0, 1, 3, 6, 255, 256, 0x104, 0x105, 0x204, 0x205,
                    0x10004, 0x10005, 0xffffff04, 0xffffff05, 0xffffffff)
        cases = [(slot, subtype) for slot in (0, 14) for subtype in subtypes]
        cases += [(slot, subtype) for slot in (15, 255, 0x80000000, 0xffffffff)
                  for subtype in (4, 5)]
        for slot, subtype in cases:
            with self.subTest(subtype=subtype, slot=slot):
                result = subprocess.run([str(self.executable), '--clear', str(slot), str(subtype)],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertEqual(result.stderr, '')

    def test_native_identity_length_and_mission_provenance(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x1324 + 4*0xdb)[0], 0x401246)
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4*0xdb)[0], 0x46b44e)
        vm = self.vm()
        self.call(vm, 0x1246)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 13)
        self.assertEqual(self.image[0x1940a8:0x1940b3], b'nMisIdx<15\0')
        self.assertEqual(self.image[0x18a0e4:0x18a0f1], b'Mission_data\0')
        self.assertEqual(self.image[0x563e9:0x563ee], b'\xbe\xe4\xa0\x58\0')
        self.assertEqual(0x5642f + struct.unpack_from('<i', self.image, 0x5642b)[0], 0x584a0)
        self.assertEqual(self.image[0x584c3:0x584c9], b'\x89\x85\xc4\x2a\x0d\0')
        self.assertEqual(self.image[0xc96cd:0xc96d3], b'\x8b\x93\xc4\x2a\x0d\0')
        # The legacy DF label must not be mistaken for this build's journal.
        self.assertIn(b'PMVendCar.cpp\0', self.image[0x19ac90:0x19ace0])

    def test_cpp_empty_bootstrap_through_native_dispatch_no_stubs(self):
        self.assertEqual(len(self.logical), 15 * 13)
        for suppress in (0, 1):
            vm = self.vm(suppress)
            for slot in range(15):
                record = self.logical[slot*13:(slot+1)*13]
                self.assertEqual(record, b'\xdb\x04\0\0\0' + struct.pack('<II', slot, 0))
                self.dispatch(vm, record)
                self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)),
                                 bytes(4*(slot+1)) + b'\xa5'*(4*(14-slot)))
            self.assertEqual(bytes(vm.mem_read(UI + 0xc2144, 4)), struct.pack('<hh', 0, 1))
            self.assertEqual(bytes(vm.mem_read(UI + 0x232eb0, 4)), bytes(4))
            for at in (0xc2100, 0xc2140, 0xc2148):
                self.assertEqual(bytes(vm.mem_read(UI + at, 4)), b'\xa5'*4)

    def test_native_opaque_values_and_ignored_padding(self):
        for subtype in (4, 5):
            vm = self.vm()
            record = bytes([0xdb, subtype, 0xa5, 0x5a, 0xff]) + struct.pack('<II', 7, 0x12345678)
            self.dispatch(vm, record)
            self.assertEqual(bytes(vm.mem_read(UI + 0xc2104 + 7*4, 4)), b'\x78\x56\x34\x12')
            self.assertEqual(bytes(vm.mem_read(UI + 0x232eb8, 4)),
                             b'\x78\x56\x34\x12' if subtype == 5 else bytes(4))

    def test_invalid_slots_reach_original_assertion_without_array_write(self):
        for subtype in (4, 5):
            for slot in (15, 255, 0x80000000, 0xffffffff):
                vm = self.vm()
                vm.mem_write(UI + 0x232eb8, struct.pack('<I', 0x12345678))
                record = bytes([0xdb, subtype, 0, 0, 0]) + struct.pack('<II', slot, 0)
                self.dispatch(vm, record, stop=0xc9688)
                self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)), b'\xa5'*60)
                # Native subtype 5 changes selection BEFORE validating the slot.
                self.assertEqual(bytes(vm.mem_read(UI + 0x232eb8, 4)),
                                 bytes(4) if subtype == 5 else struct.pack('<I', 0x12345678))

    def test_native_truncation_fault_is_not_reported_as_success(self):
        for subtype in (4, 5):
            record = bytes([0xdb, subtype, 0, 0, 0]) + struct.pack('<II', 0, 0)
            for length in range(1, 13):
                with self.subTest(subtype=subtype, length=length):
                    vm = self.vm()
                    vm.mem_write(UI + 0x232eb8, b'\x5a'*4)
                    with self.assertRaises(UcError):
                        self.dispatch(vm, record[:length])
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)), b'\xa5'*60)
                    self.assertEqual(bytes(vm.mem_read(UI + 0x232eb8, 4)), b'\x5a'*4)

    def test_cpp_single_slot_clears_preserve_other_slots_and_native_flags(self):
        self.assertEqual(len(self.clears), 30)
        # Synthetic in-range low words exercise native page calculation. The
        # closed-widget path computes catalog addresses without reading rows.
        slots = [0x12340001 + slot for slot in range(15)]
        for subtype in (4, 5):
            for slot in range(15):
                with self.subTest(subtype=subtype, slot=slot):
                    record = self.clears[(subtype-4)*15 + slot]
                    self.assertEqual(record, bytes([0xdb, subtype, 0, 0, 0]) + struct.pack('<II', slot, 0))
                    vm = self.vm(suppress_open=1)
                    vm.mem_write(RESOURCE + 0xd2ac4, struct.pack('<I', RESOURCE + 0x1000))
                    vm.mem_write(UI + 0xc2104, struct.pack('<15I', *slots))
                    vm.mem_write(UI + 0x232eb8, struct.pack('<I', slots[slot]))
                    self.dispatch(vm, record)
                    expected = slots.copy()
                    expected[slot] = 0
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)), struct.pack('<15I', *expected))
                    self.assertEqual(bytes(vm.mem_read(UI + 0x232eb8, 4)),
                                     struct.pack('<I', 0 if subtype == 5 else slots[slot]))
                    self.assertEqual(bytes(vm.mem_read(UI + 0x232eb0, 4)),
                                     struct.pack('<I', 0 if subtype == 4 and slot == 14 else 1))
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2144, 4)), struct.pack('<hh', 2, 3))
                    for at in (0xc2100, 0xc2140, 0xc2148):
                        self.assertEqual(bytes(vm.mem_read(UI + at, 4)), b'\xa5'*4)

    def test_cpp_sparse_clear_sequence_recalculates_pages_and_is_idempotent(self):
        for subtype in (4, 5):
            vm = self.vm()
            vm.mem_write(RESOURCE + 0xd2ac4, struct.pack('<I', RESOURCE + 0x1000))
            slots = [0]*15
            for slot in (0, 4, 5, 9, 10, 14):
                slots[slot] = 0x123401a2  # Synthetic catalog index 418 with opaque high word.
            vm.mem_write(UI + 0xc2104, struct.pack('<15I', *slots))
            for slot, page, count in ((14, 2, 3), (10, 0, 2), (9, 0, 2),
                                      (5, 0, 1), (4, 0, 1), (0, 0, 1)):
                slots[slot] = 0
                record = self.clears[(subtype-4)*15 + slot]
                for _ in range(2):
                    self.dispatch(vm, record)
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)), struct.pack('<15I', *slots))
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc2144, 4)), struct.pack('<hh', page, count))

    def test_unknown_subtype_does_not_enter_quest_writer(self):
        for subtype in (0, 6, 255):
            vm = self.vm()
            self.dispatch(vm, bytes([0xdb, subtype]) + bytes(11))
            self.assertEqual(bytes(vm.mem_read(UI + 0xc2104, 60)), b'\xa5'*60)


if __name__ == '__main__':
    unittest.main()
