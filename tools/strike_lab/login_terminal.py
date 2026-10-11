"""Qualify terminal login using frame, successful return and actual state write."""
import csv
import hashlib
import json


def frame(key):
    payload=bytes([10])+bytes(16)
    header=bytes([20,0])
    clear=payload+bytes([sum(b+60 for b in header+payload)&255])
    previous=(-sum(key))&255;wire=bytearray(header)
    for i,value in enumerate(clear):
        wire.append(((value^key[i])+previous-3)&255);previous=value
    return bytes(wire)


def qualify(events,prior,wire,expected):
    names=('LOGIN_TERMINAL_HANDLER','LOGIN_TERMINAL_RETURN','LOGIN_STATE_CHANGE_ENTER','LOGIN_STATE_CHANGE_RETURN')
    points=[next((e for e in events if e.get('event_type')==name),None) for name in names]
    if prior.get('LAST_ACCEPTED_STATE')!='S2C0003_ACCEPTED_WAIT_CONTINUES' or not all(points) or wire!=expected:return False
    h,r,b,a=points
    return bool(h['sequence']<r['sequence']<b['sequence']<a['sequence'] and r.get('eax')==0
        and 'state=f previous=' in b.get('ui_state','') and 'state=2 previous=f' in a.get('ui_state',''))


def summarize(home,run,events,prior):
    from lab import write_json
    from c2s0002 import key
    expected=frame(key(home))
    start=next((e for e in events if e.get('event_type')=='S2C0003_CONSUMED'),None)
    list_written=next((e for e in events if e.get('event_type')=='SERVER_LIST_WRITTEN'),None)
    if start and list_written and list_written['sequence']>start['sequence']:start=list_written
    handler=next((e for e in events if e.get('event_type')=='LOGIN_TERMINAL_HANDLER'),None)
    rx=b''.join((run/'s2c'/f'recv-{e["sequence"]:04}.bin').read_bytes() for e in events
        if e.get('event_type')=='API_RETURN' and e.get('api')=='recv' and e.get('matched')
        and start and handler and start['sequence']<e['sequence']<handler['sequence'] and 0<e.get('eax',0)<=4096)
    accepted=qualify(events,prior,rx,expected)
    state=next((e for e in events if e.get('event_type')=='LOGIN_STATE_CHANGE_RETURN'),None)
    new_tx=next((e for e in events if e.get('accepted_buffer') and state and e['sequence']>state['sequence']),None)
    empty=any('\u6c92\u6709\u4efb\u4f55\u4f3a\u670d\u5668\u958b\u555f' in e.get('message_text','') for e in events)
    result={'LAST_ACCEPTED_STATE':'LOGIN_ACCEPTED' if accepted else prior.get('LAST_ACCEPTED_STATE'),
        'LOGIN':accepted,'TERMINAL_HANDLER_RVA':'0x14386' if handler else None,'TERMINAL_OPCODE':'0x0A',
        'NEW_CLIENT_TX':new_tx['eax'] if accepted and new_tx else 0,
        'NEXT_BLOCKER':'POST_LOGIN_SERVER_LIST_EMPTY' if accepted and empty else 'C2S_0003_CONTRACT_UNKNOWN' if accepted and new_tx else 'CHARACTER_TRANSITION_UNOBSERVED' if accepted else 'LOGIN_TERMINAL_UNVERIFIED'}
    write_json(run/'login-terminal-result.json',result)
    write_json(run/'LOGIN_TERMINAL_S2C_CONTRACT.json',{'opcode':10,'wire_length':20,'payload_length':17,
        'state_before':'STATE_AFTER_S2C_0003','handler_rva':'0x14386','transform':'NO_NEW_TRANSFORM_OBSERVED',
        'reads':[{'offset':1,'width':4,'writer_rva':'0x1438e'},{'offset':5,'width':4,'writer_rva':'0x14393'},
                 {'offset':9,'width':4,'writer_rva':'0x14399'},{'offset':13,'width':4,'writer_rva':'0x143a1'},
                 {'offset':1,'width':1,'condition':'value!=5 skips informational-message path; both paths return zero'}],
        'selected_payload':'0a followed by 16 zeros; only this exact candidate certified',
        'field_classes':[{'offset':0,'size':2,'class':'FRAME'}, {'offset':2,'size':1,'class':'OPCODE'},
                         {'offset':3,'size':1,'class':'RESULT_CODE'}, {'offset':4,'size':15,'class':'UNKNOWN_SAFE'},
                         {'offset':19,'size':1,'class':'FRAME'}],
        'unknown_safe_scope':'only through verified state 0xf -> 2; no account/profile semantics asserted',
        'success_evidence':['return RVA 0xb0d9 EAX=0','state setter requested 2','state at +0x178cec changed 0xf -> 2'],
        'failure_path':'separate opcode30, payload length2, handler RVA0x14325 returns1; not exercised',
        'legal_immediate_handlers':'same state-local set 4,5,6,10,29,30 from c2s0002-v2; no new dispatcher gate',
        'request_dependencies':'none read before state transition','runtime_accepted':accepted})
    if not accepted:return result
    golden=home/'artifacts/golden/login'/run.name;golden.mkdir(parents=True,exist_ok=False)
    sources={'S2C_0001.bin':'s2c-000001.bin','C2S_0001.bin':'c2s-000001.bin',
        'S2C_0002.bin':'S2C_0002.bin','C2S_0002.bin':'C2S_0002.bin','S2C_0003.bin':'S2C_0003.bin'}
    for target,source in sources.items():(golden/target).write_bytes((run/'network'/source).read_bytes())
    (golden/'S2C_0004.bin').write_bytes(rx)
    (run/'network/S2C_0004.bin').write_bytes(rx)
    if new_tx:
        wire=(run/new_tx['accepted_buffer']).read_bytes()
        (golden/'C2S_0003.bin').write_bytes(wire)
        (run/'network/C2S_0003.bin').write_bytes(wire)
        metadata={'length':len(wire),'opcode':'UNKNOWN','caller_rva':new_tx.get('caller_rva'),
            'state_before':'LOGIN_ACCEPTED','state_after':'UNKNOWN','preceding_s2c_sha256':hashlib.sha256(rx).hexdigest()}
        write_json(golden/'C2S_0003.json',metadata);write_json(run/'network/C2S_0003.json',metadata)
    with (run/'protocol-core-c2s0002.csv').open(newline='',encoding='utf-8') as stream:rows=list(csv.reader(stream))
    rows[1][7]='S2C_0001.bin';rows[2][7]='C2S_0001.bin'
    rows.append(['6','S2C','S2C0003_ACCEPTED_WAIT_CONTINUES','10','20','0x14386','LOGIN_ACCEPTED','S2C_0004.bin','RUNTIME_VERIFIED'])
    with (golden/'protocol-core.csv').open('x',newline='',encoding='utf-8') as stream:csv.writer(stream).writerows(rows)
    write_json(golden/'session.json',{'source_run':str(run),'NEXT_PHASE':'CHARACTER',
        'phase_prerequisite':'server list before character selection','classification':'LOGIN_ACCEPTED',**result})
    return result
