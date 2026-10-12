"""Bounded static file/hash/PE/Capstone source only, no native execution."""
from pathlib import Path
import hashlib
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=BASE/'tw-native-petegg-list-nonzero-source-333'
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
    cut('status34-36-helper-complete',0x4d9be0,0x4d9c57,'Complete actual signedWORD/formalWORD/scalar counter helper; no directU0A or full20 effects.')
    cut('status30-32-ui-helper-complete',0x4d94d0,0x4d94ff,'Complete actual WORDhandle reread/twoUIcalls; no directstate write.')
    cut('known-status30-32-parent-spans',0x4d9a4e,0x4d9b34,'Selected actual cases within full3314D9990; sameU child invocations; NOT new method entry.')
    cut('known-status34-36-parent-spans',0x4d9b55,0x4d9ba9,'Selected actual cases within full3314D9990; lowWORD34/35/36 args and ECX=ESI=U; NOT new method entry.')
    cut('known-e7-world-case',0x4691fd,0x46920f,'Actual known E7 WORLD case with U=Main+A7F2F6C; NOT newmethod.')
    cut('known-e7-world-table-cell',0x46b970,0x46b974,'Prior331 actual E7 world cell',False)
    cut('known-e7-length-leaf',0x401216,0x40121c,'Prior331 complete actual E7 length2 leaf; no novelty.')
    cut('known-e7-length-cell',0x4016c0,0x4016c4,'Prior331 actual E7 length cell',False)
    cut('boundary-counter-before',0x4d9bdc,0x4d9be0,'Padding after parent jump table, before actualentry.',False)
    cut('boundary-counter-after',0x4d9c57,0x4d9c60,'Padding after allreturns; next function not entered.',False)
    cut('boundary-ui-before',0x4d94c4,0x4d94d0,'Padding before actualentry.',False)
    cut('boundary-ui-after',0x4d94ff,0x4d9500,'Padding before unrelated next method.',False)
    (dst/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8')
    (dst/'input-references.json').write_text(json.dumps([dict(path=str(INPUT/n),sha256=sha(b),bytes=len(b),copied=False)
        for n,b in [('native-image.bin',image),('originalPE.bin',original)]],indent=2)+'\n',encoding='utf8')
    refs=[]
    for rel in ['docs/research/pet-egg-validation-20260920.md','docs/research/pet-egg-coverage-matrix-20260920.md',
                'docs/research/tw-native-petegg-e7-list-source-20261012.md','docs/research/tw-native-petegg-deferred-b1-source-20261012.md']:
        p=SERVER/rel;raw=p.read_bytes();q=OUT/'source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(q.relative_to(OUT))))
    for rel in ['seal.json','seal-supplement-01.json','native/cuts.json','native/e7-receiver-complete.bin',
                'native/e7-status-child-complete.bin','native/e7-status-child-table.bin',
                'native/list-array-zero-initializer-complete.bin','REPORT.md','REPORT-CORRECTION-01.md']:
        p=BASE/'tw-native-petegg-e7-list-input-source-331'/rel;raw=p.read_bytes()
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Immutable331 full actualparent/table/clear qualification, not global writer absence.'))
    ledger=SERVER/'artifacts/integration/packet-connections-20261006/packet-route-ledger.json';raw=ledger.read_bytes()
    refs.append(dict(path=str(ledger),bytes=len(raw),sha256=sha(raw),copied=False))
    (OUT/'source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                         data_bytes=sum(c['bytes'] for c in cuts if not c['code']),new_routes=0)))

if __name__=='__main__':
    main()
