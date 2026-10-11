import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'artifacts/runs/ui-gate-real-04'
GOLDEN = ROOT / 'artifacts/golden/server-select'
SHA256 = 'bd1d63babf8850007f21a4130adc00749e9171f769b7edfc38822115b7146fae'


class PostServerSelectGoldenTests(unittest.TestCase):
    def setUp(self):
        self.metadata = json.loads((GOLDEN / 'C2S_0001.json').read_text())

    def test_unchanged_capture_and_raw_hash(self):
        raw = (GOLDEN / 'C2S_0001.bin').read_bytes()
        self.assertEqual(raw, (RUN / 'C2S_SERVER_SELECT_0001.bin').read_bytes())
        self.assertEqual(raw.hex(), '0600a3a3fdd5')
        self.assertEqual(len(raw), 6)
        self.assertEqual(self.metadata['length'], len(raw))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SHA256)
        self.assertEqual(self.metadata['sha256'], SHA256)

    def test_capture_metadata_preserved_without_interpretation(self):
        self.assertEqual(
            (GOLDEN / 'C2S_0001.json').read_bytes(),
            (RUN / 'C2S_SERVER_SELECT_0001.json').read_bytes(),
        )
        self.assertEqual(self.metadata['run_id'], RUN.name)
        # The unchanged capture metadata names its original source artifact.
        self.assertEqual(self.metadata['file'], 'C2S_SERVER_SELECT_0001.bin')
        self.assertEqual(self.metadata['caller_rva'], '0x12506')
        self.assertEqual(self.metadata['caller_address_kind'], 'send return address')
        self.assertIsNone(self.metadata['opcode'])
        self.assertIsNone(self.metadata['state_after'])
        self.assertEqual(
            self.metadata['semantic_contract'],
            'UNKNOWN; no opcode or field interpretation performed',
        )

    def test_recorded_evidence_order_and_send_identity(self):
        ui_events = json.loads((RUN / 'ui-path-events.json').read_text())
        network_events = [
            json.loads(line)
            for line in (RUN / 'network-events.jsonl').read_text().splitlines()
            if line.strip()
        ]

        def unique_event(events, sequence):
            matches = [event for event in events if event.get('sequence') == sequence]
            self.assertEqual(len(matches), 1)
            return matches[0]

        ui = unique_event(ui_events, self.metadata['ui_path_sequence'])
        entry = unique_event(network_events, self.metadata['send_entry_sequence'])
        returned = unique_event(network_events, self.metadata['send_return_sequence'])
        self.assertEqual([ui['sequence'], entry['sequence'], returned['sequence']],
                         [145, 146, 147])
        self.assertLess(ui['timestamp'], entry['timestamp'])
        self.assertLess(entry['timestamp'], returned['timestamp'])
        self.assertEqual(ui['event_type'], 'UI_PATH_A_HIT')
        self.assertEqual(ui['pc'] - 0x400000, int(self.metadata['ui_path_rva'], 16))
        self.assertEqual(entry['event_type'], 'API_ENTRY')
        self.assertEqual(returned['event_type'], 'API_RETURN')
        for event in (ui, entry, returned):
            self.assertEqual(event['run_id'], self.metadata['run_id'])
            self.assertEqual(event['pid'], self.metadata['pid'])
            self.assertEqual(event['tid'], ui['tid'])
        for event in (entry, returned):
            self.assertEqual(event['api'], 'send')
            self.assertEqual(event['caller_rva'], self.metadata['caller_rva'])
            self.assertEqual(event['return_address'], 0x412506)
            self.assertEqual(event['arguments']['a2'], self.metadata['length'])
        self.assertTrue(returned['matched'])
        self.assertEqual(returned['entry'], entry['sequence'])
        self.assertEqual(returned['arguments'], entry['arguments'])
        self.assertEqual(returned['eax'], 6)
        self.assertEqual(returned['eax'], self.metadata['send_return_bytes'])
        self.assertEqual(returned['timestamp'], self.metadata['timestamp'])
        self.assertEqual(returned['accepted_buffer'], self.metadata['file'])
        attempt = RUN / Path(entry['buffer_file'].replace('\\', '/'))
        self.assertEqual(attempt.read_bytes(), (GOLDEN / 'C2S_0001.bin').read_bytes())


if __name__ == '__main__':
    unittest.main()
