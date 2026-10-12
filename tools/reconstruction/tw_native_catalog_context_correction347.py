"""Additive347 actual stack-displacement correction; static files only, LF.
Preserve original347; no repository edits/native/runtime/parser/codec/DB calls.
"""
from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent
A=O.parent
OLD=A/'round347-normal-entry-native-readiness-source'
PIN=A/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
B=0x400000
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Preserve member '+n)
    p.write_bytes(v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def main():
    if (O/'capture-complete.json').exists() or (O/'seal.json').exists():raise RuntimeError('Preserve success')
    raw=(PIN/'native-image.bin').read_bytes();pebytes=(PIN/'originalPE.bin').read_bytes()
    assert sha(raw)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(pebytes)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=pebytes,fast_load=True);assert pe.OPTIONAL_HEADER.ImageBase==B
    oldseal=(OLD/'seal.json').read_bytes()
    assert sha(oldseal)=='10d2c4abe81d233eb6dc415c1025b05913f4292da1a99d4f24ddb5a2f90742a5'
    old=json.loads(oldseal)
    for r in old['members']:
        b=(OLD/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
    save('prior347-individual-members-verified.json',dict(seal_path=str(OLD/'seal.json'),
        seal_sha256=sha(oldseal),member_count=len(old['members']),
        member_bytes=sum(r['bytes'] for r in old['members']),members=old['members'],
        scope='Every original347 member verified in place; none overwritten or copied.'))
    refs=[]
    for p in [PIN/'native-image.bin',PIN/'originalPE.bin',OLD/'REPORT.md']:
        b=p.read_bytes();refs.append(dict(path=str(p),bytes=len(b),sha256=sha(b),copied=False))
    save('input-references.json',refs)
    md=Cs(CS_ARCH_X86,CS_MODE_32);cuts=[]
    for name,s,e in [('known-parent-context-write',0x465274,0x465328),
        ('known-setup-parameter-prefix',0x4817C0,0x481808),
        ('known-setup-ret8',0x481BD6,0x481BD9),
        ('known-setup-cache-call',0x481A1A,0x481A21)]:
        b=raw[s-B:e-B];off=pe.get_offset_from_rva(s-B)
        assert pebytes[off:off+len(b)]==b
        ins=list(md.disasm(b,s));assert sum(i.size for i in ins)==len(b)
        save('native/'+name+'.bin',b)
        save('native/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+
            ''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
        cuts.append(dict(name=name,start_va=f'{s:08X}',end_exclusive_va=f'{e:08X}',
            bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True,
            sites=len(ins),complete_method=False,
            scope='Known selected span from old347 authentic full entry; no interior function created.'))
    # Verify authentic entry/full-method custody independently, without re-copying.
    complete=[]
    for name,s,e in [('retained-parent-entry-argument-storage',0x464910,0x4649B2),
        ('retained-primary-setup-whole',0x4817C0,0x481BD9),
        ('primary-clear-catalog-cache-whole',0x498030,0x49838E)]:
        p=OLD/'native'/(name+'.bin');b=p.read_bytes()
        assert b==raw[s-B:e-B]
        off=pe.get_offset_from_rva(s-B);assert b==pebytes[off:off+len(b)]
        complete.append(dict(path=str(p),bytes=len(b),sha256=sha(b),
            equal_current=True,pe_equal=True,copied=False))
    save('known-boundary-inplace-references.json',complete)
    rows=[dict(va='00465274',esp_relative_to_S=0,meaning='Define S as current ESP; EBP=Main from actual464937.'),
        dict(va='004652DA',esp_relative_to_S=0,meaning='EDX=DWORD[Main+AA36480].'),
        dict(va='004652FB',esp_relative_to_S=0,meaning='ECX=P=S+24h.'),
        dict(va='00465303',esp_relative_to_S=-4,meaning='PUSH Main+39Ch; formal2.'),
        dict(va='00465310',esp_relative_to_S=-8,meaning='PUSH P; formal1. ECX still P at this push.'),
        dict(va='00465311',esp_relative_to_S=-8,meaning='ECX=U=Main+A7F2F6C.'),
        dict(va='00465317',esp_relative_to_S=-8,meaning='DWORD[ESP+4Ch]=EDX -> S+44h=P+20h; no intervening EDX assignment/call since4652DA.'),
        dict(va='00465323',esp_relative_to_S=-12,meaning='CALL pushes return address; callee entry SP=C=S-0Ch; formal1 atC+4=P.'),
        dict(va='004817C3',esp_relative_to_S=-28,meaning='After four callee PUSHes, ESP=C-10h=S-1Ch.'),
        dict(va='004817C4',esp_relative_to_S=-28,meaning='EDI=DWORD[ESP+14h]=DWORD[S-8]=P.'),
        dict(va='004817C8',esp_relative_to_S=-28,meaning='ESI=ECX=U.'),
        dict(va='004817FF',esp_relative_to_S=-28,meaning='EAX=DWORD[EDI+20h]=original DWORD[Main+AA36480] sampled4652DA.'),
        dict(va='00481802',esp_relative_to_S=-28,meaning='DWORD[ESI+CFF70]=EAX; first concrete supplier, before any callee child.'),
        dict(va='00481BD6',esp_relative_to_S=0,meaning='Normal epilogue restores4 regs then RET8 consumes return4+arguments8, returning callerESP=S.')]
    assert -8+0x4C==0x44 and 0x44-0x24==0x20
    assert (-12-16)+0x14==-8 and -12+4==-8
    save('stack-source-proof.json',dict(addresses='hexadecimal VAs/offsets; signed ESP differences decimal',
        S='Current caller ESP at465274, not assumed identical to function-entry SP.',P='S+24h',
        source='Actual sampled DWORD[Main+AA36480] at4652DA',destination='U+CFF70 at481802',
        relation='MainAA36480 -> EDX -> (S-8)+4Ch = S+44h = P+20h -> [EDI+20h] -> U+CFF70',
        distinct_adjacent='MainAA36478 at465294/4652A4 -> S+3Ch = P+18h, not P+20h.',
        ordered_rows=rows,
        premises=['Actual source path reaches465274 and maintains native calling convention/EBPMain.',
            'Stack/context/Main/U are valid readable/writable, no fault or exceptional exit.',
            'No code execution is observed; arithmetic is source-only.',
            'Intervening children after481802 remain opaque; later498030 needs current U+CFF70/table lifetime/stability, not an automatic equality assumption.'],
        new_methods=0,new_formats=0,new_opcodes=0,new_routes=0))
    save('cuts.json',cuts)
    save('capture-complete.json',dict(success=True,static_only=True,cuts=len(cuts),
        code_bytes=sum(c['bytes'] for c in cuts),data_bytes=0,
        sites=sum(c['sites'] for c in cuts),prior_members_verified=len(old['members']),
        new_byte_coverage=0,new_method_credit=0,new_route_credit=0))
    print(json.dumps(dict(success=True,cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts),
        data_bytes=0,prior_members_verified=len(old['members']))))
if __name__=='__main__':main()
