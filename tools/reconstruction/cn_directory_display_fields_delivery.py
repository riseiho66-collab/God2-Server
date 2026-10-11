"""Recover mode1 directory display field aliases from pinned code and retained text."""
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
NAME='cn-directory-display-fields-01'
ROUND='20261007-cn-directory-display-fields'
MODIFIED=['src/cn/protocol/CnDirectoryWire.h','tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedDirectory.h','src/cn/world/SharedDirectory.cpp',
    'src/cn/protocol/CnCharacterSummary.h','src/cn/net/SharedCredentialConnection.h']
SOURCES=MODIFIED+CONTEXT+['docs/research/cn-directory-display-fields-20261007.md',
    'tools/reconstruction/cn_directory_display_fields_delivery.py']
FUNCTIONS=['00428c80','0050eb00','00510e80','00511620','005118e0','005131a0','005137b0','00515f80']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed during source work')
    catalog=(out/'catalog32-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=captured[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ValueError('Before source changed')
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Source prior differs')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-32'})
    for rel in CONTEXT:
        b=(SERVER/rel).read_bytes()
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Unchanged source differs '+rel)
        unchanged.append({'path':rel,'sha256':sha(b),'previously_cataloged':rel in known})
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
        if not match or int(match[1],16)!=int(address,16):raise ValueError('Source metadata differs')
        size=int(match[2]);code=pe.get_data(int(address,16)-base,size)
        if len(code)!=size:raise ValueError('Missing declared bytes')
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(path),'declared_size_not_assumed_complete_body':True})
        pending.extend([(f'native/source/{address}.c',source,path),(f'native/declared-spans/{address}.bin',code,exe)])
    switches={};tables=[]
    for site,table,count in [(0x5132b1,0x513780,12),(0x516023,0x516e5c,3),(0x5160b8,0x516e88,29)]:
        data=pe.get_data(table-base,count*4);targets=list(struct.unpack('<'+'I'*count,data));switches[site]=targets
        pending.append((f'native/tables/{table:08x}.bin',data,exe))
        tables.append({'callsite':f'{site:08x}','table_va':f'{table:08x}','entries':count,
            'targets':[f'{x:08x}' for x in targets],'sha256':sha(data)})
    selector=pe.get_data(0x516e68-base,30)
    if max(selector)>=3:raise ValueError('Title selector exceeds domain')
    pending.append(('native/tables/00516e68.bin',selector,exe))
    tables.append({'table_va':'00516e68','bytes':30,'selector_hex':selector.hex(),'sha256':sha(selector)})
    cfgs=[];envelopes=[];primary={}
    for lo,hi in [(0x428c80,0x428c80+int(rows['00428c80']['bytes'])),
        (0x50eb00,0x50eb00+int(rows['0050eb00']['bytes'])),
        (0x5131a0,0x513780),(0x5137b0,0x513a30),(0x515f80,0x516e5c)]:
        code=pe.get_data(lo-base,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,switches)
        if cfg['open_edges']:raise ValueError('Qualified local CFG has an open edge')
        cfg['metadata_declared_size']=int(rows[f'{lo:08x}']['bytes'])
        cfgs.append(cfg);primary.update(ins)
        envelopes.append({'address':f'{lo:08x}','end_exclusive':f'{hi:08x}','bytes':len(code),'sha256':sha(code),
            'decoded_unique_cfg_bytes':cfg['decoded_unique_cfg_bytes'],'metadata_declared_size':cfg['metadata_declared_size']})
        pending.extend([(f'native/cfg/{lo:08x}.bin',code,exe),
            (f'native/cfg/{lo:08x}.asm',asm,'primary static CFG with explicit qualified tables')])
    required={0x4294cb:('mov','ecx, 0x7ee944'),0x42951d:('mov','dword ptr [esi + 0xb2f60], eax'),
        0x51323c:('push','dword ptr [esi + 0x30e90]'),0x513242:('push','dword ptr [esi + 0x30e8c]'),
        0x513248:('push','dword ptr [esi + 0x30e88]'),0x51325f:('push','dword ptr [esi + 0x30e88]'),
        0x513265:('push','0x7f4de4')}
    for address,(mnemonic,operand) in required.items():
        ins=primary[address]
        if (ins.mnemonic,ins.op_str)!=(mnemonic,operand):raise ValueError('Primary field alias differs')
    resource_dir=CN/'artifacts/native/20261006-cn-account-phase-01'
    asset_receipt=(resource_dir/'account-phase-evidence.json').read_bytes();receipt=json.loads(asset_receipt)
    if receipt['client_sha256']!=PIN:raise ValueError('Prior resource client differs')
    decoded_path=resource_dir/'message.csv';decoded=decoded_path.read_bytes();asset_path=Path(receipt['asset']['path']);asset=asset_path.read_bytes()
    if sha(decoded)!=receipt['asset']['decoded_sha256'] or sha(asset)!=receipt['asset']['sha256']:
        raise ValueError('Pinned text resource differs')
    if receipt['asset']['codepage']!=936:raise ValueError('Text encoding differs')
    csv_rows=list(csv.reader(decoded.decode('cp936').splitlines()));program={};section=None;declared=None
    for number,row in enumerate(csv_rows,1):
        if not row or not row[0].strip():continue
        first=row[0].strip()
        if not first.isdigit():
            section=first
            if section=='ProgramMsg':declared=int(row[1])
            continue
        if section=='ProgramMsg':
            ident=int(first)
            if ident in program:raise ValueError('Duplicate ProgramMsg ID')
            program[ident]={'row':number,'text':row[1] if len(row)>1 else ''}
    data_ids=pe.get_data(0x8a0100-base,8);ids=list(struct.unpack('<4H',data_ids))
    if ids!=[444,865,446,153]:raise ValueError('Pinned mode1 title IDs differ')
    selected={str(i):program[i] for i in [9,153,444,446,748,749,865]}
    literals=[]
    for va in [0x7ee944,0x7f4d38,0x7f4d50,0x7f4d44,0x7ed65c,0x7f4dd4,0x7f4de4,0x7f4df0]:
        data=pe.get_data(va-base,100).split(b'\0',1)[0]+b'\0'
        pending.append((f'native/strings/{va:08x}.bin',data,exe))
        literals.append({'va':f'{va:08x}','bytes':len(data),'sha256':sha(data),'cp936_text':data[:-1].decode('cp936')})
    for va,size in [(0x8a0100,8),(0x89ff64,24)]:
        pending.append((f'native/data/{va:08x}.bin',pe.get_data(va-base,size),exe))
    pending.extend([('native/resources/account-phase-evidence.json',asset_receipt,resource_dir/'account-phase-evidence.json'),
        ('native/resources/message.csv',decoded,decoded_path),('native/resources/message.csvZ',asset,asset_path)])
    last=ROOT/'cn-native-directory-owner-01/integration-manifest.json';b=last.read_bytes()
    if sha(b)!=ledger['cn_account_admission_evidence']['cn-native-directory-owner-01']['artifact_sha256']['integration-manifest.json']:
        raise ValueError('Prior native directory evidence differs')
    old=json.loads(b)
    for span in native:
        same=next((x for x in old['declared_native_spans'] if x['address']==span['address']),None)
        if same and same['declared_span_sha256']!=span['declared_span_sha256']:raise ValueError('Prior shared native bytes differ')
    pending.append(('prior-manifests/cn-native-directory-owner-01.json',b,last))
    facts={'client_sha256':PIN,'mode_scope':'native07 flags bit0 equals1; UIstate2F; selectors19/23/24',
        'mode_bit0_business_meaning_recovered':False,'programmsg_declared_count':declared,'programmsg_id1240_present':1240 in program,
        'programmsg_rows':selected,'mode1_title_ids':ids,'mode1_title_words_va':'008A0100',
        'programmsg_pointer_owner':'resource+B2F60;0042951D after ProgramMsg match004294CB',
        'mode1_header_owner':'0050EB00 ->009F0868/6C/70/74 ->00515F80 state2F ->columns1..4',
        'B0_mode1_row':{'first_text_range':[0,16],'first_text_label_id':444,
            'second_text_range':[16,16],'second_text_label_id':865,'common_affiliation_identity_recovered':False,
            'wins_word_offset':34,'losses_word_offset':36,'draws_word_offset':38,
            'total_matches_native_expression':'WORD34+WORD36; no WORD38',
            'points_label_id':153,'points_label_source_offset':34,'independent_points_field_recovered':False},
        'AE_mode1_selector19':{'subtype':8,'wins_payload_offset':4,'losses_payload_offset':8,'draws_payload_offset':12,
            'display_format_signed_dword':True,'points_literal_va':'007F4DE4','points_label_payload_offset':4,
            'payload16_score_field_proven':False,'remaining_opaque_ranges':[[0,4],[16,8]],
            'native_points_formula_recovered':False},
        'capacity_frontier':{'selector19_base':'00030E74','different_selector1B_base':'0003166C',
            'difference_bytes':0x3166c-0x30e74,'stride':40,'row51_hits_other_header':True,
            'client_array_capacity50_proven':False,'pages4_proves_capacity100':False},
        'literals':literals,'cfgs':cfgs,'tables':tables,'new_complete_routes':0}
    pending.append(('native-directory-display-fields.json',(json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode(),'static primary/text resource analysis'))
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
                'bytes':path.stat().st_size,'original':'captured before source adaptation'})
    gaps=['Concrete directory/ranking category, native row capacities,洞府 common identity, authoritative scoring/sorting/permissions remain unresolved.',
        'Display points aliases wins in this mode; do not derive server score or fill AEpayload16 from it.',
        'Other mode0 fields and AEselector23/24 summary meanings remain open.',
        'Production native login/world suppliers, common backend and ready-world general dispatcher remain incomplete.',
        'Whole-game indirect/deferred/state/variant denominator and complete routes remain unresolved.']
    manifest={'kind':'primary ProgramMsg loader/header/renderer ->mode1 native row statistics and personal summary display aliases in existing wire source',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'declared_native_spans':native,'native_code_envelopes':envelopes,'primary_switch_tables':tables,
        'client_sha256':PIN,'modified_cpp_files':1,'modified_catalog_tools':1,'new_cpp_files':0,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'mode1_row_display_semantics_recovered':True,'mode1_personal_summary_alias_recovered':True,
        'native_business_scoring_or_rank_rules_recovered':False,'full_native_array_capacity_recovered':False,
        'formal_application_hosted':False,'previous_goal_turn_classification':'progress: catalog32 conditional common directory owner and94/A4/AE/B0 source with three selectors sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed',
            'deployed','production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN mode1 directory native ProgramMsg and exact result display aliases',
        'version_scope':'cn','status':'已把mode1清單勝負和/總場次與原生積分標籤重用接入現有格式view；權威業務與正式路徑未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['native display aliases do not establish common PvP counters or score; no table added'],
        'native_form_qualifications':{'mode1_row_result_display':True,'mode1_personal_summary_display':True,
            'independent_points_field':False,'business_scoring_rules':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['directory_mode1_display']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-directory-display-fields.json','new_opcode_values':0,'complete_gameplay_routes':0,
        'independent_points_recovered':False,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Follow actual category/state/header writes and native row capacities to concrete shared authority; preserve mode1 display aliases and actual07 mode ownership. Continue login/world suppliers and actual general ready-world dispatcher.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'modified_cpp_files':1,
        'native_functions':len(native),'primary_cfgs':len(cfgs),'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
