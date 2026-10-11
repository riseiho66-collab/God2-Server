"""Fresh hidden client restores a copied, previously accepted growth settlement."""
import argparse,json,os,sqlite3,subprocess,sys
from contextlib import closing
from pathlib import Path
from . import run_private_scene_actor_route as scene
from tools.operations.native_quest_catalog_release import backup,snapshot

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--mode',choices=('restore','allocate','allocate-rapid','allocated-restore'),default='restore')
    a=ap.parse_args();source=a.source.resolve();here=a.output.resolve()
    if not here.name.startswith('private-native-blackbox-'):raise ValueError('Explicit isolated directory required')
    receipt=json.loads((source/'ui-result.json').read_text('utf-8'))
    if not receipt['accepted']:raise ValueError('Accepted settled source required')
    here.mkdir(parents=True,exist_ok=False);db=here/'diagnostic-accounts.db';original=source/db.name
    backup(original,db);before=snapshot(db);source_before=snapshot(original)
    with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as connection:
        profile=connection.execute('select profile from recovered_characters where id=4').fetchone()[0]
        resources_before=connection.execute('select hp,max_hp,mp,max_mp,revision from character_resources where character_id=4').fetchone()
    if not 1<=profile[29]<=8:raise ValueError('Unqualified copied profession')
    profession=[1,2,4,3][(profile[29]-1)//2]
    formal=Path(json.loads(scene.CONFIG.read_text('utf-8'))['database']['path']);formal_before=snapshot(formal)
    client_before=scene.sha(scene.LIVE_CLIENT);private_before=scene.sha(scene.CLIENT)
    binary=scene.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
    settings=json.loads((source/'restore-config.json').read_text('utf-8'));settings['database']['path']=str(db)
    settings.setdefault('world',{})['owned_attribute_allocation']={'enabled':a.mode in ('allocate','allocate-rapid')}
    settings['logging']['file']=str(here/'server.log');cfg=here/'server-config.json';cfg.write_text(json.dumps(settings),encoding='utf-8')
    (here/'restore-config.json').write_text(json.dumps(settings),encoding='utf-8')
    result={'accepted':False,'server_sha256':scene.sha(binary)};server=runner=output=None
    try:
        server,output=scene.start(binary,here,cfg,native_records_lab=False)
        observer=[sys.executable,'-X','utf8','-B',str(scene.ROOT/'tools/strike_lab/private_character_growth_ui.py'),
            str(here/'ui-result.json'),str(db),str(here/'server.log'),'--client-exe',str(scene.CLIENT),'--profession',str(profession),'--restore']
        if a.mode=='allocate-rapid':observer+=['--allocate','--rapid']
        elif a.mode!='restore':observer.append('--'+a.mode)
        if a.mode=='allocated-restore' and receipt.get('rapid_clicks'):observer.append('--repeated-pattern')
        env=os.environ.copy();env['GOD2_PRIVATE_SIDECAR_COMMAND']=subprocess.list2cmdline(observer);env['GOD2_PRIVATE_SIDECAR_WAIT_MS']='110000'
        with (here/'runner.log').open('wb') as log:
            runner=subprocess.Popen([str(scene.RUNNER),str(scene.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=scene.CLIENT.parent,
                env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));runner.wait(timeout=115)
        result['ui']=json.loads((here/'ui-result.json').read_text('utf-8'));result['accepted']=result['ui']['accepted']
    except Exception as error:result['error']=f'{type(error).__name__}: {error}'
    finally:
        for process in (runner,server):
            if process and process.poll() is None:process.terminate();process.wait(timeout=5)
        if output:output.close()
        after=snapshot(db)
        result.update(durable_state_unchanged=after==before,source_database_unchanged=snapshot(original)==source_before,
            live_database_unchanged=snapshot(formal)==formal_before,live_client_unchanged=scene.sha(scene.LIVE_CLIENT)==client_before,
            private_client_unchanged=scene.sha(scene.CLIENT)==private_before)
        if a.mode in ('allocate','allocate-rapid'):
            changed=[name for name in before if before[name]!=after[name]]
            result['changed_tables']=changed
            with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as connection:
                resources_after=connection.execute('select hp,max_hp,mp,max_mp,revision from character_resources where character_id=4').fetchone()
            result['resources_before']=resources_before;result['resources_after']=resources_after
            role_delta=result.get('ui',{}).get('allocated_role',{}).get('revision',0)-receipt['saved_role']['revision']
            result['resource_values_unchanged']=bool(resources_before and resources_after and 1<=role_delta<=4 and
                resources_before[:4]==resources_after[:4] and resources_after[4]==resources_before[4]+role_delta)
            result['expected_durable_changes']=set(changed)=={'character_role_snapshots','character_resources'} and result['resource_values_unchanged']
        else:result['expected_durable_changes']=result['durable_state_unchanged']
        result['accepted']=result['accepted'] and all(result[k] for k in ('expected_durable_changes','source_database_unchanged',
            'live_database_unchanged','live_client_unchanged','private_client_unchanged'))
        (here/'run-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='ui'}));return 0 if result['accepted'] else 1

if __name__=='__main__':raise SystemExit(main())
