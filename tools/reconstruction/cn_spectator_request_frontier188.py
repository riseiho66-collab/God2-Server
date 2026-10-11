"""188 bounded CN caller operands, file/PE/Capstone reads only; no execution."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import struct
import capstone
import pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-target-identity-source-01'
OUT=ROUND/'agents/cn-spectator-request-frontier'
OWNED='tools/reconstruction/cn_spectator_request_frontier188.py'
HEADER='src/cn/protocol/CnSpectator6E.h'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METADATA='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='6b9ec7faf43f692cdf92df9150845f23f8179dadaf47a42725aa8556509718d6'
OLD=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01/agents/cn-spectator-native-frontier'
SOURCES=['src/cn/protocol/CnWorldConsumerRecords.h','src/protocol/RecoveredSpectator6E.h']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
         'tools/reconstruction/cn_native_spectator_frontier186.py']
PRIMARY={
 '00435dc0':'b9846188b78f7e27e907fb9aed9937015c6bffbaf4cb344c4ae6ed21aca3c24c',
 '00435e60':'0de29b7e627220e79a48655c20462513f8f273bd82ccb93b6f77bec56f9aa645',
 '004360b0':'145f7754ec63301c7cb99ec89ddf1aa54844663ba63635ce582bddc7ace1451c',
 '0048bd90':'f3f63800f7bdd520ff11f339f525b2276537c7b2874be19b8fa1b7052e71bc00',
 '0048c200':'b4a1f81b788819d229c2981a60adb82a4c3f88fe1329167919197cd8d9a87014',
 '0050d0c0':'e5c340874a24594930de43d441eea0d339742d575cc50110e71a8706654527a9',
 '005471f0':'01db23be31ac77f3b872b5dfb19857221f59b59316405fabe4c16dcca870b34b',
}
SPANS=[
 (0x48BD90,0x48BDC4,'new_bounded','first caller incoming action/vector owner setup and action+18 jump'),
 (0x48BFC5,0x48C013,'new_bounded','first mode1 context DWORD priority4,8,0,C and lookup/call'),
 (0x48C200,0x48C224,'new_bounded','second caller selector3 stored localself DWORD'),
 (0x48C240,0x48C26A,'new_bounded','second caller selector-4 or unassigned local44 and selector2 separate branch'),
 (0x48C28F,0x48C2B7,'new_bounded','second caller excludes localself and signed action -17 selected table'),
 (0x48C35E,0x48C386,'new_bounded','second mode1 rawDWORD lookup and producer call'),
 (0x50D0D0,0x50D0DA,'new_bounded','menu caller input flags and original owner'),
 (0x50D107,0x50D130,'new_bounded','menu flag1 and signedWORD selected index to20B record DWORD'),
 (0x50D13F,0x50D155,'new_bounded','menu signed actionWORD dispatch table'),
 (0x50D1A3,0x50D1B2,'new_bounded','menu action4 rawDWORD context mode1'),
 (0x5471F0,0x547243,'new_bounded','CN mode2/context0 localstate/inputlatch plus immediate local cleanup; not full function'),
 (0x435E60,0x435E7C,'new_bounded','CN eventarg-200 dispatch for inputlatch source'),
 (0x435F94,0x435FAD,'new_bounded','CN event204 local12018 set and12024 clear'),
 (0x435FD0,0x435FF3,'new_bounded','CN event205 local12018/1201C clear and12024 set'),
 (0x4B2010,0x4B203F,'retained186_complete','complete original CN producer, rawbody8/signednegative suppression'),
 (0x4A2863,0x4A28E6,'retained186_bounded','D0-derived selected UI DWORD path mode1, two arrays and flag2'),
 (0x4A3EC0,0x4A3F05,'retained186_complete','D0 two unsignedWORD zeroextensions, not other caller namespace'),
 (0x567B93,0x567B9A,'retained186_length','independent S2C6E fixed5 leaf, not C2S logical9/ACK'),
]
CALLERS=[
 {'va':0x48C009,'mode':1,'context':'incoming4-DWORD vector priority4,8,0,C; action-17','domain':'nonnegative rawDWORD producer, namespace/issuer unknown','classification':'candidate retained186; bounded caller operands new'},
 {'va':0x48C37F,'mode':1,'context':'selector3 localself DWORD; >=4 selector-4; <4 unassigned local44; selector2 separate branch; action-17','domain':'rawDWORD not D0 WORD; unassigned-local path not qualified source identity','classification':'candidate retained186; bounded caller operands new'},
 {'va':0x4A28DC,'mode':1,'context':'D0 WORD zeroextension ->two target arrays ->actual UI flag2 and page/control selection','domain':'qualified WORD-derived UI only; no namespace/rights inferred','classification':'retained186'},
 {'va':0x50D1A8,'mode':1,'context':'local selected signedWORD index into20B record DWORD, action4','domain':'rawDWORD; selected-list producer/currentness unknown','classification':'candidate retained186; bounded caller operands new'},
 {'va':0x547223,'mode':2,'context':0,'domain':'localA97998==1 and [owner+4]+12018 inputlatch!=0; not server rights','classification':'candidate retained186; bounded caller operands new'},
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 raw=path.read_bytes();put(OUT/target,raw)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def recover():
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METADATA or len(before)!=1341 or sha(fresh)!=BEFORE:
  raise RuntimeError('Actual original/freshbefore changed; do not refresh baseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':188,'before_inputs':1341,'before_sha256':BEFORE,'baseline_replaced':False,'phase':'file/static only'})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 originals=[]
 # Full prior primary files remain actual originals, not receipt-only evidence.
 for n,row in enumerate(json.loads((OLD/'original-inputs.json').read_text(encoding='utf-8'))):
  path=Path(row['path']);body=path.read_bytes()
  if len(body)!=row['bytes'] or sha(body)!=row['sha256']:raise RuntimeError('Retained186 actual original changed')
  originals.append(original(path,f'originals/p{n:02}{path.suffix}'))
 primary_sites=[]
 for n,(address,pin) in enumerate(PRIMARY.items()):
  path=RECOVERY/rows[address]['file'];body=path.read_bytes()
  if sha(body)!=pin:raise RuntimeError('Selected full primary source changed')
  originals.append(original(path,f'originals/n{n:02}.c'))
  for line,text in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in text.lower() for k in ('004b2010','0x12018','0x12024','0xa97998','0xe9e4','0xece4','0x1478084','case -0x11','case 0xffffffef')):
    primary_sites.append({'path':path.resolve().as_posix(),'line':line,'text':text,'actual_source_sha256':pin})
 emit('original-inputs.json',originals);emit('primary-source-sites.json',primary_sites)
 context=[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)]
 for n,name in enumerate(['findings.json','seal.json','direct-call-candidates.json']):
  row=original(OLD/name,f'context/h{n:02}.json');row['kind']='historical sealed186 scope/receipt, not current original authority';context.append(row)
 emit('context-origins.json',context)
 index={r['path']:r for r in before};source_before=[]
 for n,f in enumerate(SOURCES):
  row=index[f];body=(ROUND/row['snapshot']).read_bytes()
  if len(body)!=row['bytes'] or sha(body)!=row['sha256']:raise RuntimeError('Protected source before changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,body)
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 for f in [HEADER,OWNED]:
  if f in index:raise RuntimeError('New source incorrectly present in freshbefore')
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new file absent from freshbefore'})
 emit('before-source-origins.json',source_before)
 emit('intermediate-origins.json',[original(ROOT/HEADER,'intermediate/header-01.h'),original(ROOT/OWNED,'intermediate/writer-01.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 def read(va,size):
  offset=pe.get_offset_from_rva(va-base);return offset,raw[offset:offset+size]
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset,body=read(lo,hi-lo);target=f'raw/s{n:02}.bin';put(OUT/target,body)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(body,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(body):raise RuntimeError('Actual bounded span has incomplete instruction')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,'copy':target,'bytes':len(body),'sha256':sha(body),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  total=counts.setdefault(classification,{'spans':0,'bytes':0});total['spans']+=1;total['bytes']+=len(body)
  for i in decoded:
   if i['mnemonic'] in ('call','ret','mov','movsx','movzx','cmp','test','push','lea') or i['mnemonic'].startswith('j'):
    sites.append(dict(i,span=n,classification=classification))
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 data=[]
 for va,size,purpose in [(0x48C1AC+7*4,4,'first action-17 target'),(0x48C3FC+7,1,'second action-17 selector'),(0x48C3D8+4*4,4,'second selected4 target'),(0x50D280+4*4,4,'menu action4 target'),(0x436090+4*4,4,'event204 target'),(0x436090+5*4,4,'event205 target'),(0x567CA4+0x6E*4,4,'retained186 S2C6E lengthleaf')]:
  offset,body=read(va,size);target=f'raw/t{len(data):02}.bin';put(OUT/target,body)
  data.append({'va':va,'rva':va-base,'file_offset':offset,'copy':target,'bytes':size,'sha256':sha(body),'value':body[0] if size==1 else struct.unpack('<I',body)[0],'purpose':purpose,'classification':'retained186' if va==0x567CA4+0x6E*4 else 'new_selected_caller_relation'})
 emit('data-sites.json',data);emit('caller-domains.json',CALLERS)
 source_sites=[]
 for f in SOURCES+[HEADER]:
  body=(ROOT/f).read_bytes()
  for n,line in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in line for k in ('Spectator','spectator','context()','logical_size','Request','body','shape')):
    source_sites.append({'path':f,'line':n,'text':line,'actual_source_sha256':sha(body)})
 emit('source-sites.json',source_sites)
 findings={
  'round':188,'scope':'four other retained direct-call candidates plus necessary bounded native inputlatch; no full caller/dispatcher/phase recovery',
  'actual_originals':len(originals),'actual_original_bytes':sum(r['bytes'] for r in originals),'native_PE_originals':1,'metadata_originals':1,'retained_primary_originals':10,'new_selected_primary_originals':len(PRIMARY),
  'spans':len(spans),'span_bytes':sum(r['bytes'] for r in spans),'span_categories':counts,'instruction_sites':len(sites),'data_sites':len(data),'primary_source_sites':len(primary_sites),'source_sites':len(source_sites),
  'retained':'186 complete4B2010 producer47B, D0 complete69B, selected4A28DC UI bounded131B, S2C6E length7B and five E8 candidates stay retained; no new opcode or producer count.',
  'new_relations':[
   '48C009 action-17 uses incoming DWORD vector priority offsets4,8,0,C first !=FFFFFFFF; 530450 lookup result is not tested before mode1 producer. No result-success/namespace/rights assertion.',
   '48C37F action-17 requires context != stored1478084 localself. Selector3 loads that localself (so fails self inequality); selector>=4 uses selector-4; selector<4 reads local44 unassigned in bounded/full primary setup. Selector2 is separately gated action-12 and cannot enter spectator dispatch. Do not issue identity from undefined local or selector arithmetic.',
   '50D1A8 action4 with input flag1 uses signedWORD selectedECE4 to index20B records and queues recordDWORD E9E4 in mode1. Its list publisher/namespace/current lifecycle is unknown; not D0 WORD by analogy.',
   '547223 mode2/context0 is independently present in actual CN instructions: ownerA97998==1 and [owner+4]+12018 nonzero, recipient producer object=[owner+20]. Immediate localcleanup/A970EC reset does not prove server exit/ACK.',
   'CN435E60 dispatches arg-200; actual event204 sets12018=1 and12024=0, event205 clears12018/1201C and sets12024=1. These local inputlatch events are not battle membership or spectator server authority.',
  ],
  'source_constraints':[
   'Read-only CnSpectator6E decoder admits exact opcode/logical9 and preserves all rawbody8 including three opaque localstack bytes. observed_producer_shape is caller-domain qualification, never identity/rights/ACK.',
   'Only retained4A28DC UI path has D0 WORD-derived targets. Preserve other mode1 rawDWORD domains for separately qualified realCore handling; do not force WORD cast or globally reject foreign context as if all callers were the UI.',
   'Mode2/context0 is actual observed CN producer input, but context0 is not actor0/battle0/unrestricted leave. A97998 producer/current battle and official authoritative namespace remain outside this bounded recovery.',
  ],
  'limits':['No full four caller functions recovered; original full primary C files retained as context but raw complete claims only186 producer/D0. Candidate scan was retained186 producer-containing-section exact E8 scan, not indirect/global call completeness.','No 530450 internals, formatter/glyph/capacity/155 or52F330/52F170 were followed; no native/codecs/runtime executed.','Input reset full primary sources435DC0/4360B0 were read and retained as original source context; they do not claim caller lifecycle/currentness or a new reset algorithm.'],
  'open':{'other_mode1_target_namespace':None,'selected_menu_list_publisher':None,'mode2_A97998_producer':None,'CN_current_battle_issuer':None,'CN_spectator_server_authority':None,'S2C6E_ACK':None},
  'source_before_existing':len(SOURCES),'source_new_absent':2,'source_current_expected':len(SOURCES)+2,'new_cpp':1,'new_opcodes':0,'fully_connected_routes':0,'whole_game_percent':None,
  'execution':{'native':0,'codec':0,'API':0,'build':0,'tests':0,'emulation':0,'DB':0,'SQL':0,'deployment':0},'forbidden_formatter_chain_followed':False,
 }
 emit('findings.json',findings)
 emit('derived-inputs.json',[{'path':f'derived/s{n:02}.json','kind':'file-only static decode of exact CN native PE span'} for n in range(len(spans))])
 print(json.dumps(findings,ensure_ascii=True))

def capture():
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(SOURCES+[HEADER,OWNED])]
 emit('current-source-origins.json',current)
 put(OUT/'README.txt',('188 bounded independent CN6E caller source. ActualPE582f: VA/RVA/fileoffset explicit.\n'
  'Readonly parser exactlogical9/raw8; shape preserves opaquepadding and is no authority.\n'
  'Only186 UI caller is D0WORD-derived. Othermode1 rawDWORD and mode2/context0 separate.\n'
  'Local12018 event204/205 latch is not serverbattle/currentness. Namespaces/issuer remain unknown.\n'
  'ActualPE/metadata/primary originals separate from receipt contexts and static derivatives.\n'
  'No native/codec/API/build/tests/emulation/DB/SQL/deployment. Fullroutes0; percentunknown.\n').encode())
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!='seal.json':
   body=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(body),'sha256':sha(body)})
 emit('seal.json',{'round':188,'members':members,'member_count':len(members),'all_actual_originals_fully_copied':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'sealed_members':len(members),'total_files':len(members)+1,'current_originals':len(current),'current_original_bytes':sum(r['bytes'] for r in current),'pins':[{k:r[k] for k in ('path','bytes','sha256')} for r in current[-2:]]}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('recover','capture'));args=parser.parse_args()
 (recover if args.action=='recover' else capture)()
