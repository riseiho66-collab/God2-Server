"""189 independent CN close helper and retained TW close, file/static only."""
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
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-close-record-source-01'
OUT=ROUND/'agents/native-spectator-close-frontier'
OWNED='tools/reconstruction/native_spectator_close_frontier189.py'
HEADERS=['src/protocol/RecoveredSpectatorClose.h','src/cn/protocol/CnSpectatorClose.h']
SOURCES=['src/protocol/RecoveredSpectator6E.h','src/cn/protocol/CnSpectator6E.h']
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
TW=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
CNPIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
TWPIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
BEFORE='1c7a98ae5abd06ccdfac7d83e41370d6524df074295a6afb20a318d3a779a309'
OLD187=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-ui-publication-source-01/agents/tw-spectator-window-epoch-frontier'
OLD188=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-target-identity-source-01/agents/cn-spectator-request-frontier'
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/tw_spectator_window_epoch187.py','tools/reconstruction/cn_spectator_request_frontier188.py']
PRIMARY={
 '004a1da0':'6a23d2ed53bc1a20025173eeb9d2283bfbbcdcedf905a8ab3815131e4b157ebb',
 '004a25a0':'edd0bf91fc2e47134c5ac0fe32f52a1bf9d4c26c371cb7330d4dea90d3044b7e',
 '004a26e8':'2208f8cdd9051fead85239b2a6ff03eee9d2f1069a40586f6aa68bc496d099ad',
}
SPANS=[
 ('CN',0x4A1DA0,0x4A1E16,'new_complete','independent complete close helper118B: windowflags/modes/pointer-highBYTE body1'),
 ('CN',0x4A25A0,0x4A25C6,'new_bounded','UI caller prologue ownerESI/windowhandle; not whole UI function'),
 ('CN',0x4A266A,0x4A2670,'new_bounded','actual caller inputflags from second stack argument'),
 ('CN',0x4A2670,0x4A26A5,'new_bounded','flagsbit2/selectedhandle/flag10 actual close call4A269B'),
 ('CN',0x4A26A5,0x4A26F1,'new_bounded','flagsbit1/handle/helperresult/action36 actual close call4A26EA'),
 ('TW',0x478C40,0x478CC0,'retained187_complete','complete existing TW close128B; no new TW recovery/opcode'),
]

def sha(body):return hashlib.sha256(body).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 raw=path.read_bytes();put(OUT/target,raw)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def recover():
 cn=EXE.read_bytes();tw=TW.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(cn)!=47541760 or sha(cn)!=CNPIN or len(tw)!=3174400 or sha(tw)!=TWPIN or sha(meta)!=METAPIN or len(before)!=1351 or sha(fresh)!=BEFORE:
  raise RuntimeError('Actual original/freshbefore changed; never refresh baseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':189,'before_inputs':1351,'before_sha256':BEFORE,'baseline_replaced':False,'phase':'file/static only'})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 originals=[original(EXE,'originals/cn.exe'),original(TW,'originals/tw.bin'),original(RECOVERY/'functions.tsv','originals/functions.tsv')]
 primary_sites=[]
 for n,(address,pin) in enumerate(PRIMARY.items()):
  path=RECOVERY/rows[address]['file'];body=path.read_bytes()
  if sha(body)!=pin:raise RuntimeError('Exact primary source changed')
  originals.append(original(path,f'originals/p{n:02}.c'))
  for line,text in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in text.lower() for k in ('004a1da0','0xa3,','0xcb,','0x1c8534','0x1c8536','0x78074','0x4665c','case (tm *)0x36','ustack_8')):
    primary_sites.append({'path':path.resolve().as_posix(),'line':line,'text':text,'actual_source_sha256':pin,'classification':'new_close_primary' if address=='004a1da0' else 'retained186_full_UI_primary_new_selected_relation'})
 emit('original-inputs.json',originals);emit('primary-source-sites.json',primary_sites)
 context=[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)]
 for n,(folder,name) in enumerate([(OLD187,'findings.json'),(OLD187,'seal.json'),(OLD187,'stack-ledger.json'),(OLD188,'findings.json'),(OLD188,'seal.json')]):
  row=original(folder/name,f'context/h{n:02}.json');row['kind']='historical sealed scope/receipt, not current source/native authority';context.append(row)
 emit('context-origins.json',context)
 index={r['path']:r for r in before};source_before=[]
 for n,f in enumerate(SOURCES):
  row=index[f];body=(ROUND/row['snapshot']).read_bytes()
  if len(body)!=row['bytes'] or sha(body)!=row['sha256']:raise RuntimeError('Protected before source changed')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,body)
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 for f in HEADERS+[OWNED]:
  if f in index:raise RuntimeError('New source is present in before unexpectedly')
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new file absent from freshbefore'})
 emit('before-source-origins.json',source_before)
 emit('intermediate-origins.json',[original(ROOT/f,f'intermediate/w{n:02}{Path(f).suffix}') for n,f in enumerate(HEADERS+[OWNED])])
 pe=pefile.PE(data=cn,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 def read(build,va,size):
  offset=va-0x400000 if build=='TW' else pe.get_offset_from_rva(va-base)
  body=(tw if build=='TW' else cn)[offset:offset+size]
  return offset,body
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
 for n,(build,lo,hi,classification,purpose) in enumerate(SPANS):
  offset,body=read(build,lo,hi-lo);target=f'raw/s{n:02}.bin';put(OUT/target,body)
  if build=='TW':
   old=next(r for r in json.loads((OLD187/'native-spans.json').read_text(encoding='utf-8')) if r['va_start']==lo)
   if old['bytes']!=len(body) or old['sha256']!=sha(body):raise RuntimeError('RetainedTW span identity changed')
  decoded=[{'build':build,'va':i.address,'rva':i.address-0x400000,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(body,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(body):raise RuntimeError('Bounded source contains incomplete instruction')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'build':build,'va_start':lo,'va_end':hi,'rva_start':lo-0x400000,'rva_end':hi-0x400000,'file_offset':offset,'copy':target,'bytes':len(body),'sha256':sha(body),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  total=counts.setdefault(classification,{'spans':0,'bytes':0});total['spans']+=1;total['bytes']+=len(body)
  for i in decoded:
   if i['mnemonic'] in ('call','ret','mov','movzx','cmp','test','push','lea','imul','cwde','pop') or i['mnemonic'].startswith('j'):
    sites.append(dict(i,span=n,classification=classification))
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 offset,body=read('CN',0x4A31D8,4);put(OUT/'raw/t00.bin',body)
 emit('data-sites.json',[{'build':'CN','va':0x4A31D8,'rva':0xA31D8,'file_offset':offset,'copy':'raw/t00.bin','bytes':4,'sha256':sha(body),'value':struct.unpack('<I',body)[0],'purpose':'signed action36 exact first dispatch slot ->4A26E8','classification':'new_selected_caller_relation'}])
 # A narrowly retained UI caller region scan; not global/indirect completeness.
 offset,body=read('CN',0x4A25A0,4000);candidates=[]
 for n in range(len(body)-5):
  if body[n]==0xE8 and 0x4A25A0+n+5+struct.unpack_from('<i',body,n+1)[0]==0x4A1DA0:
   candidates.append({'va':0x4A25A0+n,'rva':0xA25A0+n,'file_offset':offset+n,'bytes':body[n:n+5].hex()})
 emit('direct-call-candidates.json',{'scope':'selected4000B UI region4A25A0 only exactE8 scan, not full caller inventory or indirect completeness','candidates':candidates})
 emit('stack-ledger.json',{
  'CN':{'entry_ESP':'S','incoming_ECX':'actual UI pointer P','4A1DA0_PUSH_EBP':'EBP after MOV=S-4','4A1DA3_PUSH_ECX':'P stored[S-8,S-4), EBP=S-4','4A1DA4_PUSH_ESI':'saved ESI below P','4A1DE2_and_4A1E01_LEA_EBP_minus1':'S-5, highestBYTE of saved incomingECX P; independent of callee stack cleanup','body':'one actual pointer-highBYTE; no zero/nonce/epoch/native rights inferred'},
  'TW_retained187':json.loads((OLD187/'stack-ledger.json').read_text(encoding='utf-8')),
 })
 source_sites=[]
 for f in SOURCES+HEADERS:
  body=(ROOT/f).read_bytes()
  for n,line in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in line for k in ('Spectator','spectator','Request','opaque','logical_size','decode','0xa3','0xcb')):
    source_sites.append({'path':f,'line':n,'text':line,'actual_source_sha256':sha(body)})
 emit('source-sites.json',source_sites)
 findings={
  'round':189,'scope':'independent completeCN close helper and two bounded sameUI caller contexts; TW helper retained187; no broad dispatcher/publicationissuer recovery',
  'actual_originals':len(originals),'actual_original_bytes':sum(r['bytes'] for r in originals),'native_originals':2,'native_original_bytes':len(cn)+len(tw),'metadata_originals':1,'primary_originals':3,
  'spans':len(spans),'span_bytes':sum(r['bytes'] for r in spans),'span_categories':counts,'instruction_sites':len(sites),'data_sites':1,'primary_source_sites':len(primary_sites),'source_sites':len(source_sites),
  'new_relations':[
   'CN complete4A1DA0 requires own signedWORD window1C8534>=0 and selected UI record78074+2A08*handle bit20, calls44E7F0 with samehandle, then local4665C mode1 queuesA3/body1 or mode2 queuesCB/body1 through481440. Othermodes return without closepacket.',
   'CN pointer payload source independently proven by prologue PUSH ECX at4A1DA3 and LEA EBP-1 at4A1DE2/4A1E01. Exact opaque byte is highest saved incoming UI pointer byte; do not guesszero or interpret epoch/counter/nonce.',
   '4A269B caller inputflagbit2 requires selected signedWORD1C8536>=0 and selectedrecord flag10. 4A26EA inputflagbit1 requires samehandle>=0,44F070 return nonzero and signedaction36 table4A31D8[0]->4A26E8. Both call samehelper, which adds its ownhandle/flag20/mode requirements.',
  ],
  'retained':'TW187 entire78C40 close128B and precise pointer-highBYTE ledger retainedunchanged; CN UI fullprimary4A25A0/4A26E8 already read186, only new selected bounded caller relations counted. Existing A3/CB opcodes not new packets.',
  'source_constraints':[
   'Independent read-only TW/CN headers accept exact logical2 A3/CB and preserve originalopaque byte. No encoder, no invented paddingzero, no ACK, no inferred spectator/battle permission.',
   'A qualified actual close input may invalidate a service-owned matching publication history under its connection/entry lifecycle. That server action is not proof of the client localwindow epoch, battleexit success, raw pointer identity or authoritative target namespace.',
   'Mode2CB localUI close is not the separate CN6E mode2/context0 battle input; do not merge them by matching numeric2. Localwindow removal alone is not battle lifecycle.',
  ],
  'limits':['44E7F0/44F070 interiors and any formatter/render/glyph/capacity/155/52F330/52F170 are outside trace; bounded UI callsites are not whole UI dispatcher recovery.','Nativehelper slot/windowhandle checks are exactclientconditions, not global server-safe limits; actual serverhistory source/currentissuer still mandatory.','Original primary C files retainedcomplete, including unrelated caller branches, but only selected native rawspans interpreted; no wholesale gameplay/phase semantics claimed.'],
  'open':{'official_server_close_semantics':None,'client_window_epoch_field':None,'server_history_issuer':None,'current_battle_lifecycle':None,'spectator_authority':None,'close_ACK':None},
  'source_before_existing':len(SOURCES),'source_new_absent':3,'source_current_expected':len(SOURCES)+len(HEADERS)+1,'new_cpp':2,'new_opcodes':0,'fully_connected_routes':0,'whole_game_percent':None,
  'execution':{'native':0,'codec':0,'API':0,'build':0,'tests':0,'emulation':0,'DB':0,'SQL':0,'deployment':0},'forbidden_formatter_chain_followed':False,
 }
 emit('findings.json',findings)
 emit('derived-inputs.json',[{'path':f'derived/s{n:02}.json','kind':'file-only static decode; original native build explicitly recorded'} for n in range(len(spans))])
 print(json.dumps(findings,ensure_ascii=True))

def capture():
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(SOURCES+HEADERS+[OWNED])]
 emit('current-source-origins.json',current)
 put(OUT/'README.txt',('189 source-only independent CN A3/CB close and retainedTW187 close.\n'
  'Exactlogical2 rawopaque payload comes from savedUI pointer highBYTE; no zero/epoch/nonce.\n'
  'Nativewindow/mode gates and twoboundedCNcallers are not serverauthority or ACK.\n'
  'Completeactualnative/metadata/primary originals separate from historicalreceipts and derivatives.\n'
  'Newreadonlyheaders2; no runtime/build/tests/native/codec/API/DB/SQL/deploy. Fullroutes0; percentunknown.\n').encode())
 members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!='seal.json':
   body=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(body),'sha256':sha(body)})
 emit('seal.json',{'round':189,'members':members,'member_count':len(members),'all_actual_originals_fully_copied':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'sealed_members':len(members),'total_files':len(members)+1,'current_originals':len(current),'current_original_bytes':sum(r['bytes'] for r in current),'pins':[{k:r[k] for k in ('path','bytes','sha256')} for r in current[2:]]}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('recover','capture'));args=parser.parse_args()
 (recover if args.action=='recover' else capture)()
