"""Evidence reducer for one opcode-1 post-seed transition; no login inference."""
import csv
import hashlib
import json

WIRE=bytes.fromhex('0500fe5199')


def summarize(home,run,events,seed):
    from lab import write_json
    verified=seed.get('LAST_ACCEPTED_STATE')=='INITIAL_SEED_EXCHANGE'
    entered=next((e for e in events if e.get('event_type')=='POST_SEED_HANDLER_ENTERED'),None)
    field=next((e for e in events if e.get('event_type')=='POST_SEED_FIELD_ACCEPTED'),None)
    returned=next((e for e in events if e.get('event_type')=='POST_SEED_WAIT_RETURN' and e.get('eax')==0),None)
    end=next((e['sequence'] for e in events if e.get('event_type')=='INITIAL_HANDSHAKE_RETURN'),float('inf'))
    rx=b''.join((run/'s2c'/f'recv-{e["sequence"]:04}.bin').read_bytes() for e in events
        if e.get('api')=='recv' and e.get('event_type')=='API_RETURN' and e.get('matched')
        and 0<e.get('eax',0)<=4096 and end<e['sequence']<(entered['sequence'] if entered else float('inf')))
    accepted=bool(verified and rx==WIRE and entered and field and returned
        and entered['sequence']<field['sequence']<returned['sequence']
        and 'opcode=1 received=53 expected=53' in entered.get('field_comparison',''))
    tx=next((e for e in events if e.get('accepted_buffer') and returned and e['sequence']>returned['sequence']),None)
    result={'LAST_ACCEPTED_STATE':'POST_SEED_ACCEPTED' if accepted else 'INITIAL_SEED_EXCHANGE' if verified else 'REGRESSION',
        'LAST_ACCEPTED_PACKET':'S2C_0002' if accepted else 'C2S_0001' if verified else None,
        'NEXT_EXPECTED_DIRECTION':'UNKNOWN_PENDING_C2S_0002_ANALYSIS' if accepted and tx else 'S2C',
        'NEXT_BLOCKER':'C2S_0002_CONTRACT_UNKNOWN' if accepted and tx else 'POST_SEED_TRANSITION_UNVERIFIED',
        'NEW_CLIENT_TX':tx['eax'] if accepted and tx else 0,
        'NEW_HANDLER':'0x13270' if verified and entered else None}
    contract={'name':'POST_SEED_S2C_0001_CONTRACT','opcode':1,'wire_length':5,'header_length':2,
        'payload_length':2,'payload_hex':'0153','handler_rva':'0x13270','success_rva':'0x132ce',
        'comparison':'payload[1] == session[0x754]; observed 0x53',
        'length_evidence':'opcode 1 -> table[1] at VA 0x401328 -> VA 0x401216 -> length 2',
        'state_gate':'session[0x2cb8]==1; immediate caller VA 0x413f28 waits in VA 0x4131c0',
        'other_opcodes':'consumed and skipped by this wait; not acceptance candidates',
        'transform':'zero seed: key[0..2]=0; frame feedback=0; out=clear+previous_clear-3 mod 256',
        'checksum':'sum(header and payload bytes + 0x3c each) mod 256 = 0x49',
        'success':'comparison equal, packet consumed, wait returns zero',
        'failure':'different opcode skipped; mismatching byte returns one; wait timeout 30000 ms',
        'evidence':'artifacts/runs/post-seed-contract-01/compat-events.jsonl',
        'runtime_accepted':accepted,'LOGIN':False}
    write_json(run/'POST_SEED_S2C_0001_CONTRACT.json',contract)
    write_json(run/'post-seed-result.json',result)
    if not accepted:return result
    (run/'network/S2C_0002.bin').write_bytes(rx)
    rows=[(1,'S2C','CONNECTED','',19,'0x10e80','SEED_INSTALLED','s2c-000001.bin','RUNTIME_VERIFIED'),
          (2,'C2S','SEED_INSTALLED','',19,'','INITIAL_SEED_EXCHANGE','c2s-000001.bin','RUNTIME_VERIFIED'),
          (3,'S2C','INITIAL_SEED_EXCHANGE',1,5,'0x13270','POST_SEED_ACCEPTED','S2C_0002.bin','RUNTIME_VERIFIED')]
    if tx:
        wire=(run/tx['accepted_buffer']).read_bytes()
        (run/'network/C2S_0002.bin').write_bytes(wire)
        write_json(run/'network/C2S_0002.json',{'length':len(wire),'caller_rva':tx.get('caller_rva'),
            'state':'POST_SEED_ACCEPTED','preceding_s2c_sha256':hashlib.sha256(rx).hexdigest(),
            'sha256':hashlib.sha256(wire).hexdigest(),'semantic_contract':'UNKNOWN','credentials':'LOCAL_TEST_ONLY_REDACTED'})
        rows.append((4,'C2S','POST_SEED_ACCEPTED','UNKNOWN',len(wire),'','UNKNOWN','C2S_0002.bin','WIRE_OBSERVED_ONLY'))
    with (run/'protocol-core.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream)
        writer.writerow('sequence_index,direction,state_before,opcode,length,handler,state_after,fixture,confidence'.split(','))
        writer.writerows(rows)
    golden=home/'artifacts/golden/post-seed'/run.name
    golden.mkdir(parents=True,exist_ok=False)
    for source in (run/'network').glob('*00000*.bin'):
        (golden/source.name).write_bytes(source.read_bytes())
    for filename in ('S2C_0002.bin','C2S_0002.bin','C2S_0002.json'):
        source=run/'network'/filename
        if source.exists():(golden/filename).write_bytes(source.read_bytes())
    (golden/'protocol-core.csv').write_bytes((run/'protocol-core.csv').read_bytes())
    write_json(golden/'session.json',{'source_run':str(run),'LOGIN':False,**result})
    return result
