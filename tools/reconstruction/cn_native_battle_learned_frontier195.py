"""195 exact native list-state getters; static source/file/PE only."""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-owner-frontier-01'
OUT=ROUND/'agents/cn-native-battle-learned-frontier'
BASE=ROUND.parent
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='bcff0e9bbe5e7d2d69553e55faaadb49f86e2fb8d4e912cd8811a2ed3dc34856'
OWN='tools/reconstruction/cn_native_battle_learned_frontier195.py'
STABLE=[OWN,'src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp',
 'src/cn/protocol/CnBattleSkillDefinition.h','src/cn/protocol/CnBattleCommandGate.h',
 'src/cn/world/CnBattleSkillSelectionSource.h','src/cn/world/CnBattleSkillSelectionSource.cpp',
 'tools/reconstruction/cn_battle_skill_list_frontier193.py',
 'tools/reconstruction/cn_battle_skill_history_frontier194.py',
 'tools/reconstruction/cn_battle_subject_skill_frontier193.py']
GUIDELINES=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
ADDRESSES=['00553bc0','00553e90','00553f50','005530f0','00553600','00553630','00553590','005535d0',
 '005537a0','005537e0','00553810','00553850','005538e0','00553960','00553af0','00553b40','00553b80','00552870','00553220']
NEW=[(0x5537e0,37),(0x553810,27),(0x553b40,53)]
SPANS=[
 (0x5537e0,37,'new_complete_data_getter','BYTE input ordinal<countBYTE+5 returns component+ordinal*2D0+26C else0; no state value/domain/permission asserted.'),
 (0x553810,27,'new_complete_data_getter','Actual secondaryselectorBYTE+2D10<3 returns component+selector*54+2D50 else0; array address only.'),
 (0x553b40,53,'new_complete_data_getter','Primaryselector<=F/countpositive/index<count thenWORD at14+2index>>15. Native lacks index>=0 check; bit15 is raw state, never learned/cast authority.'),
 (0x553bc0,187,'retained193_bounded','Original bank arg/group+2D4 subject row pointers/primary data reset from193; no new initializer recovery.'),
 (0x553c7b,382,'retained193_bounded','Original normalized primaryWORD bit15/control caller frontier captured193; no GUI/render interior followed.'),
 (0x553df9,67,'retained193_bounded','Original three secondary54B-region reset and selector0100 from193; source/data fields only, UIcallee stopped.')]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(rel,raw):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=raw:raise RuntimeError('Preserve actual epoch: '+rel)
  return
 with p.open('xb') as f:f.write(raw)
def dump(rel,obj):put(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def original(p,copy):
 raw=p.read_bytes();put(copy,raw)
 return {'path':str(p.resolve()),'copy':copy,'bytes':len(raw),'sha256':sha(raw)}
def facts(final=False):
 return {'round':195,'BATCHFINAL_received':final,'owned_cpp_new':0,'owned_cpp_modified':0,
  'new_bounded_native_spans':3,'new_bounded_native_bytes':117,
  'new_native_relations':[
   {'key':'primary_auxiliary_array_actual_ordinal','scope':'5537E0 actualBYTEargument<count atcomponent+5; returns component+ordinal*0x2D0+0x26C. This is a distinct auxiliary rawBYTE-array address, not theWORD/pointer list or learned permission.','rawsites':['005537e3','005537e6','005537e9','005537eb','005537ee','005537f4','005537f9']},
   {'key':'secondary_state_array_actual_selected_group','scope':'553810 actualBYTEselectorcomponent+2D10 unsigned<3; returns component+selector*0x54+0x2D50. Exact selected group address not copied from samekind/id and no arbitrary default group.','rawsites':['00553810','00553816','00553818','0055381a','0055381d','00553820','00553825']},
   {'key':'primary_original_word_state_bit15','scope':'553B40 actualprimaryselector<=F; native signedcount>0 and signedindex<count but no index>=0. ExactWORD+0x14+index*2 shifted15 produces rawbit only. Qualified owned reader rejects invalid index; this native omission is not server permission or an input rule.','rawsites':['00553b43','00553b46','00553b48','00553b4a','00553b4d','00553b55','00553b58','00553b5a','00553b5c','00553b5f','00553b61','00553b63','00553b68']}],
  'retained_bounded_native_spans':3,'retained_bounded_native_bytes':636,'native_original_input_count':22,
  'source_action':'Existing CnBattleSkillSelection::Snapshot owns full component351C/rawWORD entries and original current source; it already preserves these fields. No equivalent reader class or guessed learned gate added.',
  'corrected_peer_qualification':{'classification':'Other agent retained provenance; not a new relation/span of this agent',
   'actual_source':'tools/reconstruction/cn_native_learned_subject_frontier195.py',
   'scope':'Correct bundle base EBP-A18: slot2 EBP-A10 is LEA P+89B26C U copied to H+20; loaded P+A69F1C is slot3 EBP-A0C copied to H+24. Same P/call/epoch required. H+14/R+90 source equality and mode1 lack of mode0 4D2D30 attachment never establish common learned/cast authority.',
   'earlier_peer_source_ready':'Historical uncorrected full receipt retained separately; corrected findings/stack ledger and final actual tool retained as separate epochs.'},
  'learned_permission_qualified':False,'actual_common_battle_supplier_recovered':False,
  'qualify_false_gaps':[
   'Actual server common learned/actor/battle context/grant86 fullhistory/MP/range/item/cost/save/replay/once settlement/native replies/Main supplier is not recovered from the three raw getters.',
   'Getter addresses, same bank, WORLD34/35 retained flags or rawbit15 do not establish native/common actor identity or a server learned/cast grant.',
   'Nativepeer independently proves sameP/epoch worldR and battleH14 source address relations; this agent does not count those spans or assume battle mode1 reattaches world mode0 UI.',
   'Actual list/bank/index/flag/source epoch issuer must qualify current raw projection; no client-memory runtime prerequisite or invented subject-row materializer.'],
  'gui_top_level_distinction':{
   '552870':'Fullcanonical top-level writes GUI handle throughcomponent+2E2C WORDpointer and sets3510FFFF; source/control/rect fields retained, no callee followed.',
   '553220':'Fullcanonical top-level writes GUI handle throughcomponent+2E30 WORDpointer and sets3512FFFF; source/control/rect fields retained, no callee followed.',
   'qualified_learned_row_transfer_found_in_these_top_levels':False,
   'global_absence_claimed':False,'gui_interiors_disassembled':False},
  'prior_layer_correction':'Initial message loosely called getters previous193 Ccontext. Exact193/194 top-level span/input manifests show no corresponding interval or canonicalC file. Metadata listing is not canonicalC/raw coverage. Scope only those compared manifests, no global never-read claim.',
  'retained_relations':['553BC0 group+2D4 holds suppliedcomponent+D8+n*3EC; current/common actor/learned privilege separate from equal addresses.',
   'Existing initializer clear/bit15 normalization, S87 direct554750 writer and194 reset/select history remain prior evidence; no new opcode/phase counted.'],
  'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,'receiver_contexts':14,'qualified_receiver_contexts':12,
  'unresolved_helpers':[{'va':x,'phase':None,'slot':None,'producer':None} for x in ['0047DE70','004812B0']],
  'whole_game_route_denominator':None,'whole_game_percentage':None,
  'gaps':['Actual learned supplier remains OPEN; preserve raw field widths/order/state and qualify actual common actor/current independently.',
   'Pure getter captures only exactlocal native branches; not all aliases/copy/cancel/destruction paths or global completeness.',
   'No GUI/render/glyph/font/formatter/capacity/155 or52F330/52F170 callees followed; no data predicates interpreted as game rights.'],
  'build_test_runtime_native_codec_api_db_deploy':False}
def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
 before_raw=(ROUND/'before-manifest.json').read_bytes()
 if sha(before_raw)!=BEFORE or len(json.loads(before_raw))!=1398:raise RuntimeError('Freshbefore1398 differs')
 before={q['path']:q for q in json.loads(before_raw)};old=[]
 for n,rel in enumerate(STABLE[1:]+GUIDELINES):
  q=before[rel];raw=(ROUND/q['snapshot']).read_bytes()
  if sha(raw)!=q['sha256'] or len(raw)!=q['bytes']:raise RuntimeError('Actual before full source differs')
  cp=f'before/b{n:02d}'+Path(rel).suffix;put(cp,raw);old.append({'path':str((ROOT/rel).resolve()),'copy':cp,'bytes':len(raw),'sha256':sha(raw),'epoch':'freshbefore1398'})
 dump('before-source-origins.json',old);dump('before-owned-absence.json',[{'path':str((ROOT/OWN).resolve()),'absent_in_freshbefore':OWN not in before}])
 raw=EXE.read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Pinned actual native PE differs')
 meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes();rows={q['address']:q for q in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RECOVERY/'calls.tsv','originals/calls.tsv')];sites=[]
 for n,address in enumerate(ADDRESSES):
  p=RECOVERY/rows[address]['file'];q=original(p,f'originals/p{n:02d}.c');inputs.append(q)
  for line,s in enumerate((OUT/q['copy']).read_text(encoding='utf-8-sig').splitlines(),1):
   if any(k in s.lower() for k in ['0x26c','0x2d50','0x2d10','0x2d4','0x3ec','0x3518','0x7fff','0x1f0','0x258','0x2e2c','0x2e30','0x3510','0x3512','param_2 < i','0xf','0x1000']):
    sites.append({'path':str(p.resolve()),'line':line,'text':s,'original_sha256':q['sha256'],'raw_getter_proof':address in ['005537e0','00553810','00553b40'],'source_only_other_context':address not in ['005537e0','00553810','00553b40','00553bc0']})
 dump('native-original-inputs.json',inputs);dump('primary-source-sites.json',sites)
 dump('bounded-original-call-rows.json',[q for q in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if q['target'] in ['005537e0','00553810','00553b40','00553bc0']])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];ins=[]
 for n,(va,size,classification,scope) in enumerate(SPANS):
  off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];cp=f'raw/s{n:02d}.bin';put(cp,b)
  decoded=[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':classification} for i in md.disasm(b,va)]
  if sum(len(bytes.fromhex(q['bytes'])) for q in decoded)!=size:raise RuntimeError('Whole bounded instruction bytes incomplete')
  dump(f'derived/s{n:02d}.json',decoded);ins.extend(decoded);spans.append({'va_start':f'{va:08x}','va_end':f'{va+size:08x}','bytes':size,'file_offset':off,'copy':cp,'sha256':sha(b),'classification':classification,'scope':scope})
 dump('native-spans.json',spans);dump('instruction-sites.json',ins)
 receipts=[];comparisons=[]
 for epoch in ['cn-native-battle-skill-selection-source-01','cn-native-battle-skill-publication-source-01']:
  manifests=list((BASE/epoch/'agents').glob('*/native*spans.json'))+list((BASE/epoch/'agents').glob('*/original-inputs.json'))
  for p in sorted(manifests):
   cp=f'prior-receipts/r{len(receipts):02d}.json';q=original(p,cp);receipts.append(q);body=json.loads((OUT/cp).read_bytes());hits=[]
   if 'spans' in p.name:
    for t,size in NEW:
     for row in body:
      lo=row.get('va_start');hi=row.get('va_end');lo=int(lo,16) if isinstance(lo,str) else lo;hi=int(hi,16) if isinstance(hi,str) else hi
      if lo is not None and hi is not None and lo<t+size and t<hi:hits.append({'target':f'{t:08x}','prior_span':row})
   else:
    hits=[q for q in body if any(f'{t:08x}' in q.get('path','').lower() for t,_ in NEW)]
   if hits:raise RuntimeError('Target already in explicitly compared oldraw/C layer; classify honestly')
   comparisons.append({'receipt_copy':cp,'original_path':q['path'],'comparison_layer':'raw_intervals' if 'spans' in p.name else 'full_canonical_input_paths','matches':hits})
 dump('prior-receipt-origins.json',receipts);dump('prior-layer-comparison.json',comparisons)
 dump('initial-coverage-correction.json',{'initial_loose_message':'193 hadCcontext butnorawspans for3getters','correct_scope':'Compared193/194 top-level span andcanonicalinput manifests have no3targetintervals orcanonicalC originals. Metadata presence notC/raw coverage; notglobal never-read proof.','old_seals_rewritten':False})
 dump('initial-source-origins.json',[original(ROOT/OWN,'initial/tool.py')]);dump('source-ready-source-origins.json',[original(ROOT/OWN,'source-ready/tool.py')]);dump('findings-source-ready.json',facts())
 print(json.dumps({'state':'source-ready','native_inputs':len(inputs),'new_spans':3,'new_bytes':117,'new_relations':3,'retained_spans':3,'retained_bytes':636,'current_planned':len(STABLE),'prior_receipts':len(receipts)}))
def final(extra):
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
 native=json.loads((OUT/'native-original-inputs.json').read_bytes())
 for q in native:
  raw=Path(q['path']).read_bytes()
  if sha(raw)!=q['sha256'] or len(raw)!=q['bytes'] or raw!=(OUT/q['copy']).read_bytes():raise RuntimeError('Actual full original differs')
 current=[original(ROOT/rel,f'current/c{n:02d}'+Path(rel).suffix) for n,rel in enumerate(STABLE)]
 context=[original(ROOT/rel,f'context-final/k{n:02d}'+Path(rel).suffix) for n,rel in enumerate(GUIDELINES+extra)]
 peer=ROUND/'agents/cn-native-learned-subject-frontier';receipts=[]
 for n,name in enumerate(['findings-source-ready.json','findings-source-ready-corrected.json','stack-ledger.json']):
  row=original(peer/name,f'peer-qualification/q{n:02d}.json');row['classification']='Derived other-agent correction receipt; not original native input or current source';receipts.append(row)
 dump('peer-qualification-receipts.json',receipts)
 dump('qualification-after-origins.json',[original(ROOT/OWN,'qualification-after/tool.py')])
 dump('current-source-origins.json',current);dump('final-context-source-origins.json',context);dump('original-inputs.json',native+current+context)
 dump('findings.json',facts(True));dump('gaps.json',facts()['gaps']+facts()['qualify_false_gaps'])
 dump('actual-read-epochs.json',{'freshbefore1398_sha256':BEFORE,'before_stable_full':9,'before_guidelines_full':3,'own_tool_absent':1,
  'initial_tool_full':1,'source_ready_tool_full':1,'qualification_before_tool_full':1,'qualification_after_tool_full':1,'corrected_peer_receipts_separate':3,'actual_native_full_originals':len(native),'current_stable_full':len(current),'final_context_full':len(context),
  'prior_receipts_separate_from_sources':True,'GUI_source_only_nonzero_data_field_sites_retained':True,'old_tools_read_not_rerun':True})
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file():
   raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
 dump('LIST.json',members);raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(raw),'sha256':sha(raw)})
 dump('seal.json',{'round':195,'scope':'Actual pure list-state getters; learned/battle authoritative suppliers OPEN','members':members,'member_count':len(members),
  'member_bytes':sum(q['bytes'] for q in members),'current_source_count':len(current),'context_source_count':len(context),'native_original_input_count':len(native)})
 print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'files_with_seal':len(members)+1,
  'member_bytes':sum(q['bytes'] for q in members),'current':len(current),'context':len(context),'original_inputs':len(native)+len(current)+len(context),'native_inputs':len(native),'tool_sha256':sha((ROOT/OWN).read_bytes())}))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['recover','final']);a.add_argument('--context',nargs='*',default=[]);q=a.parse_args()
 recover() if q.stage=='recover' else final(q.context)
