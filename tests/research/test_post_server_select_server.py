from contextlib import contextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'artifacts/golden/server-list/server-list-one-01'
REQUEST=ROOT/'artifacts/golden/server-select/C2S_0001.bin'


class PostSelectServerTests(unittest.TestCase):
    @contextmanager
    def server(self,mode='god2_post_server_select',strike=False,allow_unverified_legacy=False,
               recovered_account_auth=False,local_account_registration=False,run_for=3,database_path=None,
               recovered_character_creation=False):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=json.loads((ROOT/'config/recovered-post-server-select.json').read_text())
            with socket.socket() as reserve:
                reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
            config['server']['port']=port;config['protocol']['mode']=mode
            config['protocol']['allow_unverified_legacy']=allow_unverified_legacy
            config['development']['recovered_account_auth']=recovered_account_auth
            config['development']['local_account_registration']=local_account_registration
            config['development']['recovered_character_creation']=recovered_character_creation
            config['database']['path']=str(database_path or root/'test.db')
            config['logging']['file']=str(root/'server.log')
            config['lua']['script_root']=str(ROOT/'scripts')
            config['lua']['bootstrap']=str(ROOT/'scripts/bootstrap.lua')
            path=root/'config.json';path.write_text(json.dumps(config))
            with (root/'stdout.log').open('wb') as log:
                env=dict(os.environ)
                env.pop('GOD2_POST6B_STRIKE_HOLD',None)
                env.pop('GOD2_UI_GATE_CONTROL',None)
                if strike:env['GOD2_POST6B_STRIKE_HOLD']='1'
                process=subprocess.Popen([str(ROOT/'build/Release/god2-server.exe'),'--config',str(path),'--run-for',str(run_for)],
                    cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    deadline=time.monotonic()+2
                    while True:
                        try:client=socket.create_connection(('127.0.0.1',port),timeout=1);break
                        except OSError:
                            if time.monotonic()>deadline:raise
                            time.sleep(.05)
                    with client:yield client,root
                finally:
                    if process.poll() is None:process.terminate()
                    process.wait(timeout=5)

    def prefix(self,client):
        def receive(name):
            expected=(PREFIX/name).read_bytes();data=b''
            while len(data)<len(expected):
                chunk=client.recv(len(expected)-len(data))
                if not chunk:self.fail('Prefix closed prematurely')
                data+=chunk
            self.assertEqual(data,expected)
        receive('S2C_0001.bin');client.sendall((PREFIX/'C2S_0001.bin').read_bytes())
        receive('S2C_0002.bin');client.sendall((PREFIX/'C2S_0002.bin').read_bytes())
        for name in ('S2C_0003.bin','S2C_SERVER_LIST_0001.bin','S2C_0004.bin'):receive(name)

    def closed(self,client):
        try:self.assertEqual(client.recv(1),b'')
        except ConnectionResetError:pass

    def test_fragmented_request_no_response(self):
        with self.server() as (client,root):
            self.prefix(client)
            for byte in REQUEST.read_bytes():client.sendall(bytes([byte]));time.sleep(.01)
            client.settimeout(.3)
            with self.assertRaises(socket.timeout):client.recv(1)
            self.assertIn('POST_SERVER_SELECT_C2S_ACCEPTED length=6',(root/'stdout.log').read_text())

    def test_corrupt_request_rejected(self):
        with self.server() as (client,root):
            self.prefix(client)
            data=bytearray(REQUEST.read_bytes());data[-1]^=1
            client.sendall(data);self.closed(client)
            self.assertNotIn('POST_SERVER_SELECT_C2S_ACCEPTED',(root/'stdout.log').read_text())

    def test_old_server_list_mode_unchanged(self):
        with self.server('god2_server_list') as (client,root):
            self.prefix(client);client.sendall(REQUEST.read_bytes());self.closed(client)
            self.assertIn('C2S0002 unexpected data or length',(root/'stdout.log').read_text())

    def test_unverified_second_request_rejected(self):
        with self.server() as (client,root):
            self.prefix(client);client.sendall(REQUEST.read_bytes())
            client.settimeout(.2)
            with self.assertRaises(socket.timeout):client.recv(1)
            client.settimeout(1)
            client.sendall(REQUEST.read_bytes());self.closed(client)
            self.assertIn('Post-selection next C2S contract unknown',(root/'stdout.log').read_text())

    def test_strike_acceptance_suspends_idle_policy_without_response(self):
        with self.server(strike=True) as (client,root):
            self.prefix(client);client.sendall(REQUEST.read_bytes())
            client.settimeout(.3)
            with self.assertRaises(socket.timeout):client.recv(1)
            log=(root/'stdout.log').read_text()
            self.assertIn('POST_SERVER_SELECT_C2S_ACCEPTED',log)
            self.assertIn('POST6B_STRIKE_IDLE_TIMEOUT_SUSPENDED',log)

    def test_strike_does_not_accept_request_before_prefix(self):
        with self.server(strike=True) as (client,root):
            hello=b''
            while len(hello)<19:hello+=client.recv(19-len(hello))
            client.sendall(REQUEST.read_bytes()+bytes(13))
            self.closed(client)
            self.assertNotIn('POST6B_STRIKE_IDLE_TIMEOUT_SUSPENDED',(root/'stdout.log').read_text())

    def test_strike_flag_does_not_change_old_mode(self):
        with self.server('god2_server_list',strike=True) as (client,root):
            self.prefix(client);client.sendall(REQUEST.read_bytes());self.closed(client)
            self.assertNotIn('POST6B_STRIKE_IDLE_TIMEOUT_SUSPENDED',(root/'stdout.log').read_text())


if __name__=='__main__':unittest.main()
