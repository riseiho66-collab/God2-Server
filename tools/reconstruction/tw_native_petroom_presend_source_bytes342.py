from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_JUMP,CS_GRP_RET
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round342-petroom-presend-storage-audit')
BASE=OUT.parent;PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(PIN/'native-image.bin').read_bytes();original=(PIN/'originalPE.bin').read_bytes()
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
proof=[];lines=['package\tcut\tva\tbytes\tmnemonic\toperands'];allins={}
for folder,cutsrel in [('tw-native-petroom-presend-context-source-342','child-selected-cuts.json'),('tw-native-petegg-selected-child-source-342','native/cuts.json')]:
    package=BASE/folder
    for c in json.loads((package/cutsrel).read_bytes()):
        path=package/'native'/(c['name']+'.bin');raw=path.read_bytes();start=int(c['start_va'],16)
        off=pe.get_offset_from_rva(start-0x400000)
        assert len(raw)==c['bytes'] and sha(raw)==c['sha256'] and raw==image[start-0x400000:start-0x400000+len(raw)]==original[off:off+len(raw)]
        boundary=c.get('boundary_probe_only',False)
        ins=[] if boundary else list(md.disasm(raw,start))
        if not boundary:
            assert sum(i.size for i in ins)==len(raw)
        sites={i.address for i in ins}
        if c['name'] in ['large-child-null-input-tail','necessary-same-u-handle-child-complete']:
            assert all(i.operands[0].imm in sites for i in ins if i.group(CS_GRP_JUMP))
        for i in ins:
            lines.append(f'{folder}\t{c["name"]}\t{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}')
            allins[i.address]=i
        proof.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),start_va=c['start_va'],original_pe_offset=off,mapped_equal=True,original_pe_equal=True,boundary_probe_only=boundary,ret_sites=[f'{i.address:08X}' for i in ins if i.group(CS_GRP_RET)],copied=False))
expected={0x4b5c11:'66a3b0265900',0x4bc0d7:'83c8ff',0x4bc0da:'890d38785b00',0x4bc0e0:'66a3b2265900',0x4bc0e6:'890d3c785b00',0x4bc0ec:'66a3b4265900',0x4bc0f2:'890d40785b00',0x4bc0f8:'66c70530785b000000',0x4bc101:'890d44785b00',0x4bc107:'890d48785b00',0x4bc10d:'8bcd',0x4bc10f:'e8cc010000',0x4bc2e2:'66c705b0265900ffff',0x4bc2a0:'668b81562e2300',0x4bc2cb:'66c705b0265900ffff'}
assert all(allins[va].bytes.hex()==raw for va,raw in expected.items())
(OUT/'source-byte-comparison.json').write_text(json.dumps(dict(cuts=proof,integer_cut_bytes=sum(c['bytes'] for c in proof),images=[dict(path=str(PIN/'native-image.bin'),bytes=len(image),sha256=sha(image),copied=False),dict(path=str(PIN/'originalPE.bin'),bytes=len(original),sha256=sha(original),copied=False)],selected_instruction_bytes_verified={f'{va:08X}':raw for va,raw in expected.items()}),indent=2)+'\n',encoding='utf8',newline='\n')
(OUT/'audit-disassembly.tsv').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(cuts_verified=len(proof),cut_bytes=sum(c['bytes'] for c in proof),selected_expected_instructions=len(expected),native_execution=0)))
