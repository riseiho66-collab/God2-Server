"""190 independent CN35 raw producer and callers; pure file/PE/static decode."""
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
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-source-01'
OUT=ROUND/'agents/cn-battle-command-frontier'
HEADER='src/cn/protocol/CnBattleCommand35.h'
OWNED='tools/reconstruction/cn_battle_command_frontier190.py'
SOURCES=['src/cn/protocol/CnBattleCommandGate.h']
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='97d1f9fb3eb9d6fabb94c88078c014942448a6fbcf690bd759a5b5ca5284aaa3'
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
SECONDARY=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-close-record-source-01/web-peer/epoch2-original-00.md'
PRIMARY={
 '0054ffc0':'a04459ea39f0d0a824d668a7480c5bb1904a64f7420ee642d056449e075d2bd9',
 '0054a9a0':'eedf44c9e4852914555f0ed16d55c8227a9a86b0b4fd38ef409036b13f4b8a53',
 '005471f0':'01db23be31ac77f3b872b5dfb19857221f59b59316405fabe4c16dcca870b34b',
}
SPANS=[
 (0x54FFC0,0x5504B4,'new_complete','whole machine producer body1268B up to terminalret16; excludes table9 and externalcallees'),
 (0x54A9A0,0x54AA9D,'new_complete','whole itemcommand caller253B throughterminalret4; externalinventory getters not recovered'),
 (0x54749C,0x5474C9,'new_bounded','formationkind4 selected caller; writesA97148 from46C-10 then actual actor-return BYTE'),
 (0x5476EA,0x547708,'new_bounded','primarykind3 actual caller with full targetlist pointer and actual actor-return BYTE; terminalshortJMP ends547708'),
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  if path.read_bytes()!=raw:raise RuntimeError('Existing static artifact differs; retain it and use a new epoch/name')
  return
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 raw=path.read_bytes();put(OUT/target,raw)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def recover():
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN or len(before)!=1358 or sha(fresh)!=BEFORE:
  raise RuntimeError('Actual original/freshbefore changed; do not refreshbaseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':190,'before_inputs':1358,'before_sha256':BEFORE,'baseline_replaced':False,'phase':'source/file/static only'})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 originals=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv')]
 primary_sites=[]
 for n,(address,pin) in enumerate(PRIMARY.items()):
  path=RECOVERY/rows[address]['file'];body=path.read_bytes()
  if sha(body)!=pin:raise RuntimeError('Actual primary fullsource changed')
  originals.append(original(path,f'originals/p{n:02}.c'))
  for line,text in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in text.lower() for k in ('0x35,','00481440','0054ffc0','local_18','local_17','local_16','local_14','local_10','local_c','0xa97148','0xa9713a','0xa9713c','0x80','0xe)')):
    primary_sites.append({'path':path.resolve().as_posix(),'line':line,'text':text,'actual_source_sha256':pin,'classification':'retained188_fullprimary_new_selectedcaller' if address=='005471f0' else 'new_selectedfullprimary'})
 emit('original-inputs.json',originals);emit('primary-source-sites.json',primary_sites)
 context=[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)]
 row=original(SECONDARY,'context/web-secondary.md');row['kind']='secondary webpeer handoff, locating lead only; no CN native proof/current pin';context.append(row)
 emit('context-origins.json',context)
 index={r['path']:r for r in before};source_before=[]
 for n,f in enumerate(SOURCES):
  row=index[f];body=(ROUND/row['snapshot']).read_bytes()
  if len(body)!=row['bytes'] or sha(body)!=row['sha256']:raise RuntimeError('Protected before source changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,body)
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 for f in [HEADER,OWNED]:
  if f in index:raise RuntimeError('New source unexpectedly present in before')
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new file absent from freshbefore'})
 emit('before-source-origins.json',source_before)
 if not (OUT/'intermediate-origins.json').exists():
  emit('intermediate-origins.json',[original(ROOT/HEADER,'intermediate/header-refined.h'),original(ROOT/OWNED,'intermediate/writer-01.py')])
 emit('refinement-source-origins.json',[original(ROOT/HEADER,'intermediate/header-final.h'),original(ROOT/OWNED,'intermediate/writer-02.py')])
 emit('static-resume-receipt.json',{'existing_fulloriginals_before_epochs_unchanged':True,'same_byte_existing_writes_reused':True,'partial_s03_33B_retained':'raw/s03.bin','final_s03_30B':'raw/s03-refined.bin','reason':'actual547706 shortJMP ends547708, not54770B; no native/runtime/test execution'})
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 def read(va,size):
  offset=pe.get_offset_from_rva(va-base);return offset,raw[offset:offset+size]
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={};all_instructions=[]
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset,body=read(lo,hi-lo);target=f'raw/s{n:02}-refined.bin' if n==3 else f'raw/s{n:02}.bin';put(OUT/target,body)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(body,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(body):raise RuntimeError('Whole/boundednative span not complete instruction domain')
  emit(f'derived/s{n:02}.json',decoded);all_instructions.extend(decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,'copy':target,'bytes':len(body),'sha256':sha(body),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  total=counts.setdefault(classification,{'spans':0,'bytes':0});total['spans']+=1;total['bytes']+=len(body)
  for i in decoded:
   if i['mnemonic'] in ('call','ret','mov','movsx','movzx','cmp','test','push','lea','or','shl','bts','div','cmovne') or i['mnemonic'].startswith('j'):
    sites.append(dict(i,span=n,classification=classification))
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 offset,body=read(0x5504B4,36);put(OUT/'raw/table9.bin',body)
 table=[{'command_kind':n+4,'target_va':struct.unpack_from('<I',body,n*4)[0],'cell_va':0x5504B4+n*4} for n in range(9)]
 emit('data-sites.json',[{'va':0x5504B4,'rva':0x1504B4,'file_offset':offset,'copy':'raw/table9.bin','bytes':36,'sha256':sha(body),'classification':'new_selected_table9','entries':table}])
 emit('sender-sites.json',[i for i in all_instructions if i['mnemonic']=='call' and i['operands']=='0x481440'])
 emit('field-schema.json',[
  {'body_offset':0,'logical_offset':1,'width':1,'getter':'raw_actor_position','initial_writer':'55004A byte[EBP-14]=BH actual secondarg; no commonidentity inference'},
  {'body_offset':1,'logical_offset':2,'width':1,'getter':'raw_command_kind','initial_writer':'55006B byte[EBP-13]=BL actual firstarg; continuation80 at550259/55030C and resetfinalkind at55025E/550312'},
  {'body_offset':2,'logical_offset':3,'width':1,'getter':'raw_source_slot','initial_writer':'55004D=0 then55005F conditional1 whenA970F8==0 andA970FC!=0; native localflags not authority'},
  {'body_offset':3,'logical_offset':4,'width':1,'getter':'raw_padding','initial_writer':None,'qualification':'no explicit scalar write in selectedproducer; externalhelper/out-of-domain position aliases not proven absent; raw byte retained'},
  {'body_offset':4,'logical_offset':5,'width':4,'getter':'raw_target_field','initial_writer':'550062 DWORDzero; genericbitmask halfWORD updates5501B8; skill-special2WORD550241/550250; helper55D770 pointer path OPEN'},
  {'body_offset':8,'logical_offset':9,'width':4,'getter':'context','initial_writer':'550042 DWORD[EBP-C]=actualowner+3C; no battleID semantic/currentissuer inferred'},
  {'body_offset':12,'logical_offset':13,'width':4,'getter':'operand','initial_writer':'branch-specific[EBP-8], no common zero initialization/default; raw bytes retained'},
 ])
 source_sites=[]
 for f in SOURCES+[HEADER]:
  body=(ROOT/f).read_bytes()
  for n,line in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in line for k in ('Command','Request','raw_','operand','context()','logical_size','decode','parse_logical','0x35')):
    source_sites.append({'path':f,'line':n,'text':line,'actual_source_sha256':sha(body)})
 emit('source-sites.json',source_sites)
 findings={
  'round':190,'scope':'independent CN35 complete producer and itemcaller plus bounded primary3/formation4 caller, no TW inference or externalrule/helper recovery',
  'actual_originals':len(originals),'actual_original_bytes':sum(r['bytes'] for r in originals),'native_PE_originals':1,'metadata_originals':1,'primary_originals':3,'new_selected_primary':2,'retained188_primary':1,
  'spans':len(spans),'span_bytes':sum(r['bytes'] for r in spans),'span_categories':counts,'instruction_sites':len(sites),'data_ranges':1,'data_cells':9,'primary_source_sites':len(primary_sites),'source_sites':len(source_sites),'sender_sites':[0x550277,0x5502CF,0x55032C],
  'new_relations':[
   'Complete54FFC0..5504B4 machineproducer is1268B throughterminalret16; primarymetadata329B is a split extent, not wholealgorithm. Data table5504B4 is nineDWORDtargets, never instructions. All three481440 calls take35,LEA EBP-14,16body bytes =>logical17.',
   'Body0 actualarg2BYTE; body1 arg1BYTE; body2 initialized0 and optionally1 byA970F8/A970FC localflags; body3 no explicitscalar write. Body4 initiallyzero targetfield; body8 initiallyowner+3C DWORD context; body12 branchoperand with no globalzero initialization.',
   'Type4 tableentry5504B4[0]->5500F4 writes operand3-ownerA97148, preservingnativeDWORD arithmetic. Bounded formationcaller54749C writesA97148=owner46C-10 and calls54FFC0 kind4 with actual549750 returnBYTE. NoS88permission/currentactor inference.',
   'Type5/12 operand=(signedbyteA9713C<<24)|unsignedWORDA9713A; type7 actualDWORD A8CBFC; type8 operand=(owner488==0). Other table/default branches can leaveoperand unassigned in this producer; do not replace withzero.',
   'Ordinarynon3/17 branch ORs targetbits using rawposition/14 halfWORD and%14bit. Skill3/17 knownsubkind0/1/3 andspecialFF5 use samebit form or55D770 helper. Skill-kind2 other branch instead encodes owner4A4-selectedBYTE and indexedowner4A9 BYTE as twozeroextendedWORDs. rawtargetfield is not uniformly a mask.',
   'Multi-target skillloops setkind continuation80 before nonfinalsend and reset finalkind. These sequentialnative35 records are not generically duplicatecommands; padding/operand must stayraw.',
   'Complete54A9A0 itemcaller253B consults4C9AE0, scans downward29 torequested signedslot for positive matchingWORD+4, then stores actual selectedslotBYTE/A9713A WORD and calls54FFC0 kind5. Inventorygetter/currentownership/itemuse authority remain OPEN.',
   'Bounded5476EA primarykind3 caller supplies actualowner44C targetlist, retainedcountinECX and actual549750 returnBYTE actor input. Callerupstream andskill authority not recovered by this selectedspan.',
  ],
  'source_constraints':[
   'Readonly CnBattleCommand35 Request owns exact17bytes and exposes rawfield views; decode admits exactopcode35/length only. Unknownrawkind/source/padding/operand survive; known3/4/5 are not assumed total enum.',
   'raw_target_field naming is deliberate: a realAuthority must qualify each actualkind/subkind/continuation domain before interpretingmask or twoWORDencoding. Do not use clientposition ascommonID orcontext asguessedbattleID.',
   'Nativeinputchecks allow actualarg2BYTE<=14 and signedtargetcount<=14, but do not validate everytargetlistposition. Externalhelpers/out-of-domain aliaswrites can affect adjacentlocals; no globalpointer-safety or no-alias-padding guarantee claimed.',
   'Actualserverowner/battle/currentcommandround/targetslots/skills/inventory/formationeligibility andconsume/replay semantics remain requiredsource. Clientlocalflags and senderqueue success are not serverrights.',
  ],
  'limits':['Only producer/itemcaller are newly complete machinefunctions; fullprimary5471F0 was retained188 original and onlytwo new boundedcaller sites interpreted.','55D770 maskhelper,549A70/549750 selectedskill/actor helpers,4C9AE0 inventoryreader andsend481440 internals remain outside trace. No formatter/glyph/render/capacity155 or52F330/52F170 followed.','Webpeer fullhandoff issecondary locatingcontext only. PC/native andbrowserzero-padding policy are not treatedasequal; no webtests/builder/runtime invoked. C56 andS2Cworld35 remain separate directions/contracts.'],
  'open':{'server_battle_current_issuer':None,'actorposition_commonidentity':None,'context_semantic_namespace':None,'targethelper55D770':None,'skill_current_eligibility':None,'inventory_current_eligibility':None,'formation_current_eligibility':None,'official_command_settlement':None,'padding_all_aliases_absent':None},
  'source_before_existing':len(SOURCES),'source_new_absent':2,'source_current_expected':len(SOURCES)+2,'new_cpp':1,'new_opcodes':0,'fully_connected_routes':0,'whole_game_percent':None,
  'execution':{'native':0,'codec':0,'API':0,'build':0,'tests':0,'emulation':0,'DB':0,'SQL':0,'deployment':0},'forbidden_formatter_chain_followed':False,
 }
 emit('findings.json',findings)
 emit('derived-inputs.json',[{'path':f'derived/s{n:02}.json','kind':'Capstone file-only exactCN582f nativeoriginal decode'} for n in range(len(spans))])
 print(json.dumps(findings,ensure_ascii=True))

def capture():
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(SOURCES+[HEADER,OWNED])]
 emit('current-source-origins.json',current)
 put(OUT/'README.txt',('190 independentCN582f C2S35 source-only recovery, logical17/rawbody16.\n'
  'Rawtargetfield may bitmask or2WORD encoding; unknownkind/operand/padding remain original.\n'
  'Initialheader preserved before raw_target_field rename andpaddingalias scope refinement.\n'
  'CompleteactualPE/metadata/primary originals separate from secondaryhandoff andderiveddecode.\n'
  'Noauthority/settlement/currentbattle/ACK claimed; no encoder.\n'
  'No native/codec/runtime/build/tests/API/DB/SQL/deploy. Fullroutes0; percentunknown.\n').encode())
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!='seal.json':
   body=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(body),'sha256':sha(body)})
 emit('seal.json',{'round':190,'members':members,'member_count':len(members),'all_actual_originals_fully_copied':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'sealed_members':len(members),'total_files':len(members)+1,'current_originals':len(current),'current_original_bytes':sum(r['bytes'] for r in current),'pins':[{k:r[k] for k in ('path','bytes','sha256')} for r in current[-2:]]}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('recover','capture'));args=parser.parse_args()
 (recover if args.action=='recover' else capture)()
