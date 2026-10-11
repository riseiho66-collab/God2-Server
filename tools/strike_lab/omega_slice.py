"""Evidence-bounded SystemMessage predecessor and network-thunk analysis."""
import argparse
from collections import deque
import json
from pathlib import Path
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
import networkx as nx
from lab import HOME, sha, write_json
from omega_assets import decode_csvz, validate_table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run',default='omega-focus-02')
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    source=HOME/'artifacts/capture_work/host-20260918-1430/output/native-master-02c-after.bin'
    image=source.read_bytes(); md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
    def text(va): return image[va-0x400000:].split(b'\0',1)[0].decode('ascii',errors='backslashreplace')
    def dis(start,end): return list(md.disasm(image[start-0x400000:end-0x400000],start))
    def item(i): return {'va':hex(i.address),'rva':hex(i.address-0x400000),'bytes':i.bytes.hex(),'instruction':i.mnemonic+' '+i.op_str}
    provenance={'image':str(source),'sha256':sha(source),'run':args.run,
        'native_log':str(HOME/'artifacts/capture_work/host-20260918-1430/output'/f'{args.run}-native.log')}
    provenance['native_sha256']=sha(provenance['native_log'])
    code=dis(0x456130,0x4570d6); graph=nx.DiGraph(); known={i.address for i in code}
    for i in code:
        graph.add_node(i.address); following=i.address+i.size
        if i.mnemonic.startswith('ret'): continue
        if i.mnemonic.startswith('j'):
            if i.operands[0].type==CS_OP_IMM and i.operands[0].imm in known: graph.add_edge(i.address,i.operands[0].imm)
            if i.mnemonic=='jmp': continue
        if following in known: graph.add_edge(i.address,following)
    dom=nx.immediate_dominators(graph,0x456130)
    chain=[]; node=0x456682
    while True:
        chain.append(node)
        if node==0x456130: break
        node=dom[node]
    branch_dominators=[item(i) for i in code if i.address in chain and i.mnemonic.startswith('j')]
    write_json(args.output/'systemmessage-dispatch-slice.json',{'provenance':provenance,
        'caller_chain':['0x40DBF3 -> 0x455780','0x4557CD / 0x4558A0 -> 0x456130','0x456682 -> 0x458FF0'],
        'buffer_flow':['0x402530 opens compressed path+Z, decoder 0x401D20 writes a temporary stream',
            '0x451960 stores opened stream at this+4','0x4519C0 reads metadata line into 512-byte local buffer',
            '0x451A90 reads next line into 4096-byte local buffer','0x451BE0 splits comma-delimited byte fields into this+0x78 + index*0x17C',
            '0x456194 / 0x451AE0 copies field 0 into dispatcher local [ESP+0x18]',
            '0x4561A2 / 0x451B30 parses field 1 into local row count','0x456641..0x456679 case-sensitive compare with SystemMessage',
            '0x456682 passes row count and same object to 0x458FF0'],
        'local_dominator_analysis':{'library':'networkx.immediate_dominators','entry':'0x456130','target':'0x456682',
            'node_count':len(graph),'branch_dominators':branch_dominators,
            'scope':'Intraprocedural instruction CFG; calls modeled as returning; exceptions and OS callbacks are not modeled. Not a global startup dominator proof'},
        'dispatch_disassembly':[item(i) for i in code],
        'return_contract':{'open_failure':'0x456151 not taken -> return 0',
            'metadata_failure':'0x456168 not taken -> close and return 0',
            'EOF':'0x4570C2 closes stream; function returns 1 even if SystemMessage never appeared',
            'caller_failure':'0x4557D6 clears aggregate success; outer 22-file loop continues; 0x40DBFA jumps failure when aggregate is 0'}})
    paths=[]
    for row in range(22):
        for variant,pointer in enumerate(struct.unpack_from('<II',image,0x18987c+row*8)):
            relative='Data2/Patch/comm/'+text(pointer)+'Z'; p=HOME.parent/'God2'/relative
            paths.append({'candidate':relative,'file_exists':p.exists(),'table_row':row,'variant':variant,
            'evidence_rva':['0xdbdd','0xdbf3','0x557a4','0x557be','0x259e'],
                'construction':'cached current directory + \\Data2\\Patch\\ + comm\\ + filename; compressed suffix Z first, unsuffixed text fallback',
                'selection':'variant 1 iff WORD[0x59DFD8]==4 and WORD[0x59DFDA]==2; otherwise variant 0',
                'confidence':'STATIC_CONSTRUCTION; no current runtime attempt to this caller'})
    write_json(args.output/'systemmessage-source-candidates.json',{'provenance':provenance,'candidates':paths,
        'format_strings':{hex(a):text(a) for a in (0x589e50,0x589e38,0x589e24,0x5847d8,0x58236c)},
        'resource_registry':'No resource ID or registry lookup identified in this narrow loader path'})
    original=HOME.parent/'God2/Data2/Patch/Comm/message.csvZ'
    work=HOME/'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/message.csvZ'
    decoded=decode_csvz(original.read_bytes()); validation=validate_table(decoded)
    write_json(args.output/'systemmessage-validation.json',{'original':str(original),'original_sha256':sha(original),
        'working_copy':str(work),'working_sha256':sha(work),'identical':sha(original)==sha(work),
        'wrapper':{'magic':'0516','declared_length':struct.unpack_from('<I',original.read_bytes(),2)[0],
            'payload_offset':7,'byte6':'5a (read but not validated by recovered decoder)','decoder':'0x401D20',
            'parameters':'N=4096 F=18 cursor=4078; flag LSB 1=literal, 0=12-bit offset + low nibble length+3'},
        'validation':validation})
    events=json.loads((HOME/'artifacts/probe-runs'/args.run/'events.json').read_text())
    observed=[e for e in events if e['event_type']!='WINDOW_MESSAGE_ENTRY' or e.get('message_id')==7]
    gates=[
        {'site':'0x40DBD0 -> 0x40DBD5','condition':'Graphics/subsystem call returns','observed':'Call hit; continuation not hit before failure',
         'required':'Normal return then EAX != 0 at 0x40DBD7','source':'Reentrant focus message observed while call is outstanding'},
        {'site':'0x40DBD7','condition':'EAX != 0','observed':'NOT_REACHED','required':'Nonzero subsystem result','source':'0x4322C0'},
        {'site':'0x4557CD','condition':'Reach enumeration of 22 table paths','observed':'NOT_REACHED','required':'0x40DBF3 calls 0x455780','source':'cached cwd and language selector'},
        {'site':'0x456151','condition':'Open returns nonzero','observed':'NOT_REACHED','required':'Original message.csvZ readable or text fallback readable','source':'0x451960 -> 0x402530'},
        {'site':'0x456168','condition':'Metadata read succeeds','observed':'NOT_REACHED','required':'Valid first line and nonzero field 2','source':'0x4519C0'},
        {'site':'0x456183','condition':'Next line read returns 1','observed':'NOT_REACHED','required':'Readable section header','source':'0x451A90'},
        {'site':'0x456679','condition':'Case-sensitive section tag equals SystemMessage','observed':'NOT_REACHED','required':'SystemMessage','source':'field 0; original file section at normalized line 75'},
    ]
    write_json(args.output/'initializer-gates.json',{'provenance':provenance,'gates':gates,
        'EARLIEST_MISSING_SUCCESS_EDGE':'0x40DBD0 call 0x4322C0 -> 0x40DBD5 continuation; within the instrumented predecessor chain',
        'causal_path':['Outstanding 0x4322C0 initialization','WM_SETFOCUS 0x7 -> 0x40E42C',
            '0x40E462 calls 0x45B630 (entry return address 0x40E467)','timeGetTime byte mismatch (same run API_BYTE_CHECK_BRANCH when present; otherwise prior final captures)',
            'failure path 0x45B7A4 before loader call'],
        'timeGetTime_classification':'BLOCKING_ON_OBSERVED_REENTRANT_FOCUS_PATH; not a universal static dominator',
        'same_thread':len({e['tid'] for e in observed})==1,'observations':observed,
        'wm_setfocus_reference':'https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-setfocus'})
    write_json(args.output/'resource-access-differential.json',{'expected':'Data2/Patch/comm/message.csvZ',
        'prior_trace':'lab-equivalent-final-01 CreateFile/ReadFile/resource observations',
        'classification':'MISSING_CALL','attempted':False,'exists_in_both_trees':True,'offline_format_passed':validation['valid'],
        'source_failure':'NOT_ESTABLISHED','evidence':'Loader entry absent and graphics initializer has not returned',
        'coverage_limit':'Prior trace filters some IO to immediate client callers; this is not exhaustive OS IO coverage'})
    roots=json.loads((HOME/'artifacts/reports/strike-lab-final-20260919/network-root-candidates.json').read_text())['references']
    target={int(r['va'],16):r for r in roots}; groups={hex(a):{'thunk':r,'direct_xrefs':[]} for a,r in target.items()}
    md.skipdata=True
    preceding=deque(maxlen=8)
    for i in md.disasm(image[0x1000:0x170000],0x401000):
        if i.id and i.mnemonic in ('call','jmp') and i.operands[0].type==CS_OP_IMM and i.operands[0].imm in target:
            groups[hex(i.operands[0].imm)]['direct_xrefs'].append({**item(i),
                'preceding_linear_context':list(preceding),
                'following_context':[item(x) for x in dis(i.address,i.address+32)]})
        preceding.append(item(i))
    write_json(args.output/'winsock-ref-clusters.json',{'provenance':provenance,'groups':groups,
        'focused_clusters':{'PossibleWSAStartup':['0x411C7D','0x411F45'],
            'PossibleConnect':['0x411E36','0x411FDC'],'PossibleSend':['0x410DEB','0x410EFB','0x412501'],
            'PossibleRecv':['0x410BE0','0x410C1E','0x410C99']},
        'scope':'Only direct call/jmp references to the existing sixteen thunks; indirect callers remain unknown',
        'runtime_candidate_hits':[e for e in events if e['event_type']=='STATIC_NETWORK_CANDIDATE_HIT']})
    write_json(args.output/'startup-success-graph.json',{'observed':['argv accepted (prior captures)','window/audio activity',
        'graphics/subsystem call outstanding','focus callback','validation failure before string-table load'],
        'unreached_expected':['graphics initializer returns success','0x455780 enumerates tables',
        '0x456130 opens/decompresses original message.csvZ','SystemMessage section -> 0x458FF0','nonzero table','network init UNKNOWN placement'],
        'correction':'Do not assume strings precede all window/audio/graphics work; current code starts graphics before table enumeration'})
    print(json.dumps({'output':str(args.output),'validator_passed':validation['valid'],'sections':len(validation['sections']),
                      'network_direct_xrefs':sum(len(g['direct_xrefs']) for g in groups.values())}))


if __name__=='__main__':main()
