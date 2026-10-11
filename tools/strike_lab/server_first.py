"""Initial cleartext seed frame recovered from this GOD2 image only."""
import hashlib
import struct

BASE=0x400000
RANGES=((0x410490,0x4104f6),(0x410570,0x410598),(0x410670,0x41068c),
        (0x410750,0x410774),(0x410a10,0x410a8d),(0x410ab0,0x410ae2),
        (0x410af0,0x410b68),(0x410bc0,0x410cf4),(0x410e20,0x410ec8))


def checksum(data):
    return sum(byte+0x3c for byte in data)&255


def initial_frame(seed=bytes(16)):
    if len(seed)!=16:raise ValueError('Initial handler consumes exactly 16 bytes')
    prefix=struct.pack('<H',len(seed)+3)+seed
    return prefix+bytes([checksum(prefix)])


def zero_seed_response(image):
    table=image[0x184c30:0x185030]
    if len(table)!=1024:raise ValueError('Seed lookup table missing')
    key=bytes(16)+bytes((table[i]+i)&255 for i in range(16,256))
    proof=bytes((key[(table[i]+table[i+1])&255]+table[i])&255 for i in range(16))
    header=struct.pack('<H',19)
    clear=proof+bytes([checksum(header+proof)])
    previous=(-sum(key))&255
    wire=bytearray(header)
    for index,value in enumerate(clear):
        wire.append(((key[index]^value)+previous-3)&255)
        previous=value
    return bytes(wire)


def exchange_result(home,run,events,listener_events,image):
    from lab import write_json
    rx_events=[e for e in events if e.get('event_type')=='API_RETURN' and e.get('api')=='recv' and e.get('matched') and 0<e.get('eax',0)<4097]
    seed_end=next((e['sequence'] for e in events if e.get('event_type')=='INITIAL_HANDSHAKE_RETURN'),float('inf'))
    rx=b''.join((run/'s2c'/f'recv-{e["sequence"]:04}.bin').read_bytes() for e in rx_events if e['sequence']<seed_end
                if (run/'s2c'/f'recv-{e["sequence"]:04}.bin').exists())
    tx_event=next((e for e in events if e.get('accepted_buffer')),None)
    tx=(run/tx_event['accepted_buffer']).read_bytes() if tx_event else b''
    expected=zero_seed_response(image)
    handler=any(e.get('event_type')=='INITIAL_HANDLER_ENTERED' for e in events)
    installed=any(e.get('event_type')=='INITIAL_HANDSHAKE_RETURN' and e.get('eax')==1 and
                  'flags0=0 flags4=1 flags8=1 flagsc=1' in e.get('post_state','') for e in events)
    connected_return=any(e.get('event_type')=='CLIENT_CONNECTION_ROUTINE_RETURN' and e.get('eax')==0 for e in events)
    accepted=rx==initial_frame() and tx==expected and installed and connected_return
    sent=any(e.get('event_type')=='INITIAL_S2C_SENT' for e in listener_events)
    connected=any(e.get('event_type')=='API_RETURN' and e.get('api') in ('connect','WSAConnect') and e.get('matched') and e.get('eax')==0 for e in events)
    result={'CONNECTED':connected,'INITIAL_S2C_SENT':sent,'FIRST_RX':bool(rx_events),
        'INITIAL_HANDLER':handler,'FIRST_TX':bool(tx_event),
        'LAST_ACCEPTED_STATE':'INITIAL_SEED_EXCHANGE' if accepted else 'PENDING_VERIFICATION',
        'NEXT_BLOCKER':'NEXT_POST_SEED_S2C_CONTRACT_UNKNOWN' if accepted else 'INITIAL_EXCHANGE_NOT_VERIFIED',
        'client_response_matches_derived_bytes':tx==expected,'full_login_compatible':False}
    for direction,wire,event in (('s2c',rx,rx_events[0] if rx_events else None),('c2s',tx,tx_event)):
        if not wire:continue
        path=run/'network'/f'{direction}-000001.bin';path.write_bytes(wire)
        write_json(path.with_suffix('.json'),{'direction':direction,'length':len(wire),
            'sha256':hashlib.sha256(wire).hexdigest(),'caller_rva':event.get('caller_rva') if event else None,
            'timestamp':event.get('timestamp') if event else None,'run_id':run.name,
            'preceding_s2c_sha256':hashlib.sha256(initial_frame()).hexdigest() if direction=='c2s' else None,
            'expected_handler':'0x410e80','scope':'initial seed exchange, not login'})
    write_json(run/'C2S_FRAME_V1.json',{'scope':'initial zero-seed response only','length':19,'length_includes_entire_frame':True,
        'header':'uint16 little endian, not transformed','payload':'16 derived seed-proof bytes, no opcode',
        'checksum':'same additive checksum on clear header/payload; transformed with payload',
        'transform':'out[i]=((key[i] XOR clear[i])+previous_clear-3) mod 256; previous starts at -sum(key) mod 256',
        'wire_matches_independent_derivation':tx==expected,'caller_return_rva':'0x10f00'})
    write_json(run/'server-first-result.json',result)
    import json
    spec=run/'S2C_FRAME_V1.json'
    contract=json.loads(spec.read_text(encoding='utf-8'))
    contract['runtime_acceptance']='CLIENT_ACCEPTED_INITIAL_SEED' if accepted else 'NOT_VERIFIED'
    spec.write_text(json.dumps(contract,indent=2),encoding='utf-8')
    if accepted:
        golden=home/'artifacts/golden/handshake'/run.name;golden.mkdir(parents=True,exist_ok=False)
        (golden/'s2c-000001.bin').write_bytes(rx);(golden/'c2s-000001.bin').write_bytes(tx)
        write_json(golden/'session.json',{'scope':'INITIAL_SEED_EXCHANGE_ONLY','source_run':str(run),
            'sequence':['connect 127.0.0.1:2592','s2c-000001.bin','c2s-000001.bin'],**result})
    return result


def write_contract(home,run):
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    from lab import write_json
    source=home/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
    data=source.read_bytes();decoder=Cs(CS_ARCH_X86,CS_MODE_32)
    slices=[{'start':hex(start),'end':hex(end),'sha256':hashlib.sha256(data[start-BASE:end-BASE]).hexdigest(),
        'instructions':[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in decoder.disasm(data[start-BASE:end-BASE],start)]} for start,end in RANGES]
    write_json(run/'InitialRxPath.json',{'source':str(source),'source_sha256':hashlib.sha256(data).hexdigest(),
        'wait':'0x410e20 -> 0x410d20 (select)', 'receive':'0x410bc0 -> recv thunk 0x543d56',
        'wire_buffer':'object+0x1818','received_count':'object+0x2418','wire_length':'object+0x241c',
        'decode':'0x410ab0 -> 0x410a10','decoded_buffer':'object+0xc10','decoded_count':'object+0x1810',
        'initial_handler':'0x410e80 consumes 16 decoded bytes, 0x410570 installs seed',
        'slices':slices})
    write_json(run/'S2C_FRAME_V1.json',{'scope':'Initial cleartext, uncompressed seed frame only',
        'header_size':2,'length_offset':0,'length_width':2,'endian':'little','length_includes_header_and_checksum':True,
        'length_mask':32767,'compression_bit':32768,'rejected_length_at_or_above':3072,
        'checksum':'last byte == sum(each preceding byte + 0x3c) modulo 256',
        'initial_opcode':None,'initial_payload_size':16,'encryption_precondition':'object+8 == 0',
        'seed_values':'16 zero bytes are a lab fixture choice: copied without value comparison; not a production key',
        'byte_classification':[{'offset':0,'length':2,'class':'STRUCTURAL'},{'offset':2,'length':16,'class':'UNKNOWN_ZERO_SAFE'},
                               {'offset':18,'length':1,'class':'DERIVED'}],
        'runtime_acceptance':'PENDING'})
    frame=initial_frame();(run/'network/INITIAL_S2C_0001.bin').write_bytes(frame)
    return data,frame
