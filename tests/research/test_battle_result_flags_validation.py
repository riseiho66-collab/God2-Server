"""Independent black-box codec checks; no claim of live/native execution."""
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXECUTABLE = ROOT / 'build/tests/Release/recovered-battle-result-flags.exe'


class BattleResultFlagsValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXECUTABLE.is_file():
            raise AssertionError('Build recovered-battle-result-flags first')

    @staticmethod
    def record(position, word, flags, tail):
        return (bytes((0x86, 3, position)) + word.to_bytes(2, 'little')
                + flags.to_bytes(4, 'little') + tail)

    def batch(self, records):
        result = subprocess.run(
            [str(EXECUTABLE), '--batch'],
            input='\n'.join(record.hex() for record in records) + '\n',
            capture_output=True, text=True, check=True, timeout=30)
        self.assertEqual(result.stderr, '')
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), len(records))
        return lines

    def assert_record(self, line, record, normalized):
        encoded, *fields = line.split()
        self.assertEqual(encoded, record.hex())
        self.assertEqual(list(map(int, fields)), [
            record[2], record[2] // 14, record[2] % 14,
            int.from_bytes(record[3:5], 'little'),
            int.from_bytes(record[5:9], 'little'), normalized])

    def test_rejections_do_not_affect_neighboring_records(self):
        first = self.record(13, 0x80ff, 0xfedcba98, bytes(range(8)))
        second = self.record(14, 0xff80, 0x80000101, bytes(range(248, 256)))
        rejected = [first[:n] for n in range(17)]
        rejected += [first + bytes(n - 17) for n in (18, 35, 255, 2048)]
        rejected += [first + second, b'\x86\0\0\0\0']
        rejected += [first[:2] + bytes((p,)) + first[3:]
                     for p in (28, 127, 128, 255)]
        rejected += [bytes((op,)) + first[1:] for op in (0, 0x85, 0x87, 255)]
        rejected += [first[:1] + bytes((d,)) + first[2:]
                     for d in (0, 1, 2, 4, 255)]
        records = [record for invalid in rejected for record in (first, invalid, second)]
        lines = self.batch(records)
        for index in range(0, len(lines), 3):
            with self.subTest(invalid=records[index + 1].hex()):
                self.assert_record(lines[index], first, 0xfedcba98)
                self.assertEqual(lines[index + 1], 'reject')
                self.assert_record(lines[index + 2], second, 1)

    def test_normalization_is_idempotent_and_encoding_preserves_original(self):
        records, expected = [], []
        for position in (0, 13, 14, 27):
            for high in (0, 0x80000000, 0x12345600, 0xffffff00):
                for low in range(256):
                    flags = high | low
                    normalized = 1 if low % 2 else flags
                    tail = bytes((low, low ^ 255, 0x86, 3, position, 0, 128, 255))
                    original = self.record(position, (low << 8) | (low ^ 255), flags, tail)
                    canonical = original[:5] + normalized.to_bytes(4, 'little') + original[9:]
                    records.extend((original, canonical))
                    expected.extend((normalized, normalized))
        for index, (line, record, normalized) in enumerate(
                zip(self.batch(records), records, expected)):
            with self.subTest(index=index):
                self.assert_record(line, record, normalized)


if __name__ == '__main__':
    unittest.main()
