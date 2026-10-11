"""Seal bounded native member-leave acceptance; never promote the formal server."""
import argparse, hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/research/native-guild-membership-0078'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text('utf-8'))
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write_new(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def qualify(result,contract,contract_path):
    assert contract['design']=='CUSTOM-0078' and contract['scope']=='DISPOSABLE_LOOPBACK_LAB_ONLY_NOT_FORMAL'
    assert contract['formal_installed'] is False and result['contract_sha256']==sha(contract_path)
    sources=contract['source_sha256'];assert len(sources)>=1543
    assert result['sources_before']==sources==result['sources_after']
    assert result['frozen_before']==result['frozen_after']
    for p in ('src/core/Application.cpp','src/db/SqliteOwnedGuildMembershipRepository.cpp',
        'src/handlers/OwnedGuildLeaderPanelService.h','tests/storage_owned_guild_member_leave_0078.cpp',
        'tests/research/test_native_guild_member_leave_server_20261003.py'):
        assert p in sources
    helpers=[(ROOT/p).resolve() for p,digest in sources.items()
        if Path(p).name.startswith('private_guild_leadership_0078_') and digest==contract['helper_sha256']]
    assert len(helpers)==1 and helpers[0].is_relative_to(ROOT)
    frozen={Path(p).resolve():digest for p,digest in result['frozen_before'].items()}
    assert frozen[helpers[0]]==contract['helper_sha256']==sha(helpers[0])
    guards=('sources_unchanged','protected_files_unchanged','protected_DB_exact','frozen_unchanged',
        'protected_processes_exact','desktop_unchanged','foreground_unchanged','candidate_unchanged')
    assert result['accepted'] is True and all(result[k] is True for k in guards)
    assert len(result['cases'])==2 and {c['locale'] for c in result['cases']}=={950,936}
    for case in result['cases']:
        ui=case['ui'];assert case['accepted'] is True and ui['accepted'] is True
        assert case['runner_exit']==0 and type(case['runner_exit']) is int
        assert all(ui[k]['accepted'] is True for k in ('real_native_71_approve','real_native_72_reject','native_72_cancel'))
        events=ui['ordinary_member_leave_events'];assert len(events)==1
        event=events[0];assert event['identity']==5 and event['locale']==case['locale']
        for k in ('accepted','cancel_no_action_log','cancel_SQL_exact','cancel_native_membership_preserved',
            'owner_only_membership_deleted','pending6_exact','governance_exact','all_unrelated_tables_exact',
            'native_2D_name_empty','all_panels_closed','client_still_running','global_revision_advanced'):
            assert event[k] is True
        empty=event['native_92_self_cache_empty']
        assert type(empty['count']) is int and empty['count']==0 and empty['rows_hex']==[] and empty['by_name']=={}
        assert event['native_self_hex']=='0001'
        header=bytearray(52);header[13]=6;header[19]=2;header[23]=20
        assert event['native_header_hex']==header.hex()
        assert ui['ordinary_paired_entry_accepted'] is False and ui['rendered_pixels_tested'] is False
        assert ui['all_clients_closed'] is True and ui['all_loaders_closed'] is True and case['exclusive_2598_released'] is True
    assert all(sha(ROOT/p)==digest for p,digest in sources.items())
    return {k:result[k] for k in guards}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--live-result',type=Path,required=True);ap.add_argument('--contract',type=Path,required=True)
    a=ap.parse_args();live=a.live_result.resolve();contract_path=a.contract.resolve()
    result=read(live);contract=read(contract_path);guards=qualify(result,contract,contract_path)
    candidate=ROOT/'build-native-guild-member-leave-20261003/Release/god2-server.exe'
    assert sha(candidate)==contract['candidate_sha256']
    folder=BASE/'member-leave-runtime-v01';report_path=BASE/'implementation-report-v05.json';assert not report_path.exists()
    before=read(folder/'before.json')
    assert all(sha(Path(p))==digest for p,digest in before['protected'].items())
    testlog=folder/'accepted-current-candidate-ctest.log';assert not testlog.exists()
    rawlog=ROOT/'build-native-guild-member-leave-20261003/Testing/Temporary/LastTest.log'
    log=rawlog.read_text('utf-8',errors='replace')
    for value in ('PASS 63','PASS 290','PASS 228','PASS 66','checks=131848'):assert value in log
    tcp=BASE/'member-leave-v01/tcp-qualified-run.txt';text=tcp.read_text('utf-8')
    assert contract['candidate_sha256'] in text and 'Ran 5 tests' in text and text.rstrip().endswith('OK')
    shutil.copyfile(rawlog,testlog)
    registry=ROOT/'docs/custom-designs.json';prior=read(registry);after=json.loads(json.dumps(prior))
    entry=next(e for e in after['designs'] if e['id']=='CUSTOM-0078')
    write_new(folder/'registry-before-member-leave-acceptance.json',prior)
    entry['name']='Native cave create/apply, founder approval/rejection and ordinary member leave to candidate SQL'
    entry['native_gap']='General non-TEST create/join entry, original NPC mapping and original governance rules remain OPEN. Transfer/disband/officers/member kick/applicant-cancel UI, cooldown/guild-growth/economy and final production performance remain OPEN.'
    entry['rules']=[r for r in entry['rules'] if not r.startswith('All player-created guild native73 leaves are currently denied')]
    entry['rules']+=['CUSTOM-0078 ordinary accepted members can self-leave through native main16/modal4/C2S73 slot0 only under a fresh complete published panel. Capture the immutable SQL/world/publication lease before every batch prefix; consume before SQL. Founder leave stays denied. Same-batch help/Tick cannot grant a missing or stale lease.',
        'Member leave atomically advances the global guild generation and removes only the authenticated member. Pending applications, founder/governance, other members and all unrelated typed SQL/schema/unknown guild columns are preserved with G0/G1/G2 and paired world proofs. Native2D clears the name; remove non-self native92 slots then self0 before the old administrator roster path resumes.']
    for p in ('tests/storage_owned_guild_member_leave_0078.cpp','tests/research/test_native_guild_member_leave_server_20261003.py',live.relative_to(ROOT).as_posix()):
        if p not in entry['tests']:entry['tests'].append(p)
    for p in (contract_path,BASE/'entry-v02/native.json',BASE/'leave-storage-v01/report.json',BASE/'member-leave-v01/native.json',report_path):
        key=p.relative_to(ROOT).as_posix()
        if key not in entry['evidence']:entry['evidence'].append(key)
    entry['acceptance'].update(isolated_ordinary_member_leave_percent=100,isolated_locale_workflows=2,
        latest_native_requests=12,general_create_join_entry_percent=0,formal_create_join_percent=0,whole_game_percent=None,
        formal_installed=False,actual_client_acceptance=True,
        actual_client_acceptance_scope='Hidden current-client native WM input/VM_READ: create, two applications, founder approve, ordinary member cancel and self-leave while pending retained, founder reject cancel/reject; both950/936. No rendered-pixel proof or non-TEST create/join entry.',
        report=report_path.relative_to(ROOT).as_posix())
    assert [e for e in prior['designs'] if e['id']!='CUSTOM-0078']==[e for e in after['designs'] if e['id']!='CUSTOM-0078']
    report={'state':'CANDIDATE_NATIVE_ORDINARY_MEMBER_LEAVE_ACCEPTED_NOT_FORMAL','design_id':'CUSTOM-0078',
        'candidate':ref(candidate),'contract':ref(contract_path),'live':ref(live),'source_sha256':contract['source_sha256'],
        'tests':{'candidate_ctest_suites':5,'source_service_storage_panel_checks':647,'wire_checks':131848,
            'candidate_ctest_log':ref(testlog),'candidate_TCP_suites':5,'candidate_TCP_log':ref(tcp),
            'storage_report':ref(BASE/'leave-storage-v01/report.json'),'entry_trace':ref(BASE/'entry-v02/native.json'),
            'native_leave_trace':ref(BASE/'member-leave-v01/native.json')},'guards':guards,
        'acceptance':entry['acceptance'],'limits':entry['native_gap'],
        'formal_files_and_previous_candidate_unchanged':True,'no_formal_restart':True,'registry_only_design0078_changed':True,
        'finalizer':ref(Path(__file__))}
    registry.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n','utf-8')
    report['registry_sha256']=sha(registry);write_new(report_path,report)
    print(json.dumps({'report':str(report_path),'sha256':sha(report_path),'bounded_member_leave_percent':100,'formal_percent':0}))
if __name__=='__main__':main()
