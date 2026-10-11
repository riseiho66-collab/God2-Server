"""198 bounded CN skill-book use producers; static file/PE/Capstone only.

No client, native code, codec, C++, database, API, build or test execution.
Full PE is read/hash-qualified in place; only bounded raw bytes are copied.
GUI callees, formatter155 and52F330/52F170 interiors remain stopped.
"""
from pathlib import Path
import argparse,csv,difflib,hashlib,io,json,re
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-skill-acquisition-frontier-01/agents/native-acquisition-producer'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
REC=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
CSV=BASE/'cn-current-npc-name-source-01/inputs/current-gamedata.csv'
CENSUS=EXE.parent.parent/'God2-Server-CN/artifacts/native/20261006-cn-route-denominator-03'
OWN='tools/reconstruction/cn_native_acquisition_producer198.py'
CURRENT=['src/cn/assets/CnNativeSkillBookBindings.h','src/cn/assets/CnNativeSkillBookBindings.cpp',OWN]
CANON=['004b0720','004b0760','004b0de0','004b0590','004c61a0','0042cfb0','00481440','004da630','004d9a70']

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Preserve existing epoch: '+name)
  return
 with p.open('xb') as f:f.write(b)
def emit(name,obj):put(name,(json.dumps(obj,indent=2,ensure_ascii=True)+'\n').encode())
def original(p,name):
 b=p.read_bytes();put(name,b)
 return dict(path=p.resolve().as_posix(),copy=name,bytes=len(b),sha256=sha(b))
def in_place(p,b,scope):return dict(path=p.resolve().as_posix(),copy=None,bytes=len(b),sha256=sha(b),retained_complete_in_place=True,scope=scope)

def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Already sealed')
 raw=EXE.read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Actual pinned CN PE differs')
 meta=(REC/'functions.tsv').read_bytes();calls=(REC/'calls.tsv').read_bytes()
 rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 inputs=[in_place(EXE,raw,'Whole pinned native PE read/hash; bounded copied spans below, no full PE duplicate'),
  in_place(REC/'functions.tsv',meta,'Full primary metadata read; selected rows separately derived'),
  in_place(REC/'calls.tsv',calls,'Full primary call index read; selected actual caller rows separately derived')]
 primary=[];instructions={};selected=[]
 for address in CANON:
  r=rows[address];p=REC/r['file'];primary.append(original(p,'primary/'+address+'.c'));selected.append(r)
  va=int(address,16);size=int(r['size']) if 'size' in r else int(re.search(rb'Size: (\d+) bytes',p.read_bytes()).group(1))
  code=pe.get_data(va-base,size);instructions[address]=list(md.disasm(code,va))
 emit('derived/selected-primary-metadata.json',selected)
 links=[r for r in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if r['target'] in {'004b0720','004b0760','004b0de0','004b0590','00481440'} and r['caller'] in set(CANON)]
 emit('derived/selected-primary-callers.json',links)
 # Complete leaf source extents are independent of the GUI body's metadata split.
 spans=[];sites=[]
 specs=[('004b0720',None,None,'expanded_existing_producer','C25 body itemWORD/slotBYTE; final bodyBYTE is unmodified arg8 highBYTE; third argument ignored'),
  ('004b0760',None,None,'expanded_existing_producer','BYTEslot<30 shortcut resolves original bag item before4B0DE0'),
  ('004b0de0',None,None,'expanded_existing_producer','C26/25/28 selector and exact body writes; no learning grant'),
  ('004b0590',None,None,'expanded_existing_producer','C28 equipment-like parsed flag path, separated from C25/26'),
  ('004c61a0',0x4c63a0,0x4c6720,'expanded_bounded_caller','Actual inventory use flag branch/caller literals; GUI/format callees not followed'),
  ('0042cfb0',0x42d080,0x42d25a,'retained_bounded_parser','Token14..25 common flag producer, already old skill-book parser; no recount'),
  ('00481440',None,None,'retained_complete_queue','Original opcode+body append, bodylength+1; not a server phase binding'),
  ('004da630',0x4da630,0x4da6df,'expanded_bounded_caller','Actual shortcut triplet type0 item dispatch; unsupportedmode source bytes remain unknown'),
  ('004d9a70',0x4d9d58,0x4d9e02,'expanded_bounded_caller','Actual input-release type0 item caller; no renderer interior')]
 for n,(a,lo,hi,kind,scope) in enumerate(specs):
  ins=instructions[a];take=[i for i in ins if (lo is None or i.address>=lo) and (hi is None or i.address+i.size<=hi)]
  if not take:raise RuntimeError('Empty bounded source')
  start=take[0].address;end=take[-1].address+take[-1].size;offset=pe.get_offset_from_rva(start-base);b=raw[offset:offset+end-start]
  name=f'raw/s{n:02}.bin';put(name,b)
  put(f'raw/s{n:02}.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in take)+'\n').encode())
  spans.append(dict(va=f'{start:08x}',end_exclusive=f'{end:08x}',rva=f'{start-base:08x}',file_offset=offset,bytes=len(b),sha256=sha(b),copy=name,classification=kind,scope=scope,canonical=a))
  sites.extend(dict(va=f'{i.address:08x}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operand=i.op_str,span=n) for i in take)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 csvraw=CSV.read_bytes()
 if sha(csvraw)!='16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3':raise RuntimeError('Pinned decoded CSV differs')
 inputs.append(in_place(CSV,csvraw,'Existing complete pinned decoded CSV; derivation, not installed encoded original; raw SKB block copied separately'))
 start=739098;end=806862;put('derived/SKB-complete-raw-block.bin',csvraw[start:end]);lines=csvraw[start:end].splitlines(keepends=True)
 if lines[0]!=b'SKB,386\r\n' or len(lines)!=387:raise RuntimeError('SKB block shape differs')
 books=[];offset=start+len(lines[0]);flags={};special=[]
 for index,line in enumerate(lines[1:]):
  f=line.rstrip(b'\r\n').split(b',');item=int(f[0]);bits=[int(f[t]) for t in range(14,22)]
  if not 6501<=item<=6900:raise RuntimeError('Book item domain differs')
  flag=sum((v&1)<<i for i,v in enumerate(bits));flags[flag]=flags.get(flag,0)+1
  # Literal caller ranges; only qualification of THIS loaded book/use branch.
  confirm=6568<=item<=6575 or 6665<=item<=6669 or 6763<=item<=6765 or 6884<=item<=6886
  if confirm:special.append(item)
  books.append(dict(item_id=item,source_line=9442+index,decoded_offset=offset,raw_bytes=len(line),sha256=sha(line),native_alias=f[26].decode('ascii'),flag_tokens=bits,parsed11a=flag,inventory_use_route='literal_confirmation_frontier' if confirm else 'C25_direct_branch',eligibility_unknown=True))
  offset+=len(line)
 emit('derived/386-book-use-source.json',books)
 emit('derived/book-use-flag-census.json',dict(records=386,flag_byte_counts=flags,special_confirmation_items=special,source_line_not_item_id=True,learned_grant_proven=False))
 # Preserve old actual raw census instruction excerpts, not merely reports.
 old=[]
 for call in ['004b0750','004b0f35','004b0f61','004b0620']:
  p=CENSUS/'instructions'/f'{call}.asm'
  if p.exists():old.append(original(p,'retained-census/'+call+'.asm'))
 emit('retained-census-origins.json',old)
 inputs+=primary
 for n,path in enumerate(CURRENT):inputs.append(original(ROOT/path,f'initial/s{n:02}{Path(path).suffix}'))
 for n,path in enumerate(['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']):
  inputs.append(original(ROOT/path,f'context/g{n:02}.md'))
 emit('original-inputs.json',inputs)
 emit('native-original-inputs.json',[inputs[0]])
 emit('findings-source-ready.json',dict(round=198,scope='Static acquisition producer qualification only',native_spans=len(spans),span_bytes=sum(s['bytes'] for s in spans),instruction_sites=len(sites),new_opcode_values=0,new_complete_gameplay_routes=0,whole_game_percent=None,flag_census=flags,special_confirmation_count=len(special),true_learning_authority=None,unknown=['Actual C25/C26 server learning/removal grant, common subject identity, costs, consumption, reply ordering/save/current issuer remain OPEN.','C26 last bodyBYTE is unwritten in4B0DE0; preserve opaque and never call quantity/defaultzero.','Shortcut supplied fullDWORD and rawloaded owner targetWORD remain native namespaces, never mask-cast common actorID.','Special book confirmation caller3B callback belongs peer recovery; not followed here.'],build_test_native_codec_api_db_sql_runtime_deploy=0))
 print(json.dumps(dict(spans=len(spans),bytes=sum(s['bytes'] for s in spans),sites=len(sites),flags=flags,special=len(special))))

def refine():
 if (OUT/'seal.json').exists():raise RuntimeError('Already sealed')
 # The erroneous first body-comment epoch is retained whole, never rewritten.
 prior=OUT/'epochs/initial-body-comment/tool.py'
 if not prior.exists():raise RuntimeError('Initial error epoch must remain')
 old=prior.read_text(encoding='utf-8');now=(ROOT/OWN).read_text(encoding='utf-8')
 put('refinement/tool.py',now.encode())
 put('refinement/tool.diff',''.join(difflib.unified_diff(old.splitlines(True),now.splitlines(True),fromfile='initial-tool',tofile='corrected-tool')).encode())
 spans=json.loads((OUT/'native-spans.json').read_text())
 spans[0]['scope']='C25 body itemWORD/slotBYTE; finalbodyBYTE retained arg8 highBYTE; third explicitargument is ignored'
 emit('refinement/native-spans.json',spans)
 relations={
  'C25':{'producer':'004B0720','logical_size':5,'body_size':4,
   'writes':[{'site':'004B0736','body_offset':0,'bytes':2,'source':'original WORD[EBP+8]'},
             {'site':'004B073D','body_offset':2,'bytes':1,'source':'original BYTE[EBP+C]'}],
   'body_offset3':'EBP+B not written; existing highBYTE original DWORD argument8 survives',
   'third_argument':'EBP+10 ignored by producer, even when caller supplies1',
   'exact_inventory_caller':'004C641C/004C6423 masks loaded bagitem toFFFF in EDI; 004C65F2..004C6603 supplies that fullEDI as firstarg. Only this actual alias source yields untouchedbody3=0.',
   'different_C25_alias':'4B0DE0 writes parseditem pointer into DWORDarg8 at004B0E33; later004B0F5A/5E rewrite lowWORD/body2 only; fourthBYTE can remain highBYTE pointer. Do not globally encodezero orquantity.'},
  'C26':{'producer':'004B0DE0','queue_site':'004B0F35','logical_size':7,'body_size':6,
   'fields':[{'body_offset':0,'bytes':2,'source':'WORD at loaded [owner+430AC]','site':'004B0F24'},
             {'body_offset':2,'bytes':2,'source':'DI low16 supplied actualitem','site':'004B0F2E'},
             {'body_offset':4,'bytes':1,'source':'BL reversebag scan slot29..0','site':'004B0F32'},
             {'body_offset':5,'bytes':1,'source':'EBP-3 not written by function; opaque retained stack'}],
   'native_target_namespace':'Actual loaded owner430AC firstWORD; not proof of common character/deity/pet ID. No lowword cast may fabricate binding.',
   'qualification':'owner42E3C==0; itemlowWORDnonzero; match signed positive bagBYTEquantity and same WORD item; item/100 53/55 branchesC25; parsed11A bit4 branchesC28. These client gates are not server custody/grant.'},
  'SKB':{'records':386,'actual_item_range':[6501,6900],'source_lines':[9442,9827],
   'all_flag_tokens_14_through21':[1,0,0,0,1,1,1,1],'all_parsed11a':'F1',
   'retained_parser':'42CFB0 token14..21 to rawflagbits0..7; type6 alias token26 and rawtail27..29 retained, not newly recovered',
   'direct_inventory_books':367,'literal_confirmation_books':19,
   'confirmation_ranges':[[6568,6575],[6665,6669],[6763,6765],[6884,6886]],
   'direct_branch':'4C644C/6452 bit4 clear;4C6492 bit1 set;4C649B bit8 clear; no other item specialliteral applies outside19. Native inputflag/state/source qualifications still mandatory.',
   'confirmation_frontier':'4C66BF savesitemWORD owner1C85A8+310FC;4C66CC savesslotBYTE+310FE; formatter callsite4C6717 STOP, canonical ensuing4AD550 dialog3B caller only. Confirmation callback/rules OPEN; delegated peer.',
   'shortcut_same_books':'item/100 65..69 does not hit53/55; parsed11A F1 bit4 clear; same actual book on4B0DE0 takesC26. No forced crossclient semantic equality.'},
  'limits':['No actual CN official server handler or learned eligibility, consumption, removal, cost, save or reply discovered.',
            'Existing queue/opcode census already contained25/26/28 producers. This is new precise source/alias relationship evidence, not new opcode/gameplay route.',
            'Canonical files copied whole; GUI/renderer/formatter callees never followed. Actual PE read/hash in place, bounded rawcopies only.']}
 emit('refinement/producer-field-relations.json',relations)
 oldfind=json.loads((OUT/'findings-source-ready.json').read_text());new=dict(oldfind)
 new.update(body_alias_correction=True,new_native_code_bytes=0,new_native_relations=['C25 unused thirdargument/borrowed highBYTE alias','386 F1flags route367 direct25 vs19 dialog3B','Native book shortcut26 rawtarget/slot/opaque tail distinctions'],retained_parser_queue_bytes=sum(s['bytes'] for s in spans if s['classification'].startswith('retained')),expanded_existing_source_bytes=sum(s['bytes'] for s in spans if s['classification'].startswith('expanded')),actual_CPP_changes=0,producer_fields='refinement/producer-field-relations.json',span_classification='refinement/native-spans.json')
 new['unknown'].append('C25 fourthbodyBYTE is unmodified firstDWORDarg highBYTE; thirdarg1 must not be mistaken for quantity/tail.')
 emit('findings-source-ready-02.json',new)
 put('refinement/findings.diff',''.join(difflib.unified_diff(json.dumps(oldfind,indent=2).splitlines(True),json.dumps(new,indent=2).splitlines(True),fromfile='initial-findings',tofile='corrected-findings')).encode())
 emit('refinement/source-origins.json',[dict(path=(ROOT/OWN).as_posix(),copy='refinement/tool.py',bytes=len(now.encode()),sha256=sha(now.encode()))])
 put('README.md',b'Round198 bounded static CN book/item-use producer qualification. Read findings-source-ready-02.json and refinement/producer-field-relations.json for corrected final conclusions. Initial erroneous C25 final-byte comment is fully retained in epochs/initial-body-comment and explicit diffs. No C++ source modified, no native/runtime/DB/tests/build/codec executed. PE and full metadata retained in place; all copied raw spans have exact VA/RVA/fileoffset/hash. Full primary canonical originals are separate from derived spans/SKB block. C25/C26 do not establish learned grant or common identity.\n')
 print(json.dumps(dict(corrected=True,spans=len(spans),code_bytes_new=0,expanded_bytes=new['expanded_existing_source_bytes'],retained_bytes=new['retained_parser_queue_bytes'])))

def finalize():
 if (OUT/'seal.json').exists():raise RuntimeError('Already sealed')
 # Root's actual pre-round snapshots stay authoritative; capture only our
 # two unchanged C++ inputs, never silently create a new before baseline.
 before_path=OUT.parents[1]/'before-manifest.json'
 before_raw=before_path.read_bytes();before=json.loads(before_raw);index={r['path']:r for r in before}
 old=[]
 for n,path in enumerate(CURRENT[:2]):
  row=index[path];p=before_path.parent/row['snapshot'];b=p.read_bytes()
  if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('Root before source differs')
  name=f'before/b{n:02}{Path(path).suffix}';put(name,b)
  old.append(dict(path=(ROOT/path).as_posix(),actual_snapshot_path=p.resolve().as_posix(),copy=name,bytes=len(b),sha256=sha(b)))
 emit('before-source-origins.json',old)
 emit('before-scope.json',dict(actual_manifest_path=before_path.resolve().as_posix(),bytes=len(before_raw),sha256=sha(before_raw),inputs=len(before),owned_tool_present=OWN in index,selected_before_inputs=2,baseline_replaced=False))
 current=[]
 for n,path in enumerate(CURRENT):
  if n<2 and sha((ROOT/path).read_bytes())!=old[n]['sha256']:raise RuntimeError('Unchanged stable C++ input drifted')
  current.append(original(ROOT/path,f'current/s{n:02}{Path(path).suffix}'))
 emit('current-source-origins.json',current)
 ready=json.loads((OUT/'findings-source-ready-02.json').read_text());emit('findings.json',ready)
 top=OUT/'seal.json';members=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p!=top:
   b=p.read_bytes();members.append(dict(path=p.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
 emit('seal.json',dict(round=198,files=members,member_count=len(members),all_nested_included=True,excluded_only='seal.json at OUT root',source_static_only=True))
 print(json.dumps(dict(members=len(members),files_with_seal=len(members)+1,seal_sha256=sha(top.read_bytes()),current=len(current))))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['recover','refine','finalize']);a=p.parse_args()
 {'recover':recover,'refine':refine,'finalize':finalize}[a.action]()
