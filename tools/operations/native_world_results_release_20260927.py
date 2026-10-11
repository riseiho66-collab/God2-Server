"""Install native display/result plumbing after isolated regression; preserve saves."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base

CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
def require(value,message):
    if not value:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def unchanged(before,after):
    a,b=base.snapshot(before),base.snapshot(after)
    require(set(b)==set(a)|{'world_display_records','world_monster_levels'},'Unexpected tables in migration')
    for table in a:
        if table=='schema_migrations':
            require(a[table][0]==b[table][0] and all(row in b[table][1] for row in a[table][1]),'Existing migration changed')
        else:require(a[table]==b[table],f'Existing table changed: {table}')
    require(not b['world_display_records'][1],'No placements may be invented during release')
    require(not b['world_monster_levels'][1],'No native levels may be invented during release')
def stage(release,client_receipt):
    receipt=json.loads(client_receipt.read_text('utf-8'))
    require(receipt['accepted'] and receipt['source_db_unchanged'] and receipt['live_client_unchanged'] and
        receipt['private_client_unchanged'] and receipt['server_sha256']==base.sha(CANDIDATE),'Candidate hidden-client regression required')
    diff=json.loads((base.ROOT/'artifacts/research/native-world-results-20260927-06/verification.json').read_text('utf-8'))
    require(diff['cpp_equals_executed_native'] and diff['accumulator_cases']==70 and diff['scalar_cases']==52,'Native arithmetic differential required')
    require(diff['helper_sha256']==base.sha(base.ROOT/'build-town-visibility/tests/Release/native-world-results.exe'),'Verifier rebuilt since differential; rerun verification')
    battle_receipt=base.ROOT/'artifacts/playtests/private-native-blackbox-20260927-13/run-result.json'
    battle=json.loads(battle_receipt.read_text('utf-8'))
    require(receipt['ui']['world_records']['monster']['level_cache']==27 and
        receipt['persisted_records_before']==receipt['persisted_records_after'],'Persisted world71/72/78 client acceptance required')
    require(battle['accepted'] and battle['source_db_unchanged'] and battle['live_client_unchanged'] and
        battle['private_client_unchanged'] and battle['server_sha256']==base.sha(CANDIDATE),'Native83/0D current-candidate client acceptance required')
    release.mkdir(parents=True,exist_ok=False)
    config=json.loads(base.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    base.backup(database,release/'accounts.before.db');base.backup(database,release/'town-diagnostic-accounts.db')
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    stage_config=dict(config);stage_config['database']={**config['database'],'path':str(release/'town-diagnostic-accounts.db')}
    stage_config['logging']={**config['logging'],'file':str(release/'migration.log')}
    cfg=release/'stage-config.json';save(cfg,stage_config)
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--migrate-only'],cwd=base.ROOT,
        check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    info={'live_database':str(database),'old_server_sha256':base.sha(base.ACTIVE),'candidate_sha256':base.sha(CANDIDATE),
          'config_sha256':base.sha(base.CONFIG),'client_sha256':base.sha(base.CLIENT),'client_receipt':str(client_receipt),
          'battle_client_receipt':str(battle_receipt),
          'scope':'Qualified71/72/78 scene storage/restoration, native83/0D trusted result transactions and native HP/MP application. No invented placements, levels, stats or attack/defense formula.',
          'native_result_emission':'Explicit trusted API only; not automatically emitted for unrecovered skills',
          'state':'STAGED'}
    save(release/'manifest.json',info);return info
def verify(release):
    info=base.manifest(release);database=Path(info['live_database'])
    unchanged(release/'accounts.before.db',database)
    require(base.sha(base.ACTIVE)==info['candidate_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
        base.sha(base.CLIENT)==info['client_sha256'],'Managed identity changed')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        counts={name:db.execute('select count(*) from '+name).fetchone()[0] for name in ('accounts','recovered_characters','world_display_records','world_monster_levels')}
        schema=db.execute('select max(version) from schema_migrations').fetchone()[0]
    require(schema==35 and counts['world_display_records']==0 and counts['world_monster_levels']==0,'World display/level migration mismatch')
    result={'server_pid':base.listener(allow_players=True),'schema':schema,'counts':counts,
            'player_tables_changed':[],'client_unchanged':True,'config_unchanged':True,'original_placements_added':0,
            'all_four_contracts_client_accepted':True,'monster_level_client_accepted':True,
            'acceptance_scope':'Isolated supplied records and current-client consumers; not original spawn, level or damage formula recovery'}
    save(release/'verification.json',result);return result
def apply(release):
    info=base.manifest(release);database=Path(info['live_database'])
    require(info['state']=='STAGED','Stage before apply')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
        base.sha(base.CLIENT)==info['client_sha256'],'Managed identities changed since stage')
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Candidate changed')
    pid=base.listener();base.stop(pid)
    try:
        require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed while stopping')
        # Migrate the actual file; never replace active saves with an older stage clone.
        subprocess.run([str(release/'god2-server.candidate.exe'),'--config',str(base.CONFIG),'--migrate-only'],cwd=base.ROOT,
            check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
        unchanged(release/'accounts.before.db',database)
        shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed server did not listen'}")
        result=verify(release);info['state']='INSTALLED';save(release/'manifest.json',info);return result
    except BaseException:
        try:base.stop(base.listener(allow_players=True))
        except Exception:pass
        base.backup(release/'accounts.before.db',database)
        shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'))
    ap.add_argument('--client-receipt',type=Path);ap.add_argument('--name',required=True);args=ap.parse_args()
    require(args.name.startswith('native-world-results-') and '/' not in args.name and '\\' not in args.name,'Invalid release name')
    release=base.ROOT/'artifacts/releases'/args.name
    value=stage(release,args.client_receipt.resolve()) if args.mode=='stage' else (apply(release) if args.mode=='apply' else verify(release))
    print(json.dumps(value))
if __name__=='__main__':main()
