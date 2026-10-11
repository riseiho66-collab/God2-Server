"""Summarize observed startup blockers, not protocol or compatibility claims."""
import hashlib
import json
from pathlib import Path
HOME=Path(__file__).resolve().parents[3]
OUT=HOME/'artifacts/capture_work/host-20260918-1430/output'


def main():
    dest=HOME/'artifacts/reports/strike-phase2-20260919'
    dest.mkdir(exist_ok=False)
    runs=[]
    for run in ('native-master-02','native-master-02b','native-master-02c','native-master-02d','native-master-02e'):
        result=json.loads((OUT/f'{run}-result.json').read_text())
        events=json.loads((OUT/f'{run}-api-events.json').read_text())
        entries=[e for e in events if e['kind']=='API_ENTRY']
        runs.append({'run':run,'arguments':result['arguments'],'result':result['result'],
            'argument_check_passed':result.get('argument_check_passed',False),
            'last_observed_pc':events[-1].get('pc'),
            'last_pc_usable':run!='native-master-02b',
            'native_context_warning':'02b final native stop was displayed in forced x86 mode; truncated PC must not be used' if run.endswith('02b') else None,
            'api_hits':sorted({e['api'] for e in entries}),
            'native_sha256':hashlib.sha256((OUT/f'{run}-native.log').read_bytes()).hexdigest()})
    blockers=[{'id':'B001','status':'RESOLVED_FOR_ARGUMENT_PARSING_ONLY','fact':'Four controlled tokens reach 0x531E28'},
        {'id':'B002','status':'OBSERVED_UNRESOLVED','fact':'0x45B662 compares first byte of timeGetTime to 0x83; runtime byte 0xFF; JE at 0x45B665 not taken',
         'evidence':'native-master-02e API event sequence 59','interpretation':'Implementation-byte assumption; intent and acceptable compatibility remedy not established'},
        {'id':'B003','status':'OBSERVED_UNRESOLVED','fact':'Error-display path 0x45B7A4 has zero string-table count/pointer; null format reaches 0x54CF19',
         'evidence':['native-master-02c','native-master-02d','native-master-02b'],
         'limitation':'Cause of empty table not established; first-chance AV followed by second-chance c000041d'},
        {'id':'B004','status':'NOT_REACHED','fact':'No monitored Winsock entry observed; destination port not confirmed'}]
    (dest/'argument-matrix.json').write_text(json.dumps(runs,indent=2))
    (dest/'startup-blockers.json').write_text(json.dumps(blockers,indent=2))
    (dest/'scoreboard.json').write_text(json.dumps({'ARGUMENT_PARSER':'PASS','FULL_STARTUP':'NOT_ESTABLISHED',
        'WSAStartup':False,'socket':False,'connect':False,'loopback_accept':False,'first_tx':False,
        'frame_format':False,'handshake':False,'login':False,'character_screen':False,'world':False,
        'heartbeat':False,'movement':False,'G03':'NEED_MORE_EVIDENCE','G04':'UNVERIFIED',
        'native_WOW64_qualification':'UNCHANGED','master02_G02_certificate':'NOT_ISSUED'},indent=2))
    print('Five runs retained; two argument sets; no Winsock hit or listener launch.')


if __name__=='__main__':
    main()
