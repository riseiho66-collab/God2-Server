"""Seal static native Windows text source projection, without calling those APIs."""
import csv
import json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN,RECOVERY
from .cn_shared_movement_owner_delivery import sha,dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-native-actor-text-projection-01'
ROUND='20261007-cn-native-actor-text-projection'
NEW=['src/cn/text/CnNativeActorText.h','src/cn/text/CnNativeActorText.cpp']
MODIFIED=['src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'tools/reconstruction/dual_client_route_catalog.py','src/cn/world/SharedNativeChat.cpp']
CONTEXT=['src/cn/protocol/CnRemoteActor.h','src/cn/world/SharedNativeChat.h',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/cn/protocol/CnChat.h',
    'src/cn/protocol/CnChatConsumerContract.h','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/text/ChineseText.h','src/text/ChineseText.cpp','src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
    'src/protocol/RecoveredChat.h','src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-native-actor-text-projection-20261007.md',
    'tools/reconstruction/cn_native_actor_text_projection_delivery.py']
FUNCTIONS=['0053f880','0053f5e0','0053fb30','00405a30','00405a40','00405a60']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog44-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();r=before[rel]
        if sha(b)!=r['sha256'] or len(b)!=r['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-44',
            'comment_only':rel=='src/cn/world/SharedNativeChat.cpp'})
    for rel in CONTEXT:
        if sha((SERVER/rel).read_bytes())!=known[rel]['sha256']:raise ValueError('Context/frozen source differs '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native pin differs')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    save('native/selected-function-metadata.json',(json.dumps({'original_sha256':sha(metadata),
        'rows':[rows[a] for a in FUNCTIONS]},indent=2)+'\n').encode(),RECOVERY/'functions.tsv')
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
    imports={i.address:{'module':entry.dll.decode(),'name':i.name.decode() if i.name else 'ordinal:'+str(i.ordinal)}
        for entry in pe.DIRECTORY_ENTRY_IMPORT for i in entry.imports}
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;spans=[];api_calls=[]
    from capstone.x86 import X86_OP_MEM
    for va in FUNCTIONS:
        r=rows[va];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        source=p.read_bytes();lo=int(va,16);size=int(r['bytes']);code=pe.get_data(lo-base,size)
        if len(code)!=size:raise ValueError('Short native range')
        save('native/'+va+'.c',source,p);save('native/'+va+'.bin',code,exe)
        cfg,asm,ins=trace(md,code,lo,lo+size,{})
        save('native/'+va+'-cfg.asm',asm,'primary static CFG decoding')
        save('native/'+va+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'static native CFG, calls not followed')
        for i in ins.values():
            if i.mnemonic=='call' and i.operands[0].type==X86_OP_MEM:
                op=i.operands[0];target=op.mem.disp
                if not op.mem.base and not op.mem.index and target in imports:
                    api_calls.append({'function':va,'site':f'{i.address:08x}','iat':f'{target:08x}',**imports[target],
                        'execution':False})
        spans.append({'va':va,'reported_bytes':size,'source_sha256':sha(source),'code_sha256':sha(code),
            'cfg_instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'reported_extent_not_whole_program_claim':True})
    save('native/primary-api-call-edges.json',(json.dumps(sorted(api_calls,key=lambda r:r['site']),indent=2)+'\n').encode(),
        'pinned PE import table and primary static calls')
    # Keep original unhosted profile and native-visible lineage separately.
    p=CN/'src/text/CnTextProfile.h';save('upstream/CnTextProfile.h',p.read_bytes(),p)
    for name,rels in [('cn-chat-visible-identity-01',['native-chat-identity-lineage.json']),
        ('shared-actor-visibility-01',['native/cn/world-6f-branch.c.txt'])]:
        expected=ledger['cn_account_admission_evidence'][name]['artifact_sha256']
        for rel in rels:
            p=ROOT/name/rel;b=p.read_bytes()
            if sha(b)!=expected[rel]:raise ValueError('Prior native evidence differs')
            save('prior-native/'+name+'/'+rel,b,p)
    gates=[]
    for va,size in [(0x8a4594,4),(0x8aeeb8,4)]:
        b=pe.get_data(va-base,size);save('native/'+f'{va:08x}'+'-pe-initial.bin',b,exe)
        gates.append({'va':f'{va:08x}','pe_initial_hex':b.hex(),'initial_bytes_not_current_runtime_state':True})
    contract={'client_sha256':PIN,'self_tag':0,'unicode_gate':'00405A40 loads008AEEB8;00405A60 sets by NT/version query',
        'conversion_latch':'008A4594; failures may clear it','pe_initial_gates':gates,
        'tag1_success_sequence':[
            'MultiByteToWideChar(936,0,original,-1,NULL,0)',
            'LCMapStringA(0804,04000000,original,-1,buffer1024,originalWideCount*2)',
            'MultiByteToWideChar(936,0,mapped,-1,wide1024,originalWideCount)',
            'WideCharToMultiByte(950,0,wide,-1,NULL,0,NULL,NULL)',
            'WideCharToMultiByte(950,0,wide,-1,output,queriedCount,NULL,NULL)'],
        'sequential_fields':[29,45,61],'projection_output_non_nul_max_bytes':15,
        'native_first_result_checked_secondary_results_unchecked':True,'failure_and_disabled_native_variants_connected':False,
        'actual_receiver_nls_environment_qualified':False,'new_projection_executed':False,'wire_codepage_not_deduced_from_self_tag':True,
        'existing_adapter_body_profile':936,'body_profile_changed':False,'actual_receiver_acceptance':False}
    save('native-actor-text-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'scoped primary native/API source contract')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before source edits'})
    gaps=['Actual receiver Windows NLS/gates/current-state revision supplier and native character/5C prefix/wire/body qualification remain required; projection is not executed/accepted.',
        'Disabled/failure/stale secondary-buffer/expanding name/cross-field overwrite paths, actual native rename/reset and self/TW identities remain open.',
        'Original server5C header/audience/rules, actual scene resources/actor allocation, Board/battle/control variants and Application hosting remain incomplete.',
        'TW input->CN fanout, actual native success suppliers, monster stats/skills and whole-game denominator/complete routes remain pending.']
    manifest={'kind':'primary0053F880/gates/API sequence ->bounded successful native actor text prediction ->existing private visible CN chat identity query',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'native_spans':spans,'snapshots':snapshots,
        'native_contract':contract,'new_cpp_files':2,'modified_cpp_files':3,'comment_only_cpp_files':1,'modified_catalog_tools':1,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'formal_application_hosted':False,'native_text_projection_executed':False,'actual_nls_environment_accepted':False,
        'previous_goal_turn_classification':'progress: catalog44 ordinary peer5C connected to current visible6F identity/name',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_api_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_extraction_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native6F tag1 Windows successful text projection for visible peer chat',
        'version_scope':'cn','status':'原生API順序/能力gate/轉換latch追明並接成功來源投影；實際NLS狀態與正式authority未供應',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none; identity lookup/wire packet unchanged',
        'shared_storage':['same common leases and original identity bytes; native text projection stays recipient/adapter specific, no tables created'],
        'native_form_qualifications':{'successful_tag1_name_projection_source':True,'actual_projection_executed':False,
            'actual_receiver_environment_supplied':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['native_actor_text_projection']={'root':out.relative_to(SERVER).as_posix(),
        'success_projection_tag':1,'actual_environment_accepted':False,'body_profile_derived_from_native_tag':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'native_spans':spans,
        'new_complete_routes':0,'native_api_executed':False,'tests_run':False}))

if __name__=='__main__':main()
