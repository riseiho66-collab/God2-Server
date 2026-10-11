"""196 native roster/skill event history distinction; file/static only."""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
ROUND=BASE/'cn-native-learned-skill-event-frontier-01'
OUT=ROUND/'agents/cn-learned-event-history-frontier'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='953264e0a7624fbdc615fcd8c9d964460fd4287c2c505f4275c1d4b26cbb2c4d'
OWN='tools/reconstruction/cn_learned_event_history_frontier196.py'
STABLE=[OWN,'src/cn/protocol/CnSubjectDeclaration30.h','src/cn/protocol/CnWorldSubjectSkillUpdate.h',
 'src/cn/protocol/CnBattleSkillUpdate87.h','src/cn/world/CnPrebornSubjectState.h','src/cn/world/CnPrebornSubjectState.cpp',
 'src/cn/world/CnBattleSkillSelectionSource.h','src/cn/world/CnBattleSkillSelectionSource.cpp',
 'tools/reconstruction/cn_subject_roster_publication_source_delivery.py',
 'tools/reconstruction/cn_preborn_selected_subject_source_delivery.py',
 'tools/reconstruction/cn_battle_skill_list_frontier193.py',
 'tools/reconstruction/cn_battle_skill_history_frontier194.py',
 'tools/reconstruction/cn_native_battle_learned_frontier195.py']
GUIDELINES=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
ADDRESSES=['004d4e00','005542e0','004d5e60','004d5cc0','00554750','00554980','005549f0','00554a20','004d6040','00553bc0','004d5b20','004d5b83']
SPANS=[(0x4d5b20,92,'retained_roster_entry_data','Actual signedBYTE absolute identity/count<16/staged inactive WORD before compressed switch; no name-copy/resource or UI callee followed.'),
 (0x4d5bb1,65,'retained_roster_reset_scan','Only inline-name branch reaches body+11 flag==1; actualcount/stride3EC and signedWORD match branch to4D5C46; names/resource interiors not decoded here.'),
 (0x4d5c46,16,'retained_roster_reset_return','Only row+1F0 countBYTE zero plus original epilogue/ret4; not pointer-storage erasure or cast/learned authority.'),
 (0x4d5e60,479,'retained193_complete','WORLD34 row actualpointer append flags0; original already captured full consumer, calls not followed.'),
 (0x4d5cc0,411,'retained193_complete','WORLD35 exactpointer match sets flag3, without assuming battle list mutation; calls not followed.'),
 (0x554750,558,'retained193_complete','Independent S87 activeprimary/secondary WORD/pointer/count history; group row5C/60 auxiliary state distinct from world1F0/258.')]
OLDROSTER=BASE/'cn-subject-roster-publication-source-01'
RECEIPTS=[OLDROSTER/'native/004D5B20-expanded.bin',OLDROSTER/'native/004D5B20-expanded-cfg.asm',
 OLDROSTER/'native/004D5B20-expanded-cfg.json',OLDROSTER/'native/roster-declaration-and-publication-relations.json']

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Preserve original epoch '+name)
  return
 with p.open('xb') as f:f.write(b)
def dump(name,v):put(name,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def original(p,name):
 b=p.read_bytes();put(name,b)
 return {'path':str(p.resolve()),'copy':name,'bytes':len(b),'sha256':sha(b)}
def facts(final=False):
 return {'round':196,'BATCHFINAL_received':final,'owned_cpp_new':0,'owned_cpp_modified':0,
  'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
  'retained_bounded_native_spans':6,'retained_bounded_native_bytes':1621,
  'native_original_input_count':15,'retained_event_relations':[
   {'key':'declaration30_reset_existing_count_only','scope':'WORLD30 actual4D5B20 existing expanded source: absolute signedBYTE ID>=100 plus inline branch/body+0x11==1; count<16 precedes staged inactive row write; scan same original rowWORD at I+D8+n*3EC then row+1F0 countBYTE=0/earlyret4. Pointer/flag physical storage is not zeroed by this branch. Native name-copy completion precedes scan; malformed overread not emulated.','rawsites':['004d5b2b','004d5b33','004d5b49','004d5b66','004d5bb1','004d5bbf','004d5be0','004d5be5','004d5c48','004d5c53']},
   {'key':'world34_and35_original_row_history','scope':'Retained WORLD34 appends bank-derived pointer row+258/countBYTE+1F0/flagBYTE+1F1+n=0; WORLD35 compares exact pointer and writes flag3. Equal key/formula and local flag do not identify common actor or server skill ownership.'},
   {'key':'battle87_independent_list_history','scope':'Retained actual deferred5523F6→554750 writes activeprimary component+10/count, WORD14, pointerDC or selectedsecondary +2D14+selector54 WORD/pointer/count50; primary auxiliary lookup uses actualrow+5C/count and +60 pointers. Those rowfields differ from WORLDskillcount+1F0/pointers+258 and must not be silently unified.'},
   {'key':'initializer_current_and_storage_distinction','scope':'Retained553BC0 bank3518, group2D4 suppliedrow+D8+n3EC, selectorCF/countD4 and group reset/bit15 state. No recovered nongui copy from WORLD1F0/258 into activebattlelist; qualified learned materializer remains OPEN. Callee effects not globally excluded.'}],
  'source_action':'Existing CnSubjectDeclaration30::native_effect and original roster publisher already preserve this exact reset event. Existing fullrow/native selection sources retain separate row/bank/list projections. No duplicate reader or gameplay edits added; require actual ordered common issuer plus immutable native/current history.',
  'bounded_candidate_outcomes':[
   {'address':'004D4E00','outcome':'Already older selected-subject full196B CFG; selectedrow/page-data with UI calls, not new learned materializer.'},
   {'address':'005542E0','outcome':'Canonical read during metadata locating, recognized GUI refresh and stopped; no disassembly/callee follow/new count.'},
   {'address':'00554980','outcome':'Top-level page-index change then GUI5545C0 call; stopped at callsite; no raw recovery counted.'},
   {'address':'005549F0','outcome':'Different vtable/deleting destructor; not list event source, no follow or native raw count.'},
   {'address':'00554A20','outcome':'Handle query for different object+6; not selected skill source, no follow or native raw count.'},
   {'address':'004D6040','outcome':'Selectedrow unrelated DWORD/WORD stats then GUI calls; source locating only, no follow or native raw count.'}],
  'learned_permission_qualified':False,'actual_common_learned_issuer_recovered':False,
  'scope_limits':['This is a concrete retained event-history reconciliation, not new opcode/phase/server producer recovery or a global absence proof.',
   'H20=U only sameP/call/epoch; battle mode1 does not execute mode0 4D2D30 attachment. Same native origin never supplies common64 identity/learned/cast grant.',
   'Only selected old193-195 manifests plus actual older roster/selected-source full evidence compared; no global scan or fullgame denominator claim.',
   'World30 duplicate-reset modifies only skill count for matching active row but stages inactive slot before search. Preserve actual order, native branch bounds, original row and physical pointer history.',
   'No original server learned/grant/battle/actor/incarnation/MP/cost/range/items/save/replay/settlement/native replies/Main supplier recovered.'],
  'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,'receiver_contexts':14,'qualified_receiver_contexts':12,
  'unresolved_helpers':[{'va':x,'phase':None,'slot':None,'producer':None} for x in ['0047DE70','004812B0']],
  'whole_game_route_denominator':None,'whole_game_percentage':None,
  'build_test_runtime_native_codec_api_db_deploy':False}
def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable')
 fresh=(ROUND/'before-manifest.json').read_bytes()
 if len(json.loads(fresh))!=1403 or sha(fresh)!=BEFORE:raise RuntimeError('Freshbefore differs')
 before={q['path']:q for q in json.loads(fresh)};old=[]
 for n,rel in enumerate(STABLE[1:]+GUIDELINES):
  q=before[rel];b=(ROUND/q['snapshot']).read_bytes()
  if sha(b)!=q['sha256'] or len(b)!=q['bytes']:raise RuntimeError('Full before differs')
  name=f'before/b{n:02d}'+Path(rel).suffix;put(name,b);old.append({'path':str((ROOT/rel).resolve()),'copy':name,'bytes':len(b),'sha256':sha(b),'epoch':'freshbefore1403'})
 dump('before-source-origins.json',old);dump('before-owned-absence.json',[{'path':str((ROOT/OWN).resolve()),'absent_in_freshbefore':OWN not in before}])
 raw=EXE.read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Original pinned PE differs')
 meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes();rows={q['address']:q for q in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RECOVERY/'calls.tsv','originals/calls.tsv')];sites=[]
 for n,address in enumerate(ADDRESSES):
  p=RECOVERY/rows[address]['file'];q=original(p,f'originals/p{n:02d}.c');inputs.append(q)
  for line,t in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(x in t.lower() for x in ['0x1f0','0x1f1','0x258','+ 300','+ 0x5c','+ 0x60','0x2d4','0x3518','0x11','0x7fff','00554750','0x4000','0x3ec']):sites.append({'path':q['path'],'line':line,'text':t,'original_sha256':q['sha256'],'classification':'retained source event qualification, not new raw evidence'})
 dump('native-original-inputs.json',inputs);dump('primary-source-sites.json',sites)
 dump('bounded-call-rows.json',[q for q in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if q['target'] in ['004d5b20','004d4e00','004d5e60','004d5cc0','00554750','00553bc0']])
 receipts=[]
 for p in RECEIPTS:receipts.append(original(p,f'prior-receipts/r{len(receipts):02d}'+p.suffix))
 comparisons=[]
 for name in ['cn-native-battle-skill-selection-source-01','cn-native-battle-skill-publication-source-01','cn-native-learned-skill-owner-frontier-01']:
  paths=list((BASE/name/'agents').glob('*/native*spans.json'))+list((BASE/name/'agents').glob('*/original-inputs.json'))
  for p in sorted(paths):
   q=original(p,f'prior-receipts/r{len(receipts):02d}'+p.suffix);receipts.append(q)
   comparisons.append({'path':q['path'],'copy':q['copy'],'layer':'selected193-195 span/input inventory only; not global newness proof'})
 dump('prior-receipt-origins.json',receipts);dump('prior-layer-comparison.json',comparisons)
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];instructions=[]
 old_roster=(OLDROSTER/'native/004D5B20-expanded.bin').read_bytes()
 if old_roster!=raw[pe.get_offset_from_rva(0x4d5b20-base):pe.get_offset_from_rva(0x4d5b20-base)+0x178]:raise RuntimeError('Actual old expanded fullbytes differ')
 for n,(va,size,cl,scope) in enumerate(SPANS):
  off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];name=f'raw/s{n:02d}.bin';put(name,b)
  ins=[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':cl} for i in md.disasm(b,va)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in ins)!=size:raise RuntimeError('Bounded instruction bytes incomplete')
  dump(f'derived/s{n:02d}.json',ins);instructions.extend(ins);spans.append({'va_start':f'{va:08x}','va_end':f'{va+size:08x}','bytes':size,'file_offset':off,'copy':name,'sha256':sha(b),'classification':cl,'scope':scope})
 dump('native-spans.json',spans);dump('instruction-sites.json',instructions)
 dump('initial-source-origins.json',[original(ROOT/OWN,'initial/tool.py')]);dump('source-ready-source-origins.json',[original(ROOT/OWN,'source-ready/tool.py')]);dump('findings-source-ready.json',facts())
 print(json.dumps({'state':'source-ready','native_inputs':len(inputs),'current_planned':len(STABLE),'new_spans':0,'new_relations':0,'retained_spans':6,'retained_bytes':1621,'instruction_sites':len(instructions),'prior_receipts':len(receipts)}))
def final(extra):
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable')
 native=json.loads((OUT/'native-original-inputs.json').read_bytes())
 for q in native:
  b=Path(q['path']).read_bytes()
  if sha(b)!=q['sha256'] or len(b)!=q['bytes'] or b!=(OUT/q['copy']).read_bytes():raise RuntimeError('Actual original drift')
 current=[original(ROOT/rel,f'current/c{n:02d}'+Path(rel).suffix) for n,rel in enumerate(STABLE)]
 context=[original(ROOT/rel,f'context-final/k{n:02d}'+Path(rel).suffix) for n,rel in enumerate(GUIDELINES+extra)]
 dump('current-source-origins.json',current);dump('final-context-source-origins.json',context);dump('original-inputs.json',native+current+context)
 dump('findings.json',facts(True));dump('gaps.json',facts()['scope_limits'])
 dump('actual-read-epochs.json',{'before1403_sha256':BEFORE,'before_stable_full':12,'before_guidelines_full':3,'owned_tool_absent':1,'initial_tool_full':1,'source_ready_tool_full':1,'actual_native_full_originals':len(native),'current_actual_source_full':len(current),'final_context_full':len(context),'prior_receipts_separate':True,'raw_spans_all_retained':True,'candidate_UI_source_locating_stopped':True,'old_tools_not_rerun':True})
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file():
   b=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b)})
 dump('LIST.json',members);b=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(b),'sha256':sha(b)})
 dump('seal.json',{'round':196,'members':members,'member_count':len(members),'member_bytes':sum(q['bytes'] for q in members),'current_source_count':len(current),'context_source_count':len(context),'native_original_input_count':len(native),'new_native_spans':0,'new_complete_routes':0})
 print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'files_with_seal':len(members)+1,'member_bytes':sum(q['bytes'] for q in members),'current':len(current),'context':len(context),'native_inputs':len(native),'original_inputs':len(native)+len(current)+len(context),'tool_sha256':sha((ROOT/OWN).read_bytes())}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['recover','final']);p.add_argument('--context',nargs='*',default=[]);a=p.parse_args();recover() if a.stage=='recover' else final(a.context)
