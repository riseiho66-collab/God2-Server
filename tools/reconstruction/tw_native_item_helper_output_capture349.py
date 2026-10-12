"""Two selected complete output producers plus existing lookup/caller proof. Static only."""
from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_JUMP,CS_GRP_RET
from capstone.x86 import X86_OP_IMM

O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
    with (O/n).open('xb') as f:f.write(b)
def js(n,v):put(n,(json.dumps(v,indent=2)+'\n').encode())
v=json.loads((O/'native-inputs.json').read_bytes())
m=Path(v['mapped']['path']).read_bytes();p=Path(v['originalPE']['path']).read_bytes()
assert H(m)==v['mapped']['sha256'] and H(p)==v['originalPE']['sha256']
pe=pefile.PE(data=p,fast_load=True);cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.detail=True
P=O.parent/'tw-native-spi-generic-record-write-source-340'
sb=(P/'seal.json').read_bytes();assert H(sb)=='eea7b0a2c86f7cb32a75f869acd8503650299670ed45758d69f7069a3ebefa03'
s=json.loads(sb);verified=[]
for r in s['members']:
    b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256'];verified.append(r)
assert len(verified)==s['member_count'] and sum(x['bytes'] for x in verified)==s['member_bytes']
js('prior340-individual-verification.json',dict(base=str(P),seal_sha256=H(sb),member_count=len(verified),member_bytes=sum(x['bytes'] for x in verified),members=verified))
priorcuts=json.loads((P/'native/cuts.json').read_bytes())
js('existing-generic-method-provenance.json',dict(base=str(P),cuts_metadata_sha256=H((P/'native/cuts.json').read_bytes()),known_methods=priorcuts,scope='Verified prior340 static generic396 parser/physical rowloader, reused coverage only; not actual current pointer population'))
old=O.parent/'round346-initial-owned-material-main-plan'
expected=(old/'known-definition-lookup-full.bin').read_bytes()
assert len(expected)==30 and H(expected)=='b944430a3785216d0a76d3f5ebd52d959cbd05ce85e5148ae90833a855e39ced'
assert expected==m[0x59A60:0x59A7E]
parent=O.parent/'round348-native-item-material-helper-source'
starts={int(l.split('\t')[0],16) for l in (parent/'item-helper49B850-full.tsv').read_text().splitlines()[1:]}
cuts=[]
for name,lo,hi,scope in [
    ('output-two-WORDs49B720-full',0x49B720,0x49B768,'newly closed selected72B method, twoRET0C'),
    ('output-one-WORD49B770-full',0x49B770,0x49B7AB,'newly closed selected59B method, twoRET8'),
    ('known-generic-key-lookup-full',0x459A60,0x459A7E,'existing30B method independently equal prior346 bin, credit0'),
    ('known-parent-two-output-call',0x49B884,0x49B8C1,'partial existing49B850 stack/output/call continuation'),
    ('known-parent-one-output-call',0x49B8CB,0x49B8E1,'partial existing49B850 stack/output/call continuation'),
    ('first-preceding-RET-padding',0x49B718,0x49B720,'preceding method RET/padding only, no complete-method claim'),
    ('first-following-padding',0x49B768,0x49B770,'between selected methods padding only'),
    ('second-following-padding-entry',0x49B7AB,0x49B7B3,'padding and distinct next method entry only')]:
    b=m[lo-0x400000:hi-0x400000];off=pe.get_offset_from_rva(lo-0x400000)
    assert b==p[off:off+len(b)]
    ins=list(cs.disasm(b,lo));assert sum(i.size for i in ins)==len(b)
    put(name+'.bin',b)
    put(name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
    row=dict(name=name,begin=lo,end_exclusive=hi,bytes=len(b),sha256=H(b),originalPE_offset=off,sites=len(ins),mapped_PE_equal=True,scope=scope)
    if 'parent-' in name:
        assert lo in starts and hi in starts and all(i.address in starts for i in ins)
        row['aligned_to_verified_complete348_parent']=True
    if name.endswith('-full'):
        entries={i.address for i in ins};edges=[];calls=[];returns=[]
        for i in ins:
            if i.group(CS_GRP_JUMP):
                assert i.operands[0].type==X86_OP_IMM and i.operands[0].imm in entries
                edges.append(dict(va=i.address,target=i.operands[0].imm,mnemonic=i.mnemonic))
            if i.mnemonic=='call':
                assert i.operands[0].type==X86_OP_IMM
                calls.append(dict(va=i.address,target=i.operands[0].imm))
            if i.group(CS_GRP_RET):returns.append(dict(va=i.address,operands=i.op_str))
        assert len(returns)==2 and ins[-1].group(CS_GRP_RET)
        if lo in (0x49B720,0x49B770):assert len(calls)==1 and calls[0]['target']==0x459A60
        else:assert not calls
        row.update(branches=edges,calls=calls,returns=returns)
    cuts.append(row)
js('cuts.json',dict(cuts=cuts,selected_new_complete_method_bytes=131,existing_complete_lookup_bytes=30,total_cut_bytes=sum(x['bytes'] for x in cuts),new_complete_method_identities=['49B720','49B770'],known_coverage_not_recounted=['49B850','459A60','459420','4599B0'],new_opcode_format_route_credits=0))
print(json.dumps(dict(selected_bytes=131,total_cut_bytes=sum(x['bytes'] for x in cuts),cuts=len(cuts))))
