import struct
import subprocess
import tempfile
from pathlib import Path
import unittest

from tests.research.test_current_instance_update import build_fixture, ROOT
from tools.strike_lab import current_monster_inspect_identity as native
from tools.strike_lab.current_pet2_stat_labels import audit
from tools.strike_lab.recovered_packet_pipeline import OpcodeDispatcher, pet2_fields


class Pet2StatsCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-pet2-codec-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.exe = build_fixture(Path(cls.temp.name), source=ROOT / 'tests/test_recovered_pet2_stats.cpp')
        cls.bindings = audit()['fields']

    def decode(self, packets):
        result = subprocess.run([str(self.exe)], input=''.join(p.hex() + '\n' for p in packets),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = result.stdout.splitlines()
        self.assertEqual(len(rows), len(packets))
        return [None if r == 'reject' else (bytes.fromhex(r.split()[0]), list(map(int, r.split()[1:])))
                for r in rows]

    def test_cpp_fields_match_original_receiver_and_label_bound_consumers(self):
        vm = native.NativeInspect()
        for slot in (42, 43, 44):
            for value in (0, 1, 0x7fff, 0x8000, 0xffff):
                body = bytearray(native.diagnostic_body(28001, slot))
                for index, field in enumerate(self.bindings):
                    struct.pack_into('<H', body, field['body_offset'], (value + index) & 0xffff)
                packet = b'\xfb' + body
                encoded, parsed = self.decode([packet])[0]
                self.assertEqual(encoded, packet)
                self.assertEqual(parsed[:2], [28001, slot])
                vm.receive_fb(bytes(body))
                selected = vm.select_fb(slot)
                controls = {f['arguments'][2]: f['arguments'][4]
                            for f in vm.panel_fields(selected['record_address'])}
                self.assertEqual(parsed[2:], [controls[f['control']['control']] for f in self.bindings])
                fields = pet2_fields(packet)
                self.assertEqual(list(fields['values'].values()), parsed[2:])
                frame = bytes((76, 0)) + packet
                frame += bytes((sum(value + 0x3c for value in frame) & 255,))
                identified = OpcodeDispatcher.identify(frame, 'S2C')
                self.assertEqual(identified['pet2'], fields)
                self.assertIsNone(identified['state_consistent'])

    def test_structural_bounds_and_opaque_roundtrip(self):
        packet = b'\xfb' + native.diagnostic_body()
        packets, expected = [], []
        for length in range(75):
            packets.append((packet + b'\xcc')[:length]); expected.append(length == 73)
        for slot in range(256):
            p = bytearray(packet); p[3] = slot
            packets.append(bytes(p)); expected.append(42 <= slot <= 44)
        for key in (0, 0x6d60, 0x6d61, 0x7f57, 0x7f58, 0xffff):
            p = bytearray(packet); struct.pack_into('<H', p, 1, key)
            packets.append(bytes(p)); expected.append(0x6d61 <= key < 0x7f58)
        # Unknown tail bytes must survive, not be replaced with defaults.
        for offset in range(4, 73):
            for bit in range(8):
                p = bytearray(packet); p[offset] ^= 1 << bit
                packets.append(bytes(p)); expected.append(True)
        p = bytearray(packet); p[0] = 0xfa
        packets.append(bytes(p)); expected.append(False)
        for raw, accepted, result in zip(packets, expected, self.decode(packets)):
            self.assertEqual(result is not None, accepted)
            self.assertEqual(pet2_fields(raw) is not None, accepted)
            if result:
                self.assertEqual(result[0], raw)
                self.assertEqual(result[1][2:], [struct.unpack_from('<H', raw, f['logical_offset'])[0]
                                               for f in self.bindings])

    def test_progress_mask_matches_native_panel_and_preserves_other_fields(self):
        from tools.strike_lab.current_progression_precision_20260927 import audit as progress_audit
        evidence = progress_audit()
        packets = []
        expected = []
        for probe in evidence['probes']:
            packet = bytearray(b'\xfb' + native.diagnostic_body())
            struct.pack_into('<I', packet, 9, probe['packed_body8'])
            packets.append(bytes(packet))
            expected.append(probe['raw24'])
            self.assertEqual(pet2_fields(packet)['progress_display_raw24'], probe['raw24'])
        result = subprocess.run([str(self.exe), '--progress'],
                                input=''.join(p.hex() + '\n' for p in packets),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(map(int, result.stdout.splitlines())), expected)

    def test_level_vitals_stars_match_original_panel_across_packed_boundaries(self):
        # Execute original consumers, not merely a duplicate Python bit mask.
        vm = native.NativeInspect()
        packets, native_values = [], []
        cases = (0, 1, 0x3fff, 0x4000, 0x1ffffff, 0x2000000, 0xffffffff)
        for level in range(256):
            slot = (42, 43, 44)[level % 3]
            body = bytearray(native.diagnostic_body(28001, slot))
            body[3] = level
            struct.pack_into('<I', body, 4, cases[level % len(cases)])
            struct.pack_into('<I', body, 12, cases[(level + 3) % len(cases)])
            # All 16x16 star pairs; EXP low24 must remain independent.
            struct.pack_into('<I', body, 8, (level << 24) | 0xabcdef)
            packet = b'\xfb' + body
            packets.append(packet)
            vm.receive_fb(bytes(body))
            selected = vm.select_fb(slot)
            controls = {f['ui_field']: f['arguments'][4]
                        for f in vm.panel_fields(selected['record_address'])}
            wanted = [controls[k] for k in (5, 1, 3, 2, 4, 17, 18)]
            native_values.append(wanted)
            fields = pet2_fields(packet)
            self.assertEqual([fields['level'], *fields['vitals'].values(),
                              fields['star_rank'], fields['star_rating']], wanted)
            self.assertEqual(fields['progress_display_raw24'], 0xabcdef)
        result = subprocess.run([str(self.exe), '--progression'],
                                input=''.join(p.hex() + '\n' for p in packets),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([list(map(int, row.split())) for row in result.stdout.splitlines()],
                         native_values)


if __name__ == '__main__':
    unittest.main()
