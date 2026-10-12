"""Read/hash/PE/Capstone source capture only. Never imports or runs client code."""
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
    pe=pefile.PE(data=raw,fast_load=True)
    js('native-inputs.json',dict(inputs=[dict(path=str(N/n),bytes=len(b),sha256=H(b)) for n,b in [('native-image.bin',im),('originalPE.bin',raw)]],image_base=pe.OPTIONAL_HEADER.ImageBase,sections=[dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=s.VirtualAddress,raw_offset=s.PointerToRawData,raw_bytes=s.SizeOfRawData,virtual_bytes=s.Misc_VirtualSize,characteristics=s.Characteristics,execute=bool(s.Characteristics&0x20000000)) for s in pe.sections],execute_flag_limit='All original section execute flags are clear; not evidence of no code. Authentic entries established by aligned prior full caller CALL and closed method.'))
    prior=[]
    for name in ['round348-native-catalog-loader-source','round348-native-item-material-helper-source','round349-native-item-helper-output-source']:
        d=A/name;p=d/'seal.json';v=json.loads(p.read_bytes());rr=[]
        for r in v['members']:
            b=(d/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256'];rr.append(r)
        assert len(rr)==v['member_count'] and sum(r['bytes'] for r in rr)==v['member_bytes']
        prior.append(dict(base=str(d),seal_sha256=H(p.read_bytes()),member_count=len(rr),member_bytes=sum(r['bytes'] for r in rr),members=rr))
    js('prior-individual-verification.json',prior)
    parent=A/'round348-native-item-material-helper-source'/'item-helper49B850-full.bin'
    b=parent.read_bytes();assert b==im[0x9b850:0x9bae0]
    js('actual-parent-reference.json',dict(path=str(parent),bytes=len(b),sha256=H(b),whole_entry='0049B850',end_exclusive='0049BAE0',sites=224,returns='nine RET8',source='Already sealed348 full method; no duplicate cut or credit. Positive CALL49B8BC and clear CALL49BA88 target authentic5068C0.'))
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;cuts=[]
    def cut(n,start,end,whole):
        z=im[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000);assert z==raw[off:off+len(z)]
        ins=list(md.disasm(z,start));assert sum(i.size for i in ins)==len(z)
        put(n+'.bin',z);put(n+'.tsv',('VA\traw\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
        row=dict(name=n,begin=start,end_exclusive=end,bytes=len(z),sha256=H(z),originalPE_offset=off,mapped_PE_equal=True,sites=len(ins),whole_function=whole,returns=[dict(va=i.address,operand=i.op_str) for i in ins if i.mnemonic=='ret'],calls=[dict(va=i.address,target=i.op_str) for i in ins if i.mnemonic=='call'],branches=[dict(va=i.address,target=i.op_str) for i in ins if i.mnemonic.startswith('j')])
        if whole:
            starts={i.address for i in ins}
            for i in ins:
                if i.mnemonic.startswith('j'):assert i.operands[0].imm in starts
            assert len(row['returns'])==1 and row['returns'][0]['va']==0x50692d
        cuts.append(row)
    cut('primary5068C0-full',0x5068c0,0x506930,True)
    cut('known-parent-positive-call-span',0x49b884,0x49b8c1,False)
    cut('known-parent-clear-call-span',0x49ba73,0x49ba8d,False)
    js('cuts.json',dict(cuts=cuts,total_code_bytes=sum(c['bytes'] for c in cuts),whole_code_bytes=112,selected_caller_bytes=87,data_bytes=0,credits=dict(methods=0,opcodes=0,formats=0,routes=0),child='41EA00 remains opaque; no descendants recovered.'))
    for n in ['docs/research/current-equipment-instance-projection-20260926.md','tools/strike_lab/current_equipment_projection_20260926.py']:
        p=Path('C:/Users/risei/Desktop/God2/God2-Server')/n;b=p.read_bytes()
        js(Path(n).stem+'-historical-reference.json',dict(path=str(p),bytes=len(b),sha256=H(b),read_only=True,executed_or_imported=False,qualification='Historical document explicitly lists complete49B850->5068C0->41EA00->41E710 chain. No current runtime/resource execution or historical fixture promotion.'))
    js('capture-complete.json',dict(success=True,scope='Static read/hash/PE/Capstone only; no tracked writes, no client/CRT/resource/parser/API/SQL/compiler/tests execution',sites=cuts[0]['sites'],whole_code_bytes=112,selected_caller_bytes=87,data_bytes=0))
    print(json.dumps(dict(success=True,cuts=cuts)))
if __name__=='__main__':main()
