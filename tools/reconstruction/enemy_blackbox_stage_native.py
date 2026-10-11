"""Prepare owner-authorized disposable native experiment, never run live gameplay.

Copies the retained server, a hash-qualified historical private-desktop runner,
and the currently installed client into the research directory. Only the client
COPY's startup-port immediate changes. Creates a NEW isolated schema with the
retained server's migrate-only mode; seeds two clearly marked temporary fixture
accounts/characters, not original-client creation acceptance. No existing DB is
read, copied, or replaced. No server is started listening and no client launches.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sqlite3
import struct
import subprocess

from tools.reconstruction.archive_inputs import ArchivedInputs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/research/enemy-blackbox-20261006/native-bootstrap'
SERVER = ROOT / 'build-town-visibility/Release/god2-server.exe'
CLIENT = ROOT.parent / 'God2/God2.exe'
SERVER_SHA = '1062075f3d2063650a28adc4c9053ac5a68c646dbbb4ea0229af28bfdb8251c9'
CLIENT_SHA = 'c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
RUNNER_REL = 'artifacts/playtests/private-inventory-move-20260926-03/private-runner.exe'
RUNNER_SHA = '8a4bd51dcf48753f5934fb1088d4aac10603ad8506ecc988a07d83febe878ef4'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise ValueError('Fresh experiment directory required; inspect prior output instead of overwriting')
    if digest(SERVER) != SERVER_SHA or digest(CLIENT) != CLIENT_SHA:
        raise ValueError('Current source executable identity differs')
    OUT.mkdir(parents=True)
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    reader = ArchivedInputs()
    try:
        raw = reader.read(RUNNER_REL)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != RUNNER_SHA:
        raise ValueError('Retained runner identity differs')
    (OUT / 'private-runner.exe').write_bytes(raw)
    shutil.copyfile(SERVER, OUT / 'god2-server.exe')
    raw_client = CLIENT.read_bytes()
    signature = bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00')
    if raw_client.count(signature) != 1:
        raise ValueError('Native startup-port immediate is not unique')
    offset = raw_client.index(signature) + 1
    cloned_client = bytearray(raw_client)
    struct.pack_into('<I', cloned_client, offset, port)
    (OUT / 'God2-enemy-blackbox.exe').write_bytes(cloned_client)
    (OUT / 'bootstrap.lua').write_text('log("Isolated enemy blackbox bootstrap; CUSTOM_TEST_NOT_NATIVE")\n', encoding='utf-8')
    config = {
        'server': {'name': 'Enemy blackbox CUSTOM_TEST_NOT_NATIVE', 'host': '127.0.0.1',
                   'port': port, 'character_port': 0, 'max_sessions': 8, 'worker_threads': 2},
        'protocol': {'name': 'GOD2', 'mode': 'god2_legacy_character_list_candidate',
                     'allow_unverified_legacy': True, 'packet_header': 'uint16_length_seed_checksum',
                     'encryption': 'seed_fixture', 'compression': 'none', 'packet_dump': False},
        'database': {'type': 'sqlite', 'path': str(OUT / 'diagnostic-accounts.db')},
        'lua': {'bootstrap': str(OUT / 'bootstrap.lua'), 'script_root': str(ROOT / 'scripts'), 'hot_reload': False},
        'logging': {'level': 'debug', 'file': str(OUT / 'native-server.log')},
        'text': {'dictionary_root': str(ROOT / 'resources/opencc')},
        'development': {'mock_login': False, 'recovered_account_auth': True,
                        'local_account_registration': False, 'recovered_character_creation': True,
                        'recovered_dual_connection': True, 'recovered_world_entry': True,
                        'recovered_movement': True, 'recovered_navigation': str(ROOT / 'artifacts/world-atlas/town-2-4.json'),
                        'diagnostic_battle_transition': True, 'diagnostic_battle_participants': True,
                        'diagnostic_battle_player_appearance': True, 'diagnostic_battle_animations': True,
                        'diagnostic_battle_skill_seed': True, 'diagnostic_battle_skill_settlement': True,
                        'diagnostic_battle_rounds': 1, 'diagnostic_battle_terminal': True,
                        'diagnostic_battle_after_movement': True}}
    path = OUT / 'server-config.json'
    path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    env = os.environ.copy(); env['GOD2_LOG_FILE_ONLY'] = '1'
    with (OUT / 'migration.log').open('wb') as log:
        migration = subprocess.run([str(OUT / 'god2-server.exe'), '--config', str(path), '--migrate-only'],
                                   cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    report = {'origin': 'CUSTOM_TEST_NOT_NATIVE', 'migration_exit_code': migration.returncode,
              'live_server_started': False, 'native_client_launched': False,
              'native_ui_account_creation': False, 'native_pk_or_pve': False,
              'database_new_not_copied': True, 'port': port,
              'port_is_not_reserved_for_future_launch': True,
              'source_server_sha256': SERVER_SHA, 'source_client_sha256': CLIENT_SHA,
              'clone_client_sha256': digest(OUT / 'God2-enemy-blackbox.exe'),
              'client_startup_patch_offset': hex(offset), 'client_startup_patch_before': raw_client[offset:offset+4].hex(),
              'client_startup_patch_after': bytes(cloned_client[offset:offset+4]).hex(),
              'runner_sha256': RUNNER_SHA, 'runner_archive_reference': RUNNER_REL,
              'source_server_preserved': digest(SERVER) == SERVER_SHA,
              'source_client_preserved': digest(CLIENT) == CLIENT_SHA,
              'actors': [], 'remaining': [
                  'Prepare a locale profile and resource working-directory for the disposable client; never launch the installed client against the private port.',
                  'Launch a newly owned hidden desktop and this own server; confirm the current executable PID/create-time and bound private port.',
                  'Login a newly seeded account and capture its current native world/battle state, not old character4/5 fixtures.',
                  'The retained native actor constructor has no runtime knobs for four dimensions/five elements/carried-skill list; these remain sidecar controls, not applied native gameplay stats.',
                  'A new configurable native experiment route or separately qualified controlled projection is required for those fields.']}
    if migration.returncode == 0:
        with sqlite3.connect(OUT / 'diagnostic-accounts.db') as db:
            db.execute('PRAGMA foreign_keys=ON')
            for index in range(2):
                username = 'bb' + secrets.token_hex(5)
                password = secrets.token_hex(6)
                salt = secrets.token_bytes(16)
                derived = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000, 32)
                stored = 'god2$pbkdf2-sha256$v1$600000$' + salt.hex() + '$' + derived.hex()
                account = db.execute('INSERT INTO accounts(username,password_hash) VALUES(?,?)',
                                     ('god2-bytes:' + username.encode().hex(), stored)).lastrowid
                name = ('Blackbox' + str(index + 1)).encode()
                profile = bytearray(40); profile[:len(name)] = name
                # Deliberately synthetic fresh appearance/profile; no old saved profile is reused.
                character = db.execute('INSERT INTO recovered_characters(account_id,slot,profile,name_bytes,name_codepage) VALUES(?,0,?,?,950)',
                                       (account, bytes(profile), name)).lastrowid
                report['actors'].append({'account_id': account, 'character_id': character,
                                         'temporary_fixture_seed': True,
                                         'name': name.decode(), 'profile_origin': 'CUSTOM_TEST_NOT_NATIVE',
                                         'profile_sha256': hashlib.sha256(profile).hexdigest()})
                # Disposable credentials remain exclusively in this private fixture directory,
                # never printed, placed in packet observations, or used on any other service.
                with (OUT / ('private-credentials-' + str(index + 1) + '.json')).open('x', encoding='utf-8') as secret:
                    json.dump({'username': username, 'password': password}, secret)
            db.commit()
            report['schema_history'] = [list(row) for row in db.execute('SELECT * FROM schema_migrations ORDER BY version')]
            report['schema_version'] = report['schema_history'][-1][0]
            db.execute("CREATE TABLE enemy_blackbox_fixture_origin (character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id), origin TEXT NOT NULL CHECK(origin='CUSTOM_TEST_NOT_NATIVE'), controls_json TEXT NOT NULL, applied_to_native_gameplay INTEGER NOT NULL CHECK(applied_to_native_gameplay=0))")
            controls_path = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/identifiability-result.json'
            controls = json.loads(controls_path.read_text('utf-8'))['controls']
            for actor, key in zip(report['actors'], ('A', 'B')):
                db.execute('INSERT INTO enemy_blackbox_fixture_origin VALUES(?,?,?,0)',
                           (actor['character_id'], 'CUSTOM_TEST_NOT_NATIVE', json.dumps(controls[key], sort_keys=True)))
            db.commit()
            report['control_sidecar_origin'] = 'CUSTOM_TEST_NOT_NATIVE'
            report['sidecar_controls_applied_to_native_gameplay'] = False
    (OUT / 'preparation-result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'migration_exit': migration.returncode,
                      'new_private_fixture_characters': len(report['actors']),
                      'live_server_started': False, 'native_pk_or_pve': False}))


if __name__ == '__main__':
    main()
