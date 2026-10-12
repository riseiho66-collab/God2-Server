"""Bounded static E8/E9 source: file/hash/PE/Capstone only, no execution."""
from pathlib import Path
import hashlib
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=BASE/'tw-native-petegg-e8-e9-source-332'
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
    cut('e8-receiver-complete',0x4e8550,0x4e8576,'Complete actual E8 raw body1 ->indirectP+15E consumer; no inferred game domain.')
    cut('e9-receiver-complete',0x4f9980,0x4f99b2,'Complete actual E9 body1 ->U8B747 then directlocalzero and opaquechildren.')
    cut('e8-display-child-complete',0x4e8580,0x4e8600,'Complete necessary E8 child proves directP+15E input and0/1 conditionalUI paths; descendants opaque.')
    cut('e8-world-case',0x46b46e,0x46b480,'Selected true primary WORLD E8 case; not newmethod.')
    cut('e9-world-case',0x46b480,0x46b492,'Selected true primary WORLD E9 case; not newmethod.')
    cut('e8-world-table-cell',0x46b974,0x46b978,'Actual true E8 world cell',False)
    cut('e9-world-table-cell',0x46b978,0x46b97c,'Actual true E9 world cell',False)
    cut('known-fixed2-length-leaf',0x401216,0x40121c,'Previously331 complete MOV EAX2/RET leaf; no methodnovelty.')
    cut('e8-length-table-cell',0x4016c4,0x4016c8,'Actual E8 length cell',False)
    cut('e9-length-table-cell',0x4016c8,0x4016cc,'Actual E9 length cell',False)
    cut('boundary-e8-before',0x4e854d,0x4e8550,'Previous RET4 only, not function.')
    cut('boundary-e8-after',0x4e8576,0x4e8580,'Padding before necessary child.',False)
    cut('boundary-e9-before',0x4f997b,0x4f9980,'Padding before actualentry.',False)
    cut('boundary-e9-after',0x4f99b2,0x4f99c0,'Padding after actualreturn.',False)
    (dst/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8')
    (dst/'input-references.json').write_text(json.dumps([dict(path=str(INPUT/n),sha256=sha(b),bytes=len(b),copied=False)
        for n,b in [('native-image.bin',image),('originalPE.bin',original)]],indent=2)+'\n',encoding='utf8')
    refs=[]
    for rel in ['docs/research/pet-egg-validation-20260920.md','docs/research/pet-egg-coverage-matrix-20260920.md',
                'docs/research/tw-native-petegg-e7-list-source-20261012.md','docs/research/tw-native-petegg-deferred-b1-source-20261012.md']:
        p=SERVER/rel;raw=p.read_bytes();q=OUT/'source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(q.relative_to(OUT))))
    for rel in ['seal.json','seal-supplement-01.json','native/cuts.json','native/list-array-zero-initializer-complete.bin',
                'native/list-array-initializer-parent-complete.bin','REPORT.md','REPORT-CORRECTION-01.md']:
        p=BASE/'tw-native-petegg-e7-list-input-source-331'/rel;raw=p.read_bytes()
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Prior immutable331 actualzero-writer andE7; no nonzero population authority.'))
    ledger=SERVER/'artifacts/integration/packet-connections-20261006/packet-route-ledger.json';raw=ledger.read_bytes()
    refs.append(dict(path=str(ledger),bytes=len(raw),sha256=sha(raw),copied=False))
    (OUT/'source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                         data_bytes=sum(c['bytes'] for c in cuts if not c['code']),new_routes=0)))

if __name__=='__main__':
    main()
