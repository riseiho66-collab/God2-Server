from pathlib import Path
import json,base64,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-cn-common-owned-skill-commit-361';edits=[]
def rep(p,o,n):
 path=S/p;b=path.read_bytes();old=o.encode();new=n.encode()
 if b.count(old)!=1:old=old.replace(b'\n',b'\r\n');new=new.replace(b'\n',b'\r\n')
 assert b.count(old)==1,(p,b.count(old));path.write_bytes(b.replace(old,new));edits.append(dict(path=p,old_base64=base64.b64encode(old).decode(),new_base64=base64.b64encode(new).decode()))
BH='src/handlers/RecoveredBattleService.h';BC='src/handlers/RecoveredBattleService.cpp'
rep(BH,'        std::unordered_set<std::uint16_t> saved_owned_skills;','        std::unordered_set<std::uint16_t> saved_owned_skills;\n        bool nonpersistent_owned_skills{}; // Explicit existing isolated diagnostic only.')
rep(BH,'        bool owned_skill_operating{},owned_skill_reentered{};','        bool owned_skill_operating{},owned_skill_reentered{},owned_skill_remove_pending{};')
rep(BC,'        (bool(checkpoint_commit)!=bool(owned_checkpoint_commit)))) ||\n       (!policy.owned_skill_repository && owned_checkpoint_commit))','        (policy.nonpersistent_owned_skills ?\n            (!policy.diagnostic_single_action || checkpoint_commit || owned_checkpoint_commit) :\n            (!checkpoint_commit || !owned_checkpoint_commit)))) ||\n       (!policy.owned_skill_repository && (owned_checkpoint_commit || policy.nonpersistent_owned_skills)))')
rep(BC,'        bool& active;explicit OperationExit(bool& value) noexcept:active(value){}\n        ~OperationExit(){active=false;}','        RecoveredBattleService& service;std::uint64_t id;bool& active;bool& remove_pending;\n        OperationExit(RecoveredBattleService& owner,std::uint64_t key,bool& value,bool& pending) noexcept\n            :service(owner),id(key),active(value),remove_pending(pending){}\n        ~OperationExit(){active=false;if(remove_pending)service.remove(id);}')
rep(BC,'        owned_operation.emplace(bound.owned_skill_operating);','        owned_operation.emplace(*this,session.id(),bound.owned_skill_operating,bound.owned_skill_remove_pending);')
rep(BC,'        if(owned_skill)bound.owned_checkpoint_commit(before,after,*owned_skill);\n        else bound.checkpoint_commit(before,after);\n    }\n    bound.battle=std::move(staged);','        if(owned_skill)bound.owned_checkpoint_commit(before,after,*owned_skill);\n        else bound.checkpoint_commit(before,after);\n    }\n    // Persistence must obey the existing no-reentry/no-send callback contract.\n    // This fence prevents stale in-memory publication; it cannot undo COMMIT.\n    if(owned_skill)current_owned();\n    bound.battle=std::move(staged);')
rep(BC,'        it->second.owned_skill_reentered=true;return;','        it->second.owned_skill_reentered=true;it->second.owned_skill_remove_pending=true;return;')
rep('src/core/Application.cpp','                                                policy.owned_skill_repository=&database.companions();','                                                policy.owned_skill_repository=&database.companions();\n                                                policy.nonpersistent_owned_skills=!config.diagnostic_battle_resources;')
with (D/'source-inverse-repairs.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(edits,f,indent=2);f.write('\n')
print(json.dumps(dict(repairs=len(edits),deferred_remove=True,explicit_existing_ephemeral_scope=True,postcommit_memory_fence=True,no_postcommit_rollback_claim=True)))
