from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;U=D.parent/'round360-cn-custom-skill-health-consumer-source';P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
sb=(U/'seal.json').read_bytes();assert sha(sb)=='a01dec17f2e5e342fa9ed592fb3d34502d8d28064840dc6038f3703f0a2deacb';v=json.loads(sb);rows=[]
for m in v['members']:
 b=(U/m['path']).read_bytes();assert type(m['bytes']) is int and len(b)==m['bytes'] and sha(b)==m['sha256'];rows.append(m)
assert len(rows)==24 and sum(m['bytes'] for m in rows)==113578;put('upstream360-individual-verification.json',(json.dumps(dict(root=U.as_posix(),members=rows,seal_sha256=sha(sb),member_count=24,member_bytes=113578),indent=2)+'\n').encode())
raw=P.read_bytes();assert len(raw)==47541760 and sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;lo=0x562510;off=pe.get_offset_from_rva(lo-base);b=raw[off:off+3500];md=Cs(CS_ARCH_X86,CS_MODE_32);ins=list(md.disasm(b,lo));tsv='va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)
put('discovery/envelope.bin',b);put('discovery/linear-candidate.tsv',tsv.encode());put('original-PE-reference.json',(json.dumps(dict(path=P.as_posix(),bytes=len(raw),sha256=PIN,base=f'{base:08X}',file_offset=off,candidate_bytes=3500,whole_function=False,independent_mapped_memory_proof=False),indent=2)+'\n').encode());assert sha(P.read_bytes())==PIN;print(tsv)
