import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from recovered_packet_pipeline import FrameParser, OpcodeDispatcher, record_packet


class PipelineTests(unittest.TestCase):
    @staticmethod
    def pet_frame(slot=42, key=28001):
        body = bytearray(72)
        body[:2] = key.to_bytes(2, 'little')
        body[2] = slot
        body[0x10:0x12] = (0x8001).to_bytes(2, 'little')
        frame = b'\x4c\x00\xfb' + body
        return frame + bytes((sum(value + 0x3c for value in frame) & 255,))

    def test_pet2_is_bounded_directional_and_not_runtime_verified(self):
        frame = self.pet_frame()
        result = OpcodeDispatcher.identify(frame, 'S2C', 'CONNECTED')
        self.assertTrue(result['known_bounds_pass'])
        self.assertEqual(result['pet2']['values']['physical_attack'], 0x8001)
        self.assertEqual(result['required_client_context'], 'WORLD')
        self.assertIsNone(result['state_consistent'])
        self.assertFalse(result['pet2']['database_promotion_eligible'])
        self.assertFalse(result['client_parser_runtime_validated'])
        self.assertNotIn('pet2', OpcodeDispatcher.identify(frame, 'C2S'))
        for malformed in (self.pet_frame(slot=41), self.pet_frame(slot=45),
                          self.pet_frame(key=0x6d60), self.pet_frame(key=0x7f58)):
            parsed = OpcodeDispatcher.identify(malformed, 'S2C')
            self.assertFalse(parsed['known_bounds_pass'])
            self.assertNotIn('pet2', parsed)
        corrupt = frame[:-1] + bytes((frame[-1] ^ 1,))
        with self.assertRaises(ValueError):
            OpcodeDispatcher.identify(corrupt, 'S2C')

    def test_pet2_capture_json_and_csv_are_connected(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            private = run / 'crypto-private'
            private.mkdir()
            (private / 'packet-0002.plain.bin').write_bytes(self.pet_frame())
            path = record_packet(run, 2, {'decoded': True, 'opcode': 0xfb},
                                 direction='S2C', socket=7, caller_rva='diagnostic')
            result = json.loads((run / path).read_text())
            self.assertEqual(result['pipeline']['pet2']['metadata_key'], 28001)
            self.assertEqual(result['pipeline']['pet2']['values']['physical_attack'], 0x8001)
            self.assertFalse(result['pipeline']['pet2']['wild_monster_values_verified'])
            self.assertIn('PET2_STATS_RECORD_CANDIDATE',
                          (private / 'protocol-core.csv').read_text())

    def test_permanent_six_byte_oracle(self):
        plain = bytes.fromhex('0600a60000d8')
        result = OpcodeDispatcher.identify(plain, 'C2S', 'SERVER_LIST_READY')
        self.assertEqual(result['opcode'], 0xa6)
        self.assertTrue(result['state_consistent'])
        self.assertFalse(result['client_parser_runtime_validated'])
        self.assertFalse(result['CRYPTO_RECOVERED'])
        self.assertFalse(OpcodeDispatcher.identify(plain, 'C2S', 'CONNECTED')['state_consistent'])

    def test_input_bounds(self):
        for data in (b'', bytes(3), bytes(259), bytes.fromhex('0700a60000d8'), bytes.fromhex('0600a60000d9')):
            with self.assertRaises(ValueError):
                FrameParser.parse(data)

    def test_unknown_state_remains_unknown(self):
        self.assertIsNone(OpcodeDispatcher.identify(bytes.fromhex('0600a60000d8'), 'C2S')['state_consistent'])

    def test_paired_evidence_to_csv_without_plaintext_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            private = run / 'crypto-private'
            private.mkdir()
            base = private / 'packet-0001'
            wire = Path(str(base) + '.wire.bin')
            plain = Path(str(base) + '.plain.bin')
            wire.write_bytes(bytes.fromhex('0600a3a3fdd5'))
            plain.write_bytes(bytes.fromhex('0600a60000d8'))
            report = {'decoded': True, 'wire_file': str(wire), 'plain_file': str(plain),
                      'wire_len': 6, 'plain_len': 6, 'plain_frame_hex': '0600a60000d8'}
            path = record_packet(run, 1, report, direction='C2S', socket=1, caller_rva='0x12506')
            result = json.loads((run / path).read_text())
            self.assertEqual(result['pipeline']['opcode'], 0xa6)
            self.assertNotIn('plain_frame_hex', result)
            self.assertTrue((private / 'protocol-core.csv').exists())


if __name__ == '__main__':
    unittest.main()
