"""195 supplied native subject/list ownership frontier; static files only.

This writer reads complete pinned originals and bounded raw instruction spans.
It never runs native code, codecs, C++, Lua, database, APIs, builds or tests.
GUI/renderer callees remain stopped at the recorded call sites.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-owner-frontier-01'
OUT=ROUND/'agents/cn-native-learned-subject-frontier'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
RESOURCE=EXE.parent/'Data2/Fight/Spg/cbspec2.bin'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='bcff0e9bbe5e7d2d69553e55faaadb49f86e2fb8d4e912cd8811a2ed3dc34856'
OWN='tools/reconstruction/cn_native_learned_subject_frontier195.py'
STABLE=['src/cn/protocol/CnWorldSubjectSkillUpdate.h',
 'src/cn/world/CnPrebornSubjectState.h','src/cn/world/CnPrebornSubjectState.cpp',
 'src/cn/world/CnPrebornSkillReferences.h','src/cn/world/CnPrebornSkillReferences.cpp',
 'src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp',
 'src/cn/protocol/CnBattleSkillSelection.h']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/cn_battle_skill_list_frontier193.py',
 'tools/reconstruction/cn_battle_subject_skill_frontier193.py',
 'tools/reconstruction/cn_battle_command_context191.py']
PRIMARY=['004d5e60','004d5cc0','0048fcc0','0048da20','0054a320','0048e3e0',
 '004af370','004d2d30','005485f0','005486ee','00553bc0']
# Every byte below belongs to an already retained whole canonical/CFG source.
# This round qualifies address/owner relations; it recovers no new native code.
# The peer alone owns new 5537E0/553810/553B40 raw functions.
SPANS=[
 (0x4d5e60,0x4d603f,'retained_complete','WORLD34 appends exact pointer/flag0; row WORD compared to raw subject BYTE; no learned grant'),
 (0x4d5cc0,0x4d5e5b,'retained_complete','WORLD35 finds exact pointer and sets flag3; consumers/UI callees not followed'),
 (0x48da44,0x48da96,'retained_bounded','Bundle actual addresses: R=P+1478084; bundle[2] at EBP-A10 is U=P+89B26C; loaded P+A69F1C is bundle[3]'),
 (0x54a375,0x54a38f,'retained_bounded','H20=bundle[2]=actual embedded world U; H14=bundle[4]=R; H24=bundle[3] is distinct loaded context'),
 (0x48ddfd,0x48de0f,'retained_bounded','Phase4 supplies H=loadedP8885F0 and exact stack bundle to54A320'),
 (0x54a6a5,0x54a6e4,'retained_bounded','Actual H14+90 supplied to553BC0, same H bank9D223C; initializer interior owned by peer'),
 (0x48e3e8,0x48e3f1,'retained_bounded','Return-to-world caller U=LEA P+89B26C'),
 (0x48e489,0x48e4b1,'retained_bounded','Return-to-world mode0 sends same inline R=LEA P+1478084 with actual U'),
 (0x4af374,0x4af388,'retained_bounded','4AF370 stores actual supplied mode BYTE at U+77858'),
 (0x4af3eb,0x4af414,'retained_bounded','Actual mode test: nonzero jumps4AF68C; R+90 passed only to retained callsite, no renderer interior'),
 (0x4af485,0x4af49b,'retained_bounded','Mode0 invokes4D2D30 with actual R+90 and actual U'),
 (0x4d2d40,0x4d2d5a,'retained_bounded','Actual argument stored at U+430A8'),
 (0x4af68c,0x4af6d5,'retained_bounded','Bounded nonzero-mode branch never invokes4D2D30; no general/global negative proof'),
 (0x54a7af,0x54a7c9,'retained_bounded','Battle initializer invokes4AF370(bundle4,1) through actual H20=U, distinct mode from world mode0'),
 (0x491388,0x4913b0,'retained_bounded','WORLD34/35 selected consumers ECX=LEA P+89B26C and body+1'),
 (0x548770,0x54878d,'retained_bounded','Battle receiver34/35 consumers ECX=storedH20=actual U under same P/epoch; no common identity inferred'),
]
STACK_LEDGER={
 'base':'Exact pointer LEA EAX,[EBP-0xA18] at48DE03, pushed48DE09 and passed54A320 at48DE0A; calleeEDX=argumentEBP8 at54A326',
 'same_owner_qualification':'P is actual world owner, H=actual loaded P8885F0. Origins apply only to this same call/epoch; no common actor identity or grant follows.',
 'slots':[
  {'slot':0,'stack':'EBP-A18','source':'loaded [P+8885C4]','writes':['48DA56','48DA5C'],'callee':'54A32D loads bundle0;54A335 storesH0'},
  {'slot':1,'stack':'EBP-A14','source':'LEA EBP-9F0 actual T input','writes':['48DA36','48DA3C'],'callee':'retained context input, not actor'},
  {'slot':2,'stack':'EBP-A10','source':'LEA P+89B26C actual U','writes':['48DA4A','48DA8A'],'callee':'54A375 MOV EAX,[EDX+8];54A378 MOV[H+20],EAX'},
  {'slot':3,'stack':'EBP-A0C','source':'loaded [P+A69F1C], distinct context','writes':['48DA44','48DA50'],'callee':'54A37B MOV EAX,[EDX+C];54A37E MOV[H+24],EAX'},
  {'slot':4,'stack':'EBP-A08','source':'LEA P+1478084 actual inline R, not dereferenced R0','writes':['48DA62','48DA68'],'callee':'54A381 MOV EAX,[EDX+10];54A384 MOV[H+14],EAX'},
  {'slot':5,'stack':'EBP-A04','source':'loaded [P+A69F20]','writes':['48DA6E','48DA74'],'callee':'not copied to H20'},
  {'slot':6,'stack':'EBP-A00','source':'LEA P+1464C58','writes':['48DA7A','48DA90'],'callee':'54A387/38F copy toH2C'},
 ],
 'correction':'Initial source-ready incorrectly mapped EBP-A0C to slot2; arithmetic relative to EBP-A18 makes it slot3. Complete earlier tool/field/findings retained in correction-before; raw spans and counts unchanged.',
 'raw_copies':['raw/s02.bin','raw/s03.bin','raw/s04.bin'],
}

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Preserve earlier epoch: '+name)
  return
 with p.open('xb') as f:f.write(b)
def emit(name,obj):put(name,(json.dumps(obj,ensure_ascii=True,indent=2)+'\n').encode('utf-8'))
def original(p,target):
 b=p.read_bytes();put(target,b)
 return {'path':p.resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)}

def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Already immutable')
 fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(before)!=1398 or sha(fresh)!=BEFORE:raise RuntimeError('Freshbefore changed')
 put('epoch/root-before.raw',fresh);emit('epoch.json',{'round':195,'before_inputs':1398,'before_sha256':BEFORE,'baseline_replaced':False})
 idx={r['path']:r for r in before};old=[]
 for n,f in enumerate(STABLE+CONTEXT):
  r=idx[f];b=(ROUND/r['snapshot']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('Actual complete before differs')
  target=f'before/b{n:02}{Path(f).suffix}';put(target,b)
  old.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)})
 if OWN in idx:raise RuntimeError('New tool was present inbefore')
 emit('before-source-origins.json',old)
 emit('before-owned-absence.json',[{'path':(ROOT/OWN).resolve().as_posix(),'present':False}])
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN:raise RuntimeError('Actual pinned original differs')
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),
  original(RECOVERY/'calls.tsv','originals/calls.tsv'),original(RESOURCE,'originals/cbspec2.bin')]
 primary=[]
 for n,a in enumerate(PRIMARY):
  p=RECOVERY/rows[a]['file'];r=original(p,f'originals/p{n:02}.c');inputs.append(r)
  for line,t in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(v in t.lower() for v in ['430a8','4474','1478084','89b26c','a69f1c','0x1f1','0x1f0','0x3ec','00553bc0','004d5e60','004d5cc0','004d2d30','004af370','param_1[5] =','param_1[8] =']):
    primary.append({'path':r['path'],'line':line,'text':t,'sha256':r['sha256'],'scope':'retained full original; selected raw branch proof separate'})
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]])
 emit('primary-source-sites.json',primary)
 emit('selected-call-rows.json',[r for r in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if r['target'] in ['004af370','004d5e60','004d5cc0','004d2d30']])
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 emit('initial-source-origins.json',[original(ROOT/OWN,'initial/tool.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];classes={}
 for n,(lo,hi,cl,purpose) in enumerate(SPANS):
  off=pe.get_offset_from_rva(lo-base);b=raw[off:off+hi-lo];target=f'raw/s{n:02}.bin';put(target,b)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':cl} for i in md.disasm(b,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(b):raise RuntimeError('Bounded instruction end differs')
  emit(f'derived/s{n:02}.json',decoded);sites.extend(decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':off,'copy':target,'bytes':len(b),'sha256':sha(b),'classification':cl,'purpose':purpose,'instruction_count':len(decoded)})
  c=classes.setdefault(cl,{'spans':0,'bytes':0});c['spans']+=1;c['bytes']+=len(b)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 emit('field-relations.json',[
  {'key':'actual_inline_role_identity','native_sites':['48DA62','48DA68','54A381','54A384','54A6BA','54A6BD'],'relation':'same actual P gives R=P+1478084; exactbundle4 holds address, H14=R; initializer receives R90. Not dereference of role DWORD at R0.'},
  {'key':'world_mode0_attachment','native_sites':['48E3EB','48E48F','48E4AC','4AF40C','4AF40E','4AF493','4AF496','4D2D54'],'relation':'World caller U=P+89B26C, R=P+1478084; actual mode0 binds U430A8=R90. Same P and unchanged owner epoch are mandatory; mode1 does not execute this attachment branch.'},
  {'key':'world_skill_list','native_sites':['49138C','4913A0','4D5E60','4D5CC0'],'relation':'WORLD34/35 rawsubjectBYTE matches rowWORD, I=U430A8; I+D4 count/rowsD8 stride3EC, row1F0 count/1F1flags/258fullpointers. Pointer resolves same supplied bank4474. Appendedflag0/changedflag3 are local data, not learned/cast grant.'},
  {'key':'battle_caller_same_ui_different_mode','native_sites':['48DA4A','48DA8A','48DE03','48DE0A','54A375','54A378','54A7B7','54A7C1','54A7C4','548770','548777','548781','548788'],'relation':'Bundle base EBP-A18: slot2=EBP-A10 is LEA P+89B26C stored48DA8A; H20=slot2 via54A375/378. Loaded *P+A69F1C is slot3=EBP-A0C copied toH24. Battle init invokes4AF370(R,1); battle34/35 receiver forwards through actual H20=U, subject to same P/epoch and current lifecycle qualification.'},
  {'key':'phase2_35_continuation','native_sites':['548788','54878D'],'relation':'Original canonical5485F0 case35 falls throughD1 and4C9530 after4D5CC0; selected retained callsite ends54878D. Fullcanonical preserved; continuation callee not followed or declared complete.'},
 ])
 emit('stack-ledger.json',STACK_LEDGER)
 source=[]
 for f in STABLE:
  b=(ROOT/f).read_bytes()
  for line,t in enumerate(b.decode('utf-8-sig').splitlines(),1):
   if any(v in t for v in ['current','actual_','retained_','source_offset','record_bytes','raw','permission','0x258','0x1f1','0x430a8','0x3518']):
    source.append({'path':(ROOT/f).resolve().as_posix(),'line':line,'text':t,'sha256':sha(b)})
 emit('cpp-source-sites.json',source)
 facts={'round':195,'phase':'file/static only','new_cpp':0,'modified_cpp':0,'new_tools':1,
  'native_spans':len(spans),'native_bytes':sum(r['bytes'] for r in spans),'native_span_counts':classes,
  'new_native_spans':0,'new_native_opcodes':0,'instruction_sites':len(sites),'primary_sites':len(primary),'cpp_source_sites':len(source),
  'original_inputs':len(inputs),'original_bytes':sum(r['bytes'] for r in inputs),'current_originals_planned':len(STABLE)+1,
  'complete_gameplay_routes':0,'whole_game_percent':None,'build_test_runtime_native_codec_api_db_sql_deploy':0,
  'source_qualification_actions':['Reuse CnPrebornSubjectState/SkillReferences for actual complete selected row pointers and rawflags. Exact native P/R/H/U owner, fullrow/fullbank/current is required; common learned history cannot be derived from samekind/id or flags0/3.',
   'Optional battle source may qualify H14/R90 against the retained subject snapshot only with actual sameP/R and owner epoch. Preserve exact H20=U native origin under same P/epoch, mode1 lack of4D2D30 and actual current qualification; no invented row/list materializer.',
   'Peer owns separate117B nongui getter recovery and true553BC0 row/group frontier; this tool never counts that recovery or follows GUI constructor/consumer interiors.'],
  'limits':['Every captured native byte is retained whole original/CFG coverage; these selected ownership relations are not new nativefunction/opcode/gameplay recovery.',
   'WORLD subjectBYTE, rowWORD, actual native addresses and common64 actor identity are separate. Preserve original widths; no cast/name/key-only join.',
   'Battle receiver34/35 uses actual H20=U native origin under same P/epoch and phase2 case35 additional continuation. No globalphase equality, whole dispatcher completion or serverproducer inferred.',
   'Actual common learned skill issuer, ownership, complete grant86/87 history, MP/cost/collision/range/save/replay/settlement/current remain OPEN.',
   'Initial locating windows48E470/54A7A0/4AF460 started inside instructions; not evidence. Final recorded spans start independently aligned original sites.',
   'No GUI/render/formatter155/capacity/glyph/52F330/52F170 callee interiors followed; no runtime/native/tests/API/DB/SQL.']}
 emit('findings-source-ready.json',facts);emit('findings.json',facts)
 emit('gaps.json',[{'gap':'Actual learned common subject/list owner','next':'Supply actual common authority/history backed same immutable full native row/bank and exact nativeP/R/H/U epoch, before/after callbacks; flags0/3/pointer equality alone insufficient.'},
  {'gap':'Battle list materialization','next':'Peer separately preserves nongui row/group/getter frontier. GUI constructors/consumers are not a recovered materializer; no guessed count/list or default grant.'},
  {'gap':'Same H20/worldU current lifecycle','next':'Native origin equality is proved by exact bundle slots under same P, but actual epoch/attachment/live row must still be qualified; same consumer/opcode alone never establishes common learned identity.'}])
 put('README.md',b'# CN learned subject ownership frontier195\n\nFile/static only. Full pinned originals and retained selected native sites qualify actual inline role R, world mode0 attachment and same native UI origin with distinct battle mode1 consumer context. Same pointer or local flags never establish learned/cast authority. No CPP changes, new native spans0, routes0, percentnull. Current stable originals exclude Root/peer mutable source; original/derived/before/context epochs separate. Seal after Root BATCHFINAL.\n')
 derived=[]
 for folder in ['raw','derived']:
  for p in sorted((OUT/folder).rglob('*')):
   if p.is_file():
    b=p.read_bytes();derived.append({'path':p.resolve().as_posix(),'copy':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'kind':'bounded raw subset/static disassembly; not full original'})
 emit('derived-inputs.json',derived)
 print(json.dumps(facts))

def capture(seal):
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(STABLE+[OWN])]
 emit('current-source-origins.json',current)
 if seal:
  members=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.name!='seal.json':
    b=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b)})
  emit('seal.json',{'round':195,'members':members,'member_count':len(members),'current_originals':len(current),'new_native_spans':0,'complete_gameplay_routes':0,'whole_game_percent':None})
  print(json.dumps({'members':len(members),'files_with_seal':len(members)+1,'seal_sha256':sha((OUT/'seal.json').read_bytes()),'current_originals':len(current),'current_bytes':sum(r['bytes'] for r in current)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--capture',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args()
 if a.recover:recover()
 if a.capture:capture(a.seal)
