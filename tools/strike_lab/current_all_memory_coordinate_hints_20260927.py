"""Offline coordinate/name hints from the pinned, actual-RAM catalog receipt.

Never opens a process, starts a client, or turns text co-occurrence into spawns.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import re
from .current_live_memory_catalog_20260927 import source_quests
from .omega_assets import decode_csvz
from .recover_quests import parse_table

ROOT=Path(__file__).resolve().parents[2]
RECEIPT=ROOT/'artifacts/research/live-memory-references-20260927-03/memory-result.json'
RECEIPT_SHA='e568326018cc531193d4271a926e585cfd27dbdbb5ea190ca75f0d9339701bba'
GAME_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
QUEST_SHA='659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716'
COORD=re.compile(r'[（(](?P<label>[^()（）\r\n]{0,60}?[^\d()（）\r\n])?(?P<x>\d{1,5})\s*[,，/／、\s]\s*(?P<y>\d{1,5})\s*[）)]')
BOUNDARY=re.compile(r'[。！？!?；;\n]|\\n')
GAP=re.compile(r'(?:(?:/c[0-9])|\s)*\Z')


def digest(value):return hashlib.sha256(value).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def decode(raw):return raw.decode('cp950',errors='surrogateescape')
def text_view(raw):return raw.decode('cp950',errors='backslashreplace')


def build(receipt=RECEIPT,client=ROOT.parent/'God2'):
    encoded=receipt.read_bytes();require(digest(encoded)==RECEIPT_SHA,'RAM receipt identity mismatch')
    observed=json.loads(encoded);require(observed['accepted'] and observed['process_memory_writes']==0 and observed['logins']==0,'Receipt scope mismatch')
    require(observed['desktop_unchanged'] and observed['owned_client_closed'] and all(observed['files_unchanged'].values()),'Receipt cleanup/identity incomplete')
    before=observed['before_agreement']['quest_catalogs'];after=observed['after_agreement']['quest_catalogs']
    require(len(before)==len(after)==1 and before==after,'Quest catalog phases disagree')
    catalog=after[0];require(catalog['record_count']==418 and catalog['text_count']==2014,'RAM quest count mismatch')
    quests=source_quests();records=catalog['records'];require(len(records)==418,'RAM quest rows incomplete')
    mission_raw=(client/'Data2/Patch/Comm/Mission_data.csvZ').read_bytes();require(digest(mission_raw)==QUEST_SHA,'Quest source mismatch')
    parsed=parse_table('missions',decode_csvz(mission_raw));source_rows={};mission=None;index=0
    for row in parsed['records']:
        fields=[bytes.fromhex(f) for f in row['raw_fields_hex']]
        if fields[0]:mission=int(fields[0]);index=0
        else:source_rows[mission,index]=row;index+=1
    game=(client/'Data2/Patch/Comm/gamedata.csvZ').read_bytes();require(digest(game)==GAME_SHA,'Game source mismatch')
    lines=decode_csvz(game).splitlines();start=next(i for i,r in enumerate(lines) if r.startswith(b'NPCAppearData,'))
    count=int(lines[start].split(b',')[1]);require(count==4043,'NPC source count mismatch')
    statics=observed['loaded_static_catalogs'];npcs=statics['npc_records'];require(len(npcs)==count,'RAM NPC count mismatch')
    groups=defaultdict(list);npc_inventory=[];owner=int(statics['owner'],16)
    for ordinal,(row,source) in enumerate(zip(npcs,lines[start+1:start+1+count])):
        fields=source.split(b',');raw=bytes.fromhex(row['record94_hex']);key=int(fields[0]);name=raw[:16].split(b'\0')[0]
        require(len(raw)==94 and row['key']==key and row['source_line']==start+2+ordinal and row['source_record_sha256']==digest(source),'NPC source/RAM row mismatch')
        require(int(row['address'],16)==owner+0x121ea+94*key and name==fields[1],'NPC RAM address/name mismatch')
        entry={'key':key,'source_line':row['source_line'],'address':row['address'],'name_hex':name.hex(),
               'name':text_view(name),'record94_sha256':digest(raw),'source_record_sha256':digest(source)}
        npc_inventory.append(entry)
        if name:groups[decode(name)].append(entry)
    hints=[];ledger=[];adjacent=[];mention_keys=set();mention_names=set();coordinate_texts=0
    for source,memory in zip(quests,records):
        require(source['id']==memory['id'] and source['name'].hex()==memory['name_hex'] and source['count']==memory['count'],'Quest RAM header mismatch')
        record40=bytes.fromhex(memory['record40_hex'])
        require(len(record40)==40 and int.from_bytes(record40[:2],'little')==source['count'] and record40[2:36].split(b'\0')[0]==source['name'],'Quest raw40 mismatch')
        require(int(memory['record_address'],16)==int(catalog['base'],16)+(source['id']-1)*40 and int(memory['text_pointer_array'],16)==int.from_bytes(record40[36:40],'little'),'Quest raw address/pointer mismatch')
        require(len(source['texts'])==len(memory['texts'])==source['count'],'Quest RAM descriptions incomplete')
        for index,(full,actual) in enumerate(zip(source['texts'],memory['texts'])):
            raw=full[:379];require(len(raw)==actual['length'] and digest(raw)==actual['sha256'],'Quest RAM text hash/length mismatch')
            text=decode(raw);offsets=[0]
            for char in text:offsets.append(offsets[-1]+len(char.encode('cp950',errors='surrogateescape')))
            require(offsets[-1]==len(raw),'CP950 offset round trip mismatch')
            source_row=source_rows[source['id'],index]
            common={'mission_id':source['id'],'description_index':index,'source_line':source_row['source_line'],
                    'source_record_sha256':source_row['source_record_sha256'],'source_text_sha256':digest(full),
                    'source_text_length':len(full),'native_text_length':len(raw),'native_text_sha256':actual['sha256'],
                    'native_text_address':actual['address'],'native_record_address':memory['record_address'],
                    'native_truncated':len(full)!=len(raw)}
            ledger.append(common)
            positions=list(COORD.finditer(text))
            if not positions:continue
            coordinate_texts+=1;coordinates=[]
            bounds=[(m.start(),m.end()) for m in BOUNDARY.finditer(text)]
            for number,match in enumerate(positions):
                left=max((end for begin,end in bounds if end<=match.start()),default=0)
                right=min((begin for begin,end in bounds if begin>=match.end()),default=len(text))
                coordinates.append({'index':number,'x':int(match['x']),'y':int(match['y']),
                    'parenthetical_prefix':match['label'] or '',
                    'char_span':[match.start(),match.end()],'byte_span':[offsets[match.start()],offsets[match.end()]],
                    'token_memory_address':hex(int(actual['address'],16)+offsets[match.start()]),
                    'token_hex':raw[offsets[match.start()]:offsets[match.end()]].hex(),
                    'segment_char_span':[left,right],'segment_byte_span':[offsets[left],offsets[right]],
                    'segment_memory_address':hex(int(actual['address'],16)+offsets[left]),
                    'segment_hex':raw[offsets[left]:offsets[right]].hex(),'segment_text':text_view(raw[offsets[left]:offsets[right]])})
            mentions=[]
            for name,candidates in groups.items():
                at=text.find(name)
                while at>=0:
                    end=at+len(name)
                    mentions.append({'name':name,'name_hex':name.encode('cp950').hex(),'char_span':[at,end],
                        'byte_span':[offsets[at],offsets[end]],'mention_memory_address':hex(int(actual['address'],16)+offsets[at]),'candidate_keys':[row['key'] for row in candidates],
                        'candidate_records':candidates,'ambiguous_name':len(candidates)>1,
                        'lexical_match_only':True,'short_name_requires_review':len(name)<2})
                    at=text.find(name,at+1)
            mentions.sort(key=lambda m:(m['char_span'][0],-m['char_span'][1],m['candidate_keys']))
            for i,mention in enumerate(mentions):
                mention['index']=i;mention['contained_in_other_mentions']=[j for j,other in enumerate(mentions) if j!=i and
                    other['char_span'][0]<=mention['char_span'][0] and other['char_span'][1]>=mention['char_span'][1] and other['char_span']!=mention['char_span']]
                mention_keys.update(mention['candidate_keys']);mention_names.add(mention['name'])
            relations=[]
            for coord in coordinates:
                linked=[m['index'] for m in mentions if m['char_span'][1]<=coord['char_span'][0] and GAP.fullmatch(text[m['char_span'][1]:coord['char_span'][0]])]
                if linked:
                    keys=sorted({key for i in linked for key in mentions[i]['candidate_keys']})
                    relation={'coordinate_index':coord['index'],'mention_indices':linked,'candidate_keys':keys,
                        'ambiguous':len(keys)!=1 or len(linked)!=1,'authority':'ADJACENT_TEXT_NAME_COORDINATE_HINT_ONLY',
                        'direction':None,'world_instance_id':None,'world_spawn_qualified':False}
                    relations.append(relation);adjacent.append({**common,**relation,'x':coord['x'],'y':coord['y']})
            hints.append({**common,'text_hex':raw.hex(),'text':text_view(raw),'coordinates':coordinates,
                'name_mentions':mentions,'adjacent_relations':relations,
                'unlinked_coordinate_indices':[c['index'] for c in coordinates if c['index'] not in {r['coordinate_index'] for r in relations}],
                'cooccurrence_authority':'INDEPENDENT_COORDINATE_AND_NAME_LISTS; NO CARTESIAN JOIN',
                'spawn_qualified':False})
    require(len(ledger)==2014,'Not all RAM quest texts verified')
    # Enemy coverage is referenced intact, not reinterpreted as coordinate data.
    require(len(statics['enemy_records'])==7815 and len(statics['enemy_groups'])==96,'Existing monster receipt incomplete')
    summary={'quest_records_verified':418,'quest_texts_verified':len(ledger),'npc_records_verified':len(npc_inventory),
        'npc_nonempty_unique_names':len(groups),'npc_empty_name_rows':sum(not n['name_hex'] for n in npc_inventory),
        'all_duplicate_name_groups':sum(len(v)>1 for v in groups.values()),'texts_with_coordinates':coordinate_texts,
        'texts_with_coordinates_and_any_npc_name':sum(bool(row['name_mentions']) for row in hints),
        'coordinate_tokens':sum(len(row['coordinates']) for row in hints),'mentioned_unique_names':len(mention_names),
        'mentioned_candidate_keys_including_duplicates':len(mention_keys),'adjacent_hint_relations':len(adjacent),
        'ambiguous_adjacent_relations':sum(row['ambiguous'] for row in adjacent),
        'qualified_world_spawns':0,'existing_monster_arena_records':7815,'existing_visible_monster_groups':96}
    return {'schema':'god2-actual-memory-coordinate-hints-v1','receipt':str(receipt.relative_to(ROOT)),
        'receipt_sha256':RECEIPT_SHA,'sources':{'Mission_data_csvZ_sha256':QUEST_SHA,'gamedata_csvZ_sha256':GAME_SHA},
        'scope':'OFFLINE_RECONSTRUCTION_OF_SOURCE_BYTES_MATCHED_TO_ACTUAL_RAM_RECEIPT; NO NEW_PROCESS_READS',
        'native_text_rule':'source[:379]; original loader byte bound, including possible trailing CP950 half-character',
        'summary':summary,'qualified_text_ledger':ledger,'npc_records':npc_inventory,
        'duplicate_name_groups':[{'name':name,'candidate_records':rows} for name,rows in sorted(groups.items()) if len(rows)>1],
        'coordinate_texts':hints,'adjacent_name_coordinate_hints':adjacent,
        'limits':['No inferred facing, world instance or area/scene is supplied.',
                  'Names may be substring mentions, aliases, destinations, monsters, quest targets or dialogue subjects.',
                  'Even an adjacent name and coordinate is a prose hint, never a world spawn record.',
                  'Non-adjacent names and coordinates remain separate lists; no Cartesian binding.',
                  'Duplicate names retain every RAM catalog key and record address.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    result=build();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'sha256':digest(args.output.read_bytes()),**result['summary']}));return 0


if __name__=='__main__':raise SystemExit(main())
