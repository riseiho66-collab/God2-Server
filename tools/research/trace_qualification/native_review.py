"""Narrow native WOW64 boundary qualification, not OEP certification."""
import json
import re
from pathlib import Path
import sys
HOME = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(HOME/'tools/research'))
from host_capture import digest
OUT = HOME/'artifacts/capture_work/host-20260918-1430/output'


def validate(events):
    a,n,r,b = events
    return (len({(e['pid'],e['tid']) for e in events}) == 1
        and a['time'] <= n['time'] <= r['time'] <= b['time']
        and a['expected'] == b['eip'] and b['esp'] == a['esp']+4
        and r['rsp'] == b['esp'] and n['rip'] == a['eip']+9)


def review(run):
    path = OUT/f'{run}-native.log'
    native = path.read_text(encoding='ascii')
    tags = ('NATIVE_X86_ENTRY','NATIVE_EXEC','NATIVE_RETURN','NATIVE_X86_RETURN')
    events = []
    for tag in tags:
        matches = list(re.finditer(r'(?:^|> )'+tag+r' ([^\n]+)', native, re.M))
        if len(matches) != 1:
            raise ValueError('Missing/ambiguous '+tag)
        m = matches[0]
        event = {k:int(v,16) for k,v in re.findall(r'(\w+)=([a-f0-9]+)',m[1])}
        event['evidence_line'] = native[:m.start()].count('\n')+1
        events.append(event)
    if not validate(events):
        raise ValueError('Context/return mismatch')
    a,n,r,b = events
    region = '\n'.join(native.splitlines()[n['evidence_line']:b['evidence_line']])
    if not ('cs=0033' in region and 'cs=0023' in region and '41ff2e' in region
            and f'0023{a["expected"]:08x}' in region):
        raise ValueError('Missing native far-return and selector evidence')
    return {'run':run,'transition_id':run+':0','pid':a['pid'],'tid':a['tid'],
        'x86_entry_pc':a['eip'],'x86_entry_esp':a['esp'],
        'native_entry_pc':n['rip'],'native_rsp':n['rsp'],
        'native_return_pc':r['rip'],'native_rsp_before_return':r['rsp'],
        'x86_resume_pc':b['eip'],'x86_resume_esp':b['esp'],
        'effective_machines':['x86','amd64','amd64','x86'],
        'context_switch_method':'.effmach / native far-jump single steps',
        'evidence_ids':[e['evidence_line'] for e in events], 'native_sha256':digest(path),
        'commands_sha256':digest(OUT/f'{run}-commands.txt')}


if __name__ == '__main__':
    rows = [review(r) for r in ('native-f','native-g')]
    dest = HOME/'artifacts/reports/native-wow64-20260919'
    dest.mkdir(exist_ok=False)
    (dest/'wow64-context-ledger.json').write_text(json.dumps(rows,indent=2))
    (dest/'trace-method-qualification.json').write_text(json.dumps({
        'NATIVE_WOW64_TRACE':'QUALIFIED','scope':'One known QueryVolumeInformationFile boundary reproduced twice',
        'limitations':['System internals bounded, not fully traced','Not G03; full startup and own G02 still required'],
        'runs':rows},indent=2))
    print('NATIVE_WOW64_TRACE = QUALIFIED (known boundary only)')
