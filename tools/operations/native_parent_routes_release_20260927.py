"""Promote current-client accepted parent routes; code/config only, no DB replacement."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.operations import native_quest_catalog_release as managed
from tools.operations import native_logout_doors_release_20260927 as release_base
ROOT=managed.ROOT
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def require(value,message):
    if not value:raise ValueError(message)
def qualified(path):
    value=json.loads(path.read_text('utf-8'));ui=value.get('ui',{})
    require(value.get('accepted') and value.get('runner_exit')==0 and ui.get('accepted'),'Native client acceptance missing')
    require(value.get('server_sha256')==managed.sha(CANDIDATE) and value.get('actual_server_sha256')==managed.sha(CANDIDATE),'Different candidate tested')
    require(bool(value.get('source_files_unchanged')) and all(value['source_files_unchanged'].values()) and
            bool(value.get('route_sources_unchanged')) and all(value['route_sources_unchanged'].values()),'Source preservation missing')
    require(ui.get('desktop_unchanged') and ui.get('all_clients_closed'),'Owned process/desktop cleanup missing')
    require(ui.get('database_before') and ui.get('database_before')==ui.get('database_after'),'Nonposition database preservation missing')
    for name in ('entry','return'):
        require(ui.get(name,{}).get('pending_receipt'),'Transition receipt missing')
    for name in ('actor_sees_peer','peer_sees_actor','remote_movement','cold_actor_peer','cold_observer_peer','returned_scene_isolation'):
        require(ui.get(name),'Parent multiplayer qualification missing: '+name)
    return value
def stage(args,release):
    values=[qualified(p.resolve()) for p in args.parent_receipt]
    by_area={v['ui']['entry']['native']['area']:v for v in values}
    require(set(by_area)=={2,4},'Both native parent areas required')
    for area,value in by_area.items():
        ui=value['ui'];source_scene=4 if area==2 else 3
        require((ui['entry']['native']['scene'],ui['entry']['native']['kind'])==(0,1),'Incorrect native parent selector')
        require((ui['return']['native']['scene'],ui['return']['native']['kind'])==(source_scene,0),'Incorrect native city selector')
        require((ui['cold_restore']['area'],ui['cold_restore']['scene'],ui['cold_restore']['kind'])==(area,0,1),'Cold parent restore missing')
    require(not release.exists(),'Release exists')
    before=json.loads(managed.CONFIG.read_text('utf-8'));database=Path(before['database']['path'])
    require(before['development']['diagnostic_town']['player_visibility'],'Existing multiplayer must remain enabled')
    release.mkdir(parents=True)
    shutil.copy2(managed.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(managed.CONFIG,release/'server-config.before.json')
    managed.backup(database,release/'accounts.before.db');managed.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    config=json.loads(json.dumps(before));town=config['development']['diagnostic_town']
    town.update(island_routes=True,island_navigation=str(ROOT/'artifacts/world-atlas/island01-full-navigation-2-0.json'),
        kunlun_parent_routes=True,kunlun_parent_navigation=str(ROOT/'artifacts/world-atlas/island03-full-navigation-4-0.json'))
    require(town['all_door_routes'] and town['kunlun_door_routes'] and town['player_visibility'],'Existing room/multiplayer route disabled')
    write(release/'server-config.candidate.json',config)
    check=json.loads(json.dumps(config));check['database']['path']=str(release/'town-diagnostic-accounts.db');check['logging']['file']=str(release/'migration.log')
    write(release/'migration-config.json',check)
    with (release/'migration.stdout.log').open('wb') as log:
        subprocess.run([str(CANDIDATE),'--config',str(release/'migration-config.json'),'--migrate-only'],cwd=ROOT,
            check=True,stdout=log,stderr=subprocess.STDOUT,creationflags=managed.FLAGS,timeout=30)
    require(managed.snapshot(release/'accounts.before.db')==managed.snapshot(release/'town-diagnostic-accounts.db'),'Migration changed saved rows')
    write(release/'manifest.json',{'candidate_sha256':managed.sha(CANDIDATE),'old_server_sha256':managed.sha(managed.ACTIVE),
        'config_sha256':managed.sha(managed.CONFIG),'client_sha256':managed.sha(managed.CLIENT),'database':str(database),
        'town_doors':True,'kunlun_doors':True,'island_routes':True,'kunlun_parent_routes':True,
        'parent_receipts':[str(p.resolve()) for p in args.parent_receipt],'database_replacement':False,
        'rule_origin':'CUSTOM-0036 source-order town boundary pairing; CUSTOM-0053 second-pair activation/first-point landing',
        'scope':'44 town-parent directions and 2 Kunlun-parent directions; no whole-world completion claim'})
    print(json.dumps({'staged':str(release),'database_unchanged':True}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('stage','apply'))
    p.add_argument('--release-name',required=True);p.add_argument('--parent-receipt',type=Path,action='append',default=[])
    a=p.parse_args();require(a.release_name.startswith('native-parent-routes-') and '/' not in a.release_name and '\\' not in a.release_name,'Invalid release name')
    release=ROOT/'artifacts/releases'/a.release_name
    if a.mode=='stage':stage(a,release)
    else:
        release_base.apply(release)
        result=json.loads((release/'verification.json').read_text('utf-8'));config=json.loads(managed.CONFIG.read_text('utf-8'))['development']['diagnostic_town']
        result.update(island_routes=config.get('island_routes'),kunlun_parent_routes=config.get('kunlun_parent_routes'),player_visibility=config.get('player_visibility'))
        write(release/'verification.json',result);require(all(result[k] for k in ('island_routes','kunlun_parent_routes','player_visibility')),'Installed flags mismatch')
