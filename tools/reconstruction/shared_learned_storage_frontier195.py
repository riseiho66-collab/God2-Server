"""195 bounded source/storage frontier; file copies/text/hash only, never DB/SQL execution."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-owner-frontier-01'
OUT=BASE/'agents/shared-learned-storage-frontier'
OWN='tools/reconstruction/shared_learned_storage_frontier195.py'
STABLE=[
 'src/db/RecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.h',
 'src/db/SqliteRecoveredCharacterRepository.cpp','src/db/SqliteCompanionRepository.h','src/db/SqliteCompanionRepository.cpp',
 'src/db/NativeSkillBookCatalog.h','src/db/NativeSkillBookCatalog.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp',
 'src/db/InventoryRepository.h','src/db/Migration.cpp','src/protocol/RecoveredDeityState.h',
 'src/handlers/RecoveredOwnedCompanions.h','src/handlers/RecoveredOwnedCompanions.cpp',
 'src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp',
 'src/game/Battle.h','src/game/Battle.cpp','src/game/FixtureBattle.h','src/game/FixtureBattle.cpp',
 'src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp',
 'src/cn/world/CnPrebornSkillChoiceSource.h','src/cn/world/CnPrebornSkillChoiceSource.cpp',
 'src/cn/world/CnPrebornSkillReferences.h','src/cn/world/CnPrebornSkillReferences.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'src/cn/world/SharedSubjectSkillPublication.h','src/cn/world/SharedSubjectSkillPublication.cpp',
 'src/cn/world/SharedNativeBattleCommandData.h','src/cn/world/SharedNativeBattleCommandData.cpp',
 'src/cn/world/SharedBattleSkillPublication.h','src/cn/world/SharedBattleSkillPublication.cpp',
 'src/cn/protocol/CnWorldSubjectSkillUpdate.h','scripts/gameplay/combat.lua','scripts/fixtures/combat.lua']
# This file is retained whole as context, but only the named bounded spans were
# semantically inspected. It is never a stable current pin of this agent.
CONTEXT=['src/core/Application.cpp']
READ_RANGES={
 'src/core/Application.cpp':[(637,702),(5486,5730),(5871,5928)],
 'src/db/Migration.cpp':[(223,249),(287,320)],
 'src/handlers/RecoveredBattleService.cpp':[(1,220),(221,570)],
 'src/db/SqliteCompanionRepository.cpp':[(1,174),(175,360)]}
WORDS=['learned','skills','skill','Skill','DataAuthority','character_deities','CUSTOM-',
 'store_deity','source_sha256','revision','require_owner','require_provenance','Transaction',
 'commit','Commit','Qualify','qualify','apply','current','source_offset']
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,b):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def dump(n,x):write(n,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def capture(names,folder,before=False):
 index={r['path']:r for r in json.loads((BASE/'before-manifest.json').read_text())} if before else {}
 rows=[]
 for i,n in enumerate(names):
  r=index.get(n)
  b=(BASE/r['snapshot']).read_bytes() if r else (ROOT/n).read_bytes()
  c=f'{folder}/s{i:03}.txt';write(c,b)
  rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),
   'epoch':'actual freshbefore1398 full source' if r else 'actual read epoch full source',
   'semantic_read':'bounded listed ranges, whole retained' if n in READ_RANGES else 'source/interface inspection; whole retained'})
 return rows
def sources_ready():
 dump('before-source-origins.json',capture(STABLE+CONTEXT,'before',True))
 index={r['path'] for r in json.loads((BASE/'before-manifest.json').read_text())}
 dump('before-owned-absence.json',{'path':OWN,'absent_in_actual_root_before':OWN not in index,'new_cpp_sources':0})
 dump('initial-source-origins.json',capture([OWN],'initial'))
 dump('actual-read-context-origins.json',capture(CONTEXT,'read-context'))
 dump('native-original-inputs.json',[])
 dump('original-inputs.json',[])
 sites=[]
 for n in STABLE+CONTEXT:
  for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if n in READ_RANGES and not any(lo<=line<=hi for lo,hi in READ_RANGES[n]):continue
   if any(w in text for w in WORDS):sites.append({'path':n,'line':line,'text':text})
 dump('source-sites.json',sites)
 dump('bounded-semantic-read-ranges.json',READ_RANGES)
 dump('frontier-findings.json',{
  'round':195,'scope':'Current server interfaces, SQL source text, actual bounded callers and CN source suppliers; no DB content observation',
  'facts':[
   {'source':'src/db/RecoveredCharacterRepository.h','fact':'Full interface provides character/resources/role/experience/position/battle settlement; no learned-skill load/commit API'},
   {'source':'src/db/SqliteCompanionRepository.cpp','fact':'Concrete trusted owned deity persistence exists: require_owner account/character, complete raw S34 skills, expected revision CAS in transaction, readback, pending-battle rejection'},
   {'source':'src/db/SqliteCompanionRepository.h','fact':'StoredDeity holds snapshot/revision/CompanionProvenance, selected_deity_has_skill compares selected owned raw kind/id; bool has no CN mapping or provenance-type discriminator'},
   {'source':'src/db/Migration.cpp','fact':'character_deities stores TW 19B declaration/29B status/4B skill list, fixed TW70a4 source and three origin labels; character_deity_selection has separate revision/FK'},
   {'source':'src/protocol/RecoveredDeityState.h','fact':'TW projection gates portrait/current icon eligibility and accepts custom kind0 IDs126/150; display eligibility is not native learned/cast authority'},
   {'source':'src/core/Application.cpp','fact':'Actual inspected calls selected_deity_has_skill feed CUSTOM0058/0059 diagnostic trusted policies/87 seeds. Fixture service is explicit config-isolated; no CN learned supplier found in these caller spans'},
   {'source':'src/db/NativeSkillBookCatalog.cpp','fact':'Lookup resolves source+book+definition binding with fixed TW dataset/hash/381 rows; no owner, learned row, consumption or commit'},
   {'source':'src/cn/assets/CnSharedSkillCatalog.cpp','fact':'Existing common catalog tables accept exact CN453 definition rows through explicit dataset/source/raw provenance; matching definitions do not establish shared gameplay skill identity'},
   {'source':'src/cn/world/SharedPrebornWindowSource.h','fact':'Actual apply and postcommit qualifier must be supplied; source retains full definitions/order/optional native selection evidence but performs no concrete learned store transaction'},
   {'source':'src/cn/world/SharedSubjectSkillPublication.h','fact':'WORLD34/35 supplies postcommit publication only, true subject mapping/revision/save/replay/learning qualifier mandatory'},
   {'source':'src/cn/world/SharedBattleSkillPublication.h','fact':'BATTLE87 retains ordered supplied rawWORD events and full catalog definitions/held release receipt; true committed learned event/actor mapping/replay owner remains mandatory'},
   {'source':'src/cn/world/SharedNativeBattleCommandData.h','fact':'DataAuthority is explicit required supplier for learned/custody/actor/rules/grant; definition and optional selection provenance are separate'},
   {'source':'src/game/Battle.h','fact':'Transactional action/checkpoint core is labelled CUSTOM0007; RecoveredBattleService is CUSTOM0008 trusted diagnostic policy and FixtureBattle explicitly non-native'},
   {'source':'scripts/gameplay/combat.lua','fact':'CUSTOM0006 formula and fixture CUSTOM0001 cannot be promoted as recovered CN rules'},
   {'source':'src/db/InventoryRepository.h','fact':'Reserved empty inventory interface cannot provide learned-book item custody'}],
  'reusable_without_relabeling':[
   'Common account/character ownership checks, source provenance, expected revision CAS, transaction/readback and separate selection revision mechanisms',
   'Existing native_data_sources/native_skill_catalog shared tables with explicit CN dataset/source/raw identity',
   'Existing actual ready presence/transports and publication delivery lifetime; no new server or per-region gameplay DB'],
  'not_directly_reusable_as_cn_native_grant':[
   'TW S34 saved bytes, TW deity key/portrait/icon gates and TW70a4 provenance accepted with custom labels',
   'Same kind/id/book item name, native UI flag or catalog definition match without actual common actor/skill mapping',
   'CUSTOM diagnostic Policy.skills/basic target/source position/cost or fixture formula'],
  'qualified_absence':'Within retained RecoveredCharacterRepository, SqliteCompanionRepository, CN catalog/preborn/subject/battle suppliers and inspected Application callers, no concrete CN learned transaction/actor owner was identified. This is not global proof that every uninspected file/database lacks learned data.',
  'next_required_real_source':[
   'Actual common actor/owned subject identity plus explicitly qualified CN WORLD subject BYTE and BATTLE actor/list incarnation mapping',
   'True learned acquisition/change rule, previous/next committed revision and durable receipt/replay; preserve origin/profile rather than bulk promote old rows',
   'True CN source definition identity and optional recovered list/pointer lineage, not a client-memory operational prerequisite',
   'True cost/grant/MP/item/timing/target battle policy and complete supplied publication records from the same committed owner'],
  'implementation_decision':'Research/source frontier only; no new empty interface or guessed permission CPP',
  'native_inputs':0,'new_native_spans':0,'new_cpp_sources':0,'complete_route_increment':0,'execution':'Python-B file/source copies/text/hash only'})
 print(json.dumps({'source_ready':True,'before_sources':len(STABLE+CONTEXT),'stable_sources':len(STABLE),'context_sources':len(CONTEXT),'sites':len(sites),'new_cpp_sources':0}))
def final():
 current=capture(STABLE+[OWN],'current');context=capture(CONTEXT,'final-context')
 dump('current-source-origins.json',current);dump('root-final-context-origins.json',context)
 write('initial-original-inputs-list.json',(OUT/'original-inputs.json').read_bytes())
 actual=[{'path':r['absolute_path'],'source_path':r['path'],'copy':r['copy'],'bytes':r['bytes'],'sha256':r['sha256'],'role':'stable actual source' if r in current else 'bounded read root context only'} for r in current+context]
 (OUT/'original-inputs.json').write_bytes((json.dumps(actual,indent=2)+'\n').encode())
 epochs={n:len(json.loads((OUT/p).read_text())) for n,p in [('before','before-source-origins.json'),('initial','initial-source-origins.json'),('read-context','actual-read-context-origins.json')]}
 dump('findings.json',{'round':195,'new_tool':1,'new_cpp_sources':0,'modified_cpp_sources':0,'current_sources':len(current),'final_context':len(context),'source_epochs':epochs,'full_source_originals':sum(epochs.values())+len(current)+len(context),'actual_original_inputs':len(actual),'native_inputs':0,'new_native_spans':0,'complete_route_increment':0,'current_excludes':'Application root context, all new/mutable peers, mutable books/catalog/ledger/reports/receipts','research_boundary':'Retained full sources plus precise bounded semantic ranges; no DB/SQL/game/native/codec execution'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 members=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files]
 dump('LIST.json',members);members.append({'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())})
 dump('seal.json',{'round':195,'source_only':True,'members':members,'member_count':len(members)})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current':len(current),'context':len(context),'actual_inputs':len(actual),'full_source_originals':sum(epochs.values())+len(current)+len(context),'tool':[r for r in current if r['path']==OWN]},indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',choices=['source-ready','final'],required=True);a=ap.parse_args()
 sources_ready() if a.stage=='source-ready' else final()
