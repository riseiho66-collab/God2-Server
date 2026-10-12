"""PHASE1 bounded static file/hash/PE/Capstone source capture only."""
from pathlib import Path
import hashlib
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=BASE/'tw-native-petegg-alternative-actions-source-330'
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
    cut('alternative16-open-complete',0x4da680,0x4da6d5,'Complete actual method; direct UI handle/flag gates; children opaque.')
    cut('alternative16-close-complete',0x4da6e0,0x4da721,'Complete actual local close; direct BYTE U50 clear conditional on native handle/flag.')
    cut('alternative16-action-complete',0x4da730,0x4da788,'Complete actual deferred control/event dispatcher; selectors10/11 through known B1 producer.')
    cut('alternative23-open-complete',0x4dc710,0x4dc82d,'Complete actual list/open; scans24 WORDs at U0A; actual metadata calls; children opaque.')
    cut('alternative23-close-known-complete',0x4dc830,0x4dc871,'Previously324 qualified complete close; no global novelty credit.')
    cut('alternative23-action-complete',0x4dc880,0x4dc900,'Complete actual deferred dispatcher; selectors14..37/43 through known B1 producer.')
    cut('known-b1-producer-complete',0x4d6ba0,0x4d6bc2,'Prior329 complete B1/body1 producer recaptured without novelty credit.')
    cut('known-control23-invocation',0x4d6a02,0x4d6a29,'Selected actual invocation span within full3294D6940; not method entry.')
    cut('known-control16-invocation',0x4d6a52,0x4d6a73,'Selected actual invocation span within full3294D6940; not method entry.')
    cut('known-alternative16-dispatch',0x482733,0x482752,'Selected real same-U dispatch span within full3294820A0; not method entry.')
    cut('known-alternative23-dispatch',0x482790,0x4827af,'Selected real same-U dispatch span within full3294820A0; not method entry.')
    cut('boundary16-before',0x4da679,0x4da680,'Boundary alignment only, not function.')
    cut('boundary16-action-after',0x4da788,0x4da790,'Padding boundary only.',False)
    cut('boundary23-before',0x4dc703,0x4dc710,'Boundary alignment only, not function.')
    cut('boundary23-open-after',0x4dc82d,0x4dc830,'Padding boundary only.',False)
    (dst/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8')
    (dst/'input-references.json').write_text(json.dumps([dict(path=str(INPUT/n),sha256=sha(b),bytes=len(b),copied=False)
        for n,b in [('native-image.bin',image),('originalPE.bin',original)]],indent=2)+'\n',encoding='utf8')
    refs=[]
    paths=[SERVER/'docs/research/pet-incubation-evidence-20260919.md',
           SERVER/'docs/research/pet-egg-validation-20260920.md',
           SERVER/'docs/research/pet-egg-coverage-matrix-20260920.md',
           SERVER/'docs/research/pet1-e3-current-client-20260927.md',
           SERVER/'docs/research/native-pet2-categories-current-client-20260927.md',
           SERVER/'docs/research/tw-native-petegg-selection-and-b1-source-20261012.md',
           SERVER/'docs/research/tw-native-equipment-request-context-20261012.md']
    for p in paths:
        raw=p.read_bytes();q=OUT/'source'/p.relative_to(SERVER);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(q.relative_to(OUT))))
    for rel in ['seal.json','native/cuts.json','native/primary-action-dispatch-complete.bin',
                'native/primary-action-main-prefix.bin','native/action-complete.bin','REPORT.md']:
        p=BASE/'tw-native-petegg-selection-source-329'/rel;raw=p.read_bytes()
        refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Prior329 immutable full actual caller/control/source qualification.'))
    ledger=SERVER/'artifacts/integration/packet-connections-20261006/packet-route-ledger.json';raw=ledger.read_bytes()
    refs.append(dict(path=str(ledger),bytes=len(raw),sha256=sha(raw),copied=False))
    (OUT/'source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                         data_bytes=sum(c['bytes'] for c in cuts if not c['code']),new_routes=0)))

if __name__=='__main__':
    main()
