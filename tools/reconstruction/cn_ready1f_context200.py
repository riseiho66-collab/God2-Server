"""200 bounded CN ready1F actual window/current/component qualification.

File/PE/Capstone only. No native, API, DB, SQL, codec, runtime, build/tests.
GUI/renderer/formatter callees and stopped155/52F chains are not traversed.
The original PE/indices are read/hash-qualified in place, not duplicated.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-item-control-source-frontier-01'
OUT=ROUND/'agents/native-ready1f-context'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
REC=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='61d1be29c2fca9b7bf511cbd612fb811b8035e2feb4462d0de43e5cd2e8c6dac'
OWN='tools/reconstruction/cn_ready1f_context200.py'
CURRENT=[OWN,'src/cn/protocol/CnWorldCharacterList.h']
PRIMARY=['004960a0','005176b0','005182d0','005183c0','004af370','00519590','00518f70','0048fcc0']
SPANS=[
 (0x4960a0,0x4960c8,'new_complete_leaf','Actualsignedhandle gate reads windowWORDflags20, not role/skillgrant; no upperguard'),
 (0x5176b0,0x517738,'new_bounded_initializer_prefix','Actualcomponent430A8 assignment then actualUIcreate-returnAX ->1C84C6; stopconstructor/renderinteriors'),
 (0x5182d0,0x51835d,'expanded_existing_caller','Actualpeerwindow20 gates then sameprofilehandle10 ->forced C1F; laterUICalls STOP'),
 (0x4af485,0x4af49b,'retained195_bounded_mode0','Oldmode0 invokes5176B0(suppliedR+90) then4D2D30, preserveactualcallee distinction'),
 (0x4af68c,0x4af6b0,'retained195_bounded_mode1','Oldnonzero-mode ALSO invokes5176B0(suppliedR+90), thoughno4D2D30;430A8 stillrebound'),
 (0x519590,0x51963a,'retained_complete_field_consumer','KnownWORLD/BATTLE22 fieldstores inactualcomponent; renderer/syscallcallees STOP; noC1Fcausality'),
 (0x518f70,0x51905c,'retained_complete_field_consumer','Knownscalarupdater differentmode0/6 branches; actualcounter/delta arithmetic notserverrules'),
 (0x491295,0x4912a4,'retained_bounded_WORLD22','KnownS22 packet+1/actual U passed toconsumer, noC1F pairing'),
 (0x4912e8,0x4912fd,'retained_bounded_WORLD24','KnownS24 scalarpayload+1 actualowner qualifier; caller only, noACK inferred')]

def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise RuntimeError('Preserveearlier epoch '+name)
  return
 with p.open('xb') as f:f.write(b)
def emit(name,x):put(name,(json.dumps(x,indent=2,ensure_ascii=True)+'\n').encode())
def original(p,name):
 b=p.read_bytes();put(name,b)
 return dict(path=p.resolve().as_posix(),copy=name,bytes=len(b),sha256=sha(b))
def inplace(p,b,scope):return dict(path=p.resolve().as_posix(),copy=None,bytes=len(b),sha256=sha(b),complete_retained_in_place=True,scope=scope)

def recover():
 if (OUT/'seal.json').exists():raise RuntimeError('Alreadysealed')
 old=(ROUND/'before-manifest.json').read_bytes();rows=json.loads(old)
 if len(rows)!=1426 or sha(old)!=BEFORE:raise RuntimeError('Actualfreshbefore differs')
 emit('before-scope.json',dict(path=(ROUND/'before-manifest.json').as_posix(),bytes=len(old),sha256=sha(old),input_count=1426,owned_tool_absent=OWN not in {r['path'] for r in rows},baseline_replaced=False))
 raw=EXE.read_bytes()
 if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('PinnedoriginalPE differs')
 metadata=(REC/'functions.tsv').read_bytes();calls=(REC/'calls.tsv').read_bytes()
 funcs={r['address']:r for r in csv.DictReader(io.StringIO(metadata.decode('utf-8-sig')),delimiter='\t')}
 pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 inputs=[inplace(EXE,raw,'FullpinnedPE read/hash; boundedcopies below'),inplace(REC/'functions.tsv',metadata,'Fullprimarymetadata read; selectedrows separatelyderived'),inplace(REC/'calls.tsv',calls,'Fullprimarycalls read; selectedactualedges derived')]
 for a in PRIMARY:inputs.append(original(REC/funcs[a]['file'],'primary/'+a+'.c'))
 emit('derived/selected-primary-metadata.json',[funcs[a] for a in PRIMARY])
 edges=[r for r in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if r['caller'] in PRIMARY and r['target'] in {'004960a0','005176b0','004b1b40','00519590','00518f70','00451460'}]
 emit('derived/selected-primary-callers.json',edges)
 spans=[];sites=[]
 for n,(start,end,kind,scope) in enumerate(SPANS):
  offset=pe.get_offset_from_rva(start-base);b=raw[offset:offset+end-start];ins=list(md.disasm(b,start))
  if sum(i.size for i in ins)!=len(b):raise RuntimeError('Exactboundedspan incomplete '+hex(start))
  name=f'raw/s{n:02}.bin';put(name,b)
  put(f'raw/s{n:02}.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
  spans.append(dict(va=f'{start:08x}',end_exclusive=f'{end:08x}',rva=f'{start-base:08x}',file_offset=offset,copy=name,bytes=len(b),sha256=sha(b),classification=kind,scope=scope))
  sites.extend(dict(va=f'{i.address:08x}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operand=i.op_str,span=n) for i in ins)
 emit('native-spans.json',spans);emit('instruction-sites.json',sites)
 # Originalcomplete32B constantwindowtemplate operands, no shape/renderclaim.
 offset=pe.get_offset_from_rva(0x7f5020-base);data=raw[offset:offset+32];put('data/007f5020.bin',data)
 emit('data-sites.json',[dict(va='007f5020',rva='003f5020',file_offset=offset,copy='data/007f5020.bin',bytes=32,sha256=sha(data),scope='TwoactualMOVAPS templateoperands ininitializerprefix; layoutsemantics not recovered')])
 relations={
  'real_nonforced_gate':'4B1B40 retained199 passesactualWORDowner1C84C6 into4960A0 withECX=owner+7785C. 4960A0 signedWORDnegative->0; otherwise owner+7785C+818+handle*2A08 readsrawWORDflags&20. This isnativewindowcurrent qualification, notcharacter/skillcurrent orpermission. No upperhandle guard in leaf; unsafeclient memoryarithmetic isnotservercapacity.',
  'profile_handle_writer':'5176B0 prefix receivesactualcomponentargDWORD,5176E3 writesowner430A8=it. Actual451460 callsite51772C (calleeSTOP) returnsAX;517731 writesowner1C84C6. This bindswindow/modelsource in this nativeinstance, notcommonactorID.',
  'both_mode_rebinding':'Retained4AF370 mode0/nonnullmode callsites4AF48E/4AF6AB both supplyparam2+90 to5176B0. Its430A8 overwrite thereforeoccurs inbothmodes. Retained195 truth thatmode1doesnot4D2D30 mustNOTbeexpanded toclaim430A8 untouchedinmode1. SameR/P/U/actualowner epochstillrequired; no stale pointer/defaultownerinvented.',
  'forced_open_domain':'5182D0 checkspeerwindow1C84EA and1C84EC bit20 and mayaborttoexistingnoticecalls. Sameprofile1C84C6 mustbenonnegative;51834A testsbit10,then518354/356/358 issues4B1B40(1F,1),bypassingnonforcedbit20 gate. SubsequentUIcalls/4F410 arestoppedsites. 5183C0 separatelyretainedtext corroboratesflag10 source; noextraGUIinteriors.',
  'wire_indistinguishable':'ActualreadyC1F00 is identicalfor modal3Bfollowup,ordinaryitemuse,forcedprofileopening andotherworldinitialcallers. Wire alone carriesno item,target,selector,UIhandle,commonactorID orbranch/source revision. ActualOwner mustqualifyoperation scope,notguesswhichcaller orcastgrant.',
  'known_field_consumers':'RetainedS22 exactWORLDcaller491295 passespacket+1 withactualUI U;519590 writescomponent430A8 levelBYTE26,DWORD60/68,WORD90,zeroextendedWORD78/7C/80/84 andWORD58. RetainedS24 branch to518F70 writesDWORD5C/64/60/68 andclampsselectedcomponentD0+2Cdelta; alternateconsumerparam5==6 writesselectedrow2C/30. GUIrefreshcallees STOP; definitions/counterwrites notserverruleorC1Fresponseproof.',
  'different1Fphase':'ExistingCnWorldCharacterList exact125B World-loginS2C1F view remainsindependent. Sameopcode/directionnumber isnotcausalproof forreadyC1F00 orpermissiontoreusebootstrapreplies.',
  'next_source_action':'RealreadyControlOwner shouldqualifycurrentcommonadmittedactor/modelresource/operationhistory andsupplynativeoutput underitsactualrules; it cannotpretendclientprofilewindowflags are serverrights orautomaticallysendrecoveredbootstrap/stat/skillrecords. ConcreteC1F replycause andfullissuerremainOPEN.',
  'unknown':['Actualofficialserver request/replypairing andspecificrefreshresult records remainunknown.','Profilewindow lifecycle/handle reuse/actualcomponentgeneration mustbequalified; sparsewire1F00 cannotcarrythat proof.','No nativecommon learned ownership/skillacquisition/cost/removal/ACK reconstructed.']}
 emit('field-relations.json',relations)
 for n,p in enumerate(['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']):inputs.append(original(ROOT/p,f'context/g{n:02}.md'))
 initial=[]
 for n,p in enumerate(CURRENT):
  r=original(ROOT/p,f'initial/s{n:02}{Path(p).suffix}');inputs.append(r);initial.append(r)
 emit('initial-source-origins.json',initial);emit('original-inputs.json',inputs);emit('native-original-inputs.json',[inputs[0]])
 emit('findings-source-ready.json',dict(round=200,native_spans=len(spans),native_bytes=sum(s['bytes'] for s in spans),instruction_sites=len(sites),new_complete_leafs=1,new_complete_leaf_bytes=40,new_bounded_prefixes=1,new_bounded_prefix_bytes=136,expanded_existing_caller_bytes=141,retained_spans=6,retained_bytes=sum(s['bytes'] for s in spans if s['classification'].startswith('retained')),data_sites=1,data_bytes=32,Cpp_changes=0,new_opcodes=0,new_complete_gameplay_routes=0,whole_game_percent=None,C1F_reply_causality=None,actual_native_gate_not_authority=True,mode1_model_rebind_qualified=True,runtime_native_api_db_sql_codec_build_tests_deploy=0))
 print(json.dumps(dict(spans=len(spans),bytes=sum(s['bytes'] for s in spans),sites=len(sites),inputs=len(inputs),new_leaf=40,new_prefix=136)))

def finalize():
 if (OUT/'seal.json').exists():raise RuntimeError('Alreadysealed')
 initial=json.loads((OUT/'initial-source-origins.json').read_text());current=[]
 for n,p in enumerate(CURRENT):
  if sha((ROOT/p).read_bytes())!=initial[n]['sha256']:raise RuntimeError('Source drift/refinement musthaveexplicit epoch/diff')
  current.append(original(ROOT/p,f'current/s{n:02}{Path(p).suffix}'))
 emit('current-source-origins.json',current)
 emit('findings.json',json.loads((OUT/'findings-source-ready.json').read_text()))
 put('README.md',b'200 native readyC1F context: actual window gate,actualcomponent/handle writer,bothmode model rebinding andforcedcaller domain. No response pairing/learning authority inferred. Full canonical sourcecopies separate from boundedraw/derivedindices. WholePE/TSV readhash retainedinplace. initial/current sourceexactequal; existing125B World-loginS2C1F isindependent. Stopall GUI/render/formatter155/52F interiors; no C++/runtime/API/DB/SQL/codec/build/tests.\n')
 top=OUT/'seal.json';members=[]
 for f in sorted(OUT.rglob('*')):
  if f.is_file() and f!=top:
   b=f.read_bytes();members.append(dict(path=f.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
 emit('seal.json',dict(round=200,files=members,member_count=len(members),all_nested_included=True,excluded_only='OUT root seal.json'))
 print(json.dumps(dict(members=len(members),files_with_seal=len(members)+1,seal_sha256=sha(top.read_bytes()),tool_sha256=sha((ROOT/OWN).read_bytes()),current=len(current))))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['recover','finalize']);a=p.parse_args()
 {'recover':recover,'finalize':finalize}[a.action]()
