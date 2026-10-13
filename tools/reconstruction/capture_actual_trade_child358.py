from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent;A=O.parent;P=A.parent/'20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry';B=0x400000
h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def out(n,v):put(n,(json.dumps(v,indent=2)+'\n').encode())
m=(P/'native-image.bin').read_bytes();raw=(P/'originalPE.bin').read_bytes();assert h(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' and h(raw)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);lo,hi=0x49e0c0,0x49e19d;b=m[lo-B:hi-B];off=pe.get_offset_from_rva(lo-B);assert b==raw[off:off+len(b)]
ins=list(md.disasm(b,lo));assert sum(i.size for i in ins)==len(b);starts={i.address for i in ins};branches=[]
for i in ins:
 if i.mnemonic.startswith('j'):
  target=int(i.op_str,16);assert target in starts;branches.append(dict(va=f'{i.address:08X}',mnemonic=i.mnemonic,target=f'{target:08X}'))
rets=[i for i in ins if i.mnemonic=='ret'];assert len(rets)==1 and rets[0].address==0x49e19a and rets[0].op_str=='8'
put('qualified/native/actual-trade-row-refresh49E0C0-full.bin',b)
t='va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins);put('qualified/native/actual-trade-row-refresh49E0C0-full.tsv',t.encode())
# Supporting3 padding bytes are data/boundary context, never code credit.
pad=m[hi-B:hi-B+3];assert pad==b'\x90'*3 and pad==raw[off+len(b):off+len(b)+3];put('boundary/after-RET-padding.bin',pad)
row=dict(name='actual-trade-auxiliary-row-refresh',start=f'{lo:08X}',end=f'{hi:08X}',bytes=len(b),sha256=h(b),PE_offset=off,sites=len(ins),authentic_direct_CALL_targets=['0049DEC9','0049DED9'],return_sites=[dict(va='0049E19A',cleanup=8)],direct_branches=branches,full_intraprocedural_body=True,all_bytes_PE_equal=True,novelty='new fullclosure within inspected353 named-opaque child frontier only; no global method novelty claim')
out('qualified/qualified-spans.json',[row])
calls=[dict(va=f'{i.address:08X}',target=i.op_str,descendant_expanded=False) for i in ins if i.mnemonic=='call']
out('qualified/source-relations.json',dict(caller='prior353 actual49DE50 whole in place; actual WORLD4F primaryU call source already retained',receiver='full supplied object pointer ECX retained ESI',formal1='signedlowWORDgroup MOVSX EBP,[formal1] no local range guard; actualparent literal5/7',formal2='fullDWORD supplied rowbase no null/capacity check; actualparent U866E8 orU867A8',rows='EDI0..7; EBX starts base+4 and adds24; no whole-row copy',reads=[dict(va='0049E0D5',value='current rowDWORD4 lowWORD key before49B720'),dict(va='0049E10F',value='fresh current rowDWORD4 lowWORD after49B720+5068C0 before49B770'),dict(va='0049E124',value='fresh current rowDWORD4 lowWORD TEST after49B770'),dict(va='0049E134',value='signed rowBYTE0 only after currentkeynonzero and signedWORD returnedthreshold>1')],own_stack='formalcell outputs[SP18/1C] from49B720 are loaded signedWORD; stack WORD12 from49B770 compares signed<=1',prefix_fields='row+1..3 never directly read or written by thisbody; row+4..23 outside lowkey not copied',direct_nonstack_stores=0,children=calls,unknown='child mutation/current suppliedU affinity/livecatalog and rowread validity; no finalstate or absence acrosschildren',canonical_material_qualification=False,issuer_qualification=False,loop='known nonvolatile ABI EDI/EBX/ESI/EBP preserved acrossnormalchildren; faultfree8rowreadability prerequisite',registers='UI handle only AX/CX/DX written then FULLDWORD pushed; upper16 retained, not canonicalized',data_bytes=0,boundary_padding_bytes=3))
out('successful-capture.json',dict(status='successful_once',qualified_complete_bodies=1,qualified_code_bytes=len(b),qualified_sites=len(ins),data_bytes=0,boundary_padding_bytes=3,raw_discovery_window_bytes=240,new_canonical_or_grant_credit=0,method_coverage='one authentic child wholebody within retained opaque frontier'))
print(json.dumps(row))
