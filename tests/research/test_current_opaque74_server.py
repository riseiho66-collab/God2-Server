"""Private TCP admission of current native C2S74; gameplay remains unqualified."""

from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/research"))
import test_pet2_revert_server as pet2


class CurrentOpaque74ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pet2.BINARY.is_file() or not (pet2.SOURCE / "town-diagnostic-accounts.db").is_file():
            raise AssertionError("Candidate and isolated companion fixture required")
        pet2.dual.RecoveredDualConnectionServerTests.crypto_key = pet2.dual.key(ROOT)

    def test_standalone_opaque_payload_preserves_socket_and_saved_state(self):
        with pet2.Pet2RevertServerTests.server(self) as (helper, decoder, game, saved, project, _deny, log):
            project()
            baseline = saved()
            game.sendall(helper.frame(0x88, b"\x34\x12"))
            for payload in (0x00, 0xA5, 0xFF):
                game.sendall(helper.frame(0x74, bytes((payload,))))
            helper.silent(game)
            deadline = time.monotonic() + 3
            while log().count("NATIVE_PANEL_TRANSPORT_ADMITTED") < 4:
                self.assertLess(time.monotonic(), deadline, "Panel records did not reach Application")
                time.sleep(.02)
            self.assertIn("opcode=88 no_state_change no_reply", log())
            self.assertEqual(log().count("opcode=74 no_state_change no_reply"), 3)
            self.assertEqual(saved(), baseline)
            # A native pose exchange must still be accepted on the same socket.
            game.sendall(helper.frame(0x66, b"\x00\x08\x00"))
            reply = decoder.logical(helper, game)
            self.assertEqual(reply[0], 0x77)
            self.assertEqual(saved(), baseline)


if __name__ == "__main__":
    unittest.main()
