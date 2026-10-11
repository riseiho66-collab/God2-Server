import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from post_seed import summarize,WIRE


class PostSeedTests(unittest.TestCase):
    def evaluate(self,seed_ok=True,wire=WIRE,field=True,return_value=0):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);run=home/'run';run.mkdir()
            (run/'s2c').mkdir();(run/'network').mkdir()
            (run/'s2c/recv-0002.bin').write_bytes(wire)
            events=[{'event_type':'INITIAL_HANDSHAKE_RETURN','sequence':1},
                {'event_type':'API_RETURN','api':'recv','matched':True,'eax':len(wire),'sequence':2},
                {'event_type':'POST_SEED_HANDLER_ENTERED','sequence':3,'field_comparison':'opcode=1 received=53 expected=53'},
                {'event_type':'POST_SEED_FIELD_ACCEPTED' if field else 'OTHER','sequence':4},
                {'event_type':'POST_SEED_WAIT_RETURN','sequence':5,'eax':return_value}]
            return summarize(home,run,events,{'LAST_ACCEPTED_STATE':'INITIAL_SEED_EXCHANGE' if seed_ok else 'REGRESSION'})

    def test_acceptance_requires_wire_and_runtime(self):
        self.assertEqual(self.evaluate()['LAST_ACCEPTED_STATE'],'POST_SEED_ACCEPTED')
        self.assertEqual(self.evaluate(wire=WIRE[:-1]+b'\x80')['LAST_ACCEPTED_STATE'],'INITIAL_SEED_EXCHANGE')
        self.assertEqual(self.evaluate(field=False)['LAST_ACCEPTED_STATE'],'INITIAL_SEED_EXCHANGE')
        self.assertEqual(self.evaluate(return_value=1)['LAST_ACCEPTED_STATE'],'INITIAL_SEED_EXCHANGE')

    def test_regression_blocks_downstream_claims(self):
        result=self.evaluate(seed_ok=False)
        self.assertEqual(result['LAST_ACCEPTED_STATE'],'REGRESSION')
        self.assertIsNone(result['NEW_HANDLER'])

    def test_seed_alias_exact(self):
        root=Path(__file__).resolve().parents[2]
        alias=json.loads((root/'artifacts/golden/GOLDEN_SESSION_SEED_V1.json').read_text())
        for direction in ('s2c','c2s'):
            expected=bytes.fromhex(alias[direction+'_hex'])
            self.assertEqual(len(expected),19)
            self.assertEqual((root/alias['source']/f'{direction}-000001.bin').read_bytes(),expected)

    def test_wire_independent_decode(self):
        previous=0;clear=[]
        for value in WIRE[2:]:
            decoded=(value+3-previous)&255
            clear.append(decoded);previous=decoded
        self.assertEqual(bytes(clear[:2]),bytes([1,0x53]))
        self.assertEqual(clear[-1],sum(b+0x3c for b in WIRE[:2]+bytes(clear[:2]))&255)


if __name__=='__main__':unittest.main()
