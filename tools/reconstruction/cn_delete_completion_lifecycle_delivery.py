"""Recover bounded deletion return/UI/connection-control evidence, without execution."""
import csv
import hashlib
import json
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView
from .cn_summary_world_lineage_delivery import trace

NAME='cn-delete-completion-lifecycle-01'
ROUND='20261007-cn-delete-completion-lifecycle'
FUNCTIONS=('0047e960','00446bd0','00480b10','0047f310','00440ca0',
           '0047f530','0053fee0','0053ff40')

def main():
    out=ROOT/'artifacts/integration/packet-connections-20261006'/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior evidence')
    image=CN.parent/'XJZ-CN/God2_opt.exe';raw=image.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw)
    base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as f:
        rows={r['address'].lower():r for r in csv.DictReader(f,delimiter='\t')}
    files=[];functions=[]
    def save(rel,data,original=None):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':original,'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,indent=2)+'\n').encode())
    for entry in FUNCTIONS:
        row=rows[entry];address=int(entry,16);size=int(row['bytes'])
        code=view.read(address-base,size)
        save('native/'+entry+'.bin',code,str(image)+':VA'+entry)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),str(RECOVERY/row['file']))
        instructions=list(md.disasm(code,address))
        save('native/'+entry+'.asm',('\n'.join(
            f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
            for i in instructions)+'\n').encode())
        functions.append({'entry':entry,'bytes':size,'source_file':row['file'],
            'method':'METADATA_BOUNDED_LINEAR_DISASSEMBLY_NOT_GLOBAL_CLOSURE'})
        if entry in ('0047e960','00480b10','00440ca0'):
            cfg,asm,_=trace(md,code,address,address+size,{})
            dump('native/'+entry+'-cfg.json',cfg)
            save('native/'+entry+'-cfg.asm',asm)
    # The direct CALL return address fixes the next linear instruction start.
    # No invented exception continuation or self-modification repairs it.
    tail=view.read(0x47eb58-base,0x47eb6e-0x47eb58)
    save('native/post-import-return.bin',tail)
    dump('post-import-boundary.json',{'call':'0047eb58','return_address':'0047eb5e',
        'instructions':[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),
                         'mnemonic':i.mnemonic,'operand':i.op_str}
                        for i in md.disasm(tail,0x47eb58)],
        'eax_source_at_fist':'Imported call result; no intervening EAX assignment in file bytes',
        'independent_timeout_entry':'0047ea6d JAE0047eb63',
        'exception_or_loaded_code_modification_observed':False,
        'conclusion':'File bytes fix CALL return to FIST[EAX] at0047EB5E; no recovered skip/repair. Standard API execution, x87 state and complete1E result remain unproven.'})
    # Primary spans supporting the separate local-list and control chain.
    for name,start,end in [('delete-return-status',0x47ebb2,0x47ec67),
                           ('ui-list-compaction-and-close',0x4483e4,0x44849b),
                           ('pre-world-recovery',0x440ca0,0x440d9b)]:
        save('native/'+name+'.bin',view.read(start-base,end-start))
    strings={}
    for va in (0x7f1624,0x7f162c,0x7f1768,0x7ed048):
        rva=va-base;text=bytearray()
        for n in range(512):
            b=view.read(rva+n,1);text.extend(b)
            if b==b'\0':break
        else:raise RuntimeError('Bounded literal is unterminated')
        save(f'native/literal-{va:08x}.bin',bytes(text))
        strings[f'{va:08x}']={'hex':bytes(text).hex(),'ascii':bytes(text[:-1]).decode('ascii')}
    dump('local-file-literals.json',strings)
    outcomes=[
      {'condition':'world object+2CB8==0 at entry','sites':['0047e97b','0047ec52'],'eax':1,'ui_compaction':False},
      {'condition':'S2C02 status WORD==0','sites':['0047ebb2','0047ebbc','0047ec3b'],'eax':0,'ui_compaction':True},
      {'condition':'S2C02 status WORD!=0','sites':['0047ebbe','0047ec09'],'eax':'zero_extend16(object+2CC5)','ui_compaction':False,'message_selector':'object+2CD9 &7F'},
      {'condition':'S2C1E decoder EAX!=0','sites':['0047eaee','0047eaf5','0047ec52'],'eax':1,'ui_compaction':False},
      {'condition':'S2C1E decoder EAX==0','sites':['0047eaf3','0047eb58','0047eb5e'],'eax':None,'ui_compaction':None,'remaining':'File CALL return is FIST[EAX]; exception/modified-code continuation unknown'},
      {'condition':'unsigned elapsed>=30000 while0047D8D0!=0','sites':['0047ea62','0047ea6d','0047eb69','0047eb9f'],'eax':208,'ui_compaction':False}]
    dump('native-return-branches.json',outcomes)
    lifecycle={
      'local_only_compaction':{'entry':'004483e9 tests actual EAX','zero_branch':'004483f1',
         'row_stride':36,'copy_bytes':36,'copies':'following row+2 into current row+2,16+16+4 bytes',
         'count_byte':'summary+0 decremented only if nonzero','selected_ordinal':'UI+1792D4 reset0',
         'common_server_character_or_save_deleted_proven':False},
      'world_control':{'site':'00448475','ecx':'UI+16180 world owner',
         'arguments':[2,4,1],'wrapper':'00480b10','logical_c2s_hex':'0204',
         'payload_size':1,'waiter_opcode':'03','reply_payload_semantics_recovered':False,
         'return_ignored_at_this_ui_site':True},
      'account_control':{'site':'00448488','ecx':'UI+1617C account owner','wrapper':'0047f310',
         'send_flag':1,'c2s_opcode':'0A','payload_bytes':16,'name_source':'UI+58C',
         'retained_owner_source':'cn-account-success-owner-01',
         'new_account_disconnect_discovery':False},
      'other_pre_world_control':{'caller':'00440ca0','condition':'account+2CB8==0 and world+2CB8!=0',
         'arguments':[2,0,1],'logical_c2s_hex':'0200','same_world_control_wrapper':True},
      'scope':'Pre-world deletion/recovery owner only; do not widen to every02/03 caller or gameplay dispatcher.'}
    dump('native-delete-lifecycle.json',lifecycle)
    for rel in ['src/cn/protocol/CnPreWorldCloseControl.h','src/cn/protocol/CnCharacterDeleteReply.h',
                'tools/reconstruction/cn_delete_completion_lifecycle_delivery.py']:
        save('source/'+rel,(ROOT/rel).read_bytes(),str(ROOT/rel))
    findings={'round':ROUND,'native_sha256':PIN,'functions':functions,
        'native_return_branch_records':len(outcomes),'new_read_only_control_views':1,
        'native_delete_ui_list_compaction_qualified':True,
        'qualified_c2s_pre_world_close_forms':['0200','0204'],
        'previous_goal_turn_classification':'progress: bounded import reader and corrected primary IAT chain; latest owner level acknowledgement alone made no implementation progress',
        'post_call_linear_boundary_qualified':True,'complete_1e_wrapper_outcome_proven':False,
        'new_packet_values':0,'gameplay_source_handlers_added':0,'source_owner_chains_added':0,
        'new_complete_bidirectional_routes':0,'whole_game_completion_percent':None,
        'remaining':['Native19 still needs shared offered identity/ownership, actual rules, atomic deletion/save transaction, pending generations and complete native02/1E supplier.',
          '0047EB5E file return boundary is FIST[EAX]; actual exception/code-repair continuation and1E outcome remain unknown.',
          'C2S0200/0204 require authenticated pre-world lifetime ownership, exact03 supplier and formal composition; no in-world semantic extrapolation.',
          'Native create/location/special-create issuers, full source hosting and whole-game phase/state/variant denominator remain open.'],
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False}
    dump('findings.json',findings)
    dump('native-source-manifest.json',{'files':files,'native_sha256':PIN})
    print(json.dumps({'round':ROUND,'native_functions':len(functions),
        'return_branch_records':len(outcomes),'read_only_control_views_added':1,
        'new_complete_bidirectional_routes':0}))

if __name__=='__main__':main()
