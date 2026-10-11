"""CUSTOM-0058: isolated visible manual-test fixture; never a release installer."""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import struct

ROOT=Path(__file__).resolve().parents[2]
LIVE=ROOT.parent/'God2'
OUT=ROOT/'artifacts/playtests/private-shunying-manual-20260930-01'
SOURCE=ROOT/'artifacts/playtests/private-skill-ui-20260926-18'
CANDIDATE=ROOT/'artifacts/custom-skills/shunying/client-candidate'

def main():
    if OUT.exists():raise RuntimeError('Manual fixture already exists; refusing replacement')
    manifest=json.loads((CANDIDATE/'manifest.json').read_text('utf-8'))
    if manifest['catalog']['new_id']!=126 or manifest['catalog']['reserved_ids']!=[122,123,124,125]:
        raise RuntimeError('Skill reservation/identity mismatch')
    OUT.mkdir(parents=True)
    client=OUT/'client';client.mkdir()
    for directory in ('Data','Data2','Data3','cursor','resources','config'):
        if (LIVE/directory).is_dir():shutil.copytree(LIVE/directory,client/directory)
    for source in LIVE.iterdir():
        if source.is_file() and source.suffix.lower() in ('.dll','.ini','.csvz','.godz','.rsrc'):
            shutil.copy2(source,client/source.name)
    game=LIVE/'God2-current-lab-2598.exe'
    shutil.copy2(game,client/'God2-shunying-manual.exe')
    for relative,expected in manifest['output_sha256'].items():
        raw=(CANDIDATE/relative).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise RuntimeError('Candidate digest mismatch')
        destination=client/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw)
    (client/'Save').mkdir()
    # User explicitly requested preconfigured F1. This is fixture preparation,
    # not proof that the UI shortcut editor was tested.
    hotbar=bytearray(b'\xff'*(60+960)+bytes(36))
    struct.pack_into('<HHH',hotbar,60,2,0,126)
    hotbar.extend(struct.pack('<III',0x3b,10,10))
    # No account-wide/default hotkey. Assign only after the requested test character exists.
    database=OUT/'diagnostic-accounts.db'
    with sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True) as source:
        with sqlite3.connect(database) as target:source.backup(target)
    with sqlite3.connect(database) as db:
        if db.execute('select name_bytes from recovered_characters where id=4').fetchone()[0].split(b'\0')[0]!=b'slowgirl':
            raise RuntimeError('Unexpected disposable character')
        db.execute('update recovered_positions set area=2,scene=15,x=18,y=12,revision=revision+1 where character_id=4')
        db.commit()
    config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
    config['database']['path']=str(database)
    config['logging']['file']=str(OUT/'server.log')
    config['server']['port']=2598
    dev=config['development'];dev.pop('diagnostic_town',None)
    dev.update(diagnostic_shunying_manual=False,diagnostic_shunying_character_id=0,diagnostic_battle_terminal=False,
        diagnostic_battle_resources=False,diagnostic_battle_after_movement=False,
        diagnostic_battle_rounds=1,diagnostic_battle_experience=0,
        recovered_navigation=str(ROOT/'artifacts/world-atlas/indoor-2-15.json'))
    (OUT/'server-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    (OUT/'setup.json').write_text(json.dumps(dict(status='PREPARED_NOT_LIVE_ACCEPTED',
        client=str(client/'God2-shunying-manual.exe'),database=str(database),
        client_source_sha256=hashlib.sha256(game.read_bytes()).hexdigest(),
        skill=dict(kind=0,id=126,reserved_ids=[122,123,124,125]),hotbar=dict(character=None,row=0,key='F1',temporary=True),
        dynamic_clones_implemented=False,blackbox_passed=False),indent=2),encoding='utf-8')
    print(OUT)

if __name__=='__main__':main()
