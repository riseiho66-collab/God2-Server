"""PHASE1 existing egg-refresh direct affected-state boundary; no execution."""
from pathlib import Path
import hashlib
import json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

ROOT=Path.home()/'.codex/artifact-archives/god2-server/20261012'
INPUT=ROOT/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT=ROOT/'tw-native-e5-egg-input-source-328/native-refresh'

def main():
    OUT.mkdir(exist_ok=False)
    image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
    sha=lambda r:hashlib.sha256(r).hexdigest()
    if sha(image)!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':raise ValueError('Mapped pin differs')
    if sha(original)!='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':raise ValueError('PE pin differs')
    pe=pefile.PE(data=original);rva=0xd5970;end=0xd5e36;va=0x400000+rva;raw=image[rva:end]
    offset=pe.get_offset_from_rva(rva)
    if original[offset:offset+len(raw)]!=raw:raise ValueError('Original method differs')
    rows=list(Cs(CS_ARCH_X86,CS_MODE_32).disasm(raw,va))
    if sum(i.size for i in rows)!=len(raw):raise ValueError('Incomplete method static decode')
    (OUT/'known-egg-refresh-complete.bin').write_bytes(raw)
    (OUT/'known-egg-refresh-complete.tsv').write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
        f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
    cut=dict(va=f'{va:08X}',end_exclusive=f'{0x400000+end:08X}',bytes=len(raw),sites=len(rows),sha256=sha(raw),
             original_pe_offset=offset,original_pe_equal=True,scope='Historical20260926 complete method; only guard/current inventory flag/directU44-clear newly qualified, GUI/FPU descendants not pursued')
    (OUT/'cut.json').write_text(json.dumps(cut,indent=2)+'\n',encoding='utf8')
    print(json.dumps(cut))

if __name__=='__main__':main()
