"""Offline C2S25 reconstruction, mutation recovery and native request state.

Private C++20 process fixture; original producer/append instructions in Unicorn.
No existing unittest methods, receive consumers, sockets or shared builds run.
"""
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

import test_current_inventory as inventory
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ESP

routes = inventory.routes
ROOT = Path(__file__).resolve().parents[2]

FIXTURE = r'''
#include "protocol/RecoveredInventoryItemRequest.h"
#include <charconv>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using Codec = god2::RecoveredInventoryItemRequest;
constexpr auto maximum = Codec::encode({65535, 255, 255});
static_assert(maximum == Codec::LogicalRecord{0x25, 255, 255, 255, 255});
static_assert(noexcept(Codec::encode({0, 0, 0})));
void dump(const Codec::LogicalRecord& bytes) {
    constexpr char hex[] = "0123456789abcdef";
    for (auto byte : bytes) std::cout << hex[byte >> 4] << hex[byte & 15];
    std::cout << '\n';
}
int main() {
    for (std::string line; std::getline(std::cin, line);) {
        std::istringstream input(line);
        std::string mode, text, extra;
        input >> mode;
        if (mode == "encode") {
            unsigned item, slot, tail;
            if (!(input >> item >> slot >> tail) || (input >> extra) ||
                item > 65535 || slot > 255 || tail > 255) return 3;
            dump(Codec::encode({static_cast<std::uint16_t>(item),
                               static_cast<std::uint8_t>(slot),
                               static_cast<std::uint8_t>(tail)}));
        } else if (mode == "decode") {
            input >> text;
            if (input >> extra || text.size() % 2) return 3;
            std::vector<std::uint8_t> bytes;
            for (std::size_t i = 0; i < text.size(); i += 2) {
                unsigned value = 0;
                auto parsed = std::from_chars(text.data() + i, text.data() + i + 2, value, 16);
                if (parsed.ec != std::errc{} || parsed.ptr != text.data() + i + 2) return 3;
                bytes.push_back(static_cast<std::uint8_t>(value));
            }
            const auto before = bytes;
            const auto decoded = Codec::decode(bytes);
            if (bytes != before) return 4;
            if (decoded) dump(Codec::encode(*decoded));
            else std::cout << "reject\n";
        } else return 3;
    }
}
'''


def build_fixture(directory):
    source = directory / 'request.cpp'
    source.write_text(FIXTURE, encoding='ascii')
    executable = directory / ('request.exe' if os.name == 'nt' else 'request')
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
            raise RuntimeError('Request follow-up requires C++20')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(v for k, v in environment.items() if k.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('Request follow-up requires C++20')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'request.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


class InventoryRequestFollowupTests(unittest.TestCase):
    vm = inventory.CurrentInventoryTests.vm
    call = inventory.CurrentInventoryTests.call
    run_to = inventory.CurrentInventoryTests.run_to
    consumer_vm = inventory.CurrentInventoryTests.consumer_vm

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned current image changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-request-followup-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def candidate(self, commands):
        result = subprocess.run([str(self.executable)], input='\n'.join(commands) + '\n',
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def test_mutated_records_and_rejection_recovery_in_one_process(self):
        original = bytes.fromhex('25349231ff')
        records = [original]
        for offset in range(5):
            for value in range(256):
                if value != original[offset]:
                    records.append(original[:offset] + bytes((value,)) + original[offset + 1:])
        commands, expected = [], []
        for index, record in enumerate(records):
            # Interleave partial/extended inputs with distinct valid recovery
            # records to detect stale results in one long-lived decoder process.
            malformed = record[:index % 5] if index % 2 else record + b'\0'
            recovery = struct.pack('<BHBB', 0x25, index, index & 255, (index >> 2) & 255)
            commands += ['decode ' + r.hex() for r in (malformed, record, recovery)]
            expected += ['reject', record.hex() if record[0] == 0x25 else 'reject', recovery.hex()]
        self.assertEqual(self.candidate(commands), expected)

    def native_sequence(self, initial_size, cases):
        vm = self.consumer_vm()
        queue = routes.NET + 0x36c8
        vm.mem_write(inventory.UI + 0x86874, struct.pack('<I', routes.NET))
        vm.mem_write(routes.NET + 0x36c4, struct.pack('<I', initial_size))
        expected_queue = bytearray((i * 71 + 19) & 255 for i in range(0xa00 + 8))
        vm.mem_write(queue, bytes(expected_queue))
        writes = []
        vm.hook_add(UC_HOOK_MEM_WRITE,
            lambda uc, access, address, size, value, context: writes.append((address, size)))
        size, records = initial_size, []
        for index, (item, slot, tail, gate, occupied) in enumerate(cases):
            # Synthetic fixture changes only: zero inventory versus occupied
            # metadata with IDs deliberately unrelated to the requested item.
            state = bytearray((i * 29 + index) & 255 for i in range(50 * 24))
            for position in range(50):
                state[24 * position] = 7 if occupied else 0
                state[24 * position + 4:24 * position + 6] = (
                    struct.pack('<H', 0x7000 + position) if occupied else bytes(2))
            vm.mem_write(inventory.SLOTS, bytes(state))
            vm.mem_write(inventory.UI + 0x866e4, struct.pack('<I', gate))
            before_ui = bytes(vm.mem_read(inventory.UI, 0x233000))
            before_net = bytes(vm.mem_read(routes.NET, 0x5000))
            writes.clear()
            self.call(vm, 0x96350, (tail << 24) | 0xee0000 | item,
                      0xabcdef00 | slot, index ^ 0xfedcba98, this=inventory.UI)
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP + 16)
            self.assertEqual(bytes(vm.mem_read(inventory.UI, len(before_ui))), before_ui)
            record = b'' if gate else struct.pack('<BHBB', 0x25, item, slot, tail)
            expected_net = bytearray(before_net)
            expected_net[0x36c8 + size:0x36c8 + size + len(record)] = record
            expected_net[0x36c4:0x36c8] = struct.pack('<I', size + len(record))
            self.assertEqual(bytes(vm.mem_read(routes.NET, 0x5000)), expected_net)
            for address, length in writes:
                allowed = routes.STACK <= address and address + length <= routes.STACK + 0x4000
                if not gate:
                    allowed |= address == routes.NET + 0x36c4 and length == 4
                    allowed |= queue + size <= address and address + length <= queue + size + 5
                self.assertTrue(allowed, f'Unexpected write {address:#x}/{length}')
            expected_queue[size:size + len(record)] = record
            size += len(record)
            self.assertLessEqual(size, 0xa00)
            self.assertEqual(bytes(vm.mem_read(queue, len(expected_queue))), expected_queue)
            if record:
                records.append((item, slot, tail, record))
        actual = self.candidate([f'encode {item} {slot} {tail}' for item, slot, tail, _ in records])
        self.assertEqual(actual, [record.hex() for _, _, _, record in records])

    def test_native_requests_across_inventory_and_gate_transitions(self):
        cases = []
        for index, slot in enumerate((*range(50), 50, 127, 128, 255)):
            item = (0, 1, 255, 256, 0x7fff, 0x8000, 0xffff, 0x9234)[index % 8]
            tail = (index * 197) & 255
            cases.extend(((item, slot, tail, 0, False),
                          (item, slot, tail, 0x80000000, True),
                          (item, slot, tail, 0, True)))
        self.native_sequence(3, cases)

    def test_native_exact_queue_capacity_and_gated_full_queue(self):
        self.native_sequence(0xa00 - 20, [
            (0, 49, 255, 0, False), (0xffff, 50, 128, 0, True),
            (0x9234, 128, 0, 0, False), (0x8000, 255, 127, 0, True),
            (1, 0, 1, 1, True), (1, 49, 1, 0xffffffff, False),
        ])


if __name__ == '__main__':
    unittest.main()
