"""Real socket policy test; the normal default is deliberately tested at 120s."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/strike_lab'))
from ui_gate import atomic_json


class HoldTests(unittest.TestCase):
    def test_normal_timeout_and_transparent_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            processes=[];clients=[];logs=[]
            def launch(label,held):
                folder=root/label;folder.mkdir()
                config=json.loads((ROOT/'config/recovered-server-list.json').read_text())
                with socket.socket() as reserve:
                    reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
                config['server']['port']=port
                config['database']['path']=str(folder/'test.db')
                config['logging']['file']=str(folder/'server.log')
                config['lua']['script_root']=str(ROOT/'scripts')
                config['lua']['bootstrap']=str(ROOT/'scripts/bootstrap.lua')
                path=folder/'config.json';path.write_text(json.dumps(config))
                env=os.environ.copy();env.pop('GOD2_UI_GATE_CONTROL',None)
                control=folder/'hold.json'
                if held:env['GOD2_UI_GATE_CONTROL']=str(control)
                log=(folder/'stdout.log').open('wb');logs.append(log)
                process=subprocess.Popen([str(ROOT/'build/Release/god2-server.exe'),'--config',str(path)],
                    cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                processes.append(process)
                deadline=time.monotonic()+5
                while True:
                    try:client=socket.create_connection(('127.0.0.1',port),timeout=.25);break
                    except OSError:
                        if time.monotonic()>deadline:raise
                        time.sleep(.05)
                clients.append(client)
                golden=ROOT/'artifacts/golden/server-list/server-list-one-01'
                def rx(name):
                    expected=(golden/name).read_bytes();actual=b''
                    while len(actual)<len(expected):
                        part=client.recv(len(expected)-len(actual))
                        if not part:raise AssertionError('Unexpected EOF')
                        actual+=part
                    self.assertEqual(actual,expected)
                rx('S2C_0001.bin');client.sendall((golden/'C2S_0001.bin').read_bytes())
                rx('S2C_0002.bin');client.sendall((golden/'C2S_0002.bin').read_bytes())
                for name in ('S2C_0003.bin','S2C_SERVER_LIST_0001.bin','S2C_0004.bin'):rx(name)
                return client,control
            try:
                normal,_=launch('normal',False)
                held,control=launch('held',True)
                status_path=Path(str(control)+'.status')
                def request(enabled):
                    atomic_json(control,{'session_id':1,'hold':enabled,'lease_until_ms':int(time.time()*1000)+10000})
                def status():return json.loads(status_path.read_text())
                def await_flag(key,value):
                    deadline=time.monotonic()+4
                    while time.monotonic()<deadline:
                        try:
                            if status().get(key) is value:return status()
                        except (OSError,ValueError):pass
                        time.sleep(.05)
                    self.fail('Missing server acknowledgement: '+key)
                request(True)
                first=await_flag('ui_gate_hold_active',True)
                started=time.monotonic()
                while time.monotonic()-started<122:
                    request(True)
                    held.settimeout(.25)
                    with self.assertRaises(socket.timeout):held.recv(1)
                    time.sleep(.5)
                normal.settimeout(3)
                try:self.assertEqual(normal.recv(1),b'')
                except ConnectionResetError:pass
                self.assertIn('closing: session timeout',(root/'normal/stdout.log').read_text())
                current=status()
                self.assertTrue(current['ui_gate_hold_active'])
                self.assertEqual(current['last_real_protocol_activity'],first['last_real_protocol_activity'])
                request(False)
                self.assertEqual(await_flag('ui_gate_hold_active',False)['session_timeout_policy'],'Normal')
                request(True);await_flag('ui_gate_hold_active',True)
                held.close()
                self.assertFalse(await_flag('session_alive',False)['ui_gate_hold_active'])
            finally:
                for client in clients:client.close()
                for process in processes:
                    if process.poll() is None:process.terminate()
                    process.wait(timeout=5)
                for log in logs:log.close()


if __name__=='__main__':unittest.main()
