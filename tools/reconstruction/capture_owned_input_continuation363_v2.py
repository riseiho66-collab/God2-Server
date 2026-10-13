from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round363-owned-bootstrap-input-continuation-implementation';H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,b):
 q=D/p;assert not q.exists(),str(q);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
def js(p,v):save(p,(json.dumps(v,indent=2,ensure_ascii=True)+'\n').encode())
assert not (D/'capture-success.json').exists() and not (D/'seal.json').exists()
stages=[json.loads((D/p).read_bytes()) for p in ['exact-edits-and-inverse.json','correction-v3.json','correction-v5.json','correction-v6.json','correction-v7.json']];pins=json.loads((D/'final-current-pins-v7.json').read_bytes());refs=[];inverse=[]
assert sum(len(v['edits']) for v in stages)==42
for pin in pins:
 p=pin['path'];b=(S/p).read_bytes();assert len(b)==pin['bytes'] and H(b)==pin['sha256'];assert b==(D/'corrected-candidate-v7'/p).read_bytes();old=b
 for stage in reversed(stages):
  for e in reversed([e for e in stage['edits'] if e['path']==p]):
   assert type(e.get('count',1)) is int and e.get('count',1)==1;x,y=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']);assert x and y and old.count(y)==1;old=old.replace(y,x)
 assert old==(D/'before'/p).read_bytes()
 base=subprocess.run(['git','show','566923291db5de40dcc7d1a153cde60cfc94d87c:'+p],cwd=S,check=True,capture_output=True).stdout;assert base==old
 q='current-v7/'+p;save(q,b);refs.append({'actual_path':(S/p).as_posix(),'retained':q,'bytes':len(b),'sha256':H(b)})
 inverse.append({'path':p,'whole_literal_inverse':True,'baseline_bytes':len(old),'baseline_sha256':H(old),'final_bytes':len(b),'final_sha256':H(b)})
deps=['src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp','src/db/SqliteCompanionRepository.h','src/db/SqliteCompanionRepository.cpp','src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/game/ShunyingSanshazhan.h','src/game/ThousandBulls.h','src/protocol/RecoveredWorldFrame.h','src/protocol/RecoveredDeityState.h','src/game/Battle.h','src/core/Application.h','src/core/Config.h','src/core/Config.cpp','src/protocol/RecoveredWorldRecords.h']
for p in deps:
 b=(S/p).read_bytes();base=subprocess.run(['git','show','566923291db5de40dcc7d1a153cde60cfc94d87c:'+p],cwd=S,check=True,capture_output=True).stdout;assert b==base,p
 q='frozen-v7/'+p;save(q,b);refs.append({'actual_path':(S/p).as_posix(),'retained':q,'bytes':len(b),'sha256':H(b)})
helper_names=['apply_owned_input_continuation363.py','apply_owned_input_continuation363_v2.py','correct_owned_input_continuation363_v3.py','correct_owned_input_continuation363_v4.py','correct_owned_input_continuation363_v5.py','correct_owned_input_continuation363_v6.py','correct_owned_input_continuation363_v7.py','capture_owned_input_continuation363.py','capture_owned_input_continuation363_v2.py','seal_owned_input_continuation363.py'];hm=[]
for name in helper_names:
 b=(A/name).read_bytes();assert not b.startswith(b'\xef\xbb\xbf') and b'\r' not in b and b.endswith(b'\n') and not b.endswith(b'\n\n')
 if (D/name).exists():assert (D/name).read_bytes()==b
 else:save(name,b)
 ok=name not in ('apply_owned_input_continuation363.py','correct_owned_input_continuation363_v4.py','capture_owned_input_continuation363.py')
 hm.append({'actual_path':(A/name).as_posix(),'retained':name,'bytes':len(b),'sha256':H(b),'successful_execution_count':1 if ok else 0,'public_successful_copy':name in ('capture_owned_input_continuation363_v2.py','seal_owned_input_continuation363.py'),'product_execution':False})
U=A/'round363-owned-bootstrap-input-continuation-proposal';sb=(U/'SEAL.json').read_bytes();meta=json.loads(sb);seen=set();total=0
for m in meta['members']:
 assert type(m['bytes']) is int and m['bytes']>=0;p=(U/m['path']).resolve();assert p.is_relative_to(U.resolve());assert m['path'].casefold() not in seen;seen.add(m['path'].casefold());b=p.read_bytes();assert len(b)==m['bytes'] and H(b)==m['sha256'];total+=len(b)
assert len(seen)==22 and total==1121940 and meta['member_count']==len(seen) and meta['member_bytes']==total
save('upstream/authority-SEAL.json',sb);js('upstream-individual-verification.json',{'actual_path':U.as_posix(),'seal_sha256':H(sb),'member_count':len(seen),'member_bytes':total,'all_individual_verified':True,'members':meta['members']})
cs=[('src/net/Session.cpp',325,376),('src/net/Session.cpp',1963,2083),('src/net/Session.cpp',2243,2274),('src/net/Session.cpp',2350,2467),('src/net/Session.cpp',2505,2679),('src/net/Session.cpp',2812,2844),('src/core/Application.cpp',6497,6513),('src/net/Session.h',412,428)];ci=[]
for n,(p,i,j) in enumerate(cs):
 lines=(S/p).read_bytes().splitlines(keepends=True);assert 0<i<=j<=len(lines);b=b''.join(lines[i-1:j]);q='cuts/'+str(n).zfill(2)+'-'+Path(p).name+'.txt';save(q,b);ci.append({'source':p,'retained':q,'first_line':i,'last_line':j,'bytes':len(b),'sha256':H(b)})
js('source-references.json',refs);js('whole-inverse-verification.json',{'baseline':'566923291db5de40dcc7d1a153cde60cfc94d87c','chronological_edits':42,'files':inverse});js('helper-metadata.json',hm);js('source-cuts.json',ci)
js('manual-invariants.json',{'status':'PASS_SOURCE_ONLY','current_existing_files':3,'new_cpp_files':0,'game_installs_atomic_exact_private_attempt_before_response_post':True,'independent_lease_not_masked_by_strong_hold':True,'tls_before_game_owned_pointer_read':True,'retired_latch_blocks_posted_ingress_even_after_pointer_clear':True,'no_game_owned_account_or_character_read_on_IO':True,'raw_input_limit':16384,'original_frame_and_batch_quotas_preserved':True,'pre_arm_already_parsed_batches_not_reclassified':True,'active_hold_GAME_hook_rejects_whole_batch_before_mutation':True,'whole_FIFO_front_and_full_transferred_bytes_required':True,'all_old_throwing_completion_and_queue_bookkeeping_before_release':True,'older_read_or_game_completion_retains_its_original_continuation':True,'no_second_read':True,'physical_Written_not_demoted':True,'no_allocation_entry_failure_retirement':True,'first_close_preserves_original_cleanup':True,'unobserved_original_wire_and_rules_preserved':True,'service362_readset_and_written_gate_frozen':True,'native_ACK_or_grant':False,'general_undestroyed_executor_abort_convergence':'OPEN','native_adoption_or_all_variants':'OPEN','no_product_execution':True})
report='''# Round363 actual owned bootstrap input continuation

PASS, bounded PHASE1 source integration. Exactly Session.h/.cpp and Application.cpp changed; no new C++ file. The 42 chronological literal edits compose to exact published 566923291db5de40dcc7d1a153cde60cfc94d87c. Initial and v3/v5/v6/v7 candidates and both prewrite helper failures are retained. The first capture failed on a nonexistent readonly dependency before completion; its helper and all partial v6 snapshots remain. The v6 PASS was withdrawn before seal for the later concurrent-arm catch correction. No compiler, test, native/API/codec/parser/SQL execution occurred.

Only the actual362 hosted owned bootstrap producer opts in after its typed full-saved-roster/binding/private complete-response qualifier and fixed tuple have passed. Arm first proves actual own callback TLS, then the same private Pending WorldResponseAttempt/Data. It installs the atomic hold on GAME before original response posting. A separate callback/post/final-Write lease owns retirement; the strong atomic hold cannot mask handler drop by keeping the Attempt alive.

IO uses the exact private Attempt, atomic phase/battle generation/status and transport fields, never game-owned account/character fields or source callbacks. Read/resume/feed gates retain raw input at the unchanged16384 limit before parsing/moving staged records. Original frame/batch/skill quotas remain. A previously parsed/posted job reaching GAME while a hold or retired latch exists is rejected whole before any capture reset or App hook: it is not split, redispatched or reclassified into raw bytes.

Release requires the exact actual FIFO front/full frame/all transferred bytes and physical Written, after ALL old marker/log/pop/next-queue bookkeeping. It clears only the same hold and resumes once only when no older read/game continuation owns progress. Existing older-read bytes remain bounded; no second read is issued. Physical Written stays a fact if later cleanup or resume fails.

Opted async-write initiation, completion, complete strand handoff and raw-retention failures are contained with retained entry identity OR a concurrently activated atomic hold OR the persistent retired latch. The no-allocation failure entry first latches retirement, close request and socket/strand closure before potentially throwing logging. The persistent retired latch prevents already-posted feed/read paths from falling back to ordinary decoding after hold-pointer removal. First opted close still executes all original cleanup. Unarmed/unobserved behavior, existing parser/native packets, service362 fresh-readset/CAS/Written gates, class rules/trials, config and models are preserved.

This conservative owner transport policy is not native ACK/cache/list adoption, turn eligibility, learned grant or recovered timing. It cannot retroactively make a pre-arm parsed batch raw, and does not widen or split accepted batches. Undestroyed/unrun executor abort convergence, complete native acceptance/all variants, CN host/bank provenance and gameplay route completeness remain OPEN. No new native method/format/whole-route or balance credit.
'''
save('REPORT.md',report.encode());js('capture-success.json',{'status':'PASS','successful_execution_count':1,'source_refs':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'current_existing_files':3,'dependencies':len(deps),'chronological_edits':42,'no_product_execution':True})
print(json.dumps({'status':'PASS','source_refs':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'final_pins':pins,'upstream_members':len(seen),'upstream_bytes':total,'upstream_seal_sha256':H(sb)}))
