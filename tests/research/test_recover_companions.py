"""Evidence checks use actual Taiwan client rows and their source provenance."""
import copy
from pathlib import Path
import unittest

from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.recover_companions import (
    GAME, MESSAGES, SECTIONS, build_companions, digest, message_claims,
    parse_sections, record, serialize,
)

REPO = Path(__file__).resolve().parents[2]
CLIENT = REPO.parent / 'God2'


class CompanionRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = build_companions(CLIENT)
        cls.game = decode_csvz((CLIENT / GAME).read_bytes())
        cls.messages = decode_csvz((CLIENT / MESSAGES).read_bytes())

    def test_all_imported_bytes_match_current_sources(self):
        for section in self.artifact['sections'].values():
            for row in [section['header'], *section['records']]:
                raw = bytes.fromhex(row['raw_record_hex'])
                offset = row['decoded_offset']
                self.assertEqual(raw, self.game[offset:offset + len(raw)])
                self.assertEqual(digest(raw), row['sha256'])
                self.assertEqual([f.hex() for f in raw.rstrip(b'\r\n').split(b',')], row['fields_hex'])
                self.assertEqual(self.game[:offset].count(b'\n') + 1, row['source_line'])

    def test_current_sources_match_manifest(self):
        for relative, source in self.artifact['sources'].items():
            raw = (CLIENT / relative).read_bytes()
            self.assertEqual(digest(raw), source['sha256'])
            self.assertEqual(digest(decode_csvz(raw)), source['decoded_sha256'])

    def test_counts_are_source_declarations_not_legacy_constants(self):
        parsed = parse_sections(self.game, SECTIONS)
        for name, section in parsed.items():
            self.assertEqual(section['declared_count'], len(section['records']))
            self.assertEqual(section['records'], self.artifact['sections'][name]['records'])

    def test_transport_family_not_promoted_to_combat_pet(self):
        families = {c['section']: c['family'] for c in self.artifact['classification']}
        self.assertEqual(families, {'GOD': 'immortal', 'PET': 'pet_unqualified',
                                    'COM': 'battle_pet', 'NCP': 'battle_pet'})

    def test_message_evidence_is_exact_and_not_executable(self):
        section = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        claims = message_claims(section)
        self.assertEqual(claims, self.artifact['transition_and_restriction_evidence'])
        for claim in claims:
            self.assertFalse(claim['runtime_eligible'])
            row = claim['source']
            raw = bytes.fromhex(row['raw_record_hex'])
            self.assertEqual(raw, self.messages[row['decoded_offset']:row['decoded_offset'] + len(raw)])

    def test_message_text_drift_rejected(self):
        section = copy.deepcopy(parse_sections(self.messages, ('SystemMessage',))['SystemMessage'])
        row = next(r for r in section['records'] if r['fields_hex'][0] == b'509'.hex())
        row['fields_hex'][2] = b''.hex()
        with self.assertRaisesRegex(ValueError, 'Inconsistent message record'):
            message_claims(section)

    def test_message_record_provenance_tampering_rejected(self):
        original = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        mutations = {
            'hash': lambda row: row.update(sha256='0' * 64),
            'raw_bytes': lambda row: row.update(raw_record_hex='00'),
            'invalid_hex': lambda row: row.update(raw_record_hex='not hex'),
            'display': lambda row: row['fields_cp950_display'].__setitem__(2, ''),
            'missing_identity': lambda row: row.update(fields_hex=[]),
            'negative_offset': lambda row: row.update(decoded_offset=-1),
            'boolean_offset': lambda row: row.update(decoded_offset=True),
            'zero_line': lambda row: row.update(source_line=0),
            'missing_hash': lambda row: row.pop('sha256'),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                section = copy.deepcopy(original)
                row = next(r for r in section['records'] if r['fields_hex'][0] == b'509'.hex())
                mutate(row)
                with self.assertRaisesRegex(ValueError, 'Inconsistent message record'):
                    message_claims(section)

    def test_unsupported_progression_fields_rejected(self):
        original = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        for field in ('growth_formula', 'required_level', 'skills', 'reward', 'runtime_eligible'):
            with self.subTest(field=field):
                section = copy.deepcopy(original)
                row = next(r for r in section['records'] if r['fields_hex'][0] == b'861'.hex())
                row[field] = 'unsupported-test-marker'
                with self.assertRaisesRegex(ValueError, 'Inconsistent message record'):
                    message_claims(section)

    def test_message_identity_transplant_rejected(self):
        section = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        rows = {r['fields_hex'][0]: r for r in section['records']}
        first, second = rows[b'508'.hex()], rows[b'509'.hex()]
        first['fields_hex'], second['fields_hex'] = second['fields_hex'], first['fields_hex']
        with self.assertRaisesRegex(ValueError, 'Inconsistent message record'):
            message_claims(section)

    def test_consistent_wrong_message_text_still_rejected(self):
        section = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        index = next(i for i, r in enumerate(section['records']) if r['fields_hex'][0] == b'509'.hex())
        row = section['records'][index]
        other = next(r for r in section['records'] if r['fields_hex'][0] == b'508'.hex())
        fields = [bytes.fromhex(f) for f in row['fields_hex']]
        fields[2] = bytes.fromhex(other['fields_hex'][2])
        section['records'][index] = record(b','.join(fields) + b'\r\r\n',
                                            row['source_line'], row['decoded_offset'])
        with self.assertRaisesRegex(ValueError, 'Message text changed: 509'):
            message_claims(section)

    def test_self_consistent_invalid_raw_records_rejected(self):
        original = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        index = next(i for i, r in enumerate(original['records']) if r['fields_hex'][0] == b'509'.hex())
        row = original['records'][index]
        raw = bytes.fromhex(row['raw_record_hex'])
        for malformed in (raw + raw, raw + b'\n', raw.replace(b',', b',\0', 1), b'\r\r\n'):
            with self.subTest(raw_sha256=digest(malformed)):
                section = copy.deepcopy(original)
                section['records'][index] = record(malformed, row['source_line'], row['decoded_offset'])
                with self.assertRaisesRegex(ValueError, 'Inconsistent message record'):
                    message_claims(section)

    def test_claims_do_not_alias_caller_records(self):
        section = parse_sections(self.messages, ('SystemMessage',))['SystemMessage']
        claims = message_claims(section)
        before = serialize(claims)
        row = next(r for r in section['records'] if r['fields_hex'][0] == b'861'.hex())
        row['fields_hex'].clear()
        row['growth_formula'] = 'unsupported-test-marker'
        self.assertEqual(serialize(claims), before)

    def test_full_recovery_preserves_current_artifact_contract(self):
        result = build_companions(CLIENT)
        self.assertEqual(serialize(result), serialize(self.artifact))
        record_keys = {'source_line', 'decoded_offset', 'raw_record_hex', 'sha256',
                       'fields_hex', 'fields_cp950_display'}
        for section in result['sections'].values():
            for row in section['records']:
                self.assertEqual(set(row), record_keys)

    def test_duplicate_and_truncated_sections_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            parse_sections(self.game + b'\nGOD,34\n', ('GOD',))
        start = self.game.index(b'GOD,34')
        with self.assertRaises(ValueError):
            parse_sections(self.game[:start + 8], ('GOD',))

    def test_artifact_serialization_is_canonical(self):
        self.assertEqual(serialize(self.artifact), serialize(copy.deepcopy(self.artifact)))


if __name__ == '__main__':
    unittest.main()
