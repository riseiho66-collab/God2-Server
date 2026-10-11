"""Concrete original inventory-state/caller dependency, not parser fuzzing."""
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_item_transition import (
    NativeItemTransition, UI, SLOTS, IMAGE_SHA)
from tools.strike_lab.recover_items import build_items
import test_current_inventory as inventory


class CurrentItemTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT / 'artifacts/item-transition'
        directory.mkdir(parents=True, exist_ok=True)
        cls.executable = inventory.build_fixture(directory)

    def update(self, native, item, slot, count):
        # Existing production encoder -> original decrypt/checksum -> full
        # original S2C41 dispatch. No new packet or server policy implementation.
        wire = bytes.fromhex(subprocess.check_output(
            [str(self.executable), '--updates', str(item), str(slot), str(count)],
            text=True, timeout=5).strip())
        transport = inventory.CurrentInventoryTests()
        transport.image = native.image
        plain = transport.decode(transport.vm(), wire)
        self.assertEqual(plain[2:-1], struct.pack('<BHBB', 0x41, item, slot, count))
        native.consume(plain[2:-1])
        self.assertIn(0x991e0, native.visits)
        self.assertIn(0x9b850, native.visits)

    def check_request(self, native, argument, expected_slot, *, item=5301,
                      tail=0xa5, by_slot=True, via_action=False):
        incoming_edx = 0x19ab1234 if via_action else (tail << 24) | 0xee1234
        record = native.request(argument, by_slot=by_slot, via_action=via_action,
                                incoming_edx=incoming_edx)
        self.assertEqual(record, struct.pack('<BHBB', 0x25, item, expected_slot, tail))
        self.assertIn(0x963c0, native.visits)
        self.assertIn(0x59a60, native.visits)
        self.assertIn(0x96350, native.visits)
        self.assertIn(0x132e0, native.visits)
        args = dict(native.arguments)[0x96350]
        self.assertEqual(args[1:], (expected_slot, 1))
        self.assertEqual(args[0] & 0xffff, item)
        decoded = subprocess.check_output([str(self.executable), '--decode-item-request',
                                           record.hex()], text=True, timeout=5)
        self.assertEqual(tuple(map(int, decoded.split())), (item, expected_slot, tail))

    def test_current_image_and_real_source_rows(self):
        native = NativeItemTransition()
        self.assertEqual(hashlib.sha256(native.image).hexdigest(), IMAGE_SHA)
        self.assertEqual(struct.unpack_from('<I', native.image, 0x6b5d4 + 0x41 * 4)[0],
                         0x46a04d)
        current = build_items(ROOT.parent / 'God2')
        self.assertEqual(current['source']['sha256'],
                         '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731')
        for item in (5301, 5501):
            rows = [row for row in current['records'] if row['client_item_id'] == item]
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]['runtime_eligible'])

    def test_original_result_retargets_next_request_without_consuming(self):
        native = NativeItemTransition()
        for slot in (3, 29, 30, 49):
            self.update(native, 5301, slot, 7)
        self.check_request(native, 3, 29)
        self.check_request(native, 3, 29)
        self.update(native, 5301, 29, 127)
        self.check_request(native, 3, 29)
        self.update(native, 5301, 29, 128)
        self.check_request(native, 3, 3)
        self.update(native, 5501, 29, 1)
        self.check_request(native, 3, 3)
        self.check_request(native, 29, 29, item=5501)
        self.update(native, 5301, 3, 0)
        self.assertEqual(native.request(5301, by_slot=False), b'')
        self.assertIn(0x59a60, native.visits)
        self.assertNotIn(0x96350, native.visits)
        self.assertEqual(bytes(native.vm.mem_read(SLOTS + 49 * 24, 1)), b'\x07')

    def test_all_thirty_slots_resolve_by_identity_not_input_slot(self):
        native = NativeItemTransition()
        for slot in range(30):
            native.consume(struct.pack('<BHBB', 0x41, 5301, slot, 1 + slot))
        for slot in range(30):
            self.check_request(native, slot, 29)
        # Clearing the top duplicate makes the next request choose its predecessor.
        for slot in range(29, 0, -1):
            native.consume(struct.pack('<BHBB', 0x41, 5301, slot, 0))
            self.check_request(native, 0, slot - 1)

    def test_signed_occupancy_and_low_word_identity_are_caller_predicates(self):
        native = NativeItemTransition()
        native.seed_slot(0, 5501, 1)
        for raw_count in (0, 1, 127, 128, 255):
            # Deliberately bypass S2C41 normalization to isolate the caller's
            # signed predicate on preexisting slot memory.
            native.seed_slot(29, 5501, raw_count)
            native.seed_slot(49, 5501, 127)
            self.check_request(native, 0, 29 if 0 < raw_count < 128 else 0, item=5501)
        native.seed_slot(29, 5301, 127)
        self.check_request(native, 0, 0, item=5501)
        native.seed_slot(0, 5501, 0)
        self.assertEqual(native.request(5501, by_slot=False), b'')

    def test_slot_entry_tail_comes_from_incoming_edx_not_count_or_third_argument(self):
        native = NativeItemTransition()
        native.seed_slot(3, 5301, 19)
        native.seed_slot(29, 5301, 47)
        for tail in (0, 1, 0x7f, 0xa5, 0xff):
            self.check_request(native, 0xdead0003, 29, tail=tail)
            self.assertEqual(dict(native.arguments)[0x963c0],
                             ((tail << 24) | 0xee0000 | 5301,))

    def test_original_action_record_resolves_id_then_tracks_slot_clear(self):
        native = NativeItemTransition()
        for slot in (3, 29, 49):
            native.consume(struct.pack('<BHBB', 0x41, 5301, slot, 7))
        # AE520 mode zero, record kind zero: six original input bytes. The
        # trailing word remains raw; its high byte survives in C2S25's tail.
        for tail in (0, 0xa5, 0xff):
            native.vm.mem_write(UI + 0xa3d18 + 6 * 4,
                                struct.pack('<HHH', 0, 5301, (tail << 8) | 0xee))
            self.check_request(native, 4, 29, tail=tail, via_action=True)
            self.assertIn(0xae520, native.visits)
            self.assertIn(0xae5cd, native.visits)
            self.assertEqual(dict(native.arguments)[0x963c0],
                             ((tail << 24) | 0xee0000 | 5301,))
        native.consume(struct.pack('<BHBB', 0x41, 5301, 29, 0))
        self.check_request(native, 4, 3, tail=0xff, via_action=True)
        native.consume(struct.pack('<BHBB', 0x41, 5301, 3, 0))
        self.assertEqual(native.request(4, via_action=True), b'')
        self.assertIn(0xae5cd, native.visits)
        self.assertNotIn(0x96350, native.visits)

    def test_caller_gate_slot_bounds_and_zero_identity(self):
        native = NativeItemTransition()
        native.seed_slot(29, 5301, 1)
        for slot in (30, 49, 50, 127, 128, 255):
            self.assertEqual(native.request(slot), b'')
            self.assertEqual(native.visits, [0x96390])
        self.assertEqual(native.request(0), b'')
        self.assertIn(0x963c0, native.visits)
        self.assertNotIn(0x59a60, native.visits)
        for gate in (1, 0x80000000, 0xffffffff):
            self.assertEqual(native.request(29, gate=gate), b'')
            self.assertEqual(native.visits, [0x96390])
            self.assertEqual(native.request(5301, by_slot=False, gate=gate), b'')
            self.assertEqual(native.visits, [0x963c0])
        self.check_request(native, 29, 29)


if __name__ == '__main__':
    unittest.main()
