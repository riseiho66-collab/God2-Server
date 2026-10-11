"""Seal independent native camera initialization/frame source; no gameplay execution."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-native-camera-frame-01'
ROUND='20261007-cn-native-camera-frame'
MODIFIED=['src/cn/world/SharedNativeMovementScene.h','src/cn/world/SharedNativeMovementScene.cpp',
    'src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp']
ADDED=['src/cn/world/CnNativeCameraMotion.h','src/cn/world/CnNativeCameraMotion.cpp']
CONTEXT=['src/cn/assets/CnOutdoorTerrain.h','src/cn/assets/CnOutdoorTerrain.cpp',
    'src/cn/world/CnOutdoorCamera.h','src/cn/world/CnOutdoorCamera.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
    'scripts/tw/native_movement.lua','scripts/cn/native_movement.lua']
SOURCES=MODIFIED+ADDED+CONTEXT+['docs/research/cn-native-camera-frame-20261007.md']
FUNCTIONS=[('00539150',16),('005393b0',16),('005395e0',16),('00489230',8),
    ('00489070',8),('005385f0',16),('00473120',6)]

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed native camera frame source')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-25';before=(cat/'source-file-manifest.json').read_bytes()
    if sha(before)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior source catalog manifest changed')
    previous=json.loads(before);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    captured.update(json.loads((out/'before-window-source-manifest.json').read_bytes()))
    snapshots=[];changes=[];unchanged=[];pending=[]
    for rel in MODIFIED:
        raw=(out/'prior-sources'/rel).read_bytes();expected=previous[rel]['sha256']
        if sha(raw)!=expected or captured[rel]!=previous[rel]:raise ValueError('Before source changed: '+rel)
        snapshots.append({'path':'prior-sources/'+rel,'sha256':sha(raw),'bytes':len(raw),'original':str(SERVER/rel)})
        changes.append({'path':rel,'before_sha256':expected,'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':cat.relative_to(SERVER).as_posix()})
    for rel in CONTEXT:
        expected=previous[rel]['sha256']
        if sha((SERVER/rel).read_bytes())!=expected:raise ValueError('Context changed: '+rel)
        unchanged.append({'path':rel,'sha256':expected,'unchanged_from_catalog25':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';pe_raw=exe.read_bytes()
    if sha(pe_raw)!=PIN:raise ValueError('Pinned CN PE changed')
    pe=pefile.PE(data=pe_raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);native=[]
    for address,part in FUNCTIONS:
        path=RECOVERY/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=path.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native extent differs')
        size=int(match.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        ins=list(md.disasm(code,int(address,16)))
        if len(code)!=size or sum(i.size for i in ins)!=size:raise ValueError('Incomplete native span')
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for ext,data,origin in [('.c',source,path),('.bin',code,exe),('.asm',asm,'pinned CN disassembly')]:
            pending.append(('native/functions/'+address+ext,data,origin))
        native.append({'address':address,'bytes':size,'native_sha256':sha(code),'source_sha256':sha(source),
            'decoded_bytes':sum(i.size for i in ins),'source_original':str(path)})
    constants=[]
    for address,fmt,expected in [('007ed104','<f',bytes.fromhex('0000003f')),
        ('007f1170','<f',bytes.fromhex('000000bf')),('007f58b8','<f',bytes.fromhex('6f12833a')),
        ('007ed2a0','<dd',bytes.fromhex('0000000000000000000000000000f041'))]:
        data=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,len(expected))
        if data!=expected:raise ValueError('Pinned constant differs: '+address)
        constants.append({'address':address,'bytes':len(data),'hex':data.hex(),'sha256':sha(data),
            'decoded_values':struct.unpack(fmt,data),'not_gameplay_execution':True})
        pending.append(('native/constants/'+address+'.bin',data,exe))
    table=pe.get_data(0x007f1cf0-pe.OPTIONAL_HEADER.ImageBase,384)
    if sha(table)!='8d79f0c397c065f37dcae558f0dbf9323938705b3a583d61713dede2cf89d778':
        raise ValueError('Pinned speed/direction table differs')
    constants.append({'address':'007f1cf0','bytes':len(table),'sha256':sha(table),
        'decoded_rows':[struct.unpack('<9f2ihh',table[i*48:(i+1)*48]) for i in range(8)],
        'not_gameplay_execution':True})
    pending.append(('native/constants/007f1cf0.bin',table,exe))
    for name in ['cn-initial-camera-source-01','cn-live-movement-scene-owner-01']:
        path=ROOT/name/'integration-manifest.json';raw=path.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior evidence changed')
        old={r['address']:r for r in json.loads(raw).get('native_spans',[])}
        for row in native:
            if row['address'] in old:
                for key in ['native_sha256','source_sha256']:
                    if row[key]!=old[row['address']][key]:raise ValueError('Prior native bytes differ')
        pending.append(('prior-manifests/'+name+'.json',raw,path))
    def save(rel,data,origin):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    save('prior-manifests/catalog25-source-files.json',before,cat/'source-file-manifest.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    save('catalog-tool.py',(SERVER/'tools/reconstruction/dual_client_route_catalog.py').read_bytes(),SERVER/'tools/reconstruction/dual_client_route_catalog.py')
    dump(out/'source-adaptation-receipt.json',changes);dump(out/'unchanged-source-receipt.json',unchanged)
    gaps=['Actual native frame scheduler/authority elapsed/state/mount resource/viewport supplier and formal Application hosting remain open.',
        'Independent frame source is integrated; actual ring admission/deferred notifications/path advance/native model publication remain mandatory authority inputs.',
        'Initial00473120 invocation, unknown null/alias/dynamic-object/frame variants, other modes/transfers/battle and TW native view remain open.',
        'Movement timing/pending/reset/server permission/full5D original authority remains open; client renderer speed LUT is not that authority.',
        'Strict float compiler/environment qualification is deferred to phase2; wrapped/nonfinite/subnormal/non-nearest domains stay unqualified.',
        'All remaining gameplay paths and whole directional/state/variant/indirect/deferred denominator remain open; no complete-route/native-render/deployment claim.']
    manifest={'kind':'native speed/direction initialization and elapsed binary32 frame ->independent ready common scene camera/cache ->actual authority/model callback',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'unchanged_context':unchanged,
        'native_spans':native,'native_constants':constants,'client_sha256':PIN,
        'new_source_files':2,'modified_cpp_files':4,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_unique_cn_phase_opcode_binding_values':0,'new_opcode_values':0,'new_complete_routes':0,
        'native_renderer_initializer_integrated':True,'independent_native_frame_source_integrated':True,
        'actual_scheduler_authority_implemented':False,'native_path_advance_implemented':False,
        'compiler_float_runtime_qualified':False,'native_wrap_variants_qualified':False,
        'one_animation_frame_per_packet_claimed':False,'initial_cache_success_assumed':False,
        'frame_mutates_common_position_or_sends_ack':False,'formal_application_hosted':False,
        'known_null_center_frame_preserves_visibility_without_projection':True,
        'previous_goal_turn_classification':'progress: native initial camera source and catalog25 sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN independent native elapsed camera frame in existing scene owner',
        'version_scope':'cn','status':'已接原生方向速度初始化/逐frame位移捨入/獨立鏡頭cache更新；實際scheduler/權限及正式掛載未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['same common character/position; no separate gameplay tables or frame DB mutation'],
        'native_form_qualifications':{'native_renderer_speed_table':True,'native_frame_arithmetic':True,
            'independent_frame_lifecycle_source':True,'actual_frame_scheduler':False,
            'native_server_movement_permission':False,'compiler_float_runtime_qualified':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover actual elapsed/scheduler/viewport and mount table input ownership; connect native ring/path completion and full5D authority into formal common dispatch.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(native),
        'native_constants':len(constants),'new_cpp_files':2,'modified_cpp_files':4,'new_partial_owner_chains':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
