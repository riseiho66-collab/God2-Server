"""Inventory full actual .text skill-field candidates; preserve authority gaps."""
import argparse
from bisect import bisect_right
from collections import Counter
from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_AC_READ
from capstone.x86 import X86_OP_MEM,X86_REG_ESP
from tools.strike_lab import import_native_skills as skill_import
from tools.strike_lab import import_native_npc_display as npc_import
from tools.strike_lab import import_native_enemy_display as enemy_import

ROOT=Path(__file__).resolve().parents[2]
RECON=ROOT.parent.parent/'God2-解殼EXE原始碼重建/decompiled/functions.tsv'
def require(ok,message):
    if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def run(directory):
    receipt=directory/'memory-result.json';raw=receipt.read_bytes();value=json.loads(raw)
    require(value['accepted'] and value['process_memory_writes']==0 and value['screenshots']==0,
        'Successful actual read-only memory receipt required')
    require(value['owned_client_closed'] and value['desktop_unchanged'],'Cleanup/desktop qualification required')
    capture=value['capture'];loaded=capture['full_loaded_catalogs'];skills=capture['skills']['records']
    require(capture['coverage']['scene_entries_read']==512 and len(capture['all_map_records'])==144,'Full world coverage required')
    require(len(loaded['npc_records'])==4043 and len(loaded['enemy_records'])==7815 and len(skills)==448,'Full display/skill catalogs required')
    expected=skill_import.pinned_records(ROOT.parent/'God2')
    by_key={(row[5],row[6]):row for row in expected}
    for row in skills:
        source=by_key[row['kind'],row['id']];memory=bytes.fromhex(row['record110_hex'])
        require(memory==source[4] and digest(memory)==row['sha256'],'Actual skill whole-record mismatch')
        require(struct.unpack_from('<H',memory,0x42)[0]==row['mp_threshold_word'],'MP WORD mismatch')
    config=json.loads((ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json').read_text('utf-8'))
    database=Path(config['database']['path'])
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        stored=db.execute('SELECT '+skill_import.RECORD_COLUMNS+' FROM native_skill_catalog WHERE dataset_id=? ORDER BY source_record_index',(skill_import.DATASET,)).fetchall()
        require(stored==expected,'Formal complete skill source mismatch')
        require(db.execute('SELECT '+skill_import.SOURCE_COLUMNS+' FROM native_data_sources WHERE dataset_id=?',(skill_import.DATASET,)).fetchall()==[skill_import.SOURCE_ROW],'Formal skill metadata mismatch')
        require(db.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()==npc_import.pinned_rows(ROOT.parent/'God2'),'Formal full NPC mismatch')
        require(db.execute('SELECT dataset_id,source_record_index,source_line,source_offset,record_sha256,raw_record,area_generation,area,scene,ordinal,lookup_visible,source_label,name_bytes FROM native_enemy_display_catalog ORDER BY source_record_index').fetchall()==enemy_import.pinned_rows(ROOT.parent/'God2'),'Formal full enemy mismatch')
    functions=[]
    with RECON.open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream,delimiter='\t'):
            if row['external']=='false':functions.append((int(row['entry'],16),int(row['end'],16),row['name']))
    functions.sort();starts=[x[0] for x in functions]
    text=capture['whole_live_text'];code=(directory/text['file']).read_bytes()
    require(len(code)==text['size'] and digest(code)==text['live_sha256'],'Full actual code receipt mismatch')
    lab=ROOT.parent/'God2/God2-current-lab-2598.exe'
    require(digest(lab.read_bytes())=='9ff8b9c99271e2e528270ce6475f231c338a09daf463c300fe39b62f66258c4f','Exact port-only lab image required')
    pe=pefile.PE(data=lab.read_bytes());original=pe.get_data(int(text['rva'],16),len(code))
    excluded=[];allowed=set();origin=0x400000+int(text['rva'],16)
    for address,name in ((0x530a70,'keybd_event'),(0x530aa0,'mouse_event'),(0x530ad0,'PostMessageA'),(0x530b00,'PostMessageW')):
        offset=address-origin
        require(original[offset:offset+10]==bytes.fromhex('9090e819000000ffe0c3'),'Qualified input thunk source changed')
        live=code[offset:offset+10]
        require(live[:6]==bytes.fromhex('8bff558bece9') and code[offset+31]==5,'Unclassified runtime input thunk changes')
        allowed.update(range(offset,offset+10));allowed.add(offset+31)
        excluded.append({'va':hex(address),'symbol':name,'original10_hex':original[offset:offset+10].hex(),
            'live10_hex':live.hex(),'jump_target':hex((address+10+struct.unpack('<i',live[6:10])[0])&0xffffffff),
            'authority':'Runtime input API thunk change; excluded from skill-field candidate interpretation'})
    changed={i for i,(a,b) in enumerate(zip(original,code)) if a!=b}
    require(changed<=allowed,'Unqualified additional runtime code changes')
    decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True;decoder.skipdata=True
    fields=[0x42,0x46,*range(0x4c,0x66,2)]
    candidates=[];skipped=0;instructions=0
    for instruction in decoder.disasm(code,0x400000+int(text['rva'],16)):
        if not instruction.id:skipped+=instruction.size;continue
        if 0x530a70<=instruction.address<0x530b40:continue
        instructions+=1;matches=[]
        for operand in instruction.operands:
            if operand.type!=X86_OP_MEM or not operand.access&CS_AC_READ or operand.mem.base==X86_REG_ESP:continue
            for field in fields:
                if operand.mem.disp<=field and operand.mem.disp+operand.size>field:
                    matches.append({'possible_field_offset':hex(field),'operand_width':operand.size,
                        'base':instruction.reg_name(operand.mem.base),'index':instruction.reg_name(operand.mem.index),
                        'scale':operand.mem.scale,'displacement':operand.mem.disp})
        if not matches:continue
        index=bisect_right(starts,instruction.address)-1
        function=functions[index] if index>=0 and instruction.address<=functions[index][1] else None
        candidates.append({'va':hex(instruction.address),'rva':hex(instruction.address-0x400000),
            'instruction':instruction.mnemonic+' '+instruction.op_str,'bytes':instruction.bytes.hex(),
            'function_entry':hex(function[0]) if function else None,'possible_fields':matches,
            'authority':'ACTUAL_CODE_OFFSET_CANDIDATE; STRUCTURE_ALIAS_AND_CONTROL_FLOW_NOT_QUALIFIED'})
    result={'memory_receipt':str(receipt.relative_to(ROOT)),'memory_receipt_sha256':digest(raw),
        'actual_source_coverage':capture['coverage'],'whole_live_text':text,
        'formal_database_read_only_verification':{'npc':4043,'enemy_display':7815,'skill':448,'writes':0},
        'skill_banks':dict(sorted(Counter(row['kind'] for row in skills).items())),
        'mp_threshold_distribution':dict(sorted(Counter(row['mp_threshold_word'] for row in skills).items())),
        'unclassified_word46_distribution':dict(sorted(Counter(row['unclassified_word46'] for row in skills).items())),
        'linear_decode':{'instructions':instructions,'skipped_bytes':skipped,'candidate_instructions':len(candidates)},
        'runtime_text_difference_qualification':{'port_only_lab_reference':str(lab),'changed_bytes':len(changed),'excluded_input_api_thunks':excluded},
        'candidates':candidates,'authoritative_original_server_formulas_recovered':0,
        'limits':['Linear decode includes possible data and does not prove all functions are reachable.',
            'Offset equality does not prove a skill-record alias; source fields are not named damage coefficients.',
            'Full current-scene pools are not all scenes. Empty pools and zero caches are not original zero stats.',
            'Received amount/result application and animation are not attack/defense/hit/critical generation.']}
    return result
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.capture.resolve());args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('actual_source_coverage','formal_database_read_only_verification','linear_decode','authoritative_original_server_formulas_recovered')},indent=2))
if __name__=='__main__':main()
