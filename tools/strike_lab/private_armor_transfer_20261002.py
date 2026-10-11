"""NEW armor UI preparation. Default command is read-only and never starts UI.

Fixture instances are CUSTOM_TEST_NOT_NATIVE, not drops or battle/stat evidence.
Only a separately migrated disposable clone may be seeded by the future owner.
No packet injection, native function calls, memory writes, foreground or screenshots.
Live activation remains gated on parent-provided immutable candidate/config/projector.
"""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
SOURCE = ROOT / 'artifacts/playtests/private-native-blackbox-armor-definitions-20261002-01/town-diagnostic-accounts.db'
ORACLE = ROOT / 'artifacts/research/native-armor-20261002/oracle.json'
CLIENT = ROOT.parent / 'God2/God2.exe'
CLIENT_SHA = 'c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CATALOG_SHA = '29d1de3729c843571c3a7bc117beb12289bd7110932ec45fc5d846b627282efe'
ARMOR = 'character_armor_slot_metadata'
SCALAR = 'diagnostic_inventory_slots'
FAMILIES = {4: ('EQU', 2, (1201, 1001, 1501, 1601)),
            5: ('TEQ', 26, (20201, 20001, 20501, 20601))}
DESIGN = 'CUSTOM-0066'
ORIGIN = 'CUSTOM_TEST_NOT_NATIVE'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ro(path):
    return sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def instance(character, ordinal, item, selector):
    # Definition loader396 is not an owned20 instance. These are explicit test
    # operands, unique in the known four-dimension low bytes, grade bits zero.
    raw = bytearray(struct.pack('<HH', item, selector) + bytes(16))
    raw[8:12] = bytes((character, ordinal + 1, 3, 5))
    require(len(raw) == 20 and raw[2] & 63 == selector, 'CUSTOM_INSTANCE_LAYOUT')
    return bytes(raw)


def fixture_rows(character):
    family, selector, ids = FAMILIES[character]
    rows = []
    for slot in range(34):
        item = ids[slot % 4] if slot < 30 else ids[0] if slot == 30 else 0
        raw = instance(character, slot, item, selector) if item else None
        rows.append(dict(slot=slot, item=item, count=int(bool(item)), revision=1,
                         metadata=raw.hex() if raw else None, family=family,
                         origin=ORIGIN if item else None,
                         source=SOURCE_SHA if item else None, client=CLIENT_SHA if item else None,
                         design=DESIGN if item else None,
                         scalar_source=SOURCE_SHA, scalar_design='CUSTOM-0015',
                         provenance=f'private-armor-transfer-20261002 owner={character} fixture={slot}' if item else None))
    return rows


def actions():
    # 31 complete owned instances, 30 bag cells. Capacity is created entirely
    # by normal wear actions. No live DB mutation occurs between gestures.
    return [
        dict(kind='28', source=30, destination=None, refusal=True, label='fullbag_remove_head_refused'),
        dict(kind='28', source=1, destination=31, label='wear_body'),
        dict(kind='28', source=30, destination=1, label='remove_head'),
        dict(kind='28', source=1, destination=30, label='wear_head'),
        dict(kind='28', source=0, destination=30, label='occupied_head_full20_swap'),
        dict(kind='28', source=2, destination=32, label='wear_gloves'),
        dict(kind='28', source=3, destination=33, label='wear_shoes'),
        dict(kind='28', source=5, destination=31, label='occupied_body_full20_swap'),
        dict(kind='24', source=4, destination=2, label='bag_to_empty_full20'),
        dict(kind='24', source=6, destination=7, label='occupied_bag_different_parts_full20'),
        dict(kind='28', source=31, destination=1, label='remove_body'),
        dict(kind='28', source=32, destination=3, label='remove_gloves'),
        dict(kind='28', source=33, destination=4, label='remove_shoes'),
        dict(kind='28', source=30, destination=None, refusal=True, label='fullbag_remove_head_refused_again'),
    ]


def inventory_multiset(rows):
    return sorted(row['metadata'] for row in rows.values() if row['count'])


def predict(before, action):
    # Expected-state planning only. This is neither an emulator nor acceptance.
    after = {slot: dict(row) for slot, row in before.items()}
    source, destination = action['source'], action['destination']
    if action.get('refusal'):
        require(all(before[i]['count'] for i in range(30)), 'REFUSAL_PLAN_REQUIRES_FULL_BAG')
        return after
    a, b = before[source], before[destination]
    require(a['count'] == 1, 'ACTION_SOURCE_MUST_BE_OWNED_INSTANCE')
    for slot, other in ((source, b), (destination, a)):
        revision = before[slot]['revision'] + 1
        after[slot] = dict(other, slot=slot, revision=revision)
    require(inventory_multiset(before) == inventory_multiset(after), 'PLAN_FULL20_CONSERVATION')
    return after


def snapshot(database, character):
    with closing(ro(database)) as db:
        rows = db.execute('SELECT s.slot,s.item_id,s.count,s.revision,m.logical20,m.revision,m.origin,m.provenance,'
            'm.source_sha256,m.client_sha256,m.design_id,s.source_sha256,s.design_id '
            'FROM diagnostic_inventory_slots s LEFT JOIN character_armor_slot_metadata m '
            'ON m.character_id=s.character_id AND m.slot=s.slot WHERE s.character_id=? AND s.slot<34 '
            'ORDER BY s.slot', (character,)).fetchall()
    require(len(rows) == 34 and [row[0] for row in rows] == list(range(34)), 'EXPLICIT_34_OWNER_CELLS_REQUIRED')
    out = {}
    for slot, item, count, revision, raw, meta_revision, origin, provenance, source, client, design, scalar_source, scalar_design in rows:
        require(count in (0, 1) and bool(item) == bool(count), 'ARMOR_SCALAR_INVALID')
        require(scalar_source == SOURCE_SHA and scalar_design == 'CUSTOM-0015', 'ARMOR_SCALAR_PROVENANCE')
        require((raw is None) == (count == 0), 'FULL20_MISSING_OR_ORPHAN')
        if raw is not None:
            require(len(raw) == 20 and int.from_bytes(raw[:2], 'little') == item and meta_revision == revision,
                    'FULL20_SCALAR_OR_REVISION_MISMATCH')
            require(source == SOURCE_SHA and client == CLIENT_SHA and design == DESIGN,
                    'FULL20_SOURCE_CLIENT_DESIGN_PROVENANCE_MISMATCH')
        out[slot] = dict(slot=slot, item=item, count=count, revision=revision,
                         metadata=raw.hex() if raw else None, origin=origin, provenance=provenance,
                         source=source, client=client, design=design,
                         scalar_source=scalar_source, scalar_design=scalar_design)
    return out


def native_snapshot(handle, ui):
    # Original inventory array; read-only full24 each. No process writes.
    from private_weapon_peer_appearance_20260927 import exact
    raw = exact(handle, ui + 0x8560c, 34 * 24)
    return {slot: raw[slot * 24:(slot + 1) * 24].hex() for slot in range(34)}


def agrees(native, saved):
    for slot, row in saved.items():
        raw = bytes.fromhex(native[slot])
        if row['count']:
            if raw != struct.pack('<I', 1) + bytes.fromhex(row['metadata']):
                return False
        elif raw[:6] != bytes(6):
            # Original41 clear only clears count and item key; opaque native
            # tail can remain. Never claim exact empty20 zero restoration.
            return False
    return True


def unchanged_outside(database, character):
    with closing(ro(database)) as db:
        result = {}
        for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
            quoted = '"' + name.replace('"', '""') + '"'
            predicate = ' WHERE character_id<>? OR slot>=34' if name in (SCALAR, ARMOR) else ''
            params = (character,) if predicate else ()
            rows = sorted(repr(tuple(row)) for row in db.execute('SELECT * FROM ' + quoted + predicate, params))
            result[name] = hashlib.sha256('\n'.join(rows).encode()).hexdigest()
        return result


def hit_layout(client):
    # Same complete visible/header traversal qualified against original504620
    # by the frozen bank-swap oracle. Hidden0x13 widgets are excluded.
    from private_weapon_peer_appearance_20260927 import exact
    def number(address, size=4, signed=False):
        return int.from_bytes(exact(client['handle'], address, size), 'little', signed=signed)
    manager = client['ui'] + 0xe2170
    mouse, node = number(manager + 4), number(manager + 0x14)
    require(mouse > 0x10000, 'NATIVE_HIT_MOUSE_MANAGER_MISSING')
    rectangles = exact(client['handle'], mouse, 0xc00 * 24)
    rows, seen = [], set()
    while node:
        require(node not in seen and len(seen) < 128, 'NATIVE_HIT_LIST_CYCLE')
        seen.add(node)
        widget = number(node, 2, True)
        require(0 <= widget < 128, 'NATIVE_HIT_WIDGET_DOMAIN')
        flags = number(manager + widget * 0x2a08 + 0x818, 2)
        if flags & 0x20:
            header = number(node + 8, 2, True)
            if 0 <= header < 0xc00:
                active, left, top, right, bottom, inside = struct.unpack_from('<6i', rectangles, header * 24)
                if active:
                    rows.append(dict(widget=widget, index=-1, header=True, widget_flags=flags,
                                     hit_id=header, rect=[left, top, right, bottom], inside_last_mouse=inside))
            controls = exact(client['handle'], manager + widget * 0x2a08 + 0x8b8, 106 * 100)
            for index in range(106):
                control = controls[index * 100:(index + 1) * 100]
                hit = int.from_bytes(control[8:10], 'little', signed=True)
                if not control[0] or not 0 <= hit < 0xc00:
                    continue
                active, left, top, right, bottom, inside = struct.unpack_from('<6i', rectangles, hit * 24)
                if active:
                    rows.append(dict(widget=widget, index=index, flags=control[0],
                        type4=int.from_bytes(control[4:8], 'little'), widget_flags=flags, hit_id=hit,
                        rect=[left, top, right, bottom], inside_last_mouse=inside))
        node = number(node + 0xc)
    return rows


def hits(rows, point):
    x, y = point
    matches = [row for row in rows if row['rect'][0] <= x <= row['rect'][2] and
               row['rect'][1] <= y <= row['rect'][3]]
    headers = [row for row in matches if row.get('header')]
    if not headers:
        return []
    front = headers[0]
    controls = [row for row in matches if row['widget'] == front['widget'] and not row.get('header')]
    return (controls or [front]) + [row for row in matches if row['widget'] != front['widget']]


def hit_point(client, widget, index):
    rows = hit_layout(client)
    intended = [row for row in rows if row['widget'] == widget and row['index'] == index and not row.get('header')]
    require(len(intended) == 1, 'NATIVE_VISIBLE_CONTROL_MUST_BE_UNIQUE')
    left, top, right, bottom = intended[0]['rect']
    options = []
    for fy in (.5, .2, .8):
        for fx in (.5, .2, .8):
            point = (round(left + (right - left) * fx), round(top + (bottom - top) * fy))
            options.append(dict(point=point, hits=hits(rows, point)))
    eligible = [option for option in options if option['hits'] and
                option['hits'][0]['widget'] == widget and option['hits'][0]['index'] == index]
    require(eligible, 'NATIVE_INPUT_CONTROL_OCCLUDED_NO_FORCED_DROP')
    chosen = min(eligible, key=lambda option: len(option['hits']))
    return chosen['point'], dict(widget=widget, index=index, options=options, chosen=chosen)


def seed_migrated_clone(database, output):
    # Not invoked by the preparation CLI. Caller must have parent authorization
    # and have already executed the actual next candidate migration.
    require(database.resolve() == output.resolve() / 'town-diagnostic-accounts.db', 'EXACT_PRIVATE_CLONE_REQUIRED')
    require(database.resolve() != SOURCE.resolve(), 'SOURCE_DATABASE_WRITE_FORBIDDEN')
    require(output.resolve().is_relative_to((ROOT / 'artifacts/playtests').resolve()), 'PLAYTEST_CLONE_ONLY')
    with closing(sqlite3.connect(database)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        require(db.execute("SELECT 1 FROM sqlite_master WHERE name=? AND type='table'", (ARMOR,)).fetchone(),
                'ACTUAL_CANDIDATE_ARMOR_SCHEMA_REQUIRED_NO_HARNESS_SCHEMA_INSTALL')
        for character in FAMILIES:
            require(db.execute('SELECT account_id FROM recovered_characters WHERE id=?', (character,)).fetchone() == (character,),
                    'ISOLATED_FIXTURE_OWNERSHIP_REQUIRED')
            for table in (ARMOR, 'character_weapon_slot_metadata', 'character_teleport_gem_metadata'):
                db.execute('DELETE FROM ' + table + ' WHERE character_id=? AND slot<34', (character,))
            db.execute('DELETE FROM diagnostic_inventory_slots WHERE character_id=? AND slot<34', (character,))
            for row in fixture_rows(character):
                db.execute("INSERT INTO diagnostic_inventory_slots VALUES(?,?,?,?,1,?,'CUSTOM-0015')",
                           (character, row['slot'], row['item'], row['count'], SOURCE_SHA))
                if row['count']:
                    db.execute('INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,?,?,?,?,?)',
                        (character, row['slot'], bytes.fromhex(row['metadata']), 1, ORIGIN, row['provenance'],
                         SOURCE_SHA, CLIENT_SHA, DESIGN))
        require(db.execute('PRAGMA quick_check').fetchone() == ('ok',), 'PRIVATE_CLONE_INTEGRITY')
        require(db.execute('PRAGMA foreign_key_check').fetchone() is None, 'PRIVATE_CLONE_FOREIGN_KEYS')
        db.commit()


def gesture(client, action, checkpoint=None):
    # Prepared live primitive, not called by CLI. HWND ownership and hidden
    # desktop must be checked by the future owner before calling this function.
    from private_inventory_move_ui import desktop_names
    from private_weapon_peer_appearance_20260927 import exact, window_for
    from private_map_item_current_ui import double_click_message
    from private_potion_ui import user
    import ctypes
    from ctypes import wintypes
    def record(phase, **details):
        if checkpoint:
            checkpoint(phase, details)
    desktops = desktop_names()
    require(desktops['current'].startswith('God2Lab-') and desktops['current'] != desktops['input'],
            'OWNED_HIDDEN_DESKTOP_REQUIRED')
    require(window_for(client['process'].pid) == client['hwnd'], 'OWNED_WINDOW_REQUIRED')
    widget = int.from_bytes(exact(client['handle'], client['ui'] + 0x232dc8, 2), 'little', signed=True)
    require(0 <= widget < 128, 'REAL_INVENTORY_WIDGET_REQUIRED')
    flags = exact(client['handle'], client['ui'] + 0xe2988 + widget * 0x2a08, 1)[0]
    require(flags & 0x20, 'NATIVE_INVENTORY_WIDGET_NOT_VISIBLE')
    # Move into neutral game background to retire any previous native tooltip;
    # this is only a real window-local WM_MOUSEMOVE, not a memory state change.
    rect = wintypes.RECT()
    require(user.GetClientRect(client['hwnd'], ctypes.byref(rect)), 'CLIENT_RECT_REQUIRED')
    require(user.PostMessageW(client['hwnd'], 0x200, 0,
            (round(410 * rect.bottom / 600) << 16) | round(350 * rect.right / 800)), 'NEUTRAL_MOUSE_MOVE_FAILED')
    time.sleep(.2)
    start, source_hit = hit_point(client, widget, action['source'])
    record('source_hit_qualified', widget=widget, source_point=start, source_hit=source_hit)
    if action['kind'] == '28':
        points = double_click_message(client['hwnd'], *start)
        record('normal_double_click_finished', message_points=points, hits_after=hit_layout(client))
        return dict(widget=widget, source_point=start, source_hit=source_hit,
                    message_points=points, input='REAL_NATIVE_DOUBLE_CLICK')
    require(action['kind'] == '24' and action['source'] < 30 and action['destination'] < 30, 'BAG_DRAG_DOMAIN')
    sx, sy = round(start[0] * rect.right / 800), round(start[1] * rect.bottom / 600)
    def message(code, key, x, y):
        require(user.PostMessageW(client['hwnd'], code, key, (y << 16) | x), 'REAL_BAG_MOUSE_MESSAGE_FAILED')
        time.sleep(.12)
    message(0x200, 0, sx, sy)
    message(0x201, 1, sx, sy)
    selected = int.from_bytes(exact(client['handle'], client['ui'] + 0x855f0, 2), 'little', signed=True)
    record('source_pressed', selected_source=selected)
    require(selected == action['source'], 'REAL_BAG_SOURCE_NOT_SELECTED')
    # Normal source press can create a foreground tooltip. Recompute the real
    # destination hit only now, then release inside the actual target control.
    end, destination_hit = hit_point(client, widget, action['destination'])
    record('destination_hit_after_source_press', destination_point=end, destination_hit=destination_hit)
    ex, ey = round(end[0] * rect.right / 800), round(end[1] * rect.bottom / 600)
    for step in range(1, 11):
        message(0x200, 1, sx + (ex - sx) * step // 10, sy + (ey - sy) * step // 10)
    message(0x202, 0, ex, ey)
    record('destination_released', selected_source=int.from_bytes(
        exact(client['handle'], client['ui'] + 0x855f0, 2), 'little', signed=True))
    return dict(widget=widget, source_point=start, destination_point=end,
                source_hit=source_hit, destination_hit_after_press=destination_hit, selected_source=selected,
                message_points=[[sx, sy], [ex, ey]], input='REAL_NATIVE_PRESS_MOVE_RELEASE')


def preparation(output):
    from tools.strike_lab import import_native_armor_20261002 as armor
    require(sha(CLIENT) == CLIENT_SHA, 'CURRENT_CLIENT_PIN_CHANGED')
    oracle = json.loads(ORACLE.read_text(encoding='utf-8'))
    qualification = {row['item_id']: row for row in oracle['qualifications']}
    require(oracle['catalog_fingerprint'] == CATALOG_SHA, 'NATIVE_DEFINITION_FINGERPRINT')
    source_before = sha(SOURCE)
    with closing(ro(SOURCE)) as db:
        groups = tuple(tuple(tuple(row) for row in db.execute('SELECT * FROM ' + table + ' ORDER BY ' + order))
                       for table, order in zip(armor.TABLES, armor.ORDERS))
        require(armor.fingerprint(groups) == CATALOG_SHA, 'ACCEPTED_CLONE_FULL_ARMOR_SOURCE_REQUIRED')
        require(db.execute('PRAGMA quick_check').fetchone() == ('ok',), 'READONLY_SOURCE_INTEGRITY')
        migrations = [list(row) for row in db.execute('SELECT version,name FROM schema_migrations ORDER BY version')]
    guards = {str(path): sha(path) for path in (CLIENT, SOURCE, ORACLE,
        ROOT/'tools/strike_lab/private_weapon_peer_appearance_20260927.py',
        ROOT/'tools/strike_lab/private_inventory_move_ui.py',
        ROOT/'tools/strike_lab/private_owned_companions_ui.py',
        ROOT/'tools/strike_lab/private_map_item_current_ui.py',
        ROOT/'tools/strike_lab/private_armor_definitions_20261002.py')}
    plans = {}
    for character, (family, selector, ids) in FAMILIES.items():
        definitions = []
        for item, slot in zip(ids, (30, 31, 32, 33)):
            row = qualification[item]
            require(row['family'] == family and row['slot'] == slot and row['equip_flag'] and
                    row['loader_family_selector'] == selector, 'EXPLICIT_NATIVE_FOUR_PART_MAPPING')
            definitions.append(row)
        current = {row['slot']: row for row in fixture_rows(character)}
        original = inventory_multiset(current)
        stages = []
        for index, action in enumerate(actions(), 1):
            if action['kind'] == '28' and not action.get('refusal'):
                source = action['source']
                destination = action['destination']
                if source < 30:
                    require(qualification[current[source]['item']]['slot'] == destination,
                            'WEAR_PLAN_MUST_USE_EXPLICIT_PHYSICAL_PART')
                else:
                    require(destination == next(i for i in range(30) if not current[i]['count']),
                            'REMOVE_PLAN_LOWEST_OWNED_EMPTY_POLICY')
            current = predict(current, action)
            require(inventory_multiset(current) == original, 'OFFLINE_PLAN_CONSERVATION')
            stages.append(dict(step=index, **action, planned_instance_count=len(original),
                               planned_empty_bag=[s for s in range(30) if not current[s]['count']]))
        plans[str(character)] = dict(locale=950 if character == 4 else 936, family=family,
            native_definition_rows=definitions, fixture_rows=fixture_rows(character), steps=stages,
            expected_mutations=12, expected_refusals=2, relogin='both owners after full sequence; full34 projection must agree')
    require(sha(SOURCE) == source_before, 'PREPARATION_SOURCE_WAS_MUTATED')
    require(all(sha(Path(path)) == digest for path, digest in guards.items()), 'PREPARATION_FROZEN_GUARD_CHANGED')
    result = dict(status='PREPARED_NO_UI_NO_PORT_NO_CLONE_WRITES', authority=ORIGIN,
        live_acceptance=False, source_clone=str(SOURCE), source_sha256=source_before,
        accepted_source_migrations=migrations, source_catalog_fingerprint=CATALOG_SHA,
        inventory_widget_selector='UI+0x232DC8', native_inventory='UI+0x8560C + slot*24',
        control_rect='UI+0xE2170+0x818+widget*0x2A08+0xA0+control*100+0x10',
        controls=dict(bag=list(range(30)), head=30, armor=31, gloves=32, shoes=33),
        requests=dict(double_click28='0049A330 ->00496550 ->004132E0; 28 itemWORD slot 1',
                      bag_drag24='0049A330/0049EAB0 ->00496610 ->004132E0; 24 source dest'),
        plans=plans, planned_events=28, planned_mutations=24, planned_refusals=4,
        future_config={'world.owned_armor_transfers.enabled':
                       {'status':'NOT_IMPLEMENTED_AND_NOT_RUN','future_value':True}},
        frozen_guards=guards,
        needs=['parent immutable candidate path and SHA plus exclusive2598 grant',
               'actual candidate migration installs character_armor_slot_metadata; no harness schema install',
               'Application config exact owned_armor_transfers enable key and accepted startup marker',
               'full owner34 projector on initial login and relogin: clears,3B full20,41 absolute count',
               'commit/reject log markers with account/character/source/destination for actual28/24 proof',
               'nativeEquipmentRejection02/msg27 plus rollbackprojection; pending may remain1 natively; next legal UI must work',
               'live original hit-path checks for occupied/empty bag drag targets before acceptance'],
        scope='Existing native requests; custom transactional transfer policy only. Not original drops, role eligibility, stats, combat formula or armor appearance.')
    output.mkdir(parents=True, exist_ok=False)
    dump(output/'preparation.json', result)
    dump(output/'required-integration.json', dict(
        status='NOT_IMPLEMENTED_AND_NOT_RUN', immutable_candidate=None, ui_started=False,
        port2598_used=False, existing_source_only_candidate_sha256=
        '80060831f15e4f27667745848ba9c18fefec441106c935e72f4b64089a6a36ed',
        source_only_schema=41, future_config=result['future_config'],
        required=result['needs'], fixture_authority=ORIGIN, instance_family_masks=
        {'EQU':'logical20[2]&0x3f == 2','TEQ':'logical20[2]&0x3f == 26'},
        live_work_remaining='Owner launch/login/relogin orchestration and live hit-path qualification remain gated on next candidate. No real armor wear/remove executed.',
        acceptance_scope=result['scope'], planned_events=28, planned_mutations=24,
        planned_refusals=4, harness_sha256=sha(Path(__file__).resolve())))
    print(json.dumps({key: result[key] for key in ('status','planned_events','planned_mutations','planned_refusals','live_acceptance')}))
    return 0


def prepare_live(args):
    # Uses frozen owner infrastructure through process-local callbacks only.
    # Old source files remain byte-identical. Migration belongs to candidate.
    require(sha(args.server_candidate) == args.candidate_sha, 'IMMUTABLE_ARMOR_CANDIDATE_PIN')
    _BASE_PREPARE(args)
    database = args.output / 'town-diagnostic-accounts.db'
    with closing(ro(database)) as db:
        migration = db.execute('SELECT version,name,sql_text FROM schema_migrations WHERE version=42').fetchone()
        require(migration and db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (ARMOR,)).fetchone(),
                'REAL_CANDIDATE_MIGRATION42_ARMOR_SCHEMA_REQUIRED')
    config_path = args.output / 'server-config.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    config.setdefault('world', {})['owned_armor_transfers'] = {'enabled': True}
    dump(config_path, config)
    seed_migrated_clone(database, args.output)
    fixture_path = args.output / 'fixture.json'
    fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
    fixture['armor_fixture'] = dict(authority=ORIGIN, design_id=DESIGN,
        migration42_name=migration[1], migration42_sql_sha256=hashlib.sha256(migration[2].encode()).hexdigest(),
        candidate_sha256=args.candidate_sha, contract=args.contract,
        definitions='Eight current source keys level1/unrestricted; explicit physical part labels',
        instances={str(character):fixture_rows(character) for character in FAMILIES},
        actions=actions(), planned_events=28, planned_mutations=24, planned_refusals=4)
    dump(fixture_path, fixture)


def worker(args):
    import psutil
    import private_peer_role_text_20260930 as base
    import private_owned_companions_ui as owned
    from private_inventory_move_ui import desktop_names, wait_until
    from private_potion_ui import click, type_ascii
    fixture = json.loads((args.output / 'fixture.json').read_text(encoding='utf-8'))
    contract = fixture['armor_fixture']['contract']
    database, log = args.output / 'town-diagnostic-accounts.db', args.output / 'server.log'
    before = desktop_names()
    clients, loaders = [], []
    result = dict(accepted=False, events=[], owned_client_pids=[], read_handles_closed=False,
                  authority=ORIGIN, scope='ARMOR_FULL20_TRANSFER_ONLY_NOT_DROP_STATS_OR_APPEARANCE_FORMULA')
    def save():
        dump(args.output / 'ui-result.json', result)
    def text_log():
        return log.read_text(encoding='utf-8', errors='replace')
    def close(client):
        if client.get('handle'):
            base.peer.kernel.CloseHandle(client.pop('handle'))
        process = client['process']
        if process.is_running():
            if client.get('hwnd'):
                base.peer.user.PostMessageW(client['hwnd'], 0x10, 0, 0)
            try:
                process.wait(timeout=4)
            except psutil.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
    def launch(identity, page):
        image = Path(fixture['clients'][str(page)]['path'])
        require(sha(image) == fixture['clients'][str(page)]['sha256'], 'PRIVATE_IMAGE_PIN_CHANGED')
        loader = subprocess.Popen([str(base.LE), '-run', str(image), '127.0.0.1', '127.0.0.1', '6001', '1'],
            cwd=CLIENT.parent, creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        loaders.append(loader)
        def found():
            rows = [p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve() == image.resolve()]
            require(len(rows) <= 1, 'DUPLICATE_PRIVATE_IMAGE_PROCESS')
            return rows[0] if rows else None
        process = wait_until(found, 35, 'PRIVATE_LOCALE_CLIENT_MISSING')
        client = dict(process=process, identity=identity, page=page)
        clients.append(client)
        result['owned_client_pids'].append(process.pid)
        save()
        client['hwnd'] = wait_until(lambda:base.peer.window_for(process.pid), 35, 'OWNED_HIDDEN_HWND_MISSING')
        hwnd = client['hwnd']
        time.sleep(12)
        click(hwnd, 512, 464)
        time.sleep(4)
        bound = 'RECOVERED_ACCOUNT_BOUND account_id=' + str(identity)
        prior_bound = text_log().count(bound)
        restore_before = len([line for line in text_log().splitlines() if contract['restore_marker'] in line and
                              re.search(r'\bcharacter=' + str(identity) + r'\b', line)])
        click(hwnd, 437, 232)
        type_ascii(hwnd, 'codexslow' if identity == 4 else 'codexfixed')
        click(hwnd, 437, 263)
        type_ascii(hwnd, 'labtest2345')
        click(hwnd, 452, 304)
        wait_until(lambda:text_log().count(bound) > prior_bound, 35, 'OWNED_PRIVATE_LOGIN_NOT_BOUND')
        time.sleep(4)
        click(hwnd, 330, 145)
        click(hwnd, 452, 413)
        time.sleep(4)
        click(hwnd, 330, 150)
        click(hwnd, 452, 376)
        time.sleep(4)
        click(hwnd, 452, 370)
        time.sleep(12)
        client['handle'] = base.peer.kernel.OpenProcess(0x1010, False, process.pid)
        require(client['handle'], 'READONLY_PROCESS_HANDLE_REQUIRED')
        client['ui'] = base.peer.find_ui(client['handle'], identity, (0, 3, 4))
        language, sub = struct.unpack('<HH', base.peer.exact(client['handle'], 0x59dfd8, 4))
        require(language == 4 and ((sub == 2) == (page == 936)), 'NATIVE_TW_CN_LOCALE_MISMATCH')
        current = snapshot(database, identity)
        wait_until(lambda:len([line for line in text_log().splitlines() if contract['restore_marker'] in line and
            re.search(r'\bcharacter=' + str(identity) + r'\b',line)]) > restore_before,
            12,'LOGIN_ACTUAL_OWNER_ARMOR_RESTORE_MARKER_MISSING')
        native = wait_until(lambda:native_snapshot(client['handle'], client['ui']) if
            agrees(native_snapshot(client['handle'], client['ui']), current) else None, 12, 'LOGIN_FULL34_OWNER_PROJECTION_MISMATCH')
        client['stable_native'] = {key:value for key,value in owned.native(client['handle'],client['ui']).items()
                                  if key in base.peer.STABLE_KEYS}
        result.setdefault('logins', []).append(dict(identity=identity, page=page, pid=process.pid,
            ui=hex(client['ui']), saved=current, native=native, full20_and_counts_agree=True))
        save()
        return client
    def canonical_rows(rows):
        keys = ('slot', 'item', 'count', 'revision', 'metadata', 'origin', 'provenance','source','client','design',
                'scalar_source','scalar_design')
        return {slot:{key:row[key] for key in keys} for slot,row in rows.items()}
    try:
        require(before['current'].startswith('God2Lab-') and before['current'] != before['input'], 'PRIVATE_HIDDEN_DESKTOP_REQUIRED')
        require(contract['startup_marker'] in text_log(), 'ACTUAL_APPLICATION_ARMOR_ENABLED_MARKER_MISSING')
        actor, observer = launch(4, 950), launch(5, 936)
        for client in (actor, observer):
            expected = {row['slot']:row for row in fixture_rows(client['identity'])}
            require(canonical_rows(expected) == snapshot(database, client['identity']), 'CUSTOM_TEST_SEED_CHANGED_BEFORE_UI')
        for client, peer in ((actor, observer), (observer, actor)):
            invariant = unchanged_outside(database, client['identity'])
            peer_before = snapshot(database, peer['identity'])
            peer_native = native_snapshot(peer['handle'], peer['ui'])
            click(client['hwnd'], 708, 584)
            time.sleep(1)
            for step, action in enumerate(actions(), 1):
                prior = snapshot(database, client['identity'])
                native_prior = native_snapshot(client['handle'], client['ui'])
                expected = predict(prior, action)
                prefix = contract['reject_marker'] if action.get('refusal') else contract['commit_marker']
                old_lines = [line for line in text_log().splitlines() if prefix in line]
                attempt = dict(identity=client['identity'],page=client['page'],step=step,**action,
                               input_phases=[],before=prior,before_native=native_prior)
                result.setdefault('attempts',[]).append(attempt)
                save()
                def checkpoint(phase, details):
                    attempt['input_phases'].append(dict(phase=phase,details=details,
                        native=native_snapshot(client['handle'],client['ui'])))
                    save()
                input_receipt = gesture(client, action,checkpoint)
                attempt['input_receipt'] = input_receipt
                save()
                def observed():
                    current = snapshot(database, client['identity'])
                    native = native_snapshot(client['handle'], client['ui'])
                    lines = [line for line in text_log().splitlines() if prefix in line]
                    if len(lines) != len(old_lines) + 1 or current != expected or not agrees(native,current):
                        result['last_observed'] = dict(identity=client['identity'], step=step, current=current,
                            expected=expected, native=native, marker_lines=lines[len(old_lines):])
                        save()
                        return None
                    if action.get('refusal') and native != native_prior:
                        return None
                    marker = lines[-1]
                    require(re.search(r'\baccount=' + str(client['identity']) + r'\b',marker) and
                            re.search(r'\bcharacter=' + str(client['identity']) + r'\b',marker) and
                            re.search(r'\bsource=' + str(action['source']) + r'\b',marker),
                            'ARMOR_ACTUAL_REQUEST_MARKER_OWNER_OR_SOURCE_MISMATCH')
                    if not action.get('refusal'):
                        require(re.search(r'\bdestination=' + str(action['destination']) + r'\b',marker),
                                'ARMOR_ACTUAL_REQUEST_MARKER_DESTINATION_MISMATCH')
                    return dict(saved=current, native=native, server_marker=lines[-1])
                state = wait_until(observed, 12, 'ARMOR_NATIVE_UI_ACTION_NOT_CANONICAL_' + action['label'])
                require(unchanged_outside(database,client['identity']) == invariant, 'ARMOR_UNRELATED_DATABASE_OR_OTHER_OWNER_CHANGED')
                require(snapshot(database,peer['identity']) == peer_before and
                    native_snapshot(peer['handle'],peer['ui']) == peer_native, 'ARMOR_PEER_INVENTORY_CHANGED')
                for value in (client,peer):
                    stable = {key:item for key,item in owned.native(value['handle'],value['ui']).items() if key in base.peer.STABLE_KEYS}
                    require(stable == value['stable_native'], 'ARMOR_UNRELATED_NATIVE_STATE_CHANGED')
                require(inventory_multiset(prior) == inventory_multiset(state['saved']), 'ARMOR_COMPLETE20_CONSERVATION')
                result['events'].append(dict(identity=client['identity'], page=client['page'], step=step,
                    **action, input=input_receipt, before=prior, before_native=native_prior, after=state,
                    other_owner_unchanged=True, unrelated_tables_unchanged=True, full20_conserved=True))
                save()
            # Close bag by the same real HUD toggle before relogin.
            click(client['hwnd'],708,584)
            time.sleep(.2)
        durable = {identity:snapshot(database,identity) for identity in FAMILIES}
        relog_invariant = unchanged_outside(database,4)
        close(observer)
        close(actor)
        restored = [launch(4,950),launch(5,936)]
        result['relogin'] = []
        for client in restored:
            identity = client['identity']
            current, native = snapshot(database,identity), native_snapshot(client['handle'],client['ui'])
            require(current == durable[identity] and agrees(native,current), 'RELOGIN_DURABLE_FULL20_OWNER_RESTORE_FAILED')
            result['relogin'].append(dict(identity=identity,page=client['page'],saved=current,native=native,
                owner34_full20_restored=True, durable_revisions_unchanged=True))
        require(unchanged_outside(database,4) == relog_invariant, 'RELOGIN_UNRELATED_TABLES_OR_OTHER_OWNER_CHANGED')
        result['relogin_unrelated_tables_unchanged'] = True
        result['actual_mutations'] = sum(not event.get('refusal') for event in result['events'])
        result['actual_refusals'] = sum(bool(event.get('refusal')) for event in result['events'])
        result['accepted'] = result['actual_mutations'] == 24 and result['actual_refusals'] == 4 and len(result['relogin']) == 2
    except BaseException as error:
        result['error'], result['traceback'] = str(error), traceback.format_exc()
    finally:
        for client in reversed(clients):
            try:
                close(client)
            except BaseException as error:
                result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:
                loader.terminate()
                loader.wait(timeout=5)
        result['read_handles_closed'] = all(not client.get('handle') for client in clients)
        result['desktop_before'],result['desktop_after'] = before,desktop_names()
        result['desktop_unchanged'] = result['desktop_before'] == result['desktop_after']
        result['all_owned_clients_closed'] = all(not psutil.pid_exists(client['process'].pid) for client in clients)
        result['accepted'] = bool(result['accepted'] and result['read_handles_closed'] and
            result['desktop_unchanged'] and result['all_owned_clients_closed'] and not result.get('cleanup_errors'))
        save()
    return 0 if result['accepted'] else 1


def owner(args):
    import socket
    import psutil
    import private_peer_role_text_20260930 as base
    import private_peer_pose_20261002 as pose
    from private_inventory_move_ui import desktop_names
    global _BASE_PREPARE
    require(args.port_authorized and args.server_candidate and args.candidate_sha and args.contract_path,
            'PARENT_IMMUTABLE_CANDIDATE_AND_EXCLUSIVE2598_GRANT_REQUIRED')
    require(sha(args.server_candidate) == args.candidate_sha and sha(CLIENT) == CLIENT_SHA, 'LIVE_IMMUTABLE_PINS')
    args.contract = json.loads(args.contract_path.read_text(encoding='utf-8'))
    require(args.contract.get('status') == 'IMPLEMENTED_CANDIDATE_ONLY' and
            all(args.contract.get(key) for key in ('startup_marker','commit_marker','reject_marker','restore_marker')),
            'ACTUAL_APPLICATION_MARKER_CONTRACT_REQUIRED')
    # Validate the same frozen current image provenance, not a retired copy.
    pose.qualify_source()
    base.CLIENT_SHA, base.SOURCE = CLIENT_SHA, SOURCE
    _BASE_PREPARE = base.prepare
    base.prepare,base.__file__ = prepare_live,str(Path(__file__).resolve())
    before = desktop_names()
    protected = {str(p.pid):dict(exe=p.info['exe'],created=p.info['create_time']) for p in
        psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in
        ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    files = [Path(__file__).resolve(),Path(base.__spec__.origin),SOURCE,ORACLE,CLIENT,args.contract_path,
             ROOT/'tools/strike_lab/private_weapon_peer_appearance_20260927.py',
             ROOT/'tools/strike_lab/private_inventory_move_ui.py',
             ROOT/'tools/strike_lab/private_owned_companions_ui.py',
             ROOT/'tools/strike_lab/private_map_item_current_ui.py']
    guards = {str(path.resolve()):sha(path) for path in files}
    os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB'] = '1'
    code = base.owner(args)
    receipt = args.output / 'run-result.json'
    if not receipt.exists():
        return code
    result = json.loads(receipt.read_text(encoding='utf-8'))
    after = {str(p.pid):dict(exe=p.info['exe'],created=p.info['create_time']) for p in
        psutil.process_iter(['exe','create_time']) if str(p.pid) in protected}
    result['armor_files_before'] = guards
    result['armor_files_after'] = {path:sha(Path(path)) for path in guards}
    result['armor_frozen_files_unchanged'] = result['armor_files_before'] == result['armor_files_after']
    result['protected_processes_before'],result['protected_processes_preserved'] = protected,after == protected
    result['desktop_owner_before'],result['desktop_owner_after'] = before,desktop_names()
    result['desktop_owner_unchanged'] = result['desktop_owner_before'] == result['desktop_owner_after']
    with socket.socket() as probe:
        result['exclusive2598_released'] = probe.connect_ex(('127.0.0.1',2598)) != 0
    pids = [result.get('server_pid'),result.get('runner_pid')] + result.get('ui',{}).get('owned_client_pids',[])
    result['owned_pid_terminal'] = {str(pid):dict(pid_exists=psutil.pid_exists(pid)) for pid in pids if pid}
    result['accepted'] = bool(result['accepted'] and result['armor_frozen_files_unchanged'] and
        result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and result['exclusive2598_released'] and
        not any(value['pid_exists'] for value in result['owned_pid_terminal'].values()))
    dump(receipt,result)
    print(json.dumps({key:result.get(key) for key in ('accepted','error','candidate_sha256',
        'armor_frozen_files_unchanged','protected_processes_preserved','exclusive2598_released','owned_pid_terminal')}))
    return 0 if result['accepted'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--server-candidate', type=Path)
    parser.add_argument('--candidate-sha')
    parser.add_argument('--contract-path', type=Path)
    parser.add_argument('--port-authorized', action='store_true')
    parser.add_argument('--source-page', type=int, choices=(950,936), default=950)
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    if args.run:
        return owner(args)
    return preparation(args.output)


if __name__ == '__main__':
    raise SystemExit(main())
