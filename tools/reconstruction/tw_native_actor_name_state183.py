"""Actual TW cached actor-name state writer, file/static sources only.

Original native Windows imports are parsed as bytes, never called. No native,
codec/C++/DB/API/build/test/emulation execution or forbidden155-chain followup.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/native-common-actor-name-source-01'
OUT=ROUND/'agents/tw-actor-name-state'
OWNED='tools/reconstruction/tw_native_actor_name_state183.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
IMAGEPIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
EXE=Path('C:/Users/risei/Desktop/God2/God2/God2.unpacked.exe')
EXEPIN='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
BEFORE='c1972084a5d17f328e1ce38beb193364cde4ef79c1372b0a7917dd0d018d616a'
BASE=0x400000
SOURCES=[
 'src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp',
 'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
 'src/protocol/RecoveredRemoteActor.h','src/protocol/RecoveredPlayerAppearanceUpdate.h',
 'src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
 'src/game/RecoveredCharacter.h','src/db/RecoveredCharacterRepository.h',
 'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
 'src/game/SharedPublishedChatNameSource.h','src/game/SharedPublishedChatNameSource.cpp',
 'src/cn/world/SharedActorVisibility.h',
]
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/tw_native_peer_name_binding182.py']
SPANS=[
 (0x131BC0,0x131BEA,'new_complete','actual systemLANGID writer: importedAPI AX -> primary/sub cachedWORDs'),
 (0x131BF0,0x131BF7,'new_complete','complete actualprimary cachedWORD getter; no OS re-query'),
 (0x131C00,0x131C07,'new_complete','complete actualsub cachedWORD getter; no OS re-query'),
 (0x131D90,0x131E2D,'new_bounded','startup argument validation -> actualstate initializer; not complete startupfunction'),
 (0x14A4AD,0x14A4CB,'new_bounded','actual entry-context caller of startupfunction with importedmodulehandle; not wholeCRT entry'),
 (0x131C10,0x131C2D,'retained182','actual cachedprimary4/sub2 selector, already recovered182'),
 (0x695C8,0x69767,'retained182','actual6F wirebit25 vs cachedselector and in-place adaptation callers; no conversioncallee followup'),
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 raw=path.read_bytes();put(OUT/target,raw)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def pe(raw):
 address=struct.unpack_from('<I',raw,0x3C)[0];optional=address+24
 count=struct.unpack_from('<H',raw,address+6)[0];size=struct.unpack_from('<H',raw,address+20)[0]
 sections=[]
 for n in range(count):
  a=optional+size+40*n;vs,va,rs,rp=struct.unpack_from('<IIII',raw,a+8)
  sections.append({'name':raw[a:a+8].split(b'\0',1)[0].decode('ascii'),
   'rva':va,'virtual_bytes':vs,'raw_bytes':rs,'raw_offset':rp})
 def offset(rva):
  for row in sections:
   if row['rva']<=rva<row['rva']+max(row['virtual_bytes'],row['raw_bytes']):
    return row['raw_offset']+rva-row['rva']
  return rva
 return address,optional,sections,offset

def import_record(raw,iat):
 address,optional,sections,offset=pe(raw);rva,size=struct.unpack_from('<II',raw,optional+104)
 cursor=offset(rva)
 while any(raw[cursor:cursor+20]):
  oft,timestamp,forward,name,ft=struct.unpack_from('<IIIII',raw,cursor)
  nameoffset=offset(name);dll=raw[nameoffset:raw.index(0,nameoffset)].decode('ascii');index=0
  while True:
   slot=offset((oft or ft)+4*index);thunk=struct.unpack_from('<I',raw,slot)[0]
   if not thunk:break
   if ft+4*index==iat:
    if thunk&0x80000000:raise RuntimeError('Required import has onlyordinal; do not guess itsidentity')
    hintoffset=offset(thunk);nameend=raw.index(0,hintoffset+2)+1
    return {'dll':dll,'name':raw[hintoffset+2:nameend-1].decode('ascii'),
     'PE_header_offset':address,'import_directory_rva':rva,'import_directory_bytes':size,
     'descriptor_file_offset':cursor,'descriptor_rva':rva+cursor-offset(rva),
     'original_first_thunk_rva':oft,'first_thunk_rva':ft,'slot_index':index,
     'IAT_rva':iat,'IAT_va':BASE+iat,'lookup_slot_rva':(oft or ft)+4*index,
     'lookup_slot_file_offset':slot,'hint_name_rva':thunk,'hint_name_file_offset':hintoffset,
     'hint_name_bytes':nameend-hintoffset,'sections':sections}
   index+=1
  cursor+=20
 raise RuntimeError('Actual inputPE does not carry requiredIAT proof')

def recover():
 native=IMAGE.read_bytes();exe=EXE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();manifest=json.loads(fresh)
 if sha(native)!=IMAGEPIN or len(native)!=3174400 or sha(exe)!=EXEPIN or sha(fresh)!=BEFORE or len(manifest)!=1306:
  raise RuntimeError('Exact original inputs/freshbefore differ; never rewrite baseline')
 OUT.mkdir(parents=True,exist_ok=True);put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'before_inputs':1306,'before_sha256':BEFORE,'baseline_replaced':False,
  'prior182_agent_seal':'c3417572cb97f86ae6dd21bd3a28fc51e97c10419dddbd53f566fae2d724e14c',
  'prior_seal_scope':'retained historicalreceipt, not currentnative/server authority'})
 previous=ROOT/'artifacts/integration/packet-connections-20261006/native-published-chat-identity-source-01/agents/tw-peer-name-binding-frontier/seal.json'
 put(OUT/'epoch/prior182-seal.raw',previous.read_bytes())
 lookup={row['path']:row for row in manifest};before=[]
 for n,name in enumerate(SOURCES):
  row=lookup[name];raw=(ROUND/row['snapshot']).read_bytes()
  if sha(raw)!=row['sha256']:raise RuntimeError('Root preserved before sourceoriginalchanged')
  target=f'before/s{n:02d}{Path(name).suffix}';put(OUT/target,raw)
  before.append({'path':(ROOT/name).as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)})
 emit('before-source-origins.json',before)
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'copy':None,'state':'absent in fresh root before'}])
 emit('original-inputs.json',[original(IMAGE,'inputs/native.bin'),original(EXE,'inputs/unpacked.exe')])
 emit('context-originals.json',[original(ROOT/name,f'context/c{n:02d}{Path(name).suffix}') for n,name in enumerate(CONTEXT)])
 emit('intermediate-source-origins.json',[original(ROOT/OWNED,'intermediate/writer-01.py')])
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];allinstructions={}
 for n,(a,z,scope,purpose) in enumerate(SPANS):
  raw=native[a:z];target=f'raw/n{n:02d}.bin';put(OUT/target,raw);instructions=[]
  for i in cs.disasm(raw,BASE+a):
   row={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}','bytes_hex':i.bytes.hex(),
    'mnemonic':i.mnemonic,'operands':i.op_str};instructions.append(row);allinstructions[i.address-BASE]=row
  spans.append({'start_va':f'{BASE+a:08X}','end_exclusive_va':f'{BASE+z:08X}',
   'start_rva':f'{a:08X}','end_exclusive_rva':f'{z:08X}','scope':scope,'purpose':purpose,
   'copy':target,'bytes':len(raw),'sha256':sha(raw),'instructions':instructions})
 emit('native-spans.json',spans)
 sites=[]
 for site,meaning in [
  (0x131BC0,'actual Windows importcall; API is not executed'),
  (0x131BC6,'cache actual importedreturn AX as WORD6F4CA8'),
  (0x131BCC,'read DWORD from cache beforelow10mask; upperbits irrelevant aftermask'),
  (0x131BD2,'actualprimaryLANGID extraction AND03FF'),
  (0x131BD8,'actualunsigned AX shift10 -> subLANGID'),
  (0x131BDC,'actual primarywriter WORD59DFD8'),
  (0x131BE3,'actual subwriter WORD59DFDA'),
  (0x131BF0,'actual primarycache read getter returnsAX withoutOS re-query'),
  (0x131C00,'actual subcache read getter returnsAX withoutOS re-query'),
  (0x131D90,'startup function begins largeactual stackframe'),
  (0x131DA6,'actual startup thirdargument commandline pointer'),
  (0x131DCA,'empty startup commandline skips initializer and returns'),
  (0x131DF6,'actual sscanf formatpointer literal59E09C; callee internals notfollowed'),
  (0x131DFB,'actual startup commandline supplied tobounded parsecall'),
  (0x131E0E,'actual originalparse call only, no formatting/155chain followup'),
  (0x131E16,'startup parse returncount comparedwith3'),
  (0x131E19,'count>=3 qualifies actualinitializer callsite'),
  (0x131E28,'only observed directE8 initializer caller in full mappedtext scan'),
  (0x14A4B7,'actual entrycontext supplied commandline argument'),
  (0x14A4BC,'actual importedmodulehandle call source, no WindowsAPI execution'),
  (0x14A4C3,'actual entrycontext startupcaller531D90'),
  (0x131C10,'retained182 primarycache4 comparison'),
  (0x131C1A,'retained182 subcache2 comparison'),
  (0x131C24,'retained182 exact4/2 returnsfullEAX1'),
  (0x131C2A,'retained182 allother cache states return0'),
  (0x695F6,'retained182 actual6F usescachedselector atreceive time'),
  (0x695FF,'retained182 wirebit25 extracted fromactualpacked firstDWORD'),
  (0x69605,'retained182 comparewirebit to currentcachedselector'),
  (0x69607,'retained182 same state skips allnameadaptation'),
  (0x6962D,'retained182 differentstate calls52F330; never enterthatcallee'),
  (0x696C3,'retained182 inversestate calls52F170; never enterthatcallee'),
 ]:
  if site not in allinstructions:raise RuntimeError(f'Uncaptured actual instruction boundary {site:X}')
  sites.append(dict(allinstructions[site],meaning=meaning))
 emit('instruction-sites.json',sites)
 imports=[import_record(exe,0x170394),import_record(exe,0x170458)]
 if imports[0]['name']!='GetSystemDefaultLangID':raise RuntimeError('Actual import identity is not expectedsource; retain unknown')
 emit('import-relations.json',imports)
 data=[]
 def datum(raw,a,z,source,purpose,rva=None):
  body=raw[a:z];target=f'raw/d{len(data):02d}.bin';put(OUT/target,body)
  data.append({'source_original':source,'file_offset':a,'copy':target,'bytes':len(body),'sha256':sha(body),
   'rva':rva,'va':None if rva is None else BASE+rva,'purpose':purpose,'raw_hex':body.hex()})
 datum(native,0x19DFD8,0x19DFDC,'inputs/native.bin','original mappedprimary/sub cachebytes4/1; not currentruntime observation',0x19DFD8)
 datum(native,0x2F4CA8,0x2F4CAC,'inputs/native.bin','original cachedLANGIDWORD0 beforeactualsource reinit; not Current',0x2F4CA8)
 formatend=native.index(0,0x19E09C)+1
 datum(native,0x19E09C,formatend,'inputs/native.bin','literal startup parse format only, notnativepermission',0x19E09C)
 datum(native,0x17F394,0x17F398,'inputs/native.bin','historicaloriginalname-thunkbytes; no guessedOFT/IAToffset mapping',0x17F394)
 _,_,sections,offset=pe(exe)
 for record in imports:
  datum(exe,record['descriptor_file_offset'],record['descriptor_file_offset']+20,'inputs/unpacked.exe','actualPEimportdescriptor bindingOriginalLookup toIAT',record['descriptor_rva'])
  datum(exe,record['lookup_slot_file_offset'],record['lookup_slot_file_offset']+4,'inputs/unpacked.exe','actual selectedimport lookup slot atproved ordinalindex',record['lookup_slot_rva'])
  datum(exe,record['hint_name_file_offset'],record['hint_name_file_offset']+record['hint_name_bytes'],'inputs/unpacked.exe','actualhint/importname rawbyte identity',record['hint_name_rva'])
 for rva in [0x19DFD8,0x2F4CA8]:
  a=offset(rva);datum(exe,a,a+4,'inputs/unpacked.exe','compiledcache initialbytes are originalonly, never loadedcurrent proof',rva)
 a=offset(0x131BC0);datum(exe,a,offset(0x131BEA),'inputs/unpacked.exe','same actual42B initializer instruction bytes as pinnedmappedimage',0x131BC0)
 emit('data-sites.json',data)
 emit('source-byte-relations.json',[{'native_copy':'raw/n00.bin','original_PE_initializer_file_offset':a,
  'original_PE_initializer_bytes':42,'native_SHA256':sha(native[0x131BC0:0x131BEA]),
  'original_PE_initializer_SHA256':sha(exe[a:offset(0x131BEA)]),
  'scope':'actualraw source relation only, not build/native execution or fullPE equality'}])
 refs=[]
 for address in [0x59DFD8,0x59DFDA,0x6F4CA8]:
  needle=struct.pack('<I',address);start=0x1000;hits=[]
  while True:
   found=native.find(needle,start,0x170000)
   if found<0:break
   hits.append(found);start=found+4
  refs.append({'absolute_operand_va':f'{address:08X}','literal_file_offsets':hits,
   'scope':'full original mappedtext RVA1000..170000 literalcandidate scan; not allaliases/indirectwriters proof'})
 for target in [0x531BC0,0x531BF0,0x531C00,0x531D90]:
  hits=[]
  for a in range(0x1000,0x170000-5):
   if native[a]==0xE8 and BASE+a+5+struct.unpack_from('<i',native,a+1)[0]==target:hits.append(a)
  refs.append({'target_va':f'{target:08X}','direct_E8_candidates_rva':hits,
   'scope':'literalE8 targets inspected atcaptured actualboundaries, not completeindirectcall closure'})
 emit('xref-candidates.json',refs)
 source_sites=[]
 patterns={'src/cn/world/SharedActorVisibility.h':['TaiwanRawNameState','source_revision','actual_global_word','receiving observer','current;'],
  'src/game/SharedPublishedChatNameSource.cpp':['native_name_page','taiwan_globals','actual_global_word','source_revision','native_encoded','no script','Current'],
  'src/game/SharedWorldPresence.h':['uint64_t','generation','actor_handle','DB character','ready_characters'],
  'src/text/OwnedCharacterNameText.cpp':['14','from_encoded','from_utf8','encode('],
  'src/game/RecoveredCharacter.h':['uint64_t','profile','name_codepage'],
  'src/protocol/RecoveredRemoteActor.h':['identity()','with_text_fields','15','runtime_emission_enabled']}
 for name in SOURCES:
  for number,line in enumerate((ROOT/name).read_text(encoding='utf-8-sig').splitlines(),1):
   if any(word in line for word in patterns.get(name,[])):source_sites.append({'path':name,'line':number,'text':line})
 emit('source-sites.json',source_sites)
 counts={'spans':len(spans),'span_bytes':sum(row['bytes'] for row in spans),
  'new_complete':sum(row['scope']=='new_complete' for row in spans),'new_bounded':sum(row['scope']=='new_bounded' for row in spans),
  'new_bytes':sum(row['bytes'] for row in spans if row['scope'].startswith('new')),
  'retained':sum(row['scope'].startswith('retained') for row in spans),'instruction_sites':len(sites),
  'data_sites':len(data),'source_sites':len(source_sites),'original_native_inputs':2,'actualsource_files':len(SOURCES),
  'new_CPP':0,'new_opcodes':0,'complete_native_gameplay_routes':0}
 facts={'counts':counts,
  'actual_writer':'531BC0 calls proved kernel32.dll!GetSystemDefaultLangID atIAT570394, storesAXLANGID, maskslow10primary, shiftsAX10sub, writesWORD59DFD8/59DFDA',
  'raw_initial_values':'actualcompiledWORDs4/1, cachedrawLANGID0; before-init originals do not proveAPI success/currentruntime',
  'startup_scope':'actual531D90 boundedentry: emptycommandline returns; original sscanfcall format %s %s %d %d %s requiresreturn>=3 tocall531BC0 at531E28',
  'entry_scope':'actual54A4C3 call to531D90 in boundedentrycontext; this is not completeCRT/startup/lifetime recovery',
  'cached_state':'531BF0/531C00 getters and retained531C10 readstoredWORDs only; selector neverrefreshesSystemLANGID',
  'actual_state_math':{'source_width':'APIreturn AX16bits','primary':'LANGID&0x03FF','sub':'LANGID>>10',
   'after_known_initializer_domain':'primary<=03FF/sub<=003F derivesfromactualwriter only; do not imposeallreceiver statebounds orfillState automatically'},
  'identity_obligations':['realreceivingclient cached-word observation/initializer result epoch plusgenuinecurrentissuer',
   'never substitute currentserverhost OS language, userUI/threadlocale, Sessionlanguage, displaypreference, codepage orfont',
   'no OS-requery assumption: changedOSlanguage doesnot proveexistingnativecache hasrefreshed',
   'native low12actor/fullDWORD lookup namespace remains separatefrom common64 owner/lease/fullpublication',
   'actual6F rawdomain stillwirebit25==cached531C10 return; adaptedpostname issuer remainsOPEN',
   'keep common14/native15/history72 domains and owner-requiredtext conversion, no namealiases/defaultstate'],
  'closed_targeted_gap':'actualdirect writer/import and boundedstartupcaller sources ofthetwoWORDs havebeenrecovered',
  'gaps':['indirect/alias writes and complete initialization/reinitialization lifecycle are notprovedby literaltextscan',
   'true receivingclient currentcachedwords/epoch and server-visibleauthenticatedstate supplier remainOPEN',
   'textstatewords are not codepage/permissions/ordinaryplayer classification ornative server6F producer',
   'differentselector adaptation52F330/52F170 exactpostname andcodec/glyph/formatter/render closure deliberately remainOPEN',
   'commandline parsingcallee and unrelatedstartup/CRT controls notfollowed; no completeapplicationboot claim'],
  'original_provenance':'149c wholemapped image and independentlypinned5fcf wholeexistingunpackedPE retained separately; rebuiltimports proveIAT identity, not currentresolvedDLLaddress',
  'corrections':['initial exploratory startupcandidate531D40 wasjustret; actual initializer caller functionstart531D90',
   'mappedPE currentimportdirectory302FAC cannot alone identify oldIAT170394; actualunpacked rebuilt importdescriptor proveskernel32 name mapping'],
  'prior_baselines':'182 rawspans/seal/rootbefore retained; no oldevidence relabel/rewrite',
  'executed':{'native':0,'WindowsAPI':0,'codec':0,'build':0,'tests':0,'C++':0,'DB':0,'SQL':0,'emulation':0},
  'whole_game_completion_percent':None}
 emit('findings.json',facts)
 emit('derived-inputs.json',[{'sources':['inputs/native.bin','inputs/unpacked.exe'],'derived':['native-spans.json','import-relations.json','data-sites.json','xref-candidates.json'],'kind':'file-only staticPE/Capstone extraction'},
  {'sources':'actualstable C++ originals','derived':'source-sites.json','kind':'literal sourcelines, no C++ execution'}])
 put(OUT/'findings.md',('Actual state initializer531BC0 uses proved GetSystemDefaultLangID import, caches16bit LANGID and writesprimary/sub WORDs. '
  'The boundedstartup caller only invokes it after nonemptycommandline/parsecount>=3. Compileddefaults4/1 are preserved, not promoted toloadedcurrent. '
  'Cached getters and531C10 do not queryOS again. A genuine receivingclient cache/lifecycle observation remainsmandatory; serverhost/userUI/Sessionlocale/font cannot standin. '
  'This closes targeteddirect writer/source provenance while leavingindirect/reinit/current/rawadaptedname/nativeauthority scopesOPEN. '
  'No52F330/52F170 internals or155chain followed; no native/API/codec/build/tests/DB execution.\n').encode())
 print(json.dumps(counts))

def capture():
 rows=[original(ROOT/name,f'current/s{n:02d}{Path(name).suffix}') for n,name in enumerate(SOURCES+[OWNED])]
 emit('current-source-origins.json',rows)
 put(OUT/'README.md',('Round183 actual native twoWORD writer provenance; source/static only. '
  'Whole149c mappednative image and5fcf existingunpackedPE originals retained separately from derivedcode/import records. '
  'Actualstable source-current copies taken afterparentBATCHFINAL; no rootbooks/catalog/reports/artifactreceipts currentpins. '
  'Original182seal retainedhistorical only. Native state/current and entiregameplay acceptance are distinct.\n').encode())
 members=[]
 for path in sorted(OUT.rglob('*')):
  if path.is_file():
   raw=path.read_bytes();members.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
 emit('seal.json',members)
 print(json.dumps({'sealed_members':len(members),'seal_sha256':sha((OUT/'seal.json').read_bytes()),
  'current_source_originals':len(rows),'tool_bytes':len((ROOT/OWNED).read_bytes()),'tool_sha256':sha((ROOT/OWNED).read_bytes())}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['recover','capture']);args=parser.parse_args()
 if args.mode=='recover':recover()
 else:capture()
