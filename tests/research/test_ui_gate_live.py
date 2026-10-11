import json
from pathlib import Path
import queue
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/strike_lab'))
import lab
from network_driver import NetworkDriver
from ui_gate_live import RunLease, prefix_verified, LongLivedRunContext
from ui_gate import Rendezvous


class LiveGateTests(unittest.TestCase):
    def test_archived_prefix_matches(self):
        run=ROOT/'artifacts/runs/server-list-one-01'
        events=[]
        for name in ('compat-events.jsonl','network-events.jsonl'):
            events.extend(json.loads(line) for line in (run/name).read_text().splitlines())
        events.sort(key=lambda event:event.get('sequence',-1))
        self.assertTrue(prefix_verified(ROOT,run,events))
        self.assertFalse(prefix_verified(ROOT,run,[e for e in events if e.get('event_type')!='LOGIN_STATE_CHANGE_RETURN']))

    def test_unbounded_driver_pumps_health(self):
        driver=object.__new__(NetworkDriver)
        driver.deadline=None
        driver.executing_target=True
        driver.gate_tick=Mock()
        driver.q=queue.Queue()
        driver.q.put(b'0:000:x86> ')
        self.assertIn('0:000:x86>',driver.stop())
        driver.gate_tick.assert_called_once()

    def test_health_not_called_during_inspection_command(self):
        driver=object.__new__(NetworkDriver)
        driver.deadline=None
        driver.executing_target=False
        driver.gate_tick=Mock()
        driver.q=queue.Queue()
        driver.q.put(b'0:000:x86> ')
        driver.stop()
        driver.gate_tick.assert_not_called()

    def test_debugger_death_is_not_inactivity(self):
        driver=object.__new__(NetworkDriver)
        driver.deadline=None
        driver.q=queue.Queue()
        driver.q.put(None)
        with self.assertRaisesRegex(RuntimeError,'Debugger exited'):
            driver.stop()

    def test_one_run_owns_global_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first=RunLease(root)
            try:
                with self.assertRaises(RuntimeError):RunLease(root)
            finally:first.close()
            second=RunLease(root)
            second.close()

    def test_capture_and_cleanup_release_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'artifacts/strike').mkdir(parents=True)
            run=root/'run';run.mkdir()
            context=object.__new__(LongLivedRunContext)
            context.home=root;context.run=run
            context.server=Mock();context.server.process.poll.return_value=None
            context.client=Mock();context.client.is_running.return_value=True
            context.driver=Mock();context.driver.p.poll.return_value=None
            context.control=Rendezvous('run');context.control.state='WAIT_EXTERNAL_UI'
            context.control.wait_started=0
            context.paths=[];context.reason=None;context.prepared=True
            context.capture('NEW_CLIENT_TX',{'sequence':1})
            context.server.request_hold.assert_called_with(False,wait=True)
            context.server.request_hold.reset_mock()
            context.finish('OPERATOR_CANCEL')
            context.server.request_hold.assert_called_once_with(False,wait=True)
            self.assertFalse(json.loads((run/'ui_gate.json').read_text())['ui_gate_ready'])


if __name__=='__main__':unittest.main()
