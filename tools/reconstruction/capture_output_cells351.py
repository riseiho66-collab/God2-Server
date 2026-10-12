"""Only read/hash/PE/Capstone static source; never executes or imports target code."""
from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent
A=O.parent
N=A/'tw-native-entry-body-alias-and-remote-opaque-315'/'native-entry'
H=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
    with (O/n).open('xb') as f:f.write(b)
def js(n,v):put(n,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
def main():
    im=(N/'native-image.bin').read_bytes();raw=(N/'originalPE.bin').read_bytes()
    assert len(im)==3174400 and H(im)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert len(raw)==3183616 and H(raw)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    js('native-inputs.json',dict(inputs=[dict(path=str(N/n),bytes=len(b),sha256=H(b)) for n,b in [('native-image.bin',im),('originalPE.bin',raw)]],image_base=pe.OPTIONAL_HEADER.ImageBase,sections=[dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=s.VirtualAddress,raw_offset=s.PointerToRawData,raw_bytes=s.SizeOfRawData,virtual_bytes=s.Misc_VirtualSize,flags=s.Characteristics,execute=bool(s.Characteristics&0x20000000)) for s in pe.sections],limit='All original execute flags clear; actual aligned CALL41EAB2 in previously complete41EA00 proves entry, not guessed prologue.'))
    rr=[]
    for dirname in ['round350-native-item-ui-child-arguments-source','round349-native-item-ui-primary-source']:
        d=A/dirname;p=d/'seal.json';v=json.loads(p.read_bytes());rows=[]
        for r in v['members']:
            b=(d/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256'];rows.append(r)
        assert len(rows)==v['member_count'] and sum(r['bytes'] for r in rows)==v['member_bytes']
        rr.append(dict(base=str(d),seal_sha256=H(p.read_bytes()),member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),members=rows))
    js('prior-individual-verification.json',rr)
    refs=[]
    for dirname,name,start,end in [('round350-native-item-ui-child-arguments-source','child41EA00-full.bin',0x41ea00,0x41ebe7),('round349-native-item-ui-primary-source','primary5068C0-full.bin',0x5068c0,0x506930)]:
        p=A/dirname/name;b=p.read_bytes();off=pe.get_offset_from_rva(start-0x400000);assert b==im[start-0x400000:end-0x400000]==raw[off:off+len(b)]
        refs.append(dict(path=str(p),begin=start,end_exclusive=end,bytes=len(b),sha256=H(b),originalPE_offset=off,mapped_PE_equal=True))
    js('actual-parent-source-references.json',refs)
    start=0x41e710;end=0x41e7b2;b=im[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000);assert b==raw[off:off+len(b)]
    ins=list(md.disasm(b,start));assert sum(i.size for i in ins)==len(b);sites={i.address for i in ins}
    branches=[dict(va=i.address,target=i.op_str) for i in ins if i.mnemonic.startswith('j')]
    for i in ins:
        if i.mnemonic.startswith('j'):assert i.operands[0].imm in sites
    rets=[dict(va=i.address,operand=i.op_str) for i in ins if i.mnemonic=='ret'];assert [r['va'] for r in rets]==[0x41e724,0x41e7af] and all(r['operand']=='0x14' for r in rets)
    assert not any(i.mnemonic=='call' for i in ins) and len(branches)==4
    put('output41E710-full.bin',b);put('output41E710-full.tsv',('VA\traw\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
    pad=im[0x1e7b2:0x1e7c0];poff=pe.get_offset_from_rva(0x1e7b2);assert pad==raw[poff:poff+len(pad)]==b'\x90'*14;put('following-padding.bin',pad)
    g=im[0x185bd8:0x185bd9];goff=pe.get_offset_from_rva(0x185bd8);assert g==raw[goff:goff+1];put('initial585BD8-byte.bin',g)
    row=dict(name='output41E710-full',begin=start,end_exclusive=end,bytes=len(b),sha256=H(b),originalPE_offset=off,mapped_PE_equal=True,sites=len(ins),whole_function=True,returns=rets,branches=branches,calls=[])
    js('cuts.json',dict(cuts=[row],whole_code_bytes=len(b),padding_bytes=14,data_operand_bytes=1,total_data_bytes=15,padding=dict(begin=0x41e7b2,end_exclusive=0x41e7c0,bytes=14,sha256=H(pad),originalPE_offset=poff),global_byte=dict(va=0x585bd8,bytes=1,initial_value=g[0],sha256=H(g),originalPE_offset=goff,limit='Original PE initial value only; runtime/current writers and current value not observed or qualified.'),method_credit=0,opcode_credit=0,format_credit=0,route_credit=0))
    p=Path('C:/Users/risei/Desktop/God2/God2-Server/docs/research/current-equipment-instance-projection-20260926.md');z=p.read_bytes();js('historical-source-reference.json',dict(path=str(p),bytes=len(z),sha256=H(z),scope='Historical document already lists complete41E710 continuation; reference only, never execute/import old scripts or promote fixtures.'))
    js('capture-complete.json',dict(success=True,whole_code_bytes=len(b),sites=len(ins),direct_branches=4,conditional_branches=3,padding_bytes=14,data_operand_bytes=1,scope='Static only; no tracked/native/runtime/API/CRT/VM/parser/resource/codec/SQL/compiler/build/tests execution',discovery='First read-only window41E710..41EA00 revealed actual162B/twoRET/padding. Following adjacent methods remained outside recovered scope. Preliminary3branch wording counted conditional branches only; final4 includes unconditional loopback. No failed capture.'))
    print(json.dumps(dict(success=True,cut=row,padding_bytes=14,data_operand_bytes=1)))
if __name__=='__main__':main()
