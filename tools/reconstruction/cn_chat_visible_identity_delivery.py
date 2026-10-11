"""Seal primary CN6F/name/5C lineage and actual current visibility qualification."""
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
NAME='cn-chat-visible-identity-01'
ROUND='20261007-cn-chat-visible-identity'
MODIFIED=['src/cn/protocol/CnRemoteActor.h','src/cn/world/SharedActorVisibility.h',
    'src/cn/world/SharedActorVisibility.cpp','src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
    'src/cn/world/SharedWorldGameplay.cpp','tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/world/SharedMovementPublication.h','src/cn/world/SharedMovementPublication.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/cn/protocol/CnChat.h',
    'src/cn/protocol/CnChatConsumerContract.h','src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/protocol/RecoveredRemoteActor.h','src/protocol/RecoveredChat.h','src/core/Application.cpp',
    'src/net/Session.h','src/net/Session.cpp','src/text/ChineseText.h','src/text/ChineseText.cpp',
    'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp']
SOURCES=MODIFIED+CONTEXT+['docs/research/cn-chat-visible-identity-20261007.md',
    'tools/reconstruction/cn_chat_visible_identity_delivery.py']
FUNCTIONS=['00532410','0052f5a0','00531ea0','0053f5e0','0053f880','00405a30']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog43-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();r=before[rel]
        if sha(b)!=r['sha256'] or len(b)!=r['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-43'})
    for rel in CONTEXT:
        if sha((SERVER/rel).read_bytes())!=known[rel]['sha256']:raise ValueError('Context/frozen source differs '+rel)
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
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;spans=[]
    for va in FUNCTIONS:
        r=rows[va];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        source=p.read_bytes();lo=int(va,16);size=int(r['bytes']);code=pe.get_data(lo-base,size)
        if len(code)!=size:raise ValueError('Short primary span')
        save('native/'+va+'.c',source,p);save('native/'+va+'.bin',code,exe)
        span={'va':va,'reported_bytes':size,'source_sha256':sha(source),'code_sha256':sha(code),
            'declared_extent_not_complete_cfg_claim':True}
        if va in ['00532410','0052f5a0','00531ea0','00405a30']:
            cfg,asm,ins=trace(md,code,lo,lo+size,{})
            save('native/'+va+'-cfg.asm',asm,'primary static CFG decoding')
            save('native/'+va+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'primary CFG calls not followed')
            span['cfg_instructions']=cfg['decoded_cfg_instructions'];span['cfg_bytes']=cfg['decoded_unique_cfg_bytes']
            span['open_edges']=cfg['open_edges']
        spans.append(span)
    # Preserve exact existing peer/bubble evidence; no rerun of native/game code.
    for name,filenames in [
        ('cn-chat-consumer-capacity-01',['native-consumer-contract.json','native/world5C-primary.bin','native/world5C-cfg.asm','native/world5C-cfg.json']),
        ('shared-actor-visibility-01',['native-visible-actor-contract.json','native/cn/world-6f-branch.c.txt'])]:
        expected=ledger['cn_account_admission_evidence'][name]['artifact_sha256']
        for rel in filenames:
            p=ROOT/name/rel;b=p.read_bytes()
            if sha(b)!=expected[rel]:raise ValueError('Preserved native evidence differs')
            save('prior-native/'+name+'/'+rel,b,p)
    phase_path=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    phases=json.loads(phase_path.read_bytes());selected=[r for r in phases if r['phase']=='world-connection-1' and r['opcode'] in [0x6f,0x5c]]
    if len(selected)!=2:raise ValueError('Native source branches differ')
    save('native/6F-5C-phase-source-relations.json',(json.dumps(selected,indent=2)+'\n').encode(),phase_path)
    for r in selected:
        p=CN/r['branch_source'];save('native/'+Path(r['branch_source']).name,p.read_bytes(),p)
    lineage={'client_sha256':PIN,'native_6f_source':{'body_origin':1,'identity_mask':'00000fff',
        'raw_language_tag_body_bit':25,'wire_name_logical_offset':29,'name_region_admission_bytes':16,
        'native_constructor':'00532410','entry_identity_offset':'18','entry_name_offset':'1c','entry_stride':'268','pool_entries':128},
        'native_5c_peer_consumer':{'function':'00531ea0','reply_actor_dword_offset':5,
            'lookup_identity_offset':'18','lookup_name_offset':'1c','bubble_handle_offset':'60',
            'initial_board_temporary_read_offset':'strlen(stored native name)+9; not ordinary body offset',
            'ordinary_bubble_uses_full_text':True},
        'source_profile':'existing private current visible CN incarnation, tag0 raw native name; no name/control script conversion',
        'expected_send_submission_not_native_memory_observation':True,'self_or_tw_identity_equivalence_proven':False,
        'server_audience_permission_proven':False,'tag1_native_name_projection_implemented':False}
    save('native-chat-identity-lineage.json',(json.dumps(lineage,indent=2)+'\n').encode(),'scoped primary native identity/name lineage')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before source edits'})
    gaps=['Actual native chat audience/permissions/full5C header/source revisions and scene policy/allocation/resources remain required; no real production authority is supplied.',
        'Tag1 native converted actor names, actual native rename/scene/reset updates and self/TW chat identity need their separate exact owners.',
        'Board/structured/control/battle variants and native backing-buffer/destination qualification remain open; send-submitted expected actor is not client observation.',
        'TW input->CN fanout, actual Application hosting, account/world success suppliers, monster stats/skills and whole-game directional/state/variant denominator remain incomplete.']
    manifest={'kind':'native6F stored low12/name ->actual current CN visible incarnation ->ordinary peer0/6 supplied5C qualification before publication',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'native_spans':spans,
        'snapshots':snapshots,'native_identity_lineage':lineage,'modified_cpp_files':6,'modified_catalog_tools':1,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'ordinary_peer_reply_channels':[0,6],'native_world_owner_implemented':False,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog43 primary chat display capacity and phase consumer boundaries integrated',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','deployed','production_database_read_or_modified',
            'client_modified','font_modified','frozen_tw_chat_modified','resource_extraction_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native chat5C ordinary peer identity bound to current expected6F visibility',
        'version_scope':'cn','status':'兩個普通peer氣泡頻道接既有當前可見角色token/原生識別/名字；實際header/受眾/authority未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['existing actual common leases and saved-position revision; no native ID inferred from DB IDs; no tables created'],
        'native_form_qualifications':{'peer_channels':[0,6],'raw_native_name_language_tag':0,
            'current_visible_incarnation_required':True,'client_memory_observed':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['chat_visible_identity']={'root':out.relative_to(SERVER).as_posix(),
        'ordinary_peer_channels':[0,6],'same_private_visible_incarnation':True,'actual_authority_implemented':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'native_spans':spans,
        'new_complete_routes':0,'new_phase_bindings':0,'tests_run':False}))

if __name__=='__main__':main()
