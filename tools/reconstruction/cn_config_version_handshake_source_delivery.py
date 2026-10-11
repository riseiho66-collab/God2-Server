"""Retain actual CN config version ->same native account handshake source."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-config-version-handshake-source-01'
ROUND='20261008-cn-config-version-handshake-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/assets/CnClientGroupConfiguration.h','src/cn/assets/CnClientGroupConfiguration.cpp',
 'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
 'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
 'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-config-version-handshake-source-20261008.md',
 'tools/reconstruction/cn_config_version_handshake_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'No new credential tailAA..CB or billingbyte5 semantics; full native profile/billing/rights/revision/deadline/07 summaries remain unconfigured.',
 'Actual launch input owner, deployed client resource/profile pairing and formal Application hosting remain unconfigured.',
 'Arbitrary config versions, integer overflow/native buffer/64-group boundary/cache/reinit/unsupported text variants are not declared closed.',
 'All world/bootstrap/equipment/scene/ACT/shared gameplay/TW/PC/web/WSS/numeric/stack and whole-game denominator requirements remain open.']

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
    prior=(out/'retained-prior/cn-native-launch-config-lineage-source-01/manifest.json').read_bytes()
    if sha(prior)!='508e56cb0c7f6cce14fe1ba6f755dc8914307f93f7a8f2cd2b238859b4138989' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    origins=json.loads((out/'retained-config/decoded-origins.json').read_text(encoding='utf-8'))
    config=[]
    for row in origins:
        name=Path(row['requested']).name
        data=(out/'retained-config/decoded'/name).read_bytes()
        if sha(data)!=row['decoded_sha256']:raise RuntimeError('Native selected config differs')
        plain=(out/'retained-config/plain'/name).read_bytes()
        if sha((CN.parent/'Data3'/(name+'Z')).read_bytes())!=row['raw_sha256'] or (CN.parent/'Data3'/name).read_bytes()!=plain:
            raise RuntimeError('Current installed config differs from retained input')
        def directives(raw):
            return [int(line.lstrip(b' \t')[1:].strip()) for line in raw.splitlines() if line.lstrip(b' \t').startswith(b'$')]
        preferred=directives(data);sibling=directives(plain)
        if preferred!=[296] or sibling!=[268]:raise RuntimeError('Actual version directive changed')
        config.append(dict(name=name,selected_file=row['selected'],decoded_sha256=sha(data),plain_sha256=sha(plain),
            selected_version_integer=preferred[0],selected_version_byte=preferred[0]&255,
            plain_version_integer=sibling[0],plain_version_byte=sibling[0]&255,resource_read_only=True))
    dump('retained-config/version-origins.json',config)
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native image differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    for address in ('0047cbc0','0041fa50','0047fe30','0047e6c0'):
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Metadata source not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing native extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-image_base,size)
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),source=str(paths[0]),whole_cfg_claimed=False))
    literal=view.read(0x7ed65c-image_base,3)
    if literal!=b'%d\0':raise RuntimeError('Native version scan format differs')
    save('native/literals/007ed65c.bin',literal)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: normal launch config lineage/catalog119/97-file seal',
        native_sha256=SHA,native_functions=native,native_primary_envelope_and_literal_bytes=sum(n['metadata_envelope_bytes'] for n in native)+3,
        config_version_origins=config,actual_configuration_version_operand_producers_added=1,
        existing_account_version_handshake_source_bindings_added=1,same_configuration_retained_across_composition_host_connection_transport=True,
        pinned_account_version_byte=40,world_transport_version_unchanged=240,ui_world_login_record_version_unchanged=200,
        original_native_wire_changed=False,original_native_baseline_changed=False,new_credential_tail_field_semantics=0,
        new_billing_byte5_semantics=0,official_billing_profile_values_invented=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_resource_reader_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_config_version_handshake_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Same actual preferred CN config$296 ->low byte40 ->composition/host/connection/transport account01 version before credential stage',
        version_scope='pinned-cn-account-config-version-source-only',status='Actual version producer/handshake binding implemented; native metadata/profile/hosting remain open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual profile40/billing16/rights/revision/deadline/07 summaries/group billing/load/location; config input/deployment identity and cache variants. Continue all world/gameplay/numeric/TW/PC/web/WSS/denominator; PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN actual config version handshake source ('+ROUND+')\n\n'
            'Added selected native config integer/low BYTE source and retained SAME immutable configuration through real login composition, host, connection and transport. '
            'Actual preferred$296 ->40 qualifies unchanged native account01/28/00; plain$268 ->12 is not substituted. '
            'Missing/mismatched actual source rejects without rebaselining; world240/login200/codec/verification/grants unchanged. '
            'Version producer1/existing handshake binding1, new opcode/phase/complete owner/full0; no new tail or billingbyte5 semantics/guessed values. '
            'Native/code/resource file recovery only, no C++/native/API/build/test/runtime/DB/deploy. '
            'See research/cn-config-version-handshake-source-20261008.md; full goal active.\n')
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
        'actual_configuration_version_operand_producers_added','existing_account_version_handshake_source_bindings_added',
        'pinned_account_version_byte','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
