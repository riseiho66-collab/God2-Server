from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round355-native-canonical-writer-source');A=O.parent;P=A.parent/'20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry';h=lambda b:hashlib.sha256(b).hexdigest();B=0x400000
m=(P/'native-image.bin').read_bytes();raw=(P/'originalPE.bin').read_bytes();assert h(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' and h(raw)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde';pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
def put(n,b):
 p=O/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def jout(n,o):put(n,(json.dumps(o,indent=2)+'\n').encode())
verified=[]
for d in [A/'round354-native-canonical-bulk-source',A/'round353-native-item-computed-writer-source',A/'round352-native-item-row-prefix-writer-source',A.parent/'20261012/round348-native-item-material-helper-source']:
 sp=d/'seal.json';seal=json.loads(sp.read_bytes());rows=seal['members'];seen=set()
 for x in rows:
  name=x.get('path',x.get('name'));assert name and name not in seen;seen.add(name);t=(d/name).resolve();assert t.is_relative_to(d.resolve());b=t.read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256']
 verified.append({'path':str(d),'seal_sha256':h(sp.read_bytes()),'members':len(rows),'member_bytes':sum(x['bytes'] for x in rows),'individual_verified':True})
jout('prior-individual-verification.json',verified)
lo,hi=0x49d2e0,0x49d365;b=m[lo-B:hi-B];off=pe.get_offset_from_rva(lo-B);assert raw[off:off+len(b)]==b;ins=list(md.disasm(b,lo));assert sum(x.size for x in ins)==len(b);sites={x.address for x in ins};assert ins[-1].mnemonic=='ret' and not ins[-1].op_str and ins[-1].address==0x49d364
branches=[x for x in ins if x.mnemonic.startswith('j')];assert not branches
put('qualified/native/child49D2E0-full.bin',b);put('qualified/native/child49D2E0-full.tsv',('VA\tbytes\tmnemonic\toperands\n'+''.join(f'{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}\n' for x in ins)).encode())
source=A/'round354-native-canonical-bulk-source/native/actual-canonical-save-action-whole.bin';sb=source.read_bytes();assert sb==m[0x49c4b0-B:0x49c767-B];parent=list(md.disasm(sb,0x49c4b0));call=next(x for x in parent if x.address==0x49c5c6);assert call.mnemonic=='call' and call.op_str=='0x49d2e0';prior=next(x for x in parent if x.address==0x49c5c4);assert prior.mnemonic=='mov' and prior.op_str=='ecx, ebp'
child=A.parent/'20261012/round348-native-item-material-helper-source/item-helper49B850-full.bin';cb=child.read_bytes();assert cb==m[0x49b850-B:0x49bae0-B]
jout('qualified/qualified-spans.json',[{'name':'actual-selected-saved-ui-reset-child-whole','begin':f'{lo:08X}','end_exclusive':f'{hi:08X}','bytes':len(b),'sha256':h(b),'original_pe_offset':off,'sites':len(ins),'direct_branches':0,'ret_sites':[f'{x.address:08X}' for x in ins if x.mnemonic=='ret'],'ret_pop_bytes':[0],'call_sites':[{'va':f'{x.address:08X}','target':x.op_str} for x in ins if x.mnemonic=='call'],'authentic_entry':'prior354 complete49C4B0 CALL49C5C6; currentECX=EBP beforeCALL; preceding49D2D1 RET4/padding supporting boundary only','new_native_method_credit':0}])
jout('qualified/source-lineage.json',{'whole_parent_reference':{'path':str(source),'bytes':len(sb),'sha256':h(sb)},'direct_call':'49C5C4 MOV ECX,EBP ->49C5C6 CALL49D2E0 ->49D2E2 MOV ESI,ECX','caller_condition':'complete354 49C4B0 hasselectedsavedBYTE85ACC==2 branch; calls49C770(1) beforechild; currentECXread sameobject afterchild; outerU affinity remainsconditionalonESI origin perprior354','direct_destination':'REPSTOSD10 to suppliedobject85AC0..85AE7 underDF0; notcanonical8560Crow','same_object_is_not_server_owner_or_phase':True,'existing_row_callee':{'path':str(child),'bytes':len(cb),'sha256':h(cb),'not_recaptured':True},'remaining':'canonicalprefix8560D..F incoming/computed/indirectwriter andtruefull25/full1215 issuer/ownership remainOPEN'})
# Independently physical-PE-check every retained raw discovery window using known VA index.
windows=json.loads((O/'discovery/finite23-window-index.json').read_text());checks=[]
for x in windows:
 lo=int(x['window'][0],16);b=(O/x['retained']).read_bytes();off=pe.get_offset_from_rva(lo-B);assert b==m[lo-B:lo-B+len(b)]==raw[off:off+len(b)];assert len(b)==x['bytes'] and h(b)==x['sha256'];checks.append({'retained':x['retained'],'physical_pe_equal':True,'unaligned_discovery_only':True})
for name,lo in [('child49D2E0-boundary-window',0x49d2d0),('child49D2E0-before-boundary',0x49d2c0),('rep02-nearest-boundary-discovery',0x487700)]:
 b=(O/'discovery'/f'{name}.bin').read_bytes();off=pe.get_offset_from_rva(lo-B);assert b==m[lo-B:lo-B+len(b)]==raw[off:off+len(b)];checks.append({'retained':'discovery/'+name+'.bin','physical_pe_equal':True,'unaligned_discovery_only':True})
jout('discovery/window-physical-pe-readback.json',checks)
# No source/raw-input image copy. Cut paths and every prior member remain contained.
jout('capture-complete.json',{'verdict':'PASS','complete_methods':1,'qualified_code_bytes':133,'qualified_data_bytes':0,'qualified_sites':len(ins),'raw_rep_candidates':len(windows),'prior_packages':len(verified),'new_method_opcode_format_route_credits':0,'target_execution':False})
print(json.dumps({'verdict':'PASS','complete':1,'code_bytes':133,'data_bytes':0,'sites':len(ins),'prior_members':sum(x['members'] for x in verified),'prior_member_bytes':sum(x['member_bytes'] for x in verified),'raw_candidates':len(windows)}))
