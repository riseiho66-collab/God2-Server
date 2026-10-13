from pathlib import Path
import subprocess,hashlib,json
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
O=A/'round364-cn-command-common-definition-authority'
H='1d22ee991fa4ca899ddef051511bba738a54cb77'
assert O.exists() and not (O/'seal.json').exists(),'partial predecessor only'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==H
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,'preserved partial bytes differ'
 else:p.write_bytes(b)
def j(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
files=['src/cn/world/SharedNativeBattleCommandData.h','src/cn/world/SharedNativeBattleCommandData.cpp','src/cn/world/SharedNativeBattleCommandGroups.h','src/cn/world/SharedNativeBattleCommandGroups.cpp','src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/db/NativeSkillSource.h','src/cn/world/CnBattleSkillSelectionSource.h','src/cn/world/CnBattleSkillSelectionSource.cpp','src/cn/protocol/CnBattleSkillDefinition.h','src/db/SqliteCompanionRepository.h','src/db/SqliteCompanionRepository.cpp','src/handlers/RecoveredOwnedCompanions.h','src/handlers/RecoveredOwnedCompanions.cpp','src/protocol/TaiwanNativeDeityRosterPrefix.h','src/protocol/RecoveredDeityState.h','src/game/SharedTaiwanOwnedDeitySkillSource.h','src/game/SharedTaiwanOwnedDeitySkillSource.cpp','src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/core/Application.cpp']
refs=[];raw={}
for rel in files:
 b=subprocess.check_output(['git','show',H+':'+rel],cwd=R);raw[rel]=b
 dest='baseline/'+rel;put(dest,b)
 refs.append(dict(actual_path=str(R/rel),retained=str(O/dest),bytes=len(b),sha256=sha(b)))
j('source-references.json',refs)
j('source-custody.json',dict(source_state='immutable committed baseline, NOT current candidate',head=H,whole_count=len(refs),whole_bytes=sum(v['bytes'] for v in refs),all_wholes_from_git_show=True,working_file_observations=[dict(actual_path=str(R/p),bytes=len((R/p).read_bytes()),sha256=sha((R/p).read_bytes()),baseline_sha256=sha(raw[p])) for p in files[:2]]))
spec=[('src/cn/world/SharedNativeBattleCommandData.h',40,91),('src/cn/world/SharedNativeBattleCommandData.cpp',85,171),('src/cn/world/SharedNativeBattleCommandData.cpp',188,235),('src/cn/world/SharedNativeBattleCommandGroups.cpp',111,167),('src/cn/assets/CnSharedSkillCatalog.cpp',51,96),('src/db/NativeSkillCatalog.cpp',110,136),('src/db/SharedSkillDefinition.h',12,74),('src/handlers/RecoveredOwnedCompanions.cpp',24,76),('src/protocol/TaiwanNativeDeityRosterPrefix.h',103,118),('src/protocol/RecoveredDeityState.h',43,92),('src/db/SqliteCompanionRepository.h',35,83),('src/core/Application.cpp',1022,1103),('src/core/Application.cpp',4848,4968)]
cuts=[]
for i,(rel,a,z) in enumerate(spec):
 lines=raw[rel].splitlines(keepends=True);assert 0<a<=z<=len(lines)
 b=b''.join(lines[a-1:z]);dest=f'cuts/{i:02d}-{Path(rel).stem}-{a}-{z}.txt';put(dest,b)
 cuts.append(dict(actual_path=str(R/rel),retained=str(O/dest),bytes=len(b),sha256=sha(b),first_line=a,last_line=z,source_head=H,source_whole_sha256=sha(raw[rel])))
j('cut-references.json',cuts)
prior=A/'round363-owned-input-continuation-independent-source-review';sb=(prior/'seal.json').read_bytes();s=json.loads(sb);rows=s['members'];total=0
assert len(rows)==s['member_count']==47
for v in rows:
 p=prior/v['path'];assert p.resolve().is_relative_to(prior.resolve());b=p.read_bytes()
 assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256'];total+=len(b)
assert total==s['member_bytes']==3325354
j('prior-individual-verification.json',dict(package=str(prior),seal_sha256=sha(sb),member_count=len(rows),member_bytes=total,verified_every_member=True))
report='''# Round364 CN command common-definition authority proposal

PASS_SOURCE_DESIGN; immutable baseline 1d22ee991fa4ca899ddef051511bba738a54cb77. No tracked source changes, product execution, SQL, tests or native execution. The two future modified command files are captured exclusively from committed git blobs; working-file digests are observations, not baseline equality claims.

Existing concrete C35 core handoff: SharedNativeBattleCommandData resolve owns ordered rows, prepare passes Resolved to actual DataAuthority.current and prepare, execute_group passes the retained Resolved once to actual settlement. Append optional owning SharedSkillDefinition at Row END; Skill resolve uses actual CnSharedSkillCatalog.lookup_shared, retaining requested_native separately. Optional actual selection must equal the whole requested_native Record. Existing CN raw110 skill_fields parsing and exact operand key gate stay native; chosen TW common profile never substitutes CN raw. Item/Opaque common fields remain absent.

resources_current must lookup_shared again and compare both original requested_native and full retained common definition without mutation/rebase. Keep catalog/source lifetime fences, native selected-list identity/current, actor/learned/rules/cost authority and inventory result-based qualification. Default value equality covers source, profiles, raw, qualification, text, chosen index and owner rule. Definition availability grants no entitlement.

Preparation callback window: baseline after authority.current and prepare checks transport fence only. Retaining the same owning value is proven; full current after those observer windows is NOT proven by that fence. Root has approved this mandatory cut: use one resolved_resources_current helper to validate the same owning Resolved before/after actual authority.current and prepare, before retaining Input/returning plan; Input resources_current delegates to the same helper. Never fresh resolve/rebase. Candidate review must verify these actual cuts. After real execute, failed metadata/current checks terminate the existing source and do not roll back a committed prefix, reset execute-once, retry settlement or invent delivery success.

Existing true saved supplier is SqliteCompanionRepository private roster/SelectedDeitySkillReadset, consumed by actual normal restoration and owned checkpoint. Its TW display geometry/template restrictions and explicit 126/150 exceptions remain unchanged. RecoveredOwnedCompanions normal_entry_prefix reads historical TW448 raw definitions; TaiwanNativeDeityRosterPrefix explicitly pins 448/149c, not installed453/custom/CN raw. SharedTaiwanOwnedDeitySkillSource Observation likewise qualifies original TW definition plus saved ownership, not issued87/control/actor/turn authority.

CnSharedSkillCatalog.lookup_shared first requires privately qualified original CN453 and exact China profile. Original missing126/150 therefore remains missing despite common OwnerRule metadata. Native subject/list/learned/actor/host adapters and custom CN resources remain separate supplier gaps. No companions Context pointer or unfed new owner is proposed. The narrow two-file handoff is implementable; hosting, full route, grants, native formula and native acceptance credits all zero.

Next actual action: authorized two-file implementation, then independent candidate review of resolve, observer cuts, resources_current full equality and unchanged settlement/replay guards. Existing shared saved supplier may be consumed only with actual owner/account/character and CN subject mapping; no fake raw rows or weakening private identities.
'''
put('REPORT.md',report.encode())
helper=Path(__file__).read_bytes();assert b'\r' not in helper and not helper.startswith(b'\xef\xbb\xbf') and helper.endswith(b'\n') and not helper.endswith(b'\n\n');put('capture_cn_command_authority364_v2.py',helper)
j('capture-receipt.json',dict(status='PASS_SOURCE_DESIGN',head=H,whole_count=len(refs),whole_bytes=sum(v['bytes'] for v in refs),cut_count=len(cuts),cut_bytes=sum(v['bytes'] for v in cuts),executions=1,preserved_failed_predecessor=True))
members=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
seal=dict(status='PASS_SOURCE_DESIGN',member_count=len(members),member_bytes=sum(v['bytes'] for v in members),members=members)
j('seal.json',seal)
for v in members:
 p=O/v['path'];assert p.resolve().is_relative_to(O.resolve());b=p.read_bytes();assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256']
assert json.loads((O/'seal.json').read_bytes())==seal
print(json.dumps(dict(package=str(O),member_count=seal['member_count'],member_bytes=seal['member_bytes'],seal_bytes=(O/'seal.json').stat().st_size,seal_sha256=sha((O/'seal.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
