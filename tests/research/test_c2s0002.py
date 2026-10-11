import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from c2s0002 import decode,key,summarize

ROOT=Path(__file__).resolve().parents[2]


class C2S0002Tests(unittest.TestCase):
    def test_logical_equals_live_capture(self):
        for name in ('c2s0002-input-A','c2s0002-input-B'):
            run=ROOT/'artifacts/runs'/name
            self.assertEqual(decode((run/'network/C2S_0002.bin').read_bytes(),key(ROOT)),
                (run/'network/C2S_0002.logical.bin').read_bytes())

    def test_length_and_checksum(self):
        wire=(ROOT/'artifacts/golden/post-seed/C2S_0002.bin').read_bytes()
        for bad in (wire[:1],wire[:-1],b'\xb1'+wire[1:],wire+b'\0',wire[:-1]+bytes([wire[-1]^1])):
            with self.assertRaises(ValueError):decode(bad,key(ROOT))

    def test_single_input_difference(self):
        a=(ROOT/'artifacts/runs/c2s0002-input-A/network/C2S_0002.logical.bin').read_bytes()
        b=(ROOT/'artifacts/runs/c2s0002-input-B/network/C2S_0002.logical.bin').read_bytes()
        self.assertEqual([i for i in range(173) if a[i]!=b[i]],[6,8])

    def test_reducer_handles_unsequenced_ui_events(self):
        source=ROOT/'artifacts/runs/c2s0002-s2c3-01'
        events=[]
        for name in ('compat-events.jsonl','network-events.jsonl'):
            events.extend(json.loads(line) for line in (source/name).read_text().splitlines())
        events.sort(key=lambda e:e.get('sequence',-1))
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory)/'run';run.mkdir();(run/'network').mkdir();(run/'s2c').mkdir();(run/'c2s').mkdir()
            for folder in ('network','s2c','c2s'):
                for path in (source/folder).glob('*.bin'):(run/folder/path.name).write_bytes(path.read_bytes())
            (run/'network/C2S_0002.json').write_bytes((source/'network/C2S_0002.json').read_bytes())
            (run/'protocol-core.csv').write_bytes((source/'protocol-core.csv').read_bytes())
            # Regression must prohibit a new golden, even with real downstream events.
            result=summarize(ROOT,run,events,{'LAST_ACCEPTED_STATE':'REGRESSION'})
            self.assertNotEqual(result['classification'],'STATE_ADVANCED')
            self.assertFalse(result['LOGIN'])

    def test_cpp_fragmented_request(self):
        executable=ROOT/'build/Release/god2-server.exe'
        config=json.loads((ROOT/'config/recovered-c2s0002.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory)
            with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
            config['server']['port']=port
            config['database']['path']=str(temp/'test.db')
            config['logging']['file']=str(temp/'test.log')
            config['lua']['script_root']=str(ROOT/'scripts');config['lua']['bootstrap']=str(ROOT/'scripts/bootstrap.lua')
            path=temp/'config.json';path.write_text(json.dumps(config))
            def receive(client,n):
                result=b''
                while len(result)<n:
                    data=client.recv(n-len(result))
                    if not data:raise AssertionError('Unexpected EOF')
                    result+=data
                return result
            with (temp/'stdout.log').open('wb') as log:
                process=subprocess.Popen([str(executable),'--config',str(path),'--run-for','5'],cwd=ROOT,
                    stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    deadline=time.monotonic()+3
                    while True:
                        try:client=socket.create_connection(('127.0.0.1',port),timeout=1);break
                        except OSError:
                            if time.monotonic()>deadline:raise
                            time.sleep(.05)
                    with client:
                        self.assertEqual(receive(client,19),bytes.fromhex('1300000000000000000000000000000000004b'))
                        client.sendall(bytes.fromhex('1300d60ea46cf2f0801a6e134f9141487f8d6e'))
                        self.assertEqual(receive(client,5),bytes.fromhex('0500fe5199'))
                        wire=(ROOT/'artifacts/golden/post-seed/C2S_0002.bin').read_bytes()
                        for part in (wire[:1],wire[1:17],wire[17:175],wire[175:]):
                            client.sendall(part);time.sleep(.02)
                        response=receive(client,176)
                        self.assertEqual(decode(response,key(ROOT)),b'\x1d'+decode(wire,key(ROOT))[1:])
                        client.sendall(b'unsupported-next');self.assertEqual(client.recv(1),b'')
                    self.assertEqual(process.wait(timeout=7),0)
                finally:
                    if process.poll() is None:process.terminate();process.wait(timeout=3)
            self.assertIn('C2S0002_ACCEPTED',(temp/'stdout.log').read_text())


if __name__=='__main__':unittest.main()
