"""Seal fixed F9/tag2 evidence and conditional admitted common D1 directory source."""
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
NAME='cn-special-directory-owner-01'
ROUND='20261007-cn-special-directory-owner'
NEW=['src/cn/protocol/CnSpecialDirectoryWire.h','src/cn/world/SharedSpecialDirectory.h','src/cn/world/SharedSpecialDirectory.cpp']
MODIFIED=['tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/protocol/CnDirectorySelection.h','src/cn/protocol/CnCharacterSummary.h',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/cn/protocol/CnTransport.h',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/db/NativeNpcDisplayCatalog.h']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-special-directory-owner-20261007.md',
    'tools/reconstruction/cn_special_directory_owner_delivery.py']
FUNCTIONS=['0048fcc0','00428c80','0042eac0','0050e3b0','0050eb00','00511290','00514060',
    '005142d0','00515f80','00515680','00567b50']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog36-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=before[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ValueError('Before source differs')
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Before differs from catalog')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-36'})
    for rel in CONTEXT:
        b=(SERVER/rel).read_bytes()
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Unchanged source differs '+rel)
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
        if len(code)!=size:raise ValueError('Missing declared native bytes')
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(path),'declared_size_not_assumed_complete_body':True})
        pending.extend([(f'native/source/{address}.c',source,path),(f'native/declared-spans/{address}.bin',code,exe)])
    old_manifests={};switches={};tables=[]
    for name in ['cn-directory-selection-producer-01','cn-directory-display-fields-01',
        'cn-native-directory-owner-01','cn-generic-directory-owner-01']:
        path=ROOT/name/'integration-manifest.json';b=path.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Previous evidence differs')
        old=json.loads(b);old_manifests[name]=old
        for span in native:
            same=next((x for x in old['declared_native_spans'] if x['address']==span['address']),None)
            if same and same['declared_span_sha256']!=span['declared_span_sha256']:raise ValueError('Prior primary span differs')
        pending.append((f'prior-manifests/{name}.json',b,path))
        for table in old.get('primary_switch_tables',[]):
            if 'callsite' not in table:continue
            site=int(table['callsite'],16)
            if site not in [0x50e442,0x516023,0x5160b8,0x515ce8,0x515e2f,0x515e5a]:continue
            data=pe.get_data(int(table['table_va'],16)-base,table['entries']*4)
            if sha(data)!=table['sha256']:raise ValueError('Prior qualified table differs')
            if site not in switches:
                switches[site]=[int(x,16) for x in table['targets']];tables.append(table)
                pending.append((f'native/tables/{table["table_va"]}.bin',data,exe))
    cfgs=[];envelopes=[];primary={}
    for low,high in [(0x428c80,0x428c80+int(rows['00428c80']['bytes'])),
        (0x42eac0,0x42eeed),(0x50eb00,0x50eb00+int(rows['0050eb00']['bytes'])),
        (0x50e3b0,0x50e542),(0x511290,0x5115a1),(0x514060,0x5142c8),(0x5142d0,0x51460b),
        (0x515f80,0x516e5c),(0x515680,0x515eeb),(0x49020b,0x490227),(0x490227,0x49022b)]:
        code=pe.get_data(low-base,high-low);cfg,asm,ins=trace(md,code,low,high,switches)
        expected=[] if low>=0x500000 or low in [0x428c80,0x42eac0] else [{'address':
            '00490ab1' if low==0x49020b else '0049020d','kind':'outside_qualified_code_envelope'}]
        if cfg['open_edges']!=expected:raise ValueError('Unexpected CFG frontier')
        cfg['bounded_dispatcher_branch_only']=low in [0x49020b,0x490227];cfgs.append(cfg);primary.update(ins)
        envelopes.append({'address':f'{low:08x}','end_exclusive':f'{high:08x}','bytes':len(code),'sha256':sha(code),
            'decoded_unique_cfg_bytes':cfg['decoded_unique_cfg_bytes'],'bounded_branch_only':cfg['bounded_dispatcher_branch_only']})
        pending.extend([(f'native/cfg/{low:08x}.bin',code,exe),
            (f'native/cfg/{low:08x}.asm',asm,'primary static CFG; calls recorded, not followed')])
    for site,target in [(0x49021d,0x511290),(0x428fd4,0x42eac0)]:
        ins=primary[site]
        if ins.mnemonic!='call' or ins.operands[0].type!=X86_OP_IMM or ins.operands[0].imm!=target:
            raise ValueError('Pinned native call differs')
    # Exact fixed S2C size comes from the primary opcode lookup, not count.
    length_branches=[]
    for opcode,expected_length in [(0xd1,21),(0xf9,2105)]:
        table_va=0x567ca4+4*opcode;entry=pe.get_data(table_va-base,4);target=struct.unpack('<I',entry)[0]
        code=pe.get_data(target-base,7)
        if code[0]!=0xb8 or struct.unpack_from('<i',code,1)[0]!=expected_length:
            raise ValueError('Pinned fixed length differs')
        length_branches.append({'opcode':f'{opcode:02X}','direction':'S2C','length':expected_length,
            'lookup_function':'00567B50','entry_va':f'{table_va:08X}','target_va':f'{target:08X}',
            'branch_sha256':sha(code)})
        pending.extend([(f'native/length/{opcode:02X}-entry.bin',entry,exe),(f'native/length/{opcode:02X}-branch.bin',code,exe)])
    resource_dir=CN/'artifacts/native/20261006-cn-account-phase-01'
    receipt_bytes=(resource_dir/'account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_bytes)
    decoded=(resource_dir/'message.csv').read_bytes()
    if receipt['client_sha256']!=PIN or sha(decoded)!=receipt['asset']['decoded_sha256'] or receipt['asset']['codepage']!=936:
        raise ValueError('Retained text receipt differs')
    program={};section=None;has_npc=False
    for number,row in enumerate(csv.reader(decoded.decode('cp936').splitlines()),1):
        if not row or not row[0].strip():continue
        first=row[0].strip()
        if not first.isdigit():section=first;has_npc|=section=='NPCAppearData';continue
        if section=='ProgramMsg':
            ident=int(first)
            if ident in program:raise ValueError('Duplicate ProgramMsg ID')
            program[ident]={'row':number,'text':row[1] if len(row)>1 else ''}
    headers=[]
    for va,expected_ids in [(0x8a0048,[883,884,885,9]),(0x8a0050,[898,899,9,904])]:
        data=pe.get_data(va-base,8);ids=list(struct.unpack('<4H',data))
        if ids!=expected_ids:raise ValueError('Pinned header IDs differ')
        headers.append({'va':f'{va:08X}','ids':ids,'ProgramMsg_rows':[program[i] for i in ids]})
        pending.append((f'native/data/{va:08x}.bin',data,exe))
    literals=[]
    for va in [0x7ee8e4,0x7f4f2c,0x7f4f38,0x7f4f48,0x7f4f50,0x7f4f68,0x7f4f8c]:
        data=pe.get_data(va-base,100).split(b'\0',1)[0]+b'\0'
        literals.append({'va':f'{va:08X}','cp936_text':data[:-1].decode('cp936'),'sha256':sha(data)})
        pending.append((f'native/strings/{va:08x}.bin',data,exe))
    pending.extend([('native/resources/account-phase-evidence.json',receipt_bytes,resource_dir/'account-phase-evidence.json'),
        ('native/resources/message.csv',decoded,resource_dir/'message.csv')])
    path=CN/'artifacts/native/20261006-cn-dispatch-01/branches/0048fcc0-switch-0-case-203.c.txt'
    pending.append((f'native/branches/{path.name}',path.read_bytes(),path))
    facts={'client_sha256':PIN,'C2S_opcode':'D1','S2C_opcode':'F9','phase':'world-connection-1',
        'source_selectors':['25','26'],'source_native_mode_bit0':False,'length_branches':length_branches,
        'fixed_F9_record_bytes':2105,'record_offsets':{'selector':1,'page':2,'count':3,'opaque':4,'rows':5},
        'row_strides':{'25':84,'26':56},'remaining_tail_is_not_zero_filled':True,
        'source_byte_bound_count_max':{'25':25,'26':37},'official_count_limit_recovered':False,
        '25_sentinel_dword_offset':4,'25_lookup_word_offset':4,'25_stops_before_copying_sentinel':True,
        '25_lookup_resource':{'section':'NPCAppearData','loader':'0042EAC0','dispatch':'00428FD4',
            'max_selector_offset':'000124E0','row_base_offset':'000124E2','row_stride':94,'text_offset':0,
            'actual_CN_decoded_resource_or_common_mapping_recovered':False},
        'resource_message_csv_has_NPCAppearData_section':has_npc,'not_a_whole_asset_absence_claim':True,
        'copy_bases':{'25_rows':'indirect+4F90+page*25*84','25_names':'indirect+4D14+page*25*16',
            '26_rows':'indirect+8A7C+page*25*56'},
        'renderer_bases':{'25_rows':'indirect+57C4+(page-1)*25*84','25_names':'indirect+4EA4+(page-1)*25*16',
            '26_rows':'indirect+8FF4+(page-1)*25*56'},
        'initialized_source_scope_rows':146,'formal_native_allocation_capacity_proven':False,
        '25_row_text_regions':[[8,20],[28,16],[44,36]],'26_row_text_regions':[[1,15],[17,15],[33,15]],
        '26_last_column_signed_dword_offset':52,'native_star_bounty_business_rules_recovered':False,
        'monster_double_attack_defense_or_skill_data_recovered':False,'headers':headers,'literals':literals,
        'actual_common_backend_implemented':False,'official_response_causality_recovered':False,
        'new_opcode_values':0,'new_complete_routes':0,'cfgs':cfgs,'tables':tables}
    pending.append(('native-special-directory-relations.json',(json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode(),'primary static/source accounting'))
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
    gaps=['Real common star/bounty data/permissions/issuance/accounting/storage backend remains missing.',
        'CN actual NPCAppearData decoded resource/name projection and TW/common key mapping remain unqualified.',
        '146-row initialized source scope is not a global native capacity; other D1/F9/B0/94 variants and official cause/order remain open.',
        'Actual Application ready-world general dispatcher and native full login-world suppliers remain incomplete.',
        'Whole-game state/variant/direction denominator and complete routes remain unresolved.']
    manifest={'kind':'actual admitted mode0 common actor ->native D1(25/26) ->required authority ->fixed full F9 and qualified25 NPC names ->same transport conditional source',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'declared_native_spans':native,'native_code_envelopes':envelopes,'primary_switch_tables':tables,'client_sha256':PIN,
        'new_cpp_files':3,'modified_cpp_files':0,'modified_catalog_tools':1,'source_owner_chains_added':1,
        'new_phase_opcode_bindings':2,'new_opcode_values':0,'source_scoped_selectors':['25','26'],'new_complete_routes':0,
        'formal_application_hosted':False,'actual_common_backend_implemented':False,'all_native_capacity_bounds_recovered':False,
        'previous_goal_turn_classification':'progress: catalog36 bounded94/AF common-lease owner and20/24-byte formats sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native special directory D1/F9 admitted common owner and required NPC name projection',
        'version_scope':'cn','status':'已接mode0兩selector的D1/必要共用owner/完整F9來源；權威backend、CN名稱來源與正式掛載未完成',
        'native_c2s_by_phase':{'world':['D1']},'native_s2c_by_phase':{'world':['F9']},'source_paths':SOURCES,
        'source_owner_chains_added':1,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none','shared_storage':['real common star/bounty authority required; no duplicate regional table or gameplay data created'],
        'native_form_qualifications':{'scoped_selectors':['25','26'],'fixed_F9_bytes':2105,'row_strides':[84,56],
            'whole_opcode_variants_complete':False,'official_server_response_causality':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['special_directory']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-special-directory-relations.json','source_selectors':['25','26'],'new_opcode_values':0,
        'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Continue actual CN resource names/common mapping and star/bounty authority, D1(27/28)/B0/94 and B1 refresh; complete native login/world suppliers/general dispatcher.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':3,
        'native_functions':len(native),'primary_envelopes':len(envelopes),'new_partial_owner_chains':1,
        'new_phase_source_bindings':2,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
