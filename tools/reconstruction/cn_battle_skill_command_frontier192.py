"""192 selected CN skill record and target helper; file/PE/Capstone only."""
from pathlib import Path
import argparse, csv, hashlib, io, json, struct
import capstone, pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-data-source-01'
OUT=ROUND/'agents/cn-battle-skill-command-frontier'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
RESOURCE=EXE.parent/'Data2/Fight/Spg/cbspec2.bin'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
METAPIN='491dda9b838fe9d89bb3c8c80e466348a58f48bb61e5472f784aaadd19574449'
RESOURCEPIN='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004'
BEFORE='9daea736af7dd6bfb890e0e197d31072d64d5cba75f21aa6ee2bd7aa22df1ae2'
HEADER='src/cn/protocol/CnBattleSkillDefinition.h'
OWNED='tools/reconstruction/cn_battle_skill_command_frontier192.py'
STABLE=['src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp',
 'src/cn/protocol/CnBattleCommand35.h','src/cn/protocol/CnBattleContext82.h']
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'docs/research/cn-native-skill-catalog-source-20261008.md',
 'docs/research/cn-battle-deferred-consumer-20261007.md',
 'tools/reconstruction/cn_native_skill_catalog_source_delivery.py',
 'tools/reconstruction/cn_battle_deferred_consumer_delivery.py',
 'tools/reconstruction/cn_battle_command_frontier190.py',
 'tools/reconstruction/cn_battle_command_context191.py']
PRIMARY=['00549a70','00553920','00553a50','0055d770','0054ffc0',
 '00553670','00553830','00553a00','00553a90','005539b0']
SPANS=[
 (0x549A70,0x549AAB,'new_complete','selected signed slot fromownerA8CBFC; actuallookup secondary onlywhenprimaryflag0+secondarynonzero; calls553A50/553920 not commonID'),
 (0x553920,0x553955,'new_complete','secondary selectorBYTE2D10<3, signed index bounds actualcount2D64, pointerlist2D28; doesnotprove catalog writer'),
 (0x553A50,0x553A82,'retained','olddeferred primary selectorBYTE4<=15, signedindex actualcount10, pointerlistDC'),
 (0x55D770,0x55D8BD,'new_complete','complete local targethelper333B beforealignment/table; metadata50B describesentryisland only; actualswitch fivebranches plusunsigneddefaultret; externalassert not followed'),
 (0x54FFC0,0x5504B4,'retained','190 completeproducer1268B, actualskillkind03/17hex, operandidentity, nonuniformtarget andcontinuations; no re-count'),
]
DATA=[(0x55D8C0,20,'five targethelper branchaddresses'),(0x55D8D4,17,'mode1..17 byte branchselector')]
DATA += [(0x7F69E8+k*0x44,0x44,f'actual targettable rowmode{k}, full68bytes') for k in (6,7,8,9,10,15)]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  if path.read_bytes()!=raw:raise RuntimeError('Existing epoch differs; preserve and use a new epoch')
  return
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 b=path.read_bytes();put(OUT/target,b)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)}

def recover():
 raw=EXE.read_bytes();meta=(RECOVERY/'functions.tsv').read_bytes();resource=RESOURCE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
 if len(raw)!=47541760 or sha(raw)!=PIN or sha(meta)!=METAPIN or len(resource)!=112660 or sha(resource)!=RESOURCEPIN or len(before)!=1373 or sha(fresh)!=BEFORE:raise RuntimeError('Actualoriginal/before changed; no baseline refresh')
 put(OUT/'epoch/root-before.raw',fresh);emit('epoch.json',{'round':192,'before_inputs':1373,'before_sha256':BEFORE,'baseline_replaced':False,'phase':'file/static only'})
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RESOURCE,'originals/cbspec2.bin')];primary=[]
 for n,a in enumerate(PRIMARY):
  p=RECOVERY/rows[a]['file'];r=original(p,f'originals/p{n:02}.c');inputs.append(r)
  for line,text in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   if any(k in text.lower() for k in ('00553920','00553a50','0055d770','0x2d28','0x2d64','0xdc','0xa8cbfc','00a8cbfc','0x17','local_c','0x45','puvar6','7f69e8','7f6a19')):
    primary.append({'path':r['path'],'line':line,'text':text,'sha256':r['sha256'],'interpretation':'decompiler lead; raw instruction/table proof required'})
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]])
 emit('primary-source-sites.json',primary)
 emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
 index={r['path']:r for r in before};captured=[]
 for n,f in enumerate(STABLE):
  r=index[f];b=(ROUND/r['snapshot']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('Protected before differs')
  target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,b);captured.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(b),'sha256':sha(b)})
 for f in [HEADER,OWNED]:
  if f in index:raise RuntimeError('New source already in freshbefore')
  captured.append({'path':(ROOT/f).resolve().as_posix(),'present':False,'reason':'new source absent from freshbefore'})
 emit('before-source-origins.json',captured)
 emit('initial-source-origins.json',[original(ROOT/HEADER,'initial/header.h'),original(ROOT/OWNED,'initial/writer.py')])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 def read(va,size):
  o=pe.get_offset_from_rva(va-base);return o,raw[o:o+size]
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
 for n,(lo,hi,classification,purpose) in enumerate(SPANS):
  offset,b=read(lo,hi-lo);target=f'raw/s{n:02}.bin';put(OUT/target,b)
  decoded=[{'va':i.address,'rva':i.address-base,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(b,lo)]
  if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=len(b):raise RuntimeError('Selectedstatic span incomplete')
  emit(f'derived/s{n:02}.json',decoded)
  spans.append({'va_start':lo,'va_end':hi,'rva_start':lo-base,'rva_end':hi-base,'file_offset':offset,'copy':target,'bytes':len(b),'sha256':sha(b),'classification':classification,'purpose':purpose,'instructions':len(decoded)})
  c=counts.setdefault(classification,{'spans':0,'bytes':0});c['spans']+=1;c['bytes']+=len(b)
  for i in decoded:sites.append(dict(i,span=n,classification=classification))
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 data=[];table_rows=[]
 for n,(va,size,purpose) in enumerate(DATA):
  offset,b=read(va,size);target=f'raw/d{n:02}.bin';put(OUT/target,b)
  r={'va':va,'rva':va-base,'file_offset':offset,'copy':target,'bytes':size,'sha256':sha(b),'classification':'new_actual_read_table','purpose':purpose};data.append(r)
  if n>=2:
   mode=(va-0x7F69E8)//0x44;count=struct.unpack_from('<i',b)[0]
   table_rows.append({'mode':mode,'va':va,'raw_hex':b.hex(),'signed_count':count,'native_mask_dwords':[struct.unpack_from('<I',b,4+j*4)[0] for j in range(count)],'selector_bytes_31':list(b[0x31:0x31+count]),'scope':'actual modes6..10/15 only; unknown bytes retained, no gameplay permission'})
 emit('data-sites.json',data);emit('target-table-rows.json',table_rows)
 _,switch=read(0x55D8C0,20);_,selector=read(0x55D8D4,17)
 branches=[struct.unpack_from('<I',switch,k*4)[0] for k in range(5)]
 emit('target-switch.json',{'entry':'55D770','code_end_exclusive':'55D8BD','metadata_first_island_bytes':50,'actual_local_code_bytes':333,'jump_table':branches,'mode_targets':[{'mode':k+1,'selector':v,'target_va':branches[v]} for k,v in enumerate(selector)],'default':'mode0 orunsigned>17 returnswithoutwrite','unread_computed_addresses':'modes16/17 may compute EDI beyond meaningfulmaskrows but assert/generic paths never read thatrow; no synthesizedrow/defaultmask','external_assert':'53E3D0 callsite only; not authority'})
 counts_file=[struct.unpack_from('<I',resource,4+k*0x6e04)[0] for k in range(4)];definitions=[]
 for kind,count in enumerate(counts_file):
  for ident in range(1,count+1):
   at=8+kind*0x6e04+(ident-1)*110;b=resource[at:at+110]
   definitions.append({'kind':kind,'definition_id':ident,'file_offset':at,'bytes':len(b),'sha256':sha(b),'raw_hex':b.hex(),'raw_key_word':struct.unpack_from('<H',b)[0],'raw_word_3e':struct.unpack_from('<H',b,0x3e)[0],'raw_target_mode_byte_45':b[0x45],'scope':'declaration only; no learned status/cost/authority'})
 emit('derived/declared-definitions.json',definitions)
 emit('field-relations.json',[
  {'record':'complete110 byte actualpinnedcatalog','identity':'raw0 ID/raw1 kind','native_key_operand':'550208/20C→550211/214→550219 and55028A..55029C:zeroextendedrawWORD0 intofullDWORDoperand','raw_fields':'WORD3E at5501F4 special0FF5; BYTE45 at5502B1 feedshelper onlywhenactualowner468 nonzero','unknown_bytes':'all110 retained; no MP/cost/commonID inference'},
  {'command_domain':'base0x03 and0x17 (decimal3/23)','actual_bytes':'550184 80FB03 /550189 80FB17','continuation':'native OR80 yields0x83/0x97 inthese skillloops only','historical_correction':'earlier3/17 shorthand omittedhex; retainedoriginal unchanged; never reinterpret0x11/0x91 asskill because decimal17'},
  {'selected_pointer':'549A70 returns553A50 primary unlessF8==0 && FC!=0→553920 secondary','actual_index':'ownerA8CBFC signedDWORD','primary':'componentA89658 +BYTE4*2D0 +DC signedindex4 with count+10','secondary':'samecomponent +BYTE2D10*54 +2D28 signedindex4 with count+2D64','catalog_pointer_writer':'OPEN; matchingname/offset/deferredattachment not samepointer proof'},
  {'target_modes':'1..4,11,12,17','effect':'foractual count>0, OR bit(targetBYTE%14) intoWORD[targetBYTE/14]','domain':'nativehelper lacks independenttargetbound; source doesnotpromote unsafeOOB toservercap'},
  {'target_modes':'5','effect':'firsttargetBYTE unsigneddivision14, assign3FFF tothatWORD; countnotread; oppositeWORDretained'},
  {'target_modes':'6','effect':'actualrow positivecount; firstmask containing selectedpositionbit assigns lowWORD toselectedside; no match leavesprior'},
  {'target_modes':'7..10,15','effect':'actualrow positivecount; first selectorBYTE+31 ==position%14 writes WORDrow+4+index4; no match leavesprior'},
  {'target_modes':'13,14,16;0/out-of-range','effect':'assertcall then no write; defaultno write; no synthesizedzero/defaultsuccess'},
  {'specialdefinitionkind2':'whenWORD3E!=FF5, rawtarget holds twozeroextendedWORDs fromowner4A4/4A9; usesrawkeyoperand andcontinuations; not genericmask','source':'retained1905501EF..550285'},
 ])
 source=[]
 for f in STABLE+[HEADER]:
  b=(ROOT/f).read_bytes()
  for line,text in enumerate(b.decode('utf-8-sig').splitlines(),1):
   if any(k in text for k in ('raw','Record','lookup','declared','read_','current','operand','context','kind','definition_id')):source.append({'path':(ROOT/f).resolve().as_posix(),'line':line,'text':text,'sha256':sha(b)})
 emit('cpp-source-sites.json',source)
 findings={'round':192,'phase':'file/static only','new_cpp':1,'modified_cpp':0,'native_spans':len(spans),'native_bytes':sum(x['bytes'] for x in spans),'native_span_counts':counts,'instruction_sites':len(sites),'data_sites':len(data),'data_bytes':sum(x['bytes'] for x in data),'primary_sites':len(primary),'cpp_source_sites':len(source),'original_inputs':len(inputs),'original_bytes':sum(x['bytes'] for x in inputs),'declared_definitions':len(definitions),'new_opcodes':0,'complete_gameplay_routes':0,'whole_game_percent':None,'build_test_native_codec_api_db_sql_deploy':0,
  'proven':['Complete selected549A70/secondary553920 source and333B55D770 localjump-tableclosure; metadata50B retained asentryisland notfullfunction.','Exact rawkind03/17hex andcontinuations83/97; keyoperand zeroextends rawBYTE0/1 inbothnative skillbranches.','Eight actualdatatable copies:fiveDWORDtargets,17BYTEmodeselector,sixwhole68B rows; unused16/17computedrow not interpreted asmaskdata.','Ownedreadonly110byte record view withkey/WORD3E/BYTE45 supportsqualifiedNativeorSharedcatalog source; sourceowner retains allCurrent/provenance.'],
  'limits':['Primary553A50 and1268Bproducer are retained olddeferred/190; no newopcode or completegameplayclaim.','Selectedpointer lists actualproducer/clear/load provenance remainsOPEN; definitioncatalog alone is not learned/carrying list or entitlement.','Actualowner468 supplies aggregation mode; field45 doesnotalone selectsendcount/continuation/targets. Specialkind2target isnotuniformmask.','Unknown targetmode/no-match leavesprior bytes; declaredrawdefinition preserveallbytes. Parser doesnotgrant actualsourcehash/current/cost/MP or permission.','Nativeunsafe-lookingposition/no-count branches do not license serverOOBwrites or fabricated priorzero/defaultsuccess.','No formatter155/capacity/render/glyph/52F330/52F170 interiors followed; no native/API/codec/runtime/build/tests/database/SQL/deployment.']}
 emit('findings.json',findings)
 emit('gaps.json',[{'gap':'Actual selected pointer producer→catalog','next':'qualify bothprimary/secondary listwriter andexactloadedcatalog/entryepoch; no name ordefinitionID join'},
  {'gap':'Real skill rights/cost/current/target authority','next':'actualcommon learnedstate/owner/actor/phase/resource revisions andcost settlement; rawcatalog definition notgrant'},
  {'gap':'Owner468 aggregation andtargetlist source','next':'qualify realproducer/current ofaggregation flag, actualorderedtargets andspecialkind2owner4A4/4A9; clientlocalbranches notserverpermission'}])
 put(OUT/'README.md',b'# CN skill command frontier192\n\nPure file/PE/Capstone source work. Readonly full110-byte definition view, exact skill03/17hex and83/97 continuations. Full originals, derived definitions/disassembly and source epochs are separate. Selected pointer producer and server rights remain OPEN. No tests/build/runtime/deployment; routes0/percentnull. Finalseal after Root BATCHFINAL only.\n')
 derived=[]
 for folder in ['raw','derived']:
  for p in sorted((OUT/folder).rglob('*')):
   if p.is_file():
    b=p.read_bytes();derived.append({'path':p.resolve().as_posix(),'copy':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'kind':'bounded native subset/staticdisassembly/plain-source fields; not fulloriginal input'})
 emit('derived-inputs.json',derived)
 print(json.dumps(findings,ensure_ascii=True))

def capture(seal):
 current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(STABLE+[HEADER,OWNED])]
 emit('current-source-origins.json',current)
 if seal:
  members=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.name!='seal.json':
    b=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b)})
  emit('seal.json',{'round':192,'members':members,'member_count':len(members),'current_originals':len(current),'native_originals':1,'complete_gameplay_routes':0,'whole_game_percent':None})
  b=(OUT/'seal.json').read_bytes();print(json.dumps({'seal_sha256':sha(b),'members':len(members),'files_with_seal':len(members)+1,'current':current}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--capture',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args()
 if a.recover:recover()
 if a.capture:capture(a.seal)
