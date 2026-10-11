"""Bounded direct-transfer/pointer scan and native close-call argument inventory.

Static file/PE disassembly only. Raw opcode/pointer matches are candidates,
never proof of indirect reachability exhaustion or gameplay completion.
"""
import csv
from collections import Counter
import hashlib
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView

NAME='cn-close-producer-variants-01'
ROUND='20261007-cn-close-producer-variants'

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require new before snapshot; preserve prior evidence')
    image=CN.parent/'XJZ-CN/God2_opt.exe';raw=image.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    retained_path=base/'cn-wrapper-route-frontier-05/upstream/transfer-candidates.json'
    retained=[r for r in json.loads(retained_path.read_text(encoding='utf-8')) if r['target']=='00480b10']
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as f:
        metadata={r['address'].lower():r for r in csv.DictReader(f,delimiter='\t')}
    files=[]
    def save(rel,data,original=None):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':original,'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,indent=2)+'\n').encode())
    save('retained-provenance/transfer-candidates.json',retained_path.read_bytes(),str(retained_path))
    direct=[];absolute=[];sections=[]
    for section in pe.sections:
        off=section.PointerToRawData;size=section.SizeOfRawData
        if off+size>len(raw):raise RuntimeError('Section exceeds file backing')
        data=raw[off:off+size];name=section.Name.rstrip(b'\0').decode('ascii')
        sections.append({'name':name,'rva':f'{section.VirtualAddress:08x}','raw_offset':off,
            'raw_bytes':size,'executable':bool(section.Characteristics&0x20000000),
            'sha256':hashlib.sha256(data).hexdigest()})
        if section.Characteristics&0x20000000:
            for opcode in (0xe8,0xe9):
                pos=data.find(bytes([opcode]))
                while pos>=0:
                    if pos+5<=size:
                        va=ib+section.VirtualAddress+pos
                        if va+5+struct.unpack_from('<i',data,pos+1)[0]==0x480b10:
                            direct.append({'site':f'{va:08x}','opcode':f'{opcode:02x}',
                                'section':name,'bytes':data[pos:pos+5].hex(),
                                'instruction_alignment_proven_by_raw_scan':False})
                    pos=data.find(bytes([opcode]),pos+1)
        pos=data.find(struct.pack('<I',0x480b10))
        while pos>=0:
            absolute.append({'va':f'{ib+section.VirtualAddress+pos:08x}','section':name,
                             'pointer_or_instruction_semantics_proven':False})
            pos=data.find(struct.pack('<I',0x480b10),pos+1)
    dump('raw-relative-transfer-candidates.json',direct)
    dump('raw-absolute-pointer-candidates.json',absolute)
    dump('scanned-file-sections.json',sections)
    entries=sorted({r['nearest_recovery_anchor'] for r in retained}|{'00480b10'})
    instructions={};functions=[]
    for entry in entries:
        row=metadata[entry];addr=int(entry,16);code=view.read(addr-ib,int(row['bytes']))
        ins=list(md.disasm(code,addr));instructions[entry]=ins
        save('native/'+entry+'.bin',code,str(image)+':VA'+entry)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),str(RECOVERY/row['file']))
        save('native/'+entry+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode())
        functions.append({'entry':entry,'metadata_bytes':len(code),
            'method':'METADATA_BOUNDED_LINEAR_DISASSEMBLY_NOT_GLOBAL_CFG_CLOSURE'})
    contexts=[]
    for row in retained:
        ins=instructions[row['nearest_recovery_anchor']];site=int(row['callsite'],16)
        matches=[n for n,i in enumerate(ins) if i.address==site and i.mnemonic=='call' and
                 len(i.operands)==1 and i.operands[0].type==capstone.x86_const.X86_OP_IMM and i.operands[0].imm==0x480b10]
        if len(matches)!=1:raise RuntimeError('Retained site lacks unique metadata-aligned direct call')
        n=matches[0];pushes=[]
        for i in reversed(ins[max(0,n-12):n]):
            if i.mnemonic=='push':
                op=i.operands[0]
                pushes.append({'site':f'{i.address:08x}','bytes':i.bytes.hex(),'operand':i.op_str,
                    'immediate':op.imm if op.type==capstone.x86_const.X86_OP_IMM else None})
                if len(pushes)==3:break
            elif i.mnemonic in ('call','ret') or (i.mnemonic in ('add','sub') and i.op_str.startswith('esp,')):
                break
        if len(pushes)!=3:raise RuntimeError('Explicit arguments cross an unqualified stack boundary')
        registers=[i for i in ins[max(0,n-24):n] if i.mnemonic=='mov' and i.op_str.startswith('ecx,')]
        ecx=registers[-1] if registers else None
        record={'site':row['callsite'],'function':row['nearest_recovery_anchor'],
            'primary_call_bytes':ins[n].bytes.hex(),'explicit_argument_pushes_first_to_third':pushes,
            'opcode':pushes[0]['immediate'],'payload_control_byte':pushes[1]['immediate'],
            'wait_flag_immediate':pushes[2]['immediate'],
            'wait_flag_register_gate':None,
            'last_local_ecx_assignment':None if ecx is None else {'site':f'{ecx.address:08x}','operand':ecx.op_str},
            'primary_context':[{'site':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operand':i.op_str}
                               for i in ins[max(0,n-24):n+12]],
            'whole_upstream_state_and_exception_closure_proven':False,'complete_route':False}
        if pushes[2]['operand']=='edi' and row['callsite']=='00449813':
            record['wait_flag_register_gate']={'entry':'004497F0','argument_to_EDI':'004497F5',
                'cmp_EDI_1':'004497FA','jne_skip_block':'004497FD ->0044982B',
                'conditional_value':1,'register_not_written_in_this_block':True}
        contexts.append(record)
    dump('native-close-producer-contexts.json',contexts)
    # Specific phase split, preserving previously known ordinary create shape.
    dump('ordinary-create-close-split.json',{
        'entry':'0043D280','native_create_send':'0043D319 ->0047E900 emits17',
        'native_status_wait':'0043D334 ->0047DCC0; low16 return retained inEBX',
        'status0':'0043D34D/350 ->0043D459: C2S18/location waiter; successful location branch later0200',
        'status31':'0043D369/36C keeps31-specific branch and Sleep3000, no0203 at this branch',
        'other_nonzero':'0043D36C ->0043D3CB ->world flag check0043D405;0203 at0043D414 when live',
        'follow_on_account_control':'0043D427 ->0047F310(name,1), then0043D430 ->00440CA0(2)',
        'official_status31_business_meaning':None,'server_permission_or_reply_issuance_proven':False})
    for rel in ['src/cn/protocol/CnPreWorldCloseControl.h',
                'tools/reconstruction/cn_close_producer_variants_delivery.py',
                'docs/research/cn-close-producer-variants-20261007.md']:
        save('source/'+rel,(ROOT/rel).read_bytes(),str(ROOT/rel))
    retained_sites={r['callsite'] for r in retained};raw_sites={r['site'] for r in direct}
    findings={'round':ROUND,'native_sha256':PIN,'functions':functions,
        'previous_goal_turn_classification':'progress: added native03 record preservation/current-ticket/terminal write drain source and primary world03 return8 caller evidence',
        'retained_direct_call_contexts':len(contexts),'raw_executable_relative_matches':len(direct),
        'raw_matches_outside_retained':sorted(raw_sites-retained_sites),
        'retained_sites_absent_from_raw_matches':sorted(retained_sites-raw_sites),
        'absolute_u32_pointer_candidates':len(absolute),
        'control_byte_callsite_counts':dict(sorted(Counter(str(r['payload_control_byte']) for r in contexts).items())),
        'wait_argument_register_sites':[r['site'] for r in contexts if r['wait_flag_immediate'] is None],
        'new_read_only_close_forms':['0203'],'qualified_read_only_close_forms':['0200','0203','0204'],
        'native_direct_opcode_values_added':0,'computed_indirect_callers_exhausted':False,
        'actual_native_close_handlers_added':0,'phase_opcode_source_bindings_added':0,
        'source_owner_chains_added':0,'new_complete_bidirectional_routes':0,
        'remaining':['Native17 status/rule/common create transaction and complete02/18 data must retain31 vs other failure/success branches; no blanket close after every error.',
          'Native0200 has multiple UI/reconnect/abort contexts; control-byte value does not establish official reason/permission or all upstream state variants.',
          'Actual0200/0203/0204 ingress/operation owner, full source-issued03 payload and native19 transaction/02/1E suppliers remain absent.',
          'No raw absolute target references is not proof of no computed/relocated/indirect calls; whole-game directional/phase/state/variant denominator remains open.'],
        'whole_game_completion_percent':None,'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False}
    dump('findings.json',findings)
    dump('native-source-manifest.json',{'files':files,'native_sha256':PIN})
    print(json.dumps({k:findings[k] for k in ['round','retained_direct_call_contexts',
         'raw_executable_relative_matches','control_byte_callsite_counts','wait_argument_register_sites',
         'new_read_only_close_forms','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
