"""Pinned S2C72 catalog and scalar slices, not a successful live NPC spawn.

Original CSV tokenizer/accessors and 5711D..575FC loader instructions execute.
The original four scalar tests retain their limited boundary. The resource test
also executes original CSV/ROMZ/ROM loaders, allocator, lookup and CC380 through
its scalar writes, stopping before an unresolved scene dereference. Platform
adapters and explicit test-environment inputs are listed in current_npc_resources.
The render-dependency test separately bypasses that scene block and executes
CC72A..CC751 using constructor-zero pixel fields, never a scene placement.
The coordinate-only test executes CC621..CC72A against a native HMD map object;
it stops before rendering and grants no placement eligibility.
No entity allocator, renderer, asset lookup or branch-result helper is stubbed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import test_current_route_advertisement as routes
from tools.strike_lab.omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                               UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP,
                               UC_X86_REG_EIP)

RESOURCE, ACTOR, WORLD = 0x3800000, 0x3700000, 0x4000000
BASE, SP, BODY = routes.BASE, routes.SP, routes.BODY
GAME_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
GAME_DECODED_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
ROW_SHA = {3793: '964b81209c07c02fccd13ab70067aab13ab55fbfa82ead479ce0db536e128562',
           3954: '254f14af0f230da5023b4c168d33becce65840e18c638b720eaddf268ac69ac6'}


def build_fixture(directory):
    """Standalone compile in a private temporary directory, never shared build."""
    source = ROOT / 'tests/test_recovered_npc_spawn.cpp'
    executable = directory / ('npc.exe' if os.name == 'nt' else 'npc')
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
            raise RuntimeError('Standalone NPC test requires a C++20 compiler')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(v for k, v in environment.items() if k.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('Standalone NPC test requires a C++20 compiler')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'npc.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


class CurrentNpcSpawnTests(unittest.TestCase):
    call = routes.CurrentRouteAdvertisementTests.call
    run_to = routes.CurrentRouteAdvertisementTests.run_to

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned current image changed')
        cls.atlas = json.loads((ROOT / 'artifacts/world-atlas/npcs.json').read_text())
        raw = (ROOT.parent / 'God2/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
        decoded = decode_csvz(raw)
        if (hashlib.sha256(raw).hexdigest(), hashlib.sha256(decoded).hexdigest()) != (
                GAME_SHA, GAME_DECODED_SHA):
            raise AssertionError('Current gamedata changed')
        lines = decoded.splitlines()
        starts = [i for i, line in enumerate(lines) if line.startswith(b'NPCAppearData,')]
        if len(starts) != 1:
            raise AssertionError('Expected one NPCAppearData section')
        start = starts[0]
        count = int(lines[start].split(b',')[1])
        cls.rows = {int(line.split(b',')[0]): line for line in lines[start+1:start+1+count]}
        if count != 4043 or len(cls.rows) != count or max(cls.rows) != 6224:
            raise AssertionError('Current NPC selector inventory changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-npc-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def vm(self):
        vm = routes.CurrentRouteAdvertisementTests.vm(self)
        vm.mem_map(RESOURCE, 0xb3000)
        vm.mem_map(ACTOR, 0x1000)
        vm.mem_write(ACTOR, b'\xa5' * 0x1000)
        vm.mem_map((WORLD + 0xaa36480) & ~4095, 4096)
        vm.mem_write(WORLD + 0xaa36480, struct.pack('<I', RESOURCE))
        return vm

    def logical(self, selector, *coordinates):
        return bytes.fromhex(subprocess.check_output(
            [str(self.executable), '--dump', str(selector), *map(str, coordinates)],
            text=True, timeout=5).strip())

    def load_row(self, vm, selector):
        row = self.rows[selector]
        # Run the real comma tokenizer into its 380-byte field slots.
        vm.mem_write(RESOURCE + 8, struct.pack('<H', len(row.split(b','))))
        vm.mem_write(BODY, row + b'\n\0')
        self.call(vm, 0x51be0, BODY, this=RESOURCE)
        slot = RESOURCE + 0x121ea + 94 * selector
        vm.mem_write(slot, b'\xa5' * 94)
        conversions = []

        def decimal(uc, address, size, context):
            if address != BASE + 0x1480b4:
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret, source, fmt, output = struct.unpack('<4I', uc.mem_read(sp, 16))
            self.assertEqual(bytes(uc.mem_read(fmt, 3)), b'%d\0')
            raw = bytes(uc.mem_read(source, 380)).split(b'\0', 1)[0]
            self.assertRegex(raw, rb'^[0-9]+$')
            value = int(raw)
            self.assertLessEqual(value, 0x7fffffff)
            conversions.append(value)
            uc.mem_write(output, struct.pack('<I', value))
            uc.reg_write(UC_X86_REG_EAX, 1)
            uc.reg_write(UC_X86_REG_ESP, sp + 4)  # cdecl arguments stay on stack.
            uc.reg_write(UC_X86_REG_EIP, ret)

        hook = vm.hook_add(UC_HOOK_CODE, decimal)
        vm.reg_write(UC_X86_REG_EBP, RESOURCE)
        vm.reg_write(UC_X86_REG_ESP, SP)
        self.run_to(vm, 0x5711d, 0x575fc)
        vm.hook_del(hook)
        self.assertEqual(conversions, [selector, int(row.split(b',')[2]), 0, 1])
        return slot

    def consumer(self, logical, count=6224, stop=0x6a9ef):
        self.assertEqual(len(logical), 21)
        vm = self.vm()
        for selector in (3793, 3954):
            self.load_row(vm, selector)
        vm.mem_write(RESOURCE + 0x121e8, struct.pack('<h', count))
        vm.mem_write(BODY, logical)
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBP, WORLD)
        vm.reg_write(UC_X86_REG_EBX, BODY)
        self.run_to(vm, 0x6a68b, stop)
        return vm

    def test_current_dispatch(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x1324 + 4*0x72)[0], BASE + 0x127c)
        self.assertEqual(self.image[0x127c:0x1282], b'\xb8\x15\0\0\0\xc3')
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4*0x72)[0], BASE + 0x6a68b)
        self.assertEqual(self.image[0x18a12c:0x18a13a], b'NPCAppearData\0')
        # Section-dispatch match calls this exact current loader.
        self.assertEqual(self.image[0x56272:0x56277], b'\xbe\x2c\xa1\x58\0')
        self.assertEqual(0x562b8 + struct.unpack_from('<i', self.image, 0x562b4)[0], 0x570f0)

    def test_current_data_real_loader_and_resource_boundary(self):
        npc = self.atlas['current_templates']
        raw = (ROOT.parent / 'God2' / npc['provenance']['file']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), npc['provenance']['sha256'])
        decoded = decode_csvz(raw)
        self.assertEqual(hashlib.sha256(decoded).hexdigest(), npc['decoded_sha256'])
        for selector, resource in ((3793, 88), (3954, 82)):
            self.assertEqual(hashlib.sha256(self.rows[selector]).hexdigest(), ROW_SHA[selector])
            vm = self.consumer(self.logical(selector))
            slot = RESOURCE + 0x121ea + 94*selector
            self.assertEqual(bytes(vm.mem_read(slot, len(self.rows[selector].split(b',')[1]) + 1)),
                             self.rows[selector].split(b',')[1] + b'\0')
            self.assertEqual(struct.unpack('<HH', vm.mem_read(slot + 0x10, 4)), (0x4000, resource))
            self.assertEqual(struct.unpack('<I', vm.mem_read(SP + 0x14, 4))[0], slot)
            self.assertEqual(struct.unpack('<I', vm.mem_read(SP + 0x24, 4))[0], slot)
            # Stopped at CALL 61580: no manufactured asset result or entity.
            args = struct.unpack('<2I', vm.mem_read(SP - 8, 8))
            self.assertEqual(tuple(a & 255 for a in args), (0, resource))
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP - 8)
            # Execute 61580's real one-based-to-zero-based conversion, stopping
            # before 61510 reads the unqualified live resource manager.
            self.run_to(vm, 0x6a9ef, 0x615ab)
            sp = vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(vm.mem_read(sp + 0x10, 1)[0], resource - 1)
            # Current table ordinal is a row, not a placement; retain exact bytes.
            row = npc['rows'][resource - 1]
            self.assertEqual(decoded.splitlines()[row['record_id'] - 1], bytes.fromhex(row['raw_hex']))

    def test_selector_fallback_signed_count_and_inclusive_bound(self):
        for primary, secondary, count, chosen in (
                (3793, 0, 3793, 3793), (3793, 3954, 3954, 3954),
                (3793, 3955, 3954, 3793), (65535, 3954, 3954, 3954)):
            record = bytearray(self.logical(3793))
            struct.pack_into('<HH', record, 1, primary, secondary)
            vm = self.consumer(bytes(record), count, stop=0x6a72f)
            selected = struct.unpack('<I', vm.mem_read(SP + 0x24, 4))[0]
            first = struct.unpack('<I', vm.mem_read(SP + 0x14, 4))[0]
            self.assertEqual(selected, RESOURCE + 0x121ea + 94*chosen)
            self.assertEqual(first, RESOURCE + 0x121ea + 94*primary if primary <= count else 0)
        for selector, count in ((3793, 3792), (65535, 6224), (3793, -1)):
            record = bytearray(self.logical(3793))
            struct.pack_into('<H', record, 1, selector)
            self.consumer(bytes(record), count, stop=0x6b517)
        # Zero is not rejected by this index guard; that is not spawn eligibility.
        record = bytearray(self.logical(3793)); record[1:5] = bytes(4)
        vm = self.consumer(bytes(record), 0, stop=0x6a72f)
        self.assertEqual(struct.unpack('<I', vm.mem_read(SP + 0x24, 4))[0], RESOURCE + 0x121ea)

    def test_original_scalar_writes_and_state_argument_only(self):
        for selector in (3793, 3954):
            for x, y in ((0, 0), (65, 61), (240, 54), (32767, 32767), (1, 32767)):
                logical = self.logical(selector, x, y)
                vm = self.vm()
                vm.mem_write(BODY, logical[1:])
                vm.reg_write(UC_X86_REG_ESP, SP)
                vm.reg_write(UC_X86_REG_EDI, BODY)
                vm.reg_write(UC_X86_REG_ESI, ACTOR)
                # Resource-index input is an explicit sentinel, not a lookup
                # result. Only this isolated scalar block is being tested.
                vm.reg_write(UC_X86_REG_EBX, 0xa5a5)
                self.run_to(vm, 0xcc621, 0xcc690)
                self.assertEqual(struct.unpack('<I', vm.mem_read(ACTOR, 4))[0], selector)
                self.assertEqual(bytes(vm.mem_read(ACTOR + 4, 2)), b'\xa5\xa5')
                self.assertEqual(struct.unpack('<HH', vm.mem_read(ACTOR + 6, 4)), (0, logical[9] >> 5))
                self.assertEqual(struct.unpack('<II', vm.mem_read(ACTOR + 0x10, 8)), (x, y))
        # All five low bits are passed to CAFE0; only state 1 is retained.
        # No assertion that arbitrary states have meaningful gameplay semantics.
        for state in range(32):
            vm = self.vm()
            body = bytearray(self.logical(3793)[1:]); body[8] = 0xa0 | state
            vm.mem_write(BODY, bytes(body))
            vm.reg_write(UC_X86_REG_ESP, SP)
            vm.reg_write(UC_X86_REG_EDI, BODY)
            vm.reg_write(UC_X86_REG_ESI, ACTOR)
            self.run_to(vm, 0xcc76f, 0xcc78c)
            self.assertEqual(struct.unpack('<6I', vm.mem_read(SP - 24, 24))[3] & 255, state)

    def test_town_guide_resource_native_load_and_cache(self):
        from tools.strike_lab import current_npc_resources as native
        vm=self.vm()
        oracle=native.NativeNpcResources(vm,ROOT.parent/'God2',extended_decode_budget=True)
        raw=(ROOT.parent/'God2/Data2/Patch/NPC.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.atlas['current_templates']['provenance']['sha256'])
        self.assertEqual(oracle.load_csv(decode_csvz(raw)),319)
        oracle.configure_empty_bank()
        entry=native.TABLE+0x244e4+76*19
        self.assertEqual(oracle.string(entry,64).lower(),b'data2\\rom\\npc\\npc2720.rom')
        self.assertEqual(oracle.call(0x5f190,0,19),0xffffffff)
        self.assertEqual(oracle.load_ordinal(19),1)
        self.assertEqual(oracle.call(0x5f190,0,19),0)
        self.assertEqual(struct.unpack('<h',vm.mem_read(entry+64,2))[0],0)
        self.assertEqual(struct.unpack('<h',vm.mem_read(native.TABLE+0x244dc,2))[0],1)
        self.assertEqual(oracle.native_decodes,[(19,0,519564)])
        self.assertEqual(len(oracle.opens),1)
        self.assert_native_rom_pixels(vm,native.ROM,oracle.decoded[19],expected_images=80)
        self.assertEqual(oracle.load_ordinal(19),1)
        self.assertEqual(len(oracle.opens),1)
        self.assertEqual(struct.unpack('<h',vm.mem_read(native.TABLE+0x244dc,2))[0],1)
        self.assertFalse(oracle.handles)

    def test_native_resource_tables_rom_loads_and_cc380(self):
        from tools.strike_lab import current_npc_resources as native
        vm = self.vm()
        for selector in (3793, 3954):
            self.load_row(vm, selector)
        vm.mem_write(RESOURCE+0x121e8, struct.pack('<h', 6224))
        oracle = native.NativeNpcResources(vm, ROOT.parent/'God2')
        raw = (ROOT.parent/'God2/Data2/Patch/NPC.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         self.atlas['current_templates']['provenance']['sha256'])
        self.assertEqual(oracle.load_csv(decode_csvz(raw)), 319)
        table = native.TABLE
        self.assertEqual(struct.unpack('<I', vm.mem_read(table+0x244e0, 4))[0], 319)
        self.assertEqual(struct.unpack('<I3h', vm.mem_read(table+0x2accc, 10)), (10, 0, 88, 89))
        oracle.configure_empty_bank()
        # Unloaded values come from real table initialization, not an injected
        # failure response. Inclusive group last ordinal is 88; count is 89.
        for ordinal in (0, 81, 87, 88, 89, 255):
            self.assertEqual(oracle.call(0x5f190, 0, ordinal), 0xffffffff)
        # Initialize the actual empty NPC pool. Scene/renderer dependencies are
        # unmapped poison, not fabricated structures or successful helper returns.
        pool = WORLD+0x1539aed8
        vm.mem_map(pool & ~4095, 0x1f000)
        vm.mem_map(WORLD, 4096)
        unknown = 0xdead0000
        vm.mem_write(WORLD+0xbc, struct.pack('<I', unknown))
        oracle.call(0xca680, WORLD, unknown, unknown, unknown, unknown, unknown, this=pool)
        flag = WORLD+0xa7f2f3c
        vm.mem_map(flag & ~4095, 4096)
        vm.mem_write(flag, struct.pack('<I', unknown))
        vm.mem_write(BODY, self.logical(3793))
        # Test CC380's negative guard with the actual unloaded lookup result.
        # The dispatcher's separate missing-asset diagnostic path is unqualified.
        unloaded = oracle.call(0x5f190, 0, 87)
        oracle.call(0xcc380, native.SCRATCH, BODY+1, unloaded,
                    unknown, unknown, unknown, unknown, this=pool)
        self.assertEqual(bytes(vm.mem_read(native.SCRATCH, 8)), bytes(8))
        self.assertEqual(struct.unpack('<I', vm.mem_read(pool+0x70, 4))[0], 0xffffffff)
        for slot, ordinal in enumerate((81, 87)):
            entry = table+0x244e4+76*ordinal
            self.assertEqual(oracle.string(entry, 64).lower(),
                             ('data2\\rom\\npc\\'+native.ASSETS[ordinal][0]+'.rom').encode())
            self.assertEqual(struct.unpack('<hBB4h', vm.mem_read(entry+64, 12)),
                             (-1, 16, 6, 0, 0, 0, 0))
            self.assertEqual(oracle.load_ordinal(ordinal), 1)
            self.assertEqual(oracle.call(0x5f190, 0, ordinal), slot)
            self.assertEqual(oracle.call(0x5f200, 0, ordinal), 0)
            self.assertEqual(struct.unpack('<h', vm.mem_read(entry+64, 2))[0], slot)
            self.assertEqual(struct.unpack('<h', vm.mem_read(table+0x244dc, 2))[0], slot+1)
            # Native cache hit must preserve the counter and avoid a second open.
            self.assertEqual(oracle.load_ordinal(ordinal), 1)
            self.assertEqual(len(oracle.opens), slot+1)
            bank = native.ROM + 0x1514*slot
            self.assertEqual([struct.unpack('<I', vm.mem_read(bank+offset, 4))[0]
                              for offset in (0, 4, 0x88, 0x108c, 0x1490)],
                             [2776, 8, 60, 16, 0])
            self.assert_native_rom_pixels(vm, bank, oracle.decoded[ordinal])
        self.assertEqual(oracle.native_decodes, [(81, 0, 246947), (87, 1, 263835)])
        self.assertFalse(oracle.handles)

        # Native caller's counter propagation, no guessed resource slot.
        vm.reg_write(UC_X86_REG_ESI, native.MANAGER)
        vm.reg_write(UC_X86_REG_EDI, table)
        oracle.run(0x60db3, 0x60dce)
        self.assertEqual(struct.unpack('<h', vm.mem_read(native.MANAGER+0x121fc, 2))[0], 2)
        for pool_slot, (selector, resource_slot, direction, x, y) in enumerate(
                ((3954, 0, 4, 240, 54), (3793, 1, 5, 65, 61))):
            vm.mem_write(BODY, self.logical(selector))
            vm.reg_write(UC_X86_REG_ESP, native.SP)
            vm.reg_write(UC_X86_REG_EBP, WORLD)
            vm.reg_write(UC_X86_REG_EBX, BODY)
            oracle.run(0x6a68b, 0xcc690)
            actor = pool+0x70+0x1d8*pool_slot
            self.assertEqual(vm.reg_read(UC_X86_REG_ESI), actor)
            self.assertEqual(struct.unpack('<I3h', vm.mem_read(actor, 10)),
                             (selector, resource_slot, 0, direction))
            self.assertEqual(struct.unpack('<II', vm.mem_read(actor+0x10, 8)), (x, y))
            self.assertEqual(struct.unpack('<hh', vm.mem_read(actor+0xa, 4)), (-1, -1))
        self.assertEqual(struct.unpack('<I', vm.mem_read(pool+0x70+2*0x1d8, 4))[0], 0xffffffff)
        self.assertEqual(oracle.seh_accesses, {0x2982a, 0x29831, 0x29a9d})
        self.assertEqual(bytes(vm.mem_read(0, 4)), b'\xff'*4)
        # A real null load must fail despite the explicitly modeled FS:[0].
        vm.mem_write(native.SCRATCH, b'\xa1\0\0\0\0')
        with self.assertRaisesRegex(AssertionError, 'outside native SEH'):
            vm.emu_start(native.SCRATCH, native.SCRATCH+5, count=1)

    def test_native_npc_renderer_dependency_without_scene_placement(self):
        from tools.strike_lab import current_npc_resources as native
        vm = self.vm()
        for selector in (3793, 3954):
            self.load_row(vm, selector)
        vm.mem_write(RESOURCE+0x121e8, struct.pack('<h', 6224))
        n = native.NativeNpcResources(vm, ROOT.parent/'God2')
        raw = (ROOT.parent/'God2/Data2/Patch/NPC.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         self.atlas['current_templates']['provenance']['sha256'])
        self.assertEqual(n.load_csv(decode_csvz(raw)), 319)
        n.configure_empty_bank()
        for ordinal in (81, 87):
            self.assertEqual(n.load_ordinal(ordinal), 1)
        n.initialize_renderer()
        self.assertEqual(n.call(0x1b310, this=native.RENDERER), 4096)
        pool, unknown = WORLD+0x1539aed8, 0xdead0000
        vm.mem_map(pool & ~4095, 0x1f000)
        vm.mem_map(WORLD, 4096)
        vm.mem_write(WORLD+0xbc, struct.pack('<I', unknown))
        n.call(0xca680, WORLD, native.RENDERER, unknown, unknown, unknown, unknown, this=pool)
        # Explicit render-test offsets, not a recovered live camera origin.
        vm.mem_write(pool+0x68, bytes(8))
        flag = WORLD+0xa7f2f3c
        vm.mem_map(flag & ~4095, 4096)
        vm.mem_write(flag, struct.pack('<I', unknown))
        for slot, selector in enumerate((3954, 3793)):
            logical = self.logical(selector)
            vm.mem_write(BODY, logical)
            vm.reg_write(UC_X86_REG_ESP, native.SP)
            vm.reg_write(UC_X86_REG_EBP, WORLD)
            vm.reg_write(UC_X86_REG_EBX, BODY)
            n.run(0x6a68b, 0xcc690)
            actor = pool+0x70+0x1d8*slot
            self.assertEqual(vm.reg_read(UC_X86_REG_ESI), actor)
            self.assertEqual(bytes(vm.mem_read(actor+0x18, 8)), bytes(8))
            # Deliberately bypass scene projection. The constructor's zero pixel
            # fields are resource-test inputs, never an NPC placement or camera.
            n.run(0xcc72a, 0xcc751)
            self.assertEqual(struct.unpack('<hh', vm.mem_read(actor+0xa, 4)), (slot, -1))
            node = native.RENDERER+0x10+0x290*slot
            bank = native.ROM+0x1514*slot
            direction = logical[9] >> 5
            self.assertEqual(vm.mem_read(node, 1)[0], 2)
            self.assertEqual(vm.mem_read(node+1, 1)[0], direction)
            self.assertEqual(struct.unpack('<hh', vm.mem_read(node+0x12, 4)), (0, 0))
            self.assertEqual(struct.unpack('<h', vm.mem_read(node+0x16, 2))[0], slot)
            self.assertEqual(struct.unpack('<I', vm.mem_read(node+0x34, 4))[0], bank)
            self.assertEqual(bytes(vm.mem_read(node+0x38, 4)),
                             bytes(vm.mem_read(bank+0x1090+4*direction, 4)))
            # CC72A derives palette 2 from the retained selector high bits 3.
            self.assertEqual(struct.unpack('<h', vm.mem_read(node+0x2c, 2))[0], 2)
            self.assertEqual(bytes(vm.mem_read(node+0x44, 4)), bytes(vm.mem_read(bank+16, 4)))
            self.assertEqual(vm.mem_read(node+9, 1)[0], 1)
            command_slot = struct.unpack('<h', vm.mem_read(node+0xe, 2))[0]
            self.assertEqual(command_slot, slot)
            command = native.SURFACE+0x1258+200*command_slot
            self.assertEqual(vm.mem_read(command, 1)[0], 2)
            self.assertEqual(bytes(vm.mem_read(command+0x8c, 4)), bytes(vm.mem_read(node+0x40, 4)))
            self.assertEqual(bytes(vm.mem_read(command+0x94, 4)), bytes(vm.mem_read(bank+16, 4)))
        self.assertEqual(n.call(0x1b310, this=native.RENDERER), 4094)
        # The native resource bound rejects slot 512 before allocating a handle.
        self.assertEqual(n.call(0x1afe0, 512, 0, 0, 0, 1, 0xffffffff, 0, 0,
                                this=native.RENDERER), 0xffffffff)
        self.assertEqual(n.call(0x1b310, this=native.RENDERER), 4094)
        self.assertFalse(n.handles)
        self.assertTrue(n.locks)
        self.assertTrue(all(depth == 0 for depth in n.locks.values()))
        self.assertEqual(bytes(vm.mem_read(0, 4)), b'\xff'*4)
        self.assertEqual(n.seh_accesses,
                         {0x2982a, 0x29831, 0x29a9d, 0x1aa17, 0x1aa1e, 0x1abe3})

    def test_native_npc_coordinate_projection_on_loaded_indoor_map(self):
        from tools.strike_lab.current_indoor_resources import (
            NativeIndoorResources, MANAGER, SP as scene_sp, SCRATCH)
        from tools.strike_lab.indoor_navigation import parse_hmd, navigation_inputs

        vm = self.vm()
        n = NativeIndoorResources(vm, ROOT.parent/'God2')
        self.assertEqual(n.load_manager(), 1)
        indoor = n.u32(MANAGER+0x1030)
        self.assertNotEqual(indoor, 0)
        self.assertEqual(n.u32(MANAGER+0x30), 2)
        grid, width, height = struct.unpack('<3I', vm.mem_read(indoor+0x8c, 12))
        source, overlays = navigation_inputs(parse_hmd(n.hmd))
        evidence = json.loads((ROOT/'artifacts/world-atlas/indoor-2-15.json').read_text())
        self.assertEqual(source, evidence['base'])
        self.assertEqual(overlays, evidence['overlays'])
        self.assertEqual((source['width'], source['height']), (10, 30))
        self.assertEqual((width, height), (evidence['grid']['side'],)*2)
        self.assertEqual((width, height), (31, 31))
        self.assertEqual(bytes(vm.mem_read(grid, width*height)),
                         bytes.fromhex(evidence['grid']['cells_hex']))

        # Real pool initialization, explicit coordinate-only owner binding.
        # NPC resources and renderer stay poison: this slice must never use them.
        pool, poison = WORLD+0x1539aed8, 0xdead0000
        vm.mem_map(pool & ~4095, 0x1f000)
        vm.mem_map(WORLD, 4096)
        vm.mem_write(WORLD+0xbc, struct.pack('<I', MANAGER))
        n.call(0xca680, WORLD, poison, poison, poison, poison, poison, this=pool)
        actor = pool+0x70
        scene_before = bytes(vm.mem_read(MANAGER, 0x2000))
        grid_before = bytes(vm.mem_read(grid, width*height))
        visits = []
        hooks = [vm.hook_add(UC_HOOK_CODE,
                            lambda uc, address, size, context: visits.append(address-BASE),
                            begin=BASE+rva, end=BASE+rva)
                 for rva in (0x49330, 0x49b30, 0x149630)]
        self.addCleanup(lambda: [vm.hook_del(hook) for hook in hooks])

        samples = ((0, 0), (1, 0), (0, 1), (17, 13), (30, 0), (0, 30),
                   (30, 30), (31, 30), (30, 31), (65, 61), (240, 54),
                   (32767, 32767))
        for selector in (3954, 3793):
            for x, y in samples:
                with self.subTest(selector=selector, x=x, y=y):
                    logical = self.logical(selector, x, y)
                    vm.mem_write(BODY, logical[1:])
                    vm.mem_write(actor+0x18, b'\xa5'*8)
                    vm.mem_write(scene_sp, b'\xa5'*0x40)
                    vm.reg_write(UC_X86_REG_ESP, scene_sp)
                    vm.reg_write(UC_X86_REG_EBP, pool)
                    vm.reg_write(UC_X86_REG_ESI, actor)
                    vm.reg_write(UC_X86_REG_EDI, BODY)
                    vm.reg_write(UC_X86_REG_EBX, 0xffff)  # No resource lookup claim.
                    visits.clear()
                    n.run(0xcc621, 0xcc72a, instruction_limit=1000, timeout_us=0)
                    self.assertEqual(visits, [0x49330, 0x49b30, 0x149630, 0x149630])
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP), scene_sp)
                    self.assertEqual(struct.unpack('<2I', vm.mem_read(actor+0x10, 8)), (x, y))
                    # Independent arithmetic from pinned 49B30 and CC6F6/CC6F9;
                    # the constructed 31-cell native grid gives basis 30.
                    expected = (40*(x+y)+40, 20*(30-x+y)+20)
                    self.assertEqual(struct.unpack('<2f', vm.mem_read(actor+0x18, 8)), expected)
                    self.assertEqual(struct.unpack('<2i', vm.mem_read(scene_sp+0x14, 8)), expected)
                    self.assertEqual(struct.unpack('<2h', vm.mem_read(actor+0xa, 4)), (-1, -1))
                    self.assertEqual(bytes(vm.mem_read(scene_sp+0x30, 16)), b'\xa5'*16)
                    if x < width and y < height:
                        n.call(0x493c0, *expected, SCRATCH+0x1000, SCRATCH+0x1004,
                               this=MANAGER)
                        self.assertEqual(struct.unpack('<2i', vm.mem_read(SCRATCH+0x1000, 8)),
                                         (x, y))
        self.assertEqual(bytes(vm.mem_read(MANAGER, 0x2000)), scene_before)
        self.assertEqual(bytes(vm.mem_read(grid, width*height)), grid_before)
        # Retained positions are outside this source grid. Their arithmetic
        # success above cannot authorize placing either NPC in area2/scene15.
        for selector in (3954, 3793):
            position = struct.unpack_from('<I', self.logical(selector), 17)[0]
            x, y = (position >> 2) & 0x7fff, position >> 17
            self.assertFalse(0 <= x < width and 0 <= y < height)
        self.assertTrue(all(not p['runtime_eligible'] for p in self.atlas['placements']))
        self.assertFalse(n.handles)
        self.assertTrue(n.locks)
        self.assertTrue(all(depth == 0 for depth in n.locks.values()))
        self.assertEqual(n.u32(0), 0xffffffff)

        # Missing dependency must fault in original CC69D before pixel writes.
        vm.mem_write(WORLD+0xbc, struct.pack('<I', poison))
        vm.mem_write(actor+0x18, b'\xa5'*8)
        vm.reg_write(UC_X86_REG_ESP, scene_sp)
        vm.reg_write(UC_X86_REG_EBP, pool)
        vm.reg_write(UC_X86_REG_ESI, actor)
        vm.reg_write(UC_X86_REG_EDI, BODY)
        vm.reg_write(UC_X86_REG_EBX, 0xffff)
        visits.clear()
        with self.assertRaisesRegex(AssertionError, 'Indoor native failure RVA cc69d'):
            n.run(0xcc621, 0xcc72a, instruction_limit=1000, timeout_us=0)
        self.assertEqual(visits, [])
        self.assertEqual(bytes(vm.mem_read(actor+0x18, 8)), b'\xa5'*8)

    def assert_native_rom_pixels(self, vm, bank, decoded, *, expected_images=60):
        """Independent PCX RLE check against all native-decoded image buffers."""
        self.assertEqual(decoded[:12], b'IGSROM02\0\0\0\0')
        position, image_index, palette_index = 12, 0, 0
        while position < len(decoded):
            tag = decoded[position:position+8]
            length = struct.unpack_from('<I', decoded, position+8)[0]
            payload = decoded[position+12:position+12+length]
            self.assertEqual(len(payload), length)
            position += 12+length
            if tag == b'PALETTE1':
                pointer = struct.unpack('<I', vm.mem_read(bank+8+4*palette_index, 4))[0]
                expected = b''.join(struct.pack('<H', value & 0x7fff)
                                    for value in struct.unpack('<256H', payload))
                self.assertEqual(bytes(vm.mem_read(pointer, 512)), expected)
                palette_index += 1
            elif tag == b'PCX_RWIF':
                xmin, ymin, xmax, ymax = struct.unpack_from('<4H', payload, 4)
                width, height = xmax-xmin+1, ymax-ymin+1
                stride = struct.unpack_from('<H', payload, 66)[0]
                self.assertEqual(stride, width)
                self.assertTrue(0 < width <= 256 and 0 < height <= 256)
                pixels, cursor = bytearray(), 128
                while len(pixels) < width*height:
                    value = payload[cursor]; cursor += 1
                    if value & 0xc0 == 0xc0:
                        repeat = value & 0x3f
                        self.assertGreater(repeat, 0)
                        pixels.extend(bytes([payload[cursor]])*repeat); cursor += 1
                    else:
                        pixels.append(value)
                self.assertEqual(len(pixels), width*height)
                pointer = struct.unpack('<I', vm.mem_read(bank+0x8c+4*image_index, 4))[0]
                self.assertEqual(struct.unpack('<3H', vm.mem_read(pointer, 6)), (width, height, 256))
                image = struct.unpack('<I', vm.mem_read(pointer+0x14, 4))[0]
                self.assertEqual(bytes(vm.mem_read(image, len(pixels))), pixels)
                self.assertGreater(len(set(pixels)), 1)
                image_index += 1
        self.assertEqual((position, image_index, palette_index), (len(decoded), expected_images, 8))


if __name__ == '__main__':
    unittest.main()
