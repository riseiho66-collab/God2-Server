"""Narrow string-table, API-check and preidentified network-slot evidence report."""
import argparse
from pathlib import Path
import json
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM, CS_OP_IMM, CS_OP_REG, CS_AC_WRITE
import pefile
from lab import HOME, sha, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run',default='lab-initializer-01')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    source=HOME/'artifacts/capture_work/host-20260918-1430/output/native-master-02c-after.bin'
    data=source.read_bytes()
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
    instructions=list(md.disasm(data[0x1000:0x170000],0x401000))
    def record(x): return {'va':hex(x.address),'rva':hex(x.address-0x400000),'bytes':x.bytes.hex(),'instruction':x.mnemonic+' '+x.op_str}
    writers=[]; initializer_calls=[]; check_family=[]
    imports=json.loads((HOME/'artifacts/reports/native-wow64-20260919/modules/runtime-import-candidates.json').read_text())
    network={x['slot_va']:x for x in imports if any(e['module']=='ws2_32' for e in x['export_matches'])}
    roots=[]
    for index,x in enumerate(instructions):
        if not x.id: continue
        operands=x.operands
        if any(o.type==CS_OP_MEM and o.mem.disp in (0xb2c60,0xb2c64) and o.access&CS_AC_WRITE for o in operands):
            writers.append(record(x))
        if x.mnemonic=='call' and operands[0].type==CS_OP_IMM and operands[0].imm==0x458ff0:
            initializer_calls.append(record(x))
        for o in operands:
            if o.type==CS_OP_MEM and not o.mem.base and not o.mem.index and o.mem.disp in network:
                roots.append({**record(x),'slot':hex(o.mem.disp),'candidates':network[o.mem.disp]['export_matches'],
                              'status':'STATIC_SLOT_REFERENCE_NOT_RUNTIME_NETWORK_HIT'})
        if x.mnemonic!='mov' or len(operands)!=2 or operands[0].type!=CS_OP_REG or operands[1].type!=CS_OP_MEM:
            continue
        mem=operands[1].mem
        if mem.base or mem.index or not 0x570000<=mem.disp<0x582000: continue
        # Adjacent load/byte-compare/branch candidates only; no purpose inferred.
        following=instructions[index+1:index+3]
        if len(following)!=2 or not all(y.id for y in following): continue
        compare,branch=following
        if (compare.mnemonic=='cmp' and compare.operands[0].type==CS_OP_MEM
            and compare.operands[0].mem.base==operands[0].reg and compare.operands[0].size==1
            and compare.operands[0].mem.disp==0 and compare.operands[1].type==CS_OP_IMM
            and branch.mnemonic.startswith('j')):
            check_family.append({'load':record(x),'compare':record(compare),'branch':record(branch),'slot':hex(mem.disp),
                'expected_byte':compare.operands[1].imm,'purpose':'UNKNOWN'})
    provenance={'image':str(source),'sha256':sha(source),'scope':'Restored candidate image, not certified repaired PE',
                'method':'Capstone linear decoding of .text; candidates require runtime or CFG corroboration'}
    write_json(args.output/'string-table-xrefs.json',{'provenance':provenance,'writers':writers,'initializer_calls':initializer_calls,
        'initializer':{'va':'0x458ff0','status':'STATIC_IDENTIFIED_NOT_RUNTIME_EXECUTED',
            'table_header':'SystemMessage','header_va':'0x58a070','dispatch_call':'0x456682',
            'pointer_store':'0x459012','count_store':'0x459112',
            'file_loader':'0x456130','filename':'UNKNOWN','source_type':'Parsed external table inferred from loader; actual source file not observed',
            'preconditions':['Table loader opened input','Read/parse header succeeds','Header equals SystemMessage','Positive row count for row loop'],
            'runtime_scope':args.run,'runtime_outcome':'Initializer and table-loader entry breakpoints not hit before compatibility failure'}})
    events=json.loads((HOME/'artifacts/probe-runs'/args.run/'events.json').read_text())
    observed=[e for e in events if e.get('event_type') in ('S2_BEFORE_COMPATIBILITY','S3_COMPATIBILITY_BRANCH')]
    write_json(args.output/'api-compat-checks.json',{'provenance':provenance,'static_family':check_family,'runtime':observed,
        'interpretation':'Implementation-byte test; intent and supported compatibility remedy remain unverified'})
    write_json(args.output/'network-root-candidates.json',{'provenance':provenance,'references':roots,'runtime_hits':[]})
    builds=[]
    for name in ('God2.exe','God2-run.exe'):
        path=HOME.parent/'God2'/name
        pe=pefile.PE(str(path)); mapped=pe.get_memory_mapped_image()
        builds.append({'file':str(path),'sha256':sha(path),'entry_rva':hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            'packed_check_region_bytes':mapped[0x5b65d:0x5b667].hex(),
            'same_runtime_check':'UNKNOWN_PACKED_ARTIFACT_NOT_EXECUTED','failure_behavior':'UNKNOWN_UNOBSERVED_BUILD' if name!='God2.exe' else 'OBSERVED_CURRENT_CAPTURE'})
    write_json(args.output/'cross-build-check.json',{'builds':builds,'scope':'Only check-region on-disk comparison; equal packed bytes do not prove equal runtime behavior'})
    blockers=[
        {'id':'B001','location':'0x531e28','condition':'Four controlled tokens','success_path':'Argument parse complete','failure_path':'Argument rejection',
         'evidence':args.run,'status':'RESOLVED_ARGUMENTS_ONLY'},
        {'id':'B002','location':'0x45b662','condition':'First timeGetTime byte must equal 0x83; observed 0xff',
         'success_path':'JE 0x45b69f','failure_path':'0x45b667 sets failure state; current run reaches 0x45b7a4',
         'evidence':args.run,'status':'UNRESOLVED_NO_PATCH'},
        {'id':'B003','location':'object 0x5e053c + count 0xb2c64 / pointer 0xb2c60',
         'condition':'SystemMessage loader 0x458ff0 not reached in monitored window',
         'success_path':'Pointer store 0x459012 and row-count store 0x459112 (static only)',
         'failure_path':'Zero table used by validation error reporting','evidence':args.run,
         'status':'INITIALIZER_NOT_CALLED','scope':'Restored candidate to validation failure, not all possible process paths'},
        {'id':'B004','location':'Window/audio/graphics startup','condition':'Client reaches compatibility check after subsystem activity',
         'success_path':'NOT_FULLY_VALIDATED','failure_path':'No independently established subsystem blocker','evidence':args.run,'status':'PARTIAL_OBSERVATION'},
        {'id':'B005','location':'NetworkInit UNKNOWN','condition':'No monitored Winsock entry observed','success_path':'UNKNOWN','failure_path':'Prior startup failure',
         'evidence':args.run,'status':'NOT_REACHED'}]
    write_json(args.output/'startup-dependencies.json',blockers)
    write_json(args.output/'scoreboard.json',{'native_WOW64':'PRIOR_QUALIFICATION_RETAINED','argument_parser':True,
        'launcher_context_comparison':True,'historical_launcher_equivalence':False,'string_table_initialized':False,
        **{k:False for k in ('startup_stable','WSAStartup','socket','connect','loopback_accept','first_TX','framing','handshake','login','character_screen','select_character','world','heartbeat','movement')},
        'VM_test':'NOT_RUN: Get-VM denied to current account','G03':'NEED_MORE_EVIDENCE','G04':'UNVERIFIED'})
    print(json.dumps({'field_writers':len(writers),'api_check_candidates':len(check_family),'network_slot_references':len(roots),'output':str(args.output)}))


if __name__=='__main__': main()
