"""Seal static AF native recovery and conditional common directory source owner."""
import csv
import json
import re
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-generic-directory-owner-01'
ROUND='20261007-cn-generic-directory-owner'
NEW=['src/cn/protocol/CnGenericDirectoryWire.h','src/cn/world/SharedGenericDirectory.h','src/cn/world/SharedGenericDirectory.cpp']
MODIFIED=['tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/protocol/CnDirectorySelection.h','src/cn/protocol/CnDirectoryReceiver.h',
    'src/cn/protocol/CnCharacterSummary.h','src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/protocol/CnTransport.h','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-generic-directory-owner-20261007.md',
    'tools/reconstruction/cn_generic_directory_owner_delivery.py']
FUNCTIONS=['0048fcc0','0050e3b0','0050eb00','00511290','00512c50','00513c40','00524e10','0074f150']
SELECTORS=['00','01','02','03','04','05','06','07','08','09','0A','0B','0C','0E','0F','10','13','14','1E','1F','20','29']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog35-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=before[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ValueError('Before source differs')
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Before differs from catalog')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-35'})
    for rel in CONTEXT:
        b=(SERVER/rel).read_bytes()
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Unchanged context differs '+rel)
        unchanged.append({'path':rel,'sha256':sha(b),'previously_cataloged':rel in known})
    for rel in NEW:
        if rel in known:raise ValueError('Claimed new source already cataloged')
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
        if len(code)!=size:raise ValueError('Missing native bytes')
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(path),'declared_size_not_assumed_complete_body':True})
        pending.extend([(f'native/source/{address}.c',source,path),(f'native/declared-spans/{address}.bin',code,exe)])
    cfgs=[];envelopes=[];primary={}
    for low in [0x50eb00,0x511290,0x512c50,0x513c40,0x524e10,0x49020b,0x490227]:
        high=low+int(rows[f'{low:08x}']['bytes']) if low>=0x500000 else (0x490227 if low==0x49020b else 0x49022b)
        code=pe.get_data(low-base,high-low);cfg,asm,ins=trace(md,code,low,high,{})
        expected=[] if low>=0x500000 else [{'address':'00490ab1' if low==0x49020b else '0049020d',
            'kind':'outside_qualified_code_envelope'}]
        if cfg['open_edges']!=expected:raise ValueError('Unexpected qualified CFG frontier')
        cfg['bounded_dispatcher_branch_only']=low<0x500000;cfgs.append(cfg);primary.update(ins)
        envelopes.append({'address':f'{low:08x}','end_exclusive':f'{high:08x}','bytes':len(code),'sha256':sha(code),
            'decoded_unique_cfg_bytes':cfg['decoded_unique_cfg_bytes'],'bounded_branch_only':low<0x500000})
        pending.extend([(f'native/cfg/{low:08x}.bin',code,exe),
            (f'native/cfg/{low:08x}.asm',asm,'primary static CFG; calls recorded, not followed')])
    for site,target in [(0x49021d,0x511290),(0x511516,0x74f150),(0x511575,0x74f150),
        (0x511529,0x512c50),(0x511593,0x512c50),(0x50edf3,0x74fc50)]:
        ins=primary[site]
        if ins.mnemonic!='call' or ins.operands[0].type!=X86_OP_IMM or ins.operands[0].imm!=target:
            raise ValueError('Pinned callsite differs')
    for site,operand in [(0x49020b,'1'),(0x490227,'2'),(0x50edc1,'0xb538')]:
        ins=primary[site]
        if (ins.mnemonic,ins.op_str)!=('push',operand):raise ValueError('Pinned native argument differs')
    for name in ['cn-directory-selection-producer-01','cn-directory-receiver-matrix-01','cn-native-directory-owner-01']:
        path=ROOT/name/'integration-manifest.json';b=path.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Previous evidence differs')
        old=json.loads(b)
        for span in native:
            same=next((x for x in old['declared_native_spans'] if x['address']==span['address']),None)
            if same and same['declared_span_sha256']!=span['declared_span_sha256']:raise ValueError('Prior primary differs')
        pending.append((f'prior-manifests/{name}.json',b,path))
    for suffix in ['102','129','203']:
        path=CN/f'artifacts/native/20261006-cn-dispatch-01/branches/0048fcc0-switch-0-case-{suffix}.c.txt'
        pending.append((f'native/branches/{path.name}',path.read_bytes(),path))
    # Static source inventory only; this does not execute either client, C++
    # reader/owner, native gameplay or a request/response simulation.
    origin_source=(SERVER/'src/cn/protocol/CnDirectorySelection.h').read_text(encoding='utf-8')
    origins=re.findall(r'\{(true|false),(0x[0-9a-f]+),(\d+),(std::nullopt|\d+),(0x[0-9a-f]+)\}',origin_source)
    mode0={int(row[-1],16) for row in origins if row[0]=='false'}
    receiver_source=(SERVER/'src/cn/protocol/CnDirectoryReceiver.h').read_text(encoding='utf-8')
    b0={int(s,16) for s in re.findall(r'\{(0x[0-9a-f]+),Owner::',receiver_source)}
    supplied=sorted(mode0-b0-{0x25,0x26,0x27,0x28})
    if [f'{s:02X}' for s in supplied]!=SELECTORS:raise ValueError('Scope inventory differs from reviewed source')
    facts={'client_sha256':PIN,'C2S_opcode':'94','S2C_opcode':'AF','phase':'world-connection-1',
        'consumer':'00511290','consumer_tag':1,'source_mode_bit0':False,'source_selectors':SELECTORS,
        'new_complete_routes':0,'new_opcode_values':0,'source_scoped_selector_count':22,
        'AF_consumer_format_selector_domain':[0,45],'formal_native_allocation_capacity_proven':False,
        'format':{'record_size':'9+count*(selector14?24:20)','total_size_u16_offset':1,'selector_offset':3,
            'count_offset':4,'header_dword_offset':5,'rows_offset':9,'row_text_bytes':[0,16],
            'row_value_bits_offset':16,'special14_display_word_offset':20,'special14_opaque_tail':[22,2]},
        'copy_bytes':'BlockSize-1; includes8byte payload header',
        'generic_copy_destination':'player+22D08+selector*3F0','generic94_cursor':'same destination+4',
        'special14_copy_destination':'player+301C4','special14_count_destination':'player+301B8',
        'special14_AF_dword_destination':'player+301C8','special14_94_cursor_source':'player+27BCC',
        'special14_cursor_alias_proven':False,'special14_empty_text_fallback_pointer':'009F097C',
        'special14_native_capacity_or_fallback_storage_proven':False,
        'generic_initial_clear':{'callsite':'0050EDF3','start':'player+22CF0','bytes':0xb538,
            'summary_bytes':24,'slots':46,'slot_bytes':0x3f0,'normal_source_publication_count_max':50,
            'source_scope_guard_not_global_native_capacity':True},
        'same_opcode_reply94_is_different_consumer':True,'unrelated_S2C94_consumer':'00524E10',
        'F9_tag2_contract_not_AF':True,'F9_gameplay_source_added':False,
        'actual_common_backend_implemented':False,'official_response_causality_or_order_recovered':False,'cfgs':cfgs}
    pending.append(('native-generic-directory-relations.json',(json.dumps(facts,indent=2)+'\n').encode(),'primary static/source accounting'))
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
    gaps=['Actual shared directory data/score/sort/permissions/revision/native field issuance still missing.',
        'Normal50row source initialized-slot limit is not a global native capacity; special14 capacity/fallback strings remain mandatory supplier qualification.',
        'F9/D1/AE/B1, general pagination, other producers and mode1 variants are not complete.',
        'Application general ready-world dispatcher and full native login-world suppliers remain incomplete.',
        'Whole-game state/variant/direction denominator and complete routes remain unresolved.']
    manifest={'kind':'actual admitted mode0 common actor ->scoped94 ->required common owner ->complete suppliedAF ->same transport conditional source',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'declared_native_spans':native,'native_code_envelopes':envelopes,'client_sha256':PIN,
        'new_cpp_files':3,'modified_cpp_files':0,'modified_catalog_tools':1,'source_owner_chains_added':1,
        'new_phase_opcode_bindings':2,'new_opcode_values':0,'source_scoped_selector_count':22,'new_complete_routes':0,
        'formal_application_hosted':False,'actual_common_directory_backend_implemented':False,
        'native_server_response_causality_recovered':False,'all_native_capacity_bounds_recovered':False,
        'previous_goal_turn_classification':'progress: catalog35 exact native UI-selection/94 producer source descriptors sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN generic native directory94/AF and admitted common owner source',
        'version_scope':'cn','status':'已接mode0二十二種selector的94/必要共用owner/AF來源；實際backend與正式掛載未完成',
        'native_c2s_by_phase':{'world':['94']},'native_s2c_by_phase':{'world':['AF']},'source_paths':SOURCES,
        'source_owner_chains_added':1,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none','shared_storage':['real common directory authority required; no gameplay table added'],
        'native_form_qualifications':{'scoped_selectors':SELECTORS,'native_AF_generic_row_bytes':20,
            'special14_row_bytes':24,'whole_opcode_variants_complete':False,'official_server_response_causality':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['generic_directory']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-generic-directory-relations.json','scoped_selectors':SELECTORS,
        'new_opcode_values':0,'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Continue actual native directory labels/data authority and generic pagination; special14 capacity/fallback; F9/D1 contracts. Continue native login-world suppliers/general source dispatcher.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':3,
        'native_functions':len(native),'primary_envelopes':len(envelopes),'new_partial_owner_chains':1,
        'new_phase_source_bindings':2,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
