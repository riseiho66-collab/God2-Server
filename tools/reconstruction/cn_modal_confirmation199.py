"""199 actual CN modal3B -> item-use producer qualification.

Static files/PE/Capstone/hash only. No native, C++, API, codec, DB, SQL,
runtime, build or test execution. Formatter/render/GUI callees are stopped.
Whole pinned PE and primary indices retained/read/hash in place only.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json,re
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-skill-confirmation-frontier-01'
OUT=ROUND/'agents/native-modal-confirmation'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
REC=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='983a6fcb68088787bfb2a69cc6d4215784e5083f9ca82c918c2dd91fbdf1212c'
OWN='tools/reconstruction/cn_modal_confirmation199.py'
PRIMARY=['004ad550','004ad5e0','004ae370','004c61a0','004b0720','004b1b40','004815e0','00481440']
# All canonical source and sender opcode families already exist. These are
# exact expanded caller/alias relations, not new opcodes/native gameplay.
SPANS=[
 (0x4ad550,0x4ad5d4,'retained_initial_helper','Real handle20/8 gate; stores selectorDWORD and opaqueparamDWORD; renderingcallee STOP'),
 (0x4ad5e0,0x4ad687,'expanded_bounded_modal_gate','flags2 cancel; flags1/indexWORD0 confirms; selector<=3F and actualswitchentry'),
 (0x4adb73,0x4adb9f,'expanded_bounded_modal_case','Case3B zeroextends savedslotBYTE/itemWORD; C25 then conditionalC1F helper'),
 (0x4adbf6,0x4adc0e,'expanded_bounded_modal_return','Shared close callsite/actualret8; no closecallee interior'),
 (0x4aeb89,0x4aeba4,'expanded_bounded_actual_event','Actual eventhandle equals owner1C84D2 then preservedinput fields into actualmodalhandler'),
 (0x4c66bf,0x4c66d2,'retained198_bounded_item_save','Actual selectedbook itemWORD/slotBYTE stores already retained198'),
 (0x4c671c,0x4c673f,'expanded_bounded_postformatter_caller','Only caller instructions after stoppedformatter; explicitselector3B and paramaddress'),
 (0x4b0720,0x4b0751,'retained198_complete_leaf','C25body4; thirdexplicitarg ignored, body3 left as firstDWORDarg highBYTE'),
 (0x4b1b40,0x4b1b96,'retained_census_bounded_selector','Actual selector1F and callerarg0 -> realhandle4960A0 gate -> zeroBYTEqueue'),
 (0x4815e0,0x4815fe,'expanded_known_queue_metadata_tail','Existing27B metadata plus actual3B ret4 tail, body1 explicit00; not emptybody'),
 (0x481440,0x4814c5,'retained198_complete_queue','Exact opcode then bodybytes append; not peer response/castgrant')]

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Do not overwrite epoch '+name)
  return
 with p.open('xb') as f:f.write(b)
def emit(name,obj):put(name,(json.dumps(obj,indent=2,ensure_ascii=True)+'\n').encode())
def original(p,name):
 b=p.read_bytes();put(name,b)
 return dict(path=p.resolve().as_posix(),copy=name,bytes=len(b),sha256=sha(b))
def inplace(p,b,scope):return dict(path=p.resolve().as_posix(),copy=None,bytes=len(b),sha256=sha(b),complete_retained_in_place=True,scope=scope)

def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Already sealed')
 before=(ROUND/'before-manifest.json').read_bytes();rows=json.loads(before)
 if len(rows)!=1419 or sha(before)!=BEFORE:raise RuntimeError('Original freshbefore differs')
 emit('before-scope.json',dict(path=(ROUND/'before-manifest.json').as_posix(),bytes=len(before),sha256=sha(before),input_count=len(rows),tool_absent=OWN not in {r['path'] for r in rows},baseline_replaced=False))
 raw=EXE.read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Pinned actualCN PE differs')
 metadata=(REC/'functions.tsv').read_bytes();calls=(REC/'calls.tsv').read_bytes()
 funcs={r['address']:r for r in csv.DictReader(io.StringIO(metadata.decode('utf-8-sig')),delimiter='\t')}
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 inputs=[inplace(EXE,raw,'Full actual pinned PE read/hash in place; exactboundedrawcopied'),
  inplace(REC/'functions.tsv',metadata,'Full primary metadata read; selectedrows derived'),
  inplace(REC/'calls.tsv',calls,'Full primary call index read; selectedactualedges derived')]
 selected=[]
 for a in PRIMARY:
  p=REC/funcs[a]['file'];inputs.append(original(p,'primary/'+a+'.c'));selected.append(funcs[a])
 emit('derived/selected-primary-metadata.json',selected)
 edges=[r for r in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if r['caller'] in PRIMARY and r['target'] in PRIMARY]
 emit('derived/selected-primary-callers.json',edges)
 spans=[];sites=[]
 for n,(start,end,kind,scope) in enumerate(SPANS):
  offset=pe.get_offset_from_rva(start-base);b=raw[offset:offset+end-start];ins=list(md.disasm(b,start))
  if sum(i.size for i in ins)!=len(b):raise RuntimeError('Bounded raw span incomplete decode '+hex(start))
  name=f'raw/s{n:02}.bin';put(name,b)
  put(f'raw/s{n:02}.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
  spans.append(dict(va=f'{start:08x}',end_exclusive=f'{end:08x}',rva=f'{start-base:08x}',file_offset=offset,copy=name,bytes=len(b),sha256=sha(b),classification=kind,scope=scope))
  sites.extend(dict(va=f'{i.address:08x}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operand=i.op_str,span=n) for i in ins)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 data=[]
 for va,size,scope in [(0x4adcfc,4,'Exact3B index entry: 4ADC10 + 3B*4 -> target4ADB73'),
                      (0x4b1c24,1,'Exactselector1F remap index0'),
                      (0x4b1c0c,4,'Exactselector1F remappedtarget4B1B63')]:
  offset=pe.get_offset_from_rva(va-base);b=raw[offset:offset+size];name=f'data/{va:08x}.bin';put(name,b)
  data.append(dict(va=f'{va:08x}',rva=f'{va-base:08x}',file_offset=offset,copy=name,bytes=size,sha256=sha(b),scope=scope))
 emit('data-sites.json',data)
 if pe.get_data(0xadcfc,4)!=bytes.fromhex('73db4a00') or pe.get_data(0xb1c24,1)!=b'\0' or pe.get_data(0xb1c0c,4)!=bytes.fromhex('631b4b00'):raise RuntimeError('Actual selective tables differ')
 relations={
  'initial_selector':'4AD550 tests actual owner1C84D2 handle slotflags20/8, accepts negativehandle or bothclear. It stores suppliedDWORD selector to1C8D6C and *param3 to1C8D70. It does not authenticate an actor/item or issue serverpermission.',
  'actual_event':'4AEB89 tests DI against owner1C84D2,4AEB92/97 push originalsaved eventflags/index;4AEB9A calls4AD5E0 on sameactualowner. No abstract UI callback invented.',
  'modal_gate':'4AD5F6 flagsbit2 cancels before all confirmbranches;4AD63A requiresbit1;4AD642..649 signedWORD index0; selector1C8D6C<=3F;4AD680 actualcase table3B uses rawDWORD4ADCFC=4ADB73.',
  'saved_book_source':'Retained1984C66BF stores itemWORD in loaded[owner1C85A8]+310FC;4C66CC stores slotBYTE+310FE. After stoppedformattercallsite,4C6721 writes only lowWORD localparam0;4C6738 passesliteral3B to4AD550. Opaque1C8D70 is not thisconfirmation item/target.',
  'confirmed_C25':'4ADB7B MOVZX loadedslotBYTE310FE thenpush;4ADB83 MOVZX loadeditemWORD310FC thenpush;4ADB8D invokes4B0720 with thirdarg1. Producer requiresactualowner42E3C==0 then481440(C25,body4): lowWORD item atbody0,BYTEslotbody2. It ignoresarg3; body3 untouchedfirstarg highBYTE. This exactMOVZX caller makesbody3 zero; globalC25 padding0 remainswrong.',
  'conditional_C1F':'AfterC25call,4ADB98 invokes4B1B40(1F,0) regardlessofwhether C25ownergate allowedenqueue. Selectorremap actualBYTE4B1C24=0/tableDWORD4B1C0C=4B1B63; witharg0 calls4960A0 on owner1C84C6; onlynonzero enqueues C1F via4815E0. Queue4815E4 pushesbodylen1,4815E9 writesBYTE00,4815F1 calls481440: logical2,body1=00,NOT emptybody/ACK.',
  'ordered_native_output':'Actual C25 first then conditionalC1F. Either/both queuegates may suppressspecificmessage; rawclientconditions cannot substitute serverownership/current/rules.',
  'return':'4ADB9D jumps4ADBF6 commonclosecallsite4AD4E0 thensecuritycookie/ret8; closecallee/renderinteriors notfollowed.',
  'unknown':['No proof thisconfirmation is an actual learning grant, officialserver settlement, consume, responsecorrelation, skillupgrade or commoncharacter/deity/pet identity.',
             'Actual game epoch, eventhandle source lifetime and saveditem/slot stale/replacement semantics require actual owner qualification; clientfields are not a common database contract.',
             '198 ordinary367books direct25 and19literalconfirmers retain their scope. This modal3B source is shared with other nativecallers and cannot be assumedexclusive to SKB.']}
 emit('producer-relations.json',relations)
 emit('message-correction-epoch.json',dict(initial_claim='Sent peer text: additional empty C1F',correction='Raw4815E4/4815E9/4815F1 proves body1=00/logical2; initial text is wrong. No earlier tool/native artifact claimed emptybody; tool first version is alreadycorrect.',code_or_baseline_rewritten=False))
 for n,p in enumerate(['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']):inputs.append(original(ROOT/p,f'context/g{n:02}.md'))
 inputs.append(original(ROOT/OWN,'initial/tool.py'))
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]])
 emit('initial-source-origins.json',[inputs[-1]])
 emit('findings-source-ready.json',dict(round=199,native_spans=len(spans),native_bytes=sum(s['bytes'] for s in spans),instruction_sites=len(sites),data_sites=len(data),data_bytes=sum(d['bytes'] for d in data),new_native_code_bytes=0,classification='Existingcanonical/sender scopes expanded with actualmodal event/alias relationships; retained198 leaves nevercountednew',source_CPP_changes=0,new_opcodes=0,new_complete_gameplay_routes=0,whole_game_percent=None,modal3B_to_C25_source_qualified=True,C25logical5=True,conditionalC1Flogical2=True,server_learning_grant=None,interiors_stopped=['formatter155','capacity/render/glyph','52F330','52F170','renderer/GUI callees'],runtime_build_test_native_codec_api_db_sql_deploy=0))
 print(json.dumps(dict(spans=len(spans),bytes=sum(s['bytes'] for s in spans),sites=len(sites),data=len(data),inputs=len(inputs))))

def finalize():
 if (OUT/'seal.json').exists():raise RuntimeError('Alreadysealed')
 p=ROOT/OWN;b=p.read_bytes();initial=(OUT/'initial/tool.py').read_bytes()
 if b!=initial:raise RuntimeError('Tool refined: explicitlysave epochs/diff beforefinal')
 current=[original(p,'current/tool.py')];emit('current-source-origins.json',current)
 ready=json.loads((OUT/'findings-source-ready.json').read_text());emit('findings.json',ready)
 put('README.md',b'199 bounded static actual CN modal3B confirmation -> C25 then conditional C1F. producer-relations.json carries exact owner/event/alias gates and unknown authority. All canonical sourcefiles copied complete; boundedraw/selecteddata have actualVA/RVA/fileoffset/SHA. Full pinned PE/indices retainedreadhash in place. initial/current tool exactequal. Message-only mistaken emptyC1F description retained explicitly and corrected by originalbody1=00 instructions. No C++/native/runtime/API/DB/SQL/codec/build/tests.\n')
 top=OUT/'seal.json';members=[]
 for f in sorted(OUT.rglob('*')):
  if f.is_file() and f!=top:
   x=f.read_bytes();members.append(dict(path=f.relative_to(OUT).as_posix(),bytes=len(x),sha256=sha(x)))
 emit('seal.json',dict(round=199,files=members,member_count=len(members),all_nested_included=True,excluded_only='OUT root seal.json',phase='static source only'))
 print(json.dumps(dict(members=len(members),files_with_seal=len(members)+1,seal_sha256=sha(top.read_bytes()),tool_sha256=sha(b),current_originals=1,inputs=15)))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['recover','finalize']);a=p.parse_args()
 {'recover':recover,'finalize':finalize}[a.action]()
