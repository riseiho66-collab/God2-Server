"""Static first-hop inventory for every unclassified WORLD S2C dispatch entry.

This records direct call edges in bounded dispatch slices only. A call edge is
not a gameplay effect, a causal C2S reply, or a complete packet variant.
"""
import hashlib
import json
from collections import Counter

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
OUT=ROOT/'s2c-unclassified-first-hops-v1.json'
FRONTIER=ROOT/'s2c-world-consumer-frontier-v4.json'
MAX_BYTES=96


def recover():
    frontier=json.loads(FRONTIER.read_text(encoding='utf-8'))
    if frontier['native_sha256']!=PIN:
        raise ValueError('S2C frontier belongs to another native build')
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    rows=[]
    for entry in frontier['entries']:
        if entry['dispatch_class']!='NONDEFAULT' or entry['ledger_classifications']:
            continue
        start=int(entry['world_dispatch_rva'],16)
        instructions=[];direct_calls=[];stop_reason='BOUND_96_BYTES'
        for ins in md.disasm(raw[start:start+MAX_BYTES],BASE+start):
            instructions.append(ins)
            if ins.mnemonic=='call' and len(ins.bytes)==5 and ins.bytes[0]==0xe8:
                direct_calls.append(f'{ins.address+ins.size+int.from_bytes(ins.bytes[1:5],"little",signed=True)-BASE:X}')
            if ins.mnemonic=='jmp' or ins.mnemonic.startswith('ret'):
                stop_reason='FIRST_UNCONDITIONAL_BRANCH_OR_RETURN'
                break
        if not instructions:
            raise ValueError(f'No decodable dispatch entry {entry["opcode"]}')
        end=instructions[-1].address+instructions[-1].size-BASE
        if end>start+MAX_BYTES:
            raise ValueError(f'Dispatch slice escaped bound {entry["opcode"]}')
        body=raw[start:end]
        rows.append({
            'opcode':entry['opcode'],'logical_size':entry['logical_size'],
            'length_kind':entry['length_kind'],'dispatch_rva':f'{start:X}',
            'end_rva_exclusive':f'{end:X}','stop_reason':stop_reason,
            'direct_call_target_rvas':direct_calls,
            'sha256':hashlib.sha256(body).hexdigest(),'bytes_hex':body.hex(),
            'instructions':[{'rva':f'{ins.address-BASE:X}',
                             'instruction':f'{ins.mnemonic} {ins.op_str}'} for ins in instructions],
        })
    if len(rows)!=frontier['counts']['s2c_nondefault_without_route_ledger_classification']:
        raise ValueError('Unclassified frontier count changed')
    call_counts=Counter(t for row in rows for t in row['direct_call_target_rvas'])
    return {'format':'god2-current-native-unclassified-s2c-first-hops-v1',
            'native_image':IMAGE,'native_sha256':PIN,
            'frontier':'s2c-world-consumer-frontier-v4.json',
            'frontier_sha256':hashlib.sha256(FRONTIER.read_bytes()).hexdigest(),
            'method':'PINNED_BOUNDED_WORLD_DISPATCH_FIRST_HOP_DISASSEMBLY',
            'entry_count':len(rows),
            'entries_with_direct_call':sum(bool(row['direct_call_target_rvas']) for row in rows),
            'distinct_direct_call_targets':len(call_counts),
            'entries_without_direct_call':[row['opcode'] for row in rows if not row['direct_call_target_rvas']],
            'shared_direct_call_targets':[
                {'target_rva':target,'call_edges':count} for target,count in sorted(call_counts.items()) if count>1],
            'limits':['Direct E8 edges in a bounded dispatch slice are an index, not verified gameplay effects.',
                      'Indirect calls, deeper callees, other-state dispatch, variants and C2S pairing remain open.',
                      'A 96-byte bound that ends without a terminator is explicitly marked BOUND_96_BYTES.'],
            'builds_tests_client_execution_deployment':False,'entries':rows}


def main():
    if OUT.exists():raise FileExistsError('Preserve prior first-hop evidence')
    value=recover()
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'entry_count':value['entry_count'],
                      'with_call':value['entries_with_direct_call'],
                      'distinct_targets':value['distinct_direct_call_targets'],
                      'without_call':len(value['entries_without_direct_call']),
                      'shared_targets':len(value['shared_direct_call_targets'])}))


if __name__=='__main__':main()
