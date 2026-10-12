"""Append-only parent-authorized necessary small child; static PE/Capstone only."""
from pathlib import Path
import hashlib
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=BASE/'tw-native-petegg-list-nonzero-source-333/native-extra'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
    assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);cuts=[]
    def cut(name,a,z,scope,code=True):
        raw=image[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
        assert original[off:off+len(raw)]==raw
        (OUT/(name+'.bin')).write_bytes(raw)
        rows=list(md.disasm(raw,a)) if code else []
        if code:
            assert sum(i.size for i in rows)==len(raw)
            (OUT/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
        cuts.append(dict(name=name,va=f'{a:08X}',end_exclusive=f'{z:08X}',bytes=len(raw),code=code,
                         instruction_sites=len(rows),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,scope=scope))
    cut('selected-ui-forwarder-complete',0x4d98b0,0x4d98d2,'Complete actual selected helper forwards two rawDWORD args plus WORDhandle operand to5068C0; no arraywrite.')
    cut('selected-return-leaf-complete',0x4d97f0,0x4d97f1,'Complete actual directcall target RET only, no producer or state effects.')
    cut('boundary-forwarder-before',0x4d98a3,0x4d98b0,'Padding before actualcall-target entry.',False)
    cut('boundary-forwarder-after',0x4d98d2,0x4d98e0,'Padding after actualRET8.',False)
    cut('boundary-return-leaf-before',0x4d97e8,0x4d97f0,'Raw preceding boundary, not new function.',False)
    cut('boundary-return-leaf-after',0x4d97f1,0x4d9800,'Padding after actualRET.',False)
    (OUT/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),data_bytes=sum(c['bytes'] for c in cuts if not c['code']))))

if __name__=='__main__':
    main()
