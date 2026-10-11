"""201 fixed CN WORLD24 inline raw counter source qualification, files only.

No native/client, codec, API, DB/SQL, C++ execution, build or tests. All
GUI/formatter/render callees stop at the actual caller boundary. Prior full
518F70/519590 are retained evidence, not newly recovered native functions.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json,struct
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-shared-book-request-source-01'
OUT=ROUND/'agents/native-role-counter-source'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
REC=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='7afd43756858a2113a0e75371732fd0c12d275f36e8b79d95fb05169fa7dd7d0'
OWN='tools/reconstruction/cn_role_counter201.py'
VIEW='src/cn/protocol/CnInlineRoleCounters24.h'
PRIMARY={
 '0048fcc0':'Only WORLD24/9F upstream packet selection, arguments and actual UI owner; no unrelated dispatcher branches',
 '00567b50':'Only known fixed-length direct resolver and opcode24 leaf/table; no new opcode',
 '00518f70':'Retained200 whole scalar leaf; mode0 inline stores vs mode6 selected-row stores, unsigned comparisons; downstream UI calls STOP',
 '00519590':'Retained200 whole role-status leaf, absence of inline64 store in this leaf only; UI callees STOP',
 '004af370':'Retained200 same R+90 actual component caller relation; no new native recovery',
 '005176b0':'Retained200 bounded prefix component430A8 writer; GUI interiors are not traversed',
 '0054d030':'Text locator of separate battle scalar caller; no raw trace or whole branch closure claim',
 '00551d50':'Text locator of old battle dispatcher; retained context, no new algorithm or GUI traversal',
 '00492e70':'Text locator of initial supplied role object; only zero-initialization naming lead retained, no asserted nonzero64 producer',
 '004d2d30':'Text locator of supplied component assignment; GUI callees STOP, no source/authority claimed from rendering',
 '0048caa0':'Text locator of old role-object materialization; same common actor/current remains mandatory',
 '00536f30':'Rejected formatter-wrapper lead: no raw code recovery or interior follow; WORLD9F call site retained only'}
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/cn_battle_scalar_update_delivery.py',
 'tools/reconstruction/cn_native_role_summary_level_source_delivery.py',
 'tools/reconstruction/cn_same_opcode_consumer_source_delivery.py',
 'tools/reconstruction/cn_selected_subject_update_source_delivery.py',
 'tools/reconstruction/cn_native_spectator_frontier186.py']
SPANS=[
 (0x567b9a,0x567ba1,'retained_known_length','Known opcode24 fixed17 length leaf; newly qualified inline raw-field relationship, no new opcode'),
 (0x567b50,0x567b69,'retained_known_resolver','Known unsigned BYTE opcode direct table lookup; no whole resolver recovery'),
 (0x4912e8,0x4912fd,'retained200_WORLD24','Exact packet+1 and actual U=P+89B26C, mode/other two arguments all0'),
 (0x491302,0x491324,'expanded_known_WORLD_caller','Additional old WORLD9F same16B scalar prefix→mode0; stop formatter-wrapper call, no C1F causality'),
 (0x48fd3c,0x48fd6d,'expanded_known_WORLD_dispatch','Actual transport owner P+8885E4, queue selector1, raw opcode dispatch; known root, bounded only'),
 (0x518f70,0x51905c,'retained200_complete_leaf','Original full236B mode0 inline32 stores/unsigned delta vs mode6 selected-row counters'),
 (0x519590,0x51963a,'retained200_complete_leaf','Original full170B status consumer does not write inline64; downstream UI calls STOP')]

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Preserve earlier epoch: '+name)
  return
 with p.open('xb') as f:f.write(b)
def emit(name,x):put(name,(json.dumps(x,indent=2,ensure_ascii=True)+'\n').encode())
def original(p,name,scope):
 b=p.read_bytes();put(name,b)
 return dict(path=p.resolve().as_posix(),copy=name,bytes=len(b),sha256=sha(b),scope=scope)
def reference(p,b,scope):return dict(path=p.resolve().as_posix(),copy=None,bytes=len(b),sha256=sha(b),complete_retained_in_place=True,scope=scope)

def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Already sealed')
 fresh=(ROUND/'before-manifest.json').read_bytes();rows=json.loads(fresh)
 if len(rows)!=1435 or sha(fresh)!=BEFORE:raise RuntimeError('Fresh source baseline differs')
 emit('before-source-origins.json',dict(root_manifest=(ROUND/'before-manifest.json').as_posix(),sha256=sha(fresh),bytes=len(fresh),input_count=1435,new_absent=[p for p in [OWN,VIEW] if p not in {r['path'] for r in rows}],baseline_replaced=False))
 raw=EXE.read_bytes();meta=(REC/'functions.tsv').read_bytes();calls=(REC/'calls.tsv').read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Pinned native original differs')
 funcs={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
 inputs=[reference(EXE,raw,'Whole actual PE read/hash-qualified in place; bounded originals below'),reference(REC/'functions.tsv',meta,'Whole primary metadata read/hash in place'),reference(REC/'calls.tsv',calls,'Whole primary call index read/hash in place')]
 for a,scope in PRIMARY.items():inputs.append(original(REC/funcs[a]['file'],'primary/'+a+'.c',scope))
 emit('derived/selected-primary-metadata.json',[funcs[a] for a in PRIMARY])
 selected=[r for r in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if r['target']=='00518f70']
 emit('derived/indexed-scalar-callers.json',dict(scope='Selected actual direct indexed callers; neither exhaustive indirect aliases nor common authority proof',rows=selected))
 for n,p in enumerate(CONTEXT):inputs.append(original(ROOT/p,f'context/c{n:02}{Path(p).suffix}','Complete original copy; only bounded source/provenance scope used'))
 inputs.append(original(ROOT/OWN,'initial/tool.py','New owned static file capture tool, full original'))
 emit('initial-source-origins.json',[inputs[-1]])
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 def read(va,n):
  off=pe.get_offset_from_rva(va-base);return off,raw[off:off+n]
 spans=[];sites=[]
 for n,(start,end,kind,scope) in enumerate(SPANS):
  off,b=read(start,end-start);ins=list(md.disasm(b,start))
  if sum(i.size for i in ins)!=len(b):raise RuntimeError('Incomplete instruction boundary '+hex(start))
  name=f'raw/s{n:02}.bin';put(name,b);put(f'raw/s{n:02}.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
  spans.append(dict(va=f'{start:08x}',end_exclusive=f'{end:08x}',rva=f'{start-base:08x}',file_offset=off,copy=name,bytes=len(b),sha256=sha(b),classification=kind,scope=scope))
  sites.extend(dict(va=f'{i.address:08x}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operand=i.op_str,span=n) for i in ins)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 data=[]
 for va,expected,label in [(0x567d34,0x567b9a,'Known opcode24 fixed-length table cell'),(0x492a68,0x4912e8,'Known WORLD24 direct consumer table cell')]:
  off,b=read(va,4)
  if struct.unpack('<I',b)[0]!=expected:raise RuntimeError('Selected actual table differs')
  name=f'data/t{len(data):02}.bin';put(name,b);data.append(dict(va=f'{va:08x}',rva=f'{va-base:08x}',file_offset=off,copy=name,bytes=4,sha256=sha(b),target_va=f'{expected:08x}',scope=label,classification='retained_known_table_new_field_qualification'))
 emit('data-sites.json',data)
 relations=dict(
  native_pin=PIN,world24=dict(direction='S2C',phase='world-connection-1',opcode=36,logical_size=17,body_size=16,length_cell='00567D34',length_leaf='00567B9A',world_cell='00492A68',world_branch='004912E8',payload='EDI+1',actual_ui='ECX=P+89B26C',mode=0,arg3=0,arg4=0,callee='00518F70',source_current_not_in_wire=True),
  inline_words=[dict(logical_offset=1,payload_offset=0,width_bits=32,destination='actual [U+430A8]+5C'),dict(logical_offset=5,payload_offset=4,width_bits=32,destination='actual [U+430A8]+64'),dict(logical_offset=9,payload_offset=8,width_bits=32,destination='actual [U+430A8]+60'),dict(logical_offset=13,payload_offset=12,width_bits=32,destination='actual [U+430A8]+68')],
  interpretation='Whole unsigned DWORD bits retained. No inferred HP/MP/current/maximum/cost/cap identity. Value-preserving uint32→uint64 projection is exact, not expanded native wire.',
  actual_read_sites=dict(payload4='00518FCF MOV EAX,DWORD[EBX+4]',inline64_store='00518FD2 MOV DWORD[ECX+64],EAX',mode_read='00518F73 BYTE[EBP+14]'),
  signedness='Mode BYTE equality0/6. Incoming scalar fields use full DWORD; delta compares JA/JAE unsigned and clamp selected+2C only on incoming first DWORD decrease. No inline64 arithmetic/narrowing in this leaf.',
  selected_row_boundary='Mode6 reads actual inline+D0 and writes row+2C from payload0, row+30 from payload8. It does not store inline64. No native/common subject identity/learned grant follows from pointer or field offsets.',
  s22_boundary='Retained519590 stores inline+60/+68 etc but does not store inline+64; cannot use S22 as substitute for that actual source.',
  upstream='WORLD P+8885E4 transport with selected input1→47F510 returns exact logical pointer EDI; opcode BYTE controls known world table. Actual transport/current/phase qualification remains required.',
  other_supplier='Retained WORLD9F calls formatter-wrapper536F30 (callee STOP) then same518F70/0 on packet+1. Only call site/read-prefix distinction is qualified; not a C1F response or inferred cost/MP producer.',
  initial_boundary='200 retained actual5176B0 binds supplied R+90 to U430A8 in both modes. Initial role-object zeroing is not a recovered current64 value. Genuine initial source, later writer aliases, actual identity/current epoch remain unqualified.',
  gaps=['Ready C1F00 has no request/reply causality to S24/9F/22 here.','Actual server inline-role counter issuer/current/common actor/storage/rules still mandatory.','No official learned skills, MP formula/cost, numeric cap or extended native64 wire established.'],new_opcodes=0,new_complete_gameplay_routes=0,whole_game_percent=None)
 emit('field-relations.json',relations)
 emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]])
 emit('findings-source-ready.json',dict(round=201,native_spans=len(spans),native_bytes=sum(s['bytes'] for s in spans),instruction_sites=len(sites),expanded_known_caller_spans=2,expanded_known_caller_bytes=83,retained_spans=5,retained_bytes=459,new_native_code_bytes=0,new_complete_native_functions=0,new_field_source_qualifications=1,data_sites=2,data_bytes=8,source_inputs=len(inputs),Cpp_changes=0,new_opcodes=0,new_complete_gameplay_routes=0,whole_game_percent=None,C1F_reply_causality=None,native_wire_widened=False,runtime_api_native_db_sql_codec_build_tests=0))
 print(json.dumps(dict(spans=len(spans),bytes=sum(s['bytes'] for s in spans),sites=len(sites),inputs=len(inputs))))

def finalize():
 if (OUT/'seal.json').exists():raise RuntimeError('Already sealed')
 initial=json.loads((OUT/'initial-source-origins.json').read_text())
 if sha((ROOT/OWN).read_bytes())!=initial[0]['sha256']:raise RuntimeError('Tool epoch changed; preserve explicit refinement first')
 current=[original(ROOT/OWN,'current/tool.py','Actual stable owned tool')]
 if not (ROOT/VIEW).exists():raise RuntimeError('Actual final Root-owned readonly view required before seal')
 current.append(original(ROOT/VIEW,'current/view.h','Parent-authorized final readonly view, complete actual original'))
 emit('current-source-origins.json',current)
 emit('final-source-origins.json',[current[1]])
 source_inputs=json.loads((OUT/'original-inputs.json').read_text())
 emit('final-original-inputs.json',source_inputs+[current[1]])
 findings=json.loads((OUT/'findings-source-ready.json').read_text());findings['final_original_input_count']=len(source_inputs)+1;findings['final_current_count']=2
 emit('findings.json',findings)
 put('README.md',b'201 actual CN WORLD24 fixed17/body16 -> same UI inline four original unsigned DWORDs. Original mode0 and mode6 selected-row stores remain distinct. Prior200 leaves retained; bounded known upstream/caller selection expanded, newcode0. S22 does not supply inline64. C1F response cause/current/issuer/common learned/rules remain OPEN. No HP/MP/cost names inferred, no native64 wire widening. Whole PE and TSV originals qualified in place; complete canonical text and bounded raw copies separate. Formatter/GUI callees STOP; no C++ change/native/runtime/API/DB/SQL/codec/build/tests.\n')
 top=OUT/'seal.json';files=[]
 for f in sorted(OUT.rglob('*')):
  if f.is_file() and f!=top:
   b=f.read_bytes();files.append(dict(path=f.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
 emit('seal.json',dict(round=201,files=files,member_count=len(files),all_nested_included=True,excluded_only='OUT root seal.json'))
 print(json.dumps(dict(members=len(files),files_with_seal=len(files)+1,seal_sha256=sha(top.read_bytes()),tool_sha256=sha((ROOT/OWN).read_bytes()),current=2,originals=len(source_inputs)+1)))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['recover','finalize']);a=p.parse_args();{'recover':recover,'finalize':finalize}[a.action]()
