"""Integrate reviewed additive CUSTOM0081 source; formal619f EXE/save stay intact."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text('utf-8'))
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 out=ROOT/'artifacts/research/native-guild-management-0081/integration-v01';assert not out.exists()
 final=ROOT/'artifacts/research/native-guild-management-0080/implementation-final-v01';commit=load(final/'metadata-commit.json');assert commit['accepted'] is True and commit['report_sha256']==sha(final/'report.json') and commit['registry_sha256']==sha(ROOT/'docs/custom-designs.json')
 active=ROOT/'build-town-visibility/Release/god2-server.exe';assert sha(active)=='619f04ce6a09bdc2307e59a2d82f9db0bf7a92d4d81fee710843bf63b27d973e'
 contract=load(ROOT/'artifacts/research/native-guild-management-0080/post-install-v01/contract.json')
 differences={n:(h,sha(ROOT/n)) for n,h in contract['source_sha256'].items() if sha(ROOT/n)!=h};assert set(differences)=={'docs/custom-designs.json'}
 draft=ROOT/'artifacts/research/native-guild-management-0081/runtime-draft-v01';manifest=load(draft/'delivery-final.json')
 for n,h in manifest['files'].items():assert sha(draft/n)==h,n
 for n,h in manifest['source_before'].items():assert sha(ROOT/n)==h,n
 changes={}
 app=(draft/'Application.cpp').read_bytes();restored=app
 for entry in reversed(load(draft/'insertions.json')):
  add=entry['addition'].encode();assert restored.count(add)==1;restored=restored.replace(add,b'',1)
 assert restored==(ROOT/'src/core/Application.cpp').read_bytes();changes['src/core/Application.cpp']=app
 for entry in load(draft/'codec-draft-proof.json')['files']:
  assert sha(ROOT/entry['source'])==entry['source_sha256'];assert sha(draft/entry['destination'])==entry['draft_sha256']
  assert entry['only_additions_byte_exact_restore'] is True
  changes[entry['source']]=(draft/entry['destination']).read_bytes()
 changes['src/protocol/RecoveredGuildDisband75.h']=(draft/'protocol/RecoveredGuildDisband75.h').read_bytes()
 changes['tests/test_owned_guild_disband_wire_0081.cpp']=(draft/'test_owned_guild_disband_wire_0081.cpp').read_bytes()
 plan=ROOT/'artifacts/research/native-guild-management-0081/disband-plan-v01'
 decl=(plan/'disband_storage_draft.h').read_bytes();decl=decl[decl.index(b'struct Disbanded {'):];decl=b'    // CUSTOM-0081 retained guild retirement; native75 authority is separate.\n'+decl+b'\n'
 h=(ROOT/'src/db/SqliteOwnedGuildMembershipRepository.h').read_bytes();assert h.count(b'private:')==1
 changes['src/db/SqliteOwnedGuildMembershipRepository.h']=h.replace(b'private:',decl+b'private:',1)
 method=(plan/'disband_storage_draft.cpp').read_bytes();method=method[method.index(b'SqliteOwnedGuildMembershipRepository::Disbanded'):];method=b'// CUSTOM-0081 native75: retained identity/history, no fee or refund.\n'+method+b'\n'
 c=(ROOT/'src/db/SqliteOwnedGuildMembershipRepository.cpp').read_bytes();i=c.rfind(b'}');assert c[i:].strip()==b'}';changes['src/db/SqliteOwnedGuildMembershipRepository.cpp']=c[:i]+method+c[i:]
 svc=(ROOT/'artifacts/research/native-guild-management-0081/disband-service-draft-v01/OwnedGuildDisbandService.h').read_bytes()
 svc=svc.replace(b'// CUSTOM-0081 DRAFT ONLY. This header has not been compiled or installed.',b'// CUSTOM-0081 candidate native75 service; live acceptance is tracked separately.')
 changes['src/handlers/OwnedGuildDisbandService.h']=svc
 for n,rel,expected in [('storage_owned_guild_disband_0081.cpp','storage-tests-draft-v01','782d5f4fc0f3191bb7fc6e6f966b292deeab8ae10332b9fb195fa837db51280e'),('test_owned_guild_disband_service_0081.cpp','service-tests-draft-v01','2afff881be9cff17f453d1d2ff789ded1661fe38a9d97b6b8f6208fdddf7ecb4')]:
  f=ROOT/'artifacts/research/native-guild-management-0081'/rel/n;assert sha(f)==expected;changes['tests/'+n]=f.read_bytes()
 cm=(ROOT/'tests/CMakeLists.txt').read_bytes();anchor=b'foreach(guild_candidate_test IN ITEMS ';addition=b'storage_owned_guild_disband_0081 test_owned_guild_disband_service_0081 test_owned_guild_disband_wire_0081 '
 assert cm.count(anchor)==1;changes['tests/CMakeLists.txt']=cm.replace(anchor,anchor+addition,1)
 original=load(ROOT/'docs/custom-designs.json');updated=copy.deepcopy(original);assert not any(d['id']=='CUSTOM-0081' for d in original['designs'])
 updated['designs'].append({'id':'CUSTOM-0081','name':'Native75 founder retirement with retained guild identity and history','authority':'NATIVE_WIRE_WITH_CUSTOM_RETIRED_GUILD_POLICY','implementation':['src/protocol/RecoveredGuildDisband75.h','src/protocol/RecoveredWorldRecords.h','src/handlers/OwnedGuildDisbandService.h','src/db/SqliteOwnedGuildMembershipRepository.h','src/db/SqliteOwnedGuildMembershipRepository.cpp','src/core/Application.cpp'],'native_gap':'Original server disband consent, economics/refunds, name reuse, cooldown and dedicated ACK remain unrecovered. Currentc5d8 and original149c prove main25/modal5 role3 C2S75 plus self-slot; original2D/92 consumers reused, no invented75 response.','rules':['Only persisted original founder via fresh complete explicit panel, selfslot0, single-use publication and immutable founder world/ABA. Native slot/role never SQL authority.','Every accepted member and pending applicant, including offline, must be persisted nonbattle. Every connected matching-character session must be currently ready with exact account/character; all audience readiness is current policy, not immutable movement ABA.','BEGIN IMMEDIATE exact founder/governance/full roster/application CAS and paired read-only proofs; world callbacks must work after membership/governance deletion, without SQL/UI/reentry effects.','Retain owned_guilds id/name/unknown columns and all announcement history; only bump retained revision and delete exact own governance/members/applications. No fee/refund, no schema migration, save replacement or unrelated mutation.','Retained names and their native folded TW CP950/CP936 byte variants remain reserved. This is CUSTOM retirement/name-reservation policy, not recovered original name reuse.','Capture every75 before old observers and any prefix. Suppress announcement writes across recursion, revoke at EACH success/denial before suffix and at scope exit. Invalidate every connected member/applicant permission before qualified2D/92 clearing; retain native cached rows until clear.','Malformed later record rejects whole frame before earlier chat or75 callback. Cancel is native UI only; no guessed dedicated75 ACK.'], 'field_origins':{'C2S75_slot_and_native2D92':'NATIVE_VERIFIED','retirement_nonbattle_authorization_name_reservation':'CUSTOM_DESIGNED','original_economics_name_reuse_ack':'UNRECOVERED'},'activation':'CANDIDATE_APPLICATION_SOURCE_INTEGRATED_AWAITING_FULL_BUILD_TCP_AND_NATIVE_CLIENT_NOT_FORMAL','tests':['tests/storage_owned_guild_disband_0081.cpp','tests/test_owned_guild_disband_service_0081.cpp','tests/test_owned_guild_disband_wire_0081.cpp','tests/test_recovered_world_records.cpp'],'evidence':['artifacts/research/native-guild-management-0081/disband-plan-v01/report.json','artifacts/research/native-guild-management-0081/storage-validation-v01/report.json','artifacts/research/native-guild-management-0081/storage-validation-v01/sealed-result.json','artifacts/research/native-guild-management-0081/runtime-draft-v01/delivery-final.json'],'acceptance':{'private_shadow_storage_assertions_passed':49111,'private_shadow_service_checks_passed':10437,'full_Application_candidate_compiled':False,'Application_TCP_accepted':False,'actual_client_acceptance':False,'formal_installed':False,'current_native_workflow_percent':0,'whole_game_percent':None},'replacement':'Replace custom restrictions only with independent build-matched original authority and preserved-save actual-client regressions.'})
 assert updated['designs'][:-1]==original['designs'];changes['docs/custom-designs.json']=(json.dumps(updated,ensure_ascii=False,indent=2)+'\n').encode()
 out.mkdir(parents=True,exist_ok=False);before={};after={}
 for index,(name,content) in enumerate(changes.items()):
  p=ROOT/name
  if p.exists():
   before[name]=sha(p);(out/(str(index).zfill(2)+'-'+p.name+'.before')).write_bytes(p.read_bytes())
  else:before[name]=None
 for name,content in changes.items():(ROOT/name).write_bytes(content);after[name]=sha(ROOT/name)
 assert (ROOT/'src/db/SqliteOwnedGuildMembershipRepository.h').read_bytes().replace(decl,b'',1)==h
 assert (ROOT/'src/db/SqliteOwnedGuildMembershipRepository.cpp').read_bytes().replace(method,b'',1)==c
 assert (ROOT/'tests/CMakeLists.txt').read_bytes().replace(addition,b'',1)==cm
 assert sha(active)=='619f04ce6a09bdc2307e59a2d82f9db0bf7a92d4d81fee710843bf63b27d973e'
 write(out/'source-addition-proof.json',{'accepted_additive_source_integration':True,'before':before,'after':after,'old_Application_bytes_restorable':True,'old_storage_methods_bytes_restorable':True,'old_CMake_bytes_restorable':True,'all_prior_registry_records_exact':True,'formal_binary_unchanged':True,'actual_native75_acceptance':False,'full_candidate_compiled':False,'whole_game_percent':None})
 gate=subprocess.run([sys.executable,'-X','utf8','-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,text=True,encoding='utf-8',capture_output=True,check=True);assert load_json(gate.stdout)['accepted'];write(out/'frozen-gate.json',load_json(gate.stdout))
 print(json.dumps({'accepted_source_integration':True,'formal_binary_unchanged':True,'frozen_chat_pass':True,'files':len(changes)}))
def load_json(s):return json.loads(s)
if __name__=='__main__':main()
