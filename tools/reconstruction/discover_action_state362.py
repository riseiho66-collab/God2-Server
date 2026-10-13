from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;U=D.parent/'round361-cn-skill-queued-delta-reader-source';P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
sb=(U/'seal.json').read_bytes();assert sha(sb)=='6347e4dfa8da5523bf4926a53d2b88773cc708bb9cb634188895d93acd16a824';v=json.loads(sb);rows=[]
for m in v['members']:
 b=(U/m['path']).read_bytes();assert type(m['bytes']) is int and len(b)==m['bytes'] and sha(b)==m['sha256'];rows.append(m)
assert len(rows)==19 and sum(m['bytes'] for m in rows)==67662;put('upstream361-individual-verification.json',(json.dumps(dict(root=U.as_posix(),members=rows,member_count=19,member_bytes=67662,seal_sha256=sha(sb)),indent=2)+'\n').encode())
raw=P.read_bytes();assert len(raw)==47541760 and sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;lo=0x564a30;off=pe.get_offset_from_rva(lo-base);b=raw[off:off+4000];md=Cs(CS_ARCH_X86,CS_MODE_32);ins=list(md.disasm(b,lo));text='va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)
put('discovery/envelope.bin',b);put('discovery/linear-candidate.tsv',text.encode());put('original-PE-reference.json',(json.dumps(dict(path=P.as_posix(),bytes=len(raw),sha256=PIN,ImageBase=f'{base:08X}',file_offset=off,candidate_code_cap=4000,whole_function=False,independent_mapped_memory_proof=False),indent=2)+'\n').encode());assert sha(P.read_bytes())==PIN;print(text)
