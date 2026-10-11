"""Fail-closed boundary qualification with explicit unobserved nesting limits."""
import hashlib
import json
from pathlib import Path
import re
import sys

HOME = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(HOME / 'tools/research'))
from mode_trace_review import markers, matching_return, exact_ret
from startup_closure_ledgers import steps

OUT = HOME / 'artifacts/capture_work/host-20260918-1430/output'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stack_words(lines):
    result = {}
    for line in lines:
        match = re.fullmatch(r'([0-9a-f]{8})  ((?:[0-9a-f]{8}\s*){1,4})', line)
        if match:
            for i, value in enumerate(match[2].split()):
                result[int(match[1], 16) + 4*i] = int(value, 16)
    return result


def pair(entry, returned, entry_words, return_words):
    expected_sp = entry['sp'] + 4
    context = (entry_words.get(entry['sp']) == entry['expected']
               and expected_sp in entry_words
               and return_words.get(expected_sp) == entry_words[expected_sp])
    matched = returned is not None and matching_return(entry, returned)
    return {'entry_pc': entry['pc'], 'entry_esp': entry['sp'],
        'entry_thread': entry['tid'], 'entry_pid': entry['pid'],
        'expected_return_pc': entry['expected'], 'expected_return_esp': expected_sp,
        'observed_return_pc': returned['pc'] if returned else None,
        'observed_return_esp': returned['sp'] if returned else None,
        'thread_match': returned is not None and entry['pid'] == returned['pid'] and entry['tid'] == returned['tid'],
        'stack_match': returned is not None and returned['sp'] == expected_sp,
        'call_context_match': context,
        'context_scope': 'stack-derived continuation and preserved immediate caller return word',
        'nested_depth': None, 'parent_transition_id': None,
        'result': 'PARTIALLY_QUALIFIED' if matched and context else 'FAILED',
        'explanation': 'MATCHED_BOUNDARY_NESTING_UNOBSERVED' if matched and context else 'UNEXPLAINED',
        'entry_time': entry['time'], 'return_time': returned['time'] if returned else None,
        'evidence_ids': [entry['native_line'], returned['native_line'] if returned else None]}


def analyze(run):
    path = OUT / f'{run}-stdout.log'
    native = path.read_text(encoding='ascii')
    lines = native.splitlines()
    entries = markers(native, 'MODE_BRIDGE_ENTRY')
    returns = markers(native, 'MODE_BRIDGE_RETURN')
    frames = []
    for i, entry in enumerate(entries):
        candidates = [v for v in returns if v['index'] == entry['index']]
        ret = candidates[0] if len(candidates) == 1 else None
        end = entries[i+1]['native_line']-1 if i+1 < len(entries) else len(lines)
        split = ret['native_line']-1 if ret else end
        frame = pair(entry, ret, stack_words(lines[entry['native_line']:split]),
                     stack_words(lines[split:end]))
        frame['transition_id'] = f'{run}:{entry["index"]}'
        frames.append(frame)
    wrapper = json.loads((OUT / f'{run}-result.json').read_text())
    tool_error = bool(re.search(r'^.*Syntax error', native, re.M)) or wrapper['timed_out'] or wrapper['exit_code'] != 0
    result = ('TOOL_ERROR' if tool_error else 'PARTIALLY_QUALIFIED'
              if frames and all(f['result'] == 'PARTIALLY_QUALIFIED' for f in frames) else 'FAILED')
    rows = steps(native)
    image = (OUT / f'{run}-after.bin').read_bytes()
    correlation = []
    begin = next((i+1 for i,l in enumerate(lines) if l == 'MODE_WINDOW_BEGIN'), len(lines))
    for row in rows:
        client = 0x400000 <= row['pc'] < 0x707000
        size = len(bytes.fromhex(row['bytes']))
        mapped = image[row['pc']-0x400000:row['pc']-0x400000+size].hex() if client else None
        correlation.append(dict(row, scope='CLIENT' if client else 'EXTERNAL_NATIVE_ONLY',
            mapped_bytes=mapped, agreement=mapped == row['bytes'] and row['boundary_agreement'] if client else None))
    pages = []
    for phase in ('boundary', 'end', 'live', 'mismatch'):
        p = OUT / f'{run}-{phase}.bin'
        if not p.exists():
            continue
        data = p.read_bytes()
        if len(data) != len(image):
            raise ValueError('Truncated image')
        for rva in range(0x1000, 0x170000, 0x1000):
            a, b = image[rva:rva+0x1000], data[rva:rva+0x1000]
            pages.append({'phase': phase, 'rva': rva, 'before_sha256': hashlib.sha256(a).hexdigest(),
                'sample_sha256': hashlib.sha256(b).hexdigest(), 'changed_bytes': sum(x != y for x,y in zip(a,b)),
                'zero_to_nonzero_bytes': sum(x == 0 and y != 0 for x,y in zip(a,b))})
    return {'run': run, 'result': result, 'frames': frames, 'native_sha256': digest(path),
        'script_sha256': digest(OUT / f'capture-{run}.txt'), 'correlation': correlation,
        'pages': pages, 'liveness': markers(native, 'FRAME_LIVENESS'),
        'packer_pcs': [r for r in rows if r['line'] > begin and 0x702000 <= r['pc'] < 0x706000],
        'write_hits': re.findall(r'^MODE_CODE_WRITE_.*$', native, re.M),
        'termination_hits': re.findall(r'^MODE_TERMINATES.*$', native, re.M),
        'limitations': ['Entry breakpoint disabled during return wait; nested transitions not observed',
            'Native stack unwind warnings retained; no inferred callback/unwind explanation',
            'Page snapshots cannot exclude transient writes between samples',
            'Per-step TID not emitted; boundary PID/TID only',
            'No new formal G02 certificate; complete protection/DEP timeline absent']}


def main():
    results = [analyze(run) for run in ('frame-a', 'frame-b')]
    dest = HOME / 'artifacts/reports/g03-final-qualification-20260919'
    dest.mkdir(exist_ok=False)
    coverage = []
    for result in results:
        for frame in result['frames']:
            coverage.append({'segment_id': frame['transition_id'], 'start_pc': frame['entry_pc'],
                'end_pc': frame['observed_return_pc'], 'module': 'WoW64/system boundary',
                'thread': frame['entry_thread'], 'coverage': 'PARTIAL', 'materiality': 'UNKNOWN',
                'transition_ids': [frame['transition_id']], 'call_ids': [], 'branch_ids': [],
                'mutation_events': [], 'evidence_ids': frame['evidence_ids'],
                'scope': 'No BOUNDED_EXTERNAL claim until nested visibility and mutation limits resolved'})
    claims = []
    for run in ('exact-ret-a', 'exact-ret-b'):
        p = OUT / f'{run}-stdout.log'
        claims.append(dict(exact_ret(p.read_text(encoding='ascii')), run=run, native_sha256=digest(p)))
    outputs = {
        'trace-method-qualification.json': {'tool': 'Microsoft x86 CDB', 'tool_version': '10.0.29617.1000',
            'architecture': 'x86 client / WoW64 host', 'transition_type': 'gate-disarmed stack-return breakpoint',
            'result': 'PARTIALLY_QUALIFIED' if all(r['result'] == 'PARTIALLY_QUALIFIED' for r in results) else 'FAILED',
            'runs': [{k:v for k,v in r.items() if k not in ('correlation','pages')} for r in results],
            'g03_core_evidence_eligible': False},
        'transition-frame-ledger.json': [f for r in results for f in r['frames']],
        'startup-window-coverage-v3.json': {'scope': 'boundary segments only; not full startup coverage', 'segments': coverage},
        'runtime-static-correlation-v4.json': {r['run']:r['correlation'] for r in results},
        'mutation-page-samples.json': {r['run']:r['pages'] for r in results},
        'claim-third-init-returns.json': {'claim': 'CLAIM_THIRD_INIT_RETURNS', 'status': 'STRONG',
            'scope': 'Observed RET 0x54ED7A to 0x54A46E, coherent same-PID/TID stack transition only', 'evidence': claims},
        'g03-review.json': {'decision': 'NEED_MORE_EVIDENCE', 'g04_unlocked': False,
            'blockers': ['Nested-transition survival not qualified', 'Boundary memory mutation remains incompletely monitored',
                         'Two new own-G02 formal captures still required', 'Protection timeline incomplete',
                         'Beyond-return liveness sampled in only one run']}}
    for name, value in outputs.items():
        (dest / name).write_text(json.dumps(value, indent=2), encoding='utf-8')
    print(json.dumps([{ 'run':r['run'], 'result':r['result'], 'frames':len(r['frames']),
        'matched':sum(f['result']=='PARTIALLY_QUALIFIED' for f in r['frames']),
        'changed_page_samples':sum(p['changed_bytes']>0 for p in r['pages']),
        'packer_hits':len(r['packer_pcs']), 'liveness':r['liveness']} for r in results]))


if __name__ == '__main__':
    main()
