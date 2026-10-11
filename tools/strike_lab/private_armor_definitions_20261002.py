"""Armor source-only Application startup and original TW/CN regression.

NEW wrapper reuses the frozen original bank-swap20 UI workflow verbatim. Bank
acceptance is existing-gameplay regression, NOT armor equip/unequip acceptance.
No foreground activation, screenshot, memory write, packet injection or grants.
Only a disposable cloned database and port-only private images are used.
"""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil
import private_bank_swap_20261002 as bank
from private_inventory_move_ui import desktop_names,require
from tools.strike_lab import import_native_armor_20261002 as armor

CANDIDATE_SHA='80060831f15e4f27667745848ba9c18fefec441106c935e72f4b64089a6a36ed'
CATALOG_SHA='29d1de3729c843571c3a7bc117beb12289bd7110932ec45fc5d846b627282efe'
STARTUP='NATIVE_ARMOR_DEFINITIONS equ=692 teq=662 authority=NATIVE_PARSED_DEFINITION_ONLY no_instances no_combat_formula'
SOURCE_PREPARE=bank.prepare
BASE_FILE=Path(bank.base.__file__).resolve()

def table_groups(db):
    return tuple(tuple(tuple(row) for row in db.execute('SELECT * FROM '+table+' ORDER BY '+order))
                 for table,order in zip(armor.TABLES,armor.ORDERS))

def unrelated(db):
    return {name:sorted(repr(tuple(row)) for row in db.execute('SELECT * FROM "'+name.replace('"','""')+'"'))
            for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            if name not in armor.TABLES}

def prepare(args):
    require(bank.base.sha(args.server_candidate)==CANDIDATE_SHA,'ARMOR_IMMUTABLE_CANDIDATE_CHANGED')
    SOURCE_PREPARE(args)
    database=args.output/'town-diagnostic-accounts.db'
    with closing(sqlite3.connect(database)) as db:
        migration=db.execute('SELECT version,name,sql_text FROM schema_migrations WHERE version=41').fetchone()
        require(migration and migration[:2]==(41,'native_armor_definitions'),'REAL_CANDIDATE_MIGRATION41_MISSING')
        require(table_groups(db)==((),()),'PRIVATE_FIXTURE_ARMOR_NOT_EMPTY_BEFORE_IMPORT')
        before=unrelated(db)
        records=armor.cached_records(armor.RECORDS)
        imported=armor.import_catalog(db,records=records)
        current=table_groups(db)
        require(current==records and armor.fingerprint(current)==CATALOG_SHA,'ARMOR_FULL_NATIVE_CATALOG_IMPORT_MISMATCH')
        require(imported['inserted']==1354 and imported['player_instances_created']==0 and imported['combat_rules_created']==0,
                'ARMOR_IMPORT_IS_NOT_SOURCE_ONLY')
        require(before==unrelated(db),'ARMOR_IMPORT_CHANGED_UNRELATED_DATA')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',) and
                db.execute('PRAGMA foreign_key_check').fetchone() is None,'ARMOR_PRIVATE_DB_INTEGRITY_FAILED')
    bank.base.peer.dump(args.output/'armor-import.json',dict(migration41_version=migration[0],
        migration41_name=migration[1],migration41_sql_sha256=hashlib.sha256(migration[2].encode()).hexdigest(),
        import_result=imported,catalog_fingerprint=CATALOG_SHA,source_rows=2,definition_rows=1354,
        current_equals_all_pinned_records=True,unrelated_rows_preserved=True,
        scope='Definition catalog only, no armor20byte instance grants or combat predicates'))
    fixture=json.loads((args.output/'fixture.json').read_text(encoding='utf-8'))
    fixture['armor_catalog']={'sources':2,'equ':692,'teq':662,'fingerprint':CATALOG_SHA,
        'authority':'NATIVE_PARSED_DEFINITION_ONLY','player_instances_created':0,'combat_rules_created':0}
    bank.base.peer.dump(args.output/'fixture.json',fixture)

bank.base.prepare=prepare

def worker(args):
    database=args.output/'town-diagnostic-accounts.db'
    with closing(bank.base.peer.ro(database)) as db:
        require(armor.fingerprint(table_groups(db))==CATALOG_SHA,'ARMOR_WORKER_START_FINGERPRINT_MISMATCH')
    require(STARTUP in (args.output/'server.log').read_text(encoding='utf-8',errors='strict'),
            'REAL_APPLICATION_ARMOR_STARTUP_LOG_MISSING')
    # This is exactly the old accepted twenty original UI mutations. We do not
    # copy or edit any bank controls, coordinates, retries or native readers.
    code=bank.worker(args)
    with closing(bank.base.peer.ro(database)) as db:
        records=armor.cached_records(armor.RECORDS)
        preserved=table_groups(db)==records and armor.fingerprint(table_groups(db))==CATALOG_SHA
    result=json.loads((args.output/'ui-result.json').read_text(encoding='utf-8'))
    result['armor_definition_catalog_all_rows_preserved']=preserved
    result['armor_acceptance_scope']='SOURCE_ONLY_STARTUP_AND_EXISTING_BANK_GAMEPLAY_REGRESSION_NOT_ARMOR_EQUIP'
    result['accepted']=bool(result['accepted'] and preserved)
    bank.base.peer.dump(args.output/'ui-result.json',result)
    return 0 if not code and result['accepted'] else 1

def protected_processes():
    rows={}
    for p in psutil.process_iter(['pid','exe','create_time']):
        path=p.info['exe']
        if path and (Path(path).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe') or
                     str(bank.base.LIVE.parent).lower() in str(Path(path).resolve()).lower()):
            rows[str(p.pid)]={'exe':str(Path(path).resolve()),'create_time':p.info['create_time']}
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--server-candidate',type=Path)
    p.add_argument('--source-page',type=int,choices=(950,936),default=950)
    p.add_argument('--npc-hex',default='')
    p.add_argument('--worker',action='store_true')
    a=p.parse_args()
    if a.worker:return worker(a)
    if a.server_candidate is None:p.error('--server-candidate required')
    if not a.npc_hex:p.error('--npc-hex required for qualified private CUSTOM_TEST banker')
    require(bank.base.sha(a.server_candidate)==CANDIDATE_SHA,'ARMOR_CANDIDATE_PIN_FAILED')
    bank.qualify();os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    desktop_before=desktop_names();processes_before=protected_processes()
    guards={str(f):bank.base.sha(f) for f in (Path(__file__).resolve(),Path(bank.__file__).resolve(),
        BASE_FILE,Path(armor.__file__).resolve(),armor.RECORDS,armor.ORIGINAL,armor.CLIENT/armor.SOURCE,
        Path(bank.pose.__file__).resolve())}
    bank.base.__file__=str(Path(__file__).resolve())
    code=bank.base.owner(a)
    receipt=a.output/'run-result.json'
    if not receipt.exists():return code
    result=json.loads(receipt.read_text(encoding='utf-8'))
    guards_after={f:bank.base.sha(Path(f)) for f in guards}
    processes_after=protected_processes()
    result['armor_wrapper_guards_before']=guards
    result['armor_wrapper_guards_after']=guards_after
    result['armor_wrapper_files_unchanged']=guards==guards_after
    result['protected_processes_before']=processes_before
    result['protected_processes_preserved']=all(processes_after.get(pid)==entry for pid,entry in processes_before.items())
    result['desktop_owner_before']=desktop_before
    result['desktop_owner_after']=desktop_names()
    result['desktop_owner_unchanged']=result['desktop_owner_before']==result['desktop_owner_after']
    log=(a.output/'server.log').read_text(encoding='utf-8',errors='replace')
    result['real_application_armor_startup_matches']=log.count(STARTUP)
    with closing(bank.base.peer.ro(a.output/'town-diagnostic-accounts.db')) as db:
        records=armor.cached_records(armor.RECORDS)
        result['armor_full_rows_preserved']=table_groups(db)==records
        result['armor_catalog_fingerprint']=armor.fingerprint(table_groups(db))
    result['scope']='SOURCE_ONLY_MIGRATION41_IMPORT_AND_APPLICATION_STARTUP_WITH_TW_CN_BANK20_REGRESSION'
    result['armor_equipment_live_acceptance']=False
    result['armor20byte_grants_created']=0
    result['CUSTOM0066_Application_gearroute_live_acceptance']=False
    ui=result.get('ui',{})
    mutations=[event for event in ui.get('events',[]) if event.get('operation') in ('0x63','0x64','0x65')]
    result['existing_gameplay_mutations']=len(mutations)
    result['existing_gameplay_opcode_counts']=dict(Counter(event['operation'] for event in mutations))
    with socket.socket() as probe:result['exclusive2598_released']=probe.connect_ex(('127.0.0.1',2598))!=0
    pids=[result.get('server_pid'),result.get('runner_pid')]+ui.get('owned_client_pids',[])
    result['owned_pid_terminal']={str(pid):{'pid_exists':psutil.pid_exists(pid)} for pid in pids if pid is not None}
    result['accepted']=bool(result['accepted'] and result['armor_wrapper_files_unchanged'] and
        result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and
        result['real_application_armor_startup_matches']>=1 and result['armor_full_rows_preserved'] and
        result['armor_catalog_fingerprint']==CATALOG_SHA and len(mutations)==20 and
        result['exclusive2598_released'] and not any(row['pid_exists'] for row in result['owned_pid_terminal'].values()))
    bank.base.peer.dump(receipt,result)
    print(json.dumps({k:result.get(k) for k in ('accepted','scope','real_application_armor_startup_matches',
        'existing_gameplay_mutations','armor_full_rows_preserved','protected_processes_preserved',
        'exclusive2598_released','owned_pid_terminal')}))
    return 0 if result['accepted'] else 1

if __name__=='__main__':raise SystemExit(main())
