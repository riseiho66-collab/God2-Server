import unittest
from tools.strike_lab.current_pet2_stat_labels import audit


class Pet2StatLabelTests(unittest.TestCase):
    def test_original_resource_and_thirteen_numeric_bindings(self):
        result = audit()
        self.assertEqual(result['panel']['image_index'], 69)
        self.assertEqual(result['panel']['pixels_sha256'],
                         '248c2b7ca5ec437efb2d0d9070dade162bc157f51e8d231e21adad1c078c4f21')
        self.assertEqual(len(result['fields']), 13)
        self.assertEqual([(r['name'], r['logical_offset']) for r in result['fields'][:4]],
                         [('physical_attack', 17), ('physical_defense', 19),
                          ('magical_attack', 21), ('magical_defense', 23)])
        self.assertFalse(result['wildmonsterjoin_proven'])
        self.assertEqual(result['original_wild_values_recovered'], 0)
        self.assertEqual(result['database_promotions'], 0)
        self.assertEqual(len(result['packed_fields']), 7)
        self.assertEqual([(r['name'], r['logical_offset'], r['shift'], r['mask'])
                          for r in result['packed_fields']],
                         [('current_hp', 5, 0, 0x3fff), ('current_mp', 5, 14, 0x7ff),
                          ('maximum_hp', 13, 0, 0x3fff), ('maximum_mp', 13, 14, 0x7ff),
                          ('level', 4, 0, 0xff), ('star_rank', 9, 28, 15),
                          ('star_rating', 9, 24, 15)])
        self.assertFalse(result['growth_type_mapping_verified'])
        self.assertFalse(result['level_cap_verified'])


if __name__ == '__main__':
    unittest.main()
