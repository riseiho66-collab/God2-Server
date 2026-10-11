"""Audit current-client NPC placement evidence without inventing coordinates.

Does not read retired corpora, modify client files, grant entities or populate
spawn tables. Mission-text coordinate references remain hints, not placements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import pefile
from .omega_assets import decode_csvz

CATALOG_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
RANGES={
    'npc_direction_and_new_position':(0xcc621,0xcc690,'e2aac96315e1a4408dc39ad9154f785885a983b5dcf2250bee1d7bc9ecb96982'),
    'existing_npc_position':(0xcc41a,0xcc447,'2b43c4598aa96eed157a59d13ebd99578d876f872e40dc241a4aa0972a002ce9'),
    'received_record_argument':(0x6aa63,0x6aa8e,'8404b51adfba80ca6ec3faed7707bc31e71bd68760ba895efc432992c5ac0d79')}
def sha(data):return hashlib.sha256(data).hexdigest()
def section(lines,name):
    starts=[i for i,row in enumerate(lines) if row.startswith(name+b',')]
    if len(starts)!=1:raise ValueError('Expected unique section '+repr(name))
    start=starts[0];count=int(lines[start].split(b',')[1])
    if start+count>=len(lines):raise ValueError('Truncated section')
    return [(start+i+2,raw) for i,raw in enumerate(lines[start+1:start+1+count])]

def audit(root):
    root=root.resolve();catalog_path=root/'Data2/Patch/Comm/gamedata.csvZ'
    raw=catalog_path.read_bytes()
    if sha(raw)!=CATALOG_SHA:raise ValueError('Current NPC source changed')
    decoded=decode_csvz(raw);lines=decoded.splitlines()
    templates=[]
    for line,row in section(lines,b'NPCAppearData'):
        fields=row.split(b',')
        if len(fields) not in (5,9):raise ValueError('Unsupported native appearance row')
        templates.append({'template':int(fields[0]),'name':fields[1].decode('cp950'),
            'source_line':line,'raw_record_hex':row.hex(),'record_sha256':sha(row),
            'appearance':int(fields[2]),'raw_remaining_fields':[field.decode('ascii') for field in fields[3:]],
            'area':None,'scene':None,'x':None,'y':None,'direction':None})
    groups=[]
    for line,row in section(lines,b'NPCList'):
        fields=[int(value) for value in row.split(b',')]
        if not 2<=len(fields)<=7:raise ValueError('Unsupported native preload group row')
        groups.append({'area':fields[0],'scene':fields[1],'appearance_resources':fields[2:],
            'source_line':line,'raw_record_hex':row.hex(),'record_sha256':sha(row)})
    # Parse every coordinate reference with exact line and byte record origin.
    hints=[];hint_files=[]
    pattern=re.compile(r'[（(]\s*(\d{1,5})\s*[/／,，]\s*(\d{1,5})\s*[)）]')
    for path in sorted((root/'Data2/Patch/Comm').glob('*.csvZ')):
        if '-gb.' in path.name.lower():continue
        if not (path.name.lower().startswith(('mission_data','npcmission','npcnormal','multimessage'))):continue
        packed=path.read_bytes();plain=decode_csvz(packed);count=0
        for line,record in enumerate(plain.splitlines(),1):
            text=record.decode('cp950',errors='replace')
            for match in pattern.finditer(text):
                count+=1
                hints.append({'file':path.relative_to(root).as_posix(),'file_sha256':sha(packed),
                    'source_line':line,'record_sha256':sha(record),'raw_record_hex':record.hex(),
                    'text':text,'x_reference':int(match[1]),'y_reference':int(match[2]),
                    'template_name_mentions':[t['template'] for t in templates if t['name'] and t['name'] in text],
                    'qualification':'TEXT_REFERENCE_ONLY_NOT_FULL_SPAWN_RECORD','direction':None})
        hint_files.append({'file':path.relative_to(root).as_posix(),'sha256':sha(packed),'coordinate_references':count})
    # Terrain/model assets inspected independently from server-sent NPC actors.
    map_files=[];npc_model_references=[]
    for path in sorted((root/'Data2/map').rglob('*')):
        if path.suffix.lower() not in ('.mdtz','.mdlz','.hmdz'):continue
        packed=path.read_bytes();plain=decode_csvz(packed)
        hits=[{'line':i+1,'raw_hex':row.hex()} for i,row in enumerate(plain.splitlines()) if b'npc' in row.lower()]
        map_files.append({'file':path.relative_to(root).as_posix(),'sha256':sha(packed),'decoded_sha256':sha(plain)})
        if hits:npc_model_references.append({'file':path.relative_to(root).as_posix(),'references':hits})
    exe=root/'God2.exe';image=pefile.PE(str(exe)).get_memory_mapped_image()
    code=[]
    for name,(start,end,expected) in RANGES.items():
        actual=sha(image[start:end])
        if actual!=expected:raise ValueError('Current EXE NPC receive path changed: '+name)
        code.append({'name':name,'rva_start':hex(start),'rva_end':hex(end),'sha256':actual})
    return {'schema':'god2-current-npc-placement-evidence-v1',
        'client_exe_sha256':sha(exe.read_bytes()),'catalog_sha256':sha(raw),'catalog_decoded_sha256':sha(decoded),
        'counts':{'appearance_templates':len(templates),'preload_group_rows':len(groups),
            'map_assets_inspected':len(map_files),'text_coordinate_references':len(hints),
            'fully_qualified_native_placements':0,'native_placements_written':0},
        'native_receive_contract':{'logical_opcode':'0x72','logical_size':21,
            'direction':'logical[9] >> 5 (native numeric direction, compass names unqualified)',
            'x':'(little_endian_u32(logical[17:21]) >> 2) & 0x7fff',
            'y':'little_endian_u32(logical[17:21]) >> 17','matched_current_executable_ranges':code},
        'templates':templates,'scene_preload_groups':groups,'text_coordinate_hints':hints,
        'hint_sources':hint_files,'map_assets_inspected':map_files,'npc_model_references':npc_model_references,
        'missing_for_full_placement':'Authoritative area/scene/template/x/y/direction records from native server spawn data or original spawn messages. A parser or animation resource does not contain those input values by itself.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--client',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.resolve().is_relative_to(args.client.resolve()):raise ValueError('Output must be outside client')
    result=audit(args.client);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['counts'],ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
