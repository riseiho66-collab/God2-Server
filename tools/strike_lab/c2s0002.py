"""Bounded opcode-4 provenance and opcode-29 evidence. Never print credentials."""
import csv
import hashlib
import json
from pathlib import Path


def key(home):
    data=(home/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    table=data[0x184c30:0x185030]
    return bytes(16)+bytes((table[i]+i)&255 for i in range(16,256))


def decode(wire,k):
    if len(wire)!=176 or wire[:2]!=b'\xb0\x00':raise ValueError('Invalid frame length')
    previous=(-sum(k))&255;clear=bytearray()
    for i,b in enumerate(wire[2:]):
        value=((b+3-previous)&255)^k[i];clear.append(value);previous=value
    if clear[-1]!=sum(b+0x3c for b in wire[:2]+clear[:-1])&255:raise ValueError('Checksum rejected')
    return bytes(clear[:-1])


def freeze(home):
    from lab import write_json
    source=home/'artifacts/runs/post-seed-cpp-final-03'
    golden=home/'artifacts/golden/post-seed'
    target=golden/'C2S_0002.bin'
    wire=(source/'network/C2S_0002.bin').read_bytes()
    tx=next(json.loads(line) for line in (source/'network-events.jsonl').read_text().splitlines()
        if json.loads(line).get('accepted_buffer') and json.loads(line).get('eax')==176)
    metadata={'length':176,'caller_rva':tx['caller_rva'],'timestamp':tx['timestamp'],
        'session_state':'POST_SEED_ACCEPTED','preceding_packet':'S2C_0002',
        'preceding_s2c_sha256':hashlib.sha256((source/'network/S2C_0002.bin').read_bytes()).hexdigest(),
        'handler_rva':'0x13270','sha256':hashlib.sha256(wire).hexdigest(),
        'source_run':source.name,'credentials':'LOCAL_TEST_ONLY_REDACTED'}
    if target.exists():
        if target.read_bytes()!=wire:raise ValueError('Golden collision')
    else:
        with target.open('xb') as stream:stream.write(wire)
        write_json(target.with_suffix('.json'),metadata)


def provenance(home,out):
    from lab import write_json
    out.mkdir(parents=True,exist_ok=False)
    freeze(home)
    k=key(home)
    ranges=[
        (0,2,'header','0x109c4','payload length + 3','DERIVED'),
        (2,1,'opcode','0x13320','constant 4','CONSTANT'),
        (3,24,'field_01','0xb024;0xb039','controlled account input; bounded copy and forced NUL','ACCOUNT_INPUT'),
        (27,132,'field_02','0xb047;0xb055','controlled password input; bounded copy and forced NUL','ACCOUNT_INPUT'),
        (159,8,'unknown_9c_a3','0x13338','copied from input struct[0x9c:0xa4]; earlier writers unresolved','UNKNOWN'),
        (167,2,'field_a4','0x13f9d','GameSN_God2.DAT scanned as decimal; uint16 <1000, fallback zero','CONFIG'),
        (169,1,'field_a6','0xb097','constant 0xc8','CONSTANT'),
        (170,5,'unknown_a7_ab','0x13338','copied from input struct[0xa7:0xac]; earlier writers unresolved','UNKNOWN'),
        (175,1,'checksum','0x109dd','additive checksum of clear header/payload','DERIVED')]
    write_json(out/'c2s-0002-layout.json',{'wire_length':176,'logical_payload_length':173,
        'builder_entry_rva':'0x13e10','caller_rva':'0xb0d9','input_copy_entry_rva':'0xb010',
        'builder_arguments':'struct172, result-list pointer, message buffer, result-byte pointer',
        'logical_buffer':'session+0x36c8','logical_length_field':'session+0x36c4',
        'framing_entry_rva':'0x124d0','send_return_rva':'0x12506',
        'output_wire_buffer':'codec+0x10','sequence':'NONE_OBSERVED_FOR_THIS_FRAME',
        'all_wire_bytes_covered':sum(r[1] for r in ranges)==176,
        'ranges':[dict(zip(('offset','size','field','writer_rva','source','class'),r)) for r in ranges],
        'write_pipeline':['0x13320 opcode','0x13338 copied 172 bytes','0x109b0/0x109b7 frame payload copy',
            '0x109c4 header','0x109dd checksum','0x10690 transform bytes 2..175'],
        'unknown_warning':'13 copied bytes have no established earlier writer; zero observations are not mandatory constants'})
    captures={}
    for case in ('A','B'):
        run=home/f'artifacts/runs/c2s0002-input-{case}'
        wire=(run/'network/C2S_0002.bin').read_bytes()
        logical=(run/'network/C2S_0002.logical.bin').read_bytes()
        if decode(wire,k)!=logical:raise ValueError('Captured pre-transform bytes disagree')
        captures[case]=(wire,logical)
    a,b=captures['A'],captures['B']
    diff={'only_changed_input':'controlled account; password and zero seed held fixed',
        'wire_changed_offsets':[i for i in range(176) if a[0][i]!=b[0][i]],
        'logical_changed_offsets':[i for i in range(173) if a[1][i]!=b[1][i]],
        'source_runs':['c2s0002-input-A','c2s0002-input-B'],
        'account_input_matched':a[1][1:25].split(b'\0')[0]==b'codexlab' and b[1][1:25].split(b'\0')[0]==b'codexmap',
        'password_input_matched':all(x[1][25:157].split(b'\0')[0]==b'labtest2345' for x in (a,b))}
    write_json(out/'c2s-0002-diff-account.json',diff)
    write_json(out/'c2s-0002-dependencies.json',{'logical_1_24':'ACCOUNT_INPUT',
        'logical_25_156':'PASSWORD_INPUT','logical_157_164':'UNKNOWN_CLIENT_STRUCT',
        'logical_165_166':'CONFIG','logical_167':'CONSTANT_C8','logical_168_172':'UNKNOWN_CLIENT_STRUCT',
        'wire_2_175':'key[i] XOR clear[i], previous clear byte; initial feedback from zero seed',
        'seed_variation':'NOT_RUN: frozen seed baseline retained; transform proven by captured logical/wire equality',
        'semantics':'CREDENTIAL_REQUEST' if diff['account_input_matched'] and diff['password_input_matched'] else 'UNKNOWN',
        'authentication_success':False})
    write_json(out/'S2C_0003_CONTRACT.json',{'opcode':29,'wire_length':176,'logical_length':173,
        'handler_rva':'0x14091','precondition':'after C2S_0002; session enabled; immediate wait in 0x14044',
        'payload':'opcode29 + exact 172-byte request struct; only observed flags=0 branch supported',
        'checks':['strcmp struct[0] with request[0]','strcmp struct[0x18] with request[0x18]'],
        'success':'copy 172 bytes at 0x141db; consume packet; reset wait timer; resume waiting',
        'not_claimed':'authentication completed or terminal login success',
        'legal_immediate_candidates':[
            {'opcode':4,'logical_length':5,'handler_rva':'0x14234','role':'index/list setup'},
            {'opcode':5,'logical_length':9,'handler_rva':'0x1426f','role':'indexed update; requires preceding index'},
            {'opcode':6,'logical_length':5,'handler_rva':'0x142d0','role':'nested indexed update; requires preceding indices'},
            {'opcode':10,'logical_length':17,'handler_rva':'0x14386','role':'terminal result; deferred'},
            {'opcode':29,'logical_length':173,'handler_rva':'0x14091','role':'selected request-structure acknowledgement'},
            {'opcode':30,'logical_length':2,'handler_rva':'0x14325','role':'failure result'}]})


def summarize(home,run,events,prior):
    from lab import write_json
    k=key(home)
    baseline_ok=prior.get('LAST_ACCEPTED_STATE')=='POST_SEED_ACCEPTED'
    tx=next((e for e in events if e.get('accepted_buffer') and e.get('eax')==176 and e.get('caller_rva')=='0x12506'),None)
    entered=next((e for e in events if e.get('event_type')=='S2C0003_HANDLER_ENTERED'),None)
    comparisons=[next((e for e in events if e.get('event_type')==name),None) for name in
        ('S2C0003_COMPARE_1','S2C0003_COMPARE_2','S2C0003_STRUCT_COPIED','S2C0003_CONSUMED')]
    logical=(run/'network/C2S_0002.logical.bin').read_bytes() if (run/'network/C2S_0002.logical.bin').exists() else b''
    wire=(run/tx['accepted_buffer']).read_bytes() if tx else b''
    request_valid=bool(baseline_ok and tx and logical and decode(wire,k)==logical and logical[0]==4)
    rx=b''.join((run/'s2c'/f'recv-{e["sequence"]:04}.bin').read_bytes() for e in events
        if e.get('event_type')=='API_RETURN' and e.get('api')=='recv' and e.get('matched')
        and tx and entered and tx['sequence']<e['sequence']<entered['sequence'] and 0<e.get('eax',0)<=4096)
    expected=b'\x1d'+logical[1:]
    accepted=bool(prior.get('LAST_ACCEPTED_STATE')=='POST_SEED_ACCEPTED' and request_valid and entered
        and all(comparisons) and comparisons[0]['eax']==0 and comparisons[1]['eax']==0
        and len(rx)==176 and decode(rx,k)==expected
        and entered['sequence']<comparisons[0]['sequence']<comparisons[1]['sequence']<comparisons[2]['sequence']<comparisons[3]['sequence'])
    result={'classification':'STATE_ADVANCED' if accepted else 'HANDLER_ENTERED' if entered and baseline_ok else 'UNVERIFIED',
        'LAST_ACCEPTED_STATE':'S2C0003_ACCEPTED_WAIT_CONTINUES' if accepted else prior.get('LAST_ACCEPTED_STATE'),
        'LAST_ACCEPTED_PACKET':'S2C_0003' if accepted else prior.get('LAST_ACCEPTED_PACKET'),
        'NEXT_EXPECTED_DIRECTION':'S2C','NEXT_BLOCKER':'NEXT_TERMINAL_RESPONSE_CONTRACT_UNKNOWN' if accepted else 'S2C0003_NOT_VERIFIED',
        'NEW_CLIENT_TX':0,'NEW_HANDLER':'0x14091' if entered and baseline_ok else None,
        'C2S0002_CONTRACT_VERIFIED':request_valid,'CREDENTIAL_REQUEST_VERIFIED':request_valid,'LOGIN':False,'LOGIN_SUCCESS':False}
    write_json(run/'c2s0002-result.json',result)
    if wire:
        with (run/'network/C2S_0002.wire.bin').open('xb') as stream:stream.write(wire)
    if accepted:
        golden=home/'artifacts/golden/c2s0002'/run.name;golden.mkdir(parents=True,exist_ok=False)
        with (run/'network/S2C_0003.bin').open('xb') as stream:stream.write(rx)
        write_json(run/'network/S2C_0003.json',{'length':len(rx),'opcode':29,'handler_rva':'0x14091',
            'timestamp':entered['timestamp'],'sha256':hashlib.sha256(rx).hexdigest(),
            'preceding_c2s_sha256':hashlib.sha256(wire).hexdigest(),'state_after':result['LAST_ACCEPTED_STATE'],
            'credentials':'LOCAL_TEST_ONLY_REDACTED'})
        for name in ('C2S_0002.wire.bin','C2S_0002.logical.bin','C2S_0002.json','S2C_0003.bin','S2C_0003.json'):
            (golden/name).write_bytes((run/'network'/name).read_bytes())
        with (run/'protocol-core.csv').open(newline='',encoding='utf-8') as stream:rows=list(csv.reader(stream))
        rows[4][3]='4';rows[4][6]='CREDENTIAL_REQUEST_SENT';rows[4][8]='RUNTIME_INPUT_PROVENANCE'
        rows.append(['5','S2C','CREDENTIAL_REQUEST_SENT','29','176','0x14091','S2C0003_ACCEPTED_WAIT_CONTINUES','S2C_0003.bin','RUNTIME_VERIFIED'])
        with (golden/'protocol-core.csv').open('x',newline='',encoding='utf-8') as stream:csv.writer(stream).writerows(rows)
        with (run/'protocol-core-c2s0002.csv').open('x',newline='',encoding='utf-8') as stream:csv.writer(stream).writerows(rows)
        write_json(golden/'session.json',{'source_run':str(run),**result})
    return result


if __name__=='__main__':
    from lab import HOME
    provenance(HOME,HOME/'artifacts/contracts/c2s0002-v1')
