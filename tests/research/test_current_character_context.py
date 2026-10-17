"""Current preselection 1F: original parser/waiter/caller, never UI or auth.

Starts B910/F930 after their outgoing request. Only the OS tick-count import is
adapted. Native receive framing, copying, queue consumption and continuation
execute unmodified. Synthetic state is not a live world acceptance claim.
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
from unicorn import UcError, UC_ERR_READ_UNMAPPED, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn import UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                              UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP)

ROOT, BASE, SP, NET = routes.ROOT, routes.BASE, routes.SP, routes.NET
MAIN, CONTEXT_PAGE, CLOCK = 0x3800000, 0x4000000, 0x4100000
RETURN = routes.STACK + 0x3ff0
CONTEXT = CONTEXT_PAGE + 4096 - 124


def build_fixture(directory):
    source = ROOT / 'tests/test_recovered_character_context.cpp'
    executable = directory / ('context.exe' if os.name == 'nt' else 'context')
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
            raise RuntimeError('C++20 compiler required')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(v for k, v in environment.items() if k.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('C++20 compiler required')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'context.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


class CurrentCharacterContextTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    run_to = routes.CurrentRouteAdvertisementTests.run_to

    def call(self, vm, entry, *arguments):
        # RVA 1000 is the real 1F length function, not a usable stop sentinel.
        vm.mem_write(SP, struct.pack('<' + 'I' * (len(arguments) + 1), RETURN, *arguments))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, NET)
        self.run_to(vm, entry, RETURN - BASE)

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned current client changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-context-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def cpp(self, logical):
        result = subprocess.check_output([str(self.executable), '--decode', logical.hex()],
                                         text=True, timeout=5).strip()
        return None if result == 'reject' else bytes.fromhex(result)

    def parser_vm(self, logical):
        vm = self.vm()
        vm.mem_protect(0x5b4000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(0x5b4da8, bytes(4))  # Native optional logging disabled.
        codec = NET + 0x758
        vm.mem_write(NET + 0x2cb8, b'\x01')
        vm.mem_write(codec + 0xc10, logical)
        vm.mem_write(codec + 0x1810, struct.pack('<II', len(logical), 0))
        return vm

    def continuation(self, body, alternate=False, connected=True):
        vm = self.parser_vm(b'\x1f' + body)
        vm.mem_map(MAIN, 0x180000)
        vm.mem_map(CONTEXT_PAGE, 4096)
        vm.mem_write(CONTEXT_PAGE, b'\xa5' * 4096)
        vm.mem_map(CLOCK, 4096)
        vm.mem_protect(0x570000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(0x5707bc, struct.pack('<I', CLOCK))
        vm.mem_write(NET + 0x2cb8, bytes([connected]))
        pointer_offset = 0x670 if alternate else 0x15e88
        vm.mem_write(MAIN + pointer_offset, struct.pack('<I', NET))
        vm.mem_write(MAIN + 0x668, struct.pack('<I', CONTEXT))
        # Exact stack layout immediately after 149C0 returned. We do not run or
        # emulate the outgoing authentication request.
        frame_size = 0x108 if alternate else 0x184
        output = CONTEXT if alternate else SP + 0x108
        vm.mem_write(SP + frame_size, struct.pack('<II', RETURN, 0))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ESI, MAIN)
        before = bytes(vm.mem_read(MAIN, 0x180000))
        copied, reads_after_copy, copy_writes, trace = [False], [], [], []

        def code(uc, address, size, context):
            if address == CLOCK:
                esp = uc.reg_read(UC_X86_REG_ESP)
                ret = struct.unpack('<I', uc.mem_read(esp, 4))[0]
                uc.reg_write(UC_X86_REG_EAX, 1000)
                uc.reg_write(UC_X86_REG_ESP, esp + 4)
                uc.reg_write(UC_X86_REG_EIP, ret)
                return
            rva = address - BASE
            if rva == 0x14b2a:
                copied[0] = True
            if rva in (0x13420, 0x13650, 0x13670, 0x14b28):
                trace.append(rva)
            if rva in (0x149c0, 0x13370, 0x2dc0):
                raise AssertionError('Crossed outgoing request, transport or UI boundary')

        def read(uc, access, address, size, value, context):
            if copied[0] and address < output + 124 and output < address + size:
                reads_after_copy.append((uc.reg_read(UC_X86_REG_EIP) - BASE, address, size))

        def write(uc, access, address, size, value, context):
            if uc.reg_read(UC_X86_REG_EIP) == BASE + 0x14b28:
                copy_writes.append((address, size))

        hooks = (vm.hook_add(UC_HOOK_CODE, code), vm.hook_add(UC_HOOK_MEM_READ, read),
                 vm.hook_add(UC_HOOK_MEM_WRITE, write))
        self.run_to(vm, 0xf967 if alternate else 0xb980, RETURN - BASE)
        for hook in hooks:
            vm.hook_del(hook)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + frame_size + 8)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1)
        self.assertEqual(bytes(vm.mem_read(MAIN, 0x180000)), before)
        self.assertFalse(reads_after_copy)
        if connected:
            self.assertEqual(bytes(vm.mem_read(output, 124)), body)
            self.assertEqual(copy_writes, [(output + offset, 4) for offset in range(0, 124, 4)])
            self.assertEqual(trace.count(0x13670), 1)
            self.assertEqual(struct.unpack('<I', vm.mem_read(NET + 0x2cc0, 4))[0], 0)
            self.assertEqual(struct.unpack('<I', vm.mem_read(NET + 0x758 + 0x1814, 4))[0], 125)
        else:
            self.assertFalse(trace)
            self.assertFalse(copy_writes)
        return vm, output

    def test_cpp_shape_bounds_and_opaque_bytes(self):
        subprocess.run([str(self.executable)], check=True, capture_output=True, timeout=10)
        for body in (bytes(124), b'\xff' * 124, bytes(range(124))):
            self.assertEqual(self.cpp(b'\x1f' + body), body)
        self.assertIsNone(self.cpp(b'\x1f' + bytes(125)))

    def test_original_b910_discards_every_payload_byte_after_copy(self):
        # One-byte impulses distinguish every payload offset from the zero lab
        # candidate. No decoded payload pointer escapes the tested continuation.
        for index in range(-1, 124):
            body = bytearray(124)
            if index >= 0:
                body[index] = 0xff
            with self.subTest(offset=index):
                vm, output = self.continuation(bytes(body))
                self.assertEqual(bytes(vm.mem_read(output - 1, 1)), b'\xa5')
                self.assertEqual(bytes(vm.mem_read(output + 124, 4)), struct.pack('<I', RETURN))

    def test_original_parser_requires_125_and_preserves_next_record(self):
        target = struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x1f)[0] - BASE
        self.assertEqual(self.image[target:target + 6], b'\xb8\x7d\x00\x00\x00\xc3')
        logical = b'\x1f' + bytes(range(124))
        for length in range(1, 125):
            vm = self.parser_vm(logical[:length])
            self.call(vm, 0x13420, 0)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1)
            self.assertEqual(struct.unpack('<I', vm.mem_read(NET + 0x2cc0, 4))[0], length)
            self.assertIsNone(self.cpp(logical[:length]))
        vm = self.parser_vm(logical + b'\x01\xf6')
        self.call(vm, 0x13420, 0)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
        self.call(vm, 0x13650, 0)
        pointer = vm.reg_read(UC_X86_REG_EAX)
        self.assertEqual(bytes(vm.mem_read(pointer, 125)), logical)
        self.call(vm, 0x13670, 0)
        self.call(vm, 0x13420, 0)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
        self.assertEqual(bytes(vm.mem_read(pointer, 2)), b'\x01\xf6')

    def test_disconnected_waiter_success_is_not_received_context(self):
        vm, output = self.continuation(bytes(124), connected=False)
        self.assertEqual(bytes(vm.mem_read(output, 124)), b'\xa5' * 124)

    def test_alternate_f930_retains_body_and_f410_reads_hazardous_token_offsets(self):
        body = bytearray(124)
        body[38], body[78], body[118] = 1, 2, 0xfe
        vm, output = self.continuation(bytes(body), alternate=True)
        self.assertEqual(output, CONTEXT)
        for selected, expected in ((0, 1), (1, 2), (2, 0xfe)):
            vm.mem_write(MAIN + 0x660, struct.pack('<h', selected))
            vm.mem_write(SP, struct.pack('<III', RETURN, 0, 0))
            vm.reg_write(UC_X86_REG_ESP, SP)
            vm.reg_write(UC_X86_REG_ECX, MAIN)
            self.run_to(vm, 0xf410, 0x14c50)
            esp = vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(struct.unpack('<I', vm.mem_read(esp + 12, 4))[0], expected)
        # A selected index of 3 reads byte 158, outside the 124-byte destination.
        # This accessor lacks a local bound check; upstream reachability is NOT
        # established, so this is a guarded hazard, not a live vulnerability claim.
        vm.mem_write(MAIN + 0x660, struct.pack('<h', 3))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, MAIN)
        with self.assertRaises(UcError) as error:
            vm.emu_start(BASE + 0xf410, BASE + 0x14c50, count=32)
        self.assertEqual(error.exception.errno, UC_ERR_READ_UNMAPPED)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + 0xf425)

    def test_current_world_dispatch_does_not_treat_1f_as_player_spawn(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4 * 0x1f)[0],
                         BASE + 0x6b517)
        vm = self.vm()
        vm.mem_map(CONTEXT_PAGE, 4096)
        vm.mem_write(CONTEXT_PAGE + 4095, b'\x1f')
        vm.reg_write(UC_X86_REG_EAX, CONTEXT_PAGE + 4095)
        vm.reg_write(UC_X86_REG_ESP, SP)
        # Only the opcode is mapped; any attempted body access fails.
        self.run_to(vm, 0x68b4c, 0x6b517)




if __name__ == '__main__':
    unittest.main()
