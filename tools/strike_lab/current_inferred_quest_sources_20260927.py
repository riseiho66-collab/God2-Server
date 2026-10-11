"""Pinned source bundle for explicitly inferred Guoli collection-quest runtime.

No DB/client writes. Exact source facts, semantic joins, external historical
rewards and proposed server policies carry separate authority fields.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .omega_assets import decode_csvz
from .audit_native_npc_placements import section
from .world_atlas import parse_catalog

ROOT = Path(__file__).resolve().parents[2]
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
PINS = {
    'gamedata': ('70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731', '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'),
    'Mission_data': ('659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716', 'f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0'),
    'NPCMission09': ('0f00d56b93808a933e6bee811c79d477651b8c6aac002b271a79e002e5dfc812', '96fbea32007a5e8272a57ffc58c865d677485f1771ded22a27bca9982b5dc36f'),
    'NpcMission13': ('fa9a8338fb328cf8eaaaaa8f8a00f0b3d51c61789736324933c8387aeba74b2f', '15bec786bc14035008fd9f08ef7ed5b979cb19987efeabc2d939a22680448b04'),
}
WIKI = 'https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%9E%9C%E5%8A%9B%E6%9D%91'
SPECS = [
    (234,'果力名產',2936,'廚師梁禎',108,110,1487,5098,'蝸牛肉',5,8885,3,400),
    (236,'青梅竹馬',2937,'李樂',113,69,1491,5091,'冬蟲夏草',5,8890,10,3000),
    (237,'愛心便當',2938,'阿銀嬸',69,72,1493,5098,'蝸牛肉',10,8900,5,1500),
    (238,'禦寒衣物',2939,'馬老伯',68,116,1495,3464,'兔皮',20,8895,8,2000),
]


def sha(data): return hashlib.sha256(data).hexdigest()


def bundle(client):
    if sha((client/'God2.exe').read_bytes()) != CLIENT_SHA:
        raise ValueError('Current client identity changed')
    sources, decoded = {}, {}
    for name,(packed_sha,plain_sha) in PINS.items():
        path = client/'Data2/Patch/Comm'/f'{name}.csvZ'
        packed = path.read_bytes()
        plain = decode_csvz(packed)
        if sha(packed) != packed_sha or sha(plain) != plain_sha:
            raise ValueError('Pinned current quest source changed: '+name)
        sources[name] = {'path':path.relative_to(client).as_posix(), 'source_sha256':packed_sha, 'decoded_sha256':plain_sha}
        decoded[name] = plain

    def row(name, line):
        raw = decoded[name].splitlines()[line-1]
        return {'source':name, 'line':line, 'raw_hex':raw.hex(), 'sha256':sha(raw),
                'text':raw.decode('cp950'), 'authority':'CURRENT_NATIVE_SOURCE_TEXT'}

    game_lines = decoded['gamedata'].splitlines()
    npc = {int(raw.split(b',')[0]):line for line,raw in section(game_lines,b'NPCAppearData')}
    item_rows = {}
    for tag in (b'MAT01',b'MIS'):
        for line,raw in section(game_lines,tag):
            item_rows[int(raw.split(b',')[0])] = (line,tag.decode())
    dialogues = {int(raw.split(b',')[0]):line for line,raw in enumerate(decoded['NPCMission09'].splitlines(),1)
                 if raw.split(b',')[0].isdigit()}
    maps = [x for x in parse_catalog(decoded['gamedata']) if (x['area'],x['scene'])==(13,12)]
    if len(maps)!=1 or bytes.fromhex(maps[0]['map_name_bytes']).decode('cp950')!='果力村':
        raise ValueError('Guoli map namespace changed')
    quests=[]
    for mission,title,npc_id,name,x,y,definition_line,key,item_name,quantity,dialog_base,level,xp in SPECS:
        definition = row('Mission_data',definition_line)
        description = row('Mission_data',definition_line+1)
        if not definition['text'].startswith(f'{mission},[新手任務]{title},1'):
            raise ValueError('Mission definition changed')
        npc_record=row('gamedata',npc[npc_id])
        if npc_record['text'].split(',')[1]!=name:
            raise ValueError('NPC exact name changed')
        line,section_name=item_rows[key]
        item_record=row('gamedata',line)
        if item_record['text'].split(',')[4]!=item_name:
            raise ValueError('Item exact name changed')
        roles={role:row('NPCMission09',dialogues[dialog_base+offset])
               for offset,role in enumerate(('idle_before','offer','incomplete','completion','idle_after'))}
        for offset,role in enumerate(roles):roles[role]['text_id']=dialog_base+offset
        quests.append({'mission_id':mission,'name':title,'definition':definition,'description':description,
            'npc':{'catalog_id':npc_id,'exact_name':name,'source':npc_record,'area':13,'scene':12,
                   'x_text_hint':x,'y_text_hint':y,'direction':None,'world_instance_id':None,
                   'join_authority':'EXACT_NAMES_AND_CURRENT_MISSION_TEXT; WORLD INSTANCE AND FACING REQUIRE CUSTOM DESIGN'},
            'requirement':{'item_key':key,'item_name':item_name,'quantity':quantity,'source_section':section_name,
                           'item_source':item_record,'quantity_authority':'CURRENT_MISSION_AND_DIALOGUE_TEXT',
                           'owned_consumption_policy_authority':'INFERRED_SERVER_DESIGN'},
            'dialogue_candidates':roles,
            'dialogue_state_mapping_authority':'SEMANTIC_TEXT_JOIN_NOT_NATIVE_SERVER_TRANSITION_TABLE',
            'external_historical':{'url':WIKI,'observed_date':'2026-09-27','minimum_level_reported':level,
                                   'reward_exp_reported':xp,'reward_reputation_reported':1,
                                   'authority':'EXTERNAL_HISTORICAL_COMMUNITY_NOT_CURRENT_NATIVE',
                                   'npc_coordinate_discrepancy': {'external':[69,115],'current_text':[68,116]} if mission==238 else None},
            'proposed_journal_active_value':(1<<16)|mission,
            'journal_transition_authority':'NATIVE_SELECTOR_FORMAT; INFERRED_ACCEPT/COMPLETE_TIMING',
            'design_id':None,'repeat_policy_native':None,'prerequisites_native':None})
    drop=row('NpcMission13',974)
    if not drop['text'].startswith('12972,'):raise ValueError('Drop-source text key changed')
    return {'schema':'god2-inferred-guoli-quest-source-bundle-v1','client_sha256':CLIENT_SHA,
            'sources':sources,'map_catalog':maps[0],'quests':quests,
            'recommended_first_mission':234,'material_drop_text':drop,
            'drop_authority':'CURRENT_TEXT_ONLY; NO RATE, TABLE OR GUARANTEED DROP CLAIM',
            'external_access':'Web search returned the page sections; direct open returned HTTP403. No external page bytes falsely hashed.',
            'proposed_policy':{'authority':'CUSTOM_DESIGN_PENDING_PARENT_ID',
                'lifecycle':['not_started','accepted','completed'],
                'repeat':'once per character with unique completion receipt; not recovered original repeat policy',
                'accept':'issued NPC conversation + level gate if adopting historical reference + owned free journal slot',
                'turn_in':'owned bag0..29 exact source-key counts; atomically consume requirement, update exp/reputation, clear own journal entry, commit receipt',
                'dialogue':'bind C2S85 to issued session/NPC/stage/revision, never reinterpret raw request_word as mission ID',
                'no_grant_on_read':'open/refresh/insufficient/replay/other-owner/pending battle must not mutate balances',
                'consumption_order':'deterministic ascending bag slots if parent adopts; preserve unrelated instance metadata',
                'remaining_design_fields':['world instance/facing','interaction distance','level/rebirth eligibility interpretation',
                                           'reward overflow and level-up integration','material acquisition drop rates','cancel/repeat policy']}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.resolve().is_relative_to(args.client.resolve()):raise ValueError('No client output')
    result=bundle(args.client)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'quests':len(result['quests']),'first':234,'sha256':sha(args.output.read_bytes())}))


if __name__=='__main__':main()
