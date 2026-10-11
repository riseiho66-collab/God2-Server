"""Same accepted E3/FB candidate: socket transfers, persistence and restart."""
import hashlib
import json
from pathlib import Path
import unittest
import test_owned_companions_server as owned

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=ROOT/'artifacts/research/native-pet1-20260927/accepted-server.exe'
RECEIPT=ROOT/'artifacts/playtests/private-pet1-mixed-20260927-02/run-result.json'

class OwnedPet1ServerTests(unittest.TestCase):
    def test_mixed_generation_transfer_restart_and_exact_restore(self):
        accepted=json.loads(RECEIPT.read_text('utf-8'))
        self.assertTrue(accepted['accepted']);self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),accepted['server_sha256'])
        original=owned.BINARY
        try:
            owned.BINARY=ARCHIVE;owned.OwnedCompanionsServerTests.setUpClass()
            owned.OwnedCompanionsServerTests().run_case(pet1_only=True)
        finally:owned.BINARY=original

if __name__=='__main__':unittest.main()
