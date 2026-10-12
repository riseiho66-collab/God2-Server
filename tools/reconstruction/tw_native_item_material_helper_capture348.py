"""Exactly one new full child; small authentic caller/boundary cuts. Static only."""
from pathlib import Path
import hashlib
import json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_JUMP,CS_GRP_RET
from capstone.x86 import X86_OP_IMM

OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
    with (OUT/n).open('xb') as f:f.write(b)
def js(n,v):put(n,(json.dumps(v,indent=2)+'\n').encode())
inputs=json.loads((OUT/'native-inputs.json').read_bytes())
m=Path(inputs['mapped']['path']).read_bytes();p=Path(inputs['originalPE']['path']).read_bytes()
assert sha(m)==inputs['mapped']['sha256'] and sha(p)==inputs['originalPE']['sha256']
pe=pefile.PE(data=p,fast_load=True);cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.detail=True
cuts=[]
for name,lo,hi,scope in [
    ('item-helper49B850-full',0x49B850,0x49BAE0,'authentic complete selected child; nine RET8'),
    ('preceding-boundary',0x49B83B,0x49B850,'preceding method tail/padding only; not new full method'),
    ('next-entry',0x49BAE0,0x49BAE7,'following distinct method entry only'),
    ('known3B-row-copy',0x498E00,0x498E26,'existing3B partial copy source continuity only'),
    ('known3B-selected-call',0x498EA4,0x498EF8,'existing3B partial direct sameU/row/slot caller continuity only'),
]:
    b=m[lo-0x400000:hi-0x400000];off=pe.get_offset_from_rva(lo-0x400000)
    assert b==p[off:off+len(b)] and len(b)==hi-lo
    ins=list(cs.disasm(b,lo));assert sum(i.size for i in ins)==len(b)
    put(name+'.bin',b)
    put(name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
    row=dict(name=name,begin=lo,end_exclusive=hi,bytes=len(b),sha256=sha(b),originalPE_offset=off,sites=len(ins),mapped_PE_equal=True,scope=scope)
    if name=='item-helper49B850-full':
        starts={i.address for i in ins};edges=[];calls=[];returns=[]
        for i in ins:
            if i.group(CS_GRP_JUMP):
                assert i.operands[0].type==X86_OP_IMM
                target=i.operands[0].imm
                assert target in starts
                edges.append(dict(va=i.address,mnemonic=i.mnemonic,target=target))
            if i.mnemonic=='call':
                assert i.operands[0].type==X86_OP_IMM
                calls.append(dict(va=i.address,target=i.operands[0].imm))
            if i.group(CS_GRP_RET):returns.append(dict(va=i.address,operands=i.op_str))
        assert len(returns)==9 and all(x['operands']=='8' for x in returns)
        assert ins[-1].group(CS_GRP_RET) and ins[-1].address+ins[-1].size==hi
        row.update(branches=edges,calls=calls,returns=returns)
    cuts.append(row)
js('cuts.json',dict(cuts=cuts,total_code_bytes=sum(x['bytes'] for x in cuts),new_complete_method_identities=['49B850'],prior_complete_methods=['498DD0','459A60'],new_opcode_format_route_credits=0,child_scope='Only49B850 recovered;49B720/49B770/5068C0/5077C0 opaque'))
print(json.dumps(dict(cuts=len(cuts),bytes=sum(x['bytes'] for x in cuts),full_method_bytes=656)))
