"""Publish bounded candidate receipt only after actual hidden client acceptance."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/research/native-guild-membership-0078'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf-8'))
def write_new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def reference(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live-result',type=Path,required=True)
    parser.add_argument('--contract',type=Path,required=True);args=parser.parse_args()
    live=args.live_result.resolve();contract_path=args.contract.resolve()
    result=read(live);contract=read(contract_path)
    assert contract['design']=='CUSTOM-0078' and contract['scope']=='DISPOSABLE_LOOPBACK_LAB_ONLY_NOT_FORMAL'
    assert contract['formal_installed'] is False and result['contract_sha256']==sha(contract_path)
    source_map=contract['source_sha256'];assert isinstance(source_map,dict) and len(source_map)>=1531
    assert result['sources_before']==source_map and result['sources_after']==source_map
    for required in ('src/core/Application.cpp','src/db/SqliteOwnedGuildMembershipRepository.cpp',
        'src/handlers/OwnedGuildLeaderPanelService.h','src/protocol/RecoveredGuildLeadership.h','tests/CMakeLists.txt'):
        assert required in source_map
    assert result['frozen_before']==result['frozen_after']
    helpers=[(ROOT/p).resolve() for p,digest in source_map.items()
        if Path(p).name.startswith('private_guild_leadership_0078_') and digest==contract['helper_sha256']]
    assert len(helpers)==1 and helpers[0].is_relative_to(ROOT)
    frozen={Path(p).resolve():digest for p,digest in result['frozen_before'].items()}
    assert frozen[helpers[0]]==contract['helper_sha256']==sha(helpers[0])
    assert result['accepted'] and len(result['cases'])==2
    assert {case['locale'] for case in result['cases']}=={950,936}
    checks=('sources_unchanged','protected_files_unchanged','protected_DB_exact','frozen_unchanged',
        'protected_processes_exact','desktop_unchanged','foreground_unchanged','candidate_unchanged')
    assert all(result[k] for k in checks)
    for case in result['cases']:
        ui=case['ui'];assert case['accepted'] and ui['accepted']
        assert ui['real_native_71_approve']['accepted'] and ui['real_native_72_reject']['accepted']
        assert ui['native_72_cancel']['accepted'] and not ui['rendered_pixels_tested']
        assert ui['all_clients_closed'] and ui['all_loaders_closed'] and case['exclusive_2598_released']
    assert all(sha(ROOT/p)==digest for p,digest in contract['source_sha256'].items())
    candidate=ROOT/'build-native-guild-leadership-20261003/Release/god2-server.exe'
    assert sha(candidate)==contract['candidate_sha256']
    report_path=BASE/'implementation-report-v04.json';assert not report_path.exists()
    log_path=BASE/'leader-fixture-gate-v01/accepted-current-candidate-ctest.log'
    assert not log_path.exists();shutil.copyfile(ROOT/'build-native-guild-leadership-20261003/Testing/Temporary/LastTest.log',log_path)
    log=log_path.read_text('utf-8',errors='replace')
    for value in ('PASS 63','PASS 290','PASS 228','checks=131848'):assert value in log
    registry=ROOT/'docs/custom-designs.json';before=read(registry)
    write_new(BASE/'leader-fixture-gate-v01/registry-before-leader-acceptance.json',before)
    after=json.loads(json.dumps(before));entry=next(x for x in after['designs'] if x['id']=='CUSTOM-0078')
    entry['name']='Native cave create/apply and founder pending approval/rejection to candidate SQL'
    entry['implementation']+=['src/protocol/RecoveredGuildLeadership.h','src/handlers/OwnedGuildLeaderPanelService.h']
    entry['native_gap']='Original NPC create/join entry, original approval/officer policy, transfer/disband/member-leave/applicant-cancel UI, cooldown/guild-growth/economy rules and production performance remain OPEN.'
    entry['rules'][3]='Atomic schema49 create/apply/approve/reject/cancel repository. Joining saves only pending applications; native71/72 mutate only an exact pending row under a persisted founder, immutable published recipient-local slot, complete current world/SQL identity and paired proofs. No officer appointment/member kick.'
    entry['rules'][4]='Application route enabled solely in disposable loopback lab. TEST_ONLY characters4/5 and exact recovered applicant6 receive automatic8D. Normal native toolbar help opens the founder/member panel; no original NPC entry or formal save changes claimed.'
    entry['rules'][5]='Complete typed SQL/schema G0/G1/G2 preservation retained. Optimized preservation implementation benchmarks reduced operation median22–28%, still125–136ms with outliers; exact final admission candidate production performance remains a promotion gate.'
    entry['rules']+=['CUSTOM technical projection admission: complete accepted members plus all pending plus new applicant <= native50. Dual-codepage folded-name and character/account-slot collisions reject atomically; existing applications remain reviewable.',
        'Native91 selfrole3 comes only from persisted founder governance; native91 role0 represents pending, role1 accepted. Header capacity20/count accepted members/status6 are explicitly CUSTOM. Benign Tick never opens the panel or restores action authority. Each mutation consumes its publication; explicit help reopening rearms it.',
        'All player-created guild native73 leaves are currently denied, including ordinary members, to preserve founder governance until a separately qualified leave/transfer/disband design. This is an OPEN gameplay gap.']
    entry['tests']+=['tests/test_owned_guild_leadership_wire_0078.cpp','tests/storage_owned_guild_leader_panel_0078.cpp',
        'tests/research/test_native_guild_leadership_server_20261003.py',live.relative_to(ROOT).as_posix()]
    entry['evidence']+=[(BASE/p).relative_to(ROOT).as_posix() for p in ('performance-v02/report.json','admission-v01/report.json',
        'leadership-wire-v01/receipt.json','leader-runtime-review-v01/final-receipt.json') if (BASE/p).exists()]
    entry['evidence']+=[contract_path.relative_to(ROOT).as_posix(),report_path.relative_to(ROOT).as_posix()]
    entry['acceptance'].update(isolated_leader_approve_and_reject_percent=100,isolated_locale_workflows=2,
        latest_native_requests=10,formal_create_join_percent=0,whole_game_percent=None,formal_installed=False,
        actual_client_acceptance=True,actual_client_acceptance_scope='Hidden native WM input and VM_READ: create, two pending applications, founder approve, rejection cancel and reject, both950/936. SQL/cache/controls, not rendered pixels.',
        report=report_path.relative_to(ROOT).as_posix())
    assert [x for x in before['designs'] if x['id']!='CUSTOM-0078']==[x for x in after['designs'] if x['id']!='CUSTOM-0078']
    registry.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n','utf-8')
    report={'state':'CANDIDATE_NATIVE_CREATE_APPLY_FOUNDER_APPROVE_REJECT_ACCEPTED_NOT_FORMAL',
        'design_id':'CUSTOM-0078','candidate':reference(candidate),'contract':reference(contract_path),
        'live':reference(live),'source_sha256':contract['source_sha256'],
        'checks':{'ctest_suites':4,'service_storage_leader_checks':581,'wire_boundary_checks':131848,
            'ctest_log':reference(log_path),'final_candidate_TCP_tests':4,'final_candidate_TCP_seconds':18.344,
            'TCP_receipt_origin':'Root actual unified exec session6874, exit0; synthetic peers NOT_LIVE_UI',
            'prior_afc_candidate_old_route_TCP_tests':13,'preserved_prior_final_review':reference(BASE/'leader-runtime-review-v01/final-receipt.json')},
        'guards':{k:result[k] for k in checks},'registry_only_design0078_changed':True,'registry_sha256':sha(registry),
        'acceptance':{'locale_workflows':2,'native_requests':10,'bounded_leader_workflow_percent':100,
            'formal_installed':False,'formal_create_join_percent':0,'whole_game_percent':None,'rendered_pixels_tested':False},
        'limits':entry['native_gap'],'no_formal_restart':True,
        'preserved_failed_runs':['leader-live-v01/preflight-before-seal.json','leader-live-v01/run-twcn-01/run-result.json',
            'leader-live-v01/leader-twcn-02/run-result.json','leader-live-v02/leader-twcn-03/run-result.json'],
        'seal_and_finalizer':reference(Path(__file__))}
    write_new(report_path,report);print(json.dumps({'report':str(report_path),'sha256':sha(report_path),'bounded_percent':100,'formal_percent':0}))
if __name__=='__main__':main()
