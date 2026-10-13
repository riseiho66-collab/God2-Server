from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round364-cn-command-common-definition-implementation';H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,b):
 q=D/p;assert not q.exists(),str(q);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
def js(p,v):save(p,(json.dumps(v,indent=2,ensure_ascii=True)+'\n').encode())
assert not (D/'capture-success.json').exists() and not (D/'seal.json').exists()
stages=[json.loads((D/p).read_bytes()) for p in ['exact-edits-and-inverse.json','continuation-correction-v3.json']];pins=json.loads((D/'final-current-pins-v3.json').read_bytes());assert sum(len(v['edits']) for v in stages)==19;refs=[];inv=[]
for pin in pins:
 p=pin['path'];b=(S/p).read_bytes();assert len(b)==pin['bytes'] and H(b)==pin['sha256'];assert b==(D/'corrected-candidate-v3'/p).read_bytes();old=b
 for stage in reversed(stages):
  for e in reversed([e for e in stage['edits'] if e['path']==p]):
   assert type(e.get('count',1)) is int and e.get('count',1)==1;x,y=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']);assert x and y and old.count(y)==1;old=old.replace(y,x)
 assert old==(D/'before'/p).read_bytes();base=subprocess.run(['git','show','1d22ee991fa4ca899ddef051511bba738a54cb77:'+p],cwd=S,check=True,capture_output=True).stdout;assert old==base
 q='final/'+p;save(q,b);refs.append({'actual_path':(S/p).as_posix(),'retained':q,'bytes':len(b),'sha256':H(b)});inv.append({'path':p,'whole_inverse':True,'baseline_bytes':len(old),'baseline_sha256':H(old),'bytes':len(b),'sha256':H(b)})
deps=['src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/world/CnBattleSkillSelectionSource.h','src/cn/world/CnBattleSkillSelectionSource.cpp','src/cn/protocol/CnBattleSkillDefinition.h','src/cn/protocol/CnBattleSkillSelection.h','src/cn/protocol/CnBattleInventorySlot.h','src/cn/world/SharedNativeBattleCommandGroups.h','src/cn/world/SharedNativeBattleCommandGroups.cpp','src/cn/world/SharedNativeBattleCommandSource.h','src/cn/world/SharedNativeBattleCommandSource.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp','src/core/Application.cpp','src/main.cpp']
for p in deps:
 b=(S/p).read_bytes();base=subprocess.run(['git','show','1d22ee991fa4ca899ddef051511bba738a54cb77:'+p],cwd=S,check=True,capture_output=True).stdout;assert b==base,p
 q='dependencies/'+p;save(q,b);refs.append({'actual_path':(S/p).as_posix(),'retained':q,'bytes':len(b),'sha256':H(b)})
hm=[]
for name in ['apply_cn_command_common_definition364.py','correct_cn_command_common_continuation364_v2.py','correct_cn_command_common_continuation364_v3.py','capture_cn_command_common_definition364.py','seal_cn_command_common_definition364.py']:
 b=(A/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n')
 if(D/name).exists():assert (D/name).read_bytes()==b
 else:save(name,b)
 hm.append({'actual_path':(A/name).as_posix(),'retained':name,'bytes':len(b),'sha256':H(b),'successful_execution_count':0 if name=='correct_cn_command_common_continuation364_v2.py' else 1,'public_copy':name in ['capture_cn_command_common_definition364.py','seal_cn_command_common_definition364.py']})
U=A/'round364-cn-command-common-definition-authority';sb=(U/'seal.json').read_bytes();meta=json.loads(sb);seen=set();total=0
for m in meta['members']:
 assert type(m['bytes']) is int and m['bytes']>=0;p=(U/m['path']).resolve();assert p.is_relative_to(U.resolve());assert m['path'].casefold() not in seen;seen.add(m['path'].casefold());b=p.read_bytes();assert len(b)==m['bytes'] and H(b)==m['sha256'];total+=len(b)
assert len(seen)==46 and total==1841072 and meta['member_count']==len(seen) and meta['member_bytes']==total
save('upstream/authority-seal.json',sb);js('upstream-individual-verification.json',{'actual_path':U.as_posix(),'seal_sha256':H(sb),'member_count':len(seen),'member_bytes':total,'members':meta['members'],'all_individual_verified':True})
cs=[('src/cn/world/SharedNativeBattleCommandData.h',37,58),('src/cn/world/SharedNativeBattleCommandData.cpp',9,66),('src/cn/world/SharedNativeBattleCommandData.cpp',130,226),('src/cn/world/SharedNativeBattleCommandData.cpp',237,300),('src/cn/world/SharedNativeBattleCommandData.cpp',300,327),('src/cn/assets/CnSharedSkillCatalog.cpp',76,97),('src/cn/world/SharedNativeBattleCommandGroups.cpp',117,160),('src/cn/net/SharedCredentialServer.h',22,60),('src/cn/net/SharedCredentialServer.cpp',214,239),('src/core/Application.cpp',7867,7883)];cuts=[]
for n,(p,i,j) in enumerate(cs):
 ls=(S/p).read_bytes().splitlines(keepends=True);assert 0<i<=j<=len(ls);b=b''.join(ls[i-1:j]);q='cuts/'+str(n).zfill(2)+'-'+Path(p).name+'.txt';save(q,b);cuts.append({'source':p,'first_line':i,'last_line':j,'retained':q,'bytes':len(b),'sha256':H(b)})
js('source-references.json',refs);js('whole-inverse-verification.json',{'baseline':'1d22ee991fa4ca899ddef051511bba738a54cb77','chronological_edits':19,'files':inv});js('helper-metadata.json',hm);js('source-cuts.json',cuts)
js('manual-invariants.json',{'status':'PASS_SOURCE_ONLY','modified_existing_files':2,'new_cpp_files':0,'row_common_definition_owning_end_append':True,'exact_requested_CN_native_preserved':True,'raw_skill_fields_and_key_gate_preserved':True,'domains_and_03_17_83_97_gates_preserved':True,'actual_DataAuthority_prepare_current_execute_receives_retained_Resolved':True,'full_common_and_requested_native_snapshot_equal_no_rebase':True,'pending_shared_group_old_Append_not_executed_required':True,'old_private_native_selection_holder_retained':True,'new_snapshot_value_not_private_storage_identity':True,'pure_item_opaque_no_new_prefix_guard':True,'mixed_inventory_actual_current_and_used_cells_not_fullbank_new_equality':True,'execute_once_and_postResult_contract_unchanged':True,'sequential_current_not_catalog_atomic_CAS':True,'CN_original453_no_custom126_150_fabrication':True,'hosting_or_global_route_credit':0,'formula_or_grant_recovery':False,'no_product_execution':True})
report='''# Round364 actual CN command common-definition handoff

PASS, bounded PHASE1 source integration. Exactly SharedNativeBattleCommandData.h/.cpp changed; no new C++ file. Initial14 edits plus5 continuation edits restore both whole files to published1d22ee991fa4ca899ddef051511bba738a54cb77. The initial candidate and failed correction-v2 mixed-newline preflight remain separate; source writes/candidate writes were0 for that failure. No native/API/parser/codec/SQL/compiler/test execution occurred.

An owning optional SharedSkillDefinition is appended to Row. The existing qualified CnSharedSkillCatalog.lookup_shared supplies the exact requested originalCN NativeSkillRecord independently of the complete owner-selected common profile. Both selection and direct-key variants retain CN raw/skill_fields and every Domain/03/17/83/97/raw-key gate. Real DataAuthority.prepare/current/execute_group already receive retained Resolved, so this connects same-registry definitions into the actual command-data handoff rather than creating an unused getter or factory.

Resolve and preparation observer windows requalify the exact requestedCN plus full owning common snapshot. Reobservation compares with the captured value and never replaces it to make Current succeed. For a shared Skill group continuation, old Input/plan/requests/lease/token are retained; only an unexecuted exact pendingAppend can extend. New prefix values must match, then OLD Row/native private Snapshot holders are copied into the next Input and only the suffix is added. The new Append/Final must retain issuer/group capabilities and generations. Value equality is not claimed to prove private Storage identity.

Pure Item/Opaque groups do not receive the new no-rebase prefix guard. Mixed inventory is qualified by existing old/new InventorySource.current and used prefix-cell bytes; no new old-vs-new whole-bank equality rule is added. Existing execute-once, actual Result inventory and irreversible post-COMMIT/no retry contracts remain. Current cuts are sequential: final allocation/oldCurrent observation is not a cross-catalog atomic CAS. Actual later Groups.current/execute still requalify the complete next snapshot before effects/publication.

The supplier audit remains bounded: Application supplies CN shared characters/common-world/native-skill readers, but SharedServerPlan.Context has no companion repository. Ordinary main selects run_server(config,seconds), so fullCN controllers/actor/list/control/resource providers still need an explicit real plan. OriginalTW-only saved/native observations do not create missing originalCN126/150 records. This handoff does not host a provider, grant learning/casting, recover formulas, activate customCN assets or complete a gameplay route. Native/global hosting and route credit remain0.
'''
save('REPORT.md',report.encode());js('capture-success.json',{'status':'PASS','successful_execution_count':1,'source_refs':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'current_existing_files':2,'dependency_files':len(deps),'chronological_edits':19,'no_product_execution':True})
print(json.dumps({'status':'PASS','source_refs':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'final_pins':pins,'upstream_members':len(seen),'upstream_bytes':total,'upstream_seal_sha256':H(sb)}))
