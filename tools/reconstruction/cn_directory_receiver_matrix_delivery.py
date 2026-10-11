"""Seal complete B0consumer selector layouts and actual initialized row spans statically."""
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
NAME='cn-directory-receiver-matrix-01'
ROUND='20261007-cn-directory-receiver-matrix'
NEW=['src/cn/protocol/CnDirectoryReceiver.h']
MODIFIED=['src/cn/protocol/CnDirectoryWire.h','src/cn/world/SharedDirectory.cpp',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedDirectory.h','src/cn/protocol/CnCharacterSummary.h']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-directory-receiver-matrix-20261007.md',
    'tools/reconstruction/cn_directory_receiver_matrix_delivery.py']
FUNCTIONS=['005118e0','0050eb00','00515680','0074fc50']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog33-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog changed')
    known=json.loads(catalog);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=captured[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ValueError('Before source changed')
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Source before differs')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-33'})
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
        if len(code)!=size:raise ValueError('Missing primary bytes')
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(path),'declared_size_not_assumed_complete_body':True})
        pending.extend([(f'native/source/{address}.c',source,path),(f'native/declared-spans/{address}.bin',code,exe)])
    cfgs=[];envelopes=[];primary={}
    for lo,hi in [(0x5118e0,0x5126f8),(0x50eb00,0x50eb00+int(rows['0050eb00']['bytes']))]:
        code=pe.get_data(lo-base,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,{})
        if cfg['open_edges']:raise ValueError('Qualified CFG has an open edge')
        cfg['metadata_declared_size']=int(rows[f'{lo:08x}']['bytes']);cfgs.append(cfg);primary.update(ins)
        envelopes.append({'address':f'{lo:08x}','end_exclusive':f'{hi:08x}','bytes':len(code),
            'sha256':sha(code),'decoded_unique_cfg_bytes':cfg['decoded_unique_cfg_bytes']})
        pending.extend([(f'native/cfg/{lo:08x}.bin',code,exe),
            (f'native/cfg/{lo:08x}.asm',asm,'primary static recursive CFG, calls recorded but not followed')])
    # Retain actual source-call windows for the noncontiguous argument pushes,
    # not a count inferred from pages4 or a synthetic capacity assumption.
    clear_calls=[]
    for site,low in [(0x50eef9,0x50eec5),(0x50ef0c,0x50eefe),(0x50ef3c,0x50ef0c)]:
        ins=primary[site]
        if ins.mnemonic!='call' or ins.operands[0].type!=X86_OP_IMM or ins.operands[0].imm!=0x74fc50:
            raise ValueError('Primary memset call differs')
        window=[x for a,x in sorted(primary.items()) if low<=a<site+ins.size]
        asm=('\n'.join(f'{x.address:08x} {x.bytes.hex():24} {x.mnemonic:8} {x.op_str}' for x in window)+'\n').encode()
        pending.append((f'native/clear-calls/{site:08x}.asm',asm,'qualified subset of initializer CFG'))
        clear_calls.append({'callsite':f'{site:08x}','target':'0074FC50','source_window':f'{low:08x}',
            'sha256':sha(asm),'source_clear_bytes':2000})
    # The table is source accounting; primary-native origins and branch/clear
    # semantics remain explicitly separate in the raw C/CFG evidence above.
    source=(SERVER/NEW[0]).read_text(encoding='utf-8')
    expressions=re.findall(r'\{(0x[0-9a-f]+),Owner::(\w+),(0x[0-9a-f]+),(0x[0-9a-f]+),HighIndex::(\w+),(\d+),(\d+),(0x[0-9a-f]+|\d+)\}',source)
    layouts=[{'selector':f'{int(s,16):02X}','owner':owner,'row_base':f'{int(row,16):08X}',
        'metadata_base':f'{int(meta,16):08X}','nonempty_high_index':update,'pages_written':int(pages),
        'receive_clear_bytes':int(clear),'initial_cleared_row_bytes':int(initial,0) if initial.startswith('0x') else int(initial)}
        for s,owner,row,meta,update,pages,clear,initial in expressions]
    expected=['11','12','15','16','17','18','19','1B','21','22','23','24','27','28','2A','2B','2C','2D']
    if [r['selector'] for r in layouts]!=expected:raise ValueError('Source layout inventory differs from reviewed native branches')
    for name in ['cn-directory-display-fields-01','cn-native-directory-owner-01']:
        last=ROOT/name/'integration-manifest.json';b=last.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior evidence differs')
        old=json.loads(b)
        for span in native:
            same=next((x for x in old['declared_native_spans'] if x['address']==span['address']),None)
            if same and same['declared_span_sha256']!=span['declared_span_sha256']:raise ValueError('Prior primary span differs')
        pending.append((f'prior-manifests/{name}.json',b,last))
    facts={'client_sha256':PIN,'consumer':'005118E0','mode0_selectors':expected,'mode1_selectors':['19','23','24'],
        'consumer_mode_selector_variants':21,'consumer_opcode':'B0','complete_for_this_one_consumer_selector_switch':True,
        'other_world_receivers_or_all_gameplay_complete':False,'format':{'row_stride':40,'row_native_index_offset':32,
            'record_header_bytes':9,'record_total_size':'9+count*40','cursor_record_offset':5},
        'source_layouts':layouts,'empty_count_clears_high_index':True,
        'high_index_uses_last_row_not_max_of_all_rows':True,'rows27_28_share_base':True,
        'metadata27_28_2A_2B_2C_2D_alias':True,'native_receiver_checks_row_indices':False,
        'actual_initializer_memset_calls':clear_calls,'formal_native_allocation_capacity_proven':False,
        'existing_source_publication_scope':{'selectors':['19','23','24'],'row_indices_in_actual_initial_clear':[1,50],
            'source_scope_guard_not_native_all_variants_rule':True},'cfgs':cfgs,
        'new_receiver_layout_forms':15,'new_opcode_values':0,'new_phase_source_bindings':0,'new_complete_routes':0}
    pending.append(('native-directory-receiver-matrix.json',(json.dumps(facts,indent=2)+'\n').encode(),'primary static native/source accounting'))
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
    gaps=['Actual allocation capacities/larger row variants/business categories/shared directory authority remain unresolved.',
        'Initialized row span is a bounded source publication guard, not a complete native decoder bound or a success route.',
        'Only existing19/23/24 source owner is connected conditionally; other recovered receiver forms are not new handlers.',
        'Native full login/world suppliers/general ready-world dispatcher/production plan remain incomplete.',
        'Whole-game indirect/deferred/state/variant denominator and complete routes remain unresolved.']
    manifest={'kind':'complete pinned B0consumer mode/selector layout matrix +actual initialized row regions integrated into existing source publication guard',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'declared_native_spans':native,'native_code_envelopes':envelopes,'client_sha256':PIN,
        'modified_cpp_files':2,'new_cpp_files':1,'modified_catalog_tools':1,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'new_receiver_layout_forms':15,'qualified_consumer_mode_selector_variants':21,
        'formal_native_allocation_capacity_proven':False,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog33 native ProgramMsg/header/renderer statistics and exact points-label aliases sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed',
            'deployed','production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN complete B0consumer receiver layout matrix and actual initial-row source region',
        'version_scope':'cn','status':'已恢復此B0consumer mode0十八/mode1三種布局，接既有三channel初始化列區域；其他權威handler與全遊戲未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['native cache alias layouts, no gameplay tables added'],
        'native_form_qualifications':{'this_one_B0consumer_selector_switch_complete':True,
            'mode_selector_variant_count':21,'native_full_allocation_capacity':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['directory_receiver_matrix']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-directory-receiver-matrix.json','consumer_mode_selector_variants':21,
        'new_opcode_values':0,'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Continue actual directory category/state producers and common backend, retain distinct row/metadata aliases and cleared-span scope. Continue native login/world suppliers and general ready-world source.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':1,'modified_cpp_files':2,
        'receiver_layouts':18,'mode_selector_variants':21,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
