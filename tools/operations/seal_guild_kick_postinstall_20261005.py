"""Seal installed619f own-server native postacceptance, no save/config changes."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 old=ROOT/'artifacts/research/native-guild-management-0080/kick-live-v02/contract.json';c=json.loads(old.read_text('utf-8'))
 for n,h in c['source_sha256'].items():assert sha(ROOT/n)==h,n
 rel=ROOT/'artifacts/releases/owned-guild-kick-20261005-01';a=json.loads((rel/'apply-result.json').read_text('utf-8'))
 assert a['accepted'] is True and a['formal_installed'] is True and a['same_schema50_exact_before_start'] is True
 assert all(a[k] is False for k in ('database_replaced','config_changed','resources_changed'))
 active=ROOT/'build-town-visibility/Release/god2-server.exe';assert sha(active)==c['candidate_sha256']==a['candidate_sha256']
 before=json.loads((rel/'database-install-before.json').read_text('utf-8'));after=json.loads((rel/'database-install-after.json').read_text('utf-8'));assert before==after and before['history'][-1][0]==50
 names=('tools/operations/owned_guild_kick_release_v01_20261005.py','tools/operations/kick_postinstall_closeout_20261005.py','tools/operations/seal_guild_kick_postinstall_20261005.py')
 c['source_sha256'].update({n:sha(ROOT/n) for n in names})
 c.update(candidate_path=active.relative_to(ROOT).as_posix(),formal_release=rel.relative_to(ROOT).as_posix(),sealed_at_utc=datetime.now(timezone.utc).isoformat(),supersedes_attempt_contract=old.relative_to(ROOT).as_posix(),supersedes_attempt_contract_sha256=sha(old),reason='Installed619f same50 binary and unchanged current formal configuration. Complete original native72/announcement/commonchat/relogin workflow in both950/936 isolated owned fixtures; no formal gameplay grants.')
 out=ROOT/'artifacts/research/native-guild-management-0080/post-install-v01';out.mkdir(exist_ok=False)
 write(out/'contract.json',c);write(out/'installation-proof.json',{'accepted_for_postinstall_native_test':True,'formal_installed':True,'owned_pid':a['owned_pid'],'apply_result_sha256':sha(rel/'apply-result.json'),'candidate_sha256':sha(active),'same_schema50_typed_save_exact_before_start':True,'database_replaced':False,'config_changed':False,'resources_changed':False,'source_files':len(c['source_sha256']),'actual_client_postinstall_accepted':False})
 print(json.dumps({'accepted_for_postinstall_native_test':True,'contract':str(out/'contract.json')}))
if __name__=='__main__':main()
