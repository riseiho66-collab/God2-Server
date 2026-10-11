"""Back up and stage the owner's native-only NPC policy; no process control."""
from contextlib import closing
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release-name',default='native-npc-policy-20260926-01')
    ap.add_argument('--monster-native-only',action='store_true')
    ap.add_argument('--kunlun-birthplace',action='store_true')
    ap.add_argument('--world-clock',action='store_true')
    args=ap.parse_args()
    prefix='world-clock-' if args.world_clock else ('kunlun-birthplace-' if args.kunlun_birthplace else ('native-monster-policy-' if args.monster_native_only else 'native-npc-policy-'))
    if '/' in args.release_name or '\\' in args.release_name or not args.release_name.startswith(prefix):
        raise ValueError('Invalid release directory name')
    release=ROOT/'artifacts/releases'/args.release_name
    release.mkdir(parents=True,exist_ok=False)
    config=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'
    active=ROOT/'build-town-visibility/Release/god2-server.exe'
    candidate=ROOT/'build-town-visibility/Release'/('god2-server-world-clock.exe' if args.world_clock else ('god2-server-kunlun.exe' if args.kunlun_birthplace else ('god2-server-native-monsters.exe' if args.monster_native_only else 'god2-server-native-npc.exe')))
    client=ROOT.parent/'God2/God2.exe'
    data=json.loads(config.read_text('utf-8'));database=Path(data['database']['path'])
    if not database.is_absolute():raise ValueError('Require explicit live database path')
    shutil.copy2(config,release/'server-config.before.json')
    shutil.copy2(active,release/'god2-server.before.exe')
    shutil.copy2(candidate,release/'god2-server.candidate.exe')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as source:
        if source.execute('pragma quick_check').fetchone()!=('ok',):raise ValueError('Live DB integrity failed')
        resources=source.execute('select character_id,hp,max_hp,mp,max_mp,revision,design_id from character_resources').fetchall()
        roles=source.execute('select character_id,logical,revision,design_id from character_role_snapshots').fetchall()
        for character,logical,revision,design in roles:
            row=next((row for row in resources if row[0]==character),None)
            if row is None or design!='CUSTOM-0013' or not revision or len(logical)!=25:
                raise ValueError('Live role snapshot unqualified')
            if int.from_bytes(logical[17:21],'little')!=row[2] or int.from_bytes(logical[21:25],'little')!=row[4]:
                raise ValueError('Live role resources disagree')
        for row in resources:
            if row[-1]!='CUSTOM-0012' or not row[-2]:raise ValueError('Live resource provenance unqualified')
        with closing(sqlite3.connect(release/'accounts.before.db')) as backup:source.backup(backup)
        counts={table:source.execute('select count(*) from '+table).fetchone()[0]
                for table in ('accounts','recovered_characters','character_resources','character_role_snapshots')}
    data['development']['diagnostic_town']['native_npc_placements_only']=True
    if args.monster_native_only:data['development']['native_monster_placements_only']=True
    if args.world_clock:
        data.setdefault('world',{})['clock']={'enabled':True,'sync_seconds':60}
    if args.kunlun_birthplace:
        data.setdefault('world',{})['new_character_birthplace']={
            'area':4,'scene':3,'kind':0,'x':126,'y':126,
            'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),
            'coordinate_authority':'CUSTOM-0040'}
    (release/'server-config.candidate.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'old_server_sha256':sha(active),'candidate_sha256':sha(candidate),'client_sha256':sha(client),
        'original_config_sha256':sha(config),'live_database':str(database),'before_counts':counts,
        'scope':'Suppress CUSTOM-0020 positions and associated interactions; no native coordinates or directions fabricated',
        'remaining':'Original NPC placements are not yet restored; guide quest cannot be triggered until qualified placement is available'}
    if args.monster_native_only:
        manifest['scope']='Suppress unqualified diagnostic encounter entry; retain NPC policy and saved data; no monster spawn coordinates fabricated'
        manifest['remaining']='Original monster spawn/encounter assignments not recovered; no new diagnostic quest encounter while native-only policy is active'
    if args.kunlun_birthplace:
        manifest['scope']='Fresh unsaved characters enter native Kunlun map 4/3. Existing saved positions are preserved.'
        manifest['remaining']='126/126 is a qualified walkable provisional coordinate (CUSTOM-0040), not a recovered original birth coordinate.'
    if args.world_clock:
        manifest['scope']='Native1A world clock on initial owned world tick and every60 seconds in ready InWorld; preserve all existing configuration and player data.'
        manifest['remaining']='CUSTOM-0042 UTC epoch-zero anchor is custom policy. No original calendar, daily reset, weather or reward authority restored.'
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'staged':str(release),'before_counts':counts}));return 0
if __name__=='__main__':raise SystemExit(main())
