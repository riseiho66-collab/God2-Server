import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from login_terminal import frame,qualify
from c2s0002 import key
from apex import progression

ROOT=Path(__file__).resolve().parents[2]


class LoginTerminalTests(unittest.TestCase):
    def setUp(self):
        source=ROOT/'artifacts/runs/login-terminal-success-01'
        self.events=[]
        for name in ('compat-events.jsonl','network-events.jsonl'):
            self.events.extend(json.loads(line) for line in (source/name).read_text().splitlines())
        self.prior={'LAST_ACCEPTED_STATE':'S2C0003_ACCEPTED_WAIT_CONTINUES'}
        self.wire=frame(key(ROOT))

    def test_exact_wire_and_decode(self):
        self.assertEqual(self.wire.hex(),'14000707fdfdfdfdfdfdfdfdfdfdfdfdfdfdba15')
        previous=0;clear=[];k=key(ROOT)
        for i,b in enumerate(self.wire[2:]):
            value=((b+3-previous)&255)^k[i];clear.append(value);previous=value
        self.assertEqual(bytes(clear[:-1]),bytes([10])+bytes(16))
        self.assertEqual(clear[-1],sum(b+60 for b in self.wire[:2]+bytes(clear[:-1]))&255)

    def test_runtime_acceptance(self):
        self.assertTrue(qualify(self.events,self.prior,self.wire,self.wire))

    def test_reject_incomplete_or_failed_evidence(self):
        for name in ('LOGIN_TERMINAL_RETURN','LOGIN_STATE_CHANGE_ENTER','LOGIN_STATE_CHANGE_RETURN'):
            filtered=[e for e in self.events if e.get('event_type')!=name]
            self.assertFalse(qualify(filtered,self.prior,self.wire,self.wire))
        changed=copy.deepcopy(self.events)
        next(e for e in changed if e.get('event_type')=='LOGIN_TERMINAL_RETURN')['eax']=1
        self.assertFalse(qualify(changed,self.prior,self.wire,self.wire))
        self.assertFalse(qualify(self.events,{'LAST_ACCEPTED_STATE':'REGRESSION'},self.wire,self.wire))
        self.assertFalse(qualify(self.events,self.prior,self.wire[:-1],self.wire))

    def test_request_is_not_login(self):
        self.assertFalse(progression([{'event_type':'CREDENTIAL_REQUEST_VERIFIED'}])['LOGIN'])
        self.assertTrue(progression([{'event_type':'LOGIN_ACCEPTED_VERIFIED'}])['LOGIN'])


if __name__=='__main__':unittest.main()
