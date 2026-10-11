"""Current original battle builder -> standalone C++ logical input decoder.

Execute 118E50 through the 1191EE post-queue boundary, including real skill
lookup and queue copy. No helpers are stubbed. Synthetic state is not a live
battle; the post-queue UI/state cleanup and all damage/result logic are outside
this test. Two-side basic attack is the only promoted input contract.
"""
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import test_current_world_ready_builder as ready
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_ERR_READ_UNMAPPED, UcError
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT, BASE, SP, NET = ready.ROOT, ready.BASE, ready.SP, ready.NET
BATTLE, TARGETS, SKILL = 0x5000000, 0x3800000, 0x3810000
SELECTOR = BATTLE + 0xa9dc198


def build_fixture(directory, source_name='test_recovered_battle_command.cpp'):
    source = ROOT / 'tests' / source_name
    executable = directory / ('battle.exe' if os.name == 'nt' else 'battle')
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
            raise RuntimeError('Standalone battle test requires a C++20 compiler')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(v for k, v in environment.items() if k.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('Standalone battle test requires a C++20 compiler')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'battle.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


class CurrentBattleCommandTests(unittest.TestCase):
    vm = ready.CurrentWorldReadyBuilderTests.vm
    queued = ready.CurrentWorldReadyBuilderTests.queued

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != ready.IMAGE_SHA:
            raise AssertionError('Pinned current client image changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-battle-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def decode(self, record):
        text = subprocess.check_output([str(self.executable), '--decode', record.hex()],
                                       text=True, timeout=5).strip()
        return None if text == 'reject' else tuple(map(int, text.split()))

    def builder(self, targets=(0,), action=1, actor=0, modes=(1, 0), active=1,
                connected=1, context=0, poison=0xa5, count=None, skill=False,
                skill_id=0x9b, skill_kind=0):
        vm = self.vm()
        pages = {BATTLE, TARGETS, SKILL, SELECTOR & ~4095,
                 (SELECTOR + 0x2d10) & ~4095,
                 (BATTLE + 0xa9df73c) & ~4095,
                 (BATTLE + 0xa9e9c38) & ~4095}
        for page in pages:
            vm.mem_map(page, 4096)
        vm.mem_write(ready.STACK, bytes([poison]) * 0x4000)
        vm.mem_write(BATTLE + 0x10, struct.pack('<I', NET))
        vm.mem_write(BATTLE + 0x3c, struct.pack('<I', context))
        vm.mem_write(BATTLE + 0x44, struct.pack('<I', active))
        vm.mem_write(BATTLE + 0xa9e9c38, struct.pack('<II', *modes))
        vm.mem_write(BATTLE + 0xa9df73c, struct.pack('<i', 0 if skill else -1))
        vm.mem_write(NET + 0x2cb8, bytes([connected]))
        vm.mem_write(TARGETS, bytes(targets).ljust(14, b'\xff'))
        # Real selected-skill accessors 11B8C0 / 11B900 read these fixtures.
        vm.mem_write(SELECTOR + 0x10, struct.pack('<I', 1))
        vm.mem_write(SELECTOR + 0xdc, struct.pack('<I', SKILL))
        vm.mem_write(SELECTOR + 0x2d64, struct.pack('<I', 1))
        vm.mem_write(SELECTOR + 0x2d28, struct.pack('<I', SKILL))
        vm.mem_write(SKILL, bytes([skill_id, skill_kind]))
        size = len(targets) if count is None else count
        vm.mem_write(SP, struct.pack('<5I', ready.RETURN, action, actor,
                                    size & 0xffffffff, TARGETS))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, BATTLE)
        writes, calls = set(), []

        def written(uc, access, address, width, value, data):
            writes.update(i for i in range(16) if address <= SP - 16 + i < address + width)

        def trace(uc, address, width, data):
            rva = address - BASE
            if rva == 0x1191ee:
                uc.emu_stop()
            if rva in (0x1156a0, 0x11b8c0, 0x11b900, 0x132e0):
                calls.append(rva)
            if rva == 0x132e0:
                sp = uc.reg_read(UC_X86_REG_ESP)
                _, opcode, pointer, length = struct.unpack('<4I', uc.mem_read(sp, 16))
                self.assertEqual((opcode, pointer, length), (0x35, SP - 16, 16))
            if rva in (0x13370, 0x112130, 0x1120b0):
                raise AssertionError('Crossed transport or post-builder boundary')

        vm.hook_add(UC_HOOK_MEM_WRITE, written)
        vm.hook_add(UC_HOOK_CODE, trace)
        vm.emu_start(BASE + 0x118e50, ready.RETURN, timeout=1000000, count=10000)
        self.assertIn(vm.reg_read(UC_X86_REG_EIP), (BASE + 0x1191ee, ready.RETURN))
        return self.queued(vm), writes, calls, vm

    def test_basic_original_bytes_widths_and_unwritten_storage(self):
        for modes in ((1, 0), (0, 1), (1, 1), (0x80000000, 2)):
            for poison in (0, 0xa5, 0x5a, 0xff):
                for actor in (0, 14, 0x1234000e):
                    with self.subTest(modes=modes, poison=poison, actor=actor):
                        context = 0x89abcdef
                        record, writes, calls, _ = self.builder(
                            (0, 13, 14, 27), actor=actor, action=0x12340001,
                            modes=modes, poison=poison, context=context)
                        side = int(modes[0] == 0 and modes[1] != 0)
                        expected = bytes([0x35, actor & 255, 1, side, poison]) + struct.pack(
                            '<HHI', 0x2001, 0x2001, context) + bytes([poison]) * 4
                        self.assertEqual(record, expected)
                        self.assertEqual(writes, set(range(16)) - {3, 12, 13, 14, 15})
                        self.assertEqual(calls, [0x1156a0,
                            0x11b900 if side else 0x11b8c0, 0x132e0])
                        self.assertEqual(self.decode(record), (actor & 255, side, poison,
                            0x2001, 0x2001, context, poison * 0x01010101))

    def test_target_boundaries_duplicates_and_empty_masks(self):
        for targets in ((), (0,), (13,), (14,), (27,), (0, 0, 27), tuple(range(14))):
            record, _, _, _ = self.builder(targets)
            masks = [0, 0]
            for target in targets:
                masks[target // 14] |= 1 << (target % 14)
            self.assertEqual(self.decode(record)[3:5], tuple(masks))
        record, _, _, _ = self.builder((), count=-1)
        self.assertEqual(self.decode(record)[3:5], (0, 0))

    def test_native_state_guards_without_invented_server_policy(self):
        for kwargs in ({'modes': (0, 0)}, {'actor': 15}, {'actor': 255},
                       {'count': 15}, {'active': 0}, {'connected': 0}):
            with self.subTest(kwargs=kwargs):
                record, _, calls, vm = self.builder(**kwargs)
                self.assertEqual(record, b'')
                self.assertNotIn(0x132e0, calls)
                if 'connected' not in kwargs:
                    self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 20)

    def test_third_group_aliases_context_and_is_not_promoted(self):
        record, _, _, _ = self.builder((28, 41), context=0x12348000)
        self.assertEqual(struct.unpack_from('<I', record, 9)[0], 0x1234a001)
        # No interpretation as target 28/41: these bytes remain opaque context.
        self.assertEqual(self.decode(record)[3:6], (0, 0, 0x1234a001))

    def test_original_skill_continuation_is_outside_basic_contract(self):
        records, writes, calls, _ = self.builder((0, 14), action=3, skill=True)
        self.assertEqual(len(records), 34)
        for index, (action, masks) in enumerate(((0x83, (1, 0)), (3, (0, 1)))):
            record = records[index * 17:(index + 1) * 17]
            self.assertEqual(record, bytes([0x35, 0, action, 0, 0xa5]) +
                struct.pack('<HHII', *masks, 0, 0x9b))
            self.assertIsNone(self.decode(record))
        self.assertEqual(writes, set(range(16)) - {3})
        self.assertEqual(calls.count(0x132e0), 2)
        record, _, _, _ = self.builder(action=3, skill=False)
        self.assertEqual(record, b'')

    def test_cpp_black_box_rejects_truncation_and_unsupported_shapes(self):
        record, _, _, _ = self.builder()
        for length in range(17):
            self.assertIsNone(self.decode(record[:length]))
        for bad in (record + b'\0', record * 2, b'\x14\0' + record + b'\0'):
            self.assertIsNone(self.decode(bad))
        for offset, values in ((0, (0, 0x34, 0x36)), (1, (15, 255)),
                               (2, (0, 2, 3, 11, 0x81, 0x83, 255)), (3, (2, 255))):
            for value in values:
                bad = bytearray(record)
                bad[offset] = value
                self.assertIsNone(self.decode(bad))
        for offset in (6, 8):
            for value in (0x40, 0x80, 0xff):
                bad = bytearray(record)
                bad[offset] = value
                self.assertIsNone(self.decode(bad))
        bad = bytearray(record)
        bad[5:9] = struct.pack('<HH', 0x3fff, 1)
        self.assertIsNone(self.decode(bad))

    def test_native_guards_and_signed_count_before_target_pointer_read(self):
        original_vm = self.vm

        def unreadable_targets():
            machine = original_vm()

            def configure(vm, address, width, data):
                if address == BASE + 0x118e50:
                    vm.mem_unmap(TARGETS, 4096)

            machine.hook_add(UC_HOOK_CODE, configure)
            return machine

        with patch.object(self, 'vm', unreadable_targets):
            for arguments in ({'count': 15}, {'count': 0x7fffffff}, {'actor': 15},
                              {'actor': 0xffffffff}, {'active': 0}, {'modes': (0, 0)}):
                with self.subTest(arguments=arguments):
                    record, _, calls, vm = self.builder(**arguments)
                    self.assertEqual(record, b'')
                    self.assertNotIn(0x132e0, calls)
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 20)
            for count in (-0x80000000, -1, 0):
                with self.subTest(count=count):
                    record, _, calls, _ = self.builder(count=count, active=0x80000000,
                        modes=(0, 0x80000000), connected=255, context=0xffffffff)
                    self.assertEqual(self.decode(record),
                                     (0, 1, 0xa5, 0, 0, 0xffffffff, 0xa5a5a5a5))
                    self.assertEqual(calls.count(0x132e0), 1)
            # The disconnected guard is after the target loop, not a pointer guard.
            # Positive controls prove the fixture really removed readable targets.
            for connected in (0, 1):
                with self.subTest(connected=connected):
                    with self.assertRaises(UcError) as fault:
                        self.builder(count=1, connected=connected)
                    self.assertEqual(fault.exception.errno, UC_ERR_READ_UNMAPPED)

    def test_cpp_guarded_native_seed_mutations_and_combined_mask_limit(self):
        cases = []

        def add(record, accepted):
            cases.append(f'{int(accepted)} {bytes(record).hex()}\n')

        # Each possible 14-target split is produced by the original builder.
        # Alternating side/poison/context also checks opaque field preservation.
        for first_count in range(15):
            targets = tuple(range(first_count)) + tuple(range(14, 28 - first_count))
            record, _, _, _ = self.builder(targets, actor=14,
                modes=(0, 1) if first_count % 2 else (1, 0),
                poison=0xff if first_count % 2 else 0,
                context=0xffffffff if first_count % 2 else 0x80000000)
            self.assertEqual(record[5:9], struct.pack('<HH',
                (1 << first_count) - 1, (1 << (14 - first_count)) - 1))
            add(record, True)

        seed, _, _, _ = self.builder((0, 13, 14, 27), actor=14, modes=(0, 1),
                                    context=0x89abcdef, poison=0xa5)
        # Every subspan, not only prefixes, gets both inaccessible-page edges.
        for start in range(18):
            for end in range(start, 18):
                add(seed[start:end], start == 0 and end == 17)
        for length in range(18, 52):
            add((seed * 3)[:length], False)
        for offset in range(17):
            for value in range(256):
                changed = bytearray(seed)
                changed[offset] = value
                accepted = True
                if offset < 4:
                    accepted = (value == 0x35, value <= 14, value == 1, value <= 1)[offset]
                elif offset in (6, 8):
                    # This seed has only four target bits. A single byte change
                    # cannot reach 15; only the two reserved high bits can fail.
                    accepted = value < 0x40
                add(changed, accepted)

        # Cross both groups' cardinalities, rotating the runs to expose bit/byte
        # boundary errors. Expectations use target-list lengths, not popcount.
        for first_count in range(15):
            for second_count in range(15):
                for rotation in range(14):
                    first = sum(1 << ((bit + rotation) % 14) for bit in range(first_count))
                    second = sum(1 << ((bit + 13 - rotation) % 14)
                                 for bit in range(second_count))
                    changed = bytearray(seed)
                    changed[5:9] = struct.pack('<HH', first, second)
                    add(changed, first_count + second_count <= 14)
                    for offset in (6, 8):
                        for reserved in (0x40, 0x80, 0xc0):
                            bad = bytearray(changed)
                            bad[offset] |= reserved
                            add(bad, False)
        # Revisit the seed after the rejection/acceptance corpus in one process.
        add(seed, True)
        result = subprocess.run([str(self.executable), '--guard-batch'],
            input=''.join(cases), text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(),
                         f'Guarded basic-attack checks passed: {2 * len(cases)}')
        print(f'Battle guard corpus: {len(cases)} candidates, {2 * len(cases)} checks')


if __name__ == '__main__':
    unittest.main()
