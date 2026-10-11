"""Distinguish original skill attribute flags from server-calculated amounts."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_skill_effect_fields import NativeSkillEffectFields, BASE, FORMATS, OUTPUT


class SkillEffectFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = NativeSkillEffectFields()

    def expected(self, raw, amount):
        out = b''
        for i, fmt in enumerate(self.n.formats):
            if struct.unpack_from('<H', raw, 0x4c + i * 2)[0]:
                out = fmt % (out, amount)
        return out

    def test_all_original_definitions_execute(self):
        self.assertEqual(len(self.n.definitions), 448)
        for key, entry in self.n.definitions.items():
            with self.subTest(skill=key):
                self.assertEqual(self.n.execute(entry.raw, -37), self.expected(entry.raw, -37))
                self.assertEqual(self.n.record_reads, [(p, 2) for p in range(0x4c, 0x66, 2)])
                enabled = [i for i in range(13) if struct.unpack_from('<H', entry.raw, 0x4c + i*2)[0]]
                self.assertEqual(self.n.format_calls,
                                 [(OUTPUT, BASE + FORMATS[i], OUTPUT, (-37) & 0xffffffff) for i in enabled])

    def test_field_magnitudes_do_not_scale_amount(self):
        for index in range(13):
            for value in (1, 2, 100, 32768, 65535):
                raw = bytearray(110)
                struct.pack_into('<H', raw, 0x4c + index * 2, value)
                for amount in (-32768, -1, 0, 1, 32767):
                    with self.subTest(field=index, value=value, amount=amount):
                        self.assertEqual(self.n.execute(bytes(raw), amount), self.n.formats[index] % (b'', amount))

    def test_reject_invalid_inputs_and_no_flags(self):
        self.assertEqual(self.n.execute(bytes(110), 17), b'')
        for raw, amount in ((bytes(109), 1), (bytes(111), 1), (bytearray(110), 1),
                            (bytes(110), True), (bytes(110), 32768), (bytes(110), -32769)):
            with self.assertRaises(ValueError):
                self.n.execute(raw, amount)


if __name__ == '__main__':
    unittest.main()
