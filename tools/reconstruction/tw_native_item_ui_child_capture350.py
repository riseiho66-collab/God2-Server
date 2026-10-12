"""Bounded read/hash/PE/Capstone only; no target, runtime or codec imports."""
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
    js('native-inputs.json',dict(inputs=[dict(path=str(N/n),bytes=len(b),sha256=H(b)) for n,b in [('native-image.bin',im),('originalPE.bin',raw)]],image_base=pe.OPTIONAL_HEADER.ImageBase,sections=[dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=s.VirtualAddress,raw_offset=s.PointerToRawData,raw_bytes=s.SizeOfRawData,virtual_bytes=s.Misc_VirtualSize,flags=s.Characteristics,execute=bool(s.Characteristics&0x20000000)) for s in pe.sections],limit='Execute flags all clear are not absence of code; known aligned full parent CALL506927 proves child entry41EA00.'))
    receipts=[]
    for name in ['round349-native-item-ui-primary-source','round348-native-item-material-helper-source','round349-native-item-helper-output-source']:
        d=A/name;p=d/'seal.json';v=json.loads(p.read_bytes());rows=[]
        for r in v['members']:
            b=(d/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256'];rows.append(r)
        assert len(rows)==v['member_count'] and sum(r['bytes'] for r in rows)==v['member_bytes']
        receipts.append(dict(base=str(d),seal_sha256=H(p.read_bytes()),member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),members=rows))
    js('prior-individual-verification.json',receipts)
    refs=[]
    for dirname,name,start,end in [('round349-native-item-ui-primary-source','primary5068C0-full.bin',0x5068c0,0x506930),('round348-native-item-material-helper-source','item-helper49B850-full.bin',0x49b850,0x49bae0),('round349-native-item-helper-output-source','output-two-WORDs49B720-full.bin',0x49b720,0x49b768)]:
        p=A/dirname/name;b=p.read_bytes();off=pe.get_offset_from_rva(start-0x400000)
        assert b==im[start-0x400000:end-0x400000]==raw[off:off+len(b)]
        refs.append(dict(path=str(p),begin=start,end_exclusive=end,bytes=len(b),sha256=H(b),originalPE_offset=off,mapped_PE_equal=True))
    js('actual-parent-source-references.json',refs)
    start=0x41ea00;end=0x41ebe7;b=im[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000);assert b==raw[off:off+len(b)]
    ins=list(md.disasm(b,start));assert sum(i.size for i in ins)==len(b);starts={i.address for i in ins}
    for i in ins:
        if i.mnemonic.startswith('j'):assert i.operands[0].imm in starts
    rets=[dict(va=i.address,operand=i.op_str) for i in ins if i.mnemonic=='ret'];assert [r['va'] for r in rets]==[0x41ea29,0x41ea51,0x41ebe4] and all(r['operand']=='0x10' for r in rets)
    put('child41EA00-full.bin',b);put('child41EA00-full.tsv',('VA\traw\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
    row=dict(name='child41EA00-full',begin=start,end_exclusive=end,bytes=len(b),sha256=H(b),originalPE_offset=off,mapped_PE_equal=True,sites=len(ins),whole_function=True,returns=rets,calls=[dict(va=i.address,target=i.op_str) for i in ins if i.mnemonic=='call'],branches=[dict(va=i.address,target=i.op_str) for i in ins if i.mnemonic.startswith('j')])
    padding=im[0x1ebe7:0x1ebf0];poff=pe.get_offset_from_rva(0x1ebe7);assert padding==raw[poff:poff+len(padding)]==b'\x90'*9;put('following-padding.bin',padding)
    js('cuts.json',dict(cuts=[row],whole_code_bytes=len(b),selected_code_bytes=0,data_bytes=9,padding=dict(begin=0x41ebe7,end_exclusive=0x41ebf0,bytes=9,originalPE_offset=poff,sha256=H(padding)),method_credit=0,opcode_credit=0,format_credit=0,route_credit=0,historical='20260926 already documents complete49B850->5068C0->41EA00->41E710->427160/4271E0. This closes current bounded frontier and does not claim global novelty.'))
    p=Path('C:/Users/risei/Desktop/God2/God2-Server/docs/research/current-equipment-instance-projection-20260926.md');z=p.read_bytes();js('historical-source-reference.json',dict(path=str(p),bytes=len(z),sha256=H(z),executed=False,scope='Only read/hash prior current-native coverage; no historical fixture promotion or resource decode.'))
    js('capture-complete.json',dict(success=True,scope='Static only, no tracked edits/target/native/CRT/VM/parser/resource/API/SQL/compiler/build/tests execution',whole_code_bytes=len(b),sites=len(ins),padding_bytes=9,discovery='Initial read-only disassembly window41EA00..41EC40 established actual RET/padding/next entry. Adjacent method bytes not retained or counted as recovered. No failed capture.'))
    print(json.dumps(dict(success=True,cut=row,padding_bytes=9)))
if __name__=='__main__':main()
