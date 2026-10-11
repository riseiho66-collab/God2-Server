"""Current text-backed encounter candidates; never generates placements or stats.

Read-only sources. Output records separate original text/name membership from
missing server rules. Run with python -m tools.strike_lab.current_inferred_encounter_sources_20260927.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from .omega_assets import decode_csvz
from .current_monster_inventory import pinned_catalog, SOURCE, SOURCE_SHA, PLAIN_SHA
from .world_atlas import parse_catalog

ROOT=Path(__file__).resolve().parents[2]
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
PINS={
 'NPCMission03.csvZ':('681a64df6497d29818b0a81d1bdda2f6b0ee49bea710c100161c4ad309b42314','ecdfaad9f2de91da5bcf77b7d45eeb6ef68aa7e271ed474515d15414a0b87286'),
 'NPCMission06.csvZ':('58a167b9f486d19c928e48a99822183203a05fa5d2de80babcc7db99e78cd1f0','29273c8d2b8135fe09a36aed9845d88c0e354b3f36a21b99d9e6516d62e2de2b'),
 'NpcMission13.csvZ':('fa9a8338fb328cf8eaaaaa8f8a00f0b3d51c61789736324933c8387aeba74b2f','15bec786bc14035008fd9f08ef7ed5b979cb19987efeabc2d939a22680448b04'),
 'NPCNormal01.csvZ':('80750b0041db5284e598237c11ecee8ccfefa0121500919dee99fe098fcc4db0','f4c4e4cdb1572d8d6d3f16668cb64eee8376987c4d6e150efd96a9ae7e346d56'),
 'NPCNormal02.csvZ':('84a7ea509e4da4fbcb6b971d5c2f149fb944311aa4654f6c6c913267ed4335fa','0d14d69d652c9524d4ae467dcc9caa88895987716eea27bd27d52a8b4f81cc9b'),
 'Mission_data.csvZ':('659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716','f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0')}
SPECS=(
 ('gray_fox','截仙遺址','大灰狐',(3,0,1),3456,'狐皮',4408,4,[('NPCMission03.csvZ',958),('NPCNormal01.csvZ',999),('Mission_data.csvZ',447)]),
 ('giant_leech','截仙遺址','巨水蛭',(3,0,6),3505,'巨水蛭的尾巴',None,None,[('NPCMission03.csvZ',958),('NPCMission06.csvZ',967),('NpcMission13.csvZ',144)]),
 ('soil_flea','風吼黑洞','食土蚤',(3,2,1),3462,'蟲殼',4412,8,[('NPCMission03.csvZ',959),('NPCNormal02.csvZ',3),('Mission_data.csvZ',451)]),
 ('large_caterpillar','天絕黑洞','大毛虫',(4,12,2),3408,'毛虫怪的卵',4411,9,[('NPCMission03.csvZ',959),('Mission_data.csvZ',452)]))

def sha(raw):return hashlib.sha256(raw).hexdigest()

def rows(plain):
    offset=0;result=[]
    for line,raw in enumerate(plain.split(b'\n'),1):
        body=raw.rstrip(b'\r')
        result.append({'source_line':line,'decoded_offset':offset,'raw_record_hex':body.hex(),'row_sha256':sha(body)})
        offset+=len(raw)+1
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    p.add_argument('--output',type=Path,default=ROOT/'artifacts/research/inferred-encounter-sources-20260927')
    a=p.parse_args();client=a.client.resolve();out=a.output.resolve()
    if sha((client/'God2.exe').read_bytes())!=CLIENT_SHA:raise ValueError('Current client changed')
    source=(client/SOURCE).read_bytes();plain=decode_csvz(source)
    if sha(source)!=SOURCE_SHA or sha(plain)!=PLAIN_SHA:raise ValueError('Gamedata identity mismatch')
    catalog=pinned_catalog(client);maps=parse_catalog(plain);game_rows=rows(plain)
    section=None
    for row in game_rows:
        fields=bytes.fromhex(row['raw_record_hex']).split(b',')
        if len(fields)>1 and re.fullmatch(rb'[A-Za-z][A-Za-z0-9_]*',fields[0]):section=fields[0].decode('ascii')
        row['section']=section
    source_rows={};identities={}
    for name,(packed_sha,plain_sha) in PINS.items():
        packed=(client/'Data2/Patch/Comm'/name).read_bytes();decoded=decode_csvz(packed)
        if (sha(packed),sha(decoded))!=(packed_sha,plain_sha):raise ValueError('Changed text source '+name)
        source_rows[name]=rows(decoded);identities[name]={'source_sha256':packed_sha,'decoded_sha256':plain_sha}
    candidates=[]
    for key,map_name,monster_name,lookup,item_key,item_name,book_key,description,refs in SPECS:
        selected_maps=[r for r in maps if bytes.fromhex(r['map_name_bytes']).decode('cp950')==map_name and (r['area'],r['scene'])==lookup[:2]]
        selected=[r for r in catalog['records'] if r['lookup_visible'] and (r['area'],r['scene'],r['ordinal'])==lookup]
        if len(selected_maps)!=1 or len(selected)!=1 or bytes.fromhex(selected[0]['name_bytes_hex']).decode('cp950')!=monster_name:
            raise ValueError('Exact map/monster lookup changed '+key)
        if lookup[0]==0:raise ValueError('Companion namespace prohibited')
        texts=[]
        for filename,line in refs:
            row=dict(source_rows[filename][line-1]);raw=bytes.fromhex(row['raw_record_hex']);text=raw.decode('cp950',errors='strict')
            if map_name not in text or monster_name not in text:raise ValueError('Source relation text mismatch '+key)
            row.update(source_file=filename,text=text,text_id=None if filename=='Mission_data.csvZ' else int(raw.split(b',',1)[0]),
                namespace='Mission_data description' if filename=='Mission_data.csvZ' else filename.split('.')[0])
            texts.append(row)
        items=[]
        for wanted in (item_key,book_key):
            if wanted is None:continue
            matches=[]
            for r in game_rows:
                raw=bytes.fromhex(r['raw_record_hex']);fields=raw.split(b',')
                if r['section']==('MAT01' if wanted==item_key else 'MIS') and fields[0]==str(wanted).encode() and len(fields)>=9:
                    matches.append(dict(r,key=wanted,name=fields[4].decode('cp950'),text=raw.decode('cp950',errors='strict')))
            if len(matches)!=1:raise ValueError('Item key not unique '+str(wanted))
            if wanted==item_key and matches[0]['name']!=item_name:raise ValueError('Material name changed')
            if wanted==book_key and ('３０個'+item_name) not in matches[0]['text']:raise ValueError('Order book text changed')
            items.extend(matches)
        collisions=[{'area':r['area'],'scene':r['scene'],'ordinal':r['ordinal'],'source_line':r['source_line'],
            'excluded_companion_namespace':r['area']==0} for r in catalog['records'] if r['lookup_visible'] and
            bytes.fromhex(r['name_bytes_hex'])==monster_name.encode('cp950',errors='strict')]
        candidates.append({'candidate':key,'map_name':map_name,'monster_name':monster_name,'native_map_catalog':selected_maps[0],
            'native_display_record':selected[0],'supporting_texts':texts,'native_items':items,'same_name_visible_records':collisions,
            'journal_definition':69 if description else None,'journal_description':description,
            'text_collection_quantity':30 if description else None,
            'authority':{'map_monster_name_relation':'NATIVE_TEXT_VERIFIED','display_tuple':'EXACT_VISIBLE_NAME_AND_MAP_JOIN',
                'journal_dialogue_book_event_join':'INFERRED_NOT_ORIGINAL_EVENT_AUTHORITY'},
            'unknown':dict.fromkeys(['instance_id','spawn_x','spawn_y','facing','subregion','trigger','rate','respawn',
                'monster_level','hp','mp','physical_attack','magical_attack','physical_defense','magical_defense',
                'skills','experience','drop_rate','quest_accept_condition','quest_completion_event','reward'])})
    code_refs={}
    for name,needles in {
        'src/game/Battle.h':['struct BattleActor','class Battle','static Battle restore'],
        'src/handlers/RecoveredBattleService.h':['struct Policy','void bind'],
        'src/db/SqliteRecoveredCharacterRepository.cpp':['policy_id!="CUSTOM-0012/diagnostic-v1"','reserve_battle('],
        'src/core/Application.cpp':['std::vector<BattleActor> actors','town_battle_ready','NATIVE_MONSTER_PLACEMENT_GAP']}.items():
        raw=(ROOT/name).read_bytes();lines=raw.decode('utf-8-sig').splitlines()
        code_refs[name]={'sha256':sha(raw),'matches':[{'line':i,'text':line.strip()} for i,line in enumerate(lines,1) if any(n in line for n in needles)]}
    result={'client_sha256':CLIENT_SHA,'gamedata_source_sha256':SOURCE_SHA,'gamedata_decoded_sha256':PLAIN_SHA,
        'text_sources':identities,'candidates':candidates,'server_code_readonly':code_refs,
        'boundary':'No spawn, event, stats, reward or drop-rate generation. Map catalog coordinates are not spawn coordinates.'}
    out.mkdir(parents=True,exist_ok=True)
    (out/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'candidates':len(candidates),'source_files':len(identities)+1,'output':str(out)},ensure_ascii=False))

if __name__=='__main__':main()
