import copy
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from server_list import WIRE,qualifies
from login_terminal import frame
from c2s0002 import key,decode

ROOT=Path(__file__).resolve().parents[2]


class ServerListTests(unittest.TestCase):
    def setUp(self):
        run=ROOT/'artifacts/runs/server-list-one-01'
        self.events=[json.loads(line) for line in (run/'compat-events.jsonl').read_text().splitlines()]

    def test_live_acceptance_and_golden(self):
        self.assertTrue(qualifies({'LOGIN':True},self.events,WIRE))
        self.assertEqual((ROOT/'artifacts/golden/server-list/server-list-one-01/S2C_SERVER_LIST_0001.bin').read_bytes(),WIRE)

    def test_strict_evidence(self):
        self.assertFalse(qualifies({'LOGIN':False},self.events,WIRE))
        self.assertFalse(qualifies({'LOGIN':True},self.events,WIRE[:-1]))
        changed=copy.deepcopy(self.events)
        for e in changed:
            if e.get('event_type')=='SERVER_LIST_UI_COUNT':e['list_state']='LIST_UI count=0 selected=ffff enabled0=0 directory_count=1'
        self.assertFalse(qualifies({'LOGIN':True},changed,WIRE))
        self.assertFalse(qualifies({'LOGIN':True},[e for e in self.events if e.get('event_type')!='SERVER_LIST_WRITTEN'],WIRE))

    def test_decode_checksum(self):
        previous=0;clear=[]
        for byte in WIRE[2:]:
            value=(byte+3-previous)&255;clear.append(value);previous=value
        self.assertEqual(bytes(clear[:-1]),bytes([4,0,0,1,0]))
        self.assertEqual(clear[-1],sum(b+60 for b in WIRE[:2]+bytes(clear[:-1]))&255)

    def test_cpp_packet_order(self):
        config=json.loads((ROOT/'config/recovered-server-list.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory)
            with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
            config['server']['port']=port;config['database']['path']=str(temp/'test.db')
            config['logging']['file']=str(temp/'server.log')
            config['lua']['script_root']=str(ROOT/'scripts');config['lua']['bootstrap']=str(ROOT/'scripts/bootstrap.lua')
            path=temp/'config.json';path.write_text(json.dumps(config))
            def receive(client,n):
                data=b''
                while len(data)<n:
                    part=client.recv(n-len(data))
                    if not part:raise AssertionError('Unexpected EOF')
                    data+=part
                return data
            with (temp/'stdout.log').open('wb') as log:
                process=subprocess.Popen([str(ROOT/'build/Release/god2-server.exe'),'--config',str(path),'--run-for','4'],
                    cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    deadline=time.monotonic()+3
                    while True:
                        try:client=socket.create_connection(('127.0.0.1',port),timeout=1);break
                        except OSError:
                            if time.monotonic()>deadline:raise
                            time.sleep(.05)
                    with client:
                        baseline=ROOT/'artifacts/golden/login/login-terminal-final-01'
                        self.assertEqual(receive(client,19),(baseline/'S2C_0001.bin').read_bytes())
                        client.sendall((baseline/'C2S_0001.bin').read_bytes())
                        self.assertEqual(receive(client,5),(baseline/'S2C_0002.bin').read_bytes())
                        request=(baseline/'C2S_0002.bin').read_bytes();client.sendall(request)
                        self.assertEqual(decode(receive(client,176),key(ROOT)),b'\x1d'+decode(request,key(ROOT))[1:])
                        self.assertEqual(receive(client,8),WIRE)
                        self.assertEqual(receive(client,20),frame(key(ROOT)))
                        client.settimeout(.2)
                        with self.assertRaises(socket.timeout):
                            client.recv(1)
                    self.assertEqual(process.wait(timeout=6),0)
                finally:
                    if process.poll() is None:process.terminate();process.wait(timeout=3)


if __name__=='__main__':unittest.main()
