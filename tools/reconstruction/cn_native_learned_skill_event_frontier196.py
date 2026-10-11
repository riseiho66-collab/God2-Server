"""196 native skill event boundary: pinned files and static disassembly only.

No native/runtime/codec/API/DB/SQL/build/test execution. No GUI or stopped
formatter/render/glyph/capacity callee interiors. Earlier epochs stay intact.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-event-frontier-01'
OUT=ROUND/'agents/cn-learned-event-native-frontier'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='953264e0a7624fbdc615fcd8c9d964460fd4287c2c505f4275c1d4b26cbb2c4d'
OWN='tools/reconstruction/cn_native_learned_skill_event_frontier196.py'
STABLE=['src/cn/protocol/CnWorldSubjectSkillUpdate.h','src/cn/protocol/CnSelectedSubjectUpdate.h',
 'src/cn/protocol/CnPrebornChoices.h','src/cn/world/CnPrebornSubjectState.h',
 'src/cn/world/CnPrebornSubjectState.cpp']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/cn_selected_subject_update_source_delivery.py',
 'tools/reconstruction/cn_selected_subject_title32_source_delivery.py',
 'tools/reconstruction/cn_preborn_selected_subject_source_delivery.py',
 'tools/reconstruction/cn_preborn_skill_choice_source_delivery.py',
 'tools/reconstruction/cn_native_learned_subject_frontier195.py']
PRIMARY=['004d5880','004d5a10','004d5e60','004d5cc0','0048fcc0','00492e70']
SPANS=[
 (0x4d5880,0x4d58a8,'retained_complete','WORLD33 onlyselectedrow40 BYTE; retained old selected-subject update, tail4D3E30 not followed'),
 (0x4d5a10,0x4d5a85,'retained_complete','WORLD32 selectedrow name copy; retained oldtitle source, GUI450B80 not followed'),
 (0x4d5e60,0x4d603f,'retained_complete','WORLD34 exactrow WORD/rawsubjectBYTE and appended bankpointer/flag0; raw debug God name not learnedgrant'),
 (0x4d5cc0,0x4d5e5b,'retained_complete','WORLD35 exactpointermatch andflag3, no skill removal or common learning inferred'),
 (0x493540,0x4935b4,'retained_bounded','Successful492E70 initialization bindsbank then clearscount/selector/selectedptr and3EC0 rowbytes; not a received remove event'),
 (0x491360,0x4913b0,'retained_bounded','WORLD32/33/34/35 body+1 consumers throughactual U=P89B26C; neighboring opcodes have distinct effects'),
 (0x48da44,0x48da96,'retained_bounded','Correct195 stack ledger: EBP-A18 base, slot2 atA10=U; slot3 A0C loadedcontext distinct;slot4A08=R'),
 (0x54a375,0x54a38f,'retained_bounded','Actualslot2 storedH20=U,slot3H24,slot4H14=R; sameP/epoch required'),
 (0x48ddfd,0x48de0f,'retained_bounded','Exact bundlebase LEA EBP-A18 supplied toactualH54A320; not grant or actor64 identity'),
]

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Preserve previous epoch: '+name)
  return
 with p.open('xb') as f:f.write(b)
def emit(name,obj):put(name,(json.dumps(obj,ensure_ascii=True,indent=2)+'\n').encode())
def original(p,target):
 b=p.read_bytes();put(target,b)
 return {'path':p.resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)}

def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
 fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(before)!=1403 or sha(fresh)!=BEFORE:raise RuntimeError('Freshbefore differs; no refresh')
 put('epoch/root-before.raw',fresh);emit('epoch.json',{'round':196,'before_inputs':1403,'before_sha256':BEFORE,'baseline_replaced':False})
 idx={r['path']:r for r in before};old=[]
 for n,f in enumerate(STABLE+CONTEXT):
  r=idx[f];b=(ROUND/r['snapshot']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('Actual fullbefore source changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(target,b)
  old.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)})
 if OWN in idx:raise RuntimeError('New tool alreadypresent before')
 emit('before-source-origins.json',old);emit('before-owned-absence.json',[{'path':(ROOT/OWN).resolve().as_posix(),'present':False}])
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN:raise RuntimeError('Actual native original changed')
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RECOVERY/'calls.tsv','originals/calls.tsv')];primary=[]
 for n,a in enumerate(PRIMARY):
  p=RECOVERY/rows[a]['file'];r=original(p,f'originals/p{n:02}.c');inputs.append(r)
  for line,t in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(x in t.lower() for x in ['004d5880','004d5a10','004d5e60','004d5cc0','430a8','0x1f1','0x1f0','0x4504','0x3ec','godupdateskill','param_3 + 0x59','param_3 + 0x5a','puvar10 + 0x59','puvar10 + 0x5a']):
    primary.append({'path':r['path'],'line':line,'text':t,'sha256':r['sha256'],'scope':'retained fullcanonical; selected byte proof separate, unselected callees notfollowed'})
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]]);emit('primary-source-sites.json',primary)
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 emit('initial-source-origins.json',[original(ROOT/OWN,'initial/tool.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];classes={}
 for n,(lo,hi,cl,purpose) in enumerate(SPANS):
  off=pe.get_offset_from_rva(lo-base);b=raw[off:off+hi-lo];target=f'raw/s{n:02}.bin';put(target,b)
  xs=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':cl} for i in md.disasm(b,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in xs)!=len(b):raise RuntimeError('Bounded instruction endpoint differs')
  emit(f'derived/s{n:02}.json',xs);sites.extend(xs)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':off,'copy':target,'bytes':len(b),'sha256':sha(b),'classification':cl,'purpose':purpose,'instruction_count':len(xs)})
  c=classes.setdefault(cl,{'spans':0,'bytes':0});c['spans']+=1;c['bytes']+=len(b)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 data=[]
 for n,va in enumerate([0x7f3bd8,0x7f3b54]):
  off=pe.get_offset_from_rva(va-base);end=raw.find(b'\0',off)
  if end<off or end-off>256:raise RuntimeError('Targeted literal lacksbounded terminator')
  b=raw[off:end+1];target=f'raw/d{n:02}.bin';put(target,b)
  data.append({'va':va,'rva':va-base,'file_offset':off,'copy':target,'bytes':len(b),'sha256':sha(b),'text':b[:-1].decode('ascii'),'classification':'retained_literal_context','scope':'native God naming only, not common subject semantics or learned rights'})
 emit('data-sites.json',data)
 callrows=list(csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t'))
 candidates=[r for r in callrows if r['target']=='00481440' and 0x4d0000<=int(r['caller'],16)<0x4d6400]
 emit('sender-candidate-frontier.json',{'scope':'metadata-only subjectmodule caller4D0000..4D6400 toknown481440; not wholeprogram/globalabsence','candidates':candidates,'callee_or_gui_body_followed':False,'candidate_shape_proven':False,'c2s_to_world34_35_causality':None})
 emit('event-relations.json',[
  {'native':'WORLD34→4D5E60','actual':'Same original U/R row by BYTEsubject/WORDrow, appendexact bankpointer andflag0; debugliteralGodUpdateSkillLevelUp belongs tothisconsumer','not_proven':'Serverlearning/fee/rule/event identity, common actor or C2S reply cause'},
  {'native':'WORLD35→4D5CC0','actual':'Findexactrow catalogpointer, writeflag3; no GodUpdateSkillLevelUp literal attribution','not_proven':'3 means granted/castable, generic level formula, permanent learn or remove event'},
  {'native':'WORLD32/33→4D5A10/4D5880','actual':'Selectedrow text/name androw40 BYTE, respectively; no skill removal','next':'Retain existing typed32/33 source, never pairnearbyopcodewithlearning'},
  {'native':'Successful492E70 initialization493594/9B/A2/AC','actual':'R164=0,R15F=FF,R160=0,clearR168..R+168+3EC0 afterbindingskillbankR4504','not_proven':'A client received skill removal or authoritative save mutation'},
  {'native':'195 exact bundle lineage','actual':'slot2 U=P89B26C→H20,slot3 loadedcontext→H24,slot4 R=P1478084→H14 in sameP/epoch','not_proven':'Common character/deity/pet identities or current learnedgrant'},
  {'native':'Existing preborn81/83/A1/A2','actual':'Retained choice/mask/WORD list source, actual window and owner mandatory','not_proven':'It causes WORLD34/35 or servesasgeneric learn/remove operation'},
 ])
 source=[]
 for f in STABLE:
  b=(ROOT/f).read_bytes()
  for line,t in enumerate(b.decode('utf-8-sig').splitlines(),1):
   if any(x in t for x in ['actual_','retained_','current','0x33','0x34','0x35','0x81','0x83','permission','entitlement','raw','0x258','0x1f1']):
    source.append({'path':(ROOT/f).resolve().as_posix(),'line':line,'text':t,'sha256':sha(b)})
 emit('cpp-source-sites.json',source)
 facts={'round':196,'phase':'file/static only','new_cpp':0,'modified_cpp':0,'new_tools':1,'native_spans':len(spans),'native_bytes':sum(r['bytes'] for r in spans),'native_span_counts':classes,'new_native_spans':0,'new_native_code_bytes':0,'new_native_opcodes':0,'instruction_sites':len(sites),'data_sites':len(data),'data_bytes':sum(r['bytes'] for r in data),'primary_sites':len(primary),'cpp_source_sites':len(source),'original_inputs':len(inputs),'original_bytes':sum(r['bytes'] for r in inputs),'current_originals_planned':len(STABLE)+1,'complete_gameplay_routes':0,'whole_game_percent':None,'build_test_native_runtime_codec_api_db_sql_deploy':0,
  'source_actions':['Preserve actual sameP/U/R/H20/row order/count/flags and separate current epoch. Skill definitions/list pointers do not establish common learned ownership.',
   'Keep WORLD32/33 out of skill-event mapping. Keep initializationcount0 distinct from actual WORLD30 reset supplied by peer; neither invents a skill removal request.',
   'True C2S acquisition/removal event remainsOPEN. Metadata sender candidates are GUI boundary only; no fabricated request/reply pair or guessed server event.'],
  'limits':['Allnative byte scopes alreadycaptured in selected-subject/preborn/skill-reference/125–195; newnative0. No sameopcode/key/flag inferred rights.',
   'GodUpdateSkillLevelUp andpmgod2.cpp are literal native labels, not proof common character/deity/pet identity or exact originalserver semantic.',
   'No GUI producer4D1ECB interior,4D3E30/450B80 renderer,155formatter/capacity/glyph or52F330/52F170 followed. Full canonical originals preserve those calls ascontext only.',
   'No runtime/native/tests/build/DB/SQL/API/codec; actual common issuer/rules/learned/save/replay/cost/range/phase remainOPEN.']}
 emit('findings-source-ready.json',facts);emit('findings.json',facts)
 emit('gaps.json',[{'gap':'Actual acquisition/removal C2S→authoritative owner→WORLD34/35 event','next':'Retain unknown cause. Existing client receive/list/GUIpreborn facts alone cannot synthesize originalserver rules/learned history.'},
  {'gap':'Native subject namespace/common identity','next':'Actual common owner maps exact supplied R/rowWORD/current tocharacter/deity/pet identity; literalGod label alone insufficient.'},
  {'gap':'Sender metadata candidates','next':'4D1ECB GUI boundary remains stopped; 3 knownsites to481440 are candidates only, no new shape/opcode/cause claimed.'}])
 put('README.md',b'# CN learned event frontier196\n\nPinned complete files and bounded retained native data consumers only. WORLD34 appendspointer/flag0,35 updatesflag3; neither provescommonlearnedgrant ororiginalC2Scause. WORLD32/33 names/row40 and492E70 initialzeroing areseparate, notskillremoval. NativeGod labels andpreborn81/83 remainqualifiedcontext. GUI/render/formatter chainsstopped. Newnative/code/opcode/CPP/routes0;percentnull. Before/current/context/original/derivedseparate. SealonlyafterRootBATCHFINAL.\n')
 derived=[]
 for folder in ['raw','derived']:
  for p in sorted((OUT/folder).rglob('*')):
   if p.is_file():
    b=p.read_bytes();derived.append({'path':p.resolve().as_posix(),'copy':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'kind':'native subset/disassembly; not whole original'})
 emit('derived-inputs.json',derived);print(json.dumps(facts))

def capture(seal):
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(STABLE+[OWN])]
 emit('current-source-origins.json',current)
 if seal:
  members=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.name!='seal.json':
    b=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b)})
  emit('seal.json',{'round':196,'members':members,'member_count':len(members),'current_originals':len(current),'complete_gameplay_routes':0,'whole_game_percent':None})
  print(json.dumps({'members':len(members),'files_with_seal':len(members)+1,'seal_sha256':sha((OUT/'seal.json').read_bytes()),'current_originals':len(current),'current_bytes':sum(r['bytes'] for r in current)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--capture',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args()
 if a.recover:recover()
 if a.capture:capture(a.seal)
