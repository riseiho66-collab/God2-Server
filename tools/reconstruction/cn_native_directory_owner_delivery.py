"""Static pinned CN directory state/packet recovery and conditional source sealing."""
import csv
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-native-directory-owner-01'
ROUND='20261007-cn-native-directory-owner'
NEW=['src/cn/protocol/CnDirectoryWire.h','src/cn/world/SharedDirectory.h','src/cn/world/SharedDirectory.cpp']
MODIFIED=['tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/protocol/CnCharacterSummary.h','src/cn/protocol/CnTransport.h','src/cn/net/CnTransportSession.h',
    'src/cn/net/CnTransportSession.cpp','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-native-directory-owner-20261007.md',
    'tools/reconstruction/cn_native_directory_owner_delivery.py']
FUNCTIONS=['0048fcc0','0047f510','0050e3b0','0050e5e0','00510e80','00511620',
    '005118e0','00512c50','005137b0','00515680','00524e10']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed round')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed during source work')
    catalog=(out/'catalog31-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog changed')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=before[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ValueError('Before source changed')
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Before differs from prior catalog')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-31'})
    for rel in CONTEXT:
        b=(SERVER/rel).read_bytes()
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Unchanged context differs '+rel)
        unchanged.append({'path':rel,'sha256':sha(b),'previously_cataloged':rel in known})
    for rel in NEW:
        if rel in known:raise ValueError('Claimed new source was already cataloged')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Pinned CN changed')
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
        if len(code)!=size:raise ValueError('Missing declared bytes')
        pending.extend([(f'native/source/{address}.c',source,path),(f'native/declared-spans/{address}.bin',code,exe)])
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(path),'declared_size_not_assumed_complete_body':True})
    switches={};tables=[]
    for site,table,count in [(0x511690,0x511870,16),(0x515ce8,0x515eec,14),
        (0x515e2f,0x515f24,2),(0x515e5a,0x515f3c,14)]:
        data=pe.get_data(table-base,count*4);targets=list(struct.unpack('<'+'I'*count,data));switches[site]=targets
        pending.append((f'native/tables/{table:08x}.bin',data,exe))
        tables.append({'callsite':f'{site:08x}','table_va':f'{table:08x}',
            'entries':count,'targets':[f'{x:08x}' for x in targets],'sha256':sha(data)})
    for table,count,target_count in [(0x5118b0,40,16),(0x515f2c,14,2)]:
        data=pe.get_data(table-base,count)
        if max(data)>=target_count:raise ValueError('Native selector domain differs')
        pending.append((f'native/tables/{table:08x}.bin',data,exe))
        tables.append({'table_va':f'{table:08x}','bytes':count,'selector_hex':data.hex(),'sha256':sha(data)})
    cfgs=[];envelopes=[];primary={}
    for low,high in [(0x511620,0x51186e),(0x5118e0,0x5126f8),
        (0x5137b0,0x513a30),(0x515680,0x515eeb),
        (0x4901d6,0x4901f7),(0x49022b,0x49023f)]:
        code=pe.get_data(low-base,high-low);cfg,asm,ins=trace(md,code,low,high,switches)
        # The two qualified dispatcher branches deliberately stop at their
        # shared exit, not a claimed complete world-dispatcher CFG.
        expected=[] if low>=0x500000 else [{'address':'00490ab1','kind':'outside_qualified_code_envelope'}]
        if cfg['open_edges']!=expected:raise ValueError('Unexpected CFG frontier')
        cfg['bounded_dispatcher_branch_only']=low<0x500000
        if f'{low:08x}' in rows:cfg['metadata_declared_size']=int(rows[f'{low:08x}']['bytes'])
        cfgs.append(cfg);primary.update(ins)
        envelopes.append({'address':f'{low:08x}','end_exclusive':f'{high:08x}','bytes':len(code),
            'sha256':sha(code),'decoded_unique_cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'metadata_declared_size':cfg.get('metadata_declared_size'),'bounded_branch_only':low<0x500000})
        pending.extend([(f'native/cfg/{low:08x}.bin',code,exe),
            (f'native/cfg/{low:08x}.asm',asm,'primary static CFG, qualified switch tables only')])
    for site,target in [(0x4901ed,0x511620),(0x490235,0x5118e0),(0x515e4c,0x481440)]:
        ins=primary[site]
        if ins.mnemonic!='call' or ins.operands[0].type!=X86_OP_IMM or ins.operands[0].imm!=target:
            raise ValueError('Primary callsite differs')
    prior_manifest=ROOT/'cn-summary-world-lineage-01/integration-manifest.json';pm=prior_manifest.read_bytes()
    if sha(pm)!=ledger['cn_account_admission_evidence']['cn-summary-world-lineage-01']['artifact_sha256']['integration-manifest.json']:
        raise ValueError('Prior lineage evidence changed')
    old=json.loads(pm)
    for span in native:
        same=next((x for x in old['declared_native_spans'] if x['address']==span['address']),None)
        if same and same['declared_span_sha256']!=span['declared_span_sha256']:raise ValueError('Prior primary span differs')
    pending.append(('prior-manifests/cn-summary-world-lineage-01.json',pm,prior_manifest))
    prior_facts=ROOT/'cn-summary-world-lineage-01/native-world-mode-and-fragments.json'
    pf=prior_facts.read_bytes()
    if sha(pf)!=ledger['cn_account_admission_evidence']['cn-summary-world-lineage-01']['artifact_sha256']['native-world-mode-and-fragments.json']:
        raise ValueError('Prior mode facts changed')
    pending.append(('prior-findings/native-world-mode-and-fragments.json',pf,prior_facts))
    for suffix in ['128','130']:
        path=CN/f'artifacts/native/20261006-cn-dispatch-01/branches/0048fcc0-switch-0-case-{suffix}.c.txt'
        pending.append((f'native/branches/{path.name}',path.read_bytes(),path))
    facts={'client_sha256':PIN,'source_scope_selectors':['19','23','24'],
        'world_owner_reference':'player+4308C, prior renderer initializer alias to actual world network',
        'mode_bit0_business_meaning_recovered':False,
        'formats':{'C2S94':{'bytes':9,'selector_offset':1,'unwritten_padding_offsets':[2,3,4],'cursor_offset':5},
            'C2SA4':{'bytes':3,'selector_offset':1,'signed_direction_offset':2,'directions':[-1,1]},
            'S2CAE':{'bytes':25,'subtype_offset':1,'opaque_payload_bytes':24},
            'S2CB0':{'bytes':'9+40*count','block_size_u16_offset':1,'selector_offset':3,'count_offset':4,
                'cursor_offset':5,'rows_offset':9,'row_bytes':40,'row_destination_index_offset':32,
                'row_second_opaque_byte_offset':33,'render_text_regions':[[0,16],[16,16]],
                'render_word_offsets':[34,36,38],'all_native_row_capacity_bounds_recovered':False}},
        'relations':[{'request_selector':s,'B0_selector':s,'AE_subtype':a,'list_base':b,'cursor_owner':c}
            for s,a,b,c in [('19','08','player+30E74','player+30E80'),
                ('23','0B','player+36D4C','player+36D58'),
                ('24','0C','[player+1C85A8]+469C','[player+1C85A8]+46A8')]],
        'pagination':{'owner_function':'00515680','source_owner_load':'0051568B',
            'wire_callsite':'00515E4C','opcode':'A4','payload_bytes':2,
            'local_cached_condition':'candidate_page*25+1 <= cached_last_index',
            'wire_when_page_not_cached':True,'direction_is_absolute_page_number':False},
        'same_opcode_pairing_94_or_D1':False,'official_server_causality_rules_recovered':False,
        'source_adapter_constrains_same_channel_only':True,'new_opcode_values':0,
        'new_complete_routes':0,'cfgs':cfgs,'tables':tables}
    pending.append(('native-directory-relations.json',(json.dumps(facts,indent=2)+'\n').encode(),'static primary-native analysis'))
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
    gaps=['Actual common directory backend, business names/permissions/native row capacities and opaque field issuance remain open.',
        'Actual general ready-world dispatcher and production plan/native success suppliers remain incomplete.',
        'Source same-channel94/A4 ->AE/B0 contract is conditional; official response causality/order/cross-channel/push rules are not recovered.',
        'All other mode0/1 directory94/A4/D1 and AE/B0 variants remain open; no whole-opcode completion.',
        'Whole-game indirect/deferred/state/variant denominator remains unresolved; no full route or percentage claim.']
    manifest={'kind':'actual admitted common actor ->bounded native directory94/A4 ->mandatory authority ->suppliedAE/B0 ->same transport conditional source',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'new_cpp_files':3,'modified_cpp_files':0,'modified_catalog_tools':1,'declared_native_spans':native,
        'native_code_envelopes':envelopes,'primary_switch_tables':tables,'client_sha256':PIN,
        'source_owner_chains_added':1,'new_phase_opcode_bindings':4,'new_opcode_values':0,
        'source_c2s_scoped_selector_branches':6,'source_s2c_scoped_channel_projections':6,
        'new_complete_routes':0,'formal_application_hosted':False,'actual_directory_backend_implemented':False,
        'native_server_response_causality_recovered':False,'all_native_row_bounds_recovered':False,
        'previous_goal_turn_classification':'progress: catalog31 exact07/ordered common-ID ticket lineage and primary world mode/fragment recovery sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed',
            'deployed','production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native directory94/A4 and actual AE/B0 channel projection owner',
        'version_scope':'cn','status':'已接三種原生清單的共用lease/94及A4/必要資料來源/AE與B0傳輸來源；正式backend、規則與完整路徑未完成',
        'native_c2s_by_phase':{'world':['94','A4']},'native_s2c_by_phase':{'world':['AE','B0']},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':'none','shared_storage':['common directory authority required; no table added'],
        'native_form_qualifications':{'scoped_selectors':['19','23','24'],'B0_cursor_to_94_owner_field':True,
            'native_A4_signed_direction':True,'AE_same_owner_summary':True,'whole_opcode_variants_complete':False,
            'official_server_response_causality':False},'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['native_directory']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-directory-relations.json','scoped_selectors':['19','23','24'],
        'new_opcode_values':0,'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Continue concrete native directory business data/bounds and shared authority; preserve conditional source limitations. Continue actual login/world suppliers and general ready-world dispatcher.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':3,
        'native_functions':len(native),'primary_envelopes':len(envelopes),'new_partial_owner_chains':1,
        'new_phase_source_bindings':4,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
