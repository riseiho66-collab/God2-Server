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
extras=[]
for root,dig,count,total in [(A/'round352-native-item-row-prefix-writer-source','a88f087fff38d036f106fc279f3e70445341ec3b7fbc5210d9952f7f02a1d27c',50,153368),(A.parent/'20261012/round348-native-item-material-helper-source','84f9106d09283a184b3361aff4d8a4bfbd5ac1946fedfe91a8fbae538f339c9f',27,84522)]:
 sb=(root/'seal.json').read_bytes();assert h(sb)==dig;z=json.loads(sb);seen=set()
 for r in z['members']:
  p=root/r['path'];assert p.resolve().is_relative_to(root.resolve()) and r['path'] not in seen;seen.add(r['path']);b=p.read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
 assert len(z['members'])==count and sum(r['bytes'] for r in z['members'])==total
 extras.append(dict(root=root.as_posix(),seal_sha256=dig,members=count,member_bytes=total,individual_members=z['members']))
out('known-row-source-extra-individual-verification.json',extras)
m=(P/'native-image.bin').read_bytes();raw=(P/'originalPE.bin').read_bytes();assert h(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' and h(raw)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde';pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
# Reference known authentic full348 callee in place, no recapture or newmethod.
root=A.parent/'20261012/round348-native-item-material-helper-source';kp=root/'item-helper49B850-full.bin';b=kp.read_bytes();lo=0x49b850;off=pe.get_offset_from_rva(lo-B)
assert len(b)==656 and h(b)=='df64f29cc15e560305cac16c5be734514fa9b1e0e1f90af894da20c0cb267b14' and b==m[lo-B:lo-B+len(b)]==raw[off:off+len(b)]
isites=list(md.disasm(b,lo));assert len(isites)==224
calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in isites if i.mnemonic=='call']
out('known49B850-in-place-reference.json',dict(path=kp.as_posix(),bytes=len(b),sha256=h(b),start='0049B850',end='0049BAE0',sites=224,PE_offset=off,PE_and_mapped_equal=True,calls=calls,recaptured=False,credits=0,canonical_pointer_lineage='Actual prior3B passes row pointer EBP. Known body reads EBP and passes keys, own-stack outputs, or UI/control operands to children. No canonical row destination forwarding qualified by this new review.'))
indices=json.loads((O/'finite-two-window-index.json').read_bytes())+json.loads((O/'finite-five-followup-windows.json').read_bytes());actual=[]
for z in indices:
 lo=int(z['start'],16);hi=int(z['end'],16);bb=m[lo-B:hi-B];assert bb==raw[z['PE_offset']:z['PE_offset']+len(bb)] and len(bb)==z['bytes'] and h(bb)==z['sha256']
 sites=list(md.disasm(bb,lo));actual.append(dict(**z,arbitrary_decode_sites=len(sites),decoded_bytes=sum(i.size for i in sites),authentic_entry=False,whole_body=False))
out('discovery-seven-window-readback.json',dict(windows=actual,raw_window_bytes=sum(z['bytes'] for z in actual),arbitrary_decoded_sites=sum(z['arbitrary_decode_sites'] for z in actual),qualified_whole_code_bytes=0,qualified_sites=0,data_bytes=0))
sections=[]
for s in pe.sections:
 end=min(s.VirtualAddress+s.SizeOfRawData,len(m));sections.append(dict(name=s.Name.rstrip(b'\0').decode(errors='replace'),RVA=s.VirtualAddress,raw_offset=s.PointerToRawData,raw_bytes=s.SizeOfRawData,mapped_overlap=max(0,end-s.VirtualAddress),characteristics=s.Characteristics,execute_flag=bool(s.Characteristics&0x20000000)))
out('PE-sections-and-bounded-scope.json',dict(sections=sections,scan='no new image scan; historical32 LEA address-materialization candidates narrowed to seven fixed raw windows',imprec_unmapped_tail_not_reviewed=True,global_absence_claimed=False))
out('qualified-scope.json',dict(complete_bodies=[],new_code_bytes=0,new_sites=0,data_bytes=0,partial_authentic_code_bytes=0,raw_discovery_windows=7,raw_discovery_bytes=sum(z['bytes'] for z in actual),historical_LEA_candidates=32,native_credit=0,opcode_credit=0,format_credit=0,authority_credit=0,fullroute_credit=0,remaining='genuine canonical postreset row+1..3/full24 incoming or computed destination; actual owner/phase/wire/currentness and independent server acquisition/issuer remain OPEN'))
print(json.dumps(dict(extra_members=77,extra_bytes=237890,known_callee_in_place=656,discovery_windows=7,discovery_bytes=sum(z['bytes'] for z in actual),qualified_bytes=0,arbitrary_sites=sum(z['arbitrary_decode_sites'] for z in actual))))
