"""D6 current-client bytes and current-file identity; no revert effect claim."""
import csv
import hashlib
from pathlib import Path
import unittest

from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.current_stat_packet_return_path import run_action, pinned_image

ROOT = Path(__file__).resolve().parents[2]
RAW_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'


class Pet2RevertContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = pinned_image()

    def test_native_request_boundaries(self):
        for item_slot in (0, 7, 29):
            for pet_slot in (42, 43, 44):
                for control, option in ((0x17, 4), (0x18, 1), (0x19, 2), (0x1a, 3)):
                    result = run_action(item_slot=item_slot, pet_slot=pet_slot,
                                        control=control, image=self.image)
                    self.assertTrue(result['returned'])
                    self.assertEqual(result['appended_hex'], bytes((0xd6, item_slot, pet_slot, option)).hex())
                    self.assertEqual(result['queue_count_after'], 4)
                    self.assertTrue(result['records_unchanged'])

    def test_unmatched_source_is_an_invalid_raw_slot(self):
        for control in range(0x17, 0x1b):
            option = 4 if control == 0x17 else control - 0x17
            for flags in (0x20, 0x60):
                result = run_action(item_slot=None, control=control,
                                    event_flags=flags, image=self.image)
                self.assertEqual(result['appended_hex'], bytes((0xd6, flags, 43, option)).hex())
                self.assertNotIn(0xa5770, result['visits'])
                self.assertNotIn(0xa57ba, result['visits'])

    def test_current_file_identifies_revert_stones(self):
        raw = (ROOT.parent / 'God2/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), RAW_SHA)
        plain = decode_csvz(raw)
        self.assertEqual(hashlib.sha256(plain).hexdigest(), PLAIN_SHA)
        lines = plain.splitlines()
        begin = lines.index(b'MIS02,2226')
        selected = [row.decode('cp950') for row in lines[begin + 1:begin + 1 + 2226]
                    if row.split(b',', 1)[0] in (b'16399', b'16400')]
        rows = list(csv.reader(selected))
        keys = {int(row[0]): row for row in rows}
        self.assertEqual(keys[0x400f][4], '戰寵天賦還原石')
        self.assertEqual(keys[0x4010][4], '戰寵型態還原石')
        self.assertEqual(keys[0x400f][7:9], ['還原上一個變動的戰寵天賦', '還原成變動前的天賦'])
        self.assertEqual(keys[0x4010][7:9], ['還原上一個變動的戰寵型態', '還原成變動前的型態'])


if __name__ == '__main__':
    unittest.main()
