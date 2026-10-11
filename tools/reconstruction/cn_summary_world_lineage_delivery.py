"""Static primary world-mode/fragment recovery and common offered-source sealing."""
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

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-summary-world-lineage-01'
ROUND='20261007-cn-summary-world-lineage'
MODIFIED=['src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/auth/SharedAccountSelection.cpp','src/cn/auth/SharedWorldSelection.h',
    'src/cn/auth/SharedWorldSelection.cpp','src/cn/protocol/CnCharacterSummary.h',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSuccess.h',
    'src/cn/auth/SharedAccountSuccess.cpp','src/cn/auth/SharedLoginComposition.h',
    'src/cn/auth/SharedLoginComposition.cpp','src/cn/net/SharedCredentialServer.h',
    'src/cn/net/SharedCredentialServer.cpp','src/cn/net/CnTransportSession.h',
    'src/cn/net/CnTransportSession.cpp','src/db/RecoveredCharacterRepository.h']
SOURCES=MODIFIED+CONTEXT+['docs/research/cn-summary-world-lineage-20261007.md',
    'tools/reconstruction/cn_summary_world_lineage_delivery.py']
FUNCTIONS=['00445040','00449310','0044d5f0','00481640','0048caa0','004ac850','004b09c0',
    '0050e3b0','0050e5e0','0050e9f0','00511620','00481440']

def trace(md,code,low,high,switches):
    """Decode CFG bytes only; no instruction execution/constant interpretation."""
    queued=[low];instructions={};edges=[];open_edges=[]
    while queued:
        address=queued.pop()
        if address in instructions:continue
        if not low<=address<high:
            open_edges.append({'address':f'{address:08x}','kind':'outside_qualified_code_envelope'});continue
        for old in instructions.values():
            if old.address<address<old.address+old.size:raise ValueError('Overlapping instruction entry')
        found=list(md.disasm(code[address-low:address-low+15],address,count=1))
        if not found or address+found[0].size>high:raise ValueError('Truncated CFG instruction')
        ins=found[0];instructions[address]=ins
        nxt=address+ins.size;targets=[]
        if ins.mnemonic.startswith('ret'):continue
        if ins.mnemonic=='jmp':
            if ins.operands[0].type==X86_OP_IMM:targets=[(ins.operands[0].imm,'direct_jump')]
            elif address in switches:targets=[(x,'qualified_switch') for x in switches[address]]
            else:open_edges.append({'address':f'{address:08x}','kind':'unresolved_indirect_jump'});continue
        elif ins.mnemonic.startswith('j') or ins.mnemonic.startswith('loop'):
            if ins.operands[0].type!=X86_OP_IMM:raise ValueError('Unsupported conditional branch')
            targets=[(ins.operands[0].imm,'conditional'),(nxt,'fallthrough')]
        else:
            if ins.mnemonic=='call':
                edges.append({'source':f'{address:08x}','kind':'call_not_followed',
                    'target':f'{ins.operands[0].imm:08x}' if ins.operands[0].type==X86_OP_IMM else ins.op_str})
            targets=[(nxt,'fallthrough')]
        for target,kind in targets:
            edges.append({'source':f'{address:08x}','kind':kind,'target':f'{target:08x}'})
            queued.append(target)
    covered=sum(i.size for i in instructions.values())
    asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
        for i in sorted(instructions.values(),key=lambda x:x.address))+'\n').encode()
    return {'entry':f'{low:08x}','code_envelope_end_exclusive':f'{high:08x}',
        'decoded_cfg_instructions':len(instructions),'decoded_unique_cfg_bytes':covered,
        'edges':edges,'open_edges':open_edges},asm,instructions

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed during source adaptation')
    catalog=(out/'catalog30-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog changed')
    known=json.loads(catalog);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[];pending=[]
    for rel in MODIFIED:
        raw=(out/'prior-sources'/rel).read_bytes();row=captured[rel]
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('Before source changed '+rel)
        if rel in known and sha(raw)!=known[rel]['sha256']:raise ValueError('Prior source changed '+rel)
        adaptations.append({'path':rel,'before_sha256':sha(raw),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-30'})
    for rel in CONTEXT:
        raw=(SERVER/rel).read_bytes()
        if rel in known and sha(raw)!=known[rel]['sha256']:raise ValueError('Context changed '+rel)
        unchanged.append({'path':rel,'sha256':sha(raw),'previously_cataloged':rel in known})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Pinned client changed')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    native=[]
    for address in FUNCTIONS:
        source_path=RECOVERY/rows[address]['file'];source=source_path.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native function metadata differs')
        size=int(match.group(2));code=pe.get_data(int(address,16)-base,size)
        if len(code)!=size:raise ValueError('Missing native bytes')
        # This is a bounded declared span only, not a complete-body assertion.
        pending.extend([('native/declared-spans/'+address+'.bin',code,exe),
            ('native/source/'+address+'.c',source,source_path)])
        native.append({'address':address,'declared_size':size,'declared_span_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(source_path),
            'declared_size_not_assumed_complete_body':True})
    pending.append(('native/functions.tsv',metadata,RECOVERY/'functions.tsv'))
    switches={};table_rows=[]
    for callsite,table,count in [(0x50e442,0x50e544,24),(0x50e6b0,0x50e918,30),
        (0x50e7f0,0x50e990,16),(0x50e857,0x50e9d0,5),
        (0x50ea4a,0x50eaac,7),(0x511690,0x511870,16)]:
        data=pe.get_data(table-base,count*4);targets=list(struct.unpack('<'+'I'*count,data));switches[callsite]=targets
        table_rows.append({'callsite':f'{callsite:08x}','table_va':f'{table:08x}',
            'entries':count,'targets':[f'{x:08x}' for x in targets],'sha256':sha(data)})
        pending.append((f'native/tables/{table:08x}.bin',data,exe))
    for va,size in [(0x50eac8,41),(0x5118b0,40)]:
        data=pe.get_data(va-base,size)
        if max(data)>=(7 if va==0x50eac8 else 16):raise ValueError('Selector table exceeds target domain')
        pending.append((f'native/tables/{va:08x}.bin',data,exe))
        table_rows.append({'table_va':f'{va:08x}','bytes':size,'selector_hex':data.hex(),'sha256':sha(data)})
    cfgs=[];primary={};envelopes=[]
    for low,high in [(0x50e3b0,0x50e542),(0x50e5e0,0x50e916),
        (0x50e9f0,0x50eaa9),(0x511620,0x51186e)]:
        code=pe.get_data(low-base,high-low)
        cfg,asm,instructions=trace(md,code,low,high,switches)
        if cfg['open_edges']:raise ValueError('Qualified local CFG has open edges')
        declared=int(rows[f'{low:08x}']['bytes'])
        cfg['metadata_declared_size']=declared
        cfg['instructions_beyond_entry_plus_declared_size']=[f'{a:08x}' for a in sorted(instructions) if a>=low+declared]
        cfgs.append(cfg);primary.update(instructions)
        envelopes.append({'address':f'{low:08x}','end_exclusive':f'{high:08x}',
            'bytes':len(code),'sha256':sha(code),'metadata_declared_size':declared,
            'cfg_decoded_bytes':cfg['decoded_unique_cfg_bytes']})
        pending.extend([(f'native/cfg/{low:08x}.bin',code,exe),(f'native/cfg/{low:08x}.asm',asm,'primary branch/table static disassembly')])
    expected={0x50e4c0:0x481440,0x50e4e3:0x481440,0x50e506:0x481440,0x50e536:0x481440}
    for address,target in expected.items():
        ins=primary[address]
        if ins.mnemonic!='call' or ins.operands[0].type!=X86_OP_IMM or ins.operands[0].imm!=target:
            raise ValueError('Native send callsite differs')
    facts={'client_sha256':PIN,'native_world_send_sites':[{'callsite':f'{a:08x}',
        'opcode':'94' if a==0x50e536 else 'D1','source_owner':'player+4308C -> same world network',
        'bytes':primary[a].bytes.hex()} for a in expected],
        'owner_alias_chain':['main+458 -> UI+16180 world network',
            '0048CAA0:main+458 ->renderer+8885E4 ->initializer[1]',
            '004AC850 at004ACD5E passes initializer[1] to004B09C0',
            '004B09C0 -> player/UI+4308C','0050E3B0 mode read and send ECX use player+4308C'],
        'mode_origin':'account07 payload1 AND1 ->account network4200 ->world network4200',
        'mode_business_meaning_recovered':False,
        'native94':{'payload_bytes':8,'selector_offset':0,'unwritten_offsets':[1,2,3],
            'owner_field_dword_offset':4,'mode0_selector27_28_dword_not_assigned':True,
            'mode0_d1_only_selectors':['25','26'],'mode0_d1_then94_selectors':['27','28'],
            'mode1_named_selectors':['19','23','24'],'server_contract_or_success_recovered':False},
        'metadata_limit':'declared count and next recovered function entry do not close primary switch fragments',
        'local_cfgs':cfgs,'tables':table_rows,'new_opcode_values':0,'new_complete_routes':0}
    pending.append(('native-world-mode-and-fragments.json',(json.dumps(facts,indent=2)+'\n').encode(),'static analysis'))
    for name in ['cn-shared-listener-host-01','cn-world-entry-projections-01']:
        path=ROOT/name/'integration-manifest.json';b=path.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior source evidence changed')
        pending.append(('prior-manifests/'+name+'.json',b,path))
    previous=ROOT/'cn-summary-opaque-agent-01';manifest_raw=(previous/'delivery-manifest.json').read_bytes()
    for row in json.loads(manifest_raw)['files']:
        if sha((previous/row['file']).read_bytes())!=row['sha256']:raise ValueError('Prior summary native evidence changed')
    pending.append(('prior-manifests/cn-summary-opaque-agent-01.json',manifest_raw,previous/'delivery-manifest.json'))
    pending.append(('prior-findings/cn-summary-opaque-agent-01.json',(previous/'findings.json').read_bytes(),previous/'findings.json'))
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
    gaps=['Actual native07/1F and1D/0A/billing/alias issuers remain required; source lineage supplies no missing values.',
        'Native mode0/1 directory/backend/receiver variants, authority and replies remain open; producer UI state is not server entitlement.',
        'All gameplay/common actor/02/2A/readiness/TW enrollment/production plan remain incomplete.',
        'Declared spans/metadata entries do not close switch fragments; broad indirect/deferred/variant denominator remains open.',
        'Source-only exact offered snapshot/common-ID row order is a bounded integration invariant, not all official reoffer/live-update semantics.']
    manifest={'kind':'actual account07/common-ID ordered snapshot ->same selected grant/current world ticket ->qualified native offer; primary world mode and switch fragment closure',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'declared_native_spans':native,'native_code_envelopes':envelopes,'primary_switch_tables':table_rows,
        'client_sha256':PIN,'modified_cpp_files':8,'modified_catalog_tools':1,'new_cpp_files':0,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'new_owner_qualified_world_send_sites':4,'exact07_opaque_bytes_and_ordered_common_ids_bound_to_ticket':True,
        'mode_bit0_business_authority_recovered':False,'metadata_function_span_assumed_complete':False,
        'full_native_value_suppliers_implemented':False,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog30 conditional Application/listener/native controller composition sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed',
            'deployed','production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN actual account summary and ordered common-ID world source lineage',
        'version_scope':'cn','status':'已接實際07完整bytes/共用ID列序到同grant及world ticket；原生mode/94/D1區塊來源已保存，正式值與完整路徑未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['same admission state/common IDs; bounded adapter-source snapshot, no new table'],
        'native_form_qualifications':{'account_world_summary_source_lineage':True,
            'ordered_common_id_association':True,'native_world_mode_owner_alias':True,
            'mode_bit0_business_authority':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['summary_world_lineage']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'native-world-mode-and-fragments.json','owner_qualified_world_send_sites':4,
        'opcode_values':['94','D1'],'new_opcode_values':0,'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Continue full native login/summary/world suppliers, and fragment-aware directory producer/receiver/backend source recovery; retain current same-grant07/common-ID lineage.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'modified_cpp_files':8,
        'native_functions':len(native),'primary_cfgs':len(cfgs),'native_world_send_sites':4,
        'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
