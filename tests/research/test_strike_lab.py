import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/strike_lab'))
import lab
import capture


class StrikeLabTests(unittest.TestCase):
    def test_static_profile_restores_ddraw_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'client'; run=Path(temp)/'run'
            root.mkdir();run.mkdir()
            original=b'[ddraw]\r\nwidth=1280\r\nheight=960\r\ncustom=preserve\r\n'
            (root/'ddraw.ini').write_bytes(original)
            with lab.profile_context(lab.PROFILES[2],root,run):
                changed=(root/'ddraw.ini').read_text()
                self.assertIn('width=800',changed)
                self.assertIn('custom=preserve',changed)
                self.assertIn('resizable=false',changed)
            self.assertEqual((root/'ddraw.ini').read_bytes(),original)

    def test_context_restores_existing_and_absent_files_on_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'client'; run=Path(temp)/'run'
            root.mkdir(); run.mkdir()
            (root/'ctserver.ini').write_bytes(b'original')
            original=os.environ.get('GOD2_CLASSIC_RESOLUTION')
            with self.assertRaises(RuntimeError):
                with lab.profile_context(lab.PROFILES[1],root,run):
                    self.assertEqual(os.environ['GOD2_CLASSIC_RESOLUTION'],'800x600')
                    self.assertIn(b'127.0.0.1',(root/'ctserver.ini').read_bytes())
                    raise RuntimeError('test')
            self.assertEqual((root/'ctserver.ini').read_bytes(),b'original')
            self.assertFalse((root/'config/display.settings').exists())
            self.assertEqual(os.environ.get('GOD2_CLASSIC_RESOLUTION'),original)

    def test_listener_rejects_unconfirmed_argument_port(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence=Path(temp)/'evidence.json'
            evidence.write_text(json.dumps({'port':6001,'kind':'CONTROLLED_ARGUMENT','destination_ip':'127.0.0.1'}))
            with self.assertRaises(ValueError): lab.confirmed_port(evidence)

    def test_listener_requires_bound_raw_sockaddr(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); log=root/'native.log'; evidence=root/'evidence.json'
            # Synthetic parser fixture only; this test never binds a socket.
            marker='LAB_CONNECT af=2 port=7117 ip=100007f'
            log.write_text(marker)
            data={'kind':'RUNTIME_CONNECT_ENTRY','destination_ip':'127.0.0.1','port':6001,
                  'native_log':'native.log','native_sha256':lab.sha(log),'sockaddr_marker':marker}
            evidence.write_text(json.dumps(data)); self.assertEqual(lab.confirmed_port(evidence),6001)
            data['port']=6002; evidence.write_text(json.dumps(data))
            with self.assertRaises(ValueError): lab.confirmed_port(evidence)
            data['port']=6001; data['destination_ip']='0.0.0.0'; evidence.write_text(json.dumps(data))
            with self.assertRaises(ValueError): lab.confirmed_port(evidence)
            data['destination_ip']='127.0.0.1'; evidence.write_text(json.dumps(data)); log.write_text('tampered')
            with self.assertRaises(ValueError): lab.confirmed_port(evidence)

    def test_parse_marker(self):
        self.assertEqual(capture.parse_marker('LAB_STOP pid=10 tid=20 pc=0045599f\n')['pc'],0x45599f)
        with self.assertRaises(ValueError): capture.parse_marker('native stop')

    def test_diff_detects_missing_and_changed_keys(self):
        self.assertEqual(set(lab.diff_values({'same':1,'old':2},{'same':1,'new':3})),{'old','new'})

    def test_exclusive_json_preserves_existing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'evidence.json'
            lab.write_json(path,{'first':True})
            with self.assertRaises(FileExistsError): lab.write_json(path,{'first':False})
            self.assertTrue(json.loads(path.read_text())['first'])


if __name__=='__main__': unittest.main()
