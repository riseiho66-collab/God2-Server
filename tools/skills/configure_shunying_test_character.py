"""Configure only the explicitly authorized isolated character 6 / test fixture.

No production database, source code, or unrelated character is modified.
Known native 22 fields use the existing CUSTOM-0013 diagnostic baseline when absent.
"""
from pathlib import Path
import datetime
import hashlib
import json
import sqlite3
import struct
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'artifacts/playtests/private-shunying-manual-20260930-01'
DATABASE = FIXTURE / 'diagnostic-accounts.db'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
# Explicit CUSTOM-0058 test instances, not recovered original generation rules.
# Native 4B45B0/4B4690 fields: +7 physical, +12 magical, +8..11 Str/Con/Int/Speed.
ITEMS = ((30,1426,'EQU',23,7,0,0,30,0),
         (31,1026,'EQU',25,7,0,30,0,0),
         (32,1526,'EQU',16,16,30,0,0,0),
         (33,1626,'EQU',16,16,0,0,0,30),
         (34,126,'WPN',61,19,48,0,48,0))


def equipment(db):
    from tools.strike_lab.omega_assets import decode_csvz
    from tools.strike_lab.recover_items import lines_of, section
    from tools.strike_lab.import_native_weapons import validate_records, TABLES, ORDERS
    source = ROOT.parent / 'God2/Data2/Patch/Comm/gamedata.csvZ'
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    lines = lines_of(decode_csvz(raw))
    source_rows = {(family,int(row.split(b',')[0])):(line,row)
                   for family in ('WPN','EQU') for line,row in section(lines,family.encode())
                   if row.split(b',')[0].isdigit()}
    # This client now carries the requested clone DLL hook. Reuse only the exact
    # fingerprinted native catalog extracted before that hook, not a fresh claim
    # that the modified executable still has the original whole-file hash.
    cached = json.loads((ROOT/'artifacts/research/native-weapons-20260926/records.json').read_text(encoding='utf-8-sig'))
    for row in cached[1]:
        row[6],row[8] = bytes.fromhex(row[6]),bytes.fromhex(row[8])
    records = validate_records(cached)
    report = []
    db.execute('BEGIN IMMEDIATE')
    actual = tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o)) for t,o in zip(TABLES,ORDERS))
    if any(actual):
        assert actual == records, 'Existing catalog conflicts with fingerprinted source'
    else:
        for table,rows in zip(TABLES,records):
            db.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in rows[0])+')',rows)
    for slot,item,family,physical,magical,strength,constitution,intelligence,speed in ITEMS:
        line,row = source_rows[family,item]
        fields = row.split(b',')
        assert fields[28] == b'50' and fields[16] == b'1'
        # Preserve the established CUSTOM-0046 template's opaque instance bytes.
        instance = bytearray.fromhex('0100010000000018000000000600000000000000')
        struct.pack_into('<H', instance, 0, item)
        instance[7:13] = bytes((physical,strength,constitution,intelligence,speed,magical))
        previous = db.execute('SELECT revision FROM diagnostic_inventory_slots WHERE character_id=6 AND slot=?',(slot,)).fetchone()
        revision = previous[0]+1 if previous else 1
        db.execute("INSERT INTO diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) VALUES(6,?,?,1,?,?,'CUSTOM-0015') ON CONFLICT(character_id,slot) DO UPDATE SET item_id=excluded.item_id,count=1,revision=excluded.revision,source_sha256=excluded.source_sha256",(slot,item,revision,SOURCE_SHA))
        if slot == 34:
            db.execute("INSERT INTO character_weapon_slot_metadata(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) VALUES(6,34,?,?,'CUSTOM_TEST_NOT_NATIVE','CUSTOM-0058/test/LV50/WPN126/native-tooltip-fields',?,?,'CUSTOM-0046') ON CONFLICT(character_id,slot) DO UPDATE SET logical20=excluded.logical20,revision=excluded.revision,origin=excluded.origin,provenance=excluded.provenance",(instance,revision,SOURCE_SHA,CLIENT_SHA))
        logical = bytes((0x41,item&255,item>>8,slot,1,0x3b,1,slot,0,0)) + instance
        report.append(dict(slot=slot,item_id=item,family=family,name=fields[4].decode('cp950'),source_line=line,source_record_hex=row.hex(),instance_hex=instance.hex(),logical_hex=logical.hex(),origin='CUSTOM_TEST_NOT_NATIVE'))
    # Native HeroDoll component order is body, face/hair, head, weapon.
    # Item descriptions specify sixth tier; Fight HeroDoll labels w105 as 巨闕劍.
    # The original item->doll server join is unavailable. This explicit fixture
    # selects real sixth-tier female assets and wood palette2, not item IDs as selectors.
    doll = ROOT.parent / 'God2/Data2/Patch/HeroDoll.csvZ'
    doll_rows = decode_csvz(doll.read_bytes()).splitlines()
    expected = [(b'r2',b'b205',b'r02b205.romz'),(b'r2',b'h305',b'r02h305.romz'),(b'r2',b'w105',b'r02w105.romz')]
    assets = []
    for role,key,filename in expected:
        matches = [(i+1,r) for i,r in enumerate(doll_rows) if r.split(b',')[:2] == [role,key]]
        assert len(matches) == 1 and matches[0][1].split(b',')[3] == filename
        path = ROOT.parent / 'God2/Data2/Rom/RoleDoll' / filename.decode()
        assert path.is_file()
        assets.append(dict(key=(role+key).decode(),source_line=matches[0][0],filename=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    profile = db.execute('SELECT profile FROM recovered_characters WHERE id=6').fetchone()[0]
    # Existing historical female world baseline + selected profile palettes.
    baseline = bytes((1,profile[32]<<5,1,profile[36]&224,1,0x60,0x31,0))
    components = bytes((0x21,0x45,1,profile[36]&224,0x31,0x45,0x11,0x45))
    appearance = b'\xda'+struct.pack('<HHBB',6,0,0,0)+components
    provenance = 'CUSTOM-0058/test/female-tier6-armor-h305-b205-sword-w105/wood-palette2;explicit-fixture-not-native-item-join'
    db.execute("INSERT INTO character_player_appearance_snapshots(character_id,logical,base_components,revision,origin,provenance,client_sha256,design_id) VALUES(6,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,'CUSTOM-0047') ON CONFLICT(character_id) DO UPDATE SET logical=excluded.logical,revision=revision+1,origin=excluded.origin,provenance=excluded.provenance",(appearance,baseline,provenance,CLIENT_SHA))
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    assert db.execute('SELECT logical FROM character_player_appearance_snapshots WHERE character_id=6').fetchone()[0] == appearance
    assert db.execute('SELECT slot,item_id,count FROM diagnostic_inventory_slots WHERE character_id=6 AND slot BETWEEN 30 AND 34 ORDER BY slot').fetchall() == [(a[0],a[1],1) for a in ITEMS]
    db.commit()
    result = dict(character_id=6,origin='CUSTOM_TEST_NOT_NATIVE',source_sha256=SOURCE_SHA,items=report,projection_hex=''.join(r['logical_hex'] for r in report),appearance_logical_hex=appearance.hex(),appearance_components_hex=components.hex(),assets=assets,appearance_join='Explicit CUSTOM-0058 selection of source-backed sixth-tier female equipment assets; original server item-to-doll join and wood palette correspondence not recovered.',instance_generation='Existing CUSTOM-0046 baseline with only identified tooltip fields replaced by source definition base values; not native generation or combat stat formula.')
    (FIXTURE/'test-equipment-configuration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def verify():
    manifest = json.loads((FIXTURE/'test-equipment-configuration.json').read_text(encoding='utf-8'))
    text = (ROOT/'src/protocol/DiagnosticShunyingEquipment.h').read_text(encoding='utf-8')
    arrays = re.findall(r'\{(3[0-4]),\{([^}]+)\}\}', text)
    assert len(arrays) == 5
    projection = b''
    with sqlite3.connect(f'file:{DATABASE.as_posix()}?mode=ro', uri=True) as db:
        assert db.execute('SELECT account_id,name_bytes FROM recovered_characters WHERE id=6').fetchone() == (6,b'test')
        role = db.execute('SELECT logical FROM character_role_snapshots WHERE character_id=6').fetchone()[0]
        assert role[1] == 50 and struct.unpack_from('<4H',role,5) == (666,)*4
        assert struct.unpack_from('<II',role,17) == (9999,9999)
        assert db.execute('SELECT hp,max_hp,mp,max_mp FROM character_resources WHERE character_id=6').fetchone() == (9999,)*4
        for (slot,raw),expected in zip(arrays,manifest['items']):
            slot = int(slot)
            instance = bytes(int(v.strip(),0) for v in raw.split(','))
            assert len(instance) == 20 and instance.hex() == expected['instance_hex']
            assert slot == expected['slot']
            item = int.from_bytes(instance[:2],'little')
            assert db.execute('SELECT item_id,count FROM diagnostic_inventory_slots WHERE character_id=6 AND slot=?',(slot,)).fetchone() == (item,1)
            projection += bytes((0x41,instance[0],instance[1],slot,1,0x3b,1,slot,0,0))+instance
            if slot == 34:
                assert db.execute('SELECT logical20 FROM character_weapon_slot_metadata WHERE character_id=6 AND slot=34').fetchone()[0] == instance
        assert len(projection) == 150 and projection.hex() == manifest['projection_hex']
        appearance = db.execute('SELECT logical FROM character_player_appearance_snapshots WHERE character_id=6').fetchone()[0]
        assert appearance.hex() == manifest['appearance_logical_hex'] and appearance[7:].hex() == manifest['appearance_components_hex']
        assert db.execute('PRAGMA quick_check').fetchone() == ('ok',)
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    result = dict(status='PASS',character_id=6,level=50,base_attributes=[666]*4,hp_mp=9999,equipment_slots=[30,31,32,33,34],cpp_manifest_db_bytes_identical=True,projection_bytes=len(projection),appearance_components_hex=appearance[7:].hex(),rendered_client_appearance='Not asserted by this database/codec check')
    (FIXTURE/'test-character-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


def run():
    if not DATABASE.is_file() or DATABASE.resolve().parent != FIXTURE.resolve():
        raise RuntimeError('Only the named existing isolated fixture is permitted')
    db = sqlite3.connect(DATABASE)
    db.execute('PRAGMA foreign_keys=ON')
    target = db.execute('SELECT account_id,name_bytes FROM recovered_characters WHERE id=6').fetchone()
    if target != (6, b'test'):
        raise RuntimeError('Expected character 6 / account 6 / exact test name')
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = FIXTURE / ('diagnostic-accounts.before-test-character-' + stamp + '.db')
    with sqlite3.connect(backup) as destination:
        db.backup(destination)
    db.execute('BEGIN IMMEDIATE')
    tables = ('character_resources', 'character_role_snapshots')
    before = {t: db.execute(f'SELECT * FROM {t} WHERE character_id<>6 ORDER BY character_id').fetchall() for t in tables}
    previous = db.execute('SELECT logical,revision FROM character_role_snapshots WHERE character_id=6').fetchone()
    if previous:
        logical = bytearray(previous[0])
        if len(logical) != 25 or logical[0] != 0x22:
            raise RuntimeError('Malformed existing native22 snapshot')
        revision = previous[1] + 1
    else:
        # DiagnosticBattleParticipants::diagnostic_role_level_seed, CUSTOM-0013.
        logical = bytearray(25)
        logical[0] = 0x22
        revision = 1
    logical[1] = 50
    struct.pack_into('<4H', logical, 5, 666, 666, 666, 666)
    struct.pack_into('<II', logical, 17, 9999, 9999)
    db.execute("INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(6,?,?,'CUSTOM-0013') ON CONFLICT(character_id) DO UPDATE SET logical=excluded.logical,revision=excluded.revision", (logical, revision))
    db.execute("INSERT INTO character_resources(character_id,hp,max_hp,mp,max_mp,revision,design_id) VALUES(6,9999,9999,9999,9999,1,'CUSTOM-0012') ON CONFLICT(character_id) DO UPDATE SET hp=9999,max_hp=9999,mp=9999,max_mp=9999,revision=revision+1")
    assert all(before[t] == db.execute(f'SELECT * FROM {t} WHERE character_id<>6 ORDER BY character_id').fetchall() for t in tables)
    assert db.execute('SELECT logical FROM character_role_snapshots WHERE character_id=6').fetchone()[0] == bytes(logical)
    assert db.execute('SELECT hp,max_hp,mp,max_mp FROM character_resources WHERE character_id=6').fetchone() == (9999,9999,9999,9999)
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    db.commit()
    gear = equipment(db) if '--equipment' in sys.argv else None
    result = dict(database=str(DATABASE), backup=str(backup), character_id=6, name='test', level=50, base_attributes=[666]*4, hp=9999, max_hp=9999, mp=9999, max_mp=9999, role_logical_hex=logical.hex(), unrelated_character_rows_unchanged=True)
    (FIXTURE / 'test-character-configuration.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    if gear:
        print(json.dumps(gear,ensure_ascii=True))
    db.close()


if __name__ == '__main__':
    verify() if '--verify' in sys.argv else run()
