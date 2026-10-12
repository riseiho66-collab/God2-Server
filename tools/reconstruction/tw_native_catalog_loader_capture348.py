"""Bounded348 static hash/PE/Capstone/catalog source capture, LF only.
No client/server/CRT/parser/resource decoder/VM/API/DB execution or repo writes.
"""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent;A=O.parent
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
P=A/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry';B=0x400000
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Preserve '+n)
    p.write_bytes(v if isinstance(v,bytes) else (json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
def reference(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b),copied=False)
def main():
    if (O/'capture-complete.json').exists() or (O/'seal.json').exists():raise RuntimeError('Preserve success')
    m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
    assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=r,fast_load=True);assert pe.OPTIONAL_HEADER.ImageBase==B
    save('input-references.json',[reference(P/'native-image.bin'),reference(P/'originalPE.bin')])
    save('pe-sections.json',[dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=s.VirtualAddress,
        virtual_size=s.Misc_VirtualSize,raw_offset=s.PointerToRawData,raw_size=s.SizeOfRawData,
        characteristics=s.Characteristics,execute_flag=bool(s.Characteristics&0x20000000)) for s in pe.sections])
    prior=[]
    for name,pin in [('round347-normal-entry-native-readiness-source','10d2c4abe81d233eb6dc415c1025b05913f4292da1a99d4f24ddb5a2f90742a5'),
        ('round347-native-catalog-context-correction','8b7f88fbcb30cd4e8e02f9d51c8fee9c57445b5d44e3a05a61cc289044fdbcc5')]:
        base=A/name;raw=(base/'seal.json').read_bytes();assert sha(raw)==pin;old=json.loads(raw)
        for row in old['members']:
            b=(base/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
        prior.append(dict(seal=reference(base/'seal.json'),member_count=len(old['members']),
            member_bytes=sum(x['bytes'] for x in old['members']),all_individual_members_verified=True,
            scope='Hash in place, no old member copied/mutated/capture rerun.'))
    save('prior347-closures-verified.json',prior)
    md=Cs(CS_ARCH_X86,CS_MODE_32);cuts=[]
    spans=[('application-startup-invocation-whole',0x531D10,0x531D3E,True),
        ('application-startup-whole',0x40DA10,0x40DE71,True),
        ('catalog-file-enumeration-whole',0x455780,0x4558CB,True),
        ('programmsg-loader-whole',0x458C90,0x458D8A,True),
        ('application-constructor-whole',0x40D7F0,0x40D879,True),
        ('catalog-constructor-whole',0x455AC0,0x455AD3,True),
        ('catalog-initializer-whole',0x4558D0,0x455ABB,True),
        ('filename-selector-whole',0x531C10,0x531C2D,True),
        ('known-main-catalog-pointer-write-prefix',0x464910,0x464A1A,False),
        ('application-constructor-forwarder',0x531C50,0x531C5A,False),
        ('known-programmsg-dispatch-selected',0x45647F,0x4564CA,False),
        ('known-normal-entry-application-this-prefix',0x40DE80,0x40DEA9,False),
        ('known-normal-entry-world-arguments',0x40E0BD,0x40E0DB,False)]
    for name,s,e,whole in spans:
        b=m[s-B:e-B];off=pe.get_offset_from_rva(s-B);assert r[off:off+len(b)]==b
        ins=list(md.disasm(b,s));assert sum(i.size for i in ins)==len(b)
        if whole:assert ins[-1].mnemonic=='ret'
        addresses={i.address for i in ins};branches=[]
        for i in ins:
            if i.mnemonic.startswith('j'):
                target=int(i.op_str,16) if i.op_str.startswith('0x') else None
                if whole:assert target in addresses,(name,hex(i.address),i.op_str)
                branches.append(dict(site=f'{i.address:08X}',target=i.op_str))
        save('native/'+name+'.bin',b)
        save('native/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+
            ''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
        cuts.append(dict(name=name,start_va=f'{s:08X}',end_exclusive_va=f'{e:08X}',bytes=len(b),
            sha256=sha(b),original_pe_offset=off,pe_equal=True,sites=len(ins),
            complete_actual_body=whole,ret_sites=[f'{i.address:08X}' for i in ins if i.mnemonic=='ret'],
            calls=[dict(site=f'{i.address:08X}',target=i.op_str) for i in ins if i.mnemonic=='call'],
            branches=branches,new_method_credit=0))
    data=[]
    def datum(name,s,b):
        off=pe.get_offset_from_rva(s-B);assert m[s-B:s-B+len(b)]==b and r[off:off+len(b)]==b
        save('native/'+name+'.bin',b)
        data.append(dict(name=name,va=f'{s:08X}',bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True))
    table=m[0x18987C:0x18992C];datum('filename-pair-table22',0x58987C,table)
    paths=[]
    for row,pair in enumerate(struct.iter_unpack('<II',table)):
        values=[]
        for variant,v in enumerate(pair):
            b=m[v-B:].split(b'\0',1)[0]+b'\0';name=f'filename-{row:02d}-variant{variant}'
            datum(name,v,b);values.append(dict(variant=variant,va=f'{v:08X}',raw_hex=b.hex(),ascii=b[:-1].decode('ascii')))
        paths.append(dict(row=row,values=values))
    for name,v in [('path-prefix-operand',0x5847D8),('filename-format',0x589E50),
        ('suffix-format-one',0x589E38),('suffix-format-zero',0x589E24),('programmsg-literal',0x58A0D0)]:
        datum(name,v,m[v-B:].split(b'\0',1)[0]+b'\0')
    save('static-filename-inputs.json',dict(table_rows=paths,
        first_row='gamedata.csv / gamedata-gb.csv',second_row='message.csv / message-gb.csv',
        selection='Current WORD59DFD8==4 and WORD59DFDA==2 ->1; otherwise0.',
        scope='Only original static literal/table/format operands. No current directory/profile/file access/resource decoding/observed filename or bank.'))
    base=A/'tw-native-f4-list-definition-key-source-335';sr=(base/'seal.json').read_bytes();old=json.loads(sr)
    members={x['path']:x for x in old['members']};refs=[]
    needed=[('section-dispatch-complete',0x456130,0x4570D6),('row-loader-complete',0x4599B0,0x459A5F),
        ('generic-record-parser-complete',0x459420,0x45995F),('category-loader-complete',0x459150,0x45937D),
        ('category-lookup-complete',0x459380,0x45941B),('definition-lookup-complete',0x459A60,0x459A7E)]
    # Actual prior filename is discovered by matching its pinned raw bytes, not guessed.
    for label,s,e in needed:
        target=m[s-B:e-B];off=pe.get_offset_from_rva(s-B);assert r[off:off+len(target)]==target
        found=[(name,member) for name,member in members.items() if name.startswith('native/') and name.endswith('.bin')
            and member['bytes']==len(target) and member['sha256']==sha(target)]
        assert len(found)==1,(label,found)
        name,member=found[0];p=base/name;b=p.read_bytes();assert b==target
        refs.append(dict(label=label,**reference(p),original_pe_offset=off,pe_equal=True,
            prior_seal_member_verified=True,start_va=f'{s:08X}',end_exclusive_va=f'{e:08X}'))
    save('prior335-known-method-references.json',dict(seal=reference(base/'seal.json'),members=refs,
        scope='Only six referenced members individually verified; no whole335 package claim or recopy/newcredit.'))
    save('source-references.json',[reference(ROOT/p) for p in ['docs/research/current-world-actor-20260919.md',
        'docs/research/current-memory-catalog-layout-20260927.md',
        'docs/research/tw-native-petroom-catalog-source-boundary-20261012.md',
        'tools/strike_lab/omega_slice.py']])
    save('cuts.json',cuts);save('data-cuts.json',data)
    save('capture-complete.json',dict(success=True,static_only=True,code_cuts=len(cuts),
        whole_body_cuts=sum(x['complete_actual_body'] for x in cuts),code_bytes=sum(x['bytes'] for x in cuts),
        data_cuts=len(data),data_bytes=sum(x['bytes'] for x in data),
        no_resource_execution=True,new_methods=0,new_opcodes=0,new_formats=0,new_routes=0))
    print(json.dumps(dict(success=True,code_cuts=len(cuts),code_bytes=sum(x['bytes'] for x in cuts),
        data_bytes=sum(x['bytes'] for x in data),prior347_members_verified=54)))
if __name__=='__main__':main()
