"""PHASE1 file-only ACTINDEX/reference and scene-source receipts; no execution."""
import csv
import hashlib
import json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-appearance-bank-source-binding-01'
ROUND='20261007-cn-appearance-bank-source-binding'
SOURCES=('src/cn/assets/CnRomCommandReferences.h','src/cn/assets/CnRomCommandReferences.cpp',
    'src/cn/assets/CnRomAsset.h','src/cn/assets/CnRomAsset.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'tools/reconstruction/cn_appearance_bank_source_binding_delivery.py',
    'docs/research/cn-appearance-bank-source-binding-20261007.md')
FUNCTIONS=('00418830','00419110','00417620','0041b590','00482f40','00483040','004830c0',
    '0041aef0','0041af00','00416140','004161a0','00488b70','00488da0','00488480','00487f70')
REMAINING=[
    'Actual two-cache initialization/checkpoint/load/history/current native bank provider and full ACT/resource lifetime remain unconfigured; reference projection is not bank allocation or rendering.',
    'Actual equipment-to-input/full6F issuer/observer policy/profile source owner and formal Application/native/WS hosting remain missing.',
    'DrvDoll declared-length discrepancy, auxiliary/alternate/CF/later appearance and complete image/palette/FLC/ACT behavior remain open.',
    'All TW/CN/native PC/web gameplay/numeric/replay/recovery and exhaustive direction/phase/state/variant/indirect/deferred denominator remain open; levels unchanged; comprehensive tests follow full source connection.',
]

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh source receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old_sources={};preserved=[]
    for row in before:
        data=(out/row['snapshot']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before receipt differs')
        old_sources[row['path']]=data
        if row['path'] not in SOURCES and row['path'] not in ('docs/PACKET_CONNECTION_GOAL_20261006.md',
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen context changed: '+row['path'])
            preserved.append(row)
    # Compare actual source text bodies, never run old/new C++ functions.
    def body(data,signature):
        start=data.index(signature);at=data.index(b'{',start);depth=1;end=at+1
        while depth:
            depth+=(data[end]==123)-(data[end]==125);end+=1
        return data[start:end]
    retained_bodies=[]
    for path,signature in (
        ('src/cn/assets/CnRomAsset.cpp',b'const CnRomAsset::Action* CnRomAsset::find_action('),
        ('src/cn/assets/CnRomAsset.cpp',b'std::span<const std::uint8_t> CnRomAsset::raw_record('),
        ('src/cn/assets/CnRomAsset.cpp',b'std::optional<CnRomAsset::TileGeometry> CnRomAsset::tile_geometry('),
        ('src/cn/world/SharedActorVisibility.cpp',b'std::optional<SharedActorVisibility::Mainland> SharedActorVisibility::normal_mainland_from_scene('),
        ('src/cn/world/SharedInitialScene.cpp',b'std::shared_ptr<SharedInitialScene> SharedInitialScene::prepare('),
        ('src/cn/world/SharedInitialScene.cpp',b'std::optional<SharedMovement::Scene> SharedInitialScene::initial_movement_scene(')):
        old=body(old_sources[path],signature);new=body((ROOT/path).read_bytes(),signature)
        if old!=new:raise RuntimeError('Existing body changed: '+signature.decode())
        retained_bodies.append({'path':path,'signature':signature.decode(),'body_sha256':sha(old),'exact_bytes_retained':True})
    dump('preserved-source-bodies.json',retained_bodies)
    prior=base/'cn-appearance-rom-input-source-01';data=(prior/'manifest.json').read_bytes();manifest=json.loads(data)
    if not manifest['sealed'] or sha(data)!='34929221d883be4dcb5111b4b48e7173f40a70617b6847752cd011133c2f156f':raise RuntimeError('Prior sealed ROM receipt differs')
    pins={r['path']:r['sha256'] for r in manifest['files']};save('retained-ROM-source/manifest.json',data)
    retained={}
    names=['findings.json','resources/referenced-ROM-file-samples.json']
    names += [f'resources/sample-{n:02}.{suffix}' for n in range(6) for suffix in ('decoded','sections.json')]
    for rel in names:
        data=(prior/rel).read_bytes()
        if sha(data)!=pins[rel]:raise RuntimeError('Prior sealed input differs: '+rel)
        save('retained-ROM-source/'+Path(rel).name,data);retained[rel]=data
    sample_rows=json.loads(retained['resources/referenced-ROM-file-samples.json']);sample_observations=[]
    for n,row in enumerate(sample_rows):
        plain=retained[f'resources/sample-{n:02}.decoded'];sections=json.loads(retained[f'resources/sample-{n:02}.sections.json'])
        identities=[];commands=[]
        for section in sections:
            at=section['payload_offset'];length=section['bytes']
            if at+length>len(plain):raise RuntimeError('Sealed section outside file')
            if section['tag']=='ACTINDEX':identities.append(int.from_bytes(plain[at:at+2],'little'))
            for ref in section.get('command10_raw_references',[]):
                offset=ref['file_offset'];raw=plain[offset:offset+10]
                if raw.hex()!=ref['raw_10byte_hex'] or raw[0]!=10:raise RuntimeError('Sealed raw command differs')
                commands.append(ref)
        sample_observations.append({'sample':n,'CSV_reference':row['CSV_reference'],'selected_path':row['selected_path'],
            'ACTINDEX_words':identities,'raw_command10_count':len(commands),'raw_command10_references':commands,
            'raw_command10_rom_words':sorted({r['rom_reference_word'] for r in commands}),
            'decoded_sha256':sha(plain),'native_bank_instantiated':False,'reference_projection_executed':False})
    dump('resources/ACTINDEX-command10-file-observations.json',sample_observations)
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    metadata=(recovery/'functions.tsv').read_bytes();rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8').splitlines(),delimiter='\t')}
    envelopes=[]
    for address in FUNCTIONS:
        row=rows[address];size=int(row['bytes']);path=(recovery/row['file']).resolve()
        if not path.is_relative_to(recovery.resolve()):raise RuntimeError('Recovery outside root')
        code=view.read(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size);source=path.read_bytes();instructions=list(md.disasm(code,int(address,16)))
        listing=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions)+'\n').encode()
        for extension,data in (('.bin',code),('.asm',listing),('.c',source)):save('native/'+address+extension,data)
        envelopes.append({'address':address,'bytes':size,'metadata':row,'native_sha256':sha(code),
            'recovery_source':str(path),'recovery_source_sha256':sha(source),'decoded_instruction_bytes':sum(i.size for i in instructions),
            'native_executed':False,'all_exceptional_or_indirect_paths_closed':False})
    pe.close();dump('native/function-envelopes.json',{'primary':str(native),'sha256':PIN,'recovery_metadata_sha256':sha(metadata),'ranges':envelopes})
    peer_root=Path('C:/Users/risei/Desktop/God2/God2/output/web-prototype')
    originals=[];peer_objects={}
    for rel,pin in (
        ('reports/client-goal-20261007/native-cn-world-appearance-verification.json','72fcb8ef76723fad78a1e94b438ec3e98eb76ebaa1934977ea27edc0e9b4a89e'),
        ('reports/client-goal-20261007/native-cn-world-appearance-source.json','aaad07673dbc0254bbe3a2d5057ff0f14cffed9a33af27811cd3eee831571e21'),
        ('WEB_SERVER_INTEGRATION.md','4e5c95be52357e9b5b5a692393d1109a5c2dd4e66816ef95da74b7ec0b3040d7')):
        data=(peer_root/rel).read_bytes()
        if sha(data)!=pin:raise RuntimeError('Peer original changed; new handoff needed: '+rel)
        filename=Path(rel).name;save('peer-handoff/'+filename,data)
        originals.append({'original':str(peer_root/rel),'path':filename,'sha256':pin,'bytes':len(data)})
        if filename.endswith('.json'):peer_objects[filename]=json.loads(data)
    peer={'round':'20261007-native-cn-world-appearance','saved_originals':originals,
        'read_method':'File-only exact supplied original SHA snapshots; no peer test/browser/native/server/DB execution',
        'renderReady':False,'new_complete_gameplay_routes':0,'nativeExecuted':False,
        'peer_ROM_input_manifest_read_confirmed':True,'peer_reported_original_ROM_files':11,'peer_reported_palette_banks':88,
        'peer_results_are_server_native_acceptance':False,'server_capacity_remeasured':False,
        'peer_capacity_bytes_reported':40512040010,'new_ACK_sent':False,'new_ACK_read_confirmed':False}
    dump('peer-handoff/server-file-source-receipt.json',peer)
    facts={'round':ROUND,'cn_native_sha256_context':PIN,
        'previous_goal_turn_classification':'progress: exact full native appearance input ->immutable CSV/ROM source and catalog104 sealed',
        'cn_ACTINDEX_action_operand_metadata_added':1,'cn_read_only_command10_projections_added':1,
        'cn_same_scene_appearance_resource_witnesses_added':1,'cn_existing6F_source_qualifications_strengthened':1,
        'native_function_envelopes_read':len(envelopes),'native_function_bytes_read':sum(r['bytes'] for r in envelopes),
        'retained_actual_ROM_file_samples':len(sample_observations),'actual_native_bank_provider_configured':False,
        'command_projection_executed':False,'auxiliary_resource_recovered':False,'authoritative_equipment_to_appearance_recovered':False,
        'new_packet_values':0,'new_native_phase_source_bindings':0,'new_source_owner_chains':0,'new_tw_source_owner_chains':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completed_routes':None,
        'whole_game_completion_percent':None,'formal_application_hosted':False,'levels_changed':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'latest_peer_handoff_round':peer['round'],'preserved_contexts':preserved,'remaining':REMAINING}
    dump('findings.json',facts)
    for rel in SOURCES:save('source/'+Path(rel).name,(ROOT/rel).read_bytes())
    dump('source/source-origins.json',[{'path':rel,'snapshot':Path(rel).name,'sha256':sha((ROOT/rel).read_bytes())} for rel in SOURCES])
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_appearance_bank_source_binding']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['cn_appearance_rom_input_source']['peer_read_confirmed']=True
    ledger['cn_appearance_rom_input_source']['peer_read_confirmation_evidence']=out.relative_to(ROOT).as_posix()+'/peer-handoff/native-cn-world-appearance-source.json'
    ledger['web_native_cn_world_appearance_handoff']=dict(peer,evidence=out.relative_to(ROOT).as_posix()+'/peer-handoff')
    ledger['dual_client_source_segments'].append({'name':'CN actual ACTINDEX/command10 reference source +same-scene full2A/ROM appearance witness to supplied6F',
        'version_scope':'cn-normal-ordinary-appearance-source-only','status':'Read-only original reference projection and actual scene/connection/lease/source-owner lineage; actual native bank/context/ACT/equipment/issuer/providers/hosting open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'tw_source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Recover actual two-cache initial/base counters/checkpoint/ROM slot history and configured source owner; connect actual equipment/full6F issuer/observer policy/resource revision/current bank to formal providers. Auxiliary/alternate/CF/ACT/rendering, all gameplay/numeric/denominator remain open; levels unchanged, PHASE1 file-only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN ACTINDEX/reference and same-scene appearance source ('+ROUND+')\n\n'
        'Actual native ACTINDEX/action operand metadata1/read-only command10 projection1/same-scene full2A+ROM source witness1/existing supplied6F source qualification strengthened1. Two native caches are reused; checkpoint restores allocator cursors, not proof512 slots reset. Actual Drv5451.ROMZ identity5455 and108 raw self references retained. No invented bank, zero slot or CSV-ordinal allocation. Actual source owner/auxiliary/ACT/equipment/full6F issuer/observer/Application hosting and all gameplay/denominator remain open. Web peer confirmed prior127-file ROM source read; current three originals received file-only, renderReady=false, new full route0. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-appearance-bank-source-binding-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','native_function_envelopes_read','native_function_bytes_read','cn_same_scene_appearance_resource_witnesses_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
