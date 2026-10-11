"""Read-only attachment to an explicitly identified owned loopback server."""
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
import threading

import psutil


class BorrowedProcess:
    def __init__(self,process,created):
        self.process=process
        self.created=created

    def poll(self):
        try:
            return None if (self.process.is_running() and self.process.create_time()==self.created
                            and self.process.status()!=psutil.STATUS_ZOMBIE) else 0
        except psutil.NoSuchProcess:
            return 0


class SharedCppServer:
    def __init__(self,manifest,home):
        home=Path(home).resolve(strict=True)
        path=Path(manifest).resolve(strict=True)
        if not path.is_relative_to(home/'artifacts'/'runs'):
            raise ValueError('Shared manifest must belong to our run evidence directory')
        document=json.loads(path.read_text(encoding='utf-8'))
        if document.get('schema')!='god2-shared-loopback-server-v1':
            raise ValueError('Unknown shared server manifest')
        pid=document['pid']
        if type(pid) is not int or pid<=0:raise ValueError('Explicit server PID required')
        process=psutil.Process(pid)
        created=document['create_time']
        if process.create_time()!=created:raise ValueError('Shared server PID generation changed')
        if Path(process.exe()).resolve()!=home/'build'/'Release'/'god2-server.exe':
            raise ValueError('Shared process is not the owned server executable')
        config=Path(document['config']).resolve(strict=True)
        if not config.is_relative_to(home/'artifacts'/'runs'):
            raise ValueError('Shared config must be isolated in run evidence')
        raw=config.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=document['config_sha256']:
            raise ValueError('Shared configuration changed')
        command=process.cmdline()
        if command.count('--config')!=1 or command.index('--config')+1>=len(command):
            raise ValueError('Shared server command lacks a unique config')
        launched=Path(command[command.index('--config')+1])
        if not launched.is_absolute():launched=Path(process.cwd())/launched
        if launched.resolve()!=config:raise ValueError('Shared config is not the process launch config')
        settings=json.loads(raw)
        dev=settings['development']
        if bool(document.get('observe_battle'))!=bool(dev.get('diagnostic_visibility_battle')):
            raise ValueError('Shared battle manifest/config mismatch')
        if bool(document.get('persist_battle'))!=bool(dev.get('diagnostic_battle_resources')):
            raise ValueError('Shared persistence manifest/config mismatch')
        if bool(document.get('checkpoint_battle'))!=bool(dev.get('diagnostic_visibility_checkpoint')):
            raise ValueError('Shared checkpoint manifest/config mismatch')
        if bool(document.get('skill_battle'))!=bool(dev.get('diagnostic_visibility_skill_recovery')):
            raise ValueError('Shared skill manifest/config mismatch')
        if settings['server']['host']!='127.0.0.1' or settings['server']['port']!=2592:
            raise ValueError('Shared native probe requires IPv4 loopback port2592')
        if not all(dev.get(key) is True for key in ('diagnostic_player_visibility','recovered_movement',
                'recovered_world_entry','recovered_dual_connection','recovered_account_auth','recovered_character_creation')):
            raise ValueError('Shared server lacks isolated visibility configuration')
        database=Path(settings['database']['path'])
        if not database.is_absolute():database=home/database
        if (dev.get('mock_login') is not False or database.name!='player-visibility-diagnostic.db'
                or not database.resolve().is_relative_to(config.parent)):
            raise ValueError('Shared server database is not isolated')
        ports=document['ports']
        if (not isinstance(ports,list) or len(ports)!=2 or len(set(ports))!=2 or 2592 not in ports
                or any(type(port) is not int or not 1<=port<=65535 for port in ports)):
            raise ValueError('Two distinct explicit listener ports required')
        listeners={(item.laddr.ip,item.laddr.port) for item in process.net_connections(kind='tcp')
                   if item.status==psutil.CONN_LISTEN}
        if listeners!={('127.0.0.1',port) for port in ports}:
            raise ValueError('Shared process listeners do not match the manifest')
        self.process=BorrowedProcess(process,created)
        if self.process.poll() is not None:raise ValueError('Shared server exited during attachment')
        self.allowed_ports=set(ports)
        self.events=[]
        self.hello_gate=threading.Event()
        self.closed=False
        self.long_lived=False
        self.document=document
        self.manifest=path
        self.database=database.resolve()

    def verify_client_profile(self,client):
        client=Path(client).resolve(strict=True)
        profile=self.document.get('client_profile',{})
        if Path(profile.get('root','')).resolve()!=client:
            raise ValueError('Shared client profile root mismatch')
        files=profile.get('sha256',{})
        required={'config/display.settings','ctserver.ini','ddraw.ini'}
        if not isinstance(files,dict) or set(files)!=required:
            raise ValueError('Complete shared client profile hashes required')
        for name,expected in files.items():
            path=(client/name).resolve(strict=True)
            if not path.is_relative_to(client) or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError('Shared client profile changed')
        if self.process.poll() is not None:raise ValueError('Shared profile owner server has stopped')

    @contextmanager
    def client_profile(self,client):
        self.verify_client_profile(client)
        prior=os.environ.get('GOD2_CLASSIC_RESOLUTION')
        os.environ['GOD2_CLASSIC_RESOLUTION']='800x600'
        try:
            yield
        finally:
            if prior is None:os.environ.pop('GOD2_CLASSIC_RESOLUTION',None)
            else:os.environ['GOD2_CLASSIC_RESOLUTION']=prior
            self.verify_client_profile(client)

    def close(self):
        # The owner, not an attached client probe, controls server termination.
        self.closed=True
