"""Back up and smoke this release against a cloned persistent configuration."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'artifacts/releases/owned-inventory-20260926-01'
CONFIG = ROOT / 'artifacts/releases/town-chat-welcome-20260924/server-config.json'
BINARY = ROOT / 'build-town-visibility/Release/god2-server-inventory-v3.exe'
LIVE_BINARY = ROOT / 'build-town-visibility/Release/god2-server.exe'
TABLES = ('accounts', 'recovered_characters', 'recovered_positions',
          'character_resources', 'diagnostic_inventory_slots',
          'diagnostic_town_guide_progress', 'diagnostic_town_guide_reward')


def snapshot(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        if db.execute('pragma quick_check').fetchone() != ('ok',):
            raise RuntimeError('SQLite integrity failed')
        result = {}
        for table in TABLES:
            rows = db.execute(f'select * from {table} order by 1,2').fetchall()
            result[table] = {'rows': len(rows), 'sha256': hashlib.sha256(repr(rows).encode()).hexdigest()}
        return result


def main():
    HERE.mkdir(parents=True, exist_ok=False)
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    live_db = Path(config['database']['path'])
    backup = HERE / 'players-before.sqlite'
    with closing(sqlite3.connect(live_db.resolve().as_uri()+'?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
    before = snapshot(backup)
    shutil.copy2(LIVE_BINARY, HERE / 'god2-server-before.exe')
    shutil.copy2(CONFIG, HERE / 'live-config-before.json')
    stage = HERE / 'town-diagnostic-accounts.db'
    shutil.copy2(backup, stage)
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    config['server']['port'] = port
    config['database']['path'] = str(stage)
    config['logging']['file'] = str(HERE / 'stage-server.log')
    stage_config = HERE / 'stage-config.json'
    stage_config.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    with (HERE / 'stage-stdout.log').open('wb') as output:
        process = subprocess.Popen([str(BINARY), '--config', str(stage_config), '--run-for', '25'],
            cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic()+8
            while True:
                if process.poll() is not None:
                    raise RuntimeError('Staged server exited before native greeting')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.25) as peer:
                        peer.settimeout(2)
                        greeting = bytearray()
                        while len(greeting)<19:
                            chunk = peer.recv(19-len(greeting))
                            if not chunk:
                                raise RuntimeError('Truncated greeting')
                            greeting.extend(chunk)
                        if greeting[:2] != b'\x13\x00':
                            raise RuntimeError('Invalid native greeting')
                        break
                except OSError:
                    if time.monotonic()>=deadline:
                        raise RuntimeError('Staged server did not bind')
                    time.sleep(.05)
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
    after = snapshot(stage)
    if after != before:
        raise RuntimeError('Staged startup changed player state')
    result = {'stage_accepted': True, 'native_seed_bytes': len(greeting),
              'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              'config_sha256': hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
              'preserved_tables': before, 'persistent_deployed': False}
    (HERE / 'stage-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='preserved_tables'}))


if __name__ == '__main__':
    main()
