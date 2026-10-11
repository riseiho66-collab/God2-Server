"""Retain actual common identity -> CN07 supplier/source-only delivery."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-common-character-summary-source-01'
ROUND='20261008-cn-common-character-summary-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp',
 'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-common-character-summary-source-20261008.md',
 'tools/reconstruction/cn_common_character_summary_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual full native07 metadata/visibility/revision owner remains unconfigured; names do not produce native slot/appearance/location/opaque bytes.',
 'Actual account metadata40/billing16/rights/deadline and group billing/load/location owners remain unconfigured.',
 'Common exact14-byte name boundary is supported; all CN15-byte/canonicalization/prompt/native issuer/durable replay variants remain open.',
 'Formal Application host/all native world/bootstrap/equipment/scene/ACT/gameplay and TW/PC/web/WSS/numeric/stack/whole-game denominator remain open.']

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
    prior=(out/'retained-prior/cn-config-version-handshake-source-01/manifest.json').read_bytes()
    if sha(prior)!='0df313ef2dd7eb4c667cfd8965d46fd4ac1e6d9f455b383981f00e7f8cbf300d' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native image differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    for address in ('00481640','00443080','00443640'):
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Metadata source not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing native extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-image_base,size)
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),source=str(paths[0]),whole_cfg_claimed=False))
    marker=base/'cn-selection-name-identity-01/findings.json'
    marker_raw=marker.read_bytes();save('retained-native/name-marker-findings.json',marker_raw)
    facts=dict(round=ROUND,previous_goal_turn_classification='no progress: status-only reply; revalidated active state and took next source action',
        previous_implementation_turn_classification='progress: config version source/catalog120/109-file seal',
        native_sha256=SHA,native_functions=native,native_primary_metadata_envelope_bytes=sum(n['metadata_envelope_bytes'] for n in native),
        retained_name_marker_findings_sha256=sha(marker_raw),common_character_name_to_cn07_producers_added=1,
        existing_account_summary_source_composition_bindings_added=1,actual_common_backend_bound_by_composition=True,
        common_supported_name_byte_limit=14,cn_wire_name_codepage=936,display_conversion_used_for_identity=False,
        complete_native_metadata_input_required=True,actual_native_summary_metadata_owner_configured=False,
        actual_native_profile_owner_configured=False,native_slots_inferred_from_common_slots=False,
        all_account_characters_made_visible=False,unknown_native_values_invented=False,
        formal_application_hosted=False,new_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,levels_changed=False,
        build_run=False,tests_run=False,runtime_run=False,text_codec_run=False,Cplusplus_source_run=False,
        Windows_API_run=False,native_execution=False,database_access=False,deployed=False,
        protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_common_character_summary_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Actual common character identity/codepage -> CN07 active name bytes with full native metadata/ordered visibility source retained',
        version_scope='pinned-cn-account-common-name-summary-source-only',
        status='Actual common-name producer and account composition implemented; native metadata/visibility/profile/hosting remain open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual native07 metadata/visibility/revision and profile40/billing16/rights/deadline/group load/location producers; all world/gameplay/numeric/TW/PC/web/WSS and denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN common character name summary source ('+ROUND+')\n\n'
            'Added actual common repository name/codepage ->unchanged Unicode identity ->CN936 name producer, retaining complete actual native07 metadata and explicit ordered common ID/visibility mapping. '
            'Native prompt markers require explicit source mode; no all-visible/slot/default/opaque/name-lookup rules. '
            'Composition binds SAME Context.characters for full account or issued Profile Prepare; conflicting summary suppliers reject. '
            'Producer1/existing source composition binding1; opcode/phase/full owner/full routes0. '
            'Actual metadata/visibility/revision/profile/billing/host remain unconfigured; whole totals/percent null. '
            'No builds/tests/native/API/text-codec/C++/DB/deployment. See research/cn-common-character-summary-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),
                fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes',
        'common_character_name_to_cn07_producers_added','existing_account_summary_source_composition_bindings_added',
        'actual_native_summary_metadata_owner_configured','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
