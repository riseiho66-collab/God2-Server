"""CN193 actual selected-skill list writers; file/PE/Capstone only."""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-selection-source-01'
OUT=ROUND/'agents/cn-battle-skill-list-frontier'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
RESOURCE=EXE.parent/'Data2/Fight/Spg/cbspec2.bin'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
RESOURCEPIN='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004'
BEFORE='6d48485ee39748151f27a3521e19de11feef6e4bc27ecbffed1276edef00ab73'
HEADER='src/cn/protocol/CnBattleSkillSelection.h'
OWNED='tools/reconstruction/cn_battle_skill_list_frontier193.py'
STABLE=['src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp',
 'src/cn/protocol/CnBattleSkillDefinition.h','src/cn/protocol/CnBattleCommand35.h',
 'src/cn/protocol/CnBattleContext82.h']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/cn_battle_skill_command_frontier192.py',
 'tools/reconstruction/cn_native_skill_catalog_source_delivery.py']
PRIMARY=['00549a70','00553920','00553a50','00553670','00553830','00553a00','00553a90','005539b0',
 '00547080','005530f0','00553220','00553590','005535d0','00553600','00553630',
 '00553bc0','00553e90','00553f50','005545c0','00554750','0054a320','0054def0',
 '00553fa0','005540b0','00554200','00553f30','00561bb0','00543560']
SPANS=[
 (0x554750,0x55497e,'new_complete','Actual558B primary/secondary writer, rawWORD bit14 route, 6bitkind/ID, samebank actual recordpointer append, count and bit15 updates; no writer capacity guard'),
 (0x54def0,0x54df0c,'new_complete','28B actual owner+A89658 forwarding payload+1 to554750; no opcode/permission inferred'),
 (0x553f30,0x553f4c,'new_complete','28B selectedsecondary count reset, pointers/old bytes remain'),
 (0x553fa0,0x553ffc,'new_complete','92B primary100 WORDs clear bit15 and auxiliary100bytes+status clear; counts/pointers remain'),
 (0x554200,0x5542d8,'new_complete','216B supplied BYTE low5 slot/high3 state; conditional priorstatus2 clearsbit15, actualsubjectWORD compare selects differentprimarygroup; not serverauthority'),
 (0x553bc0,0x553c7b,'new_bounded','187B initializer actualbankargEBP28→3518, 16groups clear and subjectrow addresses stride3EC, selector/count from actualsubjectcomponent'),
 (0x553df9,0x553e3c,'new_bounded','67B same initializer three secondary54B regions clear, pagecount1, selector WORD0100; UIcallee callsite only'),
 (0x54a6a5,0x54a6e4,'new_bounded','63B actual owner+9D223C ninth argument and owner+A89658 ECX→553BC0; fullordered stack operands retained'),
 (0x549a70,0x549aab,'retained','192 selectedslot getter: originalowner flagsA970F8/Fc and signedindexA8CBFC, stackargument ignored'),
 (0x553920,0x553955,'retained','192 secondary getter selector<3, signedindex/count, actualpointer array'),
 (0x553a50,0x553a82,'retained','olddeferred primary getter selector<=F and signedindex/count'),
 (0x553670,0x5537a0,'retained','192 fullprimaryC retained known UI page consumer; raw context first captured here; no renderer interior'),
 (0x553830,0x55384b,'retained','192 retained secondarypointer-array base getter'),
 (0x553a00,0x553a4c,'retained','192 retained key-match index finder; doesnot substitute pointer identity'),
 (0x553a90,0x553aed,'retained','192 retained page-index pointer getter; assert doesnot prevent unsafe read'),
 (0x5539b0,0x5539f4,'retained','192 retained raw signedWORD/pointer helper; no nonnegative index guarantee'),
 (0x561bb0,0x561c3d,'retained','Earlier catalog loader consumes four header bytes separately then112656 byte nativebank payload; no newloadercount'),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Existing epoch differs; preserve first and choose new epoch')
  return
 with p.open('xb') as f:f.write(b)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(p,target):
 b=p.read_bytes();put(OUT/target,b)
 return {'path':p.resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)}
def recover():
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();asset=RESOURCE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN or len(asset)!=112660 or sha(asset)!=RESOURCEPIN or len(before)!=1382 or sha(fresh)!=BEFORE:raise RuntimeError('Actual original/before drift; never refresh baseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':193,'before_inputs':1382,'before_sha256':BEFORE,'phase':'file/static only','baseline_replaced':False})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RESOURCE,'originals/cbspec2.bin')];sites=[]
 for n,a in enumerate(PRIMARY):
  p=RECOVERY/rows[a]['file'];r=original(p,f'originals/p{n:02}.c');inputs.append(r)
  for line,t in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(k in t.lower() for k in ['00554750','00553bc0','0x3518','0x2d14','0x2d28','0x2d64','0x2d10','0x2d0','0x6e04','0x3ec','0x7fff','0x4000','0xa970f8','00a970f8','0x27488f','0x888444','0x1b810']):sites.append({'path':r['path'],'line':line,'text':t,'sha256':r['sha256'],'scope':'fullprimaryoriginal; actualraw proof separate'})
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]]);emit('primary-source-sites.json',sites)
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 idx={r['path']:r for r in before};old=[]
 for n,f in enumerate(STABLE):
  r=idx[f];b=(ROUND/r['snapshot']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('Protected before changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,b);old.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)})
 for f in [HEADER,OWNED]:
  if f in idx:raise RuntimeError('New source was in freshbefore')
  old.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new source absent in freshbefore'})
 emit('before-source-origins.json',old)
 emit('initial-source-origins.json',[original(ROOT/HEADER,'initial/header.h'),original(ROOT/OWNED,'initial/writer.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 spans=[];instructions=[];counts={}
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset=pe.get_offset_from_rva(lo-base);b=raw[offset:offset+hi-lo];target=f'raw/s{n:02}.bin';put(OUT/target,b)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in cs.disasm(b,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(b):raise RuntimeError('Bounded static span incomplete')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,'copy':target,'bytes':len(b),'sha256':sha(b),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  c=counts.setdefault(classification,{'spans':0,'bytes':0});c['spans']+=1;c['bytes']+=len(b)
  instructions.extend(dict(i,span=n,classification=classification) for i in decoded)
 emit('native-spans.json',spans);emit('instruction-sites.json',instructions)
 payload=asset[4:];put(OUT/'derived/native-bank-payload.bin',payload)
 emit('bank-relation.json',{'original_file_bytes':112660,'original_file_header_bytes':4,'native_bank_bytes':112656,'derived_payload_sha256':sha(payload),'loader':'561BB0 consumes4byteheader thenfread1B810 into component888444; prior evidence retained','same_owner':'54A6A5 actualbank owner9D223C and54A6B3 listownerA89658 ->553BC0 writes3518','record':'nativebank+kind6E04+ID6E-6A = nativebank+actualfileoffset-4','unknown_bytes':'fullnativebank retained, selected110bytes compared againststrongactualcatalog; callback qualifies complete loadedbank/current, selectedrecordequality doesnot prove everypadding byte','ordinary_layout':'selectedprimary100/secondary10 maximum is qualifiedcapturedsafe domain, notnativewriter guard'})
 relations=[
 {'native':'55475D..554775','input':'rawWORD fromactualpointer, bit14 selects list, lowBYTE ID, (WORD>>8)&3F kind; bit15 state retained','namespace':'raw flags notcommonlearnedskills/permission'},
 {'native':'5547F3..55483D','primary':'rawWORD storegroup14+count2; actualbank3518+kind6E04+ID6E-6A storegroupDC+count4; count++, pages=ceilcount/15','matching_existing':'5547D1..5547DF modifies onlybit15 ofexistingWORD; pointer notrewritten'},
 {'native':'554905..554946','secondary':'rawWORD store2D14+selector54+count2; actualpointer2D28+selector54+count4; byte2D50+index statebit15; count++','matching_existing':'55495A..554975 modifiesonlybit15 WORD andsameflagBYTE'},
 {'native':'553BC0..553C7B;54A6A5..54A6E4','owner':'actualbattleownerH; listcomponentH+A89658, storedbankH+9D223C; ninthstackarg EBP28','subjectrows':'arg7 EBP20 fromH14+90, rows+ D8+selector3EC→group2D4','index':'549A70 alwaysusesownerA8CBFC, notitsstackargument'},
 {'native':'553DF9..553E3C','secondaryinitialization':'three54byte blocks cleared, pagecount1, selectorWORD0100; no lifecycleissuer invented'},
 {'native':'553F30/553FA0/554200','current_requirement':'countreset canretainoldpointers; bit15/statusclear canretaincounts/pointers; suppliedepoch mustbindoriginalflags/selector/index/bank/list andactorphase','limits':'onlytargetedwriters; notallaliases/cancel/destruction found'},
 {'native':'549A70/553920/553A50 retained','selection':'primaryflagF8 nonzero→primary; F8==0 && FC!=0→secondary; bothzero→primary; signedslotboundactualcount; selectedpointer fullDWORD'},
 ]
 emit('field-relations.json',relations)
 sources=[]
 for f in STABLE+[HEADER]:
  b=(ROOT/f).read_bytes()
  for line,t in enumerate(b.decode('utf-8-sig').splitlines(),1):
   if any(k in t for k in ['Record','Snapshot','Scope','raw_','current','lookup','bank_','address','Source','file_offset','selected','entries_']):sources.append({'path':(ROOT/f).resolve().as_posix(),'line':line,'text':t,'sha256':sha(b)})
 emit('cpp-source-sites.json',sources)
 findings={'round':193,'phase':'file/static only','new_cpp':1,'modified_cpp':0,'native_spans':len(spans),'native_bytes':sum(r['bytes'] for r in spans),'native_span_counts':counts,'instruction_sites':len(instructions),'data_sites':0,'primary_sites':len(sites),'cpp_source_sites':len(sources),'original_inputs':len(inputs),'original_bytes':sum(r['bytes'] for r in inputs),'new_opcodes':0,'complete_gameplay_routes':0,'whole_game_percent':None,'build_test_native_codec_api_db_sql_deploy':0,
 'proven':['Actual554750 whole558B writesprimary/secondary fullDWORDrecordaddresses fromsamebank3518; rawWORDbit14 route/kind6bits/statebit15 preserved.','54A320 boundedcaller plus553BC0 boundedinitializer independently bindlistcomponentH+A89658/storedbankH+9D223C; stackledger keepsall9args.','Actualtargetedcountreset/bit15clear/subjectselectorwriter change Current obligations; rawcounts/pointers retained aftersome resets.','ReadonlyprivateownedSnapshot carriesfullcomponent/nativebank/index/flags andfullselectedlist, strongactualNativeCatalog/current; exactpointer/sourceoffset-minus4/full110bytes matched.'],
 'limits':['Retained192/oldergetter/loader/rawUIcontexts are notnewopcodes/functions/gameplay; no nativeexecution.','Bankfileheader4bytes excluded fromnativepayload, no plainfile reader/source invented fornativebank.','Nativewriter lackscapacity/kind/domain guards; parseracceptsonlyqualified100/10declaredcatalog domain anddoesnotgrantpermission.','Suppliedrawmemory equality alone cannotprove actualloadedbank/owner/current/epoch/sourceissuer; mandatoryactualCurrent remainsrequired.','No allwriteraliases/cancel/destruction/learnedMP/cost/authority completeproof; targethelper192 andworld34/35 otherpeer notrecapturednew.']}
 emit('findings.json',findings)
 emit('gaps.json',[{'gap':'Actuallive suppliedprojection issuer','next':'Owner mustsupplycomplete nativebank/list/index/flag views fromsameH actualcatalogloadedepoch, bindrealactor/current/phase; sourcecallbackmandatory'}, {'gap':'Allalias/reset/destruction coverage','next':'Current invalidation ontrueowner lifetime andeverymutation; targetedwriters notabsenceproof'}, {'gap':'Native skill rights/currentcost/MP/targetauthority','next':'Realcommon/game authority source; pointerlist/currentdecode isnot entitlement'}])
 put(OUT/'README.md',b'# CN skill selection193\n\nActual static558B list writer plus bounded sameowner initializer/caller. Native payload112656 excludes4bytefileheader. Private owned readonly snapshot qualifies suppliedprojection against actual source/current and everyselected110byte record. Retained getter/loader/UIcontext notnew opcode. No tests/build/runtime/DB/deploy; routes0/percentnull. Finalseal only afterBATCHFINAL.\n')
 derived=[]
 for folder in ['raw','derived']:
  for p in sorted((OUT/folder).rglob('*')):
   if p.is_file():
    b=p.read_bytes();derived.append({'path':p.resolve().as_posix(),'copy':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'kind':'static subset/disassembly/strippedfileheader payload; notwholeoriginal'})
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
  emit('seal.json',{'round':193,'members':members,'member_count':len(members),'current_originals':len(current),'native_originals':1,'complete_gameplay_routes':0,'whole_game_percent':None})
  b=(OUT/'seal.json').read_bytes();print(json.dumps({'seal_sha256':sha(b),'members':len(members),'files_with_seal':len(members)+1,'current':current}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--capture',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args()
 if a.recover:recover()
 if a.capture:capture(a.seal)
