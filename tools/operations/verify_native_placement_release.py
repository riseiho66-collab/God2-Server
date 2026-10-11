"""Read-only comparison of a staged placement release against live files/data."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('pragma quick_check').fetchone()!=('ok',):raise ValueError('Database integrity failed')
        tables={row[0]:row[1] for row in db.execute("select name,sql from sqlite_master where type='table'")}
        data={name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"')) for name in tables}
        return tables,data

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--release',type=Path,required=True)
    args=ap.parse_args();release=args.release.resolve()
    if release.parent!=ROOT/'artifacts/releases':raise ValueError('Expected managed release path')
    manifest=json.loads((release/'manifest.json').read_text('utf-8'))
    config=json.loads((ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json').read_text('utf-8'))
    old_tables,old_data=snapshot(release/'accounts.before.db')
    new_tables,new_data=snapshot(Path(config['database']['path']))
    changed=[table for table in old_tables if old_tables[table]!=new_tables.get(table) or old_data[table]!=new_data.get(table)]
    result={'existing_tables_changed':changed,'quick_check':'ok',
        'client_unchanged':sha(ROOT.parent/'God2/God2.exe')==manifest['client_sha256'],
        'active_binary_matches_candidate':sha(ROOT/'build-town-visibility/Release/god2-server.exe')==manifest['candidate_sha256'],
        'active_config_matches_candidate':sha(ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json')==sha(release/'server-config.candidate.json'),
        'native_npc_placements_only':config['development']['diagnostic_town']['native_npc_placements_only'],
        'native_monster_placements_only':config['development'].get('native_monster_placements_only',False)}
    if release.name.startswith('kunlun-birthplace-'):
        birth=config.get('world',{}).get('new_character_birthplace',{})
        result['new_character_birthplace']={key:birth.get(key) for key in ('area','scene','kind','x','y','coordinate_authority')}
        result['kunlun_birthplace_configured']=result['new_character_birthplace']=={
            'area':4,'scene':3,'kind':0,'x':126,'y':126,'coordinate_authority':'CUSTOM-0040'}
    if release.name.startswith('world-clock-'):
        result['world_clock_configured']=config.get('world',{}).get('clock')=={'enabled':True,'sync_seconds':60}
        before=json.loads((release/'server-config.before.json').read_text('utf-8'))
        preserved=json.loads(json.dumps(config))
        preserved['world'].pop('clock',None)
        before.setdefault('world',{}).pop('clock',None)
        result['other_config_preserved']=preserved==before
    (release/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
    return 0 if not changed and result.get('kunlun_birthplace_configured',True) and result.get('world_clock_configured',True) and result.get('other_config_preserved',True) and all(result[key] for key in ('client_unchanged','active_binary_matches_candidate','active_config_matches_candidate','native_npc_placements_only','native_monster_placements_only')) else 1

if __name__=='__main__':raise SystemExit(main())
