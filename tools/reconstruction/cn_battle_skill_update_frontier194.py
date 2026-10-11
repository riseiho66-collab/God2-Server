"""CN194 exact S2C87 retained native branch and readonly field view; static only."""
from pathlib import Path
import argparse,csv,hashlib,io,json,struct
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-publication-source-01'
OUT=ROUND/'agents/cn-battle-skill-update-frontier'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
RESOURCE=EXE.parent/'Data2/Fight/Spg/cbspec2.bin'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
RESOURCEPIN='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004'
BEFORE='b4a2a26c57b6c061ae43da94ef2ac629f462bab42e66bcb7b0d6e0b9fc7e55b8'
HEADER='src/cn/protocol/CnBattleSkillUpdate87.h'
OWNED='tools/reconstruction/cn_battle_skill_update_frontier194.py'
STABLE=['src/cn/protocol/CnBattleSkillSelection.h',
 'src/cn/protocol/CnBattleSkillDefinition.h']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/cn_battle_deferred_consumer_delivery.py',
 'tools/reconstruction/cn_battle_skill_list_frontier193.py']
PRIMARY=['005485f0','00551d50','00567b50','0054def0','00554750',
 '00555450','00555540','00555560','00481170']
# All byte/consumer facts were already retained by the old deferred recovery
# or193 writer. This delivery adds typed field/producer qualification, not new
# native code coverage, opcodes or complete gameplay.
SPANS=[
 (0x567b50,0x567b69,'retained','Unsignedopcode dispatcher into table567CA4'),
 (0x567b69,0x567b70,'retained','S87 actualtable target returnslogical3'),
 (0x481170,0x481182,'retained','Actual length wrapper calls567B50, no codec or wire transformation'),
 (0x54864d,0x548677,'retained','Phase2 selectedinput, actualopcode selector andindirectreceiver table'),
 (0x548882,0x54889a,'retained','SelectedS87 queue append with actualnative length toownerA97980'),
 (0x551fc5,0x552005,'retained','Retained queuedcopy toownerA97180, opcode-low1C selector indirectconsumer'),
 (0x5523f6,0x55240d,'retained','ActualS87 direct554750 call bodyownerA97181/componentA89658; not54DEF0'),
 (0x54def0,0x54df0c,'retained','193 samebody+1 helper; truephasecaller not established, no reference absenceclaim'),
 (0x554750,0x55497e,'retained','193 whole558B writer rawWORD bit14 list/bit15 state/kind6bits/ID8'),
 (0x555450,0x5554ff,'retained','Old queue ringappend complete175B; memcpy/assert callsites only, no interiors'),
 (0x555540,0x555551,'retained','Old queue peek complete17B'),
 (0x555560,0x555617,'retained','Old queue copy/remove complete183B; false/trueflag preserves/removes logicalbytes'),
]
DATA=[(0x567ca4,255*4,'retained','Length tablefull255DWORDs; selected87slot=567EC0→567B69'),
 (0x548c9c,63*4,'retained','Receiverfulltable63DWORDs'),
 (0x548d98,252,'retained','Receiverfullopcode selector;87→3'),
 (0x552538,10*4,'retained','Deferredconsumerfulltable10DWORDs'),
 (0x552560,110,'retained','Deferredconsumerfullselector indexedopcode-1C;87→6')]
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Existing epoch differs; preserve it and choose a new epoch')
  return
 with p.open('xb') as f:f.write(b)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(p,target):
 b=p.read_bytes();put(OUT/target,b)
 return {'path':p.resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)}
def recover():
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();asset=RESOURCE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN or len(asset)!=112660 or sha(asset)!=RESOURCEPIN or len(before)!=1390 or sha(fresh)!=BEFORE:raise RuntimeError('Actualoriginal/freshbefore drift; never replacebaseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':194,'phase':'file/static only','before_inputs':1390,'before_sha256':BEFORE,'baseline_replaced':False})
 rows={x['address']:x for x in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RESOURCE,'originals/cbspec2.bin')];primary=[]
 for n,a in enumerate(PRIMARY):
  p=RECOVERY/rows[a]['file'];r=original(p,f'originals/p{n:02}.c');inputs.append(r)
  for line,t in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(k in t.lower() for k in ['0x87','00554750','005567b50','00555450','00555540','00555560','00554def0','0x4000','0x7fff','0x3518','0x6e04','0x2d28','param_4 != 0']):primary.append({'path':r['path'],'line':line,'text':t,'sha256':r['sha256'],'scope':'fullprimaryactual original, rawbranch proof separate'})
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]]);emit('primary-source-sites.json',primary)
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 idx={x['path']:x for x in before};before_sources=[]
 for n,f in enumerate(STABLE):
  r=idx[f];b=(ROUND/r['snapshot']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('Protected sourcebefore changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,b);before_sources.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)})
 for f in [HEADER,OWNED]:
  if f in idx:raise RuntimeError('New source presentinfreshbefore')
  before_sources.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new source absent fromfreshbefore'})
 emit('before-source-origins.json',before_sources)
 emit('initial-source-origins.json',[original(ROOT/HEADER,'initial/header.h'),original(ROOT/OWNED,'initial/writer.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 spans=[];sites=[];counts={}
 def read(va,size):
  offset=pe.get_offset_from_rva(va-base);return offset,raw[offset:offset+size]
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset,b=read(lo,hi-lo);target=f'raw/s{n:02}.bin';put(OUT/target,b)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in cs.disasm(b,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(b):raise RuntimeError('Boundedstatic span incomplete')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,'copy':target,'bytes':len(b),'sha256':sha(b),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  c=counts.setdefault(classification,{'spans':0,'bytes':0});c['spans']+=1;c['bytes']+=len(b)
  sites.extend(dict(i,span=n,classification=classification) for i in decoded)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 tables=[]
 for n,(va,size,classification,purpose) in enumerate(DATA):
  offset,b=read(va,size);target=f'raw/d{n:02}.bin';put(OUT/target,b)
  tables.append({'va':va,'rva':va-base,'file_offset':offset,'copy':target,'bytes':size,'sha256':sha(b),'classification':classification,'purpose':purpose})
 emit('data-sites.json',tables)
 _,length=read(0x567ca4+0x87*4,4);_,recv_index=read(0x548d98+0x87,1);_,recv=read(0x548c9c+recv_index[0]*4,4)
 _,consume_index=read(0x552560+0x87-0x1c,1);_,consume=read(0x552538+consume_index[0]*4,4)
 emit('selected-table-relations.json',{'opcode':0x87,'logical_size':3,'body_size':2,'direction':'S2C','phase':'battle-connection-2','length_target':struct.unpack('<I',length)[0],'receiver_selector':recv_index[0],'receiver_target':struct.unpack('<I',recv)[0],'consumer_selector':consume_index[0],'consumer_target':struct.unpack('<I',consume)[0],'actual_direct_consumer_call':'552403→554750','new_opcodes':0,'new_native_relationships':0,'scope':'independentactualbyte reconfirmation ofretained olddeferred tables; no newcoverage claim'})
 # Target-local locator only. E8-pattern/DWORD matches are candidates, not a
 # whole-program code/alias proof. No extra callee or formatter is followed.
 candidates=[]
 for section in pe.sections:
  if not section.Characteristics&0x20000000:continue
  chunk=raw[section.PointerToRawData:section.PointerToRawData+section.SizeOfRawData];at=0
  while True:
   at=chunk.find(b'\xe8',at)
   if at<0:break
   if at+5<=len(chunk):
    va=base+section.VirtualAddress+at
    if va+5+struct.unpack_from('<i',chunk,at+1)[0]==0x54def0:candidates.append(va)
   at+=1
 refs=[];at=0;needle=struct.pack('<I',0x54def0)
 while True:
  at=raw.find(needle,at)
  if at<0:break
  refs.append(at);at+=1
 emit('adapter-locator.json',{'target_va':0x54def0,'text_direct_E8_candidates':candidates,'fullfile_DWORD_candidates':refs,'qualifier':'No located directE8/DWORD references doesnot prove globalabsence/indirectcallers/unreachablecode; actualS87 branch bypassesadapter','new_spans_from_locator':0})
 emit('field-relations.json',[
 {'input':'exactlogical87+WORDLE1, size3','native':'567B62 table87→567B69 returns3;481170 retainedwrapper;actualqueue useslength3','typed_source':'StandaloneUpdate87 nativeconstant3; RootgenericDeferredRecord keepsoriginalsize table andchecksstaticassertequality/skill_update decode. No newCnBattleDeferredRecord87.h originalfile.'},
 {'native':'54864D..548677/548882..54889A','phase':'actual47F510 argument2→receiverS87 toqueueA97980','qualification':'localphase/nativequeue notcommonadmission/grant'},
 {'native':'551FC5..552005/5523F6..55240D','actual':'queuedfullrecord copy toownerA97180; selected87 branch passesownerA97181 withECXownerA89658 directlyto554750','requested_chain_correction':'54DEF0 equivalentbody+1 adapter isretained separately, actualS87caller notviait'},
 {'native':'55475D..554775','fields':'WORDbit14 path:0 primary/1secondary; WORDbit15 rawstate; kind=(WORD>>8)&3F, definitionID=WORDlowBYTE','limits':'unknownkind/id/flags preserved byreadonlyrecord; catalog/current/rights separatelyqualified'},
 {'native':'5547F3..55483D/554905..554946','effect':'appendactualrawWORD andrecordpointerbank3518+kind6E04+ID6E-6A;count++','limits':'nativewriter hasno safe100/10/kind/countchecks; typedrecorddoesnotexecute clientwriter'},
 {'native':'5547D1..5547DF/55495A..554975','effect':'existingmatchingkey preserveslow15bits andonlyupdatesbit15; secondaryauxBYTE alsoupdates','limits':'statebit15 isnotservercastgrant orlearnedentitlement'},
 {'native':'555450/555540/555560 retained','order':'nativequeueappend/peek/copy retainfullrawbytes and removeonlyactualcopyflag; no dedup/sort/synthetic reply','authority':'publicationcomesfromactualgameowner/rules/catalog/phase/history andnormalrealqueue; readonlyviewisnotproducer'},
 ])
 source=[]
 for f in STABLE+[HEADER]:
  b=(ROOT/f).read_bytes()
  for line,t in enumerate(b.decode('utf-8-sig').splitlines(),1):
   if any(k in t for k in ['Record','87','raw_','kind','definition_id','logical_size','decode','current','list','state_bit15']):source.append({'path':(ROOT/f).resolve().as_posix(),'line':line,'text':t,'sha256':sha(b)})
 emit('cpp-source-sites.json',source)
 findings={'round':194,'phase':'file/static only','new_cpp':1,'modified_cpp':0,'native_spans':len(spans),'native_bytes':sum(x['bytes'] for x in spans),'native_span_counts':counts,'instruction_sites':len(sites),'data_sites':len(tables),'data_bytes':sum(x['bytes'] for x in tables),'primary_sites':len(primary),'cpp_source_sites':len(source),'original_inputs':len(inputs),'original_bytes':sum(x['bytes'] for x in inputs),'new_opcodes':0,'new_native_spans':0,'complete_gameplay_routes':0,'whole_game_percent':None,'build_test_native_codec_api_db_sql_deploy':0,
 'proven':['PinnedCN independentlyreconfirmedS87 exact3 nativebytes/body2; standalonetypedRecord preserveseveryrawWORDbit; Rootgenericretains/checksoriginaltablelength viaexternalassert andtypedgetter.','Actualdeferred87consumer5523F6 directlycalls554750 withbody+1/listowner, retained54DEF0adapter notproven currentphasecaller.','Primary/secondarybit14, sixbitkind, ID8 andbit15state followretainedfullwriter; existingkey update onlybit15, nozero/default/grant reconstructed.'],
 'limits':['Allnative code/tablefacts are retainedolddeferred or193, notnewfunction/opcode/completegameplaycoverage.','ReadonlyRecord neverconstructs servermessages fromfields, accessesnativeprocess orgrantscast/learnedskills; genuineowner/catalog/rules/current publicationmandatory.','54DEF0 currentlivecaller remainsOPEN; emptytargetlocatorcandidates notglobalalias/absenceproof.','Queue localphase2/currentlabels notserverauthority, incoming WORDcontainsnosubject/commonidentity.','NoGUIconstructorconsumer interiors orformatter155/52F330/52F170/render/glyph/capacity chains followed; no build/tests/native/runtime/API/DB/SQL/deployment.']}
 emit('findings.json',findings)
 emit('gaps.json',[{'gap':'Genuine authoritativeS87 producer/currentepoch','next':'Actualgameowner/rules/learnedstate/catalog andexactnativeactor/list/phase suppliesfulloriginal3bytes; noautoconstruction/permissionfromclientstate'}, {'gap':'54DEF0 livereference','next':'RemainOPEN; actualS87branchdirectwriter proves contractwithoutguessingadaptercaller'}, {'gap':'Scope/history/reset/cancel','next':'Retain actual publicationorder andimmutableorigin before/afterstate; rawbit15 cannotdefinegrant orresetstate'}])
 put(OUT/'README.md',b'# CN skill update87 frontier194\n\nStatic independent reconfirmation of retained nativeS87 logical3/WORD2. Actual deferred branch calls554750 directly;54DEF0 livecaller isunknown. Standalone private readonly3byteRecord retainsbits; Rootgenericchecksoriginaltablelength viaexternalassert/typedgetter withoutdependencycycle. No encode/guessedflags/grant. Allnative spansretained, routes0/percentnull. Fulloriginals/derived/current/contextseparate. Seal onlyafterRootBATCHFINAL.\n')
 derived=[]
 for folder in ['raw','derived']:
  for p in sorted((OUT/folder).rglob('*')):
   if p.is_file():
    b=p.read_bytes();derived.append({'path':p.resolve().as_posix(),'copy':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'kind':'boundedactualnative subset/disassembly; notwholeoriginal'})
 emit('derived-inputs.json',derived)
 print(json.dumps(findings))
def capture(seal):
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(STABLE+[HEADER,OWNED])]
 emit('current-source-origins.json',current)
 if seal:
  members=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.name!='seal.json':
    b=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b)})
  emit('seal.json',{'round':194,'members':members,'member_count':len(members),'current_originals':len(current),'native_originals':1,'complete_gameplay_routes':0,'whole_game_percent':None})
  b=(OUT/'seal.json').read_bytes();print(json.dumps({'seal_sha256':sha(b),'members':len(members),'files_with_seal':len(members)+1,'current':current}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--capture',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args()
 if a.recover:recover()
 if a.capture:capture(a.seal)
