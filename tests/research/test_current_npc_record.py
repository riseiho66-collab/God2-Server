"""Standalone bounded native/C++ differential tests for logical opcode 0x72.

Run from the server root: python -B tests/research/test_current_npc_record.py -v
Only the pinned native image is evidence. Build products live in a private temp
directory. No existing NPC fixtures, catalog rows, or gameplay policy are used.
"""
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_npc_record as npc


def build_fixture(directory):
    source = ROOT / 'tests/test_recovered_npc_record.cpp'
    executable = directory / ('npc-record.exe' if os.name == 'nt' else 'npc-record')
    compiler = next((shutil.which(n) for n in ('cl', 'clang++', 'g++', 'c++')
                     if shutil.which(n)), None)
    environment = None
    if not compiler and os.name == 'nt':
        vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / (
            'Microsoft Visual Studio/Installer/vswhere.exe')
        installation = subprocess.check_output([
            str(vswhere), '-latest', '-products', '*', '-requires',
            'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property',
            'installationPath'], text=True, timeout=30).strip()
        if not installation:
            raise RuntimeError('C++20 compiler required; no skipped verification')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(
            f'cmd.exe /d /s /c ""{vcvars}" >nul && set"', text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(value for key, value in environment.items() if key.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('C++20 compiler required; no skipped verification')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'npc-record.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


def fixture(selector=0, position=0):
    # Arbitrary byte pattern deliberately has no template or placement meaning.
    result = bytearray([0x72] + [(i * 37 + 19) & 255 for i in range(20)])
    struct.pack_into('<I', result, 1, selector)
    struct.pack_into('<I', result, 17, position)
    return bytes(result)


class CurrentNpcRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = npc.qualified_image()
        cls.native = npc.NativeNpcRecord(cls.image)
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-current-npc-record-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def cpp(self, lines, edit=False):
        output = subprocess.run(
            [str(self.executable), '--edit-lines' if edit else '--decode-lines'],
            input='\n'.join(lines) + '\n', text=True, capture_output=True,
            timeout=30, check=True).stdout.splitlines()
        self.assertEqual(len(output), len(lines))
        return [None if line == 'reject' else
                (*map(int, line.split()[:6]), bytes.fromhex(line.split()[6]))
                for line in output]

    def test_pinned_bindings_and_native_receive_length(self):
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            npc.bindings(self.image[:-1])
        self.assertEqual(self.native.logical_length(), 21)
        for buffered in range(23):
            result = self.native.receive_length(buffered)
            self.assertEqual((result['length'], result['opcode_count']), (21, 1))
            self.assertEqual(result['needs_byte'], buffered < 21)
            self.assertIsNone(result['guard']['fault'])

    def test_cpp_ownership_exact_envelope_and_transactional_width_checks(self):
        result = subprocess.run([str(self.executable)], text=True, capture_output=True,
                                timeout=10, check=True)
        self.assertEqual(result.stdout.strip(), 'NPC record C++20 checks passed')
        valid = fixture(0xffffffff, 0xffffffff)
        messages = [valid[:n] for n in range(22)] + [valid + b'\xff']
        # n=21 is the sole exact envelope; n=0 uses the CLI's empty-input token.
        decoded = self.cpp([b.hex() or '-' for b in messages])
        self.assertEqual([i for i, record in enumerate(decoded) if record is not None], [21])

    def test_native_receive_assembly_and_unconsumed_next_byte(self):
        source = fixture(0xfedcba98, 0xabcdef01) + b'\x81'
        for size in range(23):
            with self.subTest(available=size):
                result = self.native.receive_record(source[:size])
                self.assertIsNone(result['fault'])
                self.assertEqual(result['complete'], size >= 21)
                self.assertEqual(result['count'], min(size, 21))
                self.assertEqual(result['consumed'], min(size, 21))
                self.assertEqual(bytes.fromhex(result['buffer_hex']), source[:min(size, 21)])
                self.assertEqual(self.native.reg('ESP'), self.native.SP)
                if size < 21:
                    self.assertEqual(self.native.reg('EAX'), 1)  # Original byte-reader empty result.

    def test_native_guard_page_truncations(self):
        valid = fixture(0, 0xffffffff)
        for size in range(21):
            message = valid[:size]
            with self.subTest(size=size):
                result = self.native.selectors(message, 32767)
                if size < 5:
                    self.assertIsNotNone(result['fault'])
                    self.assertEqual(result['fault']['rva'],
                                     0x68b50 if size == 0 else
                                     0x6a691 if size < 3 else 0x6a6c6)
                else:
                    self.assertIsNone(result['fault'])
                    result = self.native.position(message)
                    self.assertIsNotNone(result['fault'])
                    self.assertEqual(result['fault']['rva'],
                                     0xcc635 if size < 10 else 0xcc676)
        for existing in (False, True):
            result = self.native.position(valid, existing)
            self.assertIsNone(result['fault'])
            reads = [(pc, address - self.native.message, size)
                     for pc, write, address, size in result['events']
                     if not write and self.native.message <= address < self.native.message + 21]
            self.assertIn((0xcc41a if existing else 0xcc676, 17, 4), reads)
            self.assertEqual(max(offset + size for _, offset, size in reads), 21)
        # These slices do not validate packet length. Exact-length rejection is
        # the codec's explicit single-record boundary, not a claimed native fault.
        self.assertEqual(self.native.position(valid + b'\x81')['x'], 32767)

    def test_native_selector_signed_count_and_unsigned_halves(self):
        values = (0, 1, 2, 32766, 32767, 32768, 65534, 65535)
        messages = []
        for maximum in (-32768, -1, 0, 1, 2, 32766, 32767):
            for primary in values:
                for secondary in values:
                    message = fixture((secondary << 16) | primary)
                    messages.append(message)
                    result = self.native.selectors(message, maximum)
                    self.assertIsNone(result['fault'])
                    primary_pointer = (self.native.RESOURCE + 0x121ea + 94 * primary
                                       if primary <= maximum else 0)
                    selected = secondary if 0 < secondary <= maximum else primary
                    valid = selected <= maximum
                    self.assertEqual(result['primary_pointer'], primary_pointer)
                    self.assertEqual(result['selected'], valid)
                    if valid:
                        self.assertEqual(result['selected_pointer'],
                                         self.native.RESOURCE + 0x121ea + 94 * selected)
                    # Out-of-range low half can coexist with an accepted high half.
                    # A codec must not reject raw fields based on catalog state.
                    self.assertEqual(result['stop_rva'], 0x6a72f if valid else 0x6b517)
        decoded = self.cpp([message.hex() for message in messages])
        for message, record in zip(messages, decoded):
            self.assertIsNotNone(record)
            raw, = struct.unpack_from('<I', message, 1)
            self.assertEqual(record[:3], (raw, raw & 65535, raw >> 16))
            self.assertEqual(record[-1], message)

    def test_native_differential_position_boundaries_and_bits(self):
        values = (0, 1, 2, 255, 256, 16383, 16384, 32766, 32767)
        packed = [low | (x << 2) | (y << 17)
                  for x in values for y in values for low in range(4)]
        packed += [1 << bit for bit in range(32)]
        packed += [0xffffffff ^ (1 << bit) for bit in range(32)]
        rng = random.Random(0x720919)
        packed += [rng.getrandbits(32) for _ in range(256)]
        messages = [fixture(rng.getrandbits(32), value) for value in packed]
        decoded = self.cpp([message.hex() for message in messages])
        for message, record in zip(messages, decoded):
            fresh = self.native.position(message)
            existing = self.native.position(message, True)
            self.assertIsNone(fresh['fault'])
            self.assertIsNone(existing['fault'])
            self.assertEqual(record[3:5], (fresh['x'], fresh['y']))
            self.assertEqual(record[3:5], (existing['x'], existing['y']))
            self.assertEqual(record[3:5], existing['duplicate_position'])
            self.assertEqual(record[1], fresh['primary_selector'])
            self.assertEqual(record[5], message[17] & 3)
            self.assertEqual(record[-1], message)
            for was_existing in (False, True):
                alternate = self.native.position(message, existing=was_existing, alternate=True)
                self.assertIsNone(alternate['fault'])
                self.assertEqual(record[3:5], (alternate['x'], alternate['y']))
                if was_existing:
                    self.assertEqual(record[3:5], alternate['duplicate_position'])

    def test_every_nonopcode_byte_value_roundtrips(self):
        original = fixture(0x89abcdef, 0xfedcba98)
        messages = []
        for offset in range(1, 21):
            for value in range(256):
                message = bytearray(original)
                message[offset] = value
                messages.append(bytes(message))
        decoded = self.cpp([message.hex() for message in messages])
        self.assertEqual([record[-1] for record in decoded], messages)

    def test_opaque_bytes_do_not_change_native_coordinates(self):
        original = fixture(0x9876abcd, 0x9234567b)
        for offset in range(5, 17):
            for value in (0, 1, 31, 32, 127, 128, 224, 255):
                message = bytearray(original)
                message[offset] = value
                result = self.native.position(bytes(message))
                self.assertIsNone(result['fault'])
                self.assertEqual((result['x'], result['y']),
                                 ((0x9234567b >> 2) & 32767, 0x9234567b >> 17))
                self.assertEqual(result['direction_slice'], message[9] >> 5)

    def test_cpp_edits_against_native_preserve_opaque_bytes(self):
        lines, expected = [], []
        rng = random.Random(0x7215)
        values = (0, 1, 16383, 16384, 32766, 32767)
        for low in range(4):
            for x in values:
                for y in values:
                    source = bytearray(rng.randbytes(21))
                    source[0] = 0x72
                    source[17] = (source[17] & 0xfc) | low
                    selector = rng.getrandbits(32)
                    lines.append(f'{source.hex()} {selector} {x} {y}')
                    struct.pack_into('<I', source, 1, selector)
                    struct.pack_into('<I', source, 17, (y << 17) | (x << 2) | low)
                    expected.append(bytes(source))
        decoded = self.cpp(lines, edit=True)
        for record, expected_message in zip(decoded, expected):
            self.assertEqual(record[-1], expected_message)
            result = self.native.position(record[-1])
            self.assertIsNone(result['fault'])
            self.assertEqual(record[3:5], (result['x'], result['y']))
        bad = [(1 << 32, 0, 0), (0, 32768, 0), (0, 0, 32768),
               (0, (1 << 64) - 1, 0), ((1 << 64) - 1, 0, 0)]
        self.assertEqual(self.cpp([f'{fixture().hex()} {s} {x} {y}' for s, x, y in bad],
                                  edit=True), [None] * len(bad))


if __name__ == '__main__':
    unittest.main()
