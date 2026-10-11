"""Seal bounded native chat/common recipient source accounting, without execution."""
import json
from pathlib import Path
import pefile
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-shared-native-chat-owner-01'
ROUND='20261007-cn-shared-native-chat-owner'
NEW=['src/cn/protocol/CnChat.h','src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp',
    'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp']
MODIFIED=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/text/ChineseText.h','src/text/ChineseText.cpp','src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
    'src/protocol/RecoveredChat.h','src/net/Session.h','src/net/Session.cpp',
    'src/core/Application.cpp','src/game/RecoveredPosition.h']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-shared-native-chat-owner-20261007.md',
    'tools/reconstruction/cn_shared_native_chat_owner_delivery.py']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog41-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();r=before[rel]
        if sha(b)!=r['sha256'] or len(b)!=r['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-41'})
    for rel in CONTEXT:
        if rel in known and sha((SERVER/rel).read_bytes())!=known[rel]['sha256']:
            raise ValueError('Frozen/context source changed '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged '+rel)
    imports=json.loads((out/'source-import-manifest.json').read_bytes())
    for rel,r in imports.items():
        b=(CN/r['upstream_relative']).read_bytes()
        if sha(b)!=r['before_sha256'] or sha((out/'upstream-sources'/r['upstream_relative']).read_bytes())!=sha(b) or \
           sha((SERVER/rel).read_bytes())!=r['after_sha256']:raise ValueError('Bounded source import changed')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    native_root=CN/'artifacts/native/20261006-cn-chat-01'
    receipt_path=native_root/'chat-evidence.json';receipt_bytes=receipt_path.read_bytes();receipt=json.loads(receipt_bytes)
    if receipt['client_sha256']!=PIN:raise ValueError('Native receipt pin differs')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native executable pin differs')
    pe=pefile.PE(data=raw,fast_load=True);native=[]
    save('native/chat-evidence.json',receipt_bytes,receipt_path)
    for row in receipt['functions']:
        p=Path(row['source']);b=p.read_bytes();size=row['reported_body_bytes'];va=int(row['va'],16)
        code=pe.get_data(va-pe.OPTIONAL_HEADER.ImageBase,size)
        if sha(b)!=row['source_sha256'] or len(code)!=size or sha(code)!=row['code_sha256']:
            raise ValueError('Native source span differs '+row['va'])
        save('native/'+row['va']+'.c',b,p);save('native/'+row['va']+'.bin',code,exe)
        asm=native_root/(row['va']+'.asm')
        if asm.exists():save('native/'+row['va']+'.asm',asm.read_bytes(),asm)
        native.append({'va':row['va'],'reported_bytes':size,'code_sha256':sha(code),'source_sha256':sha(b),
            'reported_extent_not_complete_cfg_claim':True})
    span=receipt['producer_contiguous_range'];lo=int(span['start'],16);hi=int(span['end_exclusive'],16)
    code=pe.get_data(lo-pe.OPTIONAL_HEADER.ImageBase,hi-lo)
    if len(code)!=hi-lo or sha(code)!=span['sha256']:raise ValueError('Primary producer span differs')
    save('native/004B1390-004B1A10.bin',code,exe)
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before edits or bounded imported source'})
    gaps=['Actual native chat WorldOwner audience/permissions/source revisions/full5C opaque headers/native actor and bubble ordering are required; no default authority implemented.',
        'TW recipients require actual same-registry enrollment; frozen TW input ->CN recipient publication is not connected by this source.',
        'Board, structured battle text, native control variants and remaining phase/state/producer/consumer branches are unconnected.',
        'Actual common account/world/gameplay suppliers and production Application hosting remain incomplete; no new complete route.',
        'Whole-game directional/state/variant/deferred denominator and completion percentage remain unknown.']
    manifest={'kind':'CN bounded native2F ->shared ready lease ->required actual chat authority ->per-recipient body-only script/encoding ->supplied native5C CN/TW transport',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'source_imports':imports,
        'native_spans':native,'primary_shared_tail_range':span,'snapshots':snapshots,
        'new_cpp_files':5,'modified_cpp_files':2,'modified_catalog_tools':1,
        'source_owner_chains_added':1,'new_cn_phase_opcode_bindings':2,'new_tw_phase_opcode_bindings':1,
        'supported_plain_channels':[0,1,3,13,18],'supported_named_whisper_channels':[2,9],
        'channel_shapes_not_permission_or_complete_variants':True,'native_world_owner_implemented':False,
        'tw_input_pipeline_unchanged':True,'tw_input_to_cn_fanout_connected':False,'same_registry_enrollment_required':True,
        'opaque_native_header_supplied_not_synthesized':True,'body_only_presentation':True,
        'new_opcode_values':0,'new_complete_routes':0,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog41 pinned current NPC name source integrated separately from historical epoch',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','deployed','production_database_read_or_modified',
            'client_modified','font_modified','frozen_tw_chat_modified','resource_extraction_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native chat2F shared ready owner with qualified CN/TW recipient5C body projection',
        'version_scope':'cn with conditional tw recipients','status':'七種原生聊天內容形式接條件來源；權威受眾/header與正式掛接未完成',
        'native_c2s_by_phase':{'world':['2F']},'native_s2c_by_phase':{'world':['5C']},
        'tw_native_c2s_by_phase':{},'tw_native_s2c_by_phase':{'world':['5C']},
        'source_paths':SOURCES,'source_owner_chains_added':1,'tw_source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none; actual common lease/repository snapshots only, no tables created',
        'shared_storage':['actual shared session/account/character lease and saved-position revision; raw native actor/header identities remain qualified separately'],
        'native_form_qualifications':{'plain_channels':[0,1,3,13,18],'named_whisper_channels':[2,9],
            'whole_opcode_variants_complete':False,'production_audience_implemented':False,'tw_input_pipeline_modified':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['shared_native_chat_owner']={'root':out.relative_to(SERVER).as_posix(),
        'bounded_content_forms':7,'actual_authority_implemented':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cn_partial_chains':1,
        'new_cn_bindings':2,'new_tw_recipient_bindings':1,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
