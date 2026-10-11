"""Review bridge qualification and directly observed RETs without G03 promotion."""
import hashlib
import json
from pathlib import Path
import re
from startup_closure_ledgers import steps

HOME = Path(__file__).resolve().parents[2]
OUT = HOME/'artifacts/capture_work/host-20260918-1430/output'


def markers(text, prefix):
    result = []
    for match in re.finditer(r'^'+prefix+r' (.+)$', text, re.M):
        values = {k:int(v,16) for k,v in re.findall(r'(\w+)=([0-9a-f]+)', match[1])}
        values['native_line'] = text[:match.start()].count('\n')+1
        result.append(values)
    return result


def matching_return(entry, returned):
    return (entry['pid']==returned['pid'] and entry['tid']==returned['tid']
            and returned['pc']==entry.get('expected',entry.get('target'))
            and returned['sp']==entry['sp']+4 and returned['time']>=entry['time'])


def exact_ret(text):
    before = markers(text, 'EXACT_RET_BEFORE')
    after = markers(text, 'EXACT_RET_AFTER')
    if len(before)!=1 or len(after)!=1:
        raise ValueError('Missing/ambiguous RET pair')
    a,b = before[0],after[0]
    segment = '\n'.join(text.splitlines()[a['native_line']:b['native_line']])
    if not (a['pc']==0x54ed7a and a['target']==0x54a46e and matching_return(a,b)
            and re.search(r'^0054ed7a c3\s+ret\s*$',segment,re.M)
            and '001afefc  0054a46e' in segment and '0:000> t' in segment
            and 'eip=0054a46e esp=001aff00' in segment):
        raise ValueError('RET native/register/stack mismatch')
    return {'classification':'RETURNS','return_site':a['pc'],'return_address':a['target'],
        'return_observed':True,'callee_trace_complete':False,'stack_before':a['sp'],'stack_after':b['sp'],
        'pid':a['pid'],'thread':a['tid'],'trace_gap_before_return':True,
        'evidence_ids':[a['native_line'],b['native_line']],
        'scope':'Exact final RET established; preceding callee internals remain partially observed'}


def main():
    dest = HOME/'artifacts/reports/g03-mode-20260919-v2'
    dest.mkdir(exist_ok=False)
    runs = ['mode-qual','mode-a','mode-hw-a','mode-hw-b','exact-ret-a','exact-ret-b']
    qualification, calls, coverage, mutation, correlation, branches, protection = {},{},{},{},{},{},{}
    for run in runs:
        p = OUT/(run+'-stdout.log'); native=p.read_text(encoding='ascii')
        error = bool(re.search(r'^.*Syntax error',native,re.M))
        entry_prefix, return_prefix = ('QUAL_MODE_ENTRY','QUAL_MODE_RETURN') if run=='mode-qual' else ('MODE_BRIDGE_ENTRY','MODE_BRIDGE_RETURN')
        entries, returns = markers(native,entry_prefix), markers(native,return_prefix)
        pairs = []
        for i,a in enumerate(entries):
            b = returns[i] if i<len(returns) else None
            pairs.append({'entry':a,'returned':b,'matching_return':b is not None and matching_return(a,b)})
        result = 'TOOL_ERROR' if error else ('LIMITED_BOUNDARY_PASS' if run=='mode-qual' and len(pairs)==1 and pairs[0]['matching_return'] else 'NOT_QUALIFIED_FOR_STARTUP')
        if run.startswith('exact-ret'):
            calls[run]=[exact_ret(native)]
            result='EXACT_RET_PASS_NOT_G03'
        else:
            calls[run]=[{'target_va':a['entry']['pc'],'entry_observed':True,
                'callee_trace_complete':False,'return_site':a['entry']['expected'],
                'return_observed':a['matching_return'],'stack_before':a['entry']['sp'],
                'stack_after':a['returned']['sp'] if a['returned'] else None,
                'thread':a['entry']['tid'],'trace_gap_before_return':True,
                'evidence_ids':[a['entry']['native_line'],a['returned']['native_line'] if a['returned'] else None]} for a in pairs]
        qualification[run]={'tool':'Microsoft x86 CDB','version':'10.0.29617.1000','result':result,
            'configuration':'hardware return' if run.startswith('mode-hw') else 'software return/explicit RET stops',
            'test_path':'candidate startup / WoW64 boundary / third routine',
            'expected_observations':['same PID/TID','stack-derived return PC','ESP + 4','ordered timestamp'],
            'actual_observations':pairs,'native_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'limitations':['No instruction coverage inside WoW64/system kernel path',
                           'An address hit without matching stack is not a matching return',
                           'Failed extended qualification cannot unlock G03']}
        rows = steps(native)
        imagepath = OUT/(run+'-after.bin')
        image = imagepath.read_bytes() if imagepath.exists() else None
        correlation[run]=[]; branches[run]=[]
        for i,r in enumerate(rows):
            if image is not None and 0x400000<=r['pc']<0x707000:
                offset=r['pc']-0x400000; size=len(bytes.fromhex(r['bytes']))
                correlation[run].append(dict(r,rva=offset,mapped_bytes=image[offset:offset+size].hex(),
                    agreement=image[offset:offset+size].hex()==r['bytes'] and r['boundary_agreement']))
            if r['capstone'] and r['capstone'].split()[0].startswith('j') and i+1<len(rows):
                nxt=rows[i+1]
                branches[run].append({'branch_site':r['pc'],'condition':r['capstone'],
                    'flags':'native flags retained in referenced log; parser does not infer omitted flags',
                    'previous_pc':rows[i-1]['pc'] if i else None,'next_pc':nxt['pc'],
                    'target':None,'taken':None,
                    'next_pc_scope':'next recorded PC, not a proven immediate successor',
                    'trace_mode':'x86','gap_before':'UNKNOWN','gap_after':'UNKNOWN',
                    'evidence_ids':[r['line'],nxt['line']]})
        coverage[run]=[{'start_pc':pair['entry']['pc'],'end_pc':pair['returned']['pc'] if pair['returned'] else None,
            'thread':pair['entry']['tid'],'trace_method':'stack-derived boundary breakpoint',
            'coverage_status':'EXTERNAL_NATIVE_ONLY' if pair['matching_return'] else 'GAP',
            'materiality':'UNKNOWN' if pair['matching_return'] else 'MATERIAL',
            'event_ids':[pair['entry']['native_line']],
            'known_gap_reason':'System internals untraced' if pair['matching_return'] else 'Expected stack/PC return mismatch'} for pair in pairs]
        if run.startswith('exact-ret'):
            coverage[run]=[{'start_pc':0x5479bd,'end_pc':0x54ed7a,'coverage_status':'PARTIAL','materiality':'UNKNOWN','known_gap_reason':'breakpoint-to-breakpoint execution'},
                {'start_pc':0x54ed7a,'end_pc':0x54a46e,'coverage_status':'FULL','materiality':'NON_MATERIAL','known_gap_reason':None,'trace_method':'one native instruction step'}]
        script=(OUT/('capture-'+run+'.txt')).read_text()
        watches=re.findall(r'ba w 4 \(@\$t0\+([0-9a-f]+)\)',script)
        hits=re.findall(r'^(?:MODE|EXACT)_CODE_WRITE_.*$',native,re.M)
        mutation[run]={'watched_ranges':[[0x400000+int(v,16),0x400004+int(v,16)] for v in watches],
            'observed_write_hits':hits,'scope':'Three 4-byte hardware watchpoints, not full .text coverage',
            'secondary_unpack_absent':None,'limitations':'No-hit cannot exclude writes elsewhere or prove full monitor qualification'}
        protection[run]={'dep_policy':'NOT_QUERIED_FOR_THIS_PID',
            'native_vprot_lines':[i+1 for i,l in enumerate(native.splitlines()) if l.startswith('BaseAddress:')],
            'all_requested_stages_present':False}
    outputs={'trace-method-qualification.json':qualification,'startup-call-ledger.json':calls,
        'startup-branch-ledger.json':branches,'startup-window-coverage.json':coverage,
        'secondary-unpack-observation.json':mutation,'runtime-static-correlation-v3.json':correlation,
        'protection-timeline.json':protection,
        'g03-review.json':{'decision':'NEED_MORE_EVIDENCE','exact_completion':'RETURNS reproduced twice',
            'primary_blocker':'Extended bridge qualification fails matching return; material gap remains',
            'new_g02_certificate_issued':False,'g04_unlocked':False}}
    for name,value in outputs.items():
        (dest/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps({run:q['result'] for run,q in qualification.items()}))


if __name__=='__main__':
    main()
