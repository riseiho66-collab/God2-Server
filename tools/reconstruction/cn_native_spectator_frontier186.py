"""Bounded independent CN D0/CD/spectator source, PE and primary C file reads only.

No client/native/codec/API/C++/Lua/emulation/build/tests/DB/SQL/deployment.
TW opcode meanings are not an input to CN dispatch or operand recovery.
"""
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
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01'
OUT=ROUND/'agents/cn-spectator-native-frontier'
OWNED='tools/reconstruction/cn_native_spectator_frontier186.py'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METADATA='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='8200c1fca67e3d2d2b4c42714c0b294e953481731060e78f9bf3a645275529aa'
SOURCES=['src/cn/protocol/CnWorldConsumerRecords.h','src/protocol/RecoveredSpectator6E.h',
         'src/protocol/RecoveredTaiwanServerRecords.h']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
         'tools/reconstruction/cn_receiver_owner_frontier169.py',
         'tools/reconstruction/cn_native_chat_recipient180.py',
         'tools/reconstruction/tw_native_spectator_targets185.py']
PRIMARY={
 '0048fcc0':'f02edff5a139bc883d3c935b1e2ebe5b30cfc8de48668bad14c0b1ff3bedb1ac',
 '005485f0':'aeb431740bc58d539946a80ead20309ebebff1c94ea7d129b1820314f348111d',
 '004a31f0':'07df66fcce2066b54077e0048abd5594e930c8e71f67d356bd8538963af73063',
 '004a3ec0':'ad6486e69072f424dfccb4f057627ae5d65e1757f2369cc7ee3f6bde0baa89f8',
 '004a25a0':'edd0bf91fc2e47134c5ac0fe32f52a1bf9d4c26c371cb7330d4dea90d3044b7e',
 '004a26e8':'2208f8cdd9051fead85239b2a6ff03eee9d2f1069a40586f6aa68bc496d099ad',
 '004a2110':'eeaff3ff455cf02a2b3b4627999d023fc109e248023eb3f24edf7686474a363c',
 '004b2010':'fce29112726d45c277e045b074fa0c83967768b107ed8200595614aff2bfc9fc',
 '00481170':'f6e83b21cb4c7a1987f8e8d181b38a19b732e3111be66ff2f3014232fa42d956',
 '00567b50':'e36cb24767fe9ef3385c9021a26bc49c551ade77b19c1bf98ab4e0f32b831ecf',
}
SPANS=[
 (0x4A31F0,0x4A3326,'new_complete','CN complete CD consumer, flags and two22B copies; no targetarray writes'),
 (0x4A3EC0,0x4A3F05,'new_complete','CN complete D0 consumer, twoWORD zeroextensions and exactflagbits'),
 (0x4B2010,0x4B203F,'new_complete','CN complete C2S6E producer body8 with nonnegativecontext, rawpadding unwritten'),
 (0x49118B,0x4911B3,'new_bounded','CN actual world CD/D0 bodypointer and UI owner member calls'),
 (0x4A2863,0x4A28E6,'new_bounded','CN UI two rows of rawtargetDWORDs and lowflagbits2 to producer'),
 (0x4A2110,0x4A21B8,'new_bounded','CN initialization fields and three fill-call preparations; not whole initializer or fillcallee'),
 (0x48FD51,0x48FD6D,'retained_dispatch','known world direct opcode table range and jump; not whole receiver'),
 (0x548659,0x548677,'retained_dispatch','known battle selector and target table; not whole receiver'),
 (0x490AB1,0x490AC4,'retained_dispatch','world defaultconsume header with actual47E8D0 call'),
 (0x548906,0x548916,'retained_dispatch','battle defaultconsume header with actual47E8D0 call'),
 (0x567B50,0x567B69,'retained_length','known CN length resolver range and direct table'),
 (0x567C1F,0x567C26,'retained_length','CD fixed65 leaf independently read from CN table'),
 (0x567BE0,0x567BE7,'retained_length','D0 fixed7 leaf independently read from CN table'),
 (0x567B93,0x567B9A,'retained_length','S2C6E fixed5 leaf, distinct from C2S6E body8'),
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
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METADATA or len(before)!=1325 or sha(fresh)!=BEFORE:
  raise RuntimeError('Exact CN/metadata/freshbefore changed; do not replace baseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':186,'before_inputs':1325,'before_sha256':BEFORE,'baseline_replaced':False,'phase':'source/static only'})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 originals=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv')]
 selected=[];primary_sites=[]
 for address,pin in PRIMARY.items():
  row=rows[address];path=RECOVERY/row['file'];body=path.read_bytes()
  if sha(body)!=pin:raise RuntimeError('Exact selected primary decompiler source changed')
  originals.append(original(path,f'originals/{address}.c'));selected.append(row)
  for n,line in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in line.lower() for k in ('0x452b5','0x45279','0x4624c','0x46314','0x46248','0x46310','0x6e,','case 0xcd:','case 0xd0:','004b2010','004a3ec0','004a31f0')):
    primary_sites.append({'path':path.resolve().as_posix(),'line':n,'text':line,'actual_source_sha256':pin})
 emit('original-inputs.json',originals);emit('selected-primary-metadata.json',selected);emit('primary-source-sites.json',primary_sites)
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 index={r['path']:r for r in before};source_before=[]
 for n,f in enumerate(SOURCES):
  row=index[f];body=(ROUND/row['snapshot']).read_bytes()
  if len(body)!=row['bytes'] or sha(body)!=row['sha256']:raise RuntimeError('Protected source before changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,body)
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 source_before.append({'path':(ROOT/OWNED).resolve().as_posix(),'present':False,'reason':'new file absent from freshbefore'})
 emit('before-source-origins.json',source_before);emit('intermediate-origins.json',[original(ROOT/OWNED,'intermediate/writer-01.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 def read(va,size):
  offset=pe.get_offset_from_rva(va-base);return offset,raw[offset:offset+size]
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset,body=read(lo,hi-lo);target=f'raw/s{n:02}.bin';put(OUT/target,body)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(body,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(body):raise RuntimeError('Actual span is not complete-instruction bounded')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,
                'copy':target,'bytes':len(body),'sha256':sha(body),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  total=counts.setdefault(classification,{'spans':0,'bytes':0});total['spans']+=1;total['bytes']+=len(body)
  for i in decoded:
   if i['mnemonic'] in ('call','ret','mov','movzx','movups','cmp','test','and','or','xor') or i['mnemonic'].startswith('j'):
    sites.append(dict(i,span=n,classification=classification))
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 table_sites=[];relations=[]
 def table(va,size,purpose):
  offset,body=read(va,size);target=f'raw/t{len(table_sites):02}.bin';put(OUT/target,body)
  value=body[0] if size==1 else struct.unpack('<I',body)[0]
  table_sites.append({'va':va,'rva':va-base,'file_offset':offset,'copy':target,'bytes':size,'sha256':sha(body),
                      'classification':'retained_known_table_new_selected_relationship','purpose':purpose,'value':value})
  return value
 for op in (0xCD,0xD0,0x6E):
  world=table(0x4929D8+4*op,4,f'world opcode{op:02X}')
  selector=table(0x548D98+op,1,f'battle selector opcode{op:02X}')
  length=table(0x567CA4+4*op,4,f'length opcode{op:02X}')
  relations.append({'opcode':op,'world_target_va':world,'battle_selector':selector,'battle_target_va':struct.unpack('<I',read(0x548C9C+4*selector,4)[1])[0],'length_leaf_va':length})
 table(0x548C9C+4*62,4,'shared battle selector62 default target')
 emit('data-sites.json',table_sites);emit('selected-opcode-relations.json',relations)
 section=next(s for s in pe.sections if s.VirtualAddress<=0x4B2010-base<s.VirtualAddress+s.Misc_VirtualSize)
 calls=[]
 for offset in range(section.PointerToRawData,section.PointerToRawData+section.SizeOfRawData-5):
  if raw[offset]==0xE8:
   va=base+section.VirtualAddress+offset-section.PointerToRawData
   if va+5+struct.unpack_from('<i',raw,offset+1)[0]==0x4B2010:calls.append({'va':va,'rva':va-base,'file_offset':offset,'raw':raw[offset:offset+5].hex()})
 emit('direct-call-candidates.json',{'scope':'exactE8 byte scan in the original producer-containing section; not an exhaustive instruction/indirect caller proof','candidates':calls})
 source_sites=[]
 for f in SOURCES:
  body=(ROOT/f).read_bytes()
  for n,line in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in line for k in ('Spectator','spectator','context()','native_lengths','/*C0*/','/*D0*/','CnWorldConsumerRecord')):
    source_sites.append({'path':f,'line':n,'text':line,'actual_source_sha256':sha(body)})
 emit('source-sites.json',source_sites)
 findings={
  'round':186,'scope':'independent CN D0/CD world/battle and bounded UI to C2S6E, no inherited TW semantics',
  'actual_originals':len(originals),'actual_original_bytes':sum(r['bytes'] for r in originals),
  'native_PE_originals':1,'primary_function_originals':len(PRIMARY),'metadata_originals':1,
  'spans':len(spans),'span_bytes':sum(r['bytes'] for r in spans),'span_categories':counts,
  'instruction_sites':len(sites),'data_sites':len(table_sites),'primary_source_sites':len(primary_sites),'source_sites':len(source_sites),
  'new_relations':[
   'CN own world4929D8 CD->49118B->4A31F0 and D0->49119F->4A3EC0, body=record+1 and this=main+89B26C. These concrete call/operand relationships independently resemble TW but are not inferred from equal opcode values.',
   'CN D0 zeroextends unsigned WORD body2/body4 to UI DWORD arrays46248/46310 +4*body0. One-based slots1..50 correspond arrays4624C/46314 at slot-1. Flag45279+60*slot gets (old&FE)|2. No slot bounds or target identity validation in the complete69B function.',
   'CN CD uses body4 one-based index and body1 selector0/1/2. It independently updates452B5 flags with the same actual bitoperations and copies two22B opaque fields at452C0/452D6; metadata452B8/452BC comes from body8/C. It does not write the two D0 targetarrays.',
   'Actual bounded4A2863..4A28E6 selects arrays by17*page463DC plus control14..24 or25..35, rejects DWORDFFFFFFFF and requires record452B5 low2bits2, then calls4B2010 with mode1. Complete4B2010 builds6E plus8rawbodybytes, signednegative context suppressed and three local padding bytes not written.',
   'CN battle548D98 selectors for CD/D0/6E are62 and jump548C9C[62] to548906 default consume. CN world6E goes490AB1 default consume. No target publication or6E ACK relation is proven in those phase-default paths.',
  ],
  'retained':[
   'Known native length grammar gives CD65,D07 and S2C6E5 from actualCN567CA4 leaves. C2S6E logical9 comes from the separate actualproducer, not the S2C length table; no new opcode count.',
   'World/battle receiver and length dispatch roots were recovered in prior work; this round retains the exact bounded roots/leaves and selected table cells instead of claiming complete new dispatchers.',
  ],
  'limits':[
   'Initializer4A2110..4A21B8 is only a bounded call-preparation prefix: it supplies zero/3000 at452B4 and FF/200 at each array to74FC50, matching primary C memset representation. Fillcallee interiors and the rest of initialization are outside trace; no loaded runtime reset/current proof.',
   'Primary decompiler functions can have split metadata extents. Only CD310B,D069B,C2S6E47B are labeled newly complete machine functions; UI/world/battle raw ranges are expressly bounded, despite full original C files being retained.',
   'FFFF WORD becomes0000FFFF; the UI only rejectsFFFFFFFF, so no guessedFFFF invalid-target sentinel or native safe slot cap. Slot1..50 is a qualified future source domain, not native rejection behavior.',
   'Neither D0 words nor CD metadata prove native actor/room/battle/common64 identity. Retain exact recipient publication, raw slot and WORD operands, UI owner/entry incarnation and update/reset lifetime; require an actual identity/currentbattle issuer.',
  ],
  'open':{'CN_target_namespace':None,'CN_current_entry_issuer':None,'CN_spectator_server_authority':None,'CN_D0_to_battle_entry_causal_proof':None,'S2C6E_ACK':None},
  'source_before':len(SOURCES),'source_current_expected':len(SOURCES)+1,'new_cpp':0,'new_opcodes':0,'fully_connected_routes':0,'whole_game_percent':None,
  'execution':{'native':0,'codec':0,'API':0,'build':0,'tests':0,'emulation':0,'DB':0,'deployment':0},
  'forbidden_formatter_chain_followed':False,
 }
 emit('findings.json',findings);emit('derived-inputs.json',[{'path':f'derived/s{n:02}.json','kind':'static decode of exact retained native original span'} for n in range(len(spans))])
 print(json.dumps(findings,ensure_ascii=True))

def capture():
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(SOURCES+[OWNED])]
 emit('current-source-origins.json',current)
 put(OUT/'README.txt',('186 file/static CN counterpart source. Native PE file offsets differ from VA/RVA; each span/table records all three.\n'
  'Full CN PE + primary C/metadata originals separate from derived decode and repository source context.\n'
  'CN actual D0/CD world consumers and UI-to6E producer recovered independently; namespace/currentissuer still unknown.\n'
  'No game C++ edits, new opcode or connected route. No native/codec/API/build/tests/emulation/DB/deploy.\n').encode())
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!='seal.json':
   b=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b)})
 emit('seal.json',{'round':186,'members':members,'member_count':len(members),'all_actual_originals_fully_copied':True})
 tool=(ROOT/OWNED).read_bytes()
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'sealed_members':len(members),'total_files':len(members)+1,
  'current_originals':len(current),'current_original_bytes':sum(r['bytes'] for r in current),'tool_bytes':len(tool),'tool_sha256':sha(tool)}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('recover','capture'));args=parser.parse_args()
 (recover if args.action=='recover' else capture)()
