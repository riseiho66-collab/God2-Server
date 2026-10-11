"""Seal pinned directory selection/producer source and bounded primary CFG evidence."""
import csv
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-directory-selection-producer-01'
ROUND='20261007-cn-directory-selection-producer'
NEW=['src/cn/protocol/CnDirectorySelection.h']
MODIFIED=['src/cn/protocol/CnDirectoryWire.h','tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/protocol/CnDirectoryReceiver.h','src/cn/world/SharedDirectory.h','src/cn/world/SharedDirectory.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-directory-selection-producer-20261007.md',
    'tools/reconstruction/cn_directory_selection_producer_delivery.py']
FUNCTIONS=['0050e3b0','0050e5e0','00510e80','00512700']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed during source integration')
    catalog=(out/'catalog34-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=captured[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ValueError('Before source differs')
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Before differs from catalog')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-34'})
    for rel in CONTEXT:
        b=(SERVER/rel).read_bytes()
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Context differs')
        unchanged.append({'path':rel,'sha256':sha(b),'previously_cataloged':rel in known})
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Pinned CN differs')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    pending=[('native/functions.tsv',metadata,RECOVERY/'functions.tsv')];native=[]
    for address in FUNCTIONS:
        path=RECOVERY/rows[address]['file'];source=path.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match[1],16)!=int(address,16):raise ValueError('Native metadata differs')
        size=int(match[2]);code=pe.get_data(int(address,16)-base,size)
        if len(code)!=size:raise ValueError('Missing native bytes')
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(path),'declared_size_not_assumed_complete_body':True})
        pending.extend([(f'native/source/{address}.c',source,path),(f'native/declared-spans/{address}.bin',code,exe)])
    switches={};tables=[]
    for site,table,count in [(0x50e442,0x50e544,24),(0x50e6b0,0x50e918,30),
        (0x50e7f0,0x50e990,16),(0x50e857,0x50e9d0,5)]:
        data=pe.get_data(table-base,count*4);targets=list(struct.unpack('<'+'I'*count,data));switches[site]=targets
        pending.append((f'native/tables/{table:08x}.bin',data,exe))
        tables.append({'callsite':f'{site:08x}','table_va':f'{table:08x}','entries':count,
            'targets':[f'{x:08x}' for x in targets],'sha256':sha(data)})
    cfgs=[];envelopes=[]
    for lo,hi in [(0x50e3b0,0x50e542),(0x50e5e0,0x50e916)]:
        code=pe.get_data(lo-base,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,switches)
        if cfg['open_edges']:raise ValueError('Qualified local CFG has open edges')
        cfg['metadata_declared_size']=int(rows[f'{lo:08x}']['bytes']);cfgs.append(cfg)
        envelopes.append({'address':f'{lo:08x}','end_exclusive':f'{hi:08x}','bytes':len(code),
            'sha256':sha(code),'decoded_unique_cfg_bytes':cfg['decoded_unique_cfg_bytes']})
        pending.extend([(f'native/cfg/{lo:08x}.bin',code,exe),
            (f'native/cfg/{lo:08x}.asm',asm,'static primary recursive CFG, calls recorded not followed')])
    # Parse immutable source inventory as accounting only. No native/game
    # execution, C++ evaluation or request/response simulation occurs here.
    source=(SERVER/NEW[0]).read_text(encoding='utf-8')
    expressions=re.findall(r'\{(true|false),(0x[0-9a-f]+),(\d+),(std::nullopt|\d+),(0x[0-9a-f]+)\}',source)
    origins=[{'native_mode_bit0':mode=='true','ui_state':f'{int(state,16):02X}','group':int(group),
        'secondary':None if secondary=='std::nullopt' else int(secondary),'selector':f'{int(selector,16):02X}'}
        for mode,state,group,secondary,selector in expressions]
    if len(origins)!=43 or sum(r['native_mode_bit0'] for r in origins)!=3:
        raise ValueError('Source explicit origin inventory differs')
    previous={}
    for name in ['cn-summary-world-lineage-01','cn-directory-receiver-matrix-01']:
        path=ROOT/name/'integration-manifest.json';b=path.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Previous evidence differs')
        prior_manifest=json.loads(b);previous[name]=prior_manifest
        for span in native:
            same=next((x for x in prior_manifest['declared_native_spans'] if x['address']==span['address']),None)
            if same and same['declared_span_sha256']!=span['declared_span_sha256']:raise ValueError('Prior primary differs')
        pending.append((f'prior-manifests/{name}.json',b,path))
    old=previous['cn-summary-world-lineage-01']
    for envelope in envelopes:
        prior_envelope=next(x for x in old['native_code_envelopes'] if x['address']==envelope['address'])
        if envelope['sha256']!=prior_envelope['sha256']:raise ValueError('Prior complete primary differs')
    facts={'client_sha256':PIN,'mapper':'0050E5E0','request_producer':'0050E3B0',
        'explicit_mapper_conditions':origins,'explicit_mapper_condition_count':43,'mode0_conditions':40,'mode1_conditions':3,
        'whole_game_route_variants':None,'new_native_functions_recovered':0,
        'source_uses_previously_sealed_native_primary':True,'mapper_ignored_secondary_for_group2':True,
        'producer_suppresses_group_or_secondary_minus1':True,'explicit_selector00_exists':True,
        'default_return00_must_be_distinct_from_explicit_origin':True,
        'mode1_known_refresh_selectors':['19','23','24'],'mode0_same_mapper_has_no_explicit_19_23_24':True,
        'B0consumer_does_not_imply_same_mapper_produces_every_selector':True,
        'UI_context_is_not_wire_field_permission_or_server_state':True,
        'native_mode0_only_D1':['25','26'],'native_mode0_D1_then94_with_unassigned_dword':['27','28'],
        'mode0_generic_cursor_for_2A_2B_2C_2D':{f'{s:02X}':f'{0x22d0c+s*0x3f0:08X}' for s in range(0x2a,0x2e)},
        'B0same_selectors_cursor':{'owner':'indirect1C85A8','offset':'0000B56C'},
        'generic_cursor_alias_to_indirect_B56C_proven':False,'requests_preserve_actual_opaque_bytes':True,
        'cfgs':cfgs,'tables':tables,'new_phase_source_bindings':0,'new_complete_routes':0,'new_opcode_values':0}
    pending.append(('native-directory-selection-producer.json',(json.dumps(facts,indent=2)+'\n').encode(),'static primary/source accounting'))
    snapshots=[]
    def save(rel,data,origin):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':path.relative_to(out).as_posix(),'sha256':sha(path.read_bytes()),
                'bytes':path.stat().st_size,'original':'captured before source edits'})
    gaps=['Other direct/indirect/deferred producer origins and native mode0 category/render/data authority remain incomplete.',
        'Explicit UI conditions are not wire permissions; 94/B0 generic and indirect cursors must not be falsely joined.',
        'Common real directory backend/production plan/native full login-world suppliers/general world dispatcher remain missing.',
        'Whole-game total/complete-route count/completion percent stay unknown.']
    manifest={'kind':'complete bounded native directory mapper and exact request producer descriptor integrated into existing Request source',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'declared_native_spans':native,'native_code_envelopes':envelopes,'primary_switch_tables':tables,'client_sha256':PIN,
        'new_cpp_files':1,'modified_cpp_files':1,'modified_catalog_tools':1,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,'explicit_mapper_condition_count':43,
        'formal_application_hosted':False,'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        'previous_goal_turn_classification':'progress: catalog34 complete B0consumer matrix plus actual initialized row source guard sealed',
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native directory explicit UI selection and actual refresh94 producer descriptors',
        'version_scope':'cn','status':'43個mapper條件接既有Request的producer上下文；沒有新handler或完整玩法',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['UI state is not a common ID or permission; no gameplay tables created'],
        'native_form_qualifications':{'this_mapper_explicit_conditions':43,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['directory_selection_producer']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-directory-selection-producer.json','explicit_mapper_conditions':43,'complete_gameplay_routes':0,
        'new_opcode_values':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Continue native mode0 headers/render/data categories, other producer origins and actual common directory authority; resume complete native login-world suppliers/general source dispatcher.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':1,'modified_cpp_files':1,
        'explicit_mapper_conditions':43,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
