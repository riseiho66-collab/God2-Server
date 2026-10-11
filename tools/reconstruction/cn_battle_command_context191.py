"""191 CN battle context lineage; pure file/PE/Capstone source capture only."""
from pathlib import Path
import argparse, csv, hashlib, io, json, struct
import capstone, pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-group-source-01'
OUT=ROUND/'agents/cn-battle-command-context'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='c404b8c0d8a12061cb79fbe0a30c256e921826478880dcf8f6d15a96ddf6e6b3'
HEADER='src/cn/protocol/CnBattleContext82.h'
OWNED='tools/reconstruction/cn_battle_command_context191.py'
STABLE=['src/cn/protocol/CnBattleCommandGate.h','src/cn/protocol/CnBattleCommand35.h']
PRIMARY=['0048da20','0048a4d0','0048aa10','0048fcc0','0054a320','0054cd80',
 '00551d50','0054ffc0','00549750','00549770','0054f360','0055fe30',
 '00543d40','00543f30','0054b370','0054b9b0','0054f5a0','00546c00','00546b30']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/cn_native_frame_clock_delivery.py',
 'tools/reconstruction/cn_battle_round_gate_delivery.py',
 'tools/reconstruction/cn_battle_scalar_update_delivery.py',
 'tools/reconstruction/cn_native_chat_recipient180.py',
 'tools/reconstruction/cn_world_return_state_frontier_delivery.py',
 'tools/reconstruction/cn_battle_command_frontier190.py']
# Former full functions retain their bytes; only the selected relation is new.
SPANS=[
 (0x48DA20,0x48DA42,'retained','world owner plus EBP-9F0 T stored at bundle[1] EBP-A14'),
 (0x48DAA0,0x48DAC8,'retained','phase3 pointer passes to48A4D0, actual phase return stored'),
 (0x48DDFD,0x48DE0F,'retained','phase4 actual battle owner ECX and bundle EBP-A18 passed to54A320'),
 (0x48A508,0x48A511,'retained','frame actual input pointer saved EBP-220'),
 (0x48A77A,0x48A78A,'retained','same pointer passed to48AA10; actual return phase compared3'),
 (0x48AA3D,0x48AA56,'retained','actual input T saved EBP-148'),
 (0x48B177,0x48B18A,'retained','T passed to48FCC0 and native returned phase compared4'),
 (0x48B222,0x48B22C,'retained','native localphase4 after receiving82'),
 (0x48BD04,0x48BD51,'retained','local phase EAX return8, no permission inferred'),
 (0x48FCC0,0x48FCDF,'retained','world fullrecord consumer saves T argument EBP-9A0'),
 (0x4921E8,0x492231,'retained','S82 twoDWORD copy toT+28/+2C plus cleanup and localphase4'),
 (0x54A320,0x54A32D,'new_bounded','initializer actual inputbundle and battle owner ECX/ESI'),
 (0x54A404,0x54A497,'new_bounded','bundle[1]→T, raw B lowBYTE FF qualifier, contextA/B copies, FB DWORD material and actor51/52 resetFFFF'),
 (0x549750,0x54976A,'new_complete','actual actor selector: secondary only when primaryflag0 and secondary nonzero; else primary including neither'),
 (0x549770,0x5497A4,'new_complete','selected raw side/type BYTE64/68, primary takes precedence, neither asserts andreturns0; no authority'),
 (0x54CD80,0x54CFEC,'retained','old50 complete86/5 writer; conditionalflags andactor nibbles, clock/display calls not followed'),
 (0x552117,0x552134,'retained','old49/50 battle86 subtype selector table'),
 (0x55236B,0x552378,'retained','old50 fullrecord EBX→54CD80 with sameowner'),
 (0x550392,0x5503D3,'retained','190 command consumption clears primary first, else secondary; last setsF4=1'),
 (0x567BA8,0x567BAF,'retained','S82 fixed logical9 leaf from prior native length grammar'),
 (0x567B9A,0x567BA1,'retained','S86 fixed logical17 leaf independent of C35'),
]
DATA=[(0x492BE0,4,'world82 dispatch→4921E8'),(0x567EAC,4,'S82 length→567BA8'),
 (0x567EBC,4,'S86 length→567B9A'),(0x5525E4,4,'battle86 subtype5→55236B'),
 (0x48E08C,4,'worldphase3→48DAB2'),(0x48E090,4,'worldphase4→48DAC8')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  if path.read_bytes()!=raw:raise RuntimeError('Existing epoch differs; preserve and use a new name')
  return
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 raw=path.read_bytes();put(OUT/target,raw)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def recover():
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN or len(before)!=1365 or sha(fresh)!=BEFORE:raise RuntimeError('Original/before changed; no refresh')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':191,'before_inputs':1365,'sha256':BEFORE,'baseline_replaced':False,'phase':'file/static source only'})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv')];primary=[]
 for n,a in enumerate(PRIMARY):
  p=RECOVERY/rows[a]['file'];r=original(p,f'originals/p{n:02}.c');inputs.append(r)
  for line,text in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(k in text.lower() for k in ('0048fcc0','0048a4d0','0048aa10','0054a320','0x82:','0xa970f8','00a970f8','00a970fc','local_a18','local_9f4','local_14c','param_1[0xf]','param_1[0x10]','0x51','0x52','00549750','00549770','0054cd80','0x86:')):
    primary.append({'path':r['path'],'line':line,'text':text,'sha256':r['sha256'],'interpretation':'selected raw native proof remains required; decompiler does not supply server authority'})
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]])
 emit('primary-source-sites.json',primary)
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 index={r['path']:r for r in before};captured=[]
 for n,f in enumerate(STABLE):
  r=index[f];b=(ROUND/r['snapshot']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('Protected source before changed')
  target=f'before/b{n:02}.h';put(OUT/target,b);captured.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)})
 for f in [HEADER,OWNED]:
  if f in index:raise RuntimeError('New source in protected before')
  captured.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new source absent from freshbefore'})
 emit('before-source-origins.json',captured)
 emit('initial-source-origins.json',[original(ROOT/HEADER,'initial/header.h'),original(ROOT/OWNED,'initial/writer.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 def read(va,size):
  offset=pe.get_offset_from_rva(va-base);return offset,raw[offset:offset+size]
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset,b=read(lo,hi-lo);target=f'raw/s{n:02}.bin';put(OUT/target,b)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(b,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(b):raise RuntimeError('Selected static span incomplete')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,'copy':target,'bytes':len(b),'sha256':sha(b),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  c=counts.setdefault(classification,{'spans':0,'bytes':0});c['spans']+=1;c['bytes']+=len(b)
  for i in decoded:sites.append(dict(i,span=n,classification=classification))
 data=[]
 for n,(va,size,purpose) in enumerate(DATA):
  offset,b=read(va,size);target=f'raw/d{n:02}.bin';put(OUT/target,b)
  data.append({'va':va,'rva':va-base,'file_offset':offset,'copy':target,'bytes':size,'sha256':sha(b),'value':struct.unpack('<I',b)[0],'classification':'retained_table_entry_new_selected_relation','purpose':purpose})
 emit('native-spans.json',spans);emit('instruction-sites.json',sites);emit('data-sites.json',data)
 emit('source-field-relations.json',[
  {'record':'S82','logical_size':9,'body_size':8,'rawA':'DWORD logical+1','rawB':'DWORD logical+5','receiver':'4921EE/1F1,4921F4/1F7 into actual T+28/+2C','phase':'native local4 only'},
  {'relation':'sameT pointer','chain':['48DA36/3C bundle[1]=T atEBP-9F0','48DAB2/BBA→48A4D0','48A508/50B→48A77C/782','48AA45/50→48B177/180','48FCD3/D9→4921E8','48B222→48BD04','48DE03/0A→54A326/40C','54A459/45C→owner3C,54A45F/462→owner40','190550042→C35 body8'],'permission_inferred':False},
  {'record':'S86/5','logical_size':17,'source':'55236B sameowner/fullrecord→54CD80','rawflag':'logical3 bits1/2','actor':'logical4 low/high nibble conditionalwritesowner51/52','absentbits_clear':False,'duration':'retained clock relation usesactualpriorA97130, not logicalWORD5'},
  {'selector':'549750','secondary_when':'ownerA970F8==0 AND ownerA970FC!=0','otherwise':'owner51 including neitherflag; not permission','type_selector':'549770 returnsrawowner64 forprimary; else68 forsecondary; elseassert+0 clientonly'},
  {'actor_reset':'54A491 WORDowner51=FFFF after FB DWORD material copy','flag_reset':'no A970F8/FC zero initialization proved by selected initializer; bulk/alias lifecycle OPEN'},
  {'consumption':'190550392..5503D3 clearsprimaryfirst else secondary; ifnootherflag setsF4=1','cancellation':'54F360 menu reset doesnotexplicitlyclearA970F8/FC; missing globalalias/lifecycle remainsOPEN'},
 ])
 cpp=[]
 for f in STABLE+[HEADER]:
  r=(ROOT/f).read_bytes()
  for line,text in enumerate(r.decode('utf-8-sig').splitlines(),1):
   if any(k in text for k in ('logical','context','raw_','primary_','secondary_','requested_','decode','parse_','bytes_')):cpp.append({'path':(ROOT/f).resolve().as_posix(),'line':line,'text':text,'sha256':sha(r)})
 emit('cpp-source-sites.json',cpp)
 findings={'round':191,'phase':'static source only','new_cpp':1,'modified_cpp':0,'gate_modified':False,'native_span_counts':counts,'native_spans':len(spans),'native_bytes':sum(r['bytes'] for r in spans),'instruction_sites':len(sites),'data_sites':len(data),'primary_sites':len(primary),'cpp_source_sites':len(cpp),'original_inputs':len(inputs),'original_bytes':sum(r['bytes'] for r in inputs),'new_opcodes':0,'complete_gameplay_routes':0,'whole_game_percent':None,'builds_tests_runtime_codec_database':0,
  'proven':['S82 actual logical9 two complete rawDWORD bytes; readonly ownedrecord preserves allbytes.','Same native T pointer survives frame/worldreceiver/localphase4 entry bundle into battleowner3C/40; firstDWORD is190C35 context source.','549750 and549770 actual complete selected-leaf branches qualify actor/type source, including noflags fallback which doesnot grant rights.','S86/5 flag/actor writer andC35 localconsumption retained old50/190; missingbits keep history.'],
  'limits':['Existing whole48DA20/48A4D0/48AA10/48FCC0/551D50 andold50 gate/190command code are retained even though samepointer/82 relation is newly interpreted; no repeat newbyte accounting.','54A320 is bounded13+147B; whole initializer1517B and unrelatedasset/render loops not closed. Selected19 fullprimary originals include conservative falselead context; copycounts are not recovered algorithm counts.','Native phase4, owner3C context, slot/type, localassert fallback and86 flags are clientstate. Realserver issuer/battleidentity/commonbinding/grant/current/settlement remainOPEN.','No complete proof of allalias orbulk writes to flags; initializer resets actorbytes but cannot automatically initialize flags0 or recover globalcancellation.','No TW/web/CUSTOM authority, no stopped155/52F330/52F170 interiors; no nativeexecution/codec/build/test/runtime/API/SQL/DB.']}
 emit('findings.json',findings)
 emit('gaps.json',[
  {'gap':'Server context namespace/issuer','known':'actualS82rawA→C35context', 'next_source':'actual authoritative battle owner supplier must bind exact rawcontext/history/native actor to common identity; client doesnot establish this'},
  {'gap':'Complete flags lifecycle/cancel','known':'86conditionalset and190commandconsume; actorinitializerFFFF','next_source':'qualify actualowner initialepoch, priorflags and allcancellation/bulk/alias writes; selectedmenu reset not enough'},
  {'gap':'Full command legality','known':'actor selector proven actualrawBYTE','next_source':'native selectedskill549A70,targethelper55D770,item4C9AE0 and real costs/current remain outside191; never retry155'}])
 put(OUT/'README.md',b'# CN battle context source 191\n\nFile/PE/Capstone only. Full original inputs are listed separately from derived disassembly. New source is readonly82; existing Gate unchanged. SameT lineage is proven, server authority is not. No gameplay routes, deployment or acceptance claimed. Finalseal only after root BATCHFINAL.\n')
 print(json.dumps(findings,ensure_ascii=True))

def capture(seal):
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(STABLE+[HEADER,OWNED])]
 emit('current-source-origins.json',current)
 if seal:
  members=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.name!='seal.json':
    r=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(r),'sha256':sha(r)})
  emit('seal.json',{'round':191,'members':members,'member_count':len(members),'current_originals':len(current),'native_originals':1,'complete_gameplay_routes':0,'whole_game_percent':None})
  r=(OUT/'seal.json').read_bytes();print(json.dumps({'seal_sha256':sha(r),'members':len(members),'files_with_seal':len(members)+1,'current':current}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--capture',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args()
 if a.recover:recover()
 if a.capture:capture(a.seal)
