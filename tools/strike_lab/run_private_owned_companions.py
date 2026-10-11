"""Stage and run a bounded hidden-desktop own-server acceptance fixture.

All numeric instances below are explicitly synthetic test values. This script
never writes the persistent live server DB, production config, or client EXE.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import time
from .import_companion_metadata import extract,install,SOURCE

ROOT=Path(__file__).resolve().parents[2]
SOURCE_DB=ROOT/'artifacts/playtests/private-game-2598-20260923-01/town-diagnostic-accounts.db'
CONFIG=ROOT/'artifacts/playtests/private-chain-endtoend-20260924-01/server-config.json'
CLIENT=ROOT.parent/'God2/God2-current-lab-2598.exe'
LIVE_CLIENT=ROOT.parent/'God2/God2.exe'
RUNNER=Path(os.environ.get('GOD2_OWNED_PRIVATE_RUNNER',ROOT/'artifacts/playtests/private-inventory-move-20260926-03/private-runner.exe'))
BINARY=Path(os.environ.get('GOD2_OWNED_SERVER_CANDIDATE',ROOT/'build-town-visibility/Release/god2-server-native-results.exe'))
CURRENT_CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
WEAPON_SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'

def seed_weapon_appearance(connection):
    """Mirror current fresh-world component projection, not an item mapping."""
    source=(ROOT/'src/protocol/RecoveredWorldEntry.h').read_bytes()
    match=re.search(rb'static constexpr Body historical_body\s*\{([^}]+)\}',source)
    if not match:raise RuntimeError('Current world-entry baseline initializer unavailable')
    body=bytearray(int(token,16) for token in re.findall(rb'0x([0-9a-fA-F]{2})\b',match[1]))
    profile_row=connection.execute('select profile from recovered_characters where id=4').fetchone()
    if profile_row is None:raise RuntimeError('Disposable character profile missing')
    profile=profile_row[0]
    if len(body)!=36 or len(profile)!=40 or profile[32]>6 or profile[36]>>5>6 or body[32:34]!=b'\0\0':
        raise RuntimeError('Current fresh-world appearance outside qualified profile bounds')
    # RecoveredWorldEntry::decoded(local_id, profile), components only. Preserve
    # every binary/category/ordinal and all other supplied component bits.
    body[13]=(body[13]&31)|(profile[32]<<5)
    body[15]=(body[15]&31)|(profile[36]&224)
    components=bytes(body[12:20])
    logical=b'\xda'+struct.pack('<HHBB',4,int.from_bytes(body[32:34],'little'),body[34],body[35])+components
    expected=(logical,components,1,'CUSTOM_TEST_NOT_NATIVE','hidden-weapon-appearance/profile-world-entry/CUSTOM-0047',CURRENT_CLIENT_SHA,'CUSTOM-0047')
    connection.execute('insert into character_player_appearance_snapshots '
        '(character_id,logical,base_components,revision,origin,provenance,client_sha256,design_id) values(4,?,?,?,?,?,?,?)',expected)
    actual=connection.execute('select logical,base_components,revision,origin,provenance,client_sha256,design_id '
        'from character_player_appearance_snapshots where character_id=4').fetchone()
    if actual!=expected:raise RuntimeError('Disposable appearance readback mismatch')
    return {'logical_hex':logical.hex(),'base_components':components.hex(),'revision':1,'origin':expected[3],
        'provenance':expected[4],'client_sha256':CURRENT_CLIENT_SHA,'design_id':'CUSTOM-0047',
        'world_entry_header_sha256':hashlib.sha256(source).hexdigest(),'profile_sha256':hashlib.sha256(profile).hexdigest(),
        'scope':'Current server fresh-world profile projection as synthetic baseline; fixture weapon mapping is CUSTOM only'}

def seed_weapon_transfers(connection):
    """Disposable synthetic operands, not recovered instance generation."""
    instances=(bytes.fromhex('0100010000000018000000000600000000000000'),
               bytes.fromhex('020001000000001e000000000a00000000000000'))
    connection.execute('delete from character_weapon_slot_metadata where character_id=4 and (slot between 0 and 29 or slot=34)')
    for slot in [*range(30),34]:
        item=slot+1 if slot<2 else 0;count=1 if item else 0
        connection.execute('insert into diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) '
            "values(4,?,?,?,1,?,'CUSTOM-0015') on conflict(character_id,slot) do update set "
            'item_id=excluded.item_id,count=excluded.count,revision=excluded.revision,source_sha256=excluded.source_sha256,design_id=excluded.design_id',
            (slot,item,count,WEAPON_SOURCE_SHA))
        if item:
            connection.execute('insert into character_weapon_slot_metadata '
                '(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) '
                "values(4,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')",
                (slot,instances[slot],f'hidden-weapon-fixture/item{item}/CUSTOM-0046',WEAPON_SOURCE_SHA,CURRENT_CLIENT_SHA))
    actual=connection.execute('select slot,logical20 from character_weapon_slot_metadata where character_id=4 and slot in (0,1) order by slot').fetchall()
    if actual!=[(0,instances[0]),(1,instances[1])]:raise RuntimeError('Disposable weapon metadata readback mismatch')
    return {'instances':[x.hex() for x in instances],'origin':'CUSTOM_TEST_NOT_NATIVE','source_sha256':WEAPON_SOURCE_SHA,
        'client_sha256':CURRENT_CLIENT_SHA,'design_id':'CUSTOM-0046','explicit_slots':[*range(30),34],
        'scope':'Synthetic owned WPN1/2 transfer operands; no native generation, stat formula or appearance claim'}

def seed_role_auxiliary(connection):
    """Only call on the migrated disposable clone; values are test operands."""
    logical=bytearray(61);logical[0]=0x2c
    for offset,value in ((1,2),(5,3),(9,4),(13,5),(45,56),(49,77),(53,88),(57,99)):
        struct.pack_into('<I',logical,offset,value)
    expected=(bytes(logical),1,'CUSTOM_TEST_NOT_NATIVE','hidden-fixture/client6bf/CUSTOM-0045',CURRENT_CLIENT_SHA,'CUSTOM-0045')
    connection.execute('insert into character_role_auxiliary_snapshots '
        '(character_id,logical,revision,origin,provenance,client_sha256,design_id) values(4,?,?,?,?,?,?)',expected)
    actual=connection.execute('select logical,revision,origin,provenance,client_sha256,design_id '
        'from character_role_auxiliary_snapshots where character_id=4').fetchone()
    if actual!=expected:raise RuntimeError('Disposable role auxiliary readback mismatch')
    return {'logical_hex':logical.hex(),'revision':1,'origin':expected[2],'provenance':expected[3],
            'client_sha256':CURRENT_CLIENT_SHA,'design_id':'CUSTOM-0045',
            'modifiers':[2,3,4,5],'physical_attack':77,'physical_defense':56,
            'magical_attack':99,'magical_defense':88,'no_god_fixture':True}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--catalog-database',type=Path,help='Reuse the native-parsed catalog from a preceding isolated acceptance run')
    ap.add_argument('--native-npc-only',action='store_true',help='Suppress unqualified diagnostic NPC placement')
    ap.add_argument('--native-monster-only',action='store_true',help='Suppress unqualified diagnostic encounter placement')
    ap.add_argument('--native-world-records',action='store_true',help='Isolated supplied71/72/78 rendering operands; never original placements')
    ap.add_argument('--quest-source-catalog',action='store_true',help='Import pinned quest source rows into this disposable DB only')
    ap.add_argument('--kunlun-fresh-spawn',action='store_true',help='Verify a disposable character with no saved position enters map4/3')
    ap.add_argument('--owned-quest-journal',action='store_true',help='Restore an explicitly synthetic saved journal in the disposable DB')
    ap.add_argument('--world-clock',action='store_true',help='Verify native clock initialization and periodic server synchronization')
    ap.add_argument('--knowledge-menu',action='store_true',help='Isolated native seven-option UI/85 roundtrip, no NPC spawn or quest grant')
    ap.add_argument('--knowledge-choice',type=int,choices=range(7),default=0)
    ap.add_argument("--map-view",action="store_true",help="Owned Kunlun map use/open/close/reopen; no live grant")
    ap.add_argument('--role-auxiliary',action='store_true',help='Synthetic owned2C restore in the disposable Kunlun/noGod fixture; no stat formula')
    ap.add_argument('--native-weapon-catalog',action='store_true',help='Import pinned WPN/TWP definitions only into the disposable DB')
    ap.add_argument('--weapon-transfers',action='store_true',help='Synthetic owned WPN1/2 double-click28 acceptance in this clone only')
    ap.add_argument('--weapon-appearance',action='store_true',help='Isolated unmounted/noGod CUSTOM weapon component projection after28')
    ap.add_argument('--pet-progression',action='store_true',help='Synthetic nonzero FB levels/stars; verify owned cache restore and transfers')
    ap.add_argument('--pet-categories',action='store_true',help='Native464 display-name catalog with synthetic FB selector operands')
    ap.add_argument('--pet1-mixed',action='store_true',help='Owned E3/FB shared-cell swap and return; synthetic instance values only')
    ap.add_argument('--pet-native-icons',action='store_true',help='Bounded E3/FB icon-resource qualification without synthetic deity fixtures')
    ap.add_argument('--deity-native-icons',action='store_true',help='Verify valid named deity HUD together with mixed pet icons')
    ap.add_argument('--deity-templates',action='store_true',help='Restore native GOD1/2 with the34 original current metadata definitions')
    ap.add_argument('--deity-skill-catalog',action='store_true',help='Isolated sixteen rows/100 skills each; covers409 display-qualified definitions; retains all448 catalog rows')
    args=ap.parse_args()
    if args.role_auxiliary and not args.kunlun_fresh_spawn:ap.error('--role-auxiliary requires --kunlun-fresh-spawn (bounded noGod fixture)')
    if args.pet_progression and args.kunlun_fresh_spawn:ap.error('--pet-progression requires the owned companion fixture')
    if args.pet_categories and not args.pet_progression:ap.error('--pet-categories requires --pet-progression')
    if args.pet1_mixed and (args.kunlun_fresh_spawn or args.pet_categories):ap.error('--pet1-mixed excludes Kunlun/category fixtures')
    if args.pet_native_icons and not args.pet1_mixed:ap.error('--pet-native-icons requires --pet1-mixed')
    if args.deity_native_icons and (not args.pet1_mixed or args.pet_native_icons):
        ap.error('--deity-native-icons requires --pet1-mixed and retained deity fixtures')
    if args.deity_templates and not args.deity_native_icons:ap.error('--deity-templates requires --deity-native-icons')
    if args.deity_skill_catalog and not args.deity_templates:ap.error('--deity-skill-catalog requires --deity-templates')
    if args.weapon_transfers and (args.map_view or args.knowledge_menu):ap.error('--weapon-transfers excludes --map-view/--knowledge-menu fixture conflicts')
    if args.weapon_appearance and (not args.weapon_transfers or not args.kunlun_fresh_spawn or args.role_auxiliary or args.map_view or args.knowledge_menu):
        ap.error('--weapon-appearance requires --weapon-transfers --kunlun-fresh-spawn and excludes role-auxiliary/map-view/knowledge-menu')
    here=args.output.resolve();here.mkdir(parents=True,exist_ok=False)
    result={'accepted':False,'source_db_sha256':sha(SOURCE_DB),'live_client_sha256':sha(LIVE_CLIENT),
            'private_client_sha256':sha(CLIENT),'server_sha256':sha(BINARY)}
    db=here/('knowledge-menu-diagnostic.db' if args.knowledge_menu else 'town-diagnostic-accounts.db')
    with closing(sqlite3.connect(SOURCE_DB.resolve().as_uri()+'?mode=ro',uri=True)) as source:
        with closing(sqlite3.connect(db)) as target:source.backup(target)
    config=json.loads(CONFIG.read_text('utf-8'));config['database']['path']=str(db)
    config['logging']['file']=str(here/'server.log')
    config['server']['port']=2598;config['development']['diagnostic_world_resources']=False
    for key,value in list(config['development'].items()):
        if key.startswith('diagnostic_battle_') and isinstance(value,bool):config['development'][key]=False
    config['development']['diagnostic_town'].update(battle_after_quest=False,door_after_battle=False)
    config['development']['diagnostic_town']['native_npc_placements_only']=args.native_npc_only
    config['development']['native_monster_placements_only']=args.native_monster_only
    if args.knowledge_menu:
        config['development']['diagnostic_knowledge_menu']=True
        config['development']['diagnostic_quest_dialogue']=False
    if args.kunlun_fresh_spawn:
        config['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
            'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'}}
    if args.world_clock:config.setdefault('world',{})['clock']={'enabled':True,'sync_seconds':5}
    if args.weapon_transfers:
        config.setdefault('world',{})['owned_weapon_transfers']={'enabled':True}
        config['development']['diagnostic_town']['quest_progress']=False
        config['development']['diagnostic_town']['map_probe']=False
    if args.weapon_appearance:
        config.setdefault('world',{})['owned_player_appearance']={'enabled':True}
        config['development']['diagnostic_owned_weapon_appearance']=True
        for key in ('diagnostic_player_visibility','diagnostic_town_player_visibility','diagnostic_remote_actor'):
            config['development'][key]=False
    if args.map_view:
        if not args.kunlun_fresh_spawn:raise ValueError('Map acceptance requires Kunlun fresh fixture')
        config.setdefault('world',{})['owned_map_views']={'enabled':True}
        config['development']['diagnostic_town']['quest_progress']=False
        config['development']['diagnostic_town']['map_probe']=False
    cfg=here/'server-config.json';cfg.write_text(json.dumps(config,indent=2),encoding='utf-8')
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    if args.native_world_records:
        if not args.kunlun_fresh_spawn or not here.name.startswith('private-native-blackbox-'):
            raise ValueError('World-record fixture requires isolated named Kunlun lab')
        env['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    with (here/'migration.log').open('wb') as output:
        subprocess.run([str(BINARY),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=env,
            stdout=output,stderr=subprocess.STDOUT,creationflags=flags,check=True,timeout=15)
    if args.native_weapon_catalog or args.weapon_transfers:
        from . import import_native_weapons as weapons
        records=weapons.cached_records(ROOT/'artifacts/research/native-weapons-20260926/records.json')
        with closing(sqlite3.connect(db)) as connection:
            result['native_weapon_import']=weapons.import_catalog(connection,records=records)
    if args.quest_source_catalog or args.owned_quest_journal:
        from . import import_native_quests,import_native_quest_requirements,import_native_quest_sources
        with closing(sqlite3.connect(db)) as connection:
            result['quest_source_import']={
                'missions':import_native_quests.import_catalog(connection,LIVE_CLIENT.parent),
                'requirements':import_native_quest_requirements.import_catalog(connection,LIVE_CLIENT.parent),
                'sources':import_native_quest_sources.import_catalog(connection,LIVE_CLIENT.parent)}
    if args.knowledge_menu:
        from . import import_native_multi_messages
        with closing(sqlite3.connect(db)) as connection:
            result['multi_message_import']=import_native_multi_messages.import_catalog(connection,LIVE_CLIENT.parent)
    if args.map_view:
        from . import import_native_catalog,import_native_map_items
        with closing(sqlite3.connect(db)) as connection:
            result['map_sources']={'maps':import_native_catalog.import_catalog(connection,LIVE_CLIENT.parent),'items':import_native_map_items.import_catalog(connection,LIVE_CLIENT.parent)}
    if args.native_world_records:
        from . import import_native_npc_display,import_native_enemy_display
        with closing(sqlite3.connect(db)) as connection:
            result['npc_catalog']=import_native_npc_display.install(connection,CLIENT.parent)
            result['monster_catalog']=import_native_enemy_display.import_catalog(connection,CLIENT.parent)
            npc=bytearray(bytes.fromhex('72000000000060000000000000cf01000000000000'))
            struct.pack_into('<H',npc,1,3793);npc[5]=88;npc[6]=0x66;npc[9]=0xa1
            struct.pack_into('<I',npc,17,(124<<2)|(126<<17))
            monster=bytearray(21);monster[0]=0x71
            struct.pack_into('<I',monster,1,123|(6<<29));struct.pack_into('<H',monster,5,1)
            struct.pack_into('<I',monster,9,(128<<2)|(126<<17));struct.pack_into('<H',monster,19,8)
            for raw in (npc,monster):
                identity=int.from_bytes(raw[1:3],'little')
                connection.execute('insert into world_display_records values(4,3,?,?,?,?,?,?)',
                    (raw[0],identity,bytes(raw),'ISOLATED_TEST_ONLY','synthetic hidden acceptance operands; not native positions',
                     '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'))
            connection.execute("insert into world_monster_levels values(4,3,113,123,27,'ISOLATED_TEST_ONLY','synthetic level; exact native78 consumer test')")
            connection.commit()
    if args.catalog_database:
        with closing(sqlite3.connect(args.catalog_database.resolve().as_uri()+'?mode=ro',uri=True)) as catalog:
            rows=catalog.execute("select * from native_companion_metadata where family='NCP' order by metadata_key").fetchall()
        if len(rows)!=1165 or any(row[2]!=SOURCE or hashlib.sha256(row[4]).hexdigest()!=row[5] or len(row[6])!=396 for row in rows):
            raise ValueError('Reused native NCP catalog is unqualified')
        result['metadata_import']=install(db,rows)
        result['metadata_catalog_reused_from']=str(args.catalog_database.resolve())
    else:result['metadata_import']=install(db,extract())
    if args.pet1_mixed:
        from . import import_native_pet1_metadata as pet1
        result['pet1_import']=pet1.install(db,pet1.cached(ROOT/'artifacts/research/native-pet1-20260927/records.json'))
    if args.deity_templates:
        from . import import_native_deity_metadata as gods
        result['deity_import']=gods.install(db,gods.cached(ROOT/'artifacts/research/native-deity-metadata-20260927/records.json'))
    if args.deity_skill_catalog:
        from . import import_native_skills as skills
        with closing(sqlite3.connect(db)) as connection:
            result['native_skill_import']=skills.import_catalog(connection,LIVE_CLIENT.parent)
    if args.pet_categories:
        from . import import_native_pet2_categories as categories
        with closing(sqlite3.connect(db)) as connection:
            result['category_import']=categories.install(connection,categories.cached(
                ROOT/'artifacts/research/native-pet2-categories-20260927/records.json'))
    with closing(sqlite3.connect(db)) as connection:
        # Explicit disposable owned fixtures. No value is claimed as original
        # starting stats, growth, recruitment reward or combat formula.
        connection.execute('insert into character_resources values(4,52,120,26,80,1,?)',('CUSTOM-0012',))
        role=bytearray(25);role[0]=0x22;role[1]=1
        struct.pack_into('<4H',role,5,10,10,10,10);struct.pack_into('<II',role,17,120,80)
        connection.execute('insert into character_role_snapshots values(4,?,1,?)',(bytes(role),'CUSTOM-0013'))
        if args.role_auxiliary:
            if result['live_client_sha256']!=CURRENT_CLIENT_SHA:raise RuntimeError('Role auxiliary client pin mismatch')
            result['role_auxiliary_fixture']=seed_role_auxiliary(connection)
        if args.weapon_transfers:
            if result['live_client_sha256']!=CURRENT_CLIENT_SHA:raise RuntimeError('Weapon transfer client pin mismatch')
            result['weapon_transfer_fixture']=seed_weapon_transfers(connection)
        if args.weapon_appearance:result['weapon_appearance_fixture']=seed_weapon_appearance(connection)
        if args.kunlun_fresh_spawn:connection.execute('delete from recovered_positions where character_id=4')
        else:connection.execute('update recovered_positions set area=2,scene=4,x=88,y=75,revision=revision+1 where character_id=4')
        assigned=None
        if args.deity_skill_catalog:
            from .owned_deity_skill_fixture import verified_catalog,assignments
            assigned=assignments(verified_catalog(connection,LIVE_CLIENT.parent))
            result['deity_skill_fixture']=dict(owned_rows=16,skills_per_row=100,learned_instances=1600,distinct_definitions=409,
                catalog_definitions=448,unavailable_icons=39,
                ownership_authority='CUSTOM_TEST_NOT_NATIVE',definition_authority='NATIVE_VERIFIED',production_grants=0)
        for key in (range(1,17) if assigned else ((1,2) if args.deity_templates else (101,102))):
            declaration=bytearray(19);declaration[0]=0x30;declaration[1]=key
            name=f'LabGod{key}'.encode('ascii');declaration[2:2+len(name)]=name
            status=bytearray(29);status[0]=0x31;status[1]=key;status[2]=1
            struct.pack_into('<5H',status,3,10,11,12,13,14);struct.pack_into('<4H',status,17,31,12,28,11)
            connection.execute('insert into character_deities values(4,?,?,?,?,1,?,?,?)',
                (key,bytes(declaration),bytes(status),assigned[key] if assigned else bytes((0x34,key,0,1)),SOURCE,
                 'CUSTOM_TEST_NOT_NATIVE','private-owned-companion-fixture-20260926'))
        connection.execute('insert into character_deity_selection values(4,?,1)',(1 if args.deity_templates else 101,))
        for slot,key in ((42,28001),(43,28002),(44,0)):
            if args.pet1_mixed and slot==42:
                key=24001;metadata=bytearray(20);struct.pack_into('<H',metadata,0,key);metadata[2]=32
                stats=bytearray(53);stats[0]=0xe3
                struct.pack_into('<4H',stats,1,50,100,20,40)
                struct.pack_into('<5I',stats,9,31|(10<<12)|(11<<22),12|(12<<12)|(13<<22),
                    28|(14<<12)|(15<<22),11|(16<<12)|(17<<22),18|(1234<<10)|(19<<24))
                struct.pack_into('<H',stats,29,key);stats[31:36]=bytes((20,21,22,100,37))
                struct.pack_into('<H',stats,37,23);stats[39]=slot;stats[40]=2
                result['pet1_instance_authority']='SYNTHETIC_OWNED_TEST_VALUES_NOT_GROWTH'
            elif key:
                metadata=bytearray(20);struct.pack_into('<H',metadata,0,key);metadata[2]=34
                stats=bytearray(73);stats[0]=0xfb;struct.pack_into('<H',stats,1,key);stats[3]=slot
                if args.pet_progression:
                    stats[4]=37 if slot==42 else 98
                    stats[12]=0xa5 if slot==42 else 0x5a
                if args.pet_categories:
                    stats[45]=0xf2 if slot==42 else 0xff
                    stats[61]=1 if slot==42 else 29
                struct.pack_into('<I',stats,5,50|(20<<14));struct.pack_into('<I',stats,13,100|(40<<14))
                struct.pack_into('<4H',stats,17,31,12,28,11)
                for at in (25,27,29,31,33,37,39,41,43):struct.pack_into('<H',stats,at,10)
            else:metadata=stats=b''
            connection.execute('insert into character_pet2_slots values(4,?,?,?,1,?,?,?)',
                (slot,bytes(metadata),bytes(stats),SOURCE,'CUSTOM_TEST_NOT_NATIVE','private-owned-companion-fixture-20260926'))
        if args.kunlun_fresh_spawn:
            # Map acceptance uses no synthetic companion graphics; this is a
            # disposable cloned DB, not a change to any player-owned instance.
            connection.execute('delete from character_deity_selection where character_id=4')
            connection.execute('delete from character_deities where character_id=4')
            connection.execute('delete from character_pet2_slots where character_id=4')
        if args.pet_native_icons:
            # Controlled icon isolation in this clone only. No live deity or
            # owned pet changes; retain both generations and all five moves.
            connection.execute('delete from character_deity_selection where character_id=4')
            connection.execute('delete from character_deities where character_id=4')
        if args.map_view:
            connection.execute('update diagnostic_inventory_slots set item_id=5576,count=1,revision=revision+1 where character_id=4 and slot=0')
            connection.execute('delete from diagnostic_town_guide_progress where character_id=4')
        if args.owned_quest_journal:
            values=[(1<<16)|44,(5<<16)|48,47]+[0]*11+[(3<<16)|50]
            connection.execute('insert into character_quest_journals values(4,?,1,?,?,?)',
                (struct.pack('<15I',*values),'CUSTOM_TEST_NOT_NATIVE','isolated-journal-display-20260926','CUSTOM-0041'))
        connection.commit()
    process=runner=None
    try:
        with (here/'stdout.log').open('wb') as output:
            process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','150'],cwd=ROOT,env=env,
                stdout=output,stderr=subprocess.STDOUT,creationflags=flags)
            result['server_pid']=process.pid
            deadline=time.monotonic()+10
            while True:
                if process.poll() is not None:raise RuntimeError('Private server exited')
                try:
                    with socket.create_connection(('127.0.0.1',2598),timeout=.1):break
                except OSError:
                    if time.monotonic()>deadline:raise RuntimeError('Private server did not listen')
                    time.sleep(.05)
            observer=[sys.executable,'-X','utf8','-B',str(ROOT/'tools/strike_lab/private_owned_companions_ui.py'),
                str(here/'ui-result.json'),str(db),str(here/'server.log'),'--client-exe',str(CLIENT)]
            if args.kunlun_fresh_spawn:observer.append('--expect-kunlun')
            if args.native_world_records:observer.append('--expect-native-world-records')
            if args.owned_quest_journal:observer.append('--expect-quest-journal')
            if args.world_clock:observer.append('--expect-world-clock')
            if args.map_view:observer.append('--expect-map-view')
            if args.role_auxiliary:observer.append('--expect-role-auxiliary')
            if args.weapon_transfers:observer.append('--expect-weapon-transfers')
            if args.weapon_appearance:observer.append('--expect-weapon-appearance')
            if args.pet1_mixed:observer.append('--expect-pet1-mixed')
            if args.pet_native_icons:observer.append('--expect-pet-native-icons')
            if args.deity_native_icons:observer.append('--expect-deity-native-icons')
            if args.deity_templates:observer.append('--expect-deity-templates')
            if args.deity_skill_catalog:observer.append('--expect-deity-skill-catalog')
            if args.knowledge_menu:observer.extend(['--expect-knowledge-menu','--knowledge-choice',str(args.knowledge_choice)])
            private_env=os.environ.copy();private_env['GOD2_PRIVATE_SIDECAR_COMMAND']=subprocess.list2cmdline(observer)
            private_env['GOD2_PRIVATE_SIDECAR_WAIT_MS']='120000'
            command=[str(RUNNER),str(CLIENT),'127.0.0.1','127.0.0.1','6001','1']
            result['game_command']=command;result['sidecar_command']=observer
            with (here/'runner.log').open('wb') as runner_output:
                runner=subprocess.Popen(command,cwd=CLIENT.parent,env=private_env,stdout=runner_output,
                    stderr=subprocess.STDOUT,creationflags=flags)
                result['runner_pid']=runner.pid;result['runner_exit']=runner.wait(timeout=110)
            result['ui']=json.loads((here/'ui-result.json').read_text('utf-8'))
            result['accepted']=result['ui']['accepted']
    finally:
        for target in (runner,process):
            if target and target.poll() is None:target.terminate();target.wait(timeout=5)
        result['source_db_unchanged']=sha(SOURCE_DB)==result['source_db_sha256']
        result['live_client_unchanged']=sha(LIVE_CLIENT)==result['live_client_sha256']
        result['private_client_unchanged']=sha(CLIENT)==result['private_client_sha256']
        (here/'run-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('accepted','source_db_unchanged','live_client_unchanged','private_client_unchanged')}))
    return 0 if result['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
