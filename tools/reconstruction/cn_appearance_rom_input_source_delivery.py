"""File-only primary ROM input selection/metadata source; no loader execution."""
import csv
import hashlib
import json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT,PIN
from tools.strike_lab.omega_assets import decode_csvz

NAME='cn-appearance-rom-input-source-01'
ROUND='20261007-cn-appearance-rom-input-source'
SOURCES=('src/cn/assets/CnAppearanceRomInputs.h','src/cn/assets/CnAppearanceRomInputs.cpp',
    'src/cn/assets/CnAppearanceResources.h','src/cn/assets/CnAppearanceResources.cpp',
    'src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp',
    'src/cn/assets/CnResourceBytes.h','src/cn/assets/CnResourceBytes.cpp',
    'tools/reconstruction/cn_appearance_rom_input_source_delivery.py',
    'docs/research/cn-appearance-rom-input-source-20261007.md')
FUNCTIONS=('004197e0','00418830','00419110','0045a1d0','0045a060','00417620','0041b590',
    '00488da0','00488480','00487f70')
REMAINING=[
    'Actual native512-slot bank/ACTINDEX/counter/row caches/command10 rewrite/load and action execution/rendering need current source/connection/context qualification; metadata snapshots are not native slots or renderer output.',
    'Actual CSV/ROM profile revision/world binding, authoritative equipment-to-native input/full6F issuer/observer policies and configured Application/native/WS hosting remain missing.',
    'DrvDoll declared-length discrepancy, auxiliary and alternate-key validity/fallback, CF/other/later appearance and complete resource/image/palette/FLC/finalizer behavior remain open.',
    'All TW/CN/native PC/web numeric/gameplay/replay/recovery and exhaustive direction/phase/state/variant/indirect/deferred denominator remain open; levels unchanged; comprehensive tests follow full source connection.',
]
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh source receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));preserved=[]
    for row in before:
        old=(out/row['snapshot']).read_bytes()
        if sha(old)!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in SOURCES and row['path'] not in (
            'docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):
            if old!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen context changed: '+row['path'])
            preserved.append(row)
    row=next(r for r in before if r['path']=='src/cn/assets/CnResourceBytes.cpp')
    old=(out/row['snapshot']).read_bytes();new=(ROOT/row['path']).read_bytes()
    start=b'CnSelectedResource read_cn_preferred_resource('
    a=old[old.index(start):old.index(b'CnSelectedResource read_cn_mbd_resource(',old.index(start))]
    b=new[new.index(start):new.index(b'CnSelectedResource read_cn_rom_resource(',new.index(start))]
    if a!=b:raise RuntimeError('Existing generic resource selector body changed')
    dump('preserved-generic-resource-selector.json',{'sha256':sha(a),'exact_bytes_retained':True,
        'scope':'0045B270 generic selector unchanged; new004197E0-specific selector separate'})
    prior=base/'cn-native-appearance-resource-source-01';manifest_bytes=(prior/'manifest.json').read_bytes();manifest=json.loads(manifest_bytes)
    if not manifest['sealed']:raise RuntimeError('Prior source unsealed')
    pins={r['path']:r['sha256'] for r in manifest['files']}
    save('retained-source/manifest.json',manifest_bytes)
    retained={}
    for rel in ('findings.json','resources/source-files.json','resources/HeroDoll.csvZ.rows.json','resources/Drv.csvZ.rows.json','resources/DrvDoll.csvZ'):
        data=(prior/rel).read_bytes()
        if sha(data)!=pins[rel]:raise RuntimeError('Prior sealed file differs: '+rel)
        retained[rel]=data;save('retained-source/'+Path(rel).name,data)
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    metadata=(recovery/'functions.tsv').read_bytes();rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8').splitlines(),delimiter='\t')}
    envelopes=[]
    for address in FUNCTIONS:
        row=rows[address];declared=int(row['bytes']);size=655 if address=='004197e0' else declared
        path=(recovery/row['file']).resolve()
        if not path.is_relative_to(recovery.resolve()):raise RuntimeError('Recovery outside root')
        source=path.read_bytes();code=view.read(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        decoded=list(md.disasm(code,int(address,16)))
        listing=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in decoded)+'\n').encode()
        for ext,data in (('.bin',code),('.asm',listing),('.c',source)):save('native/'+address+ext,data)
        if address=='004197e0':
            save('native/004197e0-metadata-envelope.bin',code[:declared]);save('native/004197e0-additive-return-tail.bin',code[declared:])
            end=decoded[-1]
            if sum(i.size for i in decoded)!=size or end.address!=0x419a6c or end.mnemonic!='ret' or end.op_str!='8':
                raise RuntimeError('Primary ROM root return window differs')
        envelopes.append({'address':address,'bytes':size,'metadata_declared_bytes':declared,'additive_bytes':size-declared,
            'native_sha256':sha(code),'recovery_source':str(path),'recovery_source_sha256':sha(source),'metadata':row,
            'decoded_bytes':sum(i.size for i in decoded),'native_executed':False,'all_exceptional_or_indirect_paths_closed':False})
    dump('native/function-envelopes.json',{'primary':str(native),'sha256':PIN,'recovery_metadata_sha256':sha(metadata),'ranges':envelopes})
    literals=[]
    for name,va,size in (('rom-suffix',0x7ed41c,2),('open-mode',0x7ed3d8,4)):
        data=view.read(va-pe.OPTIONAL_HEADER.ImageBase,size);save('native/'+name+'.bin',data)
        literals.append({'name':name,'va':f'{va:08x}','bytes':size,'raw_hex':data.hex(),'sha256':sha(data)})
    pe.close();dump('native/literals.json',literals)
    client=native.parent
    # Format research from real CSV references; never invent or instantiate a role.
    hero=json.loads(retained['resources/HeroDoll.csvZ.rows.json']);drivers=json.loads(retained['resources/Drv.csvZ.rows.json'])
    references=[('hero',r) for r in hero[:4]]+[('driver',r) for r in [d for d in drivers if d['filename']][:2]]
    samples=[]
    for number,(kind,row) in enumerate(references):
        directory='RoleDoll' if kind=='hero' else 'Drv'
        original=client/'Data2/Rom'/directory/row['filename']
        candidate=Path(str(original)+'Z') if original.name[-4]=='.' else original
        candidate_bytes=None
        try:candidate_bytes=candidate.read_bytes()
        except OSError:pass # Native candidate fopen failure -> original path.
        if candidate_bytes is not None and candidate_bytes[:2]==b'\x05\x16':selected=candidate;data=candidate_bytes
        else:selected=original;data=original.read_bytes()
        if len(data)>2000000:raise RuntimeError('Research resource snapshot budget exceeded')
        plain=decode_csvz(data,limit=2000000) if data[:2]==b'\x05\x16' else data
        if plain[:8]!=b'IGSROM02' or len(plain)<12:raise RuntimeError('Actual IGSROM02 resource unavailable')
        save(f'resources/sample-{number:02}.encoded',data);save(f'resources/sample-{number:02}.decoded',plain)
        sections=[];at=12;ended=False
        while at<len(plain):
            if len(plain)-at<12:raise RuntimeError('File section header truncated')
            tag=plain[at:at+8];length=int.from_bytes(plain[at+8:at+12],'little');offset=at+12
            if length>len(plain)-offset:raise RuntimeError('File section beyond actual resource')
            section={'header_offset':at,'payload_offset':offset,'tag':tag.decode('ascii'),'bytes':length}
            if tag==b'ACTINDEX' and length>=2:section['native_ACTINDEX_word']=int.from_bytes(plain[offset:offset+2],'little')
            if tag==b'ACT_STEP' and length%10==0:
                references10=[]
                for p in range(offset,offset+length,10):
                    if plain[p]==0:break
                    if plain[p]==10:references10.append({'file_offset':p,'raw_10byte_hex':plain[p:p+10].hex(),
                        'rom_reference_word':int.from_bytes(plain[p+2:p+4],'little'),
                        'action_reference_word':int.from_bytes(plain[p+4:p+6],'little')})
                if references10:section['command10_raw_references']=references10
            sections.append(section);at=offset+length
            if tag==b'FILE_END':ended=True;break
        dump(f'resources/sample-{number:02}.sections.json',sections)
        samples.append({'kind':kind,'CSV_source_line':row['source_line'],'native_row':row['native_row'],
            'CSV_reference':row['filename'],'original_path':str(original),'candidate_path':str(candidate),'selected_path':str(selected),
            'appended_Z':candidate!=original,'encoded_bytes':len(data),'encoded_sha256':sha(data),
            'decoded_bytes':len(plain),'decoded_sha256':sha(plain),'section_count':len(sections),
            'FILE_END_observed':ended,'bytes_after_FILE_END':len(plain)-at,
            'research_sample_is_authenticated_actor_input':False,'native_CPP_parser_or_loader_executed':False})
    dump('resources/referenced-ROM-file-samples.json',samples)
    current_aux=(client/'Data2/Patch/DrvDoll.csvZ').read_bytes()
    if current_aux!=retained['resources/DrvDoll.csvZ']:raise RuntimeError('Actual auxiliary input changed; requalify separately')
    dump('resources/auxiliary-gap-retained.json',{'current_encoded_sha256':sha(current_aux),
        'prior_encoded_bytes_currently_identical':True,'prior_error':'Expansion exceeds declared length',
        'decoder_reexecuted_for_auxiliary':False,'bounds_relaxed':False,'substituted_data':False})
    peer=json.loads((out/'peer-handoff/server-file-source-receipt.json').read_text(encoding='utf-8'))
    ack=json.loads((out/'peer-handoff/server-ACK-sent.json').read_text(encoding='utf-8'))
    if ack['send_tool_result'].get('isError'):raise RuntimeError('Peer ACK failed')
    facts={'round':ROUND,'cn_native_sha256_context':PIN,
        'previous_goal_turn_classification':'progress: actual HeroDoll918/Drv92 rows, original key/ActType/variant source and catalog103 sealed',
        'cn_ROM_specific_file_selectors_added':1,'cn_exact_appearance_SourceRecord_lineages_added':1,
        'cn_immutable_appearance_ROM_input_sources_added':1,'cn_scene_appearance_ROM_preparation_edges_added':2,
        'native_function_envelopes_read':len(envelopes),'native_function_bytes_read':sum(r['bytes'] for r in envelopes),
        'primary_ROM_root_additive_return_window_bytes':62,'actual_referenced_ROM_file_samples_read':len(samples),
        'research_samples_are_authenticated_actor_inputs':False,'actual_native_bank_cache_ACT_execution_recovered':False,
        'auxiliary_resource_recovered':False,'authoritative_equipment_to_appearance_recovered':False,
        'new_packet_values':0,'new_native_phase_source_bindings':0,'new_source_owner_chains':0,
        'new_tw_source_owner_chains':0,'new_complete_bidirectional_routes':0,'whole_game_route_total':None,
        'whole_game_completed_routes':None,'whole_game_completion_percent':None,'formal_application_hosted':False,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'latest_peer_handoff_round':peer['round'],'preserved_contexts':preserved,'remaining':REMAINING}
    dump('findings.json',facts)
    for rel in SOURCES:save('source/'+Path(rel).name,(ROOT/rel).read_bytes())
    dump('source/source-origins.json',[{'path':rel,'snapshot':Path(rel).name,'sha256':sha((ROOT/rel).read_bytes())} for rel in SOURCES])
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_appearance_rom_input_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['web_native_ui_registration_handoff']['new_ACK_read_confirmed']=True
    ledger['web_native_ui_registration_handoff']['ACK_read_confirmation_evidence']=out.relative_to(ROOT).as_posix()+'/peer-handoff/server-file-source-receipt.json'
    ledger['cn_native_appearance_resource_source']['peer_read_confirmed']=True
    ledger['cn_native_appearance_resource_source']['peer_read_confirmation_evidence']=out.relative_to(ROOT).as_posix()+'/peer-handoff/peer-cn-native-appearance-source-read.json'
    ledger['web_native_ui_act_lifecycle_handoff']=dict(peer,new_ACK_sent=True,evidence=out.relative_to(ROOT).as_posix()+'/peer-handoff')
    ledger['dual_client_source_segments'].append({'name':'CN full actual2A/6F ->immutable CSV rows ->original ROM selector and owned file/metadata source',
        'version_scope':'cn-normal-ordinary-appearance-ROM-inputs-only','status':'Exact full source record/profile/rows ->004197E0 .rom/.romz source selection ->actual original bytes and metadata; native512-slot bank/cache/ACT execution/current context/issuer/world hosting open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},
        'source_owner_chains_added':0,'tw_source_owner_chains_added':0,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'cn_immutable_appearance_ROM_input_sources_added':1,
        'cn_scene_appearance_ROM_preparation_edges_added':2,'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Recover actual native ROM ACTINDEX/command10/0041B590 references and512-slot bank/current context/cache/counter input qualification; bind retained full2A/6F +actual immutable CSV/ROM profile to the same connection/world/revision before publication. Native execution/rendering/auxiliary/alternate/equipment/full6F issuer/observer policy and formal providers/hosting, all gameplay/numeric/denominator remain open. Levels unchanged; PHASE1 file-only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN full appearance input ->actual selected ROM file source ('+ROUND+')\n\n'
        'Exact full parsed2A/ordinary6F and immutable CSV profile retained ->native004197E0 filename/probe/fallback selection ->four original part inputs/optional actual driver input ->owned source bytes/existing ROM metadata. New ROM-specific selector1/exact SourceRecord lineage1/immutable ROM input source1/scene preparation edges2; no native slot/cache/ACT/rendering/authority success. Six actual CSV-referenced format samples saved, not authenticated actors. Native004197E0 TSV593-byte envelope retains an additive62-byte return tail to00419A6C ret8; old sealed sources unchanged. Auxiliary bounds gap and all bank/context/revision/equipment/full6F/observer/host/gameplay/denominator remain open. New opcode/phase/owner/full route0, levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-appearance-rom-input-source-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','cn_ROM_specific_file_selectors_added','native_function_envelopes_read',
        'native_function_bytes_read','actual_referenced_ROM_file_samples_read','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
