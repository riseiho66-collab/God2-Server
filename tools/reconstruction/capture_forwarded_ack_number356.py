from pathlib import Path
import hashlib,json,subprocess
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
S=Path('C:/Users/risei/Desktop/God2/God2-Server');O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round356-native-movement-ack-source');A=O.parent;P=A.parent/'20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry';Q=S/'artifacts/integration/packet-connections-20261006/tw-native-host-composition-source-01/agents/tw-authority-frontier';h=lambda b:hashlib.sha256(b).hexdigest();B=0x400000
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes();assert h(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' and h(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde';pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
def put(n,b):
 p=O/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def jout(n,v):put(n,(json.dumps(v,indent=2)+'\n').encode())
prior=A/'round353-native-full-movement-issuer-source';sp=prior/'seal.json';seal=json.loads(sp.read_bytes());seen=set()
for x in seal['members']:
 name=x.get('path',x.get('name'));assert name not in seen;seen.add(name);p=(prior/name).resolve();assert p.is_relative_to(prior.resolve());b=p.read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256']
jout('prior353-individual-verification.json',{'path':str(prior),'seal_sha256':h(sp.read_bytes()),'members':len(seal['members']),'member_bytes':sum(x['bytes'] for x in seal['members']),'individual_verified':True})
xs=json.loads((Q/'native-spans.json').read_bytes());frame=next(x for x in xs if x['start_rva']=='00067860');case=next(x for x in xs if x['start_rva']=='000692FA')
i=next(x for x in frame['instructions'] if x['va']=='00467BBA');assert i['mnemonic']=='call' and i['operands']=='0x432bb0';assert m[0x67bba:0x67bbf]==bytes.fromhex(i['bytes_hex'])
# Demonstrated byte forwarding from an already-complete authentic parent only.
lo,hi=0x432bb0,0x432c3a;b=m[lo-B:hi-B];off=pe.get_offset_from_rva(lo-B);assert b==r[off:off+len(b)];ins=list(md.disasm(b,lo));assert sum(x.size for x in ins)==len(b);sites={x.address for x in ins};branches=[]
for i in ins:
 if i.mnemonic.startswith('j'):
  target=int(i.op_str,16);assert target in sites;branches.append({'va':f'{i.address:08X}','target':f'{target:08X}'})
assert [i.address for i in ins if i.mnemonic=='ret']==[0x432c37] and ins[-1].op_str=='0xc'
put('qualified/native/ack-byte-forwarded-number-full.bin',b);put('qualified/native/ack-byte-forwarded-number-full.tsv',('VA\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
f=m[0x1823b4:0x1823b7];foff=pe.get_offset_from_rva(0x1823b4);assert f==b'%d\0'==r[foff:foff+3];put('qualified/native/number-format-literal.bin',f)
jout('qualified/qualified-spans.json',[{'begin':f'{lo:08X}','end_exclusive':f'{hi:08X}','bytes':len(b),'sha256':h(b),'sites':len(ins),'original_pe_offset':off,'ret_sites':['00432C37'],'ret_pop_bytes':12,'direct_branches':branches,'calls':[{'va':f'{i.address:08X}','target':i.op_str,'opaque':True} for i in ins if i.mnemonic=='call'],'authentic_entry':'known whole467860 CALL467BBA forwards zeroextendedBYTE231 as fullformal3; previousboundary discovery onlysupport','data_bytes':3,'data_scope':'known shared%d literal, not new CRT semantics','credits':0}])
# Retain exact existing instructions/refs rather than duplicate known method bytes.
selected=[]
for x in xs:
 scope=[]
 for i in x['instructions']:
  va=int(i['va'],16)
  if (x['start_rva']=='00067860' and (0x46788a<=va<=0x4678e4 or 0x467b71<=va<=0x467bba)) or x['start_rva'] in ['000692FA','00103700','00103640','00103660','00103680','001036B0']:
   scope.append(i)
 if scope:selected.append({'prior_full_span':str(Q/x['copy']),'full_sha256':x['sha256'],'start_rva':x['start_rva'],'selected_instructions':scope,'new_capture_or_credit':False})
jout('qualified/retained-ring-byte-lineage.json',selected)
checks=[]
for x in json.loads((O/'finite231-literal-candidates.json').read_bytes()):
 b=(O/x['retained']).read_bytes();a=int(x['window_start'],16)-B;off=pe.get_offset_from_rva(a);assert b==m[a:a+len(b)]==r[off:off+len(b)];checks.append({'retained':x['retained'],'mapped_original_pe_equal':True,'unaligned_discovery_only':True})
b=(O/'discovery/debug-number-nearest-entry-window.bin').read_bytes();a=0x32b90;off=pe.get_offset_from_rva(a);assert b==m[a:a+len(b)]==r[off:off+len(b)];checks.append({'retained':'discovery/debug-number-nearest-entry-window.bin','mapped_original_pe_equal':True,'unaligned_discovery_only':True});jout('discovery/physical-pe-window-readback.json',checks)
head='6c2d3412e22316d1537323bc13e449f87ddfd03a';refs=[]
for rel in ['src/protocol/RecoveredNativeMovement.h','src/game/SharedTaiwanNativeMovementScene.h']:
 b=(S/rel).read_bytes();assert subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout==b;put('source/'+rel,b);refs.append({'actual_path':str(S/rel),'retained':'source/'+rel,'bytes':len(b),'sha256':h(b),'head':head})
jout('source-references.json',refs)
jout('capture-complete.json',{'verdict':'PASS','qualified_new_complete_bodies':1,'qualified_code_bytes':138,'qualified_data_bytes':3,'qualified_sites':len(ins),'ret_cleanup':12,'raw_literal231_hits':12,'credits':0,'tracked_server_edits':0,'target_execution':False})
print(json.dumps({'verdict':'PASS','code_bytes':138,'data_bytes':3,'sites':len(ins),'prior353_members':len(seal['members']),'prior353_bytes':sum(x['bytes'] for x in seal['members']),'source_refs':len(refs)}))
