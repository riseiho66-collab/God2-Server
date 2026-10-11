"""Current source text constraints; never native NPC spawn rows.

Automatic name/map co-occurrence is retained separately from reviewed textual
relationships. All catalog matches remain candidates and facing stays unknown.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from .omega_assets import decode_csvz
from .audit_native_npc_placements import section
from .world_atlas import parse_catalog

ROOT = Path(__file__).resolve().parents[2]
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
GAME_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
COORD = re.compile(r'[（(]\s*(\d{1,5})\s*(?:[/／,，]|\s+)\s*(\d{1,5})\s*[)）]')
# Manual text interpretation, not a machine-derived spawn assignment. Each tuple
# must match the named original row/name/coordinate/map text on every run.
REVIEWED = [
    ('Mission_data.csvZ',5,'涂諦頌','楓華鎮',110,110),
    ('Mission_data.csvZ',8,'田清郎','楓華鎮',117,52),
    ('Mission_data.csvZ',16,'齊慕','楓華鎮',129,44),
    ('Mission_data.csvZ',31,'段嵐','楓華鎮',136,56),
    ('Mission_data.csvZ',34,'曹大娘','楓華鎮',71,60),
    ('Mission_data.csvZ',59,'葛員外','葛城',131,204),
    ('Mission_data.csvZ',59,'錢員外','葛城',69,179),
    ('Mission_data.csvZ',59,'李員外','葛城',101,234),
    ('Mission_data.csvZ',61,'李管家','南原部落',116,100),
    ('Mission_data.csvZ',66,'燕三郎','昆吾鎮',119,167),
    ('Mission_data.csvZ',73,'公孫望','葛城',95,127),
    ('Mission_data.csvZ',73,'孫劭','南原部落',104,110),
    ('Mission_data.csvZ',118,'百戲藝人','葛城',214,180),
    ('Mission_data.csvZ',122,'仙鶴道僮','楓華鎮',119,119),
    ('Mission_data.csvZ',125,'仙華僮子','果力村',110,114),
    ('Mission_data.csvZ',125,'仙鶴道僮','楓華鎮',119,119),
    ('Mission_data.csvZ',288,'哪吒','楓華鎮',138,47),
    ('Mission_data.csvZ',371,'董古','楓華鎮',107,93),
    ('Mission_data.csvZ',389,'美食家','楓華鎮',105,85),
    ('Mission_data.csvZ',391,'馴獸師','楓華鎮',60,108),
    ('Mission_data.csvZ',525,'宣逢','昆吾鎮',146,107),
    ('Mission_data.csvZ',526,'宜逢','昆吾鎮',89,173),
    ('Mission_data.csvZ',532,'鄭立','葛城',78,188),
    ('Mission_data.csvZ',532,'鄭中','葛城',63,205),
    ('Mission_data.csvZ',542,'林雄','昆吾鎮',89,121),
    ('Mission_data.csvZ',552,'賣花的小女孩','葛城',194,101),
    ('Mission_data.csvZ',577,'仙童','崑崙仙界',148,85),
    ('Mission_data.csvZ',1164,'聖獸仙童','楓華鎮',128,122),
    ('Mission_data.csvZ',1488,'廚師梁禎','果力村',108,110),
    ('Mission_data.csvZ',1492,'李樂','果力村',113,69),
    ('Mission_data.csvZ',1494,'阿銀嬸','果力村',69,72),
    ('Mission_data.csvZ',1496,'馬老伯','果力村',68,116),
    ('Mission_data.csvZ',1498,'成範永','茄城',82,66),
    ('Mission_data.csvZ',1506,'張佑','果力村',75,123),
    ('Mission_data.csvZ',1507,'金熙','茄城',119,88),
    ('Mission_data.csvZ',1518,'農夫車允浩','茄城',143,150),
    ('Mission_data.csvZ',2041,'守衛大將軍','甘城',122,81),
    ('Mission_data.csvZ',2164,'傷病蘿蔔人','果城',131,62),
    ('Mission_data.csvZ',2165,'腰痛老人','昆吾鎮',150,61),
    ('Mission_data.csvZ',2166,'肥胖男子','暮汐村',55,70),
    ('Mission_data.csvZ',2167,'凍傷女子','焰霜鎮',170,97),
    ('NpcMission13.csvZ',309,'秦天君','誅仙陣',48,41),
    ('NpcMission13.csvZ',309,'趙天君','誅仙陣',35,165),
    ('NpcMission13.csvZ',309,'孫天君','誅仙陣',167,170),
    ('NpcMission13.csvZ',309,'張天君','誅仙陣',167,46),
    ('NpcMission13.csvZ',309,'通天教主','誅仙陣',104,101),
]
REVIEWED_NONCATALOG = [
    ('NPCNormal02.csvZ',821,'年輕女子','楓華鎮',71,69),
    ('NPCNormal02.csvZ',821,'擔心的小女孩','果力村',51,85),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(client):
    if sha((client/'God2.exe').read_bytes()) != CLIENT_SHA:
        raise ValueError('Current client identity changed')
    comm = client/'Data2/Patch/Comm'
    game = (comm/'gamedata.csvZ').read_bytes()
    if sha(game) != GAME_SHA:
        raise ValueError('Current gamedata changed')
    plain = decode_csvz(game)
    templates = defaultdict(list)
    for line, raw in section(plain.splitlines(), b'NPCAppearData'):
        fields = raw.split(b',')
        name = fields[1].decode('cp950')
        templates[name].append({'catalog_index': int(fields[0]), 'appearance': int(fields[2]),
                                'source_line': line, 'raw_record_hex': raw.hex(), 'sha256': sha(raw)})
    maps = defaultdict(list)
    for row in parse_catalog(plain):
        maps[bytes.fromhex(row['map_name_bytes']).decode('cp950')].append(row)
    # Longest exact names avoid promoting suffix matches, e.g. 仙童 from 聖獸仙童.
    names = sorted((x for x in templates if x), key=lambda x: (-len(x),x))
    sources, hints, row_index = [], [], {}
    for path in sorted(comm.glob('*.csvZ'), key=lambda p:p.name.lower()):
        if '-gb.' in path.name.lower() or not path.name.lower().startswith(
                ('gamedata','mission_data','npcnormal','npcmission','multimessage','dailymission','daymissiondesc')):
            continue
        packed = path.read_bytes()
        decoded = decode_csvz(packed)
        source = {'file':path.relative_to(client).as_posix(), 'sha256':sha(packed),
                  'decoded_sha256':sha(decoded), 'coordinate_tokens':0}
        sources.append(source)
        for line, raw in enumerate(decoded.splitlines(),1):
            text = raw.decode('cp950',errors='backslashreplace')
            matches = list(COORD.finditer(text))
            if not matches:
                continue
            origin = {'file':source['file'], 'file_sha256':source['sha256'],
                      'source_line':line, 'raw_record_hex':raw.hex(), 'record_sha256':sha(raw), 'text':text}
            row_index[path.name.lower(),line] = origin
            map_mentions = [name for name in maps if len(name)>1 and name in text]
            for match in matches:
                adjacent = next((name for name in names if text[:match.start()].endswith(name)),None)
                hints.append({**origin, 'coordinate_character_offset':match.start(),
                              'x_hint':int(match[1]), 'y_hint':int(match[2]),
                              'exact_adjacent_name':adjacent,
                              'catalog_candidates':templates[adjacent] if adjacent else [],
                              'map_names_elsewhere_in_same_row':map_mentions,
                              'map_binding':None, 'world_instance_id':None, 'direction':None,
                              'authority':'UNREVIEWED_TEXT_COORDINATE_NOT_NPC_PLACEMENT'})
                source['coordinate_tokens'] += 1
    reviewed = []
    for entry in REVIEWED + REVIEWED_NONCATALOG:
        filename,line,name,map_name,x,y = entry
        original = row_index[filename.lower(),line]
        matching = [h for h in hints if h['file']==original['file'] and h['source_line']==line
                    and (h['exact_adjacent_name']==name or entry in REVIEWED_NONCATALOG)
                    and h['x_hint']==x and h['y_hint']==y]
        if not matching or name not in original['text'] or map_name not in original['text'] or not maps[map_name]:
            raise ValueError('Reviewed original text constraint changed')
        conditions = []
        if name == '田清郎': conditions.append('Text explicitly describes invisible person; visibility/state unresolved')
        if name == '齊慕': conditions.append('Text describes contested identity/impostor; same-name catalog not unique authority')
        if name == '仙童': conditions.append('Text specifies 藥草園; world entity and sublocation binding unresolved')
        if map_name == '誅仙陣': conditions.append('Text describes instance, defeat disappearance and seal-item restrictions; no unconditional permanent spawn')
        if entry in REVIEWED_NONCATALOG: conditions.append('Explicit named recipient and map/space-separated coordinate; no exact NPCAppearData name match')
        reviewed.append({**original, 'name':name, 'map_name_text':map_name, 'x_hint':x, 'y_hint':y,
                         'catalog_candidates':templates[name], 'map_catalog_candidates':maps[map_name],
                         'world_instance_id':None, 'direction':None, 'placement_eligible':False,
                         'interpretation_conditions':conditions,
                         'authority':'REVIEWED_NAME_MAP_XY_TEXT_CONSTRAINT_ONLY'})
    return {'schema':'god2-current-npc-text-constraints-v1', 'client_sha256':CLIENT_SHA,
            'catalog_sha256':GAME_SHA, 'catalog_decoded_sha256':sha(plain), 'sources':sources,
            'counts':{'source_files':len(sources),'coordinate_tokens':len(hints),
                      'tokens_with_exact_adjacent_catalog_name':sum(bool(h['exact_adjacent_name']) for h in hints),
                      'reviewed_name_map_xy_constraints':len(reviewed),
                      'reviewed_unique_name_map_xy':len({(r['name'],r['map_name_text'],r['x_hint'],r['y_hint']) for r in reviewed}),
                      'qualified_complete_placements':0},
            'unreviewed_coordinate_hints':hints, 'reviewed_constraints':reviewed,
            'excluded_interpretations':[
                'Mission_data line12: 田清郎117/52 and 截仙遺址625/91 refer to different subjects; do not join map by row co-occurrence',
                'Mission_data line34: 曹大娘楓華鎮 and 曹爾金鰲牌坊 are different locations; do not assign 曹爾 to 楓華鎮',
                'Mission_data line380/385: 豹斑駒 has pursuit/movement locations, not a stationary human NPC',
                'Mission_data line1581: 箱子312/240 is an object-retrieval target, not an NPC constraint',
                'Mission_data line2168 / NPCMission13 line435: 九天冰屋2F qualifier cannot be dropped to select an unqualified floor'],
            'runtime_policy':'No spawning/DB writes. Exact-name and exact-map catalog joins are candidate sets, not world-entity assignments. Facing remains unknown.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.resolve().is_relative_to(args.client.resolve()):
        raise ValueError('Output must be outside client')
    result=audit(args.client)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'sha256':sha(args.output.read_bytes()),**result['counts']}))


if __name__=='__main__':main()
