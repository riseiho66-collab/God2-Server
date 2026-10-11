"""194 bounded CN list-selection/reset history; source/PE/files only."""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-publication-source-01'
OUT=ROUND/'agents/cn-battle-skill-history-frontier'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='b4a2a26c57b6c061ae43da94ef2ac629f462bab42e66bcb7b0d6e0b9fc7e55b8'
OWN='tools/reconstruction/cn_battle_skill_history_frontier194.py'
STABLE=[OWN,'src/cn/protocol/CnBattleCommandGate.h',
 'src/cn/protocol/CnBattleScalarUpdate.h','src/cn/world/CnBattleSkillSelectionSource.h',
 'src/cn/world/CnBattleSkillSelectionSource.cpp','tools/reconstruction/cn_battle_skill_list_frontier193.py',
 'tools/reconstruction/cn_battle_deferred_consumer_delivery.py','tools/reconstruction/cn_battle_command_context191.py']
GUIDELINES=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
GUI=['00552870','00553220','00552cb0','005540b0','005545c0']
ADDRESSES=GUI+['00554200','00553fa0','00553f30','0054cff0','005486ee','00552005','0054cd80','004d4e00']
SPANS=[
 (0x54cff0,49,'new_complete_wrapper','Actual receiver H+0xA89658 uses original record+1; signed AX nonnegative result passes to actual H+0x20 component. No actual incoming phase/route bound.'),
 (0x554200,216,'retained193_complete','Already193 whole selector/status writer; no new helper count or permission.'),
 (0x553fa0,92,'retained193_complete','Already193 bit15/auxiliary/status clearing; counts/old pointers are not reset here.'),
 (0x553f30,28,'retained193_complete','Already193 selected secondary count reset, other bytes/pointers remain.'),
 (0x55240d,44,'retained_old_deferred_case','Old full551D50 envelope S38: exact saved logical body byte atH+A97181, list ECXH+A89658; subject component H+0x20 on nonnegative AX.'),
 (0x5487bf,40,'retained_old_receive_case','Old full5485F0 envelope3B: actual packet+2==0x2C triggers savedBE8D95BYTE and selected secondary count reset.'),
 (0x5487ec,18,'retained_old_receive_case','Old full5485F0 envelope3C: packet+3==0x2C condition reuses exact prior reset branch. No general inventory/learned invalidation claimed.')]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(rel,raw):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=raw:raise RuntimeError('Preserve original epoch: '+rel)
  return
 with p.open('xb') as f:f.write(raw)
def dump(rel,obj):put(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def original(p,copy):
 raw=p.read_bytes();put(copy,raw)
 return {'path':str(p.resolve()),'copy':copy,'bytes':len(raw),'sha256':sha(raw)}
def facts(final=False):
 return {'round':194,'BATCHFINAL_received':final,'owned_cpp_new':0,'owned_cpp_modified':0,
  'new_bounded_native_spans':1,'new_bounded_native_bytes':49,
  'new_native_relations':[{'key':'exact_receiver_list_to_subject_selector_wrapper',
   'scope':'54CFF0 saves actual ECX H; record+1 to actual H+A89658→554200; result AX interpreted signed, nonnegative only →4D4E00 at actual H+20 subjectcomponent. This actual wrapper has no qualified incoming caller/phase in this delivery, and cannot substitute for the true deferred S38 or S87 dispatcher.',
   'rawsites':['0054cff3','0054cff7','0054cff9','0054cffa','0054cffb','0054d001','0054d006','0054d009','0054d00c','0054d00e','0054d012']}],
  'retained_bounded_native_spans':6,'retained_bounded_native_bytes':438,
  'native_original_input_count':16,'gui_full_canonical_source_inputs':5,'gui_interior_disassembled':False,
  'retained_relations':[
   '554200 source BYTE low5 slot/high3 status with boundactualcount; priorstatus2 and newstatusnot2 only clearsbit15/auxiliary; equal rowWORD identity can changeprimary selector. This is local history, not common actor identity.',
   '553F30 only selectedsecondary count clears; 553FA0 clearsbit15/auxiliary/status for16primarygroups whilecount/pointers persist. Source history/current cannot infer cleared pointer storage or remove retained physical arrival history.',
   'Old55240D exactS38 deferred case calls554200 then4D4E00. Old3B/3C case payloadspecificBYTE2C clearsselectedsecondary count. No newly counted opcodes or per-record accepted grant inferred.',
   'S86/5 actual54CD80 canonicalsource setsprimary/secondary flags andactornibbles only whenrequestbits present; absentbits keeppriorstate. Actual duration/start derivesprior state; displayWORD is not duration/grant.',
   'S87 realdeferredcase5523F6..552408 directly calls554750 withactualcomponentH+A89658 andpayloadH+A97181; nativepeer owns exactindependentproof.54DEF0 wrapper is NOT that actualcase.'],
  'producer_source_classification':{
   'existing_CnBattleDeferredRecord':'Owns retained exactS87logical3 andS86logical17, queue grammar/readonlyaccessors; not a server battle event owner or a real learned/grant publisher.',
   'existing_CnBattleCommandGate':'Raw original86/5 logical17 projection and prior-clock arithmetic; absentbits do not invalidate all prior flag state. No new defaultclock/86grant/rule inferred.',
   'existing_CnBattleSkillSelectionSource':'Supplied original list/index/flag/bank projection plusfullrecord provenance/current; not server learned entitlement, native grant history or actualcommon mutation.',
   'actual_server_issuer':'Required actual common battle/actor/incarnation/context/learnedskills/fullhistory source is OPEN; an optional post-commit publisher adapter is not that supplier.'},
  'source_qualification_actions':[
   'Use actual complete issuer event/order/nativefullhistory with exact native receiver, original registration/fullcommon root, actor/phase/current source. Do not convert one86/5 or rowflags into eligibility.',
   'Retain exact physical S87 WORD order/duplicates and original list selector/count/pointer epoch; no UIconstructor or refresh serves as learned-row materialization.',
   'Rootinitial requestedS87→54DEF0 chain is retained as historical scope, corrected byactualdeferred5523F6→554750 proof. Originalpriorseals are never rewritten.'],
  'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
  'receiver_contexts':14,'qualified_receiver_contexts':12,
  'unresolved_helpers':[{'va':x,'phase':None,'slot':None,'producer':None} for x in ['0047DE70','004812B0']],
  'whole_game_route_denominator':None,'whole_game_percentage':None,
  'gaps':['Actual learned/grant/battle/actor/common-incarnation/source-event issuer, native replies, cost/once settlement and Main integration remain OPEN.',
   'Targeted native reset/select writers are not complete alias/cancel/destruction coverage; no metadata-no-call-row implies absence/deadcode.',
   'Only bounded field/transfer facts are claimed; exact same bank or equal rowWORD never identifies a sharedsubject/common64 root.',
   'GUI5 preserved fullcanonicalC for source distinction only; no render/font/glyph/formatter/capacity/155 or52F330/52F170 callee followed.',
   'Initial5487B0 locating bytes began within prior instruction; authoritative retained case starts5487BF. Only5487EC..5487FE is the exactsecondcase.'],
  'build_test_runtime_native_codec_api_db_deploy':False}
def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
 rawbefore=(ROUND/'before-manifest.json').read_bytes()
 if sha(rawbefore)!=BEFORE or len(json.loads(rawbefore))!=1390:raise RuntimeError('Freshbefore1390 differs')
 before={x['path']:x for x in json.loads(rawbefore)};old=[]
 for n,rel in enumerate(STABLE[1:]+GUIDELINES):
  q=before[rel];raw=(ROUND/q['snapshot']).read_bytes()
  if len(raw)!=q['bytes'] or sha(raw)!=q['sha256']:raise RuntimeError('Full before source differs')
  copy=f'before/b{n:02d}'+Path(rel).suffix;put(copy,raw);old.append({'path':str((ROOT/rel).resolve()),'copy':copy,'bytes':len(raw),'sha256':sha(raw),'epoch':'freshbefore1390'})
 dump('before-source-origins.json',old);dump('before-owned-absence.json',[{'path':str((ROOT/OWN).resolve()),'absent_in_freshbefore':OWN not in before}])
 dump('initial-request-correction.json',{'historical_initial_requested_chain':'S87 dispatch/54DEF0/554750 scope requested before actualcase qualification',
  'actual_corrected_source':'S87 deferred5523F6..552408 actualcomponentH+A89658/payloadH+A97181→554750 directly;54DEF0 notthatcase',
  'independent_proof_owner':'nativepeer194','prior_seals_rewritten':False})
 raw=EXE.read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Pinned actual PE differs')
 meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes()
 rows={q['address']:q for q in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RECOVERY/'calls.tsv','originals/calls.tsv')];sites=[];gui=[]
 for n,address in enumerate(ADDRESSES):
  p=RECOVERY/rows[address]['file'];q=original(p,f'originals/p{n:02d}.c');inputs.append(q)
  for line,s in enumerate((OUT/q['copy']).read_text(encoding='utf-8-sig').splitlines(),1):
   if any(k in s.lower() for k in ['0x2d','00553f30','00554200','00554750','a970f8','a970fc','0x51','0x52','0x7fff','0x2c','004d4e00','0044df50','0044e3e0','2e14']):
    sites.append({'path':str(p.resolve()),'line':line,'text':s,'original_sha256':q['sha256'],'source_only_gui':address in GUI})
  if address in GUI:gui.append({'va':address,'original':q,'scope':'CanonicalindividualGUIconstructor/refresh source distinction only; not a qualified learned materializer','native_interior_disassembled':False,'callees_followed':False})
 dump('native-original-inputs.json',inputs);dump('primary-source-sites.json',sites);dump('gui-source-distinction.json',gui)
 dump('bounded-original-call-rows.json',[q for q in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if q['target'] in ['00554200','00553fa0','00553f30','0054cff0','004d4e00']])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];ins=[]
 for n,(va,size,classification,scope) in enumerate(SPANS):
  off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];copy=f'raw/s{n:02d}.bin';put(copy,b)
  decoded=[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':classification} for i in md.disasm(b,va)]
  if sum(len(bytes.fromhex(q['bytes'])) for q in decoded)!=size:raise RuntimeError('Whole bounded instruction bytes incomplete')
  dump(f'derived/s{n:02d}.json',decoded);ins.extend(decoded);spans.append({'va_start':f'{va:08x}','va_end':f'{va+size:08x}','bytes':size,'file_offset':off,'copy':copy,'sha256':sha(b),'classification':classification,'scope':scope})
 dump('native-spans.json',spans);dump('instruction-sites.json',ins)
 dump('initial-source-origins.json',[original(ROOT/OWN,'initial/tool.py')]);dump('source-ready-source-origins.json',[original(ROOT/OWN,'source-ready/tool.py')])
 dump('findings-source-ready.json',facts())
 print(json.dumps({'state':'source-ready','native_inputs':len(inputs),'new_spans':1,'new_bytes':49,'new_relations':1,'retained_spans':6,'retained_bytes':438,'current_planned':len(STABLE)}))
def final(extra):
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
 inputs=json.loads((OUT/'native-original-inputs.json').read_bytes())
 for q in inputs:
  raw=Path(q['path']).read_bytes()
  if len(raw)!=q['bytes'] or sha(raw)!=q['sha256'] or (OUT/q['copy']).read_bytes()!=raw:raise RuntimeError('Actual complete original differs')
 current=[original(ROOT/rel,f'current/c{n:02d}'+Path(rel).suffix) for n,rel in enumerate(STABLE)]
 context=[original(ROOT/rel,f'context-final/k{n:02d}'+Path(rel).suffix) for n,rel in enumerate(GUIDELINES+extra)]
 dump('current-source-origins.json',current);dump('final-context-source-origins.json',context);dump('original-inputs.json',inputs+current+context)
 dump('findings.json',facts(True));dump('gaps.json',facts()['gaps'])
 dump('actual-read-epochs.json',{'freshbefore1390_sha256':BEFORE,'before_stable_full':8,'before_guidelines_full':3,'owned_tool_absent':1,
  'initial_tool_full':1,'source_ready_tool_full':1,'reporting_refinement_previous_tool_full':1,
  'initial_peer_header_full':1,'initial_publisher_full':2,
  'RootDeferredRecord_initial_stable_then_final_context':True,
  'native_full_originals':len(inputs),'gui_fullcanonical_inputs':5,'gui_disassembly':False,
  'current_stable':len(current),'final_context':len(context),'old_tools_read_not_rerun':True,'unobserved_transient_context_not_reconstructed':True})
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file():
   raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
 dump('LIST.json',members);raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(raw),'sha256':sha(raw)})
 dump('seal.json',{'round':194,'scope':'Actual static bounded selection/reset history; authoritative suppliers OPEN','members':members,'member_count':len(members),
  'member_bytes':sum(q['bytes'] for q in members),'current_source_count':len(current),'context_source_count':len(context),'native_original_input_count':len(inputs)})
 print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'files_with_seal':len(members)+1,
  'member_bytes':sum(q['bytes'] for q in members),'current':len(current),'context':len(context),'original_inputs':len(inputs)+len(current)+len(context),'native_inputs':len(inputs),'tool_sha256':sha((ROOT/OWN).read_bytes())}))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['recover','final']);a.add_argument('--context',nargs='*',default=[]);q=a.parse_args()
 recover() if q.stage=='recover' else final(q.context)
