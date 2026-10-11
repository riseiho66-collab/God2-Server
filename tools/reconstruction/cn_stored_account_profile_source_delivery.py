"""Retain common SQLite snapshot -> actual CN issued-profile composition sources.

File/source accounting only. Never open SQLite, run C++ or visit config URIs.
"""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-stored-account-profile-source-01'
ROUND='20261008-cn-stored-account-profile-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=(
 'src/db/NativeAccountSnapshotRepository.h',
 'src/db/SqliteNativeAccountSnapshotRepository.h','src/db/SqliteNativeAccountSnapshotRepository.cpp',
 'src/cn/auth/SharedStoredAccountProfileSource.h','src/cn/auth/SharedStoredAccountProfileSource.cpp',
 'src/db/SqliteAccountRepository.h','src/db/Database.h','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp',
 'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-stored-account-profile-source-20261008.md',
 'tools/reconstruction/cn_stored_account_profile_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Proposed common snapshot table is NOT installed, migration-registered or imported; actual source rows/write authority remain absent.',
 'Origin/revision/value equality is not native proof, entitlement or cross-process atomicity/ABA protection.',
 'Actual Authority/Plan/rights/deadline/billing/group metadata and formal Application source selection remain unconfigured.',
 'Actual native22 role/revision and native07 metadata/visibility providers, world/bootstrap/appearance and complete owner chains remain open.',
 'All TW/CN/PC/web/WSS authoritative gameplay/shared rules/storage/output/numeric/stack/full denominator/final validation/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=74:raise RuntimeError('Expected retained 74-file before snapshot')
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected source differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-native-role-summary-level-source-01/manifest.json').read_bytes()
    prior_sha=sha(prior)
    if prior_sha!='dfc3f8393bf8b8d897e5915ed5a9bca7f806c04e4c10de16c6ff181d243c6b30' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    for address in ('0047CBC0','0047D4A0'):
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Metadata source not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing native extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-image_base,size)
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),source=str(paths[0]),whole_cfg_claimed=False))
    literal=view.read(0x7ec304-image_base,3)
    if literal!=b'%s\0':raise RuntimeError('Native string literal differs')
    save('native/literals/007EC304.bin',literal)
    retained=[]
    for segment,files in (
        ('cn-issued-account-source-01',('findings.json',)),
        ('cn-client-group-configuration-source-01',('native/decoded-origins.json',
          'native/decoded/config.ini','native/decoded/config2.ini','native/decoded/config_2.ini','native/decoded/config2_2.ini'))):
        for rel in files:
            p=base/segment/rel;data=p.read_bytes();snapshot='retained-inputs/'+segment+'/'+rel;save(snapshot,data)
            retained.append(dict(source=p.relative_to(ROOT).as_posix(),snapshot=snapshot,bytes=len(data),sha256=sha(data)))
    facts=dict(round=ROUND,previous_goal_turn_classification='no progress: read-only completion-status answer; resume unsealed source increment',
        native_sha256=SHA,native_functions=native,native_primary_metadata_envelope_bytes=sum(n['metadata_envelope_bytes'] for n in native),
        native_string_literal_va='007EC304',native_string_literal_bytes=3,
        config_URI_consumers_fully_qualified=False,config_URI_visited=False,config_URI_misrepresented_as_billing=False,
        retained_inputs=retained,before_source_files=len(before),prior_seal_sha256=prior_sha,
        common_sqlite_account_snapshot_readers_added=1,cn_stored_account_profile_producers_added=1,
        existing_stored_profile_login_composition_bindings_added=1,
        common_snapshot_table_proposals_added=1,table_name='account_native_snapshots',
        table_key=['account_id','client_sha256'],schema_migration_registered=False,schema_installed=False,
        snapshots_imported=False,snapshot_write_API_added=False,existing_migration_vectors_changed=False,
        separate_CN_database_opened=False,existing_authentication_behavior_changed=False,
        source_plan_authority_owner_configured=False,actual_native_profile_owner_configured=False,
        native_metadata_bytes=40,native_billing_bytes=16,unknown_values_invented=False,
        cross_process_atomicity_or_ABA_claimed=False,original_native_wire_layout_changed=False,
        original_native_baseline_changed=False,levels_changed=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,
        new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,whole_game_route_total=None,
        whole_game_completed_routes=None,whole_game_completion_percent=None,build_run=False,tests_run=False,
        runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,native_execution=False,
        database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_stored_account_profile_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='SAME common account SQLite snapshot -> actual CN40/16 Profile -> existing issued login composition',
        version_scope='common-account-storage-pinned-cn-opaque-profile-delivery-source-only',
        status='Read-only actual backend/Profile producer/composition implemented; schema/rows/rights/Plan/Application unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual common snapshot source rows/write authority and native entitlement/Plan; native07/22 full providers; complete world/gameplay/numeric/TW/CN/PC/web/WSS/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN stored common account profile source ('+ROUND+')\n\n'
            'Added same-account/backend read-only SQLite snapshot repository and explicit CN stored40/16 Profile producer. '
            'Actual login composition binds SAME Context.accounts to existing issuer/common summaries/held output. '
            'Complete stored values are reread before/after real Plan/Authority observations; source lineage is not native rights proof or cross-process atomicity. '
            'Common table proposal only, no defaults/migration/installation/import/write API; actual rows/rights/Plan/Application remain absent. '
            'Reader1/producer1/existing composition1, opcode/phase/full owner/full routes0, whole totals/percent null. '
            'No build/test/C++/native/API/DB/deploy, frozen contexts unchanged. '
            'See research/cn-stored-account-profile-source-20261008.md; full goal active.\n')
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
        'common_sqlite_account_snapshot_readers_added','cn_stored_account_profile_producers_added',
        'existing_stored_profile_login_composition_bindings_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
