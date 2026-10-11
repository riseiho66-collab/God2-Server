"""C++ candidate -> pinned original decoder, login dispatch and route lookup.

Synthetic Unicorn memory only. No sockets, client process, UI or shared build.
The only stub is sprintf; routing, record selection and port extraction execute
original instructions. Login slices stop before queue-consumption calls.
"""
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import UC_PROT_READ, UC_PROT_EXEC, UC_PROT_WRITE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EBP,
    UC_X86_REG_ESP, UC_X86_REG_EIP,
)

BASE, STACK, BODY, NET, GROUP, UI, OUTPUT, CODEC = (
    0x400000, 0x3000000, 0x3100000, 0x3200000,
    0x3300000, 0x3400000, 0x3500000, 0x3600000,
)
SP, RETURN, TABLE = STACK + 0x2000, BASE + 0x1000, 0x5b48a0
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'


def build_fixture(directory):
    """Compile only the standalone header assertions in a private temp folder."""
    source = ROOT / 'tests/test_recovered_server_routes.cpp'
    executable = directory / ('routes.exe' if os.name == 'nt' else 'routes')
    compiler = next((shutil.which(name) for name in ('cl', 'clang++', 'g++', 'c++')
                     if shutil.which(name)), None)
    msvc_args = ['/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                 '/I' + str(ROOT / 'src'), str(source),
                 '/Fe:' + str(executable), '/Fo:' + str(directory / 'routes.obj')]
    environment = None
    if compiler and Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, *msvc_args]
    elif compiler:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    elif os.name == 'nt':
        vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / (
            'Microsoft Visual Studio/Installer/vswhere.exe')
        installation = subprocess.check_output(
            [str(vswhere), '-latest', '-products', '*', '-requires',
             'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property',
             'installationPath'], text=True, timeout=30).strip()
        if not installation:
            raise RuntimeError('Standalone route test requires a C++20 compiler')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(
            f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
            text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        compiler_path = next(value for name, value in environment.items() if name.lower() == 'path')
        command = [shutil.which('cl.exe', path=compiler_path), *msvc_args]
    else:
        raise RuntimeError('Standalone route test requires a C++20 compiler')
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError('Standalone C++ build failed:\n' + result.stdout + result.stderr)
    return executable


class CurrentRouteAdvertisementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != IMAGE_SHA:
            raise AssertionError('Current mapped client image identity changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-route-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def vm(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        # Only the shared table-pointer page is mutable within the pinned image.
        vm.mem_protect(TABLE & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(TABLE, struct.pack('<I', GROUP + 0x100))
        for address, size in ((STACK, 0x4000), (BODY, 0x2000), (NET, 0x5000),
                              (GROUP, 0x2000), (UI, 0x2000),
                              (OUTPUT, 0x2000), (CODEC, 0x3000)):
            vm.mem_map(address, size)
        vm.mem_write(STACK, b'\xa5' * 0x4000)
        vm.mem_write(GROUP, b'\xa5' * 0x2000)
        vm.mem_write(GROUP + 0x100, bytes(0x70c))
        vm.mem_write(UI, b'\xa5' * 0x2000)
        vm.mem_write(OUTPUT, b'\xa5' * 0x2000)
        return vm

    def run_to(self, vm, entry, stop):
        vm.emu_start(BASE + entry, BASE + stop, timeout=1000000, count=100000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + stop,
                         'Original slice did not reach its bounded stop')

    def call(self, vm, entry, *arguments, this=NET):
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, this)
        vm.mem_write(SP, struct.pack('<' + 'I' * (1 + len(arguments)), RETURN, *arguments))
        self.run_to(vm, entry, RETURN - BASE)

    def candidate(self, port=2593, route=1, address=(127, 0, 0, 1)):
        output = subprocess.check_output(
            [str(self.executable), '--dump', str(port), str(route), *map(str, address)],
            text=True, timeout=10)
        frames = [bytes.fromhex(line) for line in output.splitlines()]
        self.assertEqual(list(map(len, frames)), [8, 12, 8, 78])
        return frames

    def decode(self, vm, wire):
        # 10490 expands the zero seed; 106F0 decrypts; 10750 checks the checksum.
        vm.mem_write(CODEC, bytes(0x3000))
        self.call(vm, 0x10490, this=CODEC)
        self.assertEqual(bytes(vm.mem_read(CODEC + 0x2556, 1)), b'\0')
        vm.mem_write(CODEC + 8, struct.pack('<I', 1))
        vm.mem_write(BODY, b'\xa5' * 0x1000)
        vm.mem_write(BODY + 0x100, wire)
        self.call(vm, 0x106f0, BODY + 0x102, len(wire) - 2, this=CODEC)
        plain = bytes(vm.mem_read(BODY + 0x100, len(wire)))
        self.assertEqual(struct.unpack_from('<H', plain)[0], len(wire))
        self.call(vm, 0x10750, BODY + 0x100, len(wire))
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1, 'Original checksum rejected C++ frame')
        self.assertEqual(bytes(vm.mem_read(BODY, 0x100)), b'\xa5' * 0x100)
        self.assertEqual(bytes(vm.mem_read(BODY + 0x100 + len(wire), 16)), b'\xa5' * 16)
        return plain

    def advertise(self, vm, plain_frames):
        # The enclosing login function supplies UI output and stack locals.
        vm.mem_write(SP + 0x138, struct.pack('<I', UI + 0x100))
        writes = []
        hook = vm.hook_add(UC_HOOK_MEM_WRITE,
                           lambda uc, access, address, size, value, context:
                           writes.append((address, size)))
        try:
            for plain, stop in zip(plain_frames, (0x14265, 0x142c6, 0x1430e)):
                vm.mem_write(BODY + 0x100, plain)
                vm.mem_protect(BODY, 0x1000, UC_PROT_READ)
                vm.reg_write(UC_X86_REG_ESP, SP)
                vm.reg_write(UC_X86_REG_EBP, NET)
                vm.reg_write(UC_X86_REG_EAX, BODY + 0x102)
                self.run_to(vm, 0x14070, stop)
                vm.mem_protect(BODY, 0x1000, UC_PROT_READ | UC_PROT_WRITE)
        finally:
            vm.hook_del(hook)
        expected = bytearray(b'\xa5' * 0x2000)
        expected[0x100:0x80c] = bytes(0x70c)
        expected[0x1c4:0x1cc] = plain_frames[1][3:11]
        expected[0x1cc:0x1d0] = plain_frames[2][3:7]
        self.assertEqual(bytes(vm.mem_read(GROUP, 0x2000)), expected)
        expected_ui = bytearray(b'\xa5' * 0x2000)
        expected_ui[0x100:0x104] = plain_frames[0][3:7]
        self.assertEqual(bytes(vm.mem_read(UI, 0x2000)), expected_ui)
        self.assertEqual(bytes(vm.mem_read(SP + 0x14, 12)), bytes(12))
        self.assertEqual(bytes(vm.mem_read(SP + 0x28, 4)), bytes(4))
        allowed = ((SP - 8, SP + 0x2c), (UI + 0x100, UI + 0x104),
                   (GROUP + 0x1c4, GROUP + 0x1d0))
        for address, size in writes:
            self.assertTrue(any(a <= address and address + size <= b for a, b in allowed),
                            f'Unexpected parser write: {address:#x}, {size}')

    def lookup(self, vm, raw_list, selector, expected_address=None, port=None, fallback=False):
        vm.mem_write(BODY + 0x800, bytes(raw_list))
        vm.mem_write(OUTPUT, b'\xa5' * 0x2000)
        host, port_out = OUTPUT + 0x100, OUTPUT + 0x200
        endpoint_out, route_out = OUTPUT + 0x300, OUTPUT + 0x304
        formatted = []

        def sprintf(uc, address, size, context):
            if address != BASE + 0x147af7:
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret, dest, fmt, a, b, c, d = struct.unpack('<7I', uc.mem_read(sp, 28))
            self.assertEqual(bytes(uc.mem_read(fmt, 12)), b'%d.%d.%d.%d\0')
            self.assertEqual(dest, host)
            octets = (a, b, c, d)
            self.assertTrue(all(value <= 255 for value in octets))
            formatted.append(octets)
            text = '.'.join(map(str, octets)).encode('ascii')
            uc.mem_write(dest, text + b'\0')
            uc.reg_write(UC_X86_REG_EAX, len(text))
            uc.reg_write(UC_X86_REG_ESP, sp + 4)
            uc.reg_write(UC_X86_REG_EIP, ret)

        hook = vm.hook_add(UC_HOOK_CODE, sprintf)
        try:
            if fallback:
                self.call(vm, 0x12250, 0, 0, host, port_out)
            else:
                self.call(vm, 0x12310, 0, 0, host, port_out, selector,
                          BODY + 0x800, endpoint_out, route_out)
        finally:
            vm.hook_del(hook)
        expected = bytearray(b'\xa5' * 0x2000)
        if expected_address is None:
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
            self.assertFalse(formatted)
            if not fallback:
                expected[0x100] = 0
        else:
            self.assertEqual(formatted, [expected_address])
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1 if fallback else host)
            name = '.'.join(map(str, expected_address)).encode('ascii') + b'\0'
            expected[0x100:0x100 + len(name)] = name
            expected[0x200:0x202] = struct.pack('<H', port)
            if not fallback:
                expected[0x300:0x308] = bytes(8)
        self.assertEqual(bytes(vm.mem_read(OUTPUT, 0x2000)), expected)

    def prepared(self, port=2593, route=1, address=(127, 0, 0, 1)):
        vm = self.vm()
        frames = [self.decode(vm, wire) for wire in self.candidate(port, route, address)]
        self.assertEqual([frame[2] for frame in frames], [4, 5, 6, 7])
        self.advertise(vm, frames[:3])
        return vm, frames[3][3:-1]

    def test_standalone_header_assertions(self):
        result = subprocess.check_output([str(self.executable)], text=True, timeout=10)
        self.assertIn('assertions passed', result)

    def test_original_dispatch_and_length_tables(self):
        for opcode, target, length in ((4, 0x14234, 5), (5, 0x1426f, 9), (6, 0x142d0, 5)):
            index = self.image[0x144d4 + opcode - 4]
            self.assertEqual(struct.unpack_from('<I', self.image, 0x144b8 + 4 * index)[0], BASE + target)
            length_fn = struct.unpack_from('<I', self.image, 0x1324 + 4 * opcode)[0] - BASE
            self.assertEqual(self.image[length_fn:length_fn + 6],
                             b'\xb8' + struct.pack('<I', length) + b'\xc3')

    def test_cpp_routes_parse_and_resolve_both_record_selectors(self):
        for port, route, address in ((2593, 1, (127,0,0,1)), (1, 255, (127,23,45,67)),
                                     (65535, 127, (127,255,255,254))):
            with self.subTest(port=port, route=route, address=address):
                vm, raw = self.prepared(port, route, address)
                for selector in (0, 1):
                    self.lookup(vm, raw, selector, address, port)

    def test_lookup_requires_matching_nonzero_record_route(self):
        vm, raw = self.prepared()
        for route in (0, 2, 255):
            with self.subTest(route=route):
                changed = bytearray(raw)
                changed[2 + 32] = route
                self.lookup(vm, changed, 0)
                self.lookup(vm, changed, 1, (127,0,0,1), 2593)

    def test_absent_advertisement_and_zero_route_do_not_resolve(self):
        vm, raw = self.prepared()
        vm.mem_write(GROUP + 0x1cc, bytes(4))
        self.lookup(vm, raw, 0)
        self.lookup(vm, raw, 0, fallback=True)
        vm.mem_write(GROUP + 0x100, bytes(0x70c))
        self.lookup(vm, raw, 1)

    def test_original_fallback_uses_same_advertised_endpoint(self):
        vm, raw = self.prepared()
        self.lookup(vm, raw, 0, (127,0,0,1), 2593, fallback=True)


if __name__ == '__main__':
    unittest.main()
