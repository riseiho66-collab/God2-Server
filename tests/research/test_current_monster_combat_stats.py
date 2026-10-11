"""Current-source coverage and native counterfactuals; no gameplay fixtures as facts."""
import struct
import unittest

from tools.strike_lab import current_monster_combat_stats as m
from tools.strike_lab.current_monster_inventory import pinned_catalog


class CurrentMonsterCombatStatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = m.pinned(m.IMAGE, m.IMAGE_SHA)
        cls.rows = m.source_rows(m.CARD)
        cls.report = m.evidence()

    def native(self):
        return m.NativeCard(self.image)

    @staticmethod
    def mutate(raw, changes):
        fields = raw.rstrip(b'\r\n').split(b',')
        for column, value in changes.items():
            fields[column] = str(value).encode('ascii')
        return b','.join(fields) + b'\r\n'

    def test_all_source_occurrences_match_main_without_name_merging(self):
        original = pinned_catalog()['records']
        records = self.report['records']
        self.assertEqual(len(records), len(original))
        self.assertEqual(self.report['coverage']['allocated_records'], 7815)
        self.assertEqual(self.report['coverage']['lookup_visible_records'], 7791)
        self.assertEqual(self.report['coverage']['lookup_visible_groups'], 96)
        self.assertEqual(self.report['coverage']['allocated_groups'], 97)
        self.assertEqual(self.report['coverage']['superseded_records'], 24)
        for actual, source in zip(records, original):
            for key in actual['identity']:
                self.assertEqual(actual['identity'][key], source[key])
            self.assertEqual(actual['lookup_visible'], source['lookup_visible'])
            self.assertEqual(actual['source_fields_hex'], source['fields_hex'])
            self.assertEqual(actual['source']['decoded_offset'], source['source_offset'])
            self.assertEqual(actual['source']['row_sha256_including_line_ending'], source['record_sha256'])
            self.assertEqual(set(actual['fields']), set(m.FIELDS))
            self.assertTrue(all(f['value'] is None and f['authority'] == 'unresolved'
                                for f in actual['fields'].values()))
            self.assertIsNone(actual['monster_classification'])
        superseded = [r for r in records if not r['lookup_visible']]
        self.assertEqual({r['identity']['area'] for r in superseded}, {7})
        self.assertFalse(self.report['coverage']['all_monster_systems_enumerated'])
        self.assertIsNone(self.report['coverage']['verified_wild_monster_count'])
        self.assertIn('boss', self.report['requested_scope'])
        self.assertFalse(self.report['runtime_eligible'])

    def test_every_current_card_numeric_column_and_native_join(self):
        cards = self.report['cards']
        self.assertEqual([c['card_index'] for c in cards], list(range(101)))
        self.assertEqual(self.report['header']['allocation_arguments'], [102, 48])
        expected_columns = list(range(6)) + list(range(8, 23))
        lookup = {tuple(r['identity'][k] for k in ('area', 'scene', 'ordinal')): r
                  for r in self.report['records'] if r['lookup_visible']}
        for card, row in zip(cards, self.rows[5:]):
            self.assertEqual(card['native_loader']['columns_read'], expected_columns)
            self.assertTrue(card['native_consumer']['lookup_executed'])
            formats = {f['field']: f for f in card['native_consumer']['formats']}
            for name, (column, offset, writer, _) in m.FIELDS.items():
                field = card['fields'][name]
                value = int(row['fields'][column])
                self.assertEqual(field['value'], value)
                self.assertIsNone(field['wild_monster_value'])
                self.assertEqual(field['authority'], 'card_record_signed_display_value_only')
                self.assertEqual(field['source']['row_sha256'], m.sha(row['raw'].rstrip(b'\r\n')))
                relative = field['decoded_field_offset'] - row['offset']
                self.assertTrue(row['raw'][relative:].startswith(str(value).encode() + b','))
                self.assertIn({'rva': hex(writer), 'record_offset': offset,
                               'width': 2, 'bits': value & 65535}, card['native_loader']['writes'])
                if value:
                    self.assertEqual(formats[name]['value'], value)
                    self.assertEqual(formats[name]['color_argument'], 3 if value >= 0 else 1)
                else:
                    self.assertNotIn(name, formats)
            join = card['native_participant_join']['join']
            if card['card_index'] == 0:
                self.assertIsNone(join)
                self.assertIsNone(card['joined_enemy_identity'])
            else:
                self.assertEqual(list(join.values()), list(map(int, row['fields'][3:6])))
                target = lookup[tuple(join.values())]
                self.assertEqual(card['joined_enemy_identity'], target['identity'])
                self.assertIn(card['card_index'], target['card_reference_ids'])
        self.assertEqual(self.report['coverage']['card_records_joined'], 100)
        # Card-source zeros cannot become wild-monster elemental zeros.
        self.assertTrue(all(c['fields'][f]['value'] == 0 for c in cards
                            for f in ('metal', 'wood', 'water', 'fire', 'earth')))

    def test_counterfactual_columns_signed_width_and_independence(self):
        native = self.native()
        raw = self.rows[11]['raw']  # Source card 6 has +10 attack and -5 defense.
        baseline = native.load(raw)
        self.assertEqual(baseline['index'], 6)
        baseline_record = bytes.fromhex(baseline['record_hex'])
        before_image = bytes(native.vm.mem_read(m.BASE, len(self.image)))
        for name, (column, offset, writer, _) in m.FIELDS.items():
            for supplied in (-32768, -1, 0, 32767, 65535):
                with self.subTest(field=name, supplied=supplied):
                    loaded = native.load(self.mutate(raw, {column: supplied}))
                    expected = struct.unpack('<h', struct.pack('<H', supplied & 65535))[0]
                    self.assertEqual(loaded['values'][name], expected)
                    packed = bytearray(baseline_record)
                    struct.pack_into('<H', packed, offset, supplied & 65535)
                    self.assertEqual(bytes.fromhex(loaded['record_hex']), packed)
                    self.assertIn({'rva': hex(writer), 'record_offset': offset,
                                   'width': 2, 'bits': supplied & 65535}, loaded['writes'])
                    consumed = native.consume(6)
                    formats = {v['field']: v for v in consumed['formats']}
                    if expected:
                        self.assertEqual(formats[name]['value'], expected)
                        self.assertEqual(formats[name]['color_argument'], 3 if expected > 0 else 1)
                        self.assertIn(str(expected).encode(), bytes.fromhex(consumed['text_hex']))
                    else:
                        self.assertNotIn(name, formats)
        self.assertEqual(bytes(native.vm.mem_read(m.BASE, len(self.image))), before_image)

    def test_unused_monster_label_columns_do_not_produce_card_stats(self):
        native = self.native()
        raw = self.rows[11]['raw']
        baseline = native.load(raw)
        changed = native.load(self.mutate(raw, {6: 9999, 7: 12345, 23: 777, 38: 999}))
        self.assertEqual(changed['record_hex'], baseline['record_hex'])
        self.assertNotIn(6, changed['columns_read'])
        self.assertNotIn(7, changed['columns_read'])

    def test_native_selector_and_participant_kind_counterfactuals(self):
        native = self.native()
        native.load(self.rows[11]['raw'])
        for selector in (0x188d, 0x188e, 0x1891):
            result = native.consume(6, selector)
            self.assertEqual(result['stop_rva'], '0xbb572')
            self.assertTrue(result['lookup_executed'])
        for selector in (0, 1, 0x188c, 0x188f, 0xffff):
            result = native.consume(6, selector)
            self.assertEqual(result['stop_rva'], '0xbbbce')
            self.assertFalse(result['lookup_executed'])
            self.assertEqual(result['formats'], [])
        for kind, stop in ((0, '0x11890b'), (1, '0x117874'), (2, '0x118a79'), (255, '0x118a79')):
            result = native.participant_join(6, kind)
            self.assertEqual(result['stop_rva'], stop)
            self.assertEqual(result['card_lookup_executed'], kind == 1)
            self.assertIsNone(result['wild_actor_type_authority'])
        expected = native.participant_join(6)['join']
        self.assertEqual(expected, {'area': 13, 'scene': 0, 'ordinal': 6})
        native.load(self.mutate(self.rows[11]['raw'], {3: 7, 4: 13, 5: 2, 10: 999}))
        self.assertEqual(native.participant_join(6)['join'], {'area': 7, 'scene': 13, 'ordinal': 2})

    def test_fail_closed_inputs_and_slice_hashes(self):
        with self.assertRaises(ValueError):
            m.NativeCard(self.image[:-1])
        native = self.native()
        for raw in (b'x\n', self.rows[11]['raw'].rstrip(), b'\0' + self.rows[11]['raw']):
            with self.assertRaises(ValueError):
                native.load(raw)
        for index in (True, -1, 101, 6):
            with self.assertRaises(ValueError):
                native.consume(index)
        for name, (lo, hi) in m.SLICES.items():
            self.assertEqual(self.report['slices'][name]['sha256'], m.sha(self.image[lo:hi]))
        with self.assertRaises(AssertionError):
            native.run(0x51a90, m.RETURN)


if __name__ == '__main__':
    unittest.main()
