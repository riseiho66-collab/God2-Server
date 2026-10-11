"""Actual TW raw whisper-name lineage; bounded file-only static recovery.

No client/server/native/C++/codec/DB/API/build/test/emulation execution.
Native name bytes and wire actor IDs are not common64 ownership authority.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/shared-native-chat-identity-source-01'
OUT=ROUND/'agents/tw-whisper-identity-frontier'
OWNED='tools/reconstruction/tw_native_whisper_identity181.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE='56754835636d95dd9ddbdd5a716c910391ea77f3b33dec8235918b42c3e5dcfc'
BASE=0x400000
SOURCES=[
 'src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
 'src/cn/protocol/CnCharacterSummary.h',
 'src/cn/auth/SharedStoredCharacterSummarySource.h','src/cn/auth/SharedStoredCharacterSummarySource.cpp',
 'src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp',
 'src/protocol/RecoveredRemoteActor.h','src/handlers/RecoveredVisibility.h',
 'src/protocol/RecoveredChat.h','src/game/RecoveredCharacter.h',
 'src/db/RecoveredCharacterRepository.h','src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
]
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/tw_native_chat_source178.py','tools/reconstruction/tw_native_chat_family179.py']
# Exact end offsets exclusive. Retained wire/peer consumers are never new recovery.
SPANS=[
 (0x7DCF0,0x7DD40,'new_complete','nonempty raw selected name -> tab3 -> widget/history; no ID mapping'),
 (0xB2330,0xB23D3,'new_complete','raw target setter dispatches six actual widget modes, private widget +58700'),
 (0x165D0,0x16630,'new_complete','raw name getter: byte-copy max argument and separate NUL, not glyph/renderer'),
 (0xB2A90,0xB2AD6,'new_complete','private target widget getter caller supplies max15; presentation helpers not followed'),
 (0x10F1C0,0x10F262,'new_complete','actual raw private history slot insertion, strlen<72, 32 slots stride72'),
 (0x10F270,0x10F27D,'new_complete','actual selected history raw name accessor, no character identifier'),
 (0xDCF80,0xDD0F2,'new_complete','selected context-action full dispatch; action13 rawname only -> private selector'),
 (0x73A90,0x73AF7,'new_complete','actual list record name+8 -> private selector; upstream category remains OPEN'),
 (0xFAC70,0xFAD19,'new_complete','actual peer-name getter: fullDWORD lookup then raw name+1C/+2C/+3C'),
 (0x66E8A,0x66EC9,'new_bounded','actual actor selection -> peer-name getter -> private selector; enclosing handler not recovered'),
 (0xB2C0A,0xB2C68,'new_bounded','selected private history raw name -> target widget; enclosing handler not recovered'),
 (0xDCAFD,0xDCB35,'new_bounded','external original20-byte records copied to context menu table; upstream issuer remains OPEN'),
 (0x96990,0x96F7C,'retained178','existing complete raw $target/channel/header producer; no new opcode'),
 (0xB2EA5,0xB2F9B,'retained178','existing bounded target15 getter -> private producer caller'),
 (0xB31D1,0xB32A6,'retained179','existing bounded additional typed private input caller'),
 (0xFC2C3,0xFC340,'retained_source_layout','known6F body+1C -> actor raw first name; no new6F producer'),
 (0xFC960,0xFC98A,'retained178','known128-slot actor lookup, fullDWORD field+18, stride0x268'),
 (0x7DDC0,0x7DDFD,'retained178','received private prose-derived history; not authoritative identity'),
 (0xFC1C0,0xFC2C3,'retained_source_layout','known6F EBP=tablebase+18+slot*268, preserves exact firstname destinationbase'),
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def copy(path,name):
 raw=path.read_bytes();put(OUT/name,raw)
 return {'path':path.resolve().as_posix(),'copy':name,'bytes':len(raw),'sha256':sha(raw)}
def current():
 rows=[copy(ROOT/name,f'current/s{n:02d}{Path(name).suffix}') for n,name in enumerate(SOURCES+[OWNED])]
 emit('current-source-origins.json',rows)
 put(OUT/'README.md',('Round181 file-only TW whisper name lineage. Native raw names, actor IDs, common64 identity and codepage are separate domains. '
  'Complete original native input and stable actual source copies retained. Mutable identity/chat/presence sources and root books excluded. '
  'No build/tests/native/codec/DB/API execution. Findings are source qualification evidence, not native server authority or gameplay acceptance.\n').encode())
 seal=[]
 for path in sorted(OUT.rglob('*')):
  if path.is_file():
   raw=path.read_bytes();seal.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
 emit('seal.json',seal)
 print(json.dumps({'current_sources':len(rows),'sealed_members':len(seal),'seal_sha256':sha((OUT/'seal.json').read_bytes())}))

def recover():
 raw=IMAGE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();manifest=json.loads(fresh)
 if sha(raw)!=PIN or sha(fresh)!=BEFORE or len(manifest)!=1294:
  raise RuntimeError('Pinned actual original or freshbefore mismatch; do not replace baseline')
 OUT.mkdir(parents=True,exist_ok=True)
 put(OUT/'root-before.raw',fresh)
 emit('root-lineage.json',{'before_inputs':1294,'before_sha256':BEFORE,'prior180_members':2249,
  'prior_scope':'parent whole-member preservation','baseline_replaced':False})
 lookup={row['path']:row for row in manifest};before=[]
 for n,name in enumerate(SOURCES):
  row=lookup[name];snap=ROUND/row['snapshot'];body=snap.read_bytes()
  if sha(body)!=row['sha256']:raise RuntimeError('Root original before copy changed')
  target=f'before/s{n:02d}{Path(name).suffix}';put(OUT/target,body)
  before.append({'path':(ROOT/name).as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 emit('before-source-origins.json',before)
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'state':'absent in fresh root before','copy':None}])
 emit('original-inputs.json',[copy(IMAGE,'input/native.bin')])
 emit('context-originals.json',[copy(ROOT/name,f'context/c{n:02d}{Path(name).suffix}') for n,name in enumerate(CONTEXT)])
 emit('intermediate-source-origins.json',[copy(ROOT/OWNED,'intermediate/writer-01.py')])
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];allins={}
 for n,(a,z,scope,purpose) in enumerate(SPANS):
  body=raw[a:z];target=f'raw/n{n:02d}.bin';put(OUT/target,body);instructions=[]
  for i in cs.disasm(body,BASE+a):
   row={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}','bytes_hex':i.bytes.hex(),
    'mnemonic':i.mnemonic,'operands':i.op_str}
   instructions.append(row);allins[i.address-BASE]=row
  spans.append({'start_va':f'{BASE+a:08X}','end_exclusive_va':f'{BASE+z:08X}',
   'start_rva':f'{a:08X}','end_exclusive_rva':f'{z:08X}','scope':scope,'purpose':purpose,
   'copy':target,'bytes':len(body),'sha256':sha(body),'instructions':instructions})
 emit('native-spans.json',spans)
 targets=[
 (0x7DD05,'reject empty selected name locally'),(0x7DD0D,'set actual private tab3'),
 (0x7DD1E,'pass exact original selected rawname to widget setter'),(0x7DD35,'insert same rawname into private history'),
 (0xB2332,'actual rawname argument'),(0xB233E,'actual widget mode signedWORD+5BFA4'),
 (0xB234A,'six-entry actual widget dispatch'),(0xB2363,'private raw target widget+58700'),
 (0xB2369,'rawname setter call, presentation callee deliberately not followed'),
 (0x165D2,'actual rawtext begins widget+18'),(0x165DD,'actual max argument'),
 (0x165E8,'compare max bytes against strlen'),(0x165F3,'raw bounded byte copy; no codepage mapping'),
 (0x165FB,'separate destinationNUL at max offset'),(0x1661F,'short source copied includingNUL'),
 (0xB2A9A,'private widget source +58700'),(0xB2AAB,'actual target max0F=15 bytes'),
 (0xB2AB0,'invoke actual rawbyte getter'),(0x10F1D5,'history name strlen limit72'),
 (0x10F1FA,'history duplicate helper remains local not ownership'),(0x10F228,'history slot base3 plus72*index'),
 (0x10F23D,'history copied rawname includingNUL'),(0x10F24C,'history index modulo32'),
 (0x10F272,'selected history indexBYTE+2'),(0x10F278,'selected rawname address'),
 (0xDCF9B,'actual selected signedWORD index'),(0xDCFB2,'separate actual DWORD peer/menuID'),
 (0xDCFB5,'separate actual raw menu-name +40618+20*index'),
 (0xDCFEC,'actual15-entry action dispatch'),(0xDD0C7,'private action passes name pointer only'),
 (0xDD0C8,'private menu action13 invokes47DCF0'),(0x73AB8,'actual selected list entry pointer'),
 (0x73ABF,'actual list name+8'),(0x73AC5,'listname private selector caller'),
 (0xFAC89,'lookup full actual native actorDWORD using retained4FC960'),
 (0xFAC91,'absent actor returnsfalse; no guessed name'),(0xFACA3,'actual peer record stride0x268=616'),
 (0xFACA8,'first actual name+1C'),(0xFACC3,'raw firstname copied unchanged includingNUL'),
 (0xFACE5,'third actualtext field +3C'),(0x66EB1,'selected native actorID argument'),
 (0x66EB4,'actual peer-name getter call'),(0x66EB9,'first getter result at callerlocal60'),
 (0x66EC4,'actual peer rawname to private selection helper'),
 (0xB2C0A,'bounded history branch; preceding handler retained separately'),
 (0xDCB21,'original20-byte external records copied to menu table'),
 (0xFC2C8,'known6F nativeactorID masked12bits; not common64'),
 (0xFC2D0,'known6F stores actual nativeactorID'),(0xFC2EF,'known6F first raw text copying'),
 (0xFC338,'known6F third rawtext copy remainder'),
 (0xFC1CA,'actual known6F EBP=tablebase+18'),
 (0xFC1D8,'actual known6F slot stride268hex=616decimal'),
 (0xFC1DE,'actual known6F 128-slot limit'),(0xFC205,'actualbody pointer argument'),
 ]
 sites=[]
 for a,meaning in targets:
  if a not in allins:raise RuntimeError(f'Instruction site is not captured boundary: {a:X}')
  sites.append(dict(allins[a],meaning=meaning))
 emit('instruction-sites.json',sites)
 data=[]
 for n,(a,count,purpose) in enumerate([(0xB23D4,6,'widget mode1 selects private target+58700'),
   (0xDD0F4,15,'action13 selects private rawname branch4DD0C1')]):
  body=raw[a:a+count*4];target=f'raw/d{n:02d}.bin';put(OUT/target,body)
  data.append({'va':f'{BASE+a:08X}','rva':f'{a:08X}','copy':target,'bytes':len(body),
   'sha256':sha(body),'purpose':purpose,'targets_va':[f'{x:08X}' for x in struct.unpack('<'+'I'*count,body)]})
 emit('data-sites.json',data)
 source_sites=[]
 for name in SOURCES:
  lines=(ROOT/name).read_text(encoding='utf-8-sig').splitlines()
  needles={'src/text/OwnedCharacterNameText.cpp':['from_encoded','from_utf8','codepage','14','encode('],
   'src/text/OwnedCharacterNameText.h':['codepage','identity','normal'],
   'src/game/RecoveredCharacter.h':['uint64_t','profile','name_codepage'],
   'src/protocol/RecoveredRemoteActor.h':['identity()','29u','with_text_fields','15'],
   'src/cn/auth/SharedCommonCharacterSummarySource.cpp':['NameSource','OwnedCharacterNameText','mapping','character.id','profile'],
   'src/cn/auth/SharedStoredCharacterSummarySource.cpp':['common','identity','source','mapping'],
   'src/cn/protocol/CnCharacterSummary.h':['name','16'],
   'src/text/LegacyChineseCodec.cpp':['encode_display','substituted','truncated','encoded="?"'],
   'src/handlers/RecoveredVisibility.h':['CUSTOM','character_id','identity','same','duplicate']}.get(name,[])
  for number,line in enumerate(lines,1):
   if any(needle in line for needle in needles):source_sites.append({'path':name,'line':number,'text':line})
 emit('source-sites.json',source_sites)
 facts={
  'scope':'actual selected/typed/history raw-name lineage; no server native audience or permission',
  'counts':{'spans':len(spans),'span_bytes':sum(x['bytes'] for x in spans),
   'new_complete':sum(x['scope']=='new_complete' for x in spans),
   'new_bounded':sum(x['scope']=='new_bounded' for x in spans),
   'retained':sum(x['scope'].startswith('retained') for x in spans),
   'new_bytes':sum(x['bytes'] for x in spans if x['scope'].startswith('new')),
   'instruction_sites':len(sites),'data_sites':len(data),'source_sites':len(source_sites),
   'source_files':len(SOURCES),'native_originals':1,'new_opcodes':0,'new_game_CPP':0},
  'native_peer_lineage':['known6F logical+29/body+1C -> peer record firsttext+1C',
   'known4FC960 fullDWORD nativeactorID -> 128-slot record stride0x268',
   'new4FAC70 exact firsttext getter -> bounded466EC4 -> new47DCF0',
   '47DCF0 actualprivate tab3, setter4B2330 rawname; eventual496990 raw $target producer retained'],
  'target_domains':{'UI_getter_max_bytes':15,'getter_NUL_extra_bytes':1,
   'history_max_strlen':71,'history_slot_bytes':72,'history_slots':32,
   'common_identity_max_encoded_bytes':14,'native_peer_text_capacity':16,
   'native6F_defensive_server_termination_domain':'15 bytes+NUL, not native reject behavior'},
  'stored_name_boundary':'OwnedCharacterNameText codepage0 unchangedASCII only;936/950 exact decode/encode roundtrip; no script normalization/replacement. Common64 ID comes from explicit actual ownership, never namejoin or 12bitnativeID.',
  'CN_summary_context':'actual explicit ordered common64 mappings and qualified native metadata/current source; CN summary source is not TW native summary proof',
  'next_source_qualification':['actual immutable common64 session/account/character lease',
   'exact stored profile/rawname/codepage and source revision, no display encode_display',
   'actual issuer binding nativewire actor/name publication to samecommon64 identity',
   'complete actual peer text byte equality with profileencoded name for qualifying peer namespace',
   'actual target ownership/current and native private audience independently supplied'],
  'gaps':['typed/manual/receivedprose names are not guaranteed authoritative peer identity',
   'upstream listname+8 category, context-menu external records and server native name uniqueness are OPEN',
   'native CP950 byte-copy path itself supplies no commonstored encoding or codepage proof',
   'native ID/display name/common64 ID namespaces are distinct; no global namejoin/defaultID allocator',
   'widget presentation/layout callee internals and formatter/render/glyph intentionally not followed',
   'no actualTW character-summary common64 linkage is recovered by CN summary source context'],
  'corrections_retained':['exploratory private helper end initially7DD3E truncated ret4; final fullspan ends7DD40',
   'exploratory message said268-byte peer stride; corrected immediately to0x268=616decimal'],
  'executed':{'codec':0,'emulation':0,'build':0,'tests':0,'native':0,'DB':0,'SQL':0,'API':0},
  'whole_game_completion_percent':None,
 }
 emit('findings.json',facts)
 emit('derived-inputs.json',[{'source':'input/native.bin','derived':'native-spans.json','kind':'bounded static Capstone instruction records'},
  {'source':'actual stable C++ originals','derived':'source-sites.json','kind':'literal source-line excerpts, no execution'}])
 put(OUT/'findings.md',('TW native whisper names are raw byte strings. Actual peer-name getter4FAC70 uses known fullDWORD actor lookup and raw record+1C, then actual caller466EC4 chooses that firsttext as a private target. '
  'Known6F writes this same raw text from logical+29; this proves native wire-name lineage, not common64 ownership. '
  'Private target getter accepts15 bytes plusNUL; history accepts71 bytes. Common14 storage qualification is narrower. '
  'Exact commonprofile/codepage/lease/current and actual publication name binding must be supplied by an identity issuer. '
  'Typed names and prose-derived history cannot manufacture such authority. Renderer, formatter, glyph, codecs and server authority remain unrecovered or deliberately unexecuted.\n').encode())
 print(json.dumps(facts['counts']))

def supplement():
 # The first capture retained the raw text copy interval but lacked the actual
 # EBP/tablebase setup bytes. Preserve all former evidence before adding this
 # already-known-layout context; never relabel it as newly recovered opcode.
 raw=IMAGE.read_bytes()
 if sha(raw)!=PIN:raise RuntimeError('Actual original image pin mismatch')
 for name in ['native-spans.json','instruction-sites.json','findings.json']:
  copy(OUT/name,'intermediate/first-'+name)
 copy(ROOT/OWNED,'intermediate/writer-02.py')
 spans=json.loads((OUT/'native-spans.json').read_bytes())
 if len(spans)!=18:raise RuntimeError('Supplement requires exactly preserved original18span capture')
 a,z,scope,purpose=SPANS[-1];body=raw[a:z];target='raw/n18.bin';put(OUT/target,body)
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);instructions=[];lookup={}
 for i in cs.disasm(body,BASE+a):
  row={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}','bytes_hex':i.bytes.hex(),
   'mnemonic':i.mnemonic,'operands':i.op_str};instructions.append(row);lookup[i.address-BASE]=row
 spans.append({'start_va':f'{BASE+a:08X}','end_exclusive_va':f'{BASE+z:08X}',
  'start_rva':f'{a:08X}','end_exclusive_rva':f'{z:08X}','scope':scope,'purpose':purpose,
  'copy':target,'bytes':len(body),'sha256':sha(body),'instructions':instructions})
 sites=json.loads((OUT/'instruction-sites.json').read_bytes())
 for site,meaning in [(0xFC1CA,'actual known6F EBP=tablebase+18'),
  (0xFC1D8,'actual known6F slot stride268hex=616decimal'),
  (0xFC1DE,'actual known6F 128-slot limit'),(0xFC205,'actualbody pointer argument')]:
  sites.append(dict(lookup[site],meaning=meaning))
 facts=json.loads((OUT/'findings.json').read_bytes())
 facts['counts']['spans']=len(spans);facts['counts']['span_bytes']=sum(x['bytes'] for x in spans)
 facts['counts']['retained']=7;facts['counts']['instruction_sites']=len(sites)
 facts['corrections_retained'].append('Additional retained raw6F setup259B captures EBP=tablebase+18; former18span evidence preserved complete, no new opcode or new bytes count')
 for name,value in [('native-spans.json',spans),('instruction-sites.json',sites),('findings.json',facts)]:
  (OUT/name).write_bytes((json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
 print(json.dumps(facts['counts']))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['recover','supplement','capture']);args=parser.parse_args()
 if args.mode=='recover':recover()
 elif args.mode=='supplement':supplement()
 else:current()
