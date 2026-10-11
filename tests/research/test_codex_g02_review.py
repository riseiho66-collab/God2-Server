"""Synthetic checks for the separate automated G02 path, not runtime evidence."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/research'))
import codex_g02_review as review
from test_artifact_vault import synthetic_pe


class CodexReviewTests(unittest.TestCase):
    def test_reconstruction_changes_only_declared_headers(self):
        raw = synthetic_pe()
        mapped = bytearray(0x2000)
        mapped[:0x200] = raw[:0x200]
        mapped[0x1000:0x1200] = raw[0x200:]
        result = review.reconstruct(mapped, 0x1010)
        expected = bytearray(mapped)
        pe = struct.unpack_from('<I', mapped, 0x3c)[0]
        opt = pe+24
        sh = opt+struct.unpack_from('<H', mapped, pe+20)[0]
        struct.pack_into('<I', expected, opt+16, 0x1010)
        size = struct.unpack_from('<I', mapped, sh+8)[0]
        struct.pack_into('<II', expected, sh+16, (size+0x1ff)//0x200*0x200, 0x1000)
        self.assertEqual(result, bytes(expected))
        mapped[:2] = b'XX'
        with self.assertRaises(ValueError):
            review.reconstruct(mapped, 0x1010)

    def test_audit_detects_binding_change_and_revocation(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(review, 'cross_check', return_value={'capture_sha256': review.CAPTURE}):
            home = Path(temp)
            bound = home/'bound.txt'; bound.write_text('evidence')
            value = {'kind': 'G02_CODEX_CERTIFICATE', 'human_attestation': False,
                     'capture_sha256': review.CAPTURE, 'bindings': {str(bound): review.digest(bound)}}
            identity = review.publish(home/'artifacts/codex-certificates', value)
            with patch.object(review, 'HOME', home):
                self.assertEqual(review.audit(identity), 'VALID_CODEX_ONLY')
                bound.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'Bound file changed'):
                    review.audit(identity)
                bound.write_text('evidence')
                review.publish(home/'artifacts/codex-revocations', {'certificate': identity})
                with self.assertRaisesRegex(ValueError, 'revoked'):
                    review.audit(identity)


if __name__ == '__main__':
    unittest.main()
