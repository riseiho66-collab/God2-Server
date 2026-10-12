"""Correct only the retained misaligned caller preview, never overwrite drafts."""
from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent
v=json.loads((O/'native-inputs.json').read_bytes())
m=Path(v['mapped']['path']).read_bytes();p=Path(v['originalPE']['path']).read_bytes()
H=lambda b:hashlib.sha256(b).hexdigest()
assert H(m)==v['mapped']['sha256'] and H(p)==v['originalPE']['sha256']
pe=pefile.PE(data=p,fast_load=True);cs=Cs(CS_ARCH_X86,CS_MODE_32)
lo,hi=0x498E0A,0x498E30
b=m[lo-0x400000:hi-0x400000];off=pe.get_offset_from_rva(lo-0x400000)
assert b==p[off:off+len(b)]
ins=list(cs.disasm(b,lo));assert sum(x.size for x in ins)==len(b)
prior=O.parent/'round346-initial-owned-material-main-plan'
prior_starts={int(line.split('\t')[0],0) for line in (prior/'known3B-full.tsv').read_text().splitlines()[1:]}
assert lo in prior_starts and hi in prior_starts and all(x.address in prior_starts for x in ins)
for name,data in [('known3B-row-copy-aligned.bin',b),('known3B-row-copy-aligned.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}\n' for x in ins)).encode())]:
    with (O/name).open('xb') as f:f.write(data)
row=dict(begin=lo,end_exclusive=hi,bytes=len(b),sha256=H(b),originalPE_offset=off,sites=len(ins),mapped_PE_equal=True,all_sites_equal_retained_parent_alignment=True,scope='Existing parent partial copy continuity only; complete parent independently verified in prior346/238, no new method credit')
with (O/'aligned-caller-correction.json').open('xb') as f:f.write((json.dumps(row,indent=2)+'\n').encode())
with (O/'draft-correction-appendix.txt').open('xb') as f:f.write(b'Initial capture_item_helper348.py ran successfully but selected known3B-row-copy 498E00..498E26 from the middle of PUSH1 at498DFF. Capstone coverage alone did not establish authentic alignment. Its38-byte raw/TSV/metadata draft remains preserved and MUST NOT support source claims; exclude its first false ADD from instruction/semantic accounting. New exclusive aligned cut498E0A..498E30 validates every start against the independently sealed full parent TSV and includes actual REP MOVSD. Full49B850 and other cuts are unchanged. No target execution or tracked edits occurred. Preview-partial starts49B830 inside a preceding method and is boundary reconnaissance only, never a whole preceding method.\n')
print(json.dumps(row))
