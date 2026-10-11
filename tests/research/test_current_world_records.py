"""Pinned native C2S85 queue -> formal C++ typed decoder, never quest authority."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_quest_action as native
from tools.strike_lab import current_quest_close as close
from tools.strike_lab.current_item_metadata import NativeItemMetadata
from tools.strike_lab import recover_companion_growth as growth
import test_current_supply_request_branch as supply_branch


class CurrentWorldRecordsTests(unittest.TestCase):
    def test_current_catalog_selection_requests_reach_formal_cpp_decoder(self):
        executable = ROOT / 'build/tests/Release/recovered-world-records.exe'
        self.assertTrue(executable.is_file(), 'Build the formal codec target first')
        metadata = NativeItemMetadata()
        producer = supply_branch.SupplyRequestBranchTests()
        expected_counts = {
            'EGG': (27, 27), 'SPP': (28, 28), 'MIS': (0, 987),
            'WPN': (630, 630), 'EQU': (692, 692),
            'TWP': (629, 629), 'TEQ': (662, 662),
            'SKB': (0, 381), 'MED02': (0, 100),
        }
        for section, (flagged, total) in expected_counts.items():
            rows = metadata.sections[section]['records']
            self.assertEqual(len(rows), total)
            self.assertEqual(sum(growth.fields(row)[16] == b'1' for row in rows), flagged)
        selected = []
        # These are real loaded item definitions passed to the original 963C0
        # caller in an offline UI/slot fixture. No live socket/use is implied.
        for section in ('EGG', 'SPP', 'WPN', 'EQU', 'TWP', 'TEQ'):
            rows = metadata.sections[section]['records']
            for index in (0, len(rows) - 1):
                definition = metadata.item_row(section, index)
                self.assertTrue(definition['record'][0x11a] & 4)
                _, request = producer.produce(item=definition['key'],
                                              definition=definition['record'],
                                              slot=len(selected))
                self.assertEqual(request[0], 0x28)
                self.assertEqual(request[-1], 1)
                selected.append(request)
        self.assertEqual(len(selected), 12)
        # The mixed batch is an explicit parser test, not a captured TCP batch.
        batch = b'\x30\x00'.join(selected)
        accepted = subprocess.run([str(executable), '--logical', batch.hex()],
                                  capture_output=True, text=True, timeout=20)
        self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
        self.assertEqual(accepted.stdout.strip(), batch.hex())
        for malformed in (batch[:-1], batch[:-1] + b'\x00'):
            rejected = subprocess.run([str(executable), '--logical', malformed.hex()],
                                      capture_output=True, text=True, timeout=20)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, '')

    def test_native_close_action_sequences_survive_without_pair_inference(self):
        executable = ROOT / 'build/tests/Release/recovered-world-records.exe'
        report = close.build_report()
        self.assertFalse(report['requires_85_then_86'])
        for scenario in report['scenarios']:
            with self.subTest(scenario=scenario['name']):
                self.assertTrue(scenario['result']['returned'])
                logical = scenario['result']['appended_hex']
                result = subprocess.run([str(executable), '--logical', logical],
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout.strip().lower(), logical)

    def test_all_original_stack_tails_survive_formal_cpp_batch(self):
        executable = ROOT / 'build/tests/Release/recovered-world-records.exe'
        self.assertTrue(executable.is_file(), 'Build the formal codec target first')
        machine = native.NativeAction(native.evidence())
        batch = bytearray()
        for tail in range(256):
            incoming = machine.ingest(native.fixture(
                request_word=0x1200 + tail, reply_word=0x8002, context_byte=tail ^ 0xa5))
            self.assertEqual(incoming['stop_rva'], 0xc8234)
            result = machine.action(page=0, page_count=1, mode=1, threshold=0,
                                    choice=-1, stack_byte=tail, queued_count=0,
                                    lock_pointer=0)
            self.assertEqual(result['stop_rva'], 0xc8350)
            self.assertEqual(result['queue_count_after'], 7)
            record = bytes.fromhex(result['appended_hex'])
            self.assertEqual(record, bytes((0x85, tail, 0x12, 2, 0, tail ^ 0xa5, tail)))
            batch.extend(record)
            machine.events.clear()
        result = subprocess.run([str(executable), '--logical', batch.hex()],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip().lower(), batch.hex())
        # The same native bytes with a truncated final request must fail as a
        # whole batch; the CLI must not print a successful prefix.
        rejected = subprocess.run([str(executable), '--logical', batch[:-1].hex()],
                                  capture_output=True, text=True, timeout=20)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(rejected.stdout, '')


if __name__ == '__main__':
    unittest.main()
