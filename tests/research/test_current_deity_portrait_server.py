"""Mixed E3/FB restart against the actual portrait-qualified server artifact."""
import hashlib
import json
from pathlib import Path
import unittest
import test_owned_companions_server as owned

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=ROOT/'artifacts/research/deity-portrait-20260927/accepted-server.exe'
RECEIPT=ROOT/'artifacts/playtests/private-deity-portrait-20260927-04/run-result.json'

class CurrentDeityPortraitServerTests(unittest.TestCase):
    def test_same_client_accepted_candidate_mixed_transfer_and_restart(self):
        accepted=json.loads(RECEIPT.read_text('utf-8'))
        self.assertTrue(accepted['accepted'])
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),accepted['server_sha256'])
        self.assertEqual(accepted['ui']['deity_native_portrait']['original_action_id'],1101)
        original=owned.BINARY
        try:
            owned.BINARY=ARCHIVE;owned.OwnedCompanionsServerTests.setUpClass()
            owned.OwnedCompanionsServerTests().run_case(pet1_only=True)
        finally:owned.BINARY=original

if __name__=='__main__':unittest.main()
