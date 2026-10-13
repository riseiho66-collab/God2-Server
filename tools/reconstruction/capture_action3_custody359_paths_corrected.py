from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;R=Path('C:/Users/risei/Desktop/God2/God2-Server');P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def js(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=Cs(CS_ARCH_X86,CS_MODE_32)
def at(va,size):
 off=pe.get_offset_from_rva(va-base);return raw[off:off+size]
cuts=[]
for path,va,size,kind in [('qualified/54c510-full-code.bin',0x54c510,1699,'complete_code'),('child-qualified/556d40-full-code.bin',0x556d40,1713,'complete_code'),('child-qualified/55e2f0-full-code.bin',0x55e2f0,70,'complete_code'),('delta-partial/5634e0-entry-prefix.bin',0x5634e0,664,'partial_code'),('qualified/actual-551f91-parent-lineage.bin',0x551f91,239,'partial_parent'),('qualified/actual-55202d-caller.bin',0x55202d,83,'overlapping_parent'),('qualified/54c510-target-table.bin',0x54cbb4,32,'data'),('qualified/54c510-selector-table.bin',0x54cbd4,23,'data'),('child-qualified/556d40-target-table.bin',0x5573f4,56,'data'),('child-qualified/556d40-selector-table.bin',0x55742c,23,'data'),('child-qualified/556d40-nested-target-table.bin',0x557444,20,'data'),('child-qualified/556d40-nested-selector-table.bin',0x557458,21,'data'),('child-qualified/54c510-padding.bin',0x54cbb3,1,'padding'),('child-qualified/556d40-padding.bin',0x5573f1,3,'padding')]:
 b=(D/path).read_bytes();assert len(b)==size and b==at(va,size);ins=list(md.disasm(b,va)) if 'code' in kind or 'parent' in kind else []
 if ins:assert sum(i.size for i in ins)==size
 cuts.append({'path':path,'va':f'{va:08X}','bytes':size,'sha256':sha(b),'file_offset':pe.get_offset_from_rva(va-base),'kind':kind,'sites':len(ins)})
M=R/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-selection-source-01/agents/cn-battle-subject-skill-frontier/originals/functions.tsv';mb=M.read_bytes();rows=[]
for address in [b'0054c510',b'00556d40',b'0055e2f0',b'005634e0']:
 row=next(l for l in mb.splitlines(keepends=True) if l.startswith(address+b'\t'));rows.append({'entry':address.decode(),'byte_offset':mb.index(row),'raw_line_hex':row.hex()})
put('custody/authentic-method-rows.raw',b''.join(bytes.fromhex(v['raw_line_hex']) for v in rows))
old=R/'artifacts/integration/packet-connections-20261006/cn-battle-deferred-consumer-01/native/00551d50-cfg.asm';ob=old.read_bytes();parent=next(v for v in cuts if v['kind']=='partial_parent');ins=list(md.disasm(at(0x551f91,239),0x551f91));needed=[]
for i in ins:
 line=next(l for l in ob.splitlines(keepends=True) if l.startswith(f'{i.address:08x} {i.bytes.hex()}'.encode()));needed.append(line)
put('custody/prior-exact-parent-asm.raw',b''.join(needed))
references=[]
for f in ['src/protocol/ShunyingSanshazhanReply.h','src/protocol/ThousandBullsReply.h','src/game/ShunyingSanshazhan.h','src/game/ThousandBulls.h','src/cn/protocol/CnBattleDeferredRecord.h','src/cn/protocol/CnBattleSkillDefinition.h','src/cn/assets/CnNativeSkillCatalog.h']:
 b=(R/f).read_bytes();put('source/'+f,b);references.append({'path':str(R/f),'bytes':len(b),'sha256':sha(b)})
js('custody/final-source-proof.json',{'image':{'path':str(P),'bytes':len(raw),'sha256':PIN,'base':f'{base:08X}','full_copy':False,'independent_mapped_memory_proof':False},'sections':[{'name':s.Name.rstrip(b'\0').decode(errors='replace'),'va':f'{base+s.VirtualAddress:08X}','raw_offset':s.PointerToRawData,'raw_bytes':s.SizeOfRawData,'virtual_bytes':s.Misc_VirtualSize,'characteristics':f'{s.Characteristics:08X}'} for s in pe.sections],'cuts':cuts,'authentic_metadata':{'path':str(M),'bytes':len(mb),'sha256':sha(mb),'rows':rows,'size_column_not_contiguous_extent':True},'prior_caller':{'path':str(old),'bytes':len(ob),'sha256':sha(ob),'exact_selected_instruction_bytes_equal':True,'whole_entry':'00551D50'},'source_references':references,'complete_code_bytes':sum(v['bytes'] for v in cuts if v['kind']=='complete_code'),'complete_code_sites':sum(v['sites'] for v in cuts if v['kind']=='complete_code'),'partial_code_bytes':664,'partial_parent_union_bytes':239,'data_bytes':175,'padding_bytes':4,'all_known_method_credits':0,'limits':'5634E0 actualtype3 path outside retained664 prefix: signedHP/clamp/render outcome unclosed; no native formula/rights/adoption/fullroute'})
assert sha(P.read_bytes())==PIN
js('capture-complete.json',{'status':'successful_once','complete_bodies':3,'complete_code_bytes':3482,'complete_sites':1044,'partial_code_bytes':664,'partial_code_sites':199,'parent_union_bytes':239,'parent_union_sites':parent['sites'],'overlapping_caller_bytes':83,'data_bytes':175,'padding_bytes':4,'native_method_credits':0,'route_credits':0})
print(json.dumps({'complete_code_bytes':3482,'complete_sites':1044,'partial_code_bytes':664,'parent_union_bytes':239,'parent_sites':parent['sites'],'data_bytes':175,'padding_bytes':4}))
