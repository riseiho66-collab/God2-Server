"""Native-template owned transport against the actual hidden-client candidate."""
import hashlib
import json
from pathlib import Path
import unittest
import test_owned_companions_server as owned

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=ROOT/'artifacts/research/deity-portrait-20260927/accepted-server.exe'
RECEIPT=ROOT/'artifacts/playtests/private-deity-templates-20260927-13/run-result.json'

class NativeDeityTemplatesServerTests(unittest.TestCase):
    def test_native_templates_selection_transfer_restart(self):
        accepted=json.loads(RECEIPT.read_text('utf-8'))
        self.assertTrue(accepted['accepted'])
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),accepted['server_sha256'])
        self.assertEqual(accepted['ui']['deity_native_metadata']['definition_count'],34)
        self.assertEqual([s['selection'] for s in accepted['ui']['deity_native_selection']['stages']],[[2,2],[1,3]])
        original=owned.BINARY
        try:
            owned.BINARY=ARCHIVE;owned.OwnedCompanionsServerTests.setUpClass()
            owned.OwnedCompanionsServerTests().run_case(pet1_only=True,deity_templates=True)
        finally:owned.BINARY=original

if __name__=='__main__':unittest.main()
