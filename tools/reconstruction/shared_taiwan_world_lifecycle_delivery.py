"""Seal static actual TW Session/common-world entry, ready and cleanup source."""
import json
import struct
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import ArchivedInputs,SERVER
from .packet_connection_inventory import IMAGE,PIN,BASE,LENGTH_TABLE,WORLD_TABLE
from .cn_shared_movement_owner_delivery import sha,dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='shared-taiwan-world-lifecycle-01'
ROUND='20261007-tw-common-world-lifecycle'
MODIFIED=['src/net/Session.h','src/net/Session.cpp','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp']
ADDED=['src/protocol/RecoveredWorldEntryView.h','src/game/SharedTaiwanWorldLifecycle.h','src/game/SharedTaiwanWorldLifecycle.cpp']
SOURCES=MODIFIED+ADDED+['src/protocol/RecoveredWorldEntry.h','src/protocol/RecoveredWorldReady.h',
    'src/protocol/RecoveredWorldFrame.h','src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'docs/research/shared-taiwan-world-lifecycle-20261007.md']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed TW lifecycle delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-21';before=(cat/'source-file-manifest.json').read_bytes()
    if sha(before)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog manifest changed')
    catalog=json.loads(before);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    changes=[];snapshots=[]
    for rel in MODIFIED:
        raw=(out/'prior-sources'/rel).read_bytes();expected=catalog[rel]['sha256']
        if sha(raw)!=expected or captured[rel]!=catalog[rel]:raise ValueError('Before source differs: '+rel)
        snapshots.append({'path':'prior-sources/'+rel,'sha256':sha(raw),'bytes':len(raw),'original':str(SERVER/rel)})
        changes.append({'path':rel,'before_sha256':expected,'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_source_captured_before_edit':True,'previous_catalog':cat.relative_to(SERVER).as_posix()})
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if sha(raw)!=PIN:raise ValueError('Pinned TW mapped image changed')
    leaf=struct.unpack_from('<I',raw,LENGTH_TABLE+4*0x2a)[0]-BASE
    target=struct.unpack_from('<I',raw,WORLD_TABLE+4*0x2a)[0]-BASE
    # Initial2A is consumed by the dedicated64910 ->68160/read36 route;
    # the later WORLD switch has the default consume join for this value.
    if target!=0x6b517 or raw[leaf:leaf+6]!=b'\xb8'+struct.pack('<I',37)+b'\xc3':
        raise ValueError('TW full2A length/dispatch changed')
    md=Cs(CS_ARCH_X86,CS_MODE_32);native=[];pending=[]
    for name,start,end in [('2a-length',leaf,leaf+6),('2a-normal-area',0x681cf,0x681eb),
        ('2a-initial-caller',0x65157,0x651a1),('2a-payload36-consumer',0x68160,0x681cf),
        ('2a-local-handle-geometry',0x68626,0x68675),('initial-tail',0x654f7,0x6553d),
        ('ready-1c-producer',0x157f0,0x15839)]:
        code=raw[start:end];ins=list(md.disasm(code,BASE+start))
        if sum(i.size for i in ins)!=len(code):raise ValueError('Native slice boundary differs: '+name)
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        pending.extend([('native/tw/'+name+'.bin',code,IMAGE),('native/tw/'+name+'.asm',asm,'pinned TW disassembly')])
        native.append({'name':name,'rva':f'{start:08x}','bytes':len(code),'sha256':sha(code)})
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    save('prior-manifests/catalog21-source-files.json',before,cat/'source-file-manifest.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'source-adaptation-receipt.json',changes)
    gaps=['Actual dual Application/listeners, per-TW-connection hook installation and same common CN registry hosting remain open.',
        'Actual full native2A/profile issuer, scene publication/visibility policy and full native6F/5E/73/resources/text suppliers remain required.',
        'TW selected-ID/low14 handle constraint preserved; independent actor allocation and larger IDs remain open, no truncation.',
        'TW-origin common movement,61/reset/transfer/recovery/battle/path and remaining whole-game phase/state/variant denominator remain open.',
        'Tail acceptance/source send submission is not native world rendering, client receipt, full route acceptance or deployment.']
    manifest={'kind':'actual TW Session optional full2A ->common saved geometry/lease ->native accepted tail ->real entered owner ->transport-owned visible/presence cleanup',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'tw_native_spans':native,
        'native_sha256':PIN,'new_source_files':3,'modified_cpp_files':4,
        'tw_2a_later_world_table_target':'0006b517 default consume join',
        'tw_2a_initial_consumer':'00465194 calls00468160;004681A3 reads36 payload bytes',
        'source_owner_chains_added':0,'tw_source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'new_unique_cn_phase_opcode_binding_values':0,'new_opcode_values':0,'new_complete_routes':0,
        'actual_session_extension_points_connected':True,'formal_application_hosted':False,
        'tw_common_enrollment_available_only_when_explicitly_hosted':True,'tw_formal_sessions_enrolled':False,
        'frozen_legacy_entry_and_ready_callbacks_preserved':True,'native_tw_tail_parser_modified':False,
        'initial_geometry_and_saved_revision_required':True,'transport_owned_generation_cleanup':True,
        'ready_hook_after_synchronized_native_tail_flag':True,'no_new_ingress_before_common_activation':True,
        'previous_goal_turn_classification':'progress: native6F/5E/73 private actor instances and common CN cleanup sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'TW actual native entry/tail/common presence and transport cleanup extension',
        'version_scope':'tw','status':'台服Session已接可選完整2A/共用位置與租約/尾包後啟用/世代斷線清理；正式Application未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},
        'tw_native_c2s_by_phase':{'world':['1F','23','1C']},'tw_native_s2c_by_phase':{'world':['2A']},
        'source_paths':SOURCES,'source_owner_chains_added':0,'tw_source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none; reads common saved position/ownership when hosted; no phase1 database execution',
        'shared_storage':['common account/character ownership and persisted position/revision, transient common presence/visibility'],
        'native_form_qualifications':{'actual_full_tw2a_preserved':True,'existing_tw_tail_parser_unchanged':True,
            'common_ready_after_actual_transport_ready':True,'transport_cleanup_retained':True,
            'native_render_acceptance':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'version_scope':'tw','root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Bind actual TW/CN scene owner/data suppliers and TW-origin common movement; retain per-connection hooks and native identity limits.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'tw_native_spans':len(native),
        'new_cpp_files':3,'modified_cpp_files':4,'new_tw_partial_owner_chains':1,'new_cn_phase_bindings':0,
        'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
