"""Source-only EQU/TEQ promotion. No armor instances or equipment route grants.

Migrate/import in place after a no-player stop. Never replace the live database
with a clone or an old save. A schema41 failure retains the compatible candidate
for repair; an older schema40 executable must not run against schema41.
"""
import argparse
from contextlib import closing
import json
import re
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
from tools.operations import native_peer_pose_release_20261002 as common
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import verify_frozen_chat_20260927 as frozen
from tools.strike_lab import import_native_armor_20261002 as armor

ROOT=common.ROOT
managed=common.managed
CANDIDATE=ROOT/'artifacts/research/native-armor-20261002/candidate-01/god2-server.exe'
ROUND=ROOT/'artifacts/releases/native-armor-definitions-20261002'
DEPLOY=ROUND/'deployment-04'
NATIVE=ROOT/'artifacts/playtests/private-native-blackbox-armor-definitions-20261002-01/run-result.json'
SOURCES=('src/db/NativeArmorCatalog.h','src/db/NativeArmorCatalog.cpp',
         'src/db/Migration.cpp','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp',
         'src/scripting/LuaEngine.h','src/scripting/LuaEngine.cpp','src/core/Application.cpp',
         'src/protocol/RecoveredArmorSourceSlots.h','src/protocol/RecoveredArmorInstance.h',
         'src/db/SqliteArmorSlotRepository.h','src/db/SqliteArmorSlotRepository.cpp',
         'src/handlers/OwnedArmorTransferService.h','tests/test_armor_slots.cpp',
         'tests/test_owned_armor_transfer.cpp','tests/test_native_armor_catalog.cpp',
         'tests/test_recovered_armor_instance.cpp','tests/research/test_import_native_armor_20261002.py',
         'tests/CMakeLists.txt','tools/strike_lab/current_armor_20261002.py',
         'tools/strike_lab/current_armor_projection_20261002.py',
         'tools/strike_lab/import_native_armor_20261002.py',
         'tools/operations/native_armor_definitions_release_20261002.py',
         'artifacts/research/native-armor-20261002/records.json',
         'artifacts/research/native-armor-20261002/oracle.json',
         'artifacts/research/current-armor-projection-20261002/native.json')
read=common.read
write=common.write
require=common.require
sha=managed.sha


def automated_gate():
    log=(CANDIDATE.parent/'ctest-armor.log').read_bytes().replace(b'\r\n',b'\n')
    for name in ('armor_slots','owned_armor_transfer','recovered_armor_instance','native_armor_catalog','import_native_armor'):
        block=re.search(b'Test: '+name.encode()+br'\n(.*?)(?=\n\d+/\d+ Testing:|\Z)',log,re.S)
        require(block is not None and b'Test Passed.' in block.group(1) and b'Test Failed.' not in block.group(1),
                'Missing passing armor CTest: '+name)
    require(b'Ran 5 tests' in log,'Armor importer case coverage differs')
    delivery=read(ROOT/'artifacts/research/native-armor-20261002/delivery.json')
    require(delivery['source_raw_equality_rows']==1354 and delivery['explicit_physical_slot_label_count']==1286 and
            delivery['unknown_count']==68 and delivery['all1354_native_equip_flag_true'], 'Native definition scope differs')
    require(delivery['tool_sha256']==sha(ROOT/'tools/strike_lab/current_armor_20261002.py'),'Native source oracle changed')
    for artifact,record in delivery['artifacts'].items():
        require(sha(ROOT/'artifacts/research/native-armor-20261002'/artifact)==record['sha256'],'Native source evidence changed')
    projection=read(ROOT/'artifacts/research/current-armor-projection-20261002/native.json')
    require(projection['status']=='PASS' and projection['cases']==360,'Native armor projection evidence incomplete')


def source_rows(database):
    expected=armor.pinned_records()
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        actual=tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o))
                     for t,o in zip(armor.TABLES,armor.ORDERS))
        require(actual==expected,'Formal armor source definitions differ')
        require(db.execute('PRAGMA quick_check').fetchall()==[('ok',)] and
                not db.execute('PRAGMA foreign_key_check').fetchall(),'Armor import integrity failed')


def preserve(before,after,staged=None):
    require(after['pragmas']==before['pragmas'],'Database pragmas changed')
    old_names={r[1] for r in before['schema']}
    require([r for r in after['schema'] if r[1] in old_names]==before['schema'],'Existing schema changed')
    additions=[r for r in after['schema'] if r[1] not in old_names]
    require({r[1] for r in additions if r[0]=='table'}==set(armor.TABLES) and
            all(r[2] in armor.TABLES and r[0] in ('table','index') for r in additions),
            'Unexpected new schema objects')
    require(set(after['tables'])-set(before['tables'])==set(armor.TABLES),'Unexpected new tables')
    for name,value in before['tables'].items():
        if name!='schema_migrations':require(after['tables'][name]==value,'Existing saved rows changed: '+name)
    require(after['history'][:-1]==before['history'] and
            after['history'][-1][0:2]==[41,'native_armor_definitions'],
            'Migration history differs outside schema41')
    if staged:
        require(after['schema']==staged['schema'] and
                after['history'][-1][:3]==staged['history'][-1][:3], 'Stage schema41 differs')
        for name in armor.TABLES:require(after['tables'][name]==staged['tables'][name],'Stage armor rows differ')


def candidate_run(config,*,migrate=False):
    result=subprocess.run([str(CANDIDATE),'--config',str(config)]+
                         (['--migrate-only'] if migrate else ['--run-for','1']),
                         cwd=ROOT,capture_output=True,creationflags=managed.FLAGS,timeout=30)
    result.check_returncode()
    return result.stdout+result.stderr


def stage():
    require(not DEPLOY.exists(),'Already staged; inspect the release')
    automated_gate()
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat differs')
    managed.listener()
    cfg=read(managed.CONFIG);database=Path(cfg['database']['path']);before=snapshots.capture(database)
    DEPLOY.mkdir(parents=True)
    managed.backup(database,DEPLOY/'accounts.before.db')
    require(snapshots.capture(DEPLOY/'accounts.before.db')==before,'Live saves changed during backup')
    managed.backup(DEPLOY/'accounts.before.db',DEPLOY/'town-diagnostic-accounts.db')
    cfg['database']['path']=str(DEPLOY/'town-diagnostic-accounts.db');cfg['logging']['file']=str(DEPLOY/'stage.log')
    with socket.socket() as reserved:reserved.bind(('127.0.0.1',0));port=reserved.getsockname()[1]
    cfg['server'].update(host='127.0.0.1',port=port,character_port=0)
    write(DEPLOY/'stage-config.json',cfg)
    candidate_run(DEPLOY/'stage-config.json',migrate=True)
    with closing(sqlite3.connect(DEPLOY/'town-diagnostic-accounts.db')) as db:imported=armor.import_catalog(db)
    output=candidate_run(DEPLOY/'stage-config.json')
    (DEPLOY/'stage-output.log').write_bytes(output)
    require('NATIVE_ARMOR_DEFINITIONS equ=692 teq=662' in (DEPLOY/'stage.log').read_text('utf-8'),
            'Actual Application did not validate the complete armor catalog')
    source_rows(DEPLOY/'town-diagnostic-accounts.db');after=snapshots.capture(DEPLOY/'town-diagnostic-accounts.db');preserve(before,after)
    shutil.copy2(managed.ACTIVE,DEPLOY/'god2-server.before.exe')
    shutil.copy2(CANDIDATE,DEPLOY/'god2-server.candidate.exe')
    write(DEPLOY/'save-before.json',before);write(DEPLOY/'save-stage.json',after)
    info={'state':'STAGED','time':common.now(),'database':str(database),
          'old_server_sha256':sha(managed.ACTIVE),'candidate_sha256':sha(CANDIDATE),
          'client_sha256':sha(managed.CLIENT),'config_sha256':sha(managed.CONFIG),
          'source_import':imported,'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
          'scope':'1354 native definitions and1286 source parts only; no armor gameplay activation or grants'}
    write(DEPLOY/'release.json',info);return info


def qualify():
    automated_gate()
    info=read(DEPLOY/'release.json')
    require(info['candidate_sha256']==sha(CANDIDATE),'Candidate changed')
    for p,digest in info['source_sha256'].items():require(sha(ROOT/p)==digest,'Tested source changed: '+p)
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat differs')
    source_rows(DEPLOY/'town-diagnostic-accounts.db')
    native=read(NATIVE)
    require(native.get('accepted') is True and native['candidate_sha256']==sha(CANDIDATE),
            'Same-candidate original client regression required')
    require(native.get('scope')=='SOURCE_ONLY_MIGRATION41_IMPORT_AND_APPLICATION_STARTUP_WITH_TW_CN_BANK20_REGRESSION',
            'Native regression scope differs')
    for key in ('private_files_unchanged','all_private_images_closed','source_files_unchanged',
                'candidate_unchanged','all_owned_processes_closed','armor_wrapper_files_unchanged',
                'protected_processes_preserved','desktop_owner_unchanged','armor_full_rows_preserved',
                'exclusive2598_released'):
        require(native.get(key) is True,'Native regression guard failed: '+key)
    require(native['before']==native['after'] and
            native['armor_wrapper_guards_before']==native['armor_wrapper_guards_after'],
            'Regression files differ')
    require(native['armor_wrapper_guards_before'] and native['owned_pid_terminal'] and
            all(row.get('pid_exists') is False for row in native['owned_pid_terminal'].values()),
            'Native regression processes not terminal')
    for path,digest in native['armor_wrapper_guards_before'].items():
        require(sha(Path(path))==digest,'Native regression evidence changed: '+path)
    require(native.get('real_application_armor_startup_matches',0)>=1 and
            native.get('armor_catalog_fingerprint')==armor.fingerprint(armor.pinned_records()) and
            native.get('armor20byte_grants_created')==0 and
            native.get('armor_equipment_live_acceptance') is False,
            'Source-only native regression incomplete')
    ui=native['ui']
    for key in ('accepted','unrelated_saved_rows_preserved','desktop_unchanged','all_clients_closed',
                'armor_definition_catalog_all_rows_preserved'):
        require(ui.get(key) is True,'Native UI regression guard failed: '+key)
    mutations=[e for e in ui['events'] if e['operation'] in ('0x63','0x64','0x65')]
    require(len(mutations)==native.get('existing_gameplay_mutations')==20 and
            native.get('existing_gameplay_opcode_counts')=={'0x63':6,'0x65':6,'0x64':8} and
            all(e.get('other_owner_unchanged') is True and e.get('native_and_durable_total')=={(4,950):10,(5,936):8}.get(
                (e['after']['native']['identity'],e['after']['native']['language'])) for e in mutations),
            'Native UI mutations incomplete')
    languages={e['native']['language'] for e in ui['events'] if e['operation']=='NPC37_bank_open'}
    require(languages=={950,936},'Both TW and CN native UI regression required')
    return info


def apply():
    info=qualify();require(info['state']=='STAGED','STAGED release required')
    require(sha(managed.ACTIVE)==info['old_server_sha256'] and sha(managed.CLIENT)==info['client_sha256'] and
            sha(managed.CONFIG)==info['config_sha256'],'Managed files changed')
    subprocess.run([sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,check=True)
    database=Path(info['database']);before=read(DEPLOY/'save-before.json')
    require(snapshots.capture(database)==before,'Saves changed after stage')
    pid=managed.listener();common.lifecycle.stop_managed_and_wait(pid)
    if snapshots.capture(database)!=before:
        managed.start();raise RuntimeError('Saves changed during stop; restage')
    # Install schema-compatible code first; player DB is never copied/restored.
    shutil.copy2(CANDIDATE,managed.ACTIVE)
    try:
        candidate_run(managed.CONFIG,migrate=True)
        with closing(sqlite3.connect(database)) as db:armor.import_catalog(db)
        after=snapshots.capture(database);preserve(before,after,read(DEPLOY/'save-stage.json'))
        managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        info.update(state='INSTALLED',installed_at=common.now(),server_pid=managed.listener(allow_players=True),
                    player_saved_rows_preserved=True,armor_instances_granted=0)
        require(sha(managed.ACTIVE)==info['candidate_sha256'] and sha(managed.CLIENT)==info['client_sha256'] and
                sha(managed.CONFIG)==info['config_sha256'],'Installed files differ')
        source_rows(database)
        write(DEPLOY/'save-installed.json',after);write(DEPLOY/'release.json',info)
    except BaseException as error:
        # New schema is not downgraded and no old save overwrites player progress.
        info.update(state='REPAIR_REQUIRED_COMPATIBLE_CANDIDATE_RETAINED',error=str(error),database_restored=False)
        write(DEPLOY/'release.json',info)
        try:managed.start()
        except Exception:pass
        raise
    return info


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply'))
    result={'stage':stage,'apply':apply}[parser.parse_args().mode]()
    print(json.dumps({k:result.get(k) for k in ('state','candidate_sha256','server_pid','player_saved_rows_preserved')}))

if __name__=='__main__':main()
