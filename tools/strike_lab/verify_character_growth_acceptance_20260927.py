"""Audit real hidden-client growth receipts, native stores and settlement rows."""
from contextlib import closing
import json,sqlite3,struct
from .run_private_scene_actor_route import ROOT,sha
from .current_character_growth_binding_20260927 import audit

CANDIDATE='20d0c30ea40e3559e20250713cc598a8acaac3325e753d110c29976b30f72f34'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def main():
    require(sha(ROOT/'build-town-visibility/Release/god2-server-native-results.exe')==CANDIDATE,'Qualified candidate changed')
    binding=audit();require(binding['case_count']==16,'Native profession binding incomplete')
    root=ROOT/'artifacts/playtests';rows=[]
    for run,wire,profession,stats in ((7,2,1,[12,13,10,11]),(8,4,2,[11,10,13,12]),
                                     (9,6,4,[11,11,11,13]),(10,8,3,[12,10,12,12])):
        path=root/f'private-native-blackbox-character-growth-20260927-{run:02}'
        result=json.loads((path/'run-result.json').read_text('utf-8'));ui=result['ui']
        require(result['server_sha256']==CANDIDATE and ui['accepted'],'Growth-stage client receipt failed')
        require(all(result[k] for k in ('live_database_unchanged','live_client_unchanged',
                'source_database_unchanged','private_client_unchanged')),'External state changed')
        require(ui['native_role']=={'level':2,'points':4,'stats':stats},'Owner award differs from native stores')
        with closing(sqlite3.connect((path/'diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as db:
            require(db.execute('pragma quick_check').fetchone()==('ok',),'Database integrity failed')
            role,revision=db.execute('select logical,revision from character_role_snapshots where character_id=4').fetchone()
            profile=db.execute('select profile from recovered_characters where id=4').fetchone()[0]
            require(profile[29]==wire and revision==2 and role.hex()==ui['saved_role']['logical_hex'],'Saved role/profile mismatch')
            require(list(struct.unpack_from('<4H',role,5))==stats and role[1]==2 and role[3:5]==b'\x04\x00','Saved growth mismatch')
            require(db.execute('select total from character_experience where character_id=4').fetchone()==(250,),'XP mismatch')
            require(db.execute('select s.total_experience from battle_settlements s join battle_reservations r on r.id=s.battle_id where r.character_id=4').fetchall()==[(250,)],'Expected exactly one settlement')
        log=(path/'server.log').read_text('utf-8',errors='replace')
        require(log.count('DIAGNOSTIC_POST_BATTLE_CONTEXT_ACCEPTED')==1 and 'Recovered world policy or response rejected' not in log,'Post-battle connection failed')
        rows.append({'catalog_profession':profession,'wire_profession':wire,'stats':stats,'points':4,'level':2,
            'receipt':str(path/'run-result.json'),'scope':'growth stage only; run10 reconnect failure is excluded'})
    path=root/'private-native-blackbox-character-growth-restore-20260927-03'
    result=json.loads((path/'run-result.json').read_text('utf-8'));ui=result['ui']
    require(result['accepted'] and result['server_sha256']==CANDIDATE,'Reconnect receipt failed')
    require(all(result[k] for k in ('durable_state_unchanged','source_database_unchanged','live_database_unchanged',
            'live_client_unchanged','private_client_unchanged')),'Reconnect altered durable/external state')
    require(ui['native_role']=={'level':2,'points':4,'stats':[12,10,12,12]},'Reconnect native growth mismatch')
    prefix=bytes.fromhex(ui['owner_locator']['owners'][0]['position_prefix_hex'])
    require(struct.unpack_from('<IIH',prefix,16)==(2,15,2) and struct.unpack_from('<II',prefix,8)==(18,12),'Reconnect location mismatch')
    report={'candidate_sha256':CANDIDATE,'four_profession_live_growth':rows,'native_binding_cases':16,
        'fresh_client_restore':'PASS','restore_receipt':str(path/'run-result.json'),
        'production_growth_enabled':False,'formula_origin':'OWNER_CONFIRMED_20260927',
        'baseline_and_xp_origin':'CUSTOM-0013','original_growth_formula_recovered':False}
    output=ROOT/'artifacts/research/character-growth-native-20260927/acceptance.json'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'four_professions':len(rows),'native_binding_cases':16,'fresh_client_restore':'PASS','production_enabled':False}))

if __name__=='__main__':main()
