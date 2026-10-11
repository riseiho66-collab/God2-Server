"""Static pinned CN config recovery and source delivery, no native execution."""
import difflib
import hashlib
import json
import re
import struct
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-client-group-configuration-source-01'
ROUND='20261008-cn-client-group-configuration-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/assets/CnClientGroupConfiguration.h','src/cn/assets/CnClientGroupConfiguration.cpp',
 'src/cn/auth/SharedAccountDirectorySource.h','src/cn/auth/SharedAccountDirectorySource.cpp',
 'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-client-group-configuration-source-20261008.md',
 'tools/reconstruction/cn_client_group_configuration_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Runtime initial-host/008AEEC0 operands, immutable client-profile deployment and formal Application configuration still required; resource variants are not selected by language.',
 'Native group billing/load/location, profile40/billing16/rights/revision/deadline and full07 summaries remain unconfigured.',
 'Qualified parser rejects unsafe/malformed/long-chunk forms instead of reproducing native overflows; arbitrary configurations and all native variants are not claimed complete.',
 'All world/bootstrap/equipment/scene/ACT/TW/PC/web/WSS/gameplay/numeric and whole-game denominator requirements remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def decode_file(data):
    # File-only transcription of0045A060. A missing byte at EOF reaches its
    # output-length comparison, including a final one-byte backref operand.
    # This differs from the strict historical TW analysis helper; do not
    # silently rewrite that helper or claim it decoded these CN resources.
    if len(data)<7 or data[:2]!=b'\x05\x16':raise ValueError('Missing native wrapper')
    expected=struct.unpack_from('<I',data,2)[0]
    if expected>2048:raise ValueError('Recovery budget exceeded')
    ring=bytearray(b' '*4096);valid=bytearray([1]*0xfee+[0]*18)
    cursor=0xfee;offset=7;flags=0;plain=bytearray();terminal=None
    def append(value):
        nonlocal cursor
        if len(plain)>=expected:raise ValueError('Output exceeds declared length')
        plain.append(value);ring[cursor]=value;valid[cursor]=1;cursor=(cursor+1)&4095
    while offset<len(data):
        flags>>=1
        if not flags&0x100:
            flags=data[offset]|0xff00;offset+=1
            if offset==len(data):terminal='EOF after flag';break
        first=data[offset];offset+=1
        if flags&1:append(first);continue
        if offset==len(data):terminal='EOF after first backref operand';break
        second=data[offset];offset+=1;position=first|((second&0xf0)<<4)
        for index in range((second&15)+3):
            source=(position+index)&4095
            if not valid[source]:raise ValueError('Unspecified initial ring tail')
            append(ring[source])
    if len(plain)!=expected:raise ValueError('Native declared length differs')
    return bytes(plain),dict(terminal=terminal or 'EOF between tokens',input_consumed=offset,
        declared_bytes=expected,output_bytes=len(plain))

def recover_groups(plain):
    # Actual safe input snapshot, not exercising the new C++ reader.
    groups=[];active=False
    for line_number,line in enumerate(plain.replace(b'\r\n',b'\n').split(b'\n'),1):
        line=line.lstrip(b' \t')
        if not line:active=False;continue
        if line[:1] in (b';',b'#'):continue
        if line.startswith(b'['):
            close=line.index(b']')
            groups.append(dict(ordinal=len(groups),name_cp936=line[1:close].decode('cp936'),
                name_hex=line[1:close].hex(),slots=[]));active=True;continue
        if not active:continue
        parts=line.split(b'=',1)
        name=parts[0].rstrip(b' \t') if len(parts)==2 else b''
        values=parts[1].split() if len(parts)==2 else []
        value=values[0] if values else b''
        groups[-1]['slots'].append(dict(ordinal=len(groups[-1]['slots']),line=line_number,
            name_hex=name.hex(),name_cp936=name.decode('cp936'),value_hex=value.hex(),
            value_narrow=value.decode('ascii')))
        if len(groups[-1]['slots'])==10:active=False
    return groups

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before source snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md',
        'artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected context differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-bound-account-directory-source-01/manifest.json').read_bytes()
    if sha(prior)!='da6d3cd5be23af5168f347c6480b7385d942088d73c02aeb8a63ab76364f0dfc' or not json.loads(prior)['sealed']:
        raise RuntimeError('Previous seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native image differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    roots=('00405a30','0047c990','0047cbc0','0045b270','0045a060','0053ff40','0047c970','00443fa0','00443e80')
    for address in roots:
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Native metadata not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing native metadata extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-image_base,size)
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        disassembly='\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n'
        save('native/functions/'+address+'.asm',disassembly.encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),source=str(paths[0]),
            whole_cfg_claimed=False))
    literals=[]
    for va,size,label in ((0x7f14dc,0xb0,'config path/address literals'),(0x7ed41c,2,'Z suffix'),
        (0x7ec304,3,'row token format'),(0x7ed65c,3,'version integer format')):
        data=view.read(va-image_base,size);save(f'native/literals/{va:08x}.bin',data)
        literals.append(dict(va=f'{va:08x}',bytes=size,sha256=sha(data),label=label))
    resources=[]
    for name in ('config.ini','config2.ini','config_2.ini','config2_2.ini'):
        encoded=(out/'native/resources/Data3'/f'{name}Z').read_bytes();plain,eof=decode_file(encoded)
        save('native/decoded/'+name,plain)
        groups=recover_groups(plain)
        resources.append(dict(requested='Data3/'+name,selected='Data3/'+name+'Z',raw_sha256=sha(encoded),
            decoded_sha256=sha(plain),decoded_bytes=len(plain),eof=eof,groups=groups,
            group_count=len(groups),configured_slot_counts=[len(g['slots']) for g in groups],
            same_plain_sibling=plain==(out/'native/resources/Data3'/name).read_bytes(),
            static_file_recovery=True,native_resource_loader_executed=False))
    dump('native/decoded-origins.json',resources)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: actual bound directory source/catalog117/66-file seal',
        native_sha256=SHA,native_functions=native,literal_spans=literals,resources=resources,
        native_primary_envelope_bytes=sum(n['metadata_envelope_bytes'] for n in native)+sum(n['bytes'] for n in literals),
        immutable_native_client_config_suppliers_added=1,explicit_native_config_selection_forms=4,
        native_group_slot_sources_connected_to_existing_directory=1,configured_slot_count_no_longer_caller_chosen=True,
        native_configured_groups_per_selected_file=[r['group_count'] for r in resources],
        native_configured_slots_per_group=resources[0]['configured_slot_counts'],
        configured_slot_vectors_by_resource=[r['configured_slot_counts'] for r in resources],
        native_language_helper_literal_return=0,gb_config_branches_unreachable_in_pinned_helper=True,
        compressed_z_preferred_over_plain=True,all_plain_siblings_differ=all(not r['same_plain_sibling'] for r in resources),
        strict_historical_tw_decode_attempt_rejected=True,historical_tw_decoder_modified=False,
        native_eof_length_branch_recovered=True,new_native_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        runtime_selection_operands_configured=False,formal_application_hosted=False,
        actual_native_profile_billing_owner_configured=False,official_server_topology_recovered=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_resource_reader_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_client_group_configuration_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Actual selected CN config.iniZ -> immutable group ordinal/slots -> same bound04/05/06 native directory',
        version_scope='pinned-cn-account-config-source-only',status='Source implemented; runtime selection/profile/billing and formal hosting unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual runtime initial-host/008AEEC0 config identity; native profile40/billing16/rights/deadline/summaries and group billing/load/location. Continue all world/gameplay/numeric/TW/PC/web/WSS/denominator; PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN actual selected group configuration ('+ROUND+')\n\n'
            'Recovered four selected config.iniZ resources and pinned native file selection/EOF/group ordinal/slot lineage. '
            'Implemented immutable actual resource supplier and required it in existing directory/login composition: slot counts derive from the selected client file, full catalog must match, duplicate group labels stay separate ordinals. '
            'Native helper returns0; no GB branch/language conflation. Valid native compressed files differ from plain siblings; no official topology or runtime selection claim. '
            'Source supplier1, native selection forms4, existing directory binding1, new opcode/phase/complete owner/full0. '
            'Native static file recovery only, no C++ reader/build/test/runtime/network/DB/deploy; frozen source contexts retained. '
            'See research/cn-client-group-configuration-source-20261008.md. Full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),
                data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_envelope_bytes','immutable_native_client_config_suppliers_added',
        'explicit_native_config_selection_forms','native_configured_slots_per_group','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
