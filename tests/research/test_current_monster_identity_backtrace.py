"""Differentiate current monster identity namespaces without supplying stats."""
import csv
import io
import struct
import unittest

from tools.strike_lab import current_monster_side_initialization as monster


class CurrentMonsterIdentityBacktraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = monster.MonsterSideInitializationProbe()

    def test_packet_identity_word_does_not_select_normal_enemy_source(self):
        p = self.p
        for side in (0, 1):
            baseline = None
            for word in (0, 1, 0x1234, 0x7fff, 0xffff):
                with self.subTest(side=side, identity_word=word):
                    reset = p.reset_actor()
                    result = p.run(side, diagnostic_level=0, diagnostic_identity_word=word)
                    metadata = bytes.fromhex(result['metadata_hex'])
                    self.assertEqual(struct.unpack_from('<H', metadata)[0], word)
                    self.assertEqual(metadata[7], 0)  # Explicit unknown-level input, not recovered level.
                    self.assertEqual(result['record_pointer'], p.record)
                    self.assertEqual(result['resource_pointer'], p.resource_rows[side])
                    self.assertEqual(result['stop_rva'], 0x1206e0)
                    self.assertEqual(result['scalars_hex'], 'cd' * 16)
                    self.assertTrue(all(event['rva'] == 0x11fdfe for event in reset['scalar_writes']))
                    self.assertFalse(any(event['region'] == 'actor' for event in result['writes']))
                    identity_independent = (metadata[2:], result['record_pointer'],
                                            result['resource_pointer'], result['requested_path_hex'])
                    if baseline is None:
                        baseline = identity_independent
                    self.assertEqual(identity_independent, baseline)
                    packet_reads = {(x['rva'], x['offset'], x['size']) for x in result['reads']
                                    if x['region'] == 'packet'}
                    self.assertIn((0x115d10, 3, 2), packet_reads)
                    self.assertIn((0x115ddb, 7, 2), packet_reads)
                    self.assertIn((0x115e02, 9, 1), packet_reads)
                    self.assertIn((0x115dfa, 11, 2), packet_reads)

    def test_source_label_is_not_stored_or_used_by_this_native_row_writer(self):
        p = self.p
        original = p.enemy_record
        fields = next(csv.reader(io.StringIO(bytes.fromhex(p.row['raw_record_hex']).decode('latin1'))))
        for label in ('1', '555', '65535'):
            with self.subTest(label=label):
                changed = list(fields)
                changed[0] = label
                out = io.StringIO(newline='')
                csv.writer(out, lineterminator='\r\n').writerow(changed)
                raw = out.getvalue().encode('latin1')
                p._parse(raw, monster.MESSAGES, 10, {'diagnostic_column_0': label})
                p.vm.mem_write(p.record, bytes(26))
                p._reset()
                p.setreg('EBP', monster.MESSAGES)
                p.setreg('ESI', p.record)
                trace = p._run(0x5a2b4, {0x5a516}, ('single_enemy_row', 'field_accessors'),
                               writes=((p.record, p.record + 26),))
                self.assertEqual(bytes(p.vm.mem_read(p.record, 26)), original)
                self.assertFalse(any(x['region'] == 'enemy_parser' and
                                     0x78 <= x['offset'] < 0x78 + 380 for x in trace['reads']))
                result = p.run(1, diagnostic_identity_word=1)
                self.assertEqual(result['record_pointer'], p.record)
                self.assertEqual(result['requested_path_hex'],
                                 (monster.CWD + b'\\data2\\fight\\eny\\eny5015.rom').hex())
        # Restore the original parser source as well as the identical record bytes.
        p._load_enemy_row()

    def test_source_label_needs_its_area_and_scene_namespace(self):
        rows = [row for row in self.p.catalog['records'] if row['lookup_visible']]
        self.assertEqual(len(rows), 7791)
        self.assertTrue(all(row['source_label'] == row['ordinal'] for row in rows))
        matches = [row for row in rows if row['source_label'] == 1]
        self.assertEqual(len(matches), 96)
        self.assertEqual(len({(row['area'], row['scene']) for row in matches}), 96)
        self.assertGreater(len({row['name_bytes_hex'] for row in matches}), 1)
        self.assertEqual(len({(row['area'], row['scene'], row['ordinal']) for row in rows}), 7791)

    def test_native_lookup_uses_area_scene_ordinal_not_label_alone(self):
        p = self.p
        rows = [row for row in p.catalog['records'] if row['lookup_visible'] and
                row['source_label'] == 1][:4]
        pointers = []
        for row in rows:
            p._reset()
            p.put(monster.SP, '<4I', monster.RETURN, row['area'], row['scene'], row['ordinal'])
            p.setreg('ECX', monster.MESSAGES)
            trace = p._run(0x5a0a0, {monster.RETURN - monster.BASE}, ('enemy_lookup',))
            self.assertEqual(p.getreg('ESP'), monster.SP + 16)
            self.assertEqual(p.getreg('EAX'), p.record + 26 * row['source_record_index'])
            self.assertFalse(any(x['region'] == 'enemy_record' for x in trace['reads']))
            pointers.append(p.getreg('EAX'))
        self.assertEqual(len(set(pointers)), 4)

    def test_identity_word_bounds_and_no_boolean_coercion(self):
        for word in (-1, 65536, True, None):
            with self.subTest(word=word), self.assertRaises(ValueError):
                self.p.run(1, diagnostic_identity_word=word)


if __name__ == '__main__':
    unittest.main()
