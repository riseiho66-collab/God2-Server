"""Disposable two-client native remote DA acceptance on one hidden desktop.

Only CUSTOM-0046/0047 fixture weapons and mappings are used. ReadProcessMemory
is read-only; input uses PID-owned hidden windows. No screenshots or desktop
switches. The existing owned-companion tools are imported, never modified.
Run as a module with --output and --server-candidate. --prepare-only creates
the migrated isolated fixture without launching either client.
"""
import argparse
from contextlib import closing
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import struct
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))
import psutil
from tools.strike_lab import run_private_owned_companions as fixture
import private_owned_companions_ui as owned
from private_inventory_memory import kernel, read, Region
from private_inventory_move_ui import desktop_names, wait_until, require
from private_potion_ui import user, click, type_ascii
from private_map_item_current_ui import double_click_message

HERO_SHA = 'df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359'
STABLE_KEYS = ('role_resources', 'role_auxiliary', 'deity_count',
               'deity_selected_key', 'deity_keys', 'deity_vitals', 'pet_slots', 'pet_cache')


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def ro(db):
    return sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True)


def exact(handle, address, size):
    value = read(handle, address, size)
    require(value is not None and len(value) == size, f'SHORT_READ_{address:x}_{size}')
    return value


def find_ui(handle, identity, expected_map=(0,3,4)):
    """Locate pinned world's embedded UI structurally, without a fixture item.

    46BCC0 embeds UI at W+A7F2F6C; local role is W+1539683C and
    UI+86888 publishes role+90. Require identity and current map as well.
    """
    needle = struct.pack('<IIH', *expected_map)
    address = 0x10000
    scanned = 0
    matches = set()
    while address < 0x80000000 and scanned < 800 * 1024 * 1024:
        region = Region()
        if not kernel.VirtualQueryEx(handle, address, c.byref(region), c.sizeof(region)):
            break
        base = region.BaseAddress or address
        end = min(base + region.RegionSize, 0x80000000)
        if region.State == 0x1000 and not region.Protect & 0x101:
            offset, tail = base, b''
            while offset < end:
                size = min(1024 * 1024, end - offset)
                raw = read(handle, offset, size)
                if raw:
                    scanned += len(raw)
                    combined = tail + raw
                    at = combined.find(needle)
                    while at >= 0:
                        role = offset - len(tail) + at - 0x10
                        world = role - 0x1539683c
                        ui = world + 0xa7f2f6c
                        if world > 0x10000 and read(handle, role, 4) == struct.pack('<I', identity):
                            if read(handle, ui + 0x86888, 4) == struct.pack('<I', role + 0x90):
                                matches.add(ui)
                        at = combined.find(needle, at + 1)
                    tail = combined[-9:]
                offset += size
        address = end if end > address else address + 0x1000
    require(len(matches) == 1, f'UI_STRUCTURE_MATCHES_{identity}_{len(matches)}')
    return matches.pop()


def window_for(pid):
    matches = []
    @c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    def visit(hwnd, unused):
        owner = w.DWORD()
        user.GetWindowThreadProcessId(hwnd, c.byref(owner))
        if owner.value == pid:
            name = c.create_unicode_buffer(128)
            user.GetClassNameW(hwnd, name, len(name))
            if name.value == 'XianJieWndClass':
                matches.append(hwnd)
        return True
    user.EnumWindows(visit, 0)
    require(len(matches) <= 1, 'MULTIPLE_WINDOWS_FOR_OWNED_PID')
    return matches[0] if matches else None


def remote(handle, ui, identity):
    role = int.from_bytes(exact(handle, ui + 0x86888, 4), 'little') - 0x90
    world = role - 0x1539683c
    manager = world + 0x15383410
    display = int.from_bytes(exact(handle, manager + 8, 4), 'little')
    require(display == world + 0xaba32e0, 'REMOTE_DISPLAY_POOL_BINDING')
    records = exact(handle, manager + 0x18, 128 * 0x268)
    rows = []
    for i in range(128):
        row = records[i * 0x268:(i + 1) * 0x268]
        if struct.unpack_from('<I', row)[0] != identity:
            continue
        renderer = struct.unpack_from('<h', row, 0x48)[0]
        texts = [row[o:o + 16].split(b'\0')[0].hex() for o in (4, 20, 36)]
        labels = []
        if 0 <= renderer < 4096:
            label = exact(handle, display + renderer * 0xa7e0 + 0x70, 51)
            labels = [label[o:o + 17].split(b'\0')[0].hex() for o in (0, 17, 34)]
        rows.append({'identity': identity, 'slot': i, 'world': hex(world),
            'entry': hex(manager + 0x18 + i * 0x268), 'renderer': renderer,
            'text_fields': texts, 'display_texts': labels,
            'x': struct.unpack_from('<i', row, 0x64)[0], 'y': struct.unpack_from('<i', row, 0x68)[0],
            'movement': struct.unpack_from('<H', row, 0x38)[0],
            'status': row[0x60:0x62].hex(), 'spawn_components': row[0x250:0x258].hex(),
            'scalar5': row[0x264], 'scalar6': row[0x265],
            'live_components': [{'handle': struct.unpack_from('<h', row, 0x228 + 6*j)[0],
                                 'variant': row[0x22c + 6*j]} for j in range(4)]})
    require(len(rows) <= 1, 'DUPLICATED_REMOTE_IDENTITY')
    return rows[0] if rows else None


def weapon_resource(handle, world, components, live):
    """Current 61270->63DE0->526C0 ordinary weapon table/cache binding."""
    from omega_assets import decode_csvz
    source = fixture.LIVE_CLIENT.parent / 'Data2/Patch/HeroDoll.csvZ'
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == HERO_SHA, 'HERODOLL_SOURCE_PIN')
    lines = decode_csvz(raw).splitlines()
    start, count = (int(lines[0].split(b',')[i]) for i in (2, 4))
    key = f'r{(components[6]&15)+1}w{components[6]>>4}{components[7]&31:02d}'
    matches = [(i, line.split(b',')) for i, line in enumerate(lines[start-1:])
               if b''.join(line.split(b',')[:2]).decode('ascii') == key]
    require(len(matches) == 1, 'HERODOLL_KEY_NOT_UNIQUE')
    ordinal, fields = matches[0]
    manager = world + 0xaa364b8
    bank = int.from_bytes(exact(handle, manager + 0x16ce18, 4), 'little')
    require(bank < 2, 'HERODOLL_BANK_SCOPE')
    hero = manager + bank * 0xad610 + 0x682e0 + 0x12d78
    records, loaded = struct.unpack('<II', exact(handle, hero + 0x121ec, 8))
    require(records > 0x10000 and loaded == count, 'HERODOLL_TABLE_COUNT')
    record = exact(handle, records + ordinal * 44, 44)
    filename = record[:30].split(b'\0')[0]
    cached = int.from_bytes(record[30:32], 'little')
    require(filename == fields[3], 'HERODOLL_FILENAME_MISMATCH')
    return {'key': key, 'filename': filename.decode('ascii'), 'source_line': start + ordinal,
            'source_sha256': HERO_SHA, 'cached_handle': cached, 'live_handle': live['handle'],
            'matches': cached == live['handle'], 'record': hex(records + ordinal * 44), 'bank': bank}


def check_remote(client, row, logical, name, baseline=None, spawned=False):
    require(row is not None and row['identity'] == 4, 'PEER_ACTOR4_MISSING')
    # 5097D0 centers short names with leading ASCII spaces in its 17-byte cell.
    require(name in row['text_fields'] and name in [bytes.fromhex(x).strip(b' ').hex() for x in row['display_texts']], 'PEER_NAME_DISPLAY_MISMATCH')
    require(0 <= row['renderer'] < 4096, 'PEER_RENDERER_MISSING')
    require(row['scalar5'] == logical[5] and row['scalar6'] == logical[6], 'PEER_DA_SCALAR_MISMATCH')
    if spawned:
        require(row['spawn_components'] == logical[7:].hex(), 'PEER_SPAWN_AFTERSTATE_MISMATCH')
    for i, comp in enumerate(row['live_components']):
        require(0 <= comp['handle'] < 512 and comp['variant'] == logical[8+2*i] >> 5,
                f'PEER_COMPONENT_{i}_INVALID')
        if baseline and i < 3:
            require(comp == baseline['live_components'][i], 'PEER_OTHER_COMPONENT_CHANGED')
    if baseline:
        for field in ('text_fields', 'display_texts', 'x', 'y', 'status'):
            require(row[field] == baseline[field], 'PEER_UNRELATED_' + field)
    binding = weapon_resource(client['handle'], int(row['world'], 16), logical[7:], row['live_components'][3])
    row['weapon_resource'] = binding
    return binding['matches']


def db_stable(db):
    with closing(ro(db)) as connection:
        result = {}
        for table in ('character_resources', 'character_role_snapshots', 'character_deities',
                      'character_deity_selection', 'character_pet2_slots', 'character_role_auxiliary_snapshots'):
            rows = connection.execute(f'SELECT * FROM {table} WHERE character_id IN (4,5) ORDER BY 1,2').fetchall()
            result[table] = [[v.hex() if isinstance(v, bytes) else v for v in row] for row in rows]
        return result


def close_client(client):
    if client.get('handle'):
        kernel.CloseHandle.argtypes = [w.HANDLE]
        kernel.CloseHandle(client.pop('handle'))
    process = client['process']
    if process.poll() is None:
        hwnd = window_for(process.pid)
        if hwnd:
            user.PostMessageW(hwnd, 0x10, 0, 0)
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)


def worker(args):
    result = {'accepted': False, 'authority': 'CUSTOM_TEST_NOT_NATIVE', 'stages': [],
              'actual_god_preservation_tested': False, 'rendered_pixels_tested': False}
    clients = []
    before = desktop_names()
    def checkpoint():
        dump(args.output / 'ui-result.json', result)
    try:
        require(before['current'].startswith('God2Lab-') and before['input'] != before['current'], 'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before'] = before
        def launch(identity):
            # A child inherits this hidden desktop; no visible shell or switch.
            process = subprocess.Popen([str(fixture.CLIENT), '127.0.0.1', '127.0.0.1', '6001', '1'],
                cwd=fixture.CLIENT.parent, creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            client = {'process': process, 'identity': identity}
            clients.append(client)
            result.setdefault('owned_client_pids', []).append(process.pid)
            checkpoint()
            hwnd = wait_until(lambda: window_for(process.pid), 35, f'WINDOW_{identity}_MISSING')
            client['hwnd'] = hwnd
            time.sleep(2); click(hwnd, 512, 464); time.sleep(3)
            click(hwnd, 437, 232); type_ascii(hwnd, 'codexslow' if identity == 4 else 'codexfixed')
            click(hwnd, 437, 263); type_ascii(hwnd, 'labtest2345')
            click(hwnd, 452, 304); time.sleep(4)
            click(hwnd, 330, 145); click(hwnd, 452, 413); time.sleep(4)
            click(hwnd, 330, 150); click(hwnd, 452, 376); time.sleep(4)
            click(hwnd, 452, 370); time.sleep(8)
            require(process.poll() is None, f'CLIENT_{identity}_EXITED')
            handle = kernel.OpenProcess(0x1010, False, process.pid)
            require(handle, 'READONLY_PROCESS_OPEN_FAILED')
            client['handle'] = handle
            client['ui'] = find_ui(handle, identity)
            state = owned.native(handle, client['ui'])
            require(state['world_map'] == {'kind': 0, 'area': 4, 'scene': 3}, 'KUNLUN_REQUIRED')
            require(state['deity_count'] == 0, 'NO_GOD_FIXTURE_REQUIRED')
            client['stable'] = {k: state[k] for k in STABLE_KEYS}
            return client
        actor = launch(4)
        peer = launch(5)
        database = args.output / 'town-diagnostic-accounts.db'
        with closing(ro(database)) as db:
            names = dict(db.execute('SELECT id,name_bytes FROM recovered_characters WHERE id IN (4,5)'))
        peer_before = wait_until(lambda: remote(peer['handle'], peer['ui'], 4), 15, 'PEER_CANNOT_SEE_ACTOR4')
        actor_before = wait_until(lambda: remote(actor['handle'], actor['ui'], 5), 15, 'ACTOR_CANNOT_SEE_PEER5')
        result['initial_remote_observation'] = {'peer_sees_actor':peer_before, 'actor_sees_peer':actor_before,
            'expected_names':{str(k):v.hex() for k,v in names.items()}}
        checkpoint()
        require(names[5] in [bytes.fromhex(x).strip(b' ') for x in actor_before['display_texts']], 'ACTOR_CANNOT_DISPLAY_PEER_NAME')
        initial_db = owned.saved_weapon_appearance(database)
        initial_native = owned.native_weapon_appearance(actor['handle'], actor['ui'])
        owned.check_weapon_appearance(initial_db, initial_native, initial_db, initial_native, 0, 1)
        require(check_remote(peer, peer_before, bytes.fromhex(initial_db['logical_hex']), names[4].hex(), spawned=True), 'INITIAL_PEER_RESOURCE_MISMATCH')
        stable_db = db_stable(database)
        result['before'] = {'peer_sees_actor': peer_before, 'actor_sees_peer': actor_before,
                            'owned_appearance': initial_db, 'actor_native': initial_native, 'related_rows': stable_db}
        click(actor['hwnd'], 708, 584); time.sleep(2)
        widget = int.from_bytes(exact(actor['handle'], actor['ui'] + 0x232dc8, 2), 'little', signed=True)
        for step, source in enumerate((0, 1, 34, 1), 1):
            prior = owned.saved_weapons(database)
            destination = 34 if source != 34 else next(i for i in range(30) if prior[str(i)]['count'] == 0)
            point = owned.control_point(actor['handle'], actor['ui'], widget, source)
            double_click_message(actor['hwnd'], *point)
            def changed():
                inventory = owned.saved_weapons(database)
                appearance = owned.saved_weapon_appearance(database)
                row = remote(peer['handle'], peer['ui'], 4)
                result['last_observed'] = {'step': step, 'appearance': appearance, 'peer': row}
                if not owned.weapon_after_state(prior, inventory, source, destination):
                    return None
                if not owned.weapon_slots_agree(owned.native_weapon_slots(actor['handle'], actor['ui']), inventory):
                    return None
                if appearance['revision'] != step + 1:
                    return None
                current = owned.native_weapon_appearance(actor['handle'], actor['ui'])
                if current['logical_hex'] != appearance['logical_hex']:
                    return None
                owned.check_weapon_appearance(appearance, current, initial_db, initial_native, inventory['34']['item'], step+1)
                if not check_remote(peer, row, bytes.fromhex(appearance['logical_hex']), names[4].hex(), peer_before):
                    return None
                for client in (actor, peer):
                    value = owned.native(client['handle'], client['ui'])
                    require({k: value[k] for k in STABLE_KEYS} == client['stable'], 'RELATED_NATIVE_STATE_CHANGED')
                require(db_stable(database) == stable_db, 'RELATED_DATABASE_ROWS_CHANGED')
                other = remote(actor['handle'], actor['ui'], 5)
                require(other is not None and all(other[k] == actor_before[k] for k in
                    ('text_fields', 'display_texts', 'x', 'y', 'live_components', 'spawn_components')), 'OTHER_ACTOR_CHANGED')
                return {'step': step, 'source': source, 'destination': destination, 'appearance': appearance,
                        'inventory': inventory, 'actor_native': current, 'peer_native': row,
                        'related_native_and_saved_state_unchanged': True}
            result['stages'].append(wait_until(changed, 12, f'PEER_DA_STEP_{step}_FAILED'))
            checkpoint()
        # Observer reconnect qualifies fresh6F afterstate, not merely DA cache.
        close_client(peer)
        wait_until(lambda: remote(actor['handle'], actor['ui'], 5) is None, 12, 'DISCONNECTED_PEER_NOT_REMOVED')
        peer = launch(5)
        def respawned():
            row = remote(peer['handle'], peer['ui'], 4)
            if not row:
                return None
            latest = owned.saved_weapon_appearance(database)
            if not check_remote(peer, row, bytes.fromhex(latest['logical_hex']), names[4].hex(), spawned=True):
                return None
            require(latest == result['stages'][-1]['appearance'], 'RELOGIN_CHANGED_APPEARANCE')
            require(db_stable(database) == stable_db, 'RELOGIN_CHANGED_RELATED_ROWS')
            return row
        result['peer_relogin'] = wait_until(respawned, 15, 'PEER_RELOGIN_AFTERSTATE_FAILED')
        require(remote(actor['handle'], actor['ui'], 5) is not None, 'RELOGGED_PEER_NOT_VISIBLE_TO_ACTOR')
        # Native movement and periodic clock still run after the four DA updates.
        click(actor['hwnd'], 708, 584); time.sleep(1)
        click(actor['hwnd'], 460, 340)
        def moved():
            with closing(ro(database)) as db:
                position = db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=4').fetchone()
            row = remote(peer['handle'], peer['ui'], 4)
            if not position or position[2:4] == (126,126) or row is None:
                return None
            if (row['x'], row['y']) != position[2:4]:
                return None
            return {'saved_position': list(position), 'peer': row}
        result['movement'] = wait_until(moved, 15, 'REMOTE_MOVEMENT_NOT_COMMITTED')
        clocks = [owned.native(x['handle'], x['ui'])['world_clock'] for x in (actor, peer)]
        def clock_changed():
            values = [owned.native(x['handle'], x['ui'])['world_clock'] for x in (actor, peer)]
            return values if all(a[0] != b[0] and a[0] != 0 for a,b in zip(values, clocks)) else None
        result['clock'] = {'before': clocks, 'after': wait_until(clock_changed, 12, 'CLOCK_SYNC_MISSING')}
        for client in (actor, peer):
            value = owned.native(client['handle'], client['ui'])
            require({k: value[k] for k in STABLE_KEYS} == client['stable'], 'FINAL_NATIVE_STATE_CHANGED')
        require(db_stable(database) == stable_db, 'FINAL_RELATED_ROWS_CHANGED')
        result['accepted'] = True
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
        result['traceback'] = traceback.format_exc()
    finally:
        for client in reversed(clients):
            try:
                close_client(client)
            except Exception as error:
                result.setdefault('cleanup_errors', []).append(str(error))
        result['desktop_after'] = desktop_names()
        result['all_owned_clients_closed'] = all(x['process'].poll() is not None for x in clients)
        result['accepted'] = bool(result['accepted'] and result['desktop_after'] == before and result['all_owned_clients_closed'] and not result.get('cleanup_errors'))
        checkpoint()
    return 0 if result['accepted'] else 1


def prepare(args):
    here = args.output.resolve()
    here.mkdir(parents=True, exist_ok=False)
    require(fixture.sha(fixture.LIVE_CLIENT) == fixture.CURRENT_CLIENT_SHA, 'LIVE_CLIENT_PIN')
    raw = fixture.LIVE_CLIENT.read_bytes()
    private = fixture.CLIENT.read_bytes()
    site = raw.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'))
    expected = bytearray(raw); expected[site+1:site+5] = struct.pack('<I', 2598)
    require(private == expected, 'PRIVATE_CLIENT_NOT_EXACT_PORT_ONLY_COPY')
    database = here / 'town-diagnostic-accounts.db'
    with closing(ro(fixture.SOURCE_DB)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    config = json.loads(fixture.CONFIG.read_text('utf-8'))
    config['database']['path'] = str(database)
    config['logging']['file'] = str(here / 'server.log')
    config['server']['host'] = '127.0.0.1'; config['server']['port'] = 2598
    dev = config['development']
    for key, value in list(dev.items()):
        if key.startswith('diagnostic_') and isinstance(value, bool):
            dev[key] = False
    dev['diagnostic_town'].update(spawn_guides=True, quest_progress=False, map_probe=False,
        battle_after_quest=False, door_after_battle=False, native_npc_placements_only=True, player_visibility=True)
    dev.update(diagnostic_owned_weapon_appearance=True,
               diagnostic_player_visibility=False, diagnostic_remote_actor=False,
               diagnostic_remote_actor_language=0, native_monster_placements_only=True)
    config['world'] = {'new_character_birthplace': {'area':4, 'scene':3, 'kind':0, 'x':126, 'y':126,
        'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'), 'coordinate_authority':'CUSTOM-0040'},
        'owned_weapon_transfers': {'enabled':True}, 'owned_player_appearance': {'enabled':True},
        'clock': {'enabled':True, 'sync_seconds':5}}
    dump(here/'server-config.json', config)
    env = os.environ.copy(); env['GOD2_LOG_FILE_ONLY'] = '1'
    with (here/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate), '--config', str(here/'server-config.json'), '--migrate-only'],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW, check=True, timeout=20)
    from tools.strike_lab import import_native_weapons
    with closing(sqlite3.connect(database)) as db:
        import_native_weapons.import_catalog(db, records=import_native_weapons.cached_records(ROOT/'artifacts/research/native-weapons-20260926/records.json'))
        for identity in (4,5):
            db.execute('DELETE FROM recovered_positions WHERE character_id=?', (identity,))
            db.execute('INSERT INTO character_resources VALUES(?,52,120,26,80,1,?)', (identity,'CUSTOM-0012'))
            role=bytearray(25); role[0]=0x22; role[1]=1
            struct.pack_into('<4H',role,5,10,10,10,10); struct.pack_into('<II',role,17,120,80)
            db.execute('INSERT INTO character_role_snapshots VALUES(?,?,1,?)', (identity,bytes(role),'CUSTOM-0013'))
            for table in ('character_deity_selection','character_deities','character_pet2_slots'):
                db.execute(f'DELETE FROM {table} WHERE character_id=?', (identity,))
        weapons = fixture.seed_weapon_transfers(db)
        appearance = fixture.seed_weapon_appearance(db)
        db.commit()
        require(db.execute('PRAGMA quick_check').fetchone() == ('ok',), 'CLONE_INTEGRITY_FAILED')
    dump(here/'fixture.json', {'weapons':weapons, 'appearance':appearance, 'characters':[4,5],
        'scope':'Disposable noGod ordinary unmounted CUSTOM test only; no native item-to-appearance claim'})


def owner(args):
    args.output = args.output.resolve(); args.server_candidate = args.server_candidate.resolve()
    paths = {'source_db':fixture.SOURCE_DB, 'live_client':fixture.LIVE_CLIENT, 'private_client':fixture.CLIENT}
    result = {'accepted':False, 'before':{key:fixture.sha(path) for key,path in paths.items()},
              'server_sha256':fixture.sha(args.server_candidate)}
    server = runner = None
    try:
        # Fail before launch if another service already owns the private port.
        with socket.socket() as probe:
            require(probe.connect_ex(('127.0.0.1',2598)) != 0, 'PRIVATE_PORT_ALREADY_IN_USE')
        prepare(args)
        if args.prepare_only:
            result['prepared_only'] = True
            return 0
        env=os.environ.copy(); env['GOD2_LOG_FILE_ONLY']='1'
        env.pop('GOD2_PRIVATE_SIDECAR_COMMAND', None)
        with (args.output/'stdout.log').open('wb') as log, (args.output/'runner.log').open('wb') as runner_log:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','300'],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['server_pid']=server.pid
            def listening():
                require(server.poll() is None, 'SERVER_EXITED')
                with socket.socket() as probe:
                    return probe.connect_ex(('127.0.0.1',2598)) == 0
            wait_until(listening,10,'SERVER_NOT_LISTENING')
            command=[str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),
                     '--worker','--output',str(args.output)]
            runner=subprocess.Popen(command,cwd=ROOT,env=env,stdout=runner_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['runner_pid']=runner.pid; result['runner_exit']=runner.wait(timeout=260)
            result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
            result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
    except Exception as error:
        result['error']=f'{type(error).__name__}: {error}'
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try: child.terminate()
                    except psutil.NoSuchProcess: pass
                process.terminate(); process.wait(timeout=5)
                _,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:
                    child.kill(); child.wait(timeout=5)
        result['source_files_unchanged']={key:fixture.sha(path)==result['before'][key] for key,path in paths.items()}
        result['accepted']=bool(result['accepted'] and all(result['source_files_unchanged'].values()))
        if args.output.exists(): dump(args.output/'run-result.json',result)
    print(json.dumps({'accepted':result['accepted'],'error':result.get('error'),'output':str(args.output)}))
    return 0 if result['accepted'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker: return worker(args)
    if args.server_candidate is None: parser.error('--server-candidate is required')
    return owner(args)


if __name__=='__main__':
    raise SystemExit(main())
