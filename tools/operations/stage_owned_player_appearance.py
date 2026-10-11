"""Create a reviewable candidate release without replacing a running service."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base

ROOT=base.ROOT
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-weapon-appearance.exe'

def require(value,message):
    if not value:raise RuntimeError(message)

def stage(release,acceptance,candidate=CANDIDATE,peer=False,rejection=None):
    accepted=json.loads((acceptance/'run-result.json').read_text('utf-8'))
    unchanged=(all(accepted.get('source_files_unchanged',{}).get(key) for key in ('source_db','live_client','private_client')) if peer else
        accepted.get('source_db_unchanged') and accepted.get('live_client_unchanged') and accepted.get('private_client_unchanged'))
    require(accepted.get('accepted') and unchanged,'Actual hidden acceptance and unchanged source/client are required')
    ui=json.loads((acceptance/'ui-result.json').read_text('utf-8'))
    if peer:
        steps=ui.get('stages',[])
        require(ui.get('accepted') and ui.get('all_owned_clients_closed') and len(steps)==4 and
            [step.get('inventory',{}).get('34',{}).get('item') for step in steps]==[1,2,0,1] and
            all(step.get('related_native_and_saved_state_unchanged') for step in steps) and
            ui.get('peer_relogin') and ui.get('movement') and ui.get('clock') and
            ui.get('desktop_before')==ui.get('desktop_after'), 'Complete hidden two-client appearance acceptance required')
    else:
        appearance=ui.get('weapon_appearance',{})
        steps=appearance.get('stages',[])
        require(ui.get('accepted') and ui.get('client_alive') and len(steps)==4 and
            [step.get('equipped_item') for step in steps]==[1,2,0,1] and
            all(step.get('other_components_preserved') for step in steps) and
            appearance.get('unchanged_after_movement_clock'), 'Complete local appearance sequence required')
    # Runner records the exact candidate; do not stage a different later build.
    require(accepted.get('server_sha256')==base.sha(candidate),'Acceptance candidate mismatch')
    if rejection:
        refused=json.loads((rejection/'run-result.json').read_text('utf-8'))
        detail=refused.get('ui',{});check=detail.get('rejection',{})
        require(refused.get('accepted') and refused.get('server_sha256')==base.sha(candidate) and
            all(refused.get('source_files_unchanged',{}).get(key) for key in ('source_db','live_client','private_client')) and
            check.get('all_owned_and_battle_rows_unchanged') and check.get('all50_native_slots_stats_appearance_unchanged') and
            [(step.get('source'),step.get('destination')) for step in detail.get('stages',[])]==[(0,34),(34,0)] and
            detail.get('all_owned_clients_closed') and detail.get('desktop_before')==detail.get('desktop_after'),
            'Source restriction refusal and subsequent legal operations require actual client acceptance')
    config=json.loads(base.CONFIG.read_text('utf-8'))
    require(not config.get('world',{}).get('owned_weapon_transfers',{}).get('enabled',False) and
        not config.get('world',{}).get('owned_player_appearance',{}).get('enabled',False) and
        not config['development'].get('diagnostic_owned_weapon_appearance',False),'Production fixture gates must remain disabled')
    release.mkdir(parents=True,exist_ok=False)
    shutil.copy2(candidate,release/'god2-server.candidate.exe')
    shutil.copy2(base.ACTIVE,release/'god2-server.active-before.exe')
    shutil.copy2(base.CONFIG,release/'server-config.active-before.json')
    database=Path(config['database']['path'])
    base.backup(database,release/'accounts.before.db')
    base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    before=base.snapshot(release/'accounts.before.db')
    config['database']['path']=str(release/'town-diagnostic-accounts.db')
    config['logging']['file']=str(release/'migration.log')
    cfg=release/'stage-config.json';cfg.write_text(json.dumps(config,indent=2),encoding='utf-8')
    subprocess.run([str(candidate),'--config',str(cfg),'--migrate-only'],cwd=ROOT,
        capture_output=True,check=True,creationflags=base.FLAGS,timeout=30)
    after=base.snapshot(release/'town-diagnostic-accounts.db')
    changed=[name for name,record in before.items() if name!='schema_migrations' and after.get(name)!=record]
    require(not changed,'Pre-existing tables changed: '+repr(changed))
    require(after['schema_migrations'][0]==before['schema_migrations'][0] and
        set(before['schema_migrations'][1]).issubset(after['schema_migrations'][1]),'Migration history rewritten')
    require(set(after)-set(before)=={'character_player_appearance_snapshots'}-set(before),'Unexpected new tables')
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:
        require(db.execute('select max(version) from schema_migrations').fetchone()==(29,),'Expected migration29')
        require(db.execute('select count(*) from character_player_appearance_snapshots').fetchone()==(0,),'No appearance autogrant')
    manifest={'state':'STAGED_NOT_INSTALLED','candidate_sha256':base.sha(candidate),
        'active_binary_unchanged':base.sha(base.ACTIVE)==base.sha(release/'god2-server.active-before.exe'),
        'active_config_unchanged':base.sha(base.CONFIG)==base.sha(release/'server-config.active-before.json'),
        'client_sha256':base.sha(base.CLIENT),'schema_version':29,'pre_existing_tables_changed':changed,
        'appearance_rows':0,'acceptance':str(acceptance),'production_mapping_enabled':False,
        'actual_peer_refresh_accepted':peer,
        'source_sex_rejection_acceptance':str(rejection) if rejection else None,
        'remaining':'Original WPN-to-DA mapping and equipment restrictions/final stats remain OPEN.'}
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--release',type=Path,required=True);ap.add_argument('--acceptance',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,default=CANDIDATE);ap.add_argument('--peer',action='store_true')
    ap.add_argument('--rejection-acceptance',type=Path)
    args=ap.parse_args();print(json.dumps(stage(args.release.resolve(),args.acceptance.resolve(),args.candidate.resolve(),args.peer,args.rejection_acceptance.resolve() if args.rejection_acceptance else None),indent=2))
