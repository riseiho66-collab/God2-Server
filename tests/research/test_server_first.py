import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from server_first import initial_frame,checksum,zero_seed_response


class ServerFirstTests(unittest.TestCase):
    def test_initial_wire_contract(self):
        frame=initial_frame()
        self.assertEqual(len(frame),19)
        self.assertEqual(frame[:2],b'\x13\x00')
        self.assertEqual(frame[2:18],bytes(16))
        self.assertEqual(frame[-1],0x4b)
        self.assertEqual(checksum(frame[:-1]),frame[-1])

    def test_wrong_seed_size_rejected(self):
        for size in (0,15,17):
            with self.assertRaises(ValueError):initial_frame(bytes(size))

    def test_payload_change_changes_checksum(self):
        frame=initial_frame(bytes(range(16)))
        self.assertEqual(checksum(frame[:-1]),frame[-1])
        self.assertNotEqual(frame[-1],initial_frame()[-1])

    def test_derived_response_matches_real_client(self):
        root=Path(__file__).resolve().parents[2]
        image=root/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
        wire=root/'artifacts/runs/server-first-01/c2s/REAL_C2S_0086.bin'
        if not image.exists() or not wire.exists():self.skipTest('Local runtime evidence not available')
        self.assertEqual(zero_seed_response(image.read_bytes()),wire.read_bytes())

    def test_cpp_partial_response_and_rejection(self):
        import json,socket,subprocess,tempfile,time
        root=Path(__file__).resolve().parents[2]
        executable=root/'build/Release/god2-server.exe'
        if not executable.exists():self.skipTest('C++ server not built')
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory)
            config=json.loads((root/'config/recovered-seed.json').read_text())
            with socket.socket() as reserve:
                reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
            config['server']['port']=port
            config['database']['path']=str(temp/'test.db')
            config['lua']['script_root']=str(root/'scripts')
            config['lua']['bootstrap']=str(root/'scripts/bootstrap.lua')
            config['logging']['file']=str(temp/'server.log')
            path=temp/'config.json';path.write_text(json.dumps(config))
            with (temp/'stdout.log').open('wb') as log:
                process=subprocess.Popen([str(executable),'--config',str(path),'--run-for','4'],stdout=log,stderr=subprocess.STDOUT)
                try:
                    deadline=time.monotonic()+3
                    while True:
                        try:client=socket.create_connection(('127.0.0.1',port),timeout=.5);break
                        except OSError:
                            if time.monotonic()>=deadline:raise
                            time.sleep(.05)
                    def receive_exact(client,n):
                        data=b''
                        while len(data)<n:
                            part=client.recv(n-len(data))
                            if not part:raise AssertionError('Unexpected EOF')
                            data+=part
                        return data
                    response=bytes.fromhex('1300d60ea46cf2f0801a6e134f9141487f8d6e')
                    with client:
                        self.assertEqual(receive_exact(client,19),initial_frame())
                        client.sendall(response[:1]);time.sleep(.05)
                        client.sendall(response[1:7]);time.sleep(.05);client.sendall(response[7:])
                        time.sleep(.1)
                        client.sendall(b'unsupported-next-state')
                        self.assertEqual(client.recv(1),b'')
                    time.sleep(.1)
                    with socket.create_connection(('127.0.0.1',port),timeout=1) as bad:
                        self.assertEqual(receive_exact(bad,19),initial_frame())
                        bad.sendall(response[:-1]+bytes([response[-1]^1]))
                        self.assertEqual(bad.recv(1),b'')
                    self.assertEqual(process.wait(timeout=6),0)
                finally:
                    if process.poll() is None:process.terminate();process.wait(timeout=3)
            output=(temp/'stdout.log').read_text(encoding='utf-8',errors='replace')
            self.assertEqual(output.count('GOD2_SEED_EXCHANGE_ACCEPTED'),1)


if __name__=='__main__':unittest.main()
