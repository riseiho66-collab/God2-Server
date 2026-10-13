from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;S=Path('C:/Users/risei/Desktop/God2/God2-Server');P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
raw=P.read_bytes();assert len(raw)==47541760 and sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=Cs(CS_ARCH_X86,CS_MODE_32)
for name,lo,size in [('553bc0-envelope',0x553bc0,1024),('54a6a5-caller',0x54a6a5,0x54a6e9-0x54a6a5)]:
 off=pe.get_offset_from_rva(lo-base);b=raw[off:off+size];ins=list(md.disasm(b,lo));text='va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins);put('discovery/'+name+'.bin',b);put('discovery/'+name+'.tsv',text.encode());print(text)
old=S/'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-owner-frontier-01/root-native/00553bc0.c';ob=old.read_bytes();put('old-structural-source-reference.json',(json.dumps(dict(actual_path=old.as_posix(),bytes=len(ob),sha256=sha(ob),metadata_declared_size=710,prior_C_not_independent_byte_boundary_proof=True),indent=2)+'\n').encode());put('original-PE-reference.json',(json.dumps(dict(actual_path=P.as_posix(),bytes=len(raw),sha256=PIN,ImageBase=f'{base:08X}',full_image_copied=False,independent_mapped_memory_proof=False),indent=2)+'\n').encode());assert sha(P.read_bytes())==PIN
