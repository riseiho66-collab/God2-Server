"""347 static original-file custody and bounded disassembly only. LF source.
No native/client/server/parser/codec/VM/DB execution and no repository writes.
"""
from pathlib import Path
import hashlib, json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

OUT = Path(__file__).resolve().parent
A = OUT.parent
ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
PIN = A/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
BASE = 0x400000

def sha(b): return hashlib.sha256(b).hexdigest()
def save(name, value):
    p=OUT/name; p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists(): raise RuntimeError('Preserve existing member: '+name)
    p.write_bytes(value if isinstance(value, bytes) else
        (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
def ref(p):
    b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=sha(b),copied=False)

def main():
    if (OUT/'capture-complete.json').exists() or (OUT/'seal.json').exists():
        raise RuntimeError('Successful capture is immutable; do not rerun')
    mapped=(PIN/'native-image.bin').read_bytes()
    original=(PIN/'originalPE.bin').read_bytes()
    assert sha(mapped)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=original,fast_load=True)
    assert pe.OPTIONAL_HEADER.ImageBase==BASE
    save('input-references.json',[ref(PIN/'native-image.bin'),ref(PIN/'originalPE.bin')])
    save('pe-sections.json',[dict(name=s.Name.rstrip(b'\0').decode('ascii'),
        rva=s.VirtualAddress,virtual_size=s.Misc_VirtualSize,raw_offset=s.PointerToRawData,
        raw_size=s.SizeOfRawData,characteristics=s.Characteristics,
        execute_flag=bool(s.Characteristics & 0x20000000)) for s in pe.sections])
    md=Cs(CS_ARCH_X86,CS_MODE_32)
    cuts=[]
    spans=[
        ('role-initializer-whole',0x468160,0x468924,True),
        ('actor-reset-and-primary-clear-whole',0x468120,0x46815A,True),
        ('primary-bank-clear-whole',0x497FE0,0x498026,True),
        ('primary-clear-catalog-cache-whole',0x498030,0x49838E,True),
        ('retained-primary-setup-whole',0x4817C0,0x481BD9,True),
        ('retained-2a-waiter-whole',0x415690,0x415727,True),
        ('retained-parent-entry-argument-storage',0x464910,0x4649B2,False),
        ('retained-parent-formal1-connected-branch',0x465157,0x4651A1,False),
        ('retained-primary-setup-invocation',0x465274,0x465328,False),
        ('retained-outbound-tail',0x4654F7,0x46553D,False),
    ]
    for name,start,end,whole in spans:
        b=mapped[start-BASE:end-BASE]
        off=pe.get_offset_from_rva(start-BASE)
        assert original[off:off+len(b)]==b,(name,'PE mismatch')
        ins=list(md.disasm(b,start))
        assert sum(i.size for i in ins)==len(b),(name,'partial instruction')
        if whole: assert ins[-1].mnemonic=='ret',(name,'missing ending RET')
        rows=[dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,
            operands=i.op_str) for i in ins]
        save('native/'+name+'.bin',b)
        save('native/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+
            ''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
        cuts.append(dict(name=name,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',
            bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True,
            instructions=len(ins),complete_actual_method=whole,
            returns=[r for r in rows if r['mnemonic']=='ret'],
            calls=[r for r in rows if r['mnemonic']=='call'],
            jumps=[r for r in rows if r['mnemonic'].startswith('j')]))
    data=[]
    for name,start,end in [('role-switch-table',0x468924,0x468944),
        ('catalog-key-group-one',0x5905F0,0x59061E),
        ('catalog-key-group-two',0x590748,0x59079C)]:
        b=mapped[start-BASE:end-BASE]; off=pe.get_offset_from_rva(start-BASE)
        assert original[off:off+len(b)]==b
        save('native/'+name+'.bin',b)
        data.append(dict(name=name,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',
            bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True,
            words_le=list(struct.unpack('<'+'H'*(len(b)//2),b))))
    targets=struct.unpack('<8I',mapped[0x68924:0x68944])
    init=list(md.disasm(mapped[0x68160:0x68924],0x468160))
    addresses={i.address for i in init}
    assert all(t in addresses for t in targets)
    direct=[]; indirect=[]
    for i in init:
        if i.mnemonic.startswith('j'):
            if i.op_str.startswith('0x'):
                target=int(i.op_str,16); assert target in addresses
                direct.append(dict(site=f'{i.address:08X}',target=f'{target:08X}'))
            else: indirect.append(dict(site=f'{i.address:08X}',operand=i.op_str))
    assert len(indirect)==1 and indirect[0]['site']=='00468763'
    save('role-cfg-boundaries.json',dict(start='00468160',end_exclusive='00468924',
        sites=len(init),bytes=1988,direct_jumps=direct,indirect_jumps=indirect,
        table_targets=[f'{t:08X}' for t in targets],
        return_sites=[f'{i.address:08X}' for i in init if i.mnemonic=='ret'],
        limit='Direct branch/table closure only; CALL children and exceptional effects remain opaque.'))
    prior=[]
    p311=A/'tw-native-visibility-state-and-source-311/native-visibility/spans'
    for name,start,end in [('role_initializer_actualentry_map',0x468160,0x468329),
        ('role_initializer_remaining_boundary_map',0x468328,0x468852)]:
        p=p311/(name+'.bin'); b=p.read_bytes()
        assert b==mapped[start-BASE:end-BASE]
        prior += [dict(**ref(p),equal_current=True,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}'),
            ref(p311/(name+'.json'))]
    p329=A/'tw-native-petegg-selection-source-329/native'
    for name,start,end in [('primary-setup-complete',0x4817C0,0x481BD9),
        ('retained-primary-setup-invocation',0x465274,0x465328)]:
        p=p329/(name+'.bin'); assert p.read_bytes()==mapped[start-BASE:end-BASE]
        prior += [dict(**ref(p),equal_current=True),ref(p329/(name+'.tsv'))]
    save('prior-member-inplace-references.json',prior)
    sources=['AGENTS.md','docs/GOAL_ACCEPTANCE.md',
        'docs/research/current-world-initialization-sequence-20260919.md',
        'tools/reconstruction/tw_native_entry_caller210.py',
        'src/game/RecoveredNormalWorldInitialization.cpp',
        'src/game/RecoveredNormalWorldInitialization.h']
    # Optional current source filenames vary; never invent a referenced file.
    save('source-references.json',[ref(ROOT/p) for p in sources if (ROOT/p).is_file()])
    save('cuts.json',cuts); save('data-cuts.json',data)
    save('prior311-boundary-correction.json',dict(
        old_ranges=['00468160..00468329','00468328..00468852'],
        old_union_bytes=1778,overlap_bytes=1,new_whole_bytes=1988,extension_bytes=210,
        correction='Old first cut decodes456/457 bytes; second extends to POP EDI at468851. Neither union nor second includes all returns or fallback. Actual end is468924; all four RET12 are4681CC/46885B/4688CD/468921. Preserve historical members, correct any complete-method interpretation only.',
        new_method_credit=0,new_opcode_credit=0,new_format_credit=0,new_route_credit=0))
    save('capture-complete.json',dict(success=True,static_only=True,
        complete_method_cuts=sum(c['complete_actual_method'] for c in cuts),
        code_bytes=sum(c['bytes'] for c in cuts),data_bytes=sum(d['bytes'] for d in data),
        instruction_sites=sum(c['instructions'] for c in cuts),
        original_files_copied=False,new_route_credit=0,new_method_credit=0))
    print(json.dumps(dict(success=True,code_bytes=sum(c['bytes'] for c in cuts),
        data_bytes=sum(d['bytes'] for d in data),cuts=len(cuts))))

if __name__=='__main__': main()
