"""C++ S2C86 codec against unchanged native discriminator3 consumption."""
import random
import struct
import subprocess

import test_current_battle_result_fields as native


class BattleResultFlagsCodecTests(native.CurrentBattleResultFieldsTests):
    def test_formal_codec_preserves_wire_and_matches_native_normalization(self):
        executable = native.ROOT / 'build/tests/Release/recovered-battle-result-flags.exe'
        self.assertTrue(executable.is_file(), 'Build recovered-battle-result-flags first')
        vm = self.machine()
        values = [0, 1, 0x80000000, 0xfffffffe, 0xffffffff]
        values += [1 << bit for bit in range(32)] + [(1 << bit) | 1 for bit in range(32)]
        records = [self.record(position, value, (position * 2341) & 0xffff)
                   for position in range(28) for value in values]
        rng = random.Random(860319)
        for _ in range(512):
            record = bytearray(rng.randbytes(17))
            record[:3] = bytes((0x86, 3, rng.randrange(28)))
            records.append(bytes(record))
        expected = []
        for index, record in enumerate(records):
            self.compare(vm, record, self.state(local_slot=index % 14), at_end=bool(index & 1))
            flags = struct.unpack('<I', vm.mem_read(native.ENTITY + 0xdb8, 4))[0]
            word = struct.unpack('<H', vm.mem_read(native.ENTITY + 0x278, 2))[0]
            expected.append((record.hex(), record[2], record[2] // 14, record[2] % 14,
                             word, struct.unpack_from('<I', record, 5)[0], flags))
        result = subprocess.run([str(executable), '--batch'],
                                input='\n'.join(record.hex() for record in records) + '\n',
                                capture_output=True, text=True, check=True, timeout=30)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), len(expected))
        for line, wanted in zip(lines, expected):
            encoded, *fields = line.split()
            self.assertEqual((encoded, *map(int, fields)), wanted)

    def test_other_direction_and_other_discriminators_do_not_alias(self):
        executable = native.ROOT / 'build/tests/Release/recovered-battle-result-flags.exe'
        raw = self.record()
        records = [b'\x86\x00\x00\x00\x00'] + [raw[:n] for n in range(17)]
        records += [raw + b'\0', raw * 2]
        records += [raw[:1] + bytes([state]) + raw[2:] for state in (0, 1, 2, 4, 5, 6, 255)]
        result = subprocess.run([str(executable), '--batch'],
                                input='\n'.join(record.hex() for record in records) + '\n',
                                capture_output=True, text=True, check=True, timeout=30)
        self.assertEqual(result.stdout.splitlines(), ['reject'] * len(records))


if __name__ == '__main__':
    import unittest
    unittest.main()
