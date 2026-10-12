"""Bounded static PE/Capstone/hash/direct-branch source census; no execution."""
from pathlib import Path
import hashlib
import json
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=BASE/'tw-native-petegg-list-callers-source-334'
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server')
TARGETS=(0x4dc710,0x4dc880)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def scan(raw,va,source,section):
    hits=[]
    for n in range(len(raw)):
        size=5 if raw[n] in (0xe8,0xe9) else 2 if raw[n]==0xeb else 0
        if size and n+size<=len(raw):
            disp=struct.unpack_from('<i',raw,n+1)[0] if size==5 else int.from_bytes(raw[n+1:n+2],'little',signed=True)
            target=va+n+size+disp
            if target in TARGETS:
                hits.append(dict(source=source,section=section,va=f'{va+n:08X}',target=f'{target:08X}',
                                 raw_opcode=f'{raw[n]:02X}',bytes=raw[n:n+size].hex(),candidate=True))
    return hits

def main():
    dst=OUT/'native';dst.mkdir(exist_ok=False)
    image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
    assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);sections=[];hits=[];cuts=[]
    for s in pe.sections:
        name=s.Name.rstrip(b'\0').decode('ascii');rva=s.VirtualAddress
        physical=original[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
        overlap=min(len(physical),max(0,len(image)-rva))
        mlen=min(s.Misc_VirtualSize,s.SizeOfRawData,max(0,len(image)-rva))
        mapped=image[rva:rva+mlen]
        sections.append(dict(name=name,rva=f'{rva:08X}',va=f'{0x400000+rva:08X}',
            virtual_bytes=int(s.Misc_VirtualSize),physical_offset=int(s.PointerToRawData),physical_bytes=len(physical),
            characteristics=f'{s.Characteristics:08X}',execute_flag=bool(s.Characteristics&0x20000000),
            mapped_scan_bytes=len(mapped),physical_scan_bytes=len(physical),mapped_overlap_bytes=overlap,
            overlap_equal=(physical[:overlap]==image[rva:rva+overlap]) if overlap else None,
            physical_sha256=sha(physical),mapped_scan_sha256=sha(mapped) if mapped else None))
        hits.extend(scan(physical,0x400000+rva,'originalPE-physical',name))
        hits.extend(scan(mapped,0x400000+rva,'149c-mapped-file-backed',name))
    md.detail=True;fullrefs=[];writeops=[]
    prior=BASE/'tw-native-petegg-selection-source-329'
    prior_seal=json.loads((prior/'seal.json').read_text(encoding='utf8'))
    seal_members={v['path']:v['sha256'] for v in prior_seal['members']}
    for name,a,z in [('action-complete',0x4d6940,0x4d6b72),('primary-action-dispatch-complete',0x4820a0,0x48314f)]:
        p=prior/'native'/(name+'.bin');raw=p.read_bytes();h=sha(raw)
        assert h==seal_members['native/'+name+'.bin']
        assert raw==image[a-0x400000:z-0x400000]
        offset=pe.get_offset_from_rva(a-0x400000);assert original[offset:offset+len(raw)]==raw
        rows=list(md.disasm(raw,a));assert sum(i.size for i in rows)==len(raw)
        refs=dict(path=str(p),va=f'{a:08X}',end_exclusive=f'{z:08X}',bytes=len(raw),sha256=h,
                  copied=False,prior_seal_member_equal=True,mapped_equal=True,original_pe_equal=True,
                  original_pe_offset=offset,complete_boundary='Existing329 actual entry/all returns, preserved unchanged')
        fullrefs.append(refs)
        sites={i.address:i for i in rows}
        for hit in hits:
            va=int(hit['va'],16)
            if a<=va<z:
                i=sites.get(va)
                assert i and i.bytes.hex()==hit['bytes'] and i.mnemonic in ('call','jmp')
                hit.update(dict(candidate=False,qualified=True,enclosing_complete_va=f'{a:08X}',
                                enclosing_full_reference=str(p),instruction_boundary_equal=True,
                                mnemonic=i.mnemonic,operands=i.op_str,novel_method=False))
        for i in rows:
            if any(op.type==X86_OP_MEM and op.access&CS_AC_WRITE for op in i.operands):
                writeops.append(dict(enclosing_va=f'{a:08X}',va=f'{i.address:08X}',bytes=i.bytes.hex(),
                                     mnemonic=i.mnemonic,operands=i.op_str,scope='Explicit write operand only; implicit stack/opaque descendants/alias effects not enumerated.'))
    assert all(h.get('qualified') for h in hits)
    def cut(name,a,z,scope,code=True):
        raw=image[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
        assert original[off:off+len(raw)]==raw
        (dst/(name+'.bin')).write_bytes(raw)
        rows=list(md.disasm(raw,a)) if code else []
        if code:
            assert sum(i.size for i in rows)==len(raw)
            (dst/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8',newline='\n')
        cuts.append(dict(name=name,va=f'{a:08X}',end_exclusive=f'{z:08X}',bytes=len(raw),code=code,
                         instruction_sites=len(rows),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,scope=scope))
    cut('known-list-common-event-gates',0x4d69b1,0x4d69e4,'Selected span inside full3294D6940, not method.')
    cut('known-list-caller-control23',0x4d6a02,0x4d6a29,'Actual signedU8/live row15h low7 gate and sameU call4DC710; selected span not method.')
    cut('known-list-control23-table-cell',0x4d6b94,0x4d6b98,'Actual index8/control23 cell in full329 action table',False)
    cut('known-list-action-caller',0x482790,0x4827af,'Actual sameU/windowhandle equality and direct4DC880 invocation; selected span not method.')
    cut('known-original-action-caller',0x4826f5,0x482714,'Actual sameU/primaryhandle equality then4D6940; selected span not method.')
    cut('known-main-primary-invocation-prefix',0x466b00,0x466ba1,'ActualMainentry prefix through466B9C; U=Main+A7F2F6C; selected prefix NOT complete method.')
    cut('known-action-context-prefix',0x4d6940,0x4d6950,'Actual method entry prefix ESI=ECX; full329 reference retained, prefix not fullmethod.')
    cut('known-dispatch-context-prefix',0x4820a0,0x4820a7,'Actual method entry prefix ESI=ECX; full329 reference retained, prefix not fullmethod.')
    cut('known-list-array-read-and-label-span',0x4dc744,0x4dc79d,'Selected span within full3304DC710; U0A pointer stayslocal, label getsmetadata+8 andU+E2170; no arraywrite.')
    summary=dict(physical_sections=len(sections),execute_flag_sections=sum(int(s['execute_flag']) for s in sections),
        mapped_scanned_sections=sum(int(s['mapped_scan_bytes']>0) for s in sections),
        physical_scan_bytes=sum(s['physical_scan_bytes'] for s in sections),mapped_scan_bytes=sum(s['mapped_scan_bytes'] for s in sections),
        original_raw_hits=sum(int(h['source']=='originalPE-physical') for h in hits),mapped_raw_hits=sum(int(h['source']=='149c-mapped-file-backed') for h in hits),
        unique_qualified_call_hits=len({(h['va'],h['target']) for h in hits if h['mnemonic']=='call'}),
        unique_qualified_jmp_hits=len({(h['va'],h['target']) for h in hits if h['mnemonic']=='jmp'}),new_methods=0,new_opcodes=0,new_complete_routes=0)
    for name,value in [('cuts.json',cuts),('sections.json',sections),('branch-candidates.json',hits),
                       ('complete-caller-references.json',fullrefs),('known-full-caller-direct-write-operands.json',writeops),('scan-summary.json',summary)]:
        (dst/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8',newline='\n')
    (dst/'input-references.json').write_text(json.dumps([dict(path=str(INPUT/n),sha256=sha(b),bytes=len(b),copied=False)
        for n,b in [('native-image.bin',image),('originalPE.bin',original)]],indent=2)+'\n',encoding='utf8',newline='\n')
    refs=[]
    for rel in ['docs/GOAL_ACCEPTANCE.md','docs/research/tw-native-petegg-deferred-b1-source-20261012.md',
                'docs/research/tw-native-petegg-e7-list-source-20261012.md']:
        p=SERVER/rel;raw=p.read_bytes();q=OUT/'source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(q.relative_to(OUT))))
    for folder,rels in [('tw-native-petegg-selection-source-329',['seal.json','native/cuts.json','native/action-complete.tsv','native/primary-action-dispatch-complete.tsv']),
                        ('tw-native-petegg-alternative-actions-source-330',['seal.json','native/cuts.json','native/alternative23-open-complete.bin','native/alternative23-action-complete.bin']),
                        ('tw-native-petegg-e7-list-input-source-331',['seal.json','seal-supplement-01.json','native/list-array-zero-initializer-complete.bin'])]:
        for rel in rels:
            p=BASE/folder/rel;raw=p.read_bytes();refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Prior immutable actualmethod/context/clear qualification; no recredit.'))
    ledger=SERVER/'artifacts/integration/packet-connections-20261006/packet-route-ledger.json';raw=ledger.read_bytes()
    refs.append(dict(path=str(ledger),bytes=len(raw),sha256=sha(raw),copied=False))
    (OUT/'source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),data_bytes=sum(c['bytes'] for c in cuts if not c['code']),scan=summary)))

if __name__=='__main__':
    main()
