"""One directory entry enabled by opcode4 before terminal login returns."""
import csv
import hashlib
import json

WIRE=bytes.fromhex('08000101fdfefeae')


def qualifies(prior,events,wire):
    if not prior.get('LOGIN') or wire!=WIRE:return False
    names=('SERVER_LIST_HANDLER','SERVER_LIST_WRITTEN','SERVER_LIST_UI_COUNT','SERVER_LIST_UI_READY')
    points=[next((e for e in events if e.get('event_type')==name),None) for name in names]
    if not all(points):return False
    h,w,c,r=points
    return bool(h['sequence']<w['sequence']<c['sequence']<r['sequence']
        and 'entry0=10000' in w.get('written','')
        and all('count=1 selected=0 enabled0=1 directory_count=1' in e.get('list_state','') for e in (c,r)))


def summarize(home,run,events,prior):
    from lab import write_json
    start=next((e for e in events if e.get('event_type')=='S2C0003_CONSUMED'),None)
    handler=next((e for e in events if e.get('event_type')=='SERVER_LIST_HANDLER'),None)
    wire=b''.join((run/'s2c'/f'recv-{e["sequence"]:04}.bin').read_bytes() for e in events
        if e.get('event_type')=='API_RETURN' and e.get('api')=='recv' and e.get('matched')
        and start and handler and start['sequence']<e['sequence']<handler['sequence'] and 0<e.get('eax',0)<=4096)
    accepted=qualifies(prior,events,wire)
    ready=next((e for e in events if e.get('event_type')=='SERVER_LIST_UI_READY'),None)
    new_tx=next((e for e in events if e.get('accepted_buffer') and ready and e['sequence']>ready['sequence']),None)
    result={'LAST_ACCEPTED_STATE':'SERVER_SELECTION_STATE' if accepted else prior.get('LAST_ACCEPTED_STATE'),
        'LOGIN':bool(prior.get('LOGIN')),'SERVER_LIST_READY':accepted,'SERVER_COUNT':1 if accepted else 0,
        'SELECTED_ENTRY_ID':0 if accepted else None,'SERVER_SELECTION_CONFIRMED':False,
        'NEW_CLIENT_TX':new_tx['eax'] if accepted and new_tx else 0,
        'NEXT_BLOCKER':'SERVER_SELECT_C2S_CONTRACT_UNKNOWN' if accepted and new_tx else 'SERVER_SELECTION_CONFIRMATION_PENDING' if accepted else 'SERVER_LIST_UNVERIFIED' if prior.get('LOGIN') else 'REGRESSION'}
    write_json(run/'server-list-result.json',result)
    write_json(run/'S2C_SERVER_LIST_0001_CONTRACT.json',{'opcode':4,'logical_length':5,'wire_length':8,
        'handler_rva':'0x14234','writer_rva':'0x1424d','consumer_rva':'0x6e45',
        'order':'opcode29, opcode4 entry status, opcode10 terminal; no login packet bytes changed',
        'gate':'credential receive loop, before terminal return; no evidence of post-terminal receive handler',
        'directory_count':'global VA 0x5b489c; already 1, NOT a packet count field',
        'directory_pointer':'VA 0x5b48a0; name supplied by existing directory',
        'entry_table':'UI+0x8c; stride20; server_count is number of visible enabled entries',
        'fields':[{'logical_offset':0,'width':1,'class':'REQUIRED_CONSTANT','value':4},
                  {'logical_offset':1,'width':1,'class':'ENTRY_FIELD','value':0,'condition':'id<64; also present in directory'},
                  {'logical_offset':2,'width':1,'class':'UNKNOWN_SAFE','value':0,'scope':'not read by visible-entry predicate'},
                  {'logical_offset':3,'width':2,'class':'ENTRY_FIELD','value':1,'condition':'nonzero uint16 LE at entry+2'}],
        'reads':['0x14234 id byte','0x14242 entry DWORD','0x6e45 enabled word','0x6e6b name append','0x6ea1 visible-count increment'],
        'zero_failure':'enabled word zero skips row; no rows leads to no-servers-open message',
        'endpoint':'not in this packet; frozen profile ctserver.ini supplies only 127.0.0.1',
        'selection':'client selects directory ID0 automatically; confirmation remains a separate UI action',
        'runtime_accepted':accepted})
    if not accepted:return result
    golden=home/'artifacts/golden/server-list'/run.name;golden.mkdir(parents=True,exist_ok=False)
    (run/'network/S2C_SERVER_LIST_0001.bin').write_bytes(wire)
    (golden/'S2C_SERVER_LIST_0001.bin').write_bytes(wire)
    write_json(golden/'S2C_SERVER_LIST_0001.json',{'length':8,'opcode':4,'handler_rva':'0x14234',
        'sha256':hashlib.sha256(wire).hexdigest(),'source_run':run.name,'preceding_packet':'S2C_0003',
        'next_packet':'S2C_0004 terminal','LOGIN_regression_passed':True})
    login=home/'artifacts/golden/login'/run.name
    for name in ('S2C_0001.bin','C2S_0001.bin','S2C_0002.bin','C2S_0002.bin','S2C_0003.bin','S2C_0004.bin'):
        (golden/name).write_bytes((login/name).read_bytes())
    with (login/'protocol-core.csv').open(newline='',encoding='utf-8') as stream:rows=list(csv.reader(stream))
    rows[-1][0]='7'
    rows.insert(-1,['6','S2C','S2C0003_ACCEPTED_WAIT_CONTINUES','4','8','0x14234','ENTRY_STATUS_INSTALLED','S2C_SERVER_LIST_0001.bin','RUNTIME_VERIFIED'])
    for path in (golden/'protocol-core.csv',run/'protocol-core-server-list.csv'):
        with path.open('x',newline='',encoding='utf-8') as stream:csv.writer(stream).writerows(rows)
    if new_tx:
        packet=(run/new_tx['accepted_buffer']).read_bytes()
        (golden/'C2S_SERVER_SELECT_0001.bin').write_bytes(packet)
        write_json(golden/'C2S_SERVER_SELECT_0001.json',{'length':len(packet),'caller_rva':new_tx.get('caller_rva'),
            'selected_entry':0,'semantic_role':'UNVERIFIED'})
    write_json(golden/'session.json',{'source_run':str(run),'classification':'LIST_VISIBLE',**result})
    return result


if __name__=='__main__':
    import sys
    from lab import HOME
    run=HOME/'artifacts/runs'/sys.argv[1]
    events=[]
    for name in ('compat-events.jsonl','network-events.jsonl'):
        events.extend(json.loads(line) for line in (run/name).read_text().splitlines())
    events.sort(key=lambda e:e.get('sequence',-1))
    print(json.dumps(summarize(HOME,run,events,json.loads((run/'login-terminal-result.json').read_text()))))
