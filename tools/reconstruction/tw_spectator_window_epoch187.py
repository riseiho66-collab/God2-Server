"""Bounded TW spectator UI reset/window epoch source; files and Capstone only.

Exactly two initializer callers, one necessary window-close helper; no full
dispatcher, clock/renderer/formatter internals, native or codec execution.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-ui-publication-source-01'
OUT=ROUND/'agents/tw-spectator-window-epoch-frontier'
OWNED='tools/reconstruction/tw_spectator_window_epoch187.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE='4bd04968a085573630848601024f740b49f5e72fcb513b0efdac6c044ab45f13'
BASE=0x400000
SOURCES=['src/protocol/RecoveredSpectator6E.h','src/protocol/RecoveredTaiwanServerRecords.h',
         'src/protocol/RecoveredWorldRecords.h']
HISTORY=[
 'artifacts/integration/packet-connections-20261006/shared-native-world-transport-source-01/agents/tw-spectator-source-frontier',
 'artifacts/integration/packet-connections-20261006/native-world-transport-host-composition-01/agents/tw-spectator-target-publication',
 'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01/agents/cn-spectator-native-frontier',
]
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/tw_native_spectator_entry184.py',
 'tools/reconstruction/tw_native_spectator_targets185.py',
 'tools/reconstruction/cn_native_spectator_frontier186.py']+[f'{f}/{name}' for f in HISTORY for name in ('findings.json','seal.json')]
SPANS=[
 (0x78EF0,0x78F3C,'new_bounded','first actual initializer caller: F7 prefix resets thenUI89E3C=2; no whole function claim'),
 (0x81B8F,0x81B9D,'new_bounded','second actual initializer caller in same-owner bulk UI call group; no whole dispatcher claim'),
 (0x69DD0,0x69DE2,'new_bounded','actual worldF7 bodypointer and UI owner call78EF0'),
 (0x78C40,0x78CC0,'expanded_prior_read_complete_helper','complete window-close helper locally read185; precise savedECX-highBYTE body ledger newly qualified'),
 (0x77850,0x778E0,'retained185','existing bounded reset prefix zeroing50records and invalidating two targetarrays; not new recovery'),
 (0x1300,0x1306,'retained169_length','existing fixed F7 logical1025 leaf'),
 (0x7B535,0x7B551,'retained184','existing mode1 UI entry requires89E3C=1 and89BD6=1'),
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
 raw=IMAGE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=3174400 or sha(raw)!=PIN or len(before)!=1333 or sha(fresh)!=BEFORE:
  raise RuntimeError('Exact actual native/freshbefore differs; do not rewrite baseline')
 put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'round':187,'before_inputs':1333,'before_sha256':BEFORE,'baseline_replaced':False,'phase':'source/static only'})
 emit('original-inputs.json',[original(IMAGE,'originals/native-image.bin')])
 context=[]
 for n,f in enumerate(CONTEXT):
  row=original(ROOT/f,f'context/c{n:02}{Path(f).suffix}')
  row['kind']='historical finding/seal receipt, not current native/source authority' if f.startswith('artifacts/') else 'complete original policy/retained source context'
  context.append(row)
 emit('context-origins.json',context)
 index={r['path']:r for r in before};source_before=[]
 for n,f in enumerate(SOURCES):
  row=index[f];body=(ROUND/row['snapshot']).read_bytes()
  if len(body)!=row['bytes'] or sha(body)!=row['sha256']:raise RuntimeError('Protected actual source before differs')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,body)
  source_before.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 source_before.append({'path':(ROOT/OWNED).resolve().as_posix(),'present':False,'reason':'new tool absent from freshbefore'})
 emit('before-source-origins.json',source_before);emit('intermediate-origins.json',[original(ROOT/OWNED,'intermediate/writer-01.py')])
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  body=raw[lo:hi];target=f'raw/s{n:02}.bin';put(OUT/target,body)
  decoded=[{'va':i.address,'rva':i.address-BASE,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(body,BASE+lo)]
  if sum(len(bytes.fromhex(r['bytes'])) for r in decoded)!=len(body):raise RuntimeError('Actual bounded raw span does not end on complete instruction')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'rva_start':lo,'rva_end':hi,'va_start':BASE+lo,'va_end':BASE+hi,'file_offset':lo,
                'copy':target,'bytes':len(body),'sha256':sha(body),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  total=counts.setdefault(classification,{'spans':0,'bytes':0});total['spans']+=1;total['bytes']+=len(body)
  for row in decoded:
   if row['mnemonic'] in ('call','ret','mov','lea','push','cmp','test','sub','add','rep stosd') or row['mnemonic'].startswith('j'):
    sites.append(dict(row,span=n,classification=classification))
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 table_sites=[]
 for rva,purpose in [(0x6B5D4+0xF7*4,'actualF7 world target69DD0'),(0x1324+0xF7*4,'retainedF7 fixed1025 lengthleaf1300')]:
  body=raw[rva:rva+4];target=f'raw/t{len(table_sites):02}.bin';put(OUT/target,body)
  table_sites.append({'rva':rva,'va':BASE+rva,'bytes':4,'copy':target,'sha256':sha(body),
                      'classification':'retained_known_table_new_selected_relation','purpose':purpose,'value_va':struct.unpack('<I',body)[0]})
 emit('data-sites.json',table_sites)
 callers=[]
 for rva in range(0x1000,0x170000-5):
  if raw[rva]==0xE8 and rva+5+struct.unpack_from('<i',raw,rva+1)[0]==0x77850:
   callers.append({'rva':rva,'va':BASE+rva,'bytes':raw[rva:rva+5].hex()})
 emit('direct-call-candidates.json',{'scope':'exactE8 target scan over mapped native code range; not indirect-call completeness','target_rva':0x77850,'candidates':callers})
 ledger={
  'entry_ESP':'S','initial_ECX':'actual UI this pointer P',
  '78C40_push_ECX':'ESP=S-4; original P DWORD stored at[S-4,S)',
  '78C41_push_ESI':'ESP=S-8; original ESI DWORD stored at[S-8,S-4)',
  '78C79_window_close_call':'507BB0 is thiscall with one pushed signedhandle; normal ret4 restores ESP=S-8; callee internals remain outside trace',
  '78C88_and_78CAC_body_address':'LEA[ESP+7] -> S-1, the highest BYTE of saved original ECX P',
  'body_byte_qualification':'not assigned as an independent payload field; it is not wholly uninitialized stack. Exact value depends on actual saved UI pointer highBYTE; never replace it with guessed zero/nonce/epoch.',
  'wire_queue':'C2SA3 for local89E3C=1, C2SCB for=2; sender4132E0 gets body1. No queued client epoch counter in this complete helper.',
 }
 emit('stack-ledger.json',ledger)
 source_sites=[]
 for f in SOURCES:
  body=(ROOT/f).read_bytes()
  for n,line in enumerate(body.decode('utf-8-sig').splitlines(),1):
   if any(k in line for k in ('Spectator','spectator','context()','native_lengths','/*F0*/')):
    source_sites.append({'path':f,'line':n,'text':line,'actual_source_sha256':sha(body)})
 emit('source-sites.json',source_sites)
 findings={
  'round':187,'scope':'two initializer callers plus necessary expanded close helper; no full dispatcher/open/page recovery',
  'native_originals':1,'native_original_bytes':len(raw),'spans':len(spans),'span_bytes':sum(r['bytes'] for r in spans),
  'span_categories':counts,'instruction_sites':len(sites),'data_sites':len(table_sites),'source_sites':len(source_sites),
  'direct_call_candidates':callers,
  'new_relations':[
   'TW world F7 table entry6B5D4+F7*4 ->69DD0 ->78EF0. F7 original fixed logical1025 is retained169 grammar, not a new opcode. This prefix calls77850 then writes UI89E3C=2.',
   'After reset the bounded78EF0 prefix reads rawbody4/body8, calls547EB0 with a local pointer, subtracts the subsequently read local value from body8 and writes local89E38, then calls78E20. No timestamp/nonce meaning or native clock call result is recovered; no C2S queue in this prefix. Rest of78EF0 remains outside trace.',
   'Second selected caller81B91 resets the same ESI owner amidst a bulk UI call group. Its boundedspan has no network epoch material; entire enclosing function and its upstream phase remain OPEN.',
   'F7-created local UI mode2 is distinct from the retained mode1 spectator branch requiring89E3C=1 and89BD6=1. F7 receipt therefore cannot independently establish that branch current or its authoritative battle membership.',
  ],
  'expanded_relation': 'Complete78C40 close helper was locally read185. On qualified signedwindowhandle and selected UI flag20, it calls507BB0; mode1 queuesA3/body1, mode2 queuesCB/body1. Precise prologue/LEA stack ledger shows bodybyte is highest saved ECX byte, not a counter or an entirely unwritten stack byte.',
  'retained': '77850 prefix zeroes50*60B and fills two50-DWORD arrays FFFFFFFF; retained185, not new. UI mode1 predicate retained184. No D0/CD/6E or other known opcodes recounted.',
  'source_constraints':[
   'A service can process an actually qualified A3/CB event under its own connection/UI owner generation and invalidate its own supplied publication history. This is server policy tied to a concrete input event, not proof of the client reset count, window incarnation, battle epoch or accepted spectator rights.',
   'No independent client UI epoch counter, request nonce or reset acknowledgement is established here. Do not derive one from pointer highBYTE, local89E38 arithmetic, a local reset call, F7 mode2, or context0 of the separate battle6E path.',
   'An actual history issuer still must retain exact entry/current UI owner, D0 target publication, CD updates, reset/replacement lifecycle and authoritative target mapping/currentbattle. Generic local UI cleanup is not server battle state.',
  ],
  'correction_notes': 'Before the first owned writer, preliminary close-body description was corrected using actual stack prologue: PUSH ECX stores the byte addressed by ESP+7. Existing sealed184/185/186 evidence is untouched.',
  'open':{'client_UI_epoch_field':None,'server_independent_reset_observation':None,'mode1_open_page_causal_proof':None,
          'current_history_issuer':None,'target_battle_namespace':None,'spectator_authority':None},
  'new_cpp':0,'new_opcodes':0,'fully_connected_routes':0,'whole_game_percent':None,
  'source_before':len(SOURCES),'source_current_expected':len(SOURCES)+1,
  'execution':{'native':0,'codec':0,'build':0,'tests':0,'API':0,'DB':0,'deployment':0},
  'forbidden_formatter_chain_followed':False,
 }
 emit('findings.json',findings);emit('derived-inputs.json',[{'path':f'derived/s{n:02}.json','kind':'static Capstone decode of exact original native raw span'} for n in range(len(spans))])
 print(json.dumps(findings,ensure_ascii=True))

def capture():
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(SOURCES+[OWNED])]
 emit('current-source-origins.json',current)
 put(OUT/'README.txt',('187 bounded actual TW UI window/reset source. VA=400000+RVA; mapped file offset=RVA.\n'
  'Exactly two77850 directcaller contexts, expanded necessary closehelper and retained reset/grammar/predicate.\n'
  'No native UI epoch/counter/nonce or spectator authority established. F7 mode2 differs from spectator mode1 UI.\n'
  'A3/CB bodybyte qualified as highBYTE of saved incomingECX, never guessed zero or version.\n'
  'Original native/source/before inputs separate from historical reports/seals and static derivatives.\n'
  'No game C++ edits/build/tests/native/codec/API/DB/deploy. Fullroutes0; wholegamepercent unknown.\n').encode())
 members=[]
 for path in sorted(OUT.rglob('*')):
  if path.is_file() and path.name!='seal.json':
   body=path.read_bytes();members.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(body),'sha256':sha(body)})
 emit('seal.json',{'round':187,'members':members,'member_count':len(members),'all_actual_originals_fully_copied':True})
 body=(ROOT/OWNED).read_bytes()
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'sealed_members':len(members),'total_files':len(members)+1,
  'current_originals':len(current),'current_original_bytes':sum(r['bytes'] for r in current),'tool_bytes':len(body),'tool_sha256':sha(body)}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('recover','capture'));args=parser.parse_args()
 (recover if args.action=='recover' else capture)()
