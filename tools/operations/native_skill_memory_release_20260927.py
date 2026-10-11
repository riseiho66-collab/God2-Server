"""Promote all448 actual-memory verified skills through existing runtime APIs."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import struct
import shutil
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_skills as skills

READER=base.ROOT/'build-town-visibility/tests/Release/native-skill-memory-reader.exe'
def require(ok,message):
    if not ok:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def source_receipt(path):
    value=json.loads(path.read_text('utf-8'));require(value['accepted'] and value['desktop_unchanged'] and value['owned_client_closed'],'Actual cleanup-qualified RAM receipt required')
    require(value['process_memory_writes']==0 and value['screenshots']==0,'Read-only RAM required')
    rows=skills.pinned_records(base.CLIENT.parent);observed=value['capture']['skills']['records']
    by_key={(row[5],row[6]):row[4] for row in rows}
    require(len(observed)==448 and len({(r['kind'],r['id']) for r in observed})==448,'Actual full skill domain required')
    for row in observed:require(bytes.fromhex(row['record110_hex'])==by_key[row['kind'],row['id']],'Actual RAM skill source mismatch')
    return rows
def read_cpp(database,rows):
    reply=subprocess.run([str(READER),str(database)],check=True,capture_output=True,text=True,creationflags=base.FLAGS,timeout=30)
    actual=json.loads(reply.stdout)['rows']
    expected=[{'kind':row[5],'id':row[6],'raw_hex':row[4].hex(),'mp':struct.unpack_from('<H',row[4],0x42)[0]} for row in rows]
    require(actual==expected,'C++ all448 source/MP readback mismatch')
    return {'records':448,'all_raw_bytes_and_mp_thresholds_match':True,'source_writes':0}
def unchanged(before,after):
    a,b=base.snapshot(before),base.snapshot(after);require(set(a)==set(b),'Unexpected schema/table change')
    for name in a:
        if name in ('native_data_sources','native_skill_catalog'):
            require(a[name][0]==b[name][0] and set(a[name][1])<=set(b[name][1]),'Existing source rows modified')
        else:require(a[name]==b[name],'Existing table changed: '+name)
    with closing(sqlite3.connect(after.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(not db.execute('PRAGMA foreign_key_check').fetchall(),'Foreign key failure')
        require(db.execute('SELECT '+skills.RECORD_COLUMNS+' FROM native_skill_catalog ORDER BY source_record_index').fetchall()==skills.pinned_records(base.CLIENT.parent),'Full skill table mismatch')
        require(db.execute('SELECT '+skills.SOURCE_COLUMNS+' FROM native_data_sources WHERE dataset_id=?',(skills.DATASET,)).fetchall()==[skills.SOURCE_ROW],'Skill source metadata mismatch')
def stage(release,receipt):
    rows=source_receipt(receipt);base.listener();require(not release.exists(),'New release directory required');release.mkdir(parents=True)
    config=json.loads(base.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    base.backup(database,release/'accounts.before.db');base.backup(database,release/'town-diagnostic-accounts.db')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:result=skills.import_catalog(db,base.CLIENT.parent)
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db');cpp=read_cpp(release/'town-diagnostic-accounts.db',rows)
    info={'state':'STAGED','live_database':str(database),'server_sha256':base.sha(base.ACTIVE),
        'config_sha256':base.sha(base.CONFIG),'client_sha256':base.sha(base.CLIENT),
        'memory_receipt':str(receipt),'memory_receipt_sha256':base.sha(receipt),'import':result,'cpp':cpp,
        'scope':'All448 current native skill records, existing C++/Lua source lookup and client MP thresholds. No authoritative original damage/hit/critical formula or learned ownership grant.'}
    save(release/'manifest.json',info);return info
def verify(release):
    info=base.manifest(release);database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and base.sha(base.CLIENT)==info['client_sha256'],'Managed identities changed')
    require(base.sha(Path(info['memory_receipt']))==info['memory_receipt_sha256'],'RAM receipt changed')
    unchanged(release/'accounts.before.db',database);cpp=read_cpp(database,source_receipt(Path(info['memory_receipt'])))
    result={'installed_skill_records':448,'cpp':cpp,'player_tables_changed':[],
        'new_learned_skill_grants':0,'authoritative_original_server_formulas_recovered':0,
        'client_config_executable_unchanged':True,'service_pid':base.listener(allow_players=True)}
    save(release/'verification.json',result);return result
def apply(release):
    info=base.manifest(release);require(info['state']=='STAGED','Stage required')
    database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and base.sha(base.CLIENT)==info['client_sha256'],'Managed identities changed; restage')
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db');pid=base.listener();base.stop(pid)
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise ValueError('Saves changed while stopping; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed server did not listen'}")
        result=verify(release);info['state']='INSTALLED_SKILL_SOURCE_ONLY';save(release/'manifest.json',info);return result
    except BaseException:
        try:base.stop(base.listener(allow_players=True))
        except Exception:pass
        base.backup(release/'accounts.before.db',database);base.start();raise
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply','verify'))
    parser.add_argument('--release',type=Path,required=True);parser.add_argument('--receipt',type=Path)
    args=parser.parse_args();release=args.release.resolve()
    if args.mode=='stage':
        require(args.receipt is not None,'Actual memory receipt required');result=stage(release,args.receipt.resolve())
    else:result={'apply':apply,'verify':verify}[args.mode](release)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
