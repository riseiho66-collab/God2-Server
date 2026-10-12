"""Static instruction-boundary readback of retained raw caller candidates."""
from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent
spans=json.loads((O/'qualified-spans.json').read_bytes())['code']
md=Cs(CS_ARCH_X86,CS_MODE_32);aligned={}
for span in spans:
    raw=(O/'native'/ (span['name']+'.bin')).read_bytes()
    assert len(raw)==span['bytes'] and hashlib.sha256(raw).hexdigest()==span['sha256']
    for i in md.disasm(raw,int(span['start_va'],16)):
        if i.mnemonic in ['call','jmp'] and i.op_str.startswith('0x'):
            aligned[i.address]=dict(target=int(i.op_str,16),source=span['name'],instruction_bytes=i.bytes.hex())
out=[]
for row in json.loads((O/'caller-candidates.json').read_bytes()):
    for cand in row['raw_relative_candidates']:
        site=int(cand['va'],16);target=int(row['target'],16);proof=aligned.get(site)
        exact=proof is not None and proof['target']==target
        # Original finite data's range flag must agree; no general range=code rule.
        assert cand['instruction_proved_by_cut']==exact,(cand,proof)
        out.append(dict(site=cand['va'],target=row['target'],aligned_actual_instruction=exact,proof=proof if exact else None,unqualified_if_not_aligned=True))
p=O/'aligned-caller-readback.json'
if p.exists():raise RuntimeError('Preserve')
p.write_bytes((json.dumps(dict(scope='Exact disassembled CALL/JMP boundaries, not mere address containment. Finite retained candidates verified; other candidates remain raw/open.',candidates=out),indent=2)+'\n').encode())
print(json.dumps(dict(candidates=len(out),aligned_proved=sum(x['aligned_actual_instruction'] for x in out))))
