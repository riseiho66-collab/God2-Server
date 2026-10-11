"""Retain pinned CN normal-launch lineage and actual config composition source."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-launch-config-lineage-source-01'
ROUND='20261008-cn-native-launch-config-lineage-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/assets/CnClientGroupConfiguration.h','src/cn/assets/CnClientGroupConfiguration.cpp',
 'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-native-launch-config-lineage-source-20261008.md',
 'tools/reconstruction/cn_native_launch_config_lineage_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual launch-input owner/client-profile deployment and Application configuration remain unconfigured; no current process arguments inspected.',
 '004059E0/reinitialization/009EE1B8 cache invalidation/other entry contexts remain open; ordinary startup relation is not generalized.',
 'Native Windows quoting/CP operand3 conversion is not emulated; the source requires the actual already-converted first argument.',
 'Actual profile40/billing16/rights/revision/deadline/07 summaries/group billing/load/location remain open, as do all world/gameplay/TW/PC/web/WSS/numeric and denominator requirements.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected context differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-client-group-configuration-source-01/manifest.json').read_bytes()
    if sha(prior)!='9f6a97d006e52723f9b91bde0bfc80b04a6a6d68a8a32c606c722fab576c148f' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    for file in ('findings.json','native/decoded-origins.json'):
        if (out/'retained-config'/file).read_bytes()!=(base/'cn-client-group-configuration-source-01'/file).read_bytes():
            raise RuntimeError('Retained original config evidence differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native image differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    for address in ('00405a60','00404ce0','00404d50','005413a0','00405150','00449f50','0047fa20','004059e0','0047c990','0047cbc0'):
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Metadata source not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing declared envelope')
        size=int(match.group(1));va=int(address,16);code=view.read(va-image_base,size)
        instructions=list(md.disasm(code,va))
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in instructions)+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),source=str(paths[0]),
            whole_cfg_claimed=False,calls=[dict(va=f'{i.address:08x}',operand=i.op_str) for i in instructions if i.mnemonic=='call']))
    data=view.read(0x7ec304-image_base,3);save('native/literals/007ec304.bin',data)
    if data!=b'%s\0':raise RuntimeError('Native format literal differs')
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: actual client group source/catalog118/118-file seal',
        native_sha256=SHA,native_functions=native,native_primary_envelope_and_literal_bytes=sum(n['metadata_envelope_bytes'] for n in native)+3,
        new_normal_launch_configuration_operand_projections=1,new_existing_configuration_composition_bindings=1,
        ordinary_first_startup_selection_forms=3,retained_low_level_configuration_selection_forms=4,
        normal_startup_operands_share_same_copied_first_argument=True,
        startup_argument_is_complete_formatted_copy_not_scanf_token=True,
        startup_copy_destination_bytes=256,qualified_copy_max_argument_bytes=255,
        native_multibyte_conversion_codepage_operand=3,windows_conversion_or_quoting_emulated=False,
        raw_command_line_or_current_process_inspected=False,actual_launch_input_owner_configured=False,
        reinitialization_cache_contexts_complete=False,profile_billing_owner_configured=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_resource_reader_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_native_launch_config_lineage_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Pinned normal startup complete converted first argument -> same config operands -> selected resource -> existing native account composition',
        version_scope='pinned-cn-normal-startup-account-config-source-only',
        status='Actual source composition implemented; input owner/profile/hosting unconfigured; reinit/cache open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual profile40/billing16/rights/revision/deadline/07 summaries and group billing/load/location; native caller/reinit/cache/config input ownership. Continue all world/gameplay/numeric/TW/PC/web/WSS/denominator; PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN normal startup configuration lineage ('+ROUND+')\n\n'
            'Recovered00405A60 parsed/narrow argv0 ->complete vsnprintf_s %%s copy ->008AEEC0 and same main+240/0047FA20/0047C990 initial-host lineage. '
            'Added bounded normal-startup read factory and explicit StartupClientGroups alternative in actual login composition; mutually exclusive with existing immutable config input. '
            'No Windows quoting/ACP emulation/default argument/root or reinit/cache generalization. Ordinary first startup forms3, prior lower-level forms4 retained. '
            'Projection1/existing composition binding1, new opcode/phase/complete owner/full0, denominator unknown. '
            'No native/API/C++/build/test/runtime/DB/deploy; frozen contexts preserved. See research/cn-native-launch-config-lineage-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),
                fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_envelope_and_literal_bytes',
        'new_normal_launch_configuration_operand_projections','new_existing_configuration_composition_bindings',
        'ordinary_first_startup_selection_forms','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
