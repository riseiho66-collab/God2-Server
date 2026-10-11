"""Real owned process attachment checks; not two-native-client acceptance."""
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import time
import unittest

import psutil
import test_recovered_movement_server as movement
from tools.strike_lab.shared_cpp_server import SharedCppServer


class SharedServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):movement.RecoveredMovementServerTests.setUpClass()

    def test_two_attachments_never_terminate_owner_and_reject_stale_manifest(self):
        root=movement.world.dual.ROOT
        evidence=(root/'artifacts/runs').resolve()
        harness=movement.RecoveredMovementServerTests()
        _,h=harness.harness()
        with tempfile.TemporaryDirectory(prefix='shared-server-test-',dir=evidence) as directory:
            run=Path(directory).resolve()
            self.assertEqual(run.parent,evidence)
            port=h.unused_port()
            while port==2592:port=h.unused_port()
            config=h.configuration(run,database=run/'player-visibility-diagnostic.db',character_port=port)
            config['server']['port']=2592
            config['development']['diagnostic_player_visibility']=True
            config['development']['diagnostic_remote_actor_language']=0
            with (run/'stdout.log').open('wb') as log:
                process=h.launch(run,config,log)
                try:
                    owner=psutil.Process(process.pid)
                    deadline=time.monotonic()+5
                    expected={('127.0.0.1',p) for p in (2592,port)}
                    while time.monotonic()<deadline:
                        self.assertIsNone(process.poll(),'Isolated shared server exited during startup')
                        listeners={(c.laddr.ip,c.laddr.port) for c in owner.net_connections(kind='tcp')
                                   if c.status==psutil.CONN_LISTEN}
                        if listeners==expected:break
                        time.sleep(.05)
                    self.assertEqual(listeners,expected)
                    path=run/'config.json'
                    manifest=run/'shared-server.json'
                    document=dict(schema='god2-shared-loopback-server-v1',pid=process.pid,
                        create_time=owner.create_time(),config=str(path),
                        config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),ports=[2592,port])
                    manifest.write_text(json.dumps(document))
                    first=SharedCppServer(manifest,root)
                    second=SharedCppServer(manifest,root)
                    self.assertEqual(first.allowed_ports,{2592,port})
                    client=run/'client';(client/'config').mkdir(parents=True)
                    contents={'config/display.settings':b'Windowed=true\n',
                              'ctserver.ini':b'127.0.0.1\n','ddraw.ini':b'[ddraw]\nwindowed=true\n'}
                    for name,data in contents.items():(client/name).write_bytes(data)
                    profile=dict(root=str(client),sha256={name:hashlib.sha256(data).hexdigest()
                                                         for name,data in contents.items()})
                    first.document['client_profile']=profile
                    second.document['client_profile']=profile
                    previous=os.environ.get('GOD2_CLASSIC_RESOLUTION')
                    with first.client_profile(client),second.client_profile(client):
                        self.assertEqual(os.environ['GOD2_CLASSIC_RESOLUTION'],'800x600')
                    self.assertEqual(os.environ.get('GOD2_CLASSIC_RESOLUTION'),previous)
                    for name,data in contents.items():self.assertEqual((client/name).read_bytes(),data)
                    with self.assertRaises(ValueError):
                        with first.client_profile(client):
                            (client/'ddraw.ini').write_bytes(b'changed')
                    self.assertEqual(os.environ.get('GOD2_CLASSIC_RESOLUTION'),previous)
                    (client/'ddraw.ini').write_bytes(contents['ddraw.ini'])
                    with self.assertRaises(ValueError):first.verify_client_profile(run)
                    first.close();first.close()
                    self.assertTrue(first.closed)
                    self.assertIsNone(second.process.poll())
                    self.assertIsNone(process.poll())
                    for key,value in (('create_time',document['create_time']-1),
                                      ('config_sha256','0'*64),('ports',[2592,2592]),
                                      ('ports',[2592,1]),('pid',True)):
                        bad=dict(document);bad[key]=value
                        manifest.write_text(json.dumps(bad))
                        with self.assertRaises(ValueError):SharedCppServer(manifest,root)
                        self.assertIsNone(process.poll())
                    second.close()
                    with socket.create_connection(('127.0.0.1',2592),timeout=1) as client:
                        self.assertTrue(client.recv(19))
                    self.assertIsNone(process.poll())
                finally:
                    h.stop(process)
                self.assertEqual(second.process.poll(),0)


if __name__=='__main__':unittest.main()
