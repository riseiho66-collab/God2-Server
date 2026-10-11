"""Primary file-only exception/patch frontier for CN19's unresolved1E tail.

No native/DLL/instruction execution, image repair or gameplay testing. IAT
declarations, byte candidates, bounded CFG alignment and loaded state differ.
"""
import bisect
from collections import Counter
import csv
import hashlib
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView, import_directory
from .cn_summary_world_lineage_delivery import trace

NAME='cn-delete-exception-frontier-01'
ROUND='20261007-cn-delete-exception-frontier'
APIS={'SetUnhandledExceptionFilter','UnhandledExceptionFilter','VirtualProtect',
      'FlushInstructionCache','RtlUnwind','RaiseException'}
FUNCTIONS=('00401000','00401170','004011f0','00401260','004012e0',
    '004016f0','004017c0','005419c0','00541a10','00541a20','00541a30','00541a40',
    '00748df5','0074a1cb','0074a361','0074a370','0074f0f0','007538bc','0075a8dc')
PEER=ROOT.parent/'God2/output/web-prototype'


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve prior artifacts')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('Pinned CN input changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows=list(csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t'))
    by_entry={r['address'].lower():r for r in rows}
    spans=sorted((int(r['address'],16),int(r['bytes']),r) for r in rows)
    starts=[r[0] for r in spans];files=[];decoded={};captured={}
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):
        save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),
             'static bounded source recovery; no native execution')
    def capture(entry):
        if entry in captured:return
        row=by_entry[entry];va=int(entry,16);size=int(row['bytes']);code=view.read(va-ib,size)
        save('native/functions/'+entry+'.bin',code,str(exe)+':VA'+entry)
        save('native/functions/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),RECOVERY/row['file'])
        try:
            cfg,asm,instructions=trace(md,code,va,va+size,{})
            decoded[entry]=instructions
            dump('native/functions/'+entry+'-cfg.json',cfg)
            save('native/functions/'+entry+'.asm',asm,'entry-rooted bounded CFG bytes, not execution')
            status={'instructions':len(instructions),'open_edges':len(cfg['open_edges'])}
        except ValueError as error:
            decoded[entry]={};status={'bounded_cfg_decode_error':str(error),'complete_body':False}
        captured[entry]={'metadata':row,'code_sha256':hashlib.sha256(code).hexdigest(),**status}
    def owner(va):
        n=bisect.bisect_right(starts,va)-1
        if n>=0 and va<spans[n][0]+spans[n][1]:return f'{spans[n][0]:08x}'
        return None
    for entry in FUNCTIONS:capture(entry)
    # Preserve exact primary import directory chains, not partial pefile guesses.
    imports=import_directory(pe,raw)
    selected=[x for x in imports['bindings'] if x.get('name') in APIS]
    dump('imports.json',imports)
    references=[]
    for binding in selected:
        iat=int(binding['iat_va'],16)
        for prefix in (b'\xff\x15',b'\xff\x25'):
            pattern=prefix+struct.pack('<I',iat)
            for section_index,s in enumerate(pe.sections):
                data=raw[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData];pos=0
                while True:
                    pos=data.find(pattern,pos)
                    if pos<0:break
                    va=ib+s.VirtualAddress+pos;entry=owner(va)
                    if entry:capture(entry)
                    ins=decoded.get(entry,{}).get(va)
                    aligned=bool(ins and bytes(ins.bytes)==pattern)
                    references.append({'api':binding['name'],'iat_va':binding['iat_va'],
                        'site_va':f'{va:08x}','section_index':section_index,
                        'section_executable':bool(s.Characteristics&0x20000000),
                        'bytes':pattern.hex(),'metadata_owner':entry,
                        'entry_rooted_bounded_cfg_instruction':aligned,
                        'whole_program_reachability_proven':False})
                    pos+=1
    dump('declared-api-reference-candidates.json',references)
    save('native/pe-headers.bin',raw[:pe.OPTIONAL_HEADER.SizeOfHeaders],exe)
    tlsdir=pe.OPTIONAL_HEADER.DATA_DIRECTORY[9]
    tls=view.read(tlsdir.VirtualAddress,24);values=struct.unpack('<6I',tls)
    callback_va=values[3];callback_rows=[];callback_raw=bytearray()
    for index in range(1024):
        data=view.read(callback_va-ib+index*4,4);callback_raw.extend(data)
        value=struct.unpack('<I',data)[0]
        if not value:break
        callback_rows.append(f'{value:08x}')
    else:raise RuntimeError('Bounded TLS table lacks terminator')
    save('native/tls-directory.bin',tls,str(exe)+':TLS directory')
    save('native/tls-callback-table.bin',bytes(callback_raw),str(exe)+':TLS callbacks')
    dump('pe-exception-registration-context.json',{
        'image_base':f'{ib:08x}','entry_va':f'{ib+pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}',
        'exception_directory':{'rva':pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].VirtualAddress,
                              'size':pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].Size},
        'load_config_directory':{'rva':pe.OPTIONAL_HEADER.DATA_DIRECTORY[10].VirtualAddress,
                                'size':pe.OPTIONAL_HEADER.DATA_DIRECTORY[10].Size},
        'dll_characteristics':f'{pe.OPTIONAL_HEADER.DllCharacteristics:04x}',
        'tls_directory_rva':f'{tlsdir.VirtualAddress:08x}',
        'tls_callbacks_va':f'{callback_va:08x}','file_callbacks':callback_rows,
        'terminated_at_index':index,'selected_declared_imports':selected,
        'limitations':'File TLS terminator/missing directory/import-name does not prove absence of loaded or dynamically registered SEH/VEH or code mutation.'})
    # Actual UI SEH prologue points at this cookie-checking EH adapter.
    # Span ends at its external handler jump; no guessed neighboring function.
    prologue=view.read(0x446bd0-ib,0x2d);handler=view.read(0x7c7472-ib,0x28)
    save('native/ui-seh-prologue.bin',prologue,exe)
    save('native/ui-seh-adapter.bin',handler,exe)
    cfg,asm,_=trace(md,handler,0x7c7472,0x7c749a,{})
    dump('native/ui-seh-adapter-cfg.json',cfg);save('native/ui-seh-adapter.asm',asm,exe)
    info=view.read(0x857958-ib,36);fields=struct.unpack('<9I',info)
    unwind=view.read(fields[2]-ib,fields[1]*8)
    save('native/ui-funcinfo.bin',info,exe);save('native/ui-unwind-map.bin',unwind,exe)
    unwind_rows=[{'state':i,'next_state':struct.unpack_from('<i',unwind,i*8)[0],
                 'cleanup_va':f'{struct.unpack_from("<I",unwind,i*8+4)[0]:08x}'} for i in range(fields[1])]
    dump('ui-seh-source-chain.json',{
        'registration':['00446BD5 pushes handler007C7472','00446BF7 installs current record inFS:[0]'],
        'adapter':['007C7481/007C748B ->cookie checker00749104',
                   '007C7490 EAX=00857958','007C7495 ->0074F0F0 ->007538BC'],
        'funcinfo_va':'00857958','funcinfo_fields_hex':[f'{x:08x}' for x in fields],
        'magic':'19930522','max_state':fields[1],'unwind_map_va':f'{fields[2]:08x}',
        'try_block_count':fields[3],'try_block_map_va':f'{fields[4]:08x}',
        'estype_list_va':f'{fields[7]:08x}','eh_flags':fields[8],
        'unwind_entries':unwind_rows,
        'internal_consumer':'007538BC reads FuncInfo+0C/+1C/+20 before0075338F; empty try/ESType and no flag4 do not enter handler search on non-unwinding records. It returns1; unwind cleanup is not resume-EIP repair.',
        'top_level_filter':'0074A361 passes0074A370 to declared SetUnhandledExceptionFilter;0074A370 checksE06D7363/3 arguments/C++magic, otherwise EAX0. No instruction-pointer rewrite found in its bounded body.',
        'scope':'Actual UI local frame/file-declared registration only. Other caller frames, TLS/runtime/dynamic API/translator registrations and loaded code remain open.',
        'native1e_outcome_proven':False})
    dump('bounded-code-patch-context.json',{
        'helpers':['00401170 FlushInstructionCache thenVirtualProtect40 saves old protection',
                   '004011F0 FlushInstructionCache thenrestores saved protection',
                   '004012E0 copies relocated instruction prefix and writes detour through00401610'],
        'bounded_caller':'005419C0 ->00401000 four actual argument pairs',
        'targets':[{'target':'00541A90','replacement':'00541950','resolver':'00541A30','api':'keybd_event'},
                   {'target':'00541AB0','replacement':'00541960','resolver':'00541A40','api':'mouse_event'},
                   {'target':'00541A50','replacement':'00541890','resolver':'00541A10','api':'PostMessageA'},
                   {'target':'00541A70','replacement':'005418F0','resolver':'00541A20','api':'PostMessageW'}],
        'claim':'Code modification capability exists. This bounded caller does not target0047EB5E or recover deletion repair; other pointer/caller/loader mutation paths remain open.'})
    peer_meta=[]
    for rel in ('WEB_SERVER_INTEGRATION.md',
                'reports/client-goal-20261007/native-world-relocation-verification.json',
                'reports/client-goal-20261007/native-world-relocation-source.json'):
        data=(PEER/rel).read_bytes();save('peer/'+rel,data,PEER/rel)
        peer_meta.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    peer_report=json.loads((out/'peer/reports/client-goal-20261007/native-world-relocation-verification.json').read_text(encoding='utf-8'))
    peer_source=json.loads((out/'peer/reports/client-goal-20261007/native-world-relocation-source.json').read_text(encoding='utf-8'))
    dump('peer-handoff-receipt.json',{'snapshots':peer_meta,'reported_native_executed':peer_report['nativeExecuted'],
        'reported_render_ready':peer_report['renderReady'],'reported_gameplay_routes_added':peer_report['gameplayRoutesAdded'],
        'source_pins':peer_source['sourcePins'],'reported_counts':peer_report['sourceAudit'],
        'reported_tests_are_frontend_only':True,'tests_run_by_this_server_task':False,
        'capacity_is_peer_point_in_time_report':peer_report['capacity'],
        'return_qualification':peer_source['returnQualification'],'remaining':peer_report['limits'],
        'web_wire_or_server_endpoint_changes':False,'client_files_modified_by_server_task':False})
    for name,rels in (
        ('cn-delete-completion-lifecycle-01',('post-import-boundary.json','findings.json')),
        ('cn-character-delete-operation-01',('findings.json','operation-source-chain.json'))):
        prior=base/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        for rel in rels:
            data=(prior/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pins[rel]:raise RuntimeError('Retained source changed')
            save('retained-source/'+name+'/'+rel,data,prior/rel)
    dump('native-function-index.json',{'metadata_original':str(RECOVERY/'functions.tsv'),
        'metadata_sha256':hashlib.sha256(metadata).hexdigest(),'functions':captured})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: catalog71 concrete conditional19/common-CAS/02 operation sealed',
        'new_exception_context_functions_retained':len(captured),
        'declared_api_byte_reference_candidates_not_routes':len(references),
        'entry_rooted_api_instruction_references_not_routes':sum(x['entry_rooted_bounded_cfg_instruction'] for x in references),
        'reference_candidates_by_api':dict(Counter(x['api'] for x in references)),
        'file_tls_callbacks':len(callback_rows),'actual_ui_try_block_count':fields[3],
        'actual_ui_unwind_entries_not_routes':fields[1],'scoped_patch_target_pairs_not_packets':4,
        'local_ui_or_bounded_top_filter_skip_repair_found':False,'whole_program_exception_or_loaded_repair_absence_proven':False,
        'native1e_outcome_proven':False,'new_native_phase_source_bindings':0,'new_source_owner_chains':0,
        'new_complete_bidirectional_routes':0,'new_packet_values':0,'native_replies_or_rules_invented':False,
        'web_handoff_retained':True,'remaining':['Continue actual higher-caller/loaded/dynamic exception registrations and code-mutation provenance; local empty catch map/TLS file terminator do not recover complete1E outcome.',
            'Actual native19 permission/online/guild/operation/CAS/replay owner, full02/03 issuer and configured Application hosting remain open.',
            'Web relocation remains static mask publication; actual raster cache/runtime camera/walk integration and CN resources remain open.',
            'All gameplay phase/state/variant/indirect/deferred route denominator remains unknown.'],
        'levels_changed':False,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','new_exception_context_functions_retained',
        'declared_api_byte_reference_candidates_not_routes','entry_rooted_api_instruction_references_not_routes',
        'actual_ui_try_block_count','native1e_outcome_proven','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
