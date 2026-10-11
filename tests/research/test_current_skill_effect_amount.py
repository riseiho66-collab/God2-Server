"""Native effect magnitude provenance, not authoritative damage generation."""
from pathlib import Path
import struct
import sys
import unittest
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_skill_effect_amount import receive_amount, describe_slot_zero, consume_skill_amount, SOURCE


class SkillEffectAmountTests(unittest.TestCase):
    def test_cpp_skill_effect_reaches_original_opposite_side_amount_store(self):
        root=Path(__file__).resolve().parents[2]
        raw=bytes.fromhex(subprocess.check_output([
            str(root/'build/tests/Release/recovered-battle-bootstrap.exe'),
            '--diagnostic-skill-effect'],text=True,timeout=10).strip())
        self.assertEqual(raw,bytes.fromhex('830300000000000100caff0100001c'))
        n=consume_skill_amount(0,1,0xffca,target_position=14,logical_record=raw)
        for pc in (0x12c537,0x12c7d2,0x12a95f,0x12c845,0x12b619):
            self.assertIn(pc,n.visits)
        for target in (0,28,True):
            with self.assertRaises(ValueError):
                consume_skill_amount(0,1,0xffca,target_position=target,logical_record=raw)
        with self.assertRaises(ValueError):
            consume_skill_amount(0,1,0xffca,target_position=15,logical_record=raw)

    def record(self, value):
        raw = bytearray(b'\x7d' * 14)
        struct.pack_into('<H', raw, 8, value)
        return bytes(raw)

    def test_continuous_received_amount_store_all_slots_and_states(self):
        for state in (3, 23):
            for slot in range(28):
                for word in (0, 1, 32767, 32768, 65535):
                    with self.subTest(state=state, slot=slot, word=word):
                        n = receive_amount(self.record(word), slot=slot, state=state)
                        for pc in (0x12c845, 0x12c860, 0x12b060, 0x11e75a, 0x1224a0, 0x12b619):
                            self.assertIn(pc, n.visits)

    def test_same_actor_signed_amount_to_real_text_caller(self):
        for word, signed in ((0, 0), (1, 1), (32767, 32767), (32768, -32768), (65535, -1)):
            n = receive_amount(self.record(word))
            definition = bytearray(110)
            struct.pack_into('<H', definition, 0x5e, 500)
            before = bytes(n.vm.mem_read(SOURCE, 4096))
            output = describe_slot_zero(n, bytes(definition))
            self.assertEqual(output, (' \u7269\u653b ' + f'{signed:+d} ').encode('cp950'))
            after = bytes(n.vm.mem_read(SOURCE, 4096))
            self.assertEqual(before[:0xec4], after[:0xec4])
            self.assertEqual(before[0xec8:], after[0xec8:])

    def test_invalid_records_and_bounds(self):
        for raw in (bytes(13), bytes(15), bytearray(14), None):
            with self.assertRaises(ValueError):
                receive_amount(raw)
        for args in ({'slot': -1}, {'slot': 28}, {'slot': True}, {'state': 5}, {'poison': 256}):
            with self.assertRaises(ValueError):
                receive_amount(self.record(1), **args)

    def test_full_action_entry_native_state_and_selected_definition(self):
        from tools.strike_lab.current_monster_skill_assignments import NativeSkillActions
        definitions = NativeSkillActions().definitions
        for bank, skill_id in definitions:
            with self.subTest(bank=bank, skill_id=skill_id):
                n = consume_skill_amount(bank, skill_id, 0xffdb)
                for pc in (0x12c537, 0x12c7d2, 0x12a95f, 0x12c845, 0x12b619):
                    self.assertIn(pc, n.visits)
        for word in (0, 1, 32767, 32768, 65535):
            consume_skill_amount(0, 1, word)

    def test_full_entry_rejects_unqualified_identity_and_amount(self):
        for bank, skill_id, word in ((True, 1, 0), (0, True, 0), (4, 1, 0),
                                     (0, 0, 0), (0, 1, True), (0, 1, -1), (0, 1, 65536)):
            with self.assertRaises(ValueError):
                consume_skill_amount(bank, skill_id, word)


if __name__ == '__main__':
    unittest.main()
