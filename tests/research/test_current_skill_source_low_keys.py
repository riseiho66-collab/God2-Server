"""Original low-key S2C30 lookup/copy, with explicit synthetic metadata only."""
import struct
import unittest
import json
from pathlib import Path

from tools.strike_lab.current_battle_entry import NativeRun, PACKET_PAGE, SP


class SkillSourceLowKeyTests(unittest.TestCase):
    def test_live_seed_does_not_populate_primary_hotbar(self):
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        evidence = json.loads((root/'native-player-skill-hotbar-20260921-01/run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        state = evidence['socket_skill_prerequisites']
        self.assertEqual(state['banks'][0]['first_state_word'],0x8001)
        self.assertEqual(state['selected_index'],-1)
        hotbar = state['hotbar']
        self.assertEqual((hotbar['mode'],hotbar['source_row'],hotbar['battle_action_mode']),(1,0,1))
        self.assertTrue(hotbar['source_present'])
        self.assertEqual(bytes.fromhex(hotbar['primary_records_hex']),b'\xff'*60)
        self.assertEqual(bytes.fromhex(hotbar['alternate_records_hex']),bytes(60))

    def test_live_seed_populates_owned_row_and_battle_skill_separately(self):
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        before = json.loads((root/'native-player-skill-seed-20260921-01/run.json').read_text(encoding='utf-8'))
        after = json.loads((root/'native-player-skill-seed-20260921-02/run.json').read_text(encoding='utf-8'))
        self.assertEqual(before['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        self.assertEqual(after['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        self.assertEqual(before['socket_skill_prerequisites']['banks'][0]['entry_count'],0)
        state = after['socket_skill_prerequisites']
        self.assertEqual((state['source_row_count'],state['source_current'],state['first_source_learned_count']),(1,0,1))
        self.assertEqual((state['bank_count'],state['current_bank'],state['selected_index']),(1,0,-1))
        self.assertEqual(state['banks'],[{'index':0,'entry_count':1,'raw_state':0,
                                        'first_state_word':0x8001,'first_definition_identity_hex':'0100'}])

    def test_live_god_names_match_all_current_source_rows(self):
        from tools.strike_lab.recover_combat_rules import CLIENT, SKILLS, SOURCE_HASHES, read_pinned
        from tools.strike_lab.omega_assets import decode_csvz
        from tools.strike_lab.recover_companion_growth import parse_sections, fields, decimal
        source = decode_csvz(read_pinned(CLIENT/SKILLS,SOURCE_HASHES[SKILLS]))
        rows = parse_sections(source,('GOD',))['GOD']['records']
        expected = {decimal(fields(row)[0]):fields(row)[4].hex() for row in rows}
        self.assertEqual(len(expected),34)
        root = Path(__file__).resolve().parents[2]
        evidence = json.loads((root/'artifacts/runs/native-player-god-metadata-20260921-01/run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        observed = evidence['socket_skill_prerequisites']['god_name_metadata']
        self.assertEqual(len(observed),34)
        self.assertTrue(all(row['present'] for row in observed))
        self.assertEqual({row['key']:row['name_hex'] for row in observed},expected)
        # Metadata presence does not create owned actor rows or learned skills.
        self.assertEqual(evidence['socket_skill_prerequisites']['source_row_count'],0)

    def test_all_low_keys_lookup_metadata_and_negative_keys_select_row(self):
        ui, source, catalog, metadata = 0x6800000, 0x6900000, 0x6a00000, 0x6c00000
        for key in range(1,100):
            for selected in (False,True):
                n = NativeRun()
                name = ('Fixture%02d' % key).encode('ascii')+b'\0'
                n.put(source,bytes(0x500))
                n.put(source+0xcf,b'\xff')
                n.put32(ui+0x86888,source)
                n.put32(ui+0xcff70,catalog)
                n.put32(catalog+0xb2d40+4*(2800+key),metadata)
                n.put(metadata,bytes(8)+name)
                # Handler receives body after opcode30; packet name is deliberately unrelated.
                n.put(PACKET_PAGE,bytes([(-key if selected else key)&255])+b'NOT_METADATA\0'+bytes(5))
                n.put32(SP+4,PACKET_PAGE)
                n.registers(ecx=ui)
                n.run(0xaa040,((0xaa040,0xaa1b5),(0x59a60,0x59a7e)),{0xaa1b5})
                self.assertIn(0x59a60,n.visits)
                self.assertEqual(bytes(n.vm.mem_read(source+0xd8,2)),struct.pack('<H',key))
                self.assertEqual(bytes(n.vm.mem_read(source+0xdb,len(name))),name)
                self.assertEqual(bytes(n.vm.mem_read(source+0xd4,1)),b'\x01')
                self.assertEqual(bytes(n.vm.mem_read(source+0xcf,1)),b'\0' if selected else b'\xff')
                self.assertEqual(n.get32(source+0xd0),source+0xd8 if selected else 0)


if __name__ == '__main__':
    unittest.main()
