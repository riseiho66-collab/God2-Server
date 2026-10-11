"""Seal corrected native QA only; compiled runtime and registry remain exact."""
import hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    previous=ROOT/'artifacts/research/native-guild-management-0080/kick-live-v01/contract.json'
    contract=json.loads(previous.read_text('utf-8'))
    for n,h in contract['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert sha(ROOT/contract['candidate_path'])==contract['candidate_sha256']
    failed=ROOT/'artifacts/playtests/gk-20261005-02/run-result.json'
    old=json.loads(failed.read_text('utf-8'));assert old['accepted'] is False
    assert all(old[k] is True for k in ('sources_unchanged','candidate_unchanged','protected_files_unchanged','protected_DB_exact','frozen_unchanged','protected_processes_exact','desktop_unchanged','foreground_unchanged'))
    assert old['cases'][0]['ui']['error']=='LEADER_RELOGIN_NATIVE_GUILD_NAME_MISSING'
    assert old['cases'][0]['ui']['native72_member_kick']['accepted'] is True
    run=subprocess.run([sys.executable,'-X','utf8','-B','-m','unittest','tests.research.test_native_guild_kick_helper_relogin_20261005','-v'],cwd=ROOT,text=True,encoding='utf-8',capture_output=True,check=True)
    folder=ROOT/'artifacts/research/native-guild-management-0080/kick-live-v02';folder.mkdir(exist_ok=False)
    with (folder/'helper-relogin-regression.log').open('x',encoding='utf-8') as f:f.write(run.stdout+run.stderr)
    names=('tools/strike_lab/private_guild_kick_0080_v02_20261005.py','tests/research/test_native_guild_kick_helper_relogin_20261005.py','tools/operations/seal_guild_kick_helper_v02_20261005.py')
    contract['source_sha256'].update({n:sha(ROOT/n) for n in names})
    contract.update(helper_path=names[0],helper_sha256=sha(ROOT/names[0]),sealed_at_utc=datetime.now(timezone.utc).isoformat(),supersedes_attempt_contract=str(previous.relative_to(ROOT)),supersedes_attempt_contract_sha256=sha(previous),reason='QA callback repair only: existing-member relogins retain NAME default, removed target explicitly requires empty native2D name. No runtime/docs/config/resource/client/wait-budget changes; failed gk02 evidence preserved.')
    write(folder/'contract.json',contract)
    write(folder/'repair-proof.json',{'compiled_candidate_unchanged':True,'old_source_closure_exact':True,'registry_unchanged':True,'failed_terminal_receipt':str(failed.relative_to(ROOT)),'failed_terminal_receipt_sha256':sha(failed),'prior_failure':old['cases'][0]['ui']['error'],'native_regression_tests':4,'passed':4,'real_client_acceptance':False,'candidate_sha256':contract['candidate_sha256'],'source_files':len(contract['source_sha256'])})
    print(json.dumps({'accepted_for_native_test':True,'contract':str(folder/'contract.json'),'runtime_unchanged':True}))
if __name__=='__main__':main()
