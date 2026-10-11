"""Install qualified arrival handling without replacing saves or importing test actors."""
from contextlib import closing
import json
import shutil
from tools.operations import native_quest_catalog_release as base

CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
RELEASE=base.ROOT/'artifacts/releases/scene-arrival-20260927'
RECEIPT=base.ROOT/'artifacts/playtests/private-native-blackbox-scene-route-20260927-10/run-result.json'

def require(value,message):
    if not value:raise ValueError(message)

def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def verify(info):
    database=base.Path(info['database'])
    require(base.snapshot(database)==base.snapshot(RELEASE/'accounts.before.db'),'Saved tables changed')
    require(base.sha(base.ACTIVE)==info['candidate_sha256'],'Active binary mismatch')
    require(base.sha(base.CONFIG)==info['config_sha256'],'Configuration changed')
    require(base.sha(base.CLIENT)==info['client_sha256'],'Client changed')
    with closing(base.sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        counts={t:db.execute('select count(*) from '+t).fetchone()[0] for t in ('accounts','recovered_characters','world_display_records','world_monster_levels')}
    result={'installed':True,'listener_pid':base.listener(allow_players=True),'all_saved_tables_unchanged':True,
            'config_unchanged':True,'client_unchanged':True,'counts':counts,'acceptance_receipt':str(RECEIPT),
            'scope':'Language-bound 1C arrival context, actor restoration on completed transfer; no original placements/levels added'}
    save(RELEASE/'verification.json',result);return result

def main():
    receipt=json.loads(RECEIPT.read_text('utf-8'))
    require(receipt['accepted'] and receipt['server_sha256']==base.sha(CANDIDATE),'Exact candidate current-client acceptance required')
    require(all(receipt[k] for k in ('world_records_unchanged','live_database_unchanged','live_client_unchanged','source_database_unchanged','private_client_unchanged')),'Isolated regression modified external state')
    require(receipt['route']['saved_position'][:4]==[2,4,83,73],'Continued movement not accepted')
    info={'database':json.loads(base.CONFIG.read_text('utf-8'))['database']['path'],
          'old_server_sha256':base.sha(base.ACTIVE),'candidate_sha256':base.sha(CANDIDATE),
          'config_sha256':base.sha(base.CONFIG),'client_sha256':base.sha(base.CLIENT)}
    database=base.Path(info['database'])
    # Recheck the actual listener and player connections before stopping it.
    pid=base.listener()
    RELEASE.mkdir(parents=True,exist_ok=False)
    base.backup(database,RELEASE/'accounts.before.db')
    shutil.copy2(base.ACTIVE,RELEASE/'god2-server.before.exe')
    shutil.copy2(CANDIDATE,RELEASE/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,RELEASE/'server-config.before.json')
    save(RELEASE/'manifest.json',info)
    require(base.snapshot(database)==base.snapshot(RELEASE/'accounts.before.db'),'Saved state changed during staging')
    require(base.listener()==pid,'Listener changed during staging')
    base.stop(pid)
    try:
        require(base.snapshot(database)==base.snapshot(RELEASE/'accounts.before.db'),'Saved state changed while stopping')
        shutil.copy2(RELEASE/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        result=verify(info)
    except BaseException:
        try:base.stop(base.listener(allow_players=True))
        except Exception:pass
        # No database writes occur in this release. Preserve any concurrent saves.
        shutil.copy2(RELEASE/'god2-server.before.exe',base.ACTIVE);base.start();raise
    print(json.dumps(result))

if __name__=='__main__':main()
