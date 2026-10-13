from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;A=D.parent;P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
U=A/'round359-cn-custom-skill-action3-source';seal=(U/'seal.json').read_bytes();assert sha(seal)=='d5fa4a861f3e47c7914a9141d835f33faaf76c9705c2a433edac6f4b1401a1f3';v=json.loads(seal);rows=[]
for m in v['members']:
 p=U/m.get('path',m.get('name'));b=p.read_bytes();assert type(m['bytes']) is int and len(b)==m['bytes'] and sha(b)==m['sha256'];rows.append(m)
assert len(rows)==64 and sum(m['bytes'] for m in rows)==186882
put('upstream-individual-verification.json',(json.dumps(dict(root=str(U),seal_sha256=sha(seal),members=rows,member_count=64,member_bytes=186882),indent=2)+'\n').encode())
raw=P.read_bytes();assert len(raw)==47541760 and sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;lo=0x5634e0;size=3500;off=pe.get_offset_from_rva(lo-base);b=raw[off:off+size]
md=Cs(CS_ARCH_X86,CS_MODE_32);ins=list(md.disasm(b,lo));tsv='va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)
put('discovery/envelope.bin',b);put('discovery/linear-candidate.tsv',tsv.encode());put('original-PE-reference.json',(json.dumps(dict(path=str(P),bytes=len(raw),sha256=PIN,ImageBase=f'{base:08X}',file_offset=off,candidate_start=f'{lo:08X}',candidate_size=size,whole_function=False,independent_mapped_memory_proof=False),indent=2)+'\n').encode())
assert sha(P.read_bytes())==PIN
print(tsv)
