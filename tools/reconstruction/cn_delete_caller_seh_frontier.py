"""Recover primary higher callers, qualified UI switches and CRT startup seeds.

File-only CFG decoding. No native/DLL/emulation/build/test/SQL execution; callback
seeds, code references and EH metadata never become completed gameplay routes.
"""
import bisect
from collections import deque
import csv
import hashlib
import json
import struct
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView

NAME='cn-delete-caller-seh-frontier-01'
ROUND='20261007-cn-delete-caller-seh-frontier'
FUNCTIONS=('0047e960','0043dba0','00446bd0','0044a470','00405a60',
    '00749a75','00749c34','00749e10','007529c0','0078a0e0','0078c88c','0078c8e8')
TABLES={
    '00446bd0':((0x447211,0x448740,6,0x447208,5,'signed WORD-1, then unsigned EAX<=5'),
        (0x4476b1,0x448758,4,0x4476a8,3,'signed WORD then unsigned EAX<=3'),
        (0x4477dd,0x448768,32,0x4477d4,31,'UI+1792DC state then unsigned ECX<=31')),
    '0044a470':((0x44a796,0x44a960,6,0x44a78d,5,'EBX-1 then unsigned EAX<=5'),),
}
SOURCES=('tools/reconstruction/cn_delete_caller_seh_frontier.py',
    'docs/research/cn-delete-caller-seh-frontier-20261007.md',
    'src/cn/protocol/CnCharacterDeleteReply.h')

def digest(raw):return hashlib.sha256(raw).hexdigest()

def decode_cfg(md,code,low,high,switches):
    """Entry-rooted conservative graph; explicit truncation/exception frontiers."""
    pending=deque([low]);instructions={};edges=[];frontier=[];overlap=False
    while pending:
        address=pending.popleft()
        if address in instructions:continue
        if not low<=address<high:
            frontier.append({'address':f'{address:08x}','kind':'outside_file_code_envelope'});continue
        instruction=next(md.disasm(code[address-low:address-low+15],address,count=1),None)
        if instruction is None or address+instruction.size>high:
            frontier.append({'address':f'{address:08x}','kind':'truncated_or_invalid_instruction'});continue
        if any(address<old.address+old.size and old.address<address+instruction.size for old in instructions.values()):
            overlap=True;frontier.append({'address':f'{address:08x}','kind':'conflicting_instruction_entry'});continue
        instructions[address]=instruction
        ins=instruction;nxt=address+ins.size
        if ins.group(capstone.CS_GRP_RET):continue
        if ins.mnemonic in ('int','int3','into','ud2','hlt','iret','iretd','sysenter','sysexit'):
            frontier.append({'address':f'{address:08x}','kind':'exception_or_external_transfer_not_followed'});continue
        targets=[]
        if ins.mnemonic=='jmp':
            if ins.operands[0].type==X86_OP_IMM:targets=[(ins.operands[0].imm&0xffffffff,'direct_jump')]
            elif address in switches:targets=[(target,'qualified_table') for target in switches[address]]
            else:
                frontier.append({'address':f'{address:08x}','kind':'indirect_jump_not_qualified'});continue
        elif ins.mnemonic.startswith(('j','loop')):
            if not ins.operands or ins.operands[0].type!=X86_OP_IMM:
                frontier.append({'address':f'{address:08x}','kind':'conditional_target_unknown'});continue
            targets=[(ins.operands[0].imm&0xffffffff,'conditional'),(nxt,'fallthrough')]
        else:
            if ins.group(capstone.CS_GRP_CALL):
                edges.append({'source':f'{address:08x}','kind':'call_not_followed',
                    'target':f'{ins.operands[0].imm&0xffffffff:08x}' if ins.operands[0].type==X86_OP_IMM else ins.op_str})
            targets=[(nxt,'fallthrough')]
        for target,kind in targets:
            edges.append({'source':f'{address:08x}','kind':kind,'target':f'{target:08x}'});pending.append(target)
    asm=('\n'.join(f'{i.address:08x} {bytes(i.bytes).hex():24} {i.mnemonic:8} {i.op_str}'
        for i in sorted(instructions.values(),key=lambda x:x.address))+'\n').encode()
    return {'entry':f'{low:08x}','end_exclusive':f'{high:08x}',
        'instructions':len(instructions),'instruction_overlap_found':overlap,
        'edges':edges,'open_edges':frontier,'native_execution':False},asm,instructions

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve prior deliveries')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if digest(raw)!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows=list(csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t'))
    entries={r['address'].lower():r for r in rows}
    spans=sorted((int(r['address'],16),int(r['bytes']),r) for r in rows)
    starts=[x[0] for x in spans];files=[];captured={};decoded={};switch_records=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),'sha256':digest(data)})
    def dump(rel,obj):save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),'file-only bounded primary source recovery')
    def owner(va):
        n=bisect.bisect_right(starts,va)-1
        return spans[n][2]['address'].lower() if n>=0 and va<spans[n][0]+spans[n][1] else None
    def capture(entry):
        if entry in captured:return
        row=entries[entry];lo=int(entry,16);hi=lo+int(row['bytes']);code=view.read(lo-ib,hi-lo)
        save('native/functions/'+entry+'.bin',code,str(exe)+':VA'+entry)
        save('native/functions/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),RECOVERY/row['file'])
        initial,initial_asm,initial_ins=decode_cfg(md,code,lo,hi,{})
        switches={}
        for site,table,count,guard,bound,description in TABLES.get(entry,()):
            guard_ins=initial_ins.get(guard);dispatch=initial_ins.get(site)
            branch=initial_ins.get(guard+guard_ins.size) if guard_ins else None
            if not guard_ins or guard_ins.mnemonic!='cmp' or len(guard_ins.operands)!=2 or \
               guard_ins.operands[1].type!=X86_OP_IMM or guard_ins.operands[1].imm!=bound or \
               not branch or branch.mnemonic!='ja' or not dispatch or dispatch.mnemonic!='jmp' or \
               dispatch.operands[0].type!=X86_OP_MEM or dispatch.operands[0].mem.scale!=4 or \
               dispatch.operands[0].mem.disp!=table or count!=bound+1:
                raise RuntimeError('Declared switch guard/dispatch not entry-rooted')
            table_raw=view.read(table-ib,count*4);targets=struct.unpack('<'+str(count)+'I',table_raw)
            save(f'native/switches/{site:08x}.bin',table_raw,str(exe)+':table'+f'{table:08x}')
            switches[site]=targets
            switch_records.append({'function':entry,'dispatch':f'{site:08x}','table':f'{table:08x}',
                'guard':f'{guard:08x}','guard_bytes':bytes(guard_ins.bytes).hex(),
                'guard_unsigned_bound':bound,'entries':count,'selector_relation':description,
                'targets':[f'{x:08x}' for x in targets],
                'index26_is_delete_ui':site==0x4477dd and targets[26]==0x448383,
                'whole_program_reachability_proven':False})
        cfg,asm,ins=decode_cfg(md,code,lo,hi,switches);decoded[entry]=ins
        dump('native/functions/'+entry+'-initial-cfg.json',initial)
        dump('native/functions/'+entry+'-cfg.json',cfg)
        save('native/functions/'+entry+'.asm',asm,'entry-rooted bounded graph; calls not followed')
        captured[entry]={'metadata':row,'sha256':digest(code),'initial_instructions':len(initial_ins),
            'expanded_instructions':len(ins),'additional_instruction_sites':len(set(ins)-set(initial_ins)),
            'open_edges':cfg['open_edges'],'instruction_overlap_found':cfg['instruction_overlap_found']}
    for entry in FUNCTIONS:capture(entry)
    # Primary rel32 candidates are separate from rooted instruction alignment.
    targets={0x47e960,0x43dba0,0x446bd0,0x44a470,0x405a60};calls=[]
    for section_index,s in enumerate(pe.sections):
        if not s.Characteristics&0x20000000:continue
        data=raw[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
        for op in (b'\xe8',b'\xe9'):
            pos=0
            while True:
                pos=data.find(op,pos)
                if pos<0:break
                if pos+5<=len(data):
                    va=ib+s.VirtualAddress+pos;target=(va+5+struct.unpack_from('<i',data,pos+1)[0])&0xffffffff
                    if target in targets:
                        entry=owner(va)
                        if entry:capture(entry)
                        ins=decoded.get(entry,{}).get(va)
                        aligned=bool(ins and bytes(ins.bytes)==data[pos:pos+5] and ins.mnemonic in ('call','jmp'))
                        calls.append({'site':f'{va:08x}','target':f'{target:08x}','bytes':data[pos:pos+5].hex(),
                            'metadata_owner':entry,'section':section_index,'entry_rooted_instruction':aligned,
                            'whole_program_reachability_proven':False})
                pos+=1
    dump('primary-caller-reference-candidates.json',calls);dump('qualified-ui-switches.json',switch_records)
    # The higher UI caller has its own concrete GS/C++ registration and FuncInfo.
    adapter=view.read(0x7c76ff-ib,0x28);cfg,asm,_=decode_cfg(md,adapter,0x7c76ff,0x7c7727,{})
    save('native/upper-ui-eh-adapter.bin',adapter,exe);save('native/upper-ui-eh-adapter.asm',asm,exe)
    dump('native/upper-ui-eh-adapter-cfg.json',cfg)
    info=view.read(0x857c2c-ib,36);fields=struct.unpack('<9I',info)
    save('native/upper-ui-funcinfo.bin',info,exe)
    unwind=view.read(fields[2]-ib,fields[1]*8);save('native/upper-ui-unwind.bin',unwind,exe)
    upper={'registration':['0044A475 push007C76FF','0044A498 FS:[0]=current record'],
        'adapter':['007C771D EAX=00857C2C','007C7722 ->0074F0F0'],
        'funcinfo':[f'{x:08x}' for x in fields],'try_blocks':fields[3],'estype_list':fields[7],
        'eh_flags':fields[8],'unwind_entries':[{'state':i,'next_state':struct.unpack_from('<i',unwind,i*8)[0],
            'cleanup':f'{struct.unpack_from("<I",unwind,i*8+4)[0]:08x}'} for i in range(fields[1])],
        'resumption_at_47eb63_supplied':False,'loaded_dynamic_exception_sources_closed':False}
    dump('upper-ui-eh-source-chain.json',upper)
    # Primary SEH4 ScopeTable directly supplies otherwise missing filter/handler roots.
    scope=view.read(0x87ced8-ib,28);values=struct.unpack('<7I',scope)
    save('native/crt-scope4.bin',scope,exe)
    special={}
    for name,lo,hi in (('crt-main-exe-extended',0x749a75,0x749bf1),
        ('crt-exe-filter',values[5],values[6]),('crt-exe-handler',values[6],0x749bf1)):
        code=view.read(lo-ib,hi-lo);cfg,asm,ins=decode_cfg(md,code,lo,hi,{})
        save('native/'+name+'.bin',code,str(exe)+':qualified ScopeTable/branch roots')
        save('native/'+name+'.asm',asm,'bounded static CFG; no execution')
        dump('native/'+name+'-cfg.json',cfg)
        special[name]={'entry':f'{lo:08x}','end':f'{hi:08x}','instructions':len(ins),
            'open_edges':cfg['open_edges'],'root_authority':'primary CRT ScopeTable/actual branch targets',
            'metadata_size_preserved':True}
    dump('crt-main-seh4-source-chain.json',{'prologue':'00749A75 pushes14 and0087CED8 ->00749E10 installs007529C0 and XOR ScopeTable',
        'scope_table':{'header_hex':[f'{x:08x}' for x in values[:4]],'enclosing_level':-2,
            'filter':f'{values[5]:08x}','handler':f'{values[6]:08x}'},
        'filter':'00749B96 loads actual exception code/pointers then calls0078A0E0',
        'negative_filter':'007529C0 negative filter ->disposition0; actual callback/context repair not recovered',
        'positive_filter':'007529C0 positive filter ->unwind/transfer to00749BAA; unmanaged path calls0078A589, not a deletion wrapper resume',
        'signal_callbacks':'0078A0E0 reads actual per-thread action table and can call a nonzero real function; file-only control and default table do not close runtime handlers',
        'bounded_spans':special,'native1e_result_proven':False})
    # CRT initterm ranges are genuine callback roots, not function-metadata guesses.
    initializers=[];seed_targets=set()
    for name,lo,hi,caller in (('cxx',0x7ebf1c,0x7ec258,0x749aec),('c',0x7ec25c,0x7ec284,0x749ac6)):
        code=view.read(lo-ib,hi-lo);values=struct.unpack('<'+str((hi-lo)//4)+'I',code)
        save('native/startup/'+name+'-initializer-table.bin',code,exe)
        for index,target in enumerate(values):
            if target:seed_targets.add(target)
            initializers.append({'kind':name,'index':index,'cell':f'{lo+index*4:08x}',
                'target':f'{target:08x}','nonzero':bool(target),'caller':f'{caller:08x}',
                'exact_metadata_entry':f'{target:08x}' in entries,'metadata_owner':owner(target) if target else None,
                'loaded_callback_execution_observed':False})
    seeds=[];boundaries=sorted(set(starts)|seed_targets)
    for target in sorted(seed_targets):
        sections=[s for s in pe.sections if s.SizeOfRawData and s.VirtualAddress<=target-ib<s.VirtualAddress+s.SizeOfRawData]
        if len(sections)!=1:raise RuntimeError('Initializer root not uniquely file-backed')
        section=sections[0];n=bisect.bisect_right(boundaries,target)
        next_entry=boundaries[n] if n<len(boundaries) else ib+section.VirtualAddress+section.SizeOfRawData
        hi=min(next_entry,target+4096,ib+section.VirtualAddress+section.SizeOfRawData)
        code=view.read(target-ib,hi-target);cfg,asm,ins=decode_cfg(md,code,target,hi,{})
        name=f'{target:08x}';save('native/startup/roots/'+name+'.bin',code,exe)
        save('native/startup/roots/'+name+'.asm',asm,'primary initializer-pointer root; calls not followed')
        dump('native/startup/roots/'+name+'-cfg.json',cfg)
        seeds.append({'entry':name,'end':f'{hi:08x}','envelope_is_static_bound_not_exact_function_size':True,
            'exact_metadata_entry':name in entries,'instructions':len(ins),'open_edges':cfg['open_edges'],
            'calls':[e for e in cfg['edges'] if e['kind']=='call_not_followed'],
            'global_exception_or_code_repair_absence_proven':False})
    dump('crt-startup-callback-index.json',{'rows':initializers,'roots':seeds,
        'native_execution_observed':False,'file_tls_zero_does_not_exhaust_crt_startup':True})
    for name,rels in (('cn-delete-exception-frontier-01',('findings.json','ui-seh-source-chain.json')),
        ('cn-delete-completion-lifecycle-01',('findings.json','post-import-boundary.json')),
        ('shared-taiwan-character-removal-01',('findings.json','delivery.json'))):
        prior=base/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        for rel in rels:
            code=(prior/rel).read_bytes()
            if digest(code)!=pins[rel]:raise RuntimeError('Retained source evidence changed')
            save('retained-source/'+name+'/'+rel,code,prior/rel)
    preserved=[]
    for rel in ('src/core/Application.cpp','src/net/Session.cpp','src/auth/RecoveredAccountLogin.cpp',
        'src/auth/SharedTaiwanCharacterRemoval.cpp','src/cn/auth/SharedCharacterDeleteOperation.cpp'):
        code=(ROOT/rel).read_bytes()
        if code!=(out/'before'/rel).read_bytes():raise RuntimeError('Frozen/existing source changed')
        preserved.append({'path':rel,'byte_identical':True,'sha256':digest(code)})
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: catalog75 explicit TW19 common CAS adapter sealed',
        'native_functions_retained':len(captured),'qualified_ui_switches':len(switch_records),
        'qualified_ui_switch_entries_not_packets':sum(r['entries'] for r in switch_records),
        'additional_entry_rooted_instruction_sites_not_routes':sum(r['additional_instruction_sites'] for r in captured.values()),
        'direct_caller_byte_candidates':len(calls),'entry_rooted_direct_caller_references':sum(r['entry_rooted_instruction'] for r in calls),
        'upper_ui_try_block_count':fields[3],'upper_ui_unwind_entries_not_routes':fields[1],
        'crt_seh4_filter_and_handler_roots':2,'crt_startup_table_entries_not_packets':len(initializers),
        'crt_nonzero_startup_callbacks_not_packets':len(seed_targets),
        'crt_startup_callback_roots_without_exact_metadata_entry':sum(not r['exact_metadata_entry'] for r in seeds),
        'crt_startup_roots_with_open_frontier':sum(bool(r['open_edges']) for r in seeds),
        'crt_startup_root_direct_call_targets':sorted({e['target'] for r in seeds for e in r['calls'] if len(e['target'])==8}),
        'crt_initializers_exhaustively_followed':False,'native1e_outcome_proven':False,
        'whole_program_exception_or_loaded_repair_absence_proven':False,
        'new_packet_values':0,'new_native_phase_source_bindings':0,'new_source_owner_chains':0,
        'new_complete_bidirectional_routes':0,'preserved_existing_sources':preserved,
        'levels_changed':False,'formal_application_hosted':False,'whole_game_route_total':None,
        'whole_game_completion_percent':None,'remaining':[
            'Trace actual CRT initializer callees/indirect callbacks and dynamic exception/code-modification provenance; metadata-missing startup seeds are active roots, not dead code.',
            'Native1E post-DeleteFileA FIST[EAX] boundary, actual per-thread signal callbacks/context and loaded repair remain unresolved; no decoder8-to-save-success inference.',
            'Actual TW/CN native mutation permission/guild/replay/receipt/full02/03 issuer and formal common source hosting remain open.',
            'Whole-game phase/state/variant/indirect/deferred denominator and actual native/web gameplay remain incomplete.'],
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    doc=ROOT/'docs/research/cn-delete-caller-seh-frontier-20261007.md'
    if doc.exists():raise RuntimeError('Preserve prior research document')
    doc.write_text('# CN deletion higher callers, UI switches and CRT startup roots\n\n'
        'PHASE1 primary file-only research; no native/DLL/emulation/build/test/SQL execution or deployment. Native levels unchanged. Pinned CN SHA256 '+PIN+'.\n\n'
        'Actual rel32 call chain: CRT00749A75 at00749B68 ->00405A60 at00405F25 ->0044A470 at0044A599/0044A84E ->00446BD0 at004483E4 ->0047E960. Separate0043DBA0 at0043DBD4 also calls deletion; no direct caller found in this bounded target census does not prove it is dead or never used indirectly. Byte matches and entry-rooted instruction alignment are separate.\n\n'
        f'Four primary guarded switch tables contain{findings["qualified_ui_switch_entries_not_packets"]} entries. UI state index26 selects00448383 and reaches the deletion call. The expansion adds{findings["additional_entry_rooted_instruction_sites_not_routes"]} entry-rooted instruction sites; these are code coverage, not packet/route counts. Truncation, exception transfers and unqualified jumps remain explicit.\n\n'
        'Higher0044A470 registers007C76FF throughFS:[0]. Adapter usesFuncInfo00857C2C: magic19930522, maxState3, try-count0, ESType0, EHflags1. Three unwind actions are cleanup, not an EIP skip/repair. Prior local UI00857958 and CRT top-level filter evidence are retained unchanged.\n\n'
        'CRT startup has a different SEH4 frame:00749A75 passesScopeTable0087CED8 to00749E10, which installs007529C0 and XORs the table with the actual cookie. Its table names filter00749B96 and handler00749BAA. Filter loads actual exception code/pointers and calls0078A0E0. Negative filter returns disposition0 in the actual handler; positive filter unwinds/transfers to the handler. The unmanaged handler path calls0078A589, not a deletion wrapper resumption. Actual per-thread signal actions can invoke indirect callbacks; their loaded values and context changes are not qualified by file-only decoding. No native1E result or whole-program absence of repair is claimed.\n\n'
        'The original startup metadata span ends before filter/handler/epilogue. Primary ScopeTable pointers and normal branch targets provide additional roots; the bounded recovered spans are retained separately without overwriting metadata size or older snapshots.\n\n'
        f'Before WinMain, __initterm_e consumes the10-entry C range and __initterm the207-entry C++ range: {len(seed_targets)} nonzero distinct callback roots, {findings["crt_startup_callback_roots_without_exact_metadata_entry"]} without an exact functions.tsv entry. A zero file TLS callback is therefore not complete startup coverage. Each actual pointer seed has a primary bounded CFG and open frontier; bounds use next declared entry/seed, section backing and4096-byte budget, not an assumed exact function end. Calls are not followed.\n\n'
        'Next follow those actual initializer callees and indirect/dynamic exception/code-patch registration, particularly the first CRT initializer and referenced helpers. These roots are not new opcodes or completed native gameplay. Existing common CAS/auth/native decoder behavior remains unchanged; only the decoder provenance comment links this new frontier. TW/CN permission/guild/replay/full02/03/hosting and CN1E remain open.\n\n'
        'New owner chains0, phase source bindings0, complete bidirectional routes0. Whole-game denominator and completion percentage remain null.\n',encoding='utf-8')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    dump('native-function-index.json',{'metadata_original':str(RECOVERY/'functions.tsv'),
        'metadata_sha256':digest(metadata),'functions':captured})
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','native_functions_retained',
        'qualified_ui_switches','additional_entry_rooted_instruction_sites_not_routes',
        'crt_nonzero_startup_callbacks_not_packets','crt_startup_callback_roots_without_exact_metadata_entry',
        'new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
