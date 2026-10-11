"""Bind founder-independent leave to its exact new native-client candidate."""
import argparse,hashlib,json,runpy,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/research/native-guild-membership-0078'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf-8'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write_new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def qualify(result,contract,path):
    ordinary=runpy.run_path(str(ROOT/'tools/strike_lab/finalize_guild_member_leave_0078_v01_20261003.py'))['qualify']
    guards=ordinary(result,contract,path)
    for case in result['cases']:
        ui=case['ui'];fixture=ui['founder_unsettled_reservation_fixture'];event=ui['ordinary_member_leave_events'][0]
        assert all(ui[k]['accepted'] is True for k in ('real_create','real_pending_application','second_real_pending_application'))
        assert fixture['single_gameplay_row_added'] is True and fixture['cleanup_completed'] is True
        assert fixture['actual_battle_visual_tested'] is False and fixture['authority']=='TEST_ONLY_SQL_FIXTURE_NOT_NATIVE_BATTLE'
        for k in ('all_owned_clients_closed','all_bound_sessions_disconnected'):
            assert fixture['quiescence'][k] is True
        reservation=fixture['reservation']
        assert len(reservation)==4 and type(reservation[0]) is int and reservation[0]>0
        assert type(reservation[1]) is int and reservation[1]==4 and type(reservation[2]) is int and reservation[2]>0 and reservation[3]=='CUSTOM-0012'
        for k in ('founder_unsettled_reservation_exact','founder_resources_exact','founder_no_active_client',
            'synthetic_fixture_not_actual_battle_visual'):
            assert event[k] is True
        assert type(event['founder_reservation_id']) is int and event['founder_reservation_id']==reservation[0]
        cleanup=ui['founder_reservation_fixture_cleanup']
        for k in ('completed','all_other_tables_exact','sequence_unchanged_during_cleanup','governance_pending_memberships_exact'):
            assert cleanup[k] is True
        assert type(cleanup['deleted_rows']) is int and cleanup['deleted_rows']==1
        assert cleanup['reservation']==reservation
        assert all(type(v) is int for v in cleanup['reservation'][:3])
        for k in ('all_owned_clients_closed','all_bound_sessions_disconnected'):
            assert cleanup['quiescence'][k] is True
    return guards
def main():
    p=argparse.ArgumentParser();p.add_argument('--live-result',type=Path,required=True);p.add_argument('--contract',type=Path,required=True)
    a=p.parse_args();live=a.live_result.resolve();path=a.contract.resolve();result=read(live);contract=read(path)
    guards=qualify(result,contract,path)
    candidate=ROOT/'build-native-guild-member-leave-founder-20261004/Release/god2-server.exe'
    assert sha(candidate)==contract['candidate_sha256']
    folder=BASE/'member-leave-founder-runtime-v01';report_path=BASE/'implementation-report-v07.json';assert not report_path.exists()
    assert all(sha(Path(p))==digest for p,digest in read(folder/'before.json')['protected'].items())
    raw=ROOT/'build-native-guild-member-leave-founder-20261004/Testing/Temporary/LastTest.log';text=raw.read_text('utf-8',errors='replace')
    for value in ('PASS 63','PASS 290','PASS 228','PASS 66','checks=131848'):assert value in text
    testlog=folder/'accepted-current-candidate-ctest.log';assert not testlog.exists();shutil.copyfile(raw,testlog)
    evidence=[BASE/'leave-founder-battle-storage-v01/report.json',BASE/'member-leave-founder-battle-v01/verification-final.json']
    for f in evidence:assert f.is_file()
    tcp=read(evidence[1]);assert tcp['fixed_candidate_sha256']==contract['candidate_sha256']
    assert tcp['source_before_TCP']==tcp['source_after_TCP']
    assert all(sha(ROOT/p)==digest for p,digest in tcp['source_before_TCP'].items())
    for name,count in (('TCP_founder',3),('TCP_previous_leave',5)):
        assert tcp[name]['cases']==count==tcp[name]['passed'] and tcp[name]['exit_code']==0
    assert tcp['fixed_CPP']['checks']==39 and tcp['fixed_CPP']['exit_code']==0
    assert tcp['private_processes_disposed_and_port_released'] is True and tcp['formal_installed'] is False
    registry=ROOT/'docs/custom-designs.json';before=read(registry);after=json.loads(json.dumps(before));entry=next(e for e in after['designs'] if e['id']=='CUSTOM-0078')
    write_new(folder/'registry-before-founder-battle-acceptance.json',before)
    entry['native_gap']='General non-TEST create/join entry, original NPC mapping and original governance rules remain OPEN. Transfer/disband/officers/member kick/applicant-cancel UI, cooldown/guild-growth/economy and exact final production performance/concurrency remain OPEN.'
    entry['rules']+=['Ordinary members read an exact read-only founder/governance snapshot independent of the founder battle reservation. Their own world and SQL nonbattle qualification remain mandatory. Founder panels/approval/rejection retain the original leader() action restrictions; a read-only snapshot cannot bypass them. Native-client acceptance uses a clearly marked legal TEST_ONLY SQL reservation, not an actual rendered founder battle.']
    entry['acceptance'].update(founder_in_battle_member_leave_accepted=True,
        isolated_ordinary_member_leave_scope='Owned ordinary member native WM/VM_READ/SQL: no founder reservation and legal unsettled TEST_ONLY founder reservation; both950/936. Member own battle and founder action guards verified with actual repository APIs/TCP. No actual rendered battle or pixels claimed.',
        isolated_ordinary_member_leave_percent=100,general_create_join_entry_percent=0,formal_create_join_percent=0,
        whole_game_percent=None,formal_installed=False,report=report_path.relative_to(ROOT).as_posix())
    for f in [live,path,report_path,*evidence]:
        key=f.relative_to(ROOT).as_posix()
        if key not in entry['evidence']:entry['evidence'].append(key)
    assert [e for e in before['designs'] if e['id']!='CUSTOM-0078']==[e for e in after['designs'] if e['id']!='CUSTOM-0078']
    report={'state':'CANDIDATE_NATIVE_FOUNDER_INDEPENDENT_ORDINARY_MEMBER_LEAVE_ACCEPTED_NOT_FORMAL','design_id':'CUSTOM-0078',
        'candidate':ref(candidate),'contract':ref(path),'live':ref(live),'source_sha256':contract['source_sha256'],
        'tests':{'candidate_ctest_suites':5,'candidate_ctest_log':ref(testlog),'repository_and_TCP':[ref(f) for f in evidence]},
        'guards':guards,'acceptance':entry['acceptance'],'limits':entry['native_gap'],'no_formal_restart':True,
        'prior_candidate_reports_preserved':[ref(BASE/'implementation-report-v05.json'),ref(BASE/'implementation-report-v06.json')],
        'formal_files_and_previous_candidates_unchanged':True,'registry_only_design0078_changed':True,'finalizer':ref(Path(__file__))}
    registry.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n','utf-8');report['registry_sha256']=sha(registry)
    write_new(report_path,report);print(json.dumps({'report':str(report_path),'sha256':sha(report_path),'bounded_percent':100,'formal_percent':0}))
if __name__=='__main__':main()
