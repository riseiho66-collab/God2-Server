"""Lossless C++ 3B codec versus existing pinned native helpers at actual store.

Synthetic probes only. Stops immediately after 98E2B; no display, metadata
lookup, formula, gameplay transition, runtime integration, or socket execution.
"""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_companion_instance as companion
from tools.strike_lab import current_quest_instance as quest


def build_fixture(directory, *, source=None):
    """Compile only the owned standalone test, with warnings treated as errors."""
    executable = directory / ('instance.exe' if os.name == 'nt' else 'instance')
    compiler = next((shutil.which(name) for name in ('cl', 'clang++', 'g++', 'c++')
                     if shutil.which(name)), None)
    environment = None
    if not compiler and os.name == 'nt':
        vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / (
            'Microsoft Visual Studio/Installer/vswhere.exe')
        installation = subprocess.check_output([str(vswhere), '-latest', '-products', '*',
            '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
            '-property', 'installationPath'], text=True, timeout=30).strip()
        if not installation:
            raise RuntimeError('Instance codec test requires a C++20 compiler')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(value for key, value in environment.items() if key.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('Instance codec test requires a C++20 compiler')
    source = source or ROOT / 'tests/test_recovered_instance_update.cpp'
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/permissive-', '/utf-8', '/O2', '/I' + str(ROOT / 'src'), str(source),
                   '/Fe:' + str(executable), '/Fo:' + str(directory / 'instance.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Wpedantic', '-Werror',
                   '-O2', '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, errors='replace', capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


def probe(slot=0, header=0xd8c71234, word8=0xbead, packed=0xf5a39c7e):
    # Same opaque envelope bytes as the existing companion helper.
    record = bytearray((0x81 + offset * 17) & 255 for offset in range(20))
    struct.pack_into('<I', record, 0, header)
    struct.pack_into('<H', record, 8, word8)
    struct.pack_into('<I', record, 12, packed)
    return bytes((0x3b, 0xd3, slot, 0x69, 0x96)) + record


def raw_fields(slot, stored):
    return (slot, stored[2] & 63, struct.unpack_from('<H', stored, 0)[0],
            struct.unpack_from('<H', stored, 8)[0],
            struct.unpack_from('<I', stored, 12)[0])


class CurrentInstanceUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = quest.evidence()
        cls.quest = quest.NativeInstance(cls.image)
        cls.companion = companion.NativeInstance(cls.image)
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-instance-update-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def test_cpp_requirement_reference_matches_native_serial_reader(self):
        from tools.strike_lab import current_quest_requirements as requirements
        _,table=requirements.evidence()
        packets=[];expected=[]
        for row in table['records']:
            serial=int(bytes.fromhex(row['raw_fields_hex'][0]))
            native=quest.NativeInstance(self.image)
            packet=quest.fixture(slot=0,serial=serial,low_word=4201)
            self.assertTrue(native.ingest(packet))
            observed=native.forward(0,4201)['serial']
            packets.append(packet);expected.append(str(observed))
        for category in range(64):
            for flags in (0,0x40,0x80,0xc0):
                for serial in (0,1,169,170,65535):
                    packet=bytearray(quest.fixture(serial=serial,category=category))
                    packet[7]|=flags
                    packets.append(bytes(packet))
                    expected.append(str(serial) if category==20 else 'none')
        result=subprocess.run([str(self.executable),'--requirements'],
            input=''.join(packet.hex()+'\n' for packet in packets),text=True,
            capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.splitlines(),expected)

    def codec(self, packets):
        result = subprocess.run([str(self.executable), '--batch'],
            input=''.join(packet.hex() + '\n' for packet in packets),
            text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = result.stdout.splitlines()
        self.assertEqual(len(rows), len(packets))
        return [None if row == 'reject' else
                (bytes.fromhex(row.split()[0]), tuple(map(int, row.split()[1:])))
                for row in rows]

    def compare_store(self, packet, decoded, use_companion=True):
        slot = packet[2]
        accepted = slot < 50
        self.assertEqual(decoded is not None, accepted)
        if accepted:
            encoded, fields = decoded
            self.assertEqual(encoded, packet)
        else:
            encoded, fields = packet, None

        native = self.quest
        native.events.clear()
        native.setreg('EFLAGS', 2)
        native.vm.mem_write(quest.UI + quest.SLOTS - 4, b'\xcc' * (50 * 24 + 8))
        self.assertEqual(native.ingest(encoded), accepted)
        expected = bytearray(b'\xcc' * (50 * 24 + 8))
        writes = [event for event in native.events if event['access'] == 'write']
        if accepted:
            expected[4 + slot * 24:24 + slot * 24] = encoded[5:]
            stored = bytes(native.vm.mem_read(quest.UI + quest.SLOTS + 24 * slot, 20))
            self.assertEqual(stored, encoded[5:])
            self.assertEqual(raw_fields(slot, stored), fields)
            self.assertEqual([(e['rva'], e['region'], e['offset'], e['size']) for e in writes],
                             [(0x98e2b, 'slots', 24 * slot + i, 4) for i in range(0, 20, 4)])
            reads = [e for e in native.events if e['access'] == 'read' and e['rva'] == 0x98e2b]
            self.assertEqual([(e['region'], e['offset'], e['size']) for e in reads],
                             [('packet', 4096 - 25 + 5 + i, 4) for i in range(0, 20, 4)])
        else:
            self.assertEqual(writes, [])
        self.assertEqual(bytes(native.vm.mem_read(quest.UI + quest.SLOTS - 4, len(expected))),
                         expected)
        self.assertEqual(bytes(native.vm.mem_read(native.packet_address, 25)), encoded)

        if use_companion:
            # packet_store constructs this envelope; require exact equality so
            # native execution cannot silently compare a different logical input.
            self.assertEqual(encoded[:5], bytes((0x3b, 0xd3, slot, 0x69, 0x96)))
            native = self.companion
            for dispatch in ('primary', 'secondary'):
                result = native.packet_store(slot, encoded[5:], dispatch)
                self.assertEqual(result['copied'], accepted)
                self.assertEqual(result['stop_rva'], 0x98e2d if accepted else 0x98fbd)
                self.assertEqual(bytes(native.vm.mem_read(native.MESSAGE, 25)), encoded)
                if accepted:
                    stored = bytes(native.vm.mem_read(native.STORE + 24 * slot, 20))
                    self.assertEqual(stored, encoded[5:])
                    self.assertEqual(raw_fields(slot, stored), fields)
                    self.assertEqual(result['writes'], [
                        [0x98e2b, native.STORE + 24 * slot + i, 4,
                         struct.unpack_from('<I', stored, i)[0]] for i in range(0, 20, 4)])

    def test_cpp_guard_pages_roundtrip_ownership_and_every_byte(self):
        result = subprocess.run([str(self.executable)], text=True,
                                capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(),
                         'Guarded instance-update checks passed: 29552')

    def test_native_length_and_cpp_exact_record_contract(self):
        self.assertEqual(self.quest.length(), 25)
        packet = probe()
        malformed = [packet[:length] for length in range(25)]
        malformed += [packet + bytes(length) for length in range(1, 26)]
        malformed += [bytes((opcode,)) + packet[1:] for opcode in range(256) if opcode != 0x3b]
        self.assertEqual(self.codec(malformed), [None] * len(malformed))

    def test_every_slot_byte_against_both_native_helpers(self):
        packets = [probe(slot) for slot in range(256)]
        for packet, decoded in zip(packets, self.codec(packets)):
            with self.subTest(slot=packet[2]):
                self.compare_store(packet, decoded)

    def test_all_50_slots_cross_every_packed_dword_bit_and_boundaries(self):
        values = [0, 0xffffffff, 0xa5a5a5a5, 0x5a5a5a5a] + [1 << bit for bit in range(32)]
        packets = [probe(slot, packed=value) for slot in range(50) for value in values]
        for packet, decoded in zip(packets, self.codec(packets)):
            with self.subTest(slot=packet[2], packed=packet[17:21].hex()):
                self.compare_store(packet, decoded)

    def test_category_lookup_and_word8_boundaries_at_actual_store(self):
        headers = [0, 0xffffffff, 0x003fffff, 0x00400000, 0xffff0000]
        headers += [1 << bit for bit in range(32)]
        headers += [0xffc00000 | category << 16 | 0x1234 for category in range(64)]
        headers += [0xab140000 | key for key in (0, 1, 0x7f57, 0x7f58, 0x7fff, 0x8000, 0xfffe, 0xffff)]
        words = [0, 1, 0x7fff, 0x8000, 0xffff] + [1 << bit for bit in range(16)]
        packets = [probe(slot, header=header) for slot in (0, 49) for header in headers]
        packets += [probe(slot, header=0xffd41234, word8=word)
                    for slot in (0, 49) for word in words]
        for packet, decoded in zip(packets, self.codec(packets)):
            with self.subTest(packet=packet.hex()):
                self.compare_store(packet, decoded)

    def test_opaque_instance_basis_and_unclassified_envelope_bytes(self):
        packets = []
        for slot in (0, 49):
            for bit in range(160):
                packet = bytearray(probe(slot))
                packet[5:] = bytes(20)
                packet[5 + bit // 8] = 1 << (bit % 8)
                packets.append(bytes(packet))
        for packet, decoded in zip(packets, self.codec(packets)):
            self.compare_store(packet, decoded)
        packets = []
        for offset in (1, 3, 4):
            for value in (0, 1, 0x7f, 0x80, 0xff):
                packet = bytearray(probe(49))
                packet[offset] = value
                packets.append(bytes(packet))
        for packet, decoded in zip(packets, self.codec(packets)):
            self.compare_store(packet, decoded, use_companion=False)

    def test_widget_state_is_a_native_execution_boundary_not_codec_rejection(self):
        packets = [probe(slot) for slot in range(38, 42)]
        for packet, decoded in zip(packets, self.codec(packets)):
            self.assertIsNotNone(decoded)
            for dispatch in ('primary', 'secondary'):
                result = self.companion.packet_store(packet[2], decoded[0][5:], dispatch,
                                                     auxiliary_state=1)
                self.assertEqual(result['stop_rva'], 0x98e05)
                self.assertFalse(result['copied'])
                self.assertEqual(result['writes'], [])

    def test_image_pin_and_unchanged_code(self):
        self.assertEqual(quest.IMAGE_SHA, companion.IMAGE_SHA)
        changed = bytes((self.image[0] ^ 1,)) + self.image[1:]
        with self.assertRaises(ValueError):
            quest.qualify(changed)
        with self.assertRaises(ValueError):
            companion.bindings(changed)
        for native in (self.quest, self.companion):
            self.assertEqual(bytes(native.vm.mem_read(quest.BASE, len(self.image))), self.image)


if __name__ == '__main__':
    unittest.main()
