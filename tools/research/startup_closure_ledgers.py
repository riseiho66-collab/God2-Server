"""Derive bounded startup ledgers, explicitly retaining trace coverage gaps."""
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HOME = Path(__file__).resolve().parents[2]
OUT = HOME/'artifacts/capture_work/host-20260918-1430/output'
DECODER = Cs(CS_ARCH_X86, CS_MODE_32)


def steps(text):
    lines = text.splitlines()
    records = []
    for i, line in enumerate(lines):
        if not line.startswith('eax=') or i+2 >= len(lines) or not lines[i+1].startswith('eip='):
            continue
        regs = {k: int(v,16) for k,v in re.findall(r'([a-z]{3})=([0-9a-f]{8})', line+' '+lines[i+1])}
        for j in range(i+3, min(i+7, len(lines))):
            match = re.match(r'^([0-9a-f]{8}) ([0-9a-f]+)\s+(.+)', lines[j])
            if match and int(match[1],16)==regs['eip']:
                code = bytes.fromhex(match[2]); ins = list(DECODER.disasm(code, regs['eip']))
                records.append({'pc':regs['eip'], 'registers':regs, 'line':i+1, 'bytes':match[2],
                    'native_decode':match[3], 'capstone':(ins[0].mnemonic+' '+ins[0].op_str) if ins else None,
                    'boundary_agreement':len(ins)==1 and ins[0].size==len(code)})
                break
    return records


def analyze(run):
    path = OUT/(run+'-stdout.log')
    native = path.read_text(encoding='ascii')
    marker = 'THIRD_TRACE_BEGIN' if run.startswith('third') else 'CLOSURE_TRACE_BEGIN'
    split = native.index('\n'+marker+'\n')
    begin_line = native[:split].count('\n')+1
    all_rows = steps(native)
    earlier = [r for r in all_rows if r['line'] < begin_line]
    rows = earlier[-1:]+[r for r in all_rows if r['line'] > begin_line]
    image = (OUT/(run+'-after.bin')).read_bytes()
    end = (OUT/(run+'-end.bin')).read_bytes()
    calls, branches, correlation, gaps = [], [], [], []
    for n, row in enumerate(rows):
        pc = row['pc']; code = bytes.fromhex(row['bytes'])
        client = 0x400000<=pc<0x707000
        mapped = image[pc-0x400000:pc-0x400000+len(code)].hex() if client else None
        correlation.append(dict(row, run=run, rva=pc-0x400000 if client else None,
            mapped_image_bytes=mapped, runtime_bytes_match=(mapped==row['bytes']) if client else None,
            scope='client_image' if client else 'external_native_only'))
        ins = next(DECODER.disasm(code, pc), None)
        if ins is None or n+1==len(rows):
            continue
        nxt = rows[n+1]; fall = pc+ins.size
        ref = f'{run}:native-line-{row["line"]}'
        if ins.mnemonic=='call':
            target = int(ins.op_str,16) if re.fullmatch(r'0x[0-9a-f]+',ins.op_str) else None
            later = next((r for r in rows[n+1:] if r['pc']==fall and r['registers']['esp']==row['registers']['esp']), None)
            calls.append({'call_site':pc,'target':target,'next_observed_pc':nxt['pc'],'module':'client' if target is not None and 0x400000<=target<0x707000 else 'unresolved',
                'thread':'run-marker-thread; per-step thread not emitted','entry_seen':target==nxt['pc'],'return_address':fall,
                'return_seen':later is not None,'result_registers':later['registers'] if later else None,
                'nested_calls':'see ordered call rows; full stack reconstruction not asserted',
                'evidence_ids':[ref, f'{run}:native-line-{nxt["line"]}']})
        elif ins.mnemonic.startswith('j'):
            branches.append({'branch_site':pc,'condition':ins.mnemonic,'taken':nxt['pc']!=fall,
                'target':nxt['pc'],'register_snapshot':row['registers'],'thread':'run-marker-thread',
                'evidence_ids':[ref], 'far_transition':ins.mnemonic in ('ljmp','jmpf') or ':' in ins.op_str})
        if ins.mnemonic not in ('call','ret','retf','iret','iretd','int','int3','sysenter','syscall','ljmp') and not ins.mnemonic.startswith('j') and nxt['pc']!=fall and not (ins.mnemonic.startswith('rep') and nxt['pc']==pc):
            gaps.append({'after':pc,'next':nxt['pc'],'reason':'non-control-flow discontinuity','evidence_id':ref})
        if ins.mnemonic in ('ljmp','lcall','retf','iret','iretd'):
            gaps.append({'after':pc,'next':nxt['pc'],'reason':'mode/far transfer; x86 log alone cannot establish complete execution coverage','evidence_id':ref})
    returns = re.findall(r'^(?:THIRD_RETURNS|CLOSURE_THIRD_RETURNS) pid=([0-9a-f]+) tid=([0-9a-f]+) pc=([0-9a-f]+)',native,re.M)
    outcome = 'RETURNS' if len(returns)==1 and int(returns[0][2],16)==0x54a46e and rows[-1]['pc']==0x54a46e else 'UNKNOWN'
    protections = []
    for match in re.finditer(r'^BaseAddress:\s+([0-9a-f]+)\s*\nAllocationBase:\s+([0-9a-f]+)\s*\nAllocationProtect:\s+(.+)\nRegionSize:.*\nState:.*\nProtect:\s+(.+)', native, re.M):
        protections.append({'native_line':native[:match.start()].count('\n')+1,'base':int(match[1],16),
                            'allocation_base':int(match[2],16),'allocation_protect':match[3].strip(),'current_protect':match[4].strip()})
    return {'run':run,'outcome':outcome,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'instruction_rows':len(rows),'calls':calls,'branches':branches,'correlation':correlation,'gaps':gaps,
        'packer_watch':{'range':[0x702000,0x706000],'observed_hits':[r['pc'] for r in rows if 0x702000<=r['pc']<0x706000],
                       'complete_coverage':False,'scope':'all recorded PCs, not all actual execution'},
        'protection_snapshots':protections,'changed_bytes':sum(a!=b for a,b in zip(image,end)),
        'changed_text_bytes':sum(a!=b for a,b in zip(image[0x1000:0x170000],end[0x1000:0x170000]))}


if __name__ == '__main__':
    dest = HOME/'artifacts/reports/g03-closure-20260919-v2'
    dest.mkdir(exist_ok=False)
    results = [analyze(r) for r in ('closure-a','closure-b','third-a','third-b')]
    outputs = {'startup-call-ledger.json':{r['run']:r['calls'] for r in results},
        'startup-branch-ledger.json':{r['run']:r['branches'] for r in results},
        'runtime-static-correlation-v2.json':{r['run']:r['correlation'] for r in results},
        'protection-timeline.json':{r['run']:r['protection_snapshots'] for r in results},
        'closure-review.json':{'decision':'NEED_MORE_EVIDENCE','runs':[{k:v for k,v in r.items() if k not in ('calls','branches','correlation')} for r in results],
            'blockers':['WoW64/mode-transition coverage gaps','new observations not yet formal same-capture G02-certified evidence',
                        'not all critical call/return pairs visible in one trace','per-step thread attribution absent'],
            'scope':'Third-routine return reproduced; no G03 certificate. No IAT or permission repair.'}}
    for name, value in outputs.items():
        (dest/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps({'directory':str(dest),'outcomes':[(r['run'],r['outcome'],r['instruction_rows'],len(r['gaps'])) for r in results]}))
