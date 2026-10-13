from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round362-owned-skill-bootstrap-write-implementation'
H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,b):
 q=D/p;assert not q.exists(),str(q);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
def js(p,v):save(p,(json.dumps(v,indent=2,ensure_ascii=True)+'\n').encode())
assert not (D/'capture-success.json').exists() and not (D/'seal.json').exists()
base=json.loads((D/'exact-edits-and-inverse.json').read_bytes());v4=json.loads((D/'identity-correction-v4.json').read_bytes());v5=json.loads((D/'transition-correction-v5.json').read_bytes());pins=v5['files'];refs=[];inverse=[]
for pin in pins:
 p=pin['path'];b=(S/p).read_bytes();assert len(b)==pin['bytes'] and H(b)==pin['sha256'];assert b==(D/'corrected-candidate-v5'/p).read_bytes();old=b
 for stage in (v5,v4,base):
  for e in reversed([e for e in stage['edits'] if e['path']==p]):
   x,y=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']);assert old.count(y)==1,(p,'inverse');old=old.replace(y,x)
 assert old==(D/'before'/p).read_bytes()
 head=subprocess.run(['git','show','7b5efc911fd20d8d9254f80a080a1de2d5751297:'+p],cwd=S,check=True,capture_output=True).stdout;assert old==head
 q='final/'+p;save(q,b);refs.append({'actual_path':(S/p).as_posix(),'retained':q,'bytes':len(b),'sha256':H(b)})
 inverse.append({'path':p,'whole_literal_inverse_to_7b5efc9':True,'baseline_bytes':len(old),'baseline_sha256':H(old),'final_bytes':len(b),'final_sha256':H(b)})
deps=['src/net/Session.h','src/net/Session.cpp','src/db/SqliteCompanionRepository.h','src/db/SqliteCompanionRepository.cpp','src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/game/ShunyingSanshazhan.h','src/game/ThousandBulls.h','src/protocol/RecoveredWorldFrame.h','src/protocol/RecoveredDeityState.h']
for p in deps:
 b=(S/p).read_bytes();head=subprocess.run(['git','show','7b5efc911fd20d8d9254f80a080a1de2d5751297:'+p],cwd=S,check=True,capture_output=True).stdout;assert b==head,p
 q='dependencies/'+p;save(q,b);refs.append({'actual_path':(S/p).as_posix(),'retained':q,'bytes':len(b),'sha256':H(b)})
helpers=['apply_owned_bootstrap_custody362.py','apply_owned_bootstrap_custody362_v2.py','apply_owned_bootstrap_custody362_v3.py','correct_owned_bootstrap_identity362_v4.py','correct_owned_bootstrap_transition362_v5.py','capture_owned_bootstrap_custody362.py','seal_owned_bootstrap_custody362.py'];hm=[]
for name in helpers:
 b=(A/name).read_bytes();assert not b.startswith(b'\xef\xbb\xbf') and b'\r' not in b and b.endswith(b'\n') and not b.endswith(b'\n\n')
 q=D/name
 if q.exists():assert q.read_bytes()==b
 else:save(name,b)
 hm.append({'actual_path':(A/name).as_posix(),'retained':name,'bytes':len(b),'sha256':H(b),'successful_execution_count':0 if name in helpers[:2] else 1,'product_execution':False})
up=A/'round362-shared-owned-skill-publication-authority';seal=(up/'SEAL.json').read_bytes();meta=json.loads(seal);members=meta['members'];seen=set();total=0
for m in members:
 assert type(m['bytes']) is int and m['bytes']>=0;rel=m['path'];r=(up/rel).resolve();assert r.is_relative_to(up.resolve());assert rel.casefold() not in seen;seen.add(rel.casefold());b=r.read_bytes();assert len(b)==m['bytes'] and H(b)==m['sha256'];total+=len(b)
assert len(members)==46 and total==1360898 and meta['member_count']==len(members) and meta['member_bytes']==total
save('upstream/authority-SEAL.json',seal);js('upstream-individual-verification.json',{'actual_path':up.as_posix(),'seal_sha256':H(seal),'member_count':len(members),'member_bytes':total,'members':members,'all_individual_verified':True})
cs=[('src/core/Application.cpp',6122,6192),('src/core/Application.cpp',6328,6423),('src/core/Application.cpp',6494,6512),('src/handlers/RecoveredBattleService.cpp',26,61),('src/handlers/RecoveredBattleService.cpp',146,205),('src/handlers/RecoveredBattleService.cpp',511,554),('src/db/SqliteCompanionRepository.cpp',198,217),('src/net/Session.cpp',2628,2670)];ci=[]
for n,(p,i,j) in enumerate(cs):
 ls=(S/p).read_bytes().splitlines(keepends=True);assert 0<i<=j<=len(ls);b=b''.join(ls[i-1:j]);q='cuts/'+str(n).zfill(2)+'-'+Path(p).name+'.txt';save(q,b);ci.append({'source':p,'retained':q,'first_line':i,'last_line':j,'bytes':len(b),'sha256':H(b)})
js('source-references.json',refs);js('whole-inverse-verification.json',inverse);js('helper-metadata.json',hm);js('source-cuts.json',ci)
js('manual-invariants.json',{'status':'PASS_SOURCE_ONLY','modified_existing_files':3,'new_cpp_files':0,'source_execution':False,'no_substring_boundary_proof':True,'one_full_owned_roster_supplies_both_keys':True,'same_actual_repo_typed_roster_current':True,'before_and_after_binding_guard':True,'cosmetic_epoch_not_skill_authority':True,'original_tuple_before_existing_local_transition':True,'actual_transition_result_fenced_at_capture_bind_and_return':True,'written_condition_only_on_optin_owned_C35':True,'existing361_saved_readset_and_commit_CAS_preserved':True,'native_list_adoption':False,'native_timing_recovered':False,'all907_shared_pins_byte_exact_frozen_dependency':True,'old_trials_class_bodies_and_wire_producers_unchanged':True,'known_skills':[126,150],'new_rules':0})
report='''# Round362 actual hosted owner skill bootstrap source

PASS, bounded PHASE1 source integration. Exactly Application.cpp and RecoveredBattleService.h/.cpp changed. All three whole literal inverses compose to published 7b5efc9; initial candidate, identity correction and actual-transition correction remain separate. Two prewrite apply-helper failures are retained. No target/native/C++/SQL/parser/test execution occurred.

The actual Timer36 hosted producer obtains one private full OwnedDeityRosterReadset and derives both existing kind0/126 and kind0/150 keys from the same selected saved row. The existing one-core getter checks only formal owner key/design namespace. Native/requested/profiles/chosen presence is not learned authority; missing original TW448/CN453 rows are not manufactured.

The original tuple is fenced immediately before the existing set_state(InBattle). Only that actual local transition result supplies the subsequent expected tuple; later observers cannot rebase it. The unchanged producer prepends the same actual S87 records in the same order. The final full wire is encoded once for the opt-in owned branch and captured through existing private original-callback WorldResponseWrite before binding. No arbitrary payload substring is treated as a native record-boundary proof.

The typed qualifier directly calls the bound actual companion repository deity_roster_current with an owning copy. Existing busy/reentry/deferred-remove guards protect the same Bound across observers. Both sides require exact Session/owner/controller/private receipt storage, independent owned bootstrap battle generation, active battle with no action/control consumed, and the exact expected saved key set. Cosmetic pose generation remains separate. Final App return checks the fixed expected tuple again.

Only bindings supplied this optional receipt require Written and game-owner currentness for an owned C35. Existing fresh SelectedDeitySkillReadset and atomic saved-readset/checkpoint commit remain. Absent receipts preserve explicitly trusted other bindings. Manual/revival trials and class bodies remain byte-exact; the 907 common source pin table, Session transport, native protocols and storage dependencies are unchanged.

This is passive local complete-write custody. It proves no native ACK/cache adoption, client list acceptance, turn grant or timing barrier. Pending early arrivals and native interaction timing remain acceptance gaps. Saved roster Current is not a database/socket atomic commit; durable post-COMMIT limits remain. Full primary native models, original CN custom bank/host suppliers and complete gameplay routes remain OPEN. No new balance/rule/native method/format/route completion credit.
'''
save('REPORT.md',report.encode());js('capture-success.json',{'status':'PASS','successful_execution_count':1,'source_refs':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'current_existing_files':3,'dependency_files':len(deps),'capture_helper':'capture_owned_bootstrap_custody362.py','no_product_execution':True})
print(json.dumps({'status':'PASS','source_refs':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'final_pins':pins,'upstream':{'members':len(members),'bytes':total,'seal_sha256':H(seal)}}))
