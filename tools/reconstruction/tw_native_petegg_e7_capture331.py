"""Bounded static native file/hash/PE/Capstone/table capture, no execution."""
from pathlib import Path
import hashlib
import json
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_WRITE
from capstone.x86 import X86_OP_MEM, X86_REG_ESI, X86_REG_ECX, X86_REG_EDI
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=BASE/'tw-native-petegg-e7-list-input-source-331'
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    dst=OUT/'native';dst.mkdir(exist_ok=False)
    image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
    assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);cuts=[]
    def cut(name,a,z,scope,code=True):
        raw=image[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
        assert original[off:off+len(raw)]==raw
        (dst/(name+'.bin')).write_bytes(raw)
        rows=list(md.disasm(raw,a)) if code else []
        if code:
            assert sum(i.size for i in rows)==len(raw)
            (dst/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
        cuts.append(dict(name=name,va=f'{a:08X}',end_exclusive=f'{z:08X}',bytes=len(raw),code=code,
                         instruction_sites=len(rows),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,scope=scope))
    cut('e7-receiver-complete',0x4d6340,0x4d68be,'Complete actual body1 consumer with both local state branches/all returns; children separately bounded.')
    cut('e7-world-case',0x4691fd,0x46920f,'Actual E7 primary WORLD selected case; ECX=Main+A7F2F6C, not method entry.')
    cut('e7-world-table-cell',0x46b970,0x46b974,'Actual E7 table cell',False)
    cut('e7-length-leaf',0x401216,0x40121c,'Complete actual E7 length leaf MOV EAX2/RET.')
    cut('e7-length-table-cell',0x4016c0,0x4016c4,'Actual E7 length cell',False)
    cut('e7-status-child-complete',0x4d9990,0x4d9baf,'Complete actual statusdecimal30..40 handler; no directU0A writer; opaque descendants not entered.')
    cut('e7-status-child-table',0x4d9bb0,0x4d9bdc,'Actual eleven-entry low7 decimal30..40 table',False)
    cut('e7-state-word-leaf-complete',0x4d7db0,0x4d7dd1,'Complete actual conditional WORD U52 setter; signedhandle>=0 and signedarg0..57.')
    cut('e7-bit29-control-helper-complete',0x4d6bd0,0x4d6c36,'Complete direct control helper called by E7; not E7 receiver; UI children opaque.')
    cut('list-array-zero-initializer-complete',0x4dc610,0x4dc708,'Complete actual UI constructor directly zeroes48B U0A..U39; metadata/UI descendants opaque.')
    cut('list-array-initializer-parent-complete',0x481c20,0x481f65,'Historical actual primary setup descendant retained complete;481E97 invokes sameU initializer.')
    cut('known-primary-parent-invocation',0x481bab,0x481bb8,'Selected actual invocation within prior329 full4817C0; ECX=ESI=U; not method entry.')
    cut('boundary-e7-before',0x4d6332,0x4d6340,'Boundary RET/padding only; not method.')
    cut('boundary-e7-after',0x4d68be,0x4d68c0,'Boundary padding only.',False)
    cut('boundary-child-after',0x4d9baf,0x4d9bb0,'Boundary padding only.',False)
    cells=struct.unpack('<11I',image[0xd9bb0:0xd9bdc])
    (dst/'e7-child-targets.tsv').write_text('index\tstatus_decimal\tstatus_hex\ttarget_va\n'+''.join(
        f'{n}\t{n+30}\t{n+30:02X}\t{a:08X}\n' for n,a in enumerate(cells)),encoding='utf8')
    (dst/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8')
    (dst/'input-references.json').write_text(json.dumps([dict(path=str(INPUT/n),sha256=sha(b),bytes=len(b),copied=False)
        for n,b in [('native-image.bin',image),('originalPE.bin',original)]],indent=2)+'\n',encoding='utf8')
    md.detail=True;candidates=[]
    for a in range(0x4d4b80,0x4dc900):
        row=next(md.disasm(image[a-0x400000:a-0x400000+15],a,count=1),None)
        if row:
            for op in row.operands:
                if op.type==X86_OP_MEM and op.mem.disp==0xa and op.mem.base in [X86_REG_ESI,X86_REG_ECX,X86_REG_EDI]:
                    if (op.access&CS_AC_WRITE) or row.mnemonic=='lea':
                        candidates.append(dict(va=f'{row.address:08X}',bytes=row.bytes.hex(),mnemonic=row.mnemonic,operands=row.op_str))
    (dst/'bounded-u0a-direct-candidates.json').write_text(json.dumps(dict(begin='004D4B80',end_exclusive='004DC900',
        scope='Decode every byte as raw candidates only; not full CFG/global absence. Only explicitESI/ECX/EDI+0A directwrite/LEA forms; indirect/alias writers remain open.',
        candidates=candidates),indent=2)+'\n',encoding='utf8')
    refs=[]
    for rel in ['docs/research/pet-incubation-evidence-20260919.md','docs/research/pet-egg-validation-20260920.md',
                'docs/research/pet-egg-coverage-matrix-20260920.md','docs/research/tw-native-petegg-selection-and-b1-source-20261012.md',
                'docs/research/tw-native-petegg-deferred-b1-source-20261012.md']:
        p=SERVER/rel;raw=p.read_bytes();q=OUT/'source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(q.relative_to(OUT))))
    for folder,rels in [('tw-native-petegg-selection-source-329',['seal.json','native/cuts.json','native/primary-setup-complete.bin','native/retained-primary-setup-invocation.bin']),
                        ('tw-native-petegg-alternative-actions-source-330',['seal.json','native/cuts.json','native/alternative23-open-complete.bin','native/alternative23-action-complete.bin'])]:
        for rel in rels:
            p=BASE/folder/rel;raw=p.read_bytes();refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Immutable prior actualfullmethod/context/action source.'))
    ledger=SERVER/'artifacts/integration/packet-connections-20261006/packet-route-ledger.json';raw=ledger.read_bytes()
    refs.append(dict(path=str(ledger),bytes=len(raw),sha256=sha(raw),copied=False))
    (OUT/'source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                         data_bytes=sum(c['bytes'] for c in cuts if not c['code']),new_routes=0)))

if __name__=='__main__':
    main()
