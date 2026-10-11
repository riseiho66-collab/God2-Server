"""Own-candidate TCP acceptance for native1D; not original-server rule proof."""
import sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/research'))
import test_pet2_revert_server as pet2

class CurrentOptionsServerTests(unittest.TestCase):
    setUpClass=classmethod(lambda cls:pet2.Pet2RevertServerTests.setUpClass())
    def test_options_preserve_connection_and_owned_saves(self):
        with pet2.Pet2RevertServerTests.server(self) as (helper,decoder,game,saved,project,_deny,log):
            project();before=saved()
            for raw in (0,0x10,0x1ff,0xa5a5,0xffff):
                game.sendall(helper.frame(0x1d,raw.to_bytes(2,'little')));helper.silent(game)
            deadline=time.monotonic()+3
            while log().count('NATIVE_OPTIONS_TRANSPORT_ADMITTED')<5:
                self.assertLess(time.monotonic(),deadline);time.sleep(.02)
            self.assertIn('flags=a5a5 no_state_change no_reply',log())
            self.assertEqual(saved(),before)
            game.sendall(helper.frame(0x66,b'\0\x08\0'))
            self.assertEqual(decoder.logical(helper,game)[0],0x77)
            self.assertEqual(saved(),before)

if __name__=='__main__':unittest.main()
