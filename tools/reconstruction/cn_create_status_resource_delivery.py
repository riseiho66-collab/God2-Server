"""Join pinned ordinary-create status branches to native SystemMessage data.

File-only PE disassembly and retained decoded resource accounting. No native
loader, client, server, gameplay code, build or tests are executed.
"""
import csv
import hashlib
import io
import json
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView, import_directory

NAME='cn-create-status-resource-01'
ROUND='20261007-cn-create-status-resource'
FUNCTIONS=('00428c80','0042c3a0','004231b0','0047dcc0','0047f530','0043d280','00567b50',
           '0076c3bf','00790027')

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior evidence')
    image=CN.parent/'XJZ-CN/God2_opt.exe';raw=image.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as source:
        rows={r['address'].lower():r for r in csv.DictReader(source,delimiter='\t')}
    files=[];functions=[];instructions={}
    def save(rel,data,original=None):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':original,'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']))
        ins=list(md.disasm(code,va));instructions[entry]=ins
        save('native/'+entry+'.bin',code,str(image)+':VA'+entry)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),str(RECOVERY/row['file']))
        save('native/'+entry+'.asm',('\n'.join(
            f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode())
        functions.append({'entry':entry,'metadata_bytes':len(code),
            'method':'METADATA_BOUNDED_LINEAR_DISASSEMBLY_NOT_GLOBAL_CFG_CLOSURE'})
    literal=view.string(0x7ee9a0-ib)
    if literal!='SystemMessage':raise RuntimeError('Section literal changed')
    save('native/SystemMessage-007ee9a0.bin',(literal+'\0').encode())
    resource_dir=base/'cn-directory-display-fields-01/native/resources'
    receipt_raw=(resource_dir/'account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    packed_path=CN.parent/'XJZ-CN/Data2/Patch/Comm/message.csvZ';packed=packed_path.read_bytes()
    plain=(resource_dir/'message.csv').read_bytes()
    sha=lambda data:hashlib.sha256(data).hexdigest()
    if receipt['client_sha256']!=PIN or receipt['asset']['codepage']!=936:
        raise RuntimeError('Retained resource scope differs')
    if sha(packed)!=receipt['asset']['sha256'] or sha(plain)!=receipt['asset']['decoded_sha256']:
        raise RuntimeError('Current packed or retained decoded resource differs')
    save('resources/message.csvZ',packed,str(packed_path))
    save('resources/message.csv',plain,str(resource_dir/'message.csv'))
    save('resources/prior-account-phase-evidence.json',receipt_raw,str(resource_dir/'account-phase-evidence.json'))
    csv_rows=list(csv.reader(io.StringIO(plain.decode('cp936'))))
    start=next(n for n,row in enumerate(csv_rows) if row and row[0]=='SystemMessage')
    declared=int(csv_rows[start][1]);section=csv_rows[start+1:start+1+declared]
    messages={}
    for n,row in enumerate(section,start+2):
        ident=int(row[0])
        if ident in messages:raise RuntimeError('Duplicate SystemMessage ID')
        messages[ident]={'csv_row':n,'id':ident,'metadata_column_1':row[1],
            'text_columns':[row[2+i] if len(row)>2+i else '' for i in range(3)],
            'raw_cells':row,'encoded_cells_hex':[cell.encode('cp936').hex() for cell in row]}
    selected={str(i):messages[i] for i in (48,49,50,201,231)}
    dump('system-message-selected-rows.json',selected)
    # Primary alias/argument context, not inferred from the C decompiler alone.
    accesses=[]
    for entry in ('00428c80','0042c3a0','0047f530','004231b0'):
        ins=instructions[entry]
        for n,i in enumerate(ins):
            match=any(op.type==capstone.x86_const.X86_OP_MEM and op.mem.disp in
                      (0xb2f58,0xb2f5c) for op in i.operands)
            literal_ref=any(op.type==capstone.x86_const.X86_OP_IMM and op.imm==0x7ee9a0 for op in i.operands)
            if match or literal_ref:
                accesses.append({'entry':entry,'site':f'{i.address:08x}',
                    'context':[{'site':f'{j.address:08x}','bytes':j.bytes.hex(),
                        'mnemonic':j.mnemonic,'operand':j.op_str} for j in ins[max(0,n-5):n+11]]})
    dump('system-message-primary-loader-accesses.json',accesses)
    allocations=[]
    imports=import_directory(pe,raw)
    for i in instructions['00790027']:
        if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==capstone.x86_const.X86_OP_MEM:
            slot=i.operands[0].mem.disp
            bindings=[b for b in imports['bindings'] if int(b['iat_va'],16)==slot]
            allocations.append({'site':f'{i.address:08x}','bytes':i.bytes.hex(),'operand':i.op_str,
                'declared_bindings':bindings,'loaded_binding_observed':False})
    dump('zero-initialized-table-allocation.json',{'wrapper':'0076C3BF ->00790027',
        'primary_import_calls':allocations,'loaded_execution_observed':False})
    dump('ordinary-create-status-consumer.json',{
        'wire_record_bytes':23,'status_payload_offset':0,'status_width_bits':16,
        'message_selector_payload_offset':20,'selector_mask':'7f','accepted_selector_domain':[0,1,2],
        'lookup':'table+16*(status-1)+4+4*selector; status<=signed16 loaded maximum and status!=0',
        'loader':'SystemMessage row ID is one-based; byte metadata then three optional NUL string pointers',
        'empty_or_absent_text_column':'Loader leaves zero pointer; waiter dereferences returned pointer without fallback',
        'status0':'0043D350 ->0043D459: sends18 then waits18; not finished creation',
        'status49':'0043D369/36C: exact49, optional native message, Sleep3000, retains UI branch without0203',
        'status48_resource_text_only':'Character count reached maximum; actual maximum/rule unproven',
        'status50_resource_text_only':'Name cannot use whitespace; exact whitespace/name rule unproven',
        'other_nonzero':'0043D3CB message ->live world flag check ->0203/account0A/recovery',
        'local_network_timeout':'0047DD8E..0047DDD5 returnsC9 after>=30000ms; not observed S2C201',
        'disconnected_local_return':'0047DCD0 EAX1; not observed S2C1',
        'full_server_name_equivalence_or_transaction_recovered':False,
        'all_upstream_states_and_exception_continuations_recovered':False})
    for rel in ('src/cn/protocol/CnCharacterCreateStatus.h',
                'tools/reconstruction/cn_create_status_resource_delivery.py',
                'docs/research/cn-create-status-resource-20261007.md'):
        save('source/'+rel,(ROOT/rel).read_bytes(),str(ROOT/rel))
    findings={'round':ROUND,'native_sha256':PIN,'functions':functions,
        'previous_goal_turn_classification':'progress: retained25 close producer contexts, qualified0203 and31-specific create continuation',
        'native_resource':{'packed_sha256':sha(packed),'decoded_sha256':sha(plain),'codepage':936,
            'current_packed_matches_retained_receipt':True,'decoded_is_retained_source_not_live_loader_observation':True},
        'system_message_declared_rows':declared,'selected_message_ids':[48,49,50,201,231],
        'name_collision_status':49,'name_collision_available_text_selectors':[
            i for i,text in enumerate(selected['49']['text_columns']) if text],
        'new_read_only_create_status_views':1,'new_opcode_values':0,
        'new_phase_opcode_source_bindings':0,'source_owner_chains_added':0,
        'new_complete_bidirectional_routes':0,'levels_changed':False,
        'remaining':['Native17 common name equivalence/uniqueness, slot availability, atomic creation and operation/replay owners remain open; resource text is not server rule recovery.',
          'Full source-issued02 opaque bytes,18 second payload byte,03 payload and real operation/phase ingress are missing; no native reply generator or close handler installed.',
          'Other SystemMessage statuses/columns and all phase/state/variant producers/consumers are not exhausted; global route denominator remains open.'],
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False}
    dump('findings.json',findings);dump('native-source-manifest.json',{'files':files,'native_sha256':PIN})
    print(json.dumps({k:findings[k] for k in ('round','system_message_declared_rows',
        'selected_message_ids','name_collision_status','name_collision_available_text_selectors',
        'new_read_only_create_status_views','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
