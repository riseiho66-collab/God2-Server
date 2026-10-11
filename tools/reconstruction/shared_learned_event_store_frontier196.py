"""196 actual event caller frontier; text/source copies only, no SQL/native/codec/runtime execution."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-event-frontier-01'
OUT=BASE/'agents/shared-learned-event-store-frontier'
OWN='tools/reconstruction/shared_learned_event_store_frontier196.py'
RETAINED=[
 'src/db/SqliteCompanionRepository.h','src/db/SqliteCompanionRepository.cpp',
 'src/handlers/RecoveredOwnedCompanions.h','src/handlers/RecoveredOwnedCompanions.cpp',
 'src/db/NativeSkillBookCatalog.h','src/db/NativeSkillBookCatalog.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp']
NEW_READ=[
 'src/cn/world/SharedPrebornChoices.h','src/cn/world/SharedPrebornChoices.cpp',
 'src/db/SqliteSupport.h','src/handlers/DiagnosticSupplyService.h','src/handlers/DiagnosticSupplyService.cpp',
 'src/handlers/RecoveredOwnedSupply.h','tools/skills/configure_shunying_test_deity.py',
 'tools/strike_lab/owned_deity_skill_fixture.py','tools/skills/register_shunying_skill.py',
 'tools/skills/register_thousand_bulls_skill.py','tools/strike_lab/current_skill_book_owner_chain.py',
 'src/cn/auth/SharedLoginComposition.cpp']
NEW_RANGE='src/db/SqliteRecoveredCharacterRepository.cpp'
# Publication is retained as final peer context, never a mutable peer current pin.
PUBLICATION_CONTEXT=['src/cn/world/SharedSubjectRosterPublication.h','src/cn/world/SharedSubjectRosterPublication.cpp']
ROOT_CONTEXT=['src/core/Application.cpp','src/core/SharedWorldHostPlan.h',
 'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp',
 'src/core/SharedTaiwanNativeWorldHostPlan.cpp']
LIFETIME_CONTEXT=['src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp']
CONTEXT=PUBLICATION_CONTEXT+ROOT_CONTEXT+LIFETIME_CONTEXT
ROOT_RANGES={'src/core/Application.cpp':[(555,590),(6121,6134),(6206,6247)],
 'src/core/SharedWorldHostPlan.h':[(1,65)],
 'src/cn/net/SharedCredentialServer.h':[(1,135)],
 'src/cn/net/SharedCredentialServer.cpp':[(1,280)],
 'src/core/SharedTaiwanNativeWorldHostPlan.cpp':[(9,145)],
 'src/db/SqliteDatabase.h':[(55,103)],
 'src/db/SqliteDatabase.cpp':[(1,117),(313,328)]}
STABLE=RETAINED+NEW_READ+[NEW_RANGE]
RANGES={NEW_RANGE:[(613,675)],'src/db/SqliteCompanionRepository.cpp':[(140,172)],
 'src/cn/world/SharedPrebornWindowSource.cpp':[(75,92)]}
WORDS=['apply','Apply','publish','Publication','current','qualify','pending','issued','skill','Skill',
 'owner','Owner','commit','transaction','Transaction','consume','Consumed','revision','CUSTOM-',
 'BEGIN','ROLLBACK','store_deity','INSERT','UPDATE','SELECT','records','source_']
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,b):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def dump(n,x):write(n,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def capture(names,folder,before=False):
 index={r['path']:r for r in json.loads((BASE/'before-manifest.json').read_text())} if before else {}
 rows=[]
 for i,n in enumerate(names):
  r=index.get(n);b=(BASE/r['snapshot']).read_bytes() if r else (ROOT/n).read_bytes()
  c=f'{folder}/s{i:03}.txt';write(c,b)
  rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),
   'epoch':'actual root freshbefore full source' if r else 'actual current source read epoch',
   'discovery_role':'retained195 context' if n in RETAINED else 'new bounded semantic range of retained195 file' if n==NEW_RANGE else '196 new full source semantic read' if n in NEW_READ else 'Root5 modified source context only' if n in ROOT_CONTEXT else 'bounded store lifetime context only' if n in LIFETIME_CONTEXT else '196 peer publication context only'})
 return rows
def source_ready():
 dump('before-source-origins.json',capture(STABLE+PUBLICATION_CONTEXT,'before',True))
 index={r['path'] for r in json.loads((BASE/'before-manifest.json').read_text())}
 dump('before-owned-absence.json',{'path':OWN,'absent_in_actual_root_before':OWN not in index,'new_cpp_sources':0})
 dump('initial-source-origins.json',capture([OWN],'initial'))
 dump('actual-read-context-origins.json',capture(PUBLICATION_CONTEXT,'read-context'))
 dump('native-original-inputs.json',[]);dump('original-inputs.json',[])
 sites=[]
 for n in STABLE+PUBLICATION_CONTEXT:
  for line,t in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if n in RANGES and not any(lo<=line<=hi for lo,hi in RANGES[n]):continue
   if any(w in t for w in WORDS):sites.append({'path':n,'line':line,'text':t,'role':'retained195' if n in RETAINED else 'new196 range' if n==NEW_RANGE else 'new196 read'})
 dump('source-sites.json',sites);dump('bounded-semantic-ranges.json',RANGES)
 dump('new-vs-retained.json',{'retained195_full_sources':RETAINED,'new196_full_semantic_sources':NEW_READ,
  'new196_bounded_semantic_ranges':{NEW_RANGE:RANGES[NEW_RANGE]},'new196_peer_context':PUBLICATION_CONTEXT,
  'no_new_native_fact':'Historical owner-chain emulator tool read as text only; no emulator/image/codec invocation or inferred authority'})
 dump('actual-event-chain.json',[
  {'from':'SharedWorldGameplay::initialize','to':'SharedPrebornChoices::attach_window / attach','role':'Existing actual optional child installation; actual supplied owner remains mandatory','new_discovery':False},
  {'from':'SharedPrebornChoices::receive native81','to':'pending_=Pending{actual Scope,raw Mask}','role':'Ready connection and current real issued scope; staging only, no learned transaction or output','new_discovery':True},
  {'from':'SharedPrebornChoices::receive native83','to':'pending_.reset();issued_=scope;world_.apply(scope,selection)','role':'Single designated mutation call with whole exact mask/ordered WORD choices, no local replay','new_discovery':True},
  {'from':'SharedPrebornWindowSource::apply','to':'source_.apply(scope,consumed subject/definitions/books/facts)','role':'Retained source bridge consumes issued window first; actual common entitlement/save/book debit remains external callback','new_discovery':False},
  {'from':'SharedPrebornChoices::receive apply result','to':'world_.qualify_delivery -> send_world_batch_with_publication','role':'Requires committed revision and exact supported A0/A1/A2/A3 records; old precommit Current deliberately not reused','new_discovery':True},
  {'from':'compose_native_login','to':'external SharedLoginSourceFactory(Context) / sources.world -> supplied preparation','role':'True same host/store/identity validation; no concrete learned apply supplier instantiated in inspected definition','new_discovery':True},
  {'from':'configure_shunying_test_deity::configure','to':'direct character_deities + character_deity_selection SQL inserts','role':'Fixed isolated character6/account6/test; CUSTOM_TEST_NOT_NATIVE explicit fixture, not live acquisition','new_discovery':True},
  {'from':'owned_deity_skill_fixture::assignments','to':'100 display-qualified raw S34 perfixture row','role':'Coverage fixture, not a native learned rule/ownership event','new_discovery':True},
  {'from':'register_shunying_skill / register_thousand_bulls_skill','to':'custom_skill_registry registration/candidate DB','role':'Definitions/registry only; explicit no character grants','new_discovery':True},
  {'from':'DiagnosticSupplyService::use','to':'SqliteRecoveredCharacterRepository::commit_inventory_resources','role':'Concrete preencoded supply output + owned slot/resource CAS and single transaction; CUSTOM0016/0050 nonrevival supplies, no learned mutation','new_discovery':True},
  {'from':'SqliteCompanionRepository::store_deity','to':'standalone BEGIN IMMEDIATE + character_deities CAS/readback + selection + COMMIT','role':'Retained195 trusted snapshot acquisition/import; not coupled to item consume or durable learned event receipt','new_discovery':False},
  {'from':'SharedSubjectRosterPublication::publish','to':'ordered whole30/31/34/35/selected/title records -> one held batch','role':'Postcommit full staged roster/definition/framing observation; actual real event/rules/replay owner external','new_discovery':True}])
 dump('frontier-findings.json',{
  'round':196,'decision':'No new CPP/interface: no truthful concrete native learned event owner was found in the exact inspected caller/source scope',
  'new_concrete_findings':[
   'Preborn81 is only request staging.83 is the precise single actual mutation boundary; all learning/book consumption/common IDs remain inside its supplied apply callback',
   'Actual postcommit native output is prepared and qualified after apply, then requalified in held-release approval; this is not a persistence implementation',
   'SharedLoginComposition receives factory/world suppliers and retains actual same repository/host credentials, but does not instantiate an acquisition/apply/store owner',
   'Runtime src/scripts store_deity search finds only declaration/definition. Newly inspected explicit fixture writer bypasses that API with isolated SQL seed; do not claim a live learning handler',
   'Existing item consumption changes owned diagnostic inventory/resources atomically, but its transaction contains no deity/learned row change',
   'SqliteSupport::Transaction starts its own BEGIN IMMEDIATE. Both store_deity and commit_inventory_resources own and commit separate transactions; sequential calls are not one atomic learned+book debit',
   'Custom registry registration is separate from character entitlement; display coverage fixture and historical emulator book identity are not acquisition authorities'],
  'reused195_not_new':['Existing trusted deity snapshot/raw TW provenance/three origin types','Existing shared definition/book tables','Existing owner/CAS/revision/readback techniques','Existing definition/current/native selection wrappers'],
  'qualified_search_scope':['src/scripts declarations, create/apply assignment/store_deity calls','Actual SharedPrebornChoices full receive/publish definitions','SharedPrebornWindowSource apply retained bridge','compose_native_login full definition','Explicit custom skill/fixture writers read as text only','Supply use and SQL text613..675 transaction'],
  'concrete_next_step':[
   'Find the real acquisition/forget/reforge/book-use event issuer and owned common actor/subject identity before allocating a new CPP learned interface',
   'Qualify book cell/custody/previous learned revision and true rule outcome together; a future same-store implementation must own ONE transaction encompassing learned change, book debit and durable event/replay receipt',
   'Current separate transaction primitives must not be composed as an atomic learning operation; any approved refactor requires exact source/profile/native actor mapping and preservation of existing TW custom snapshots',
   'Emit actual ordered WORLD34/35 or BATTLE87 records from the same committed owner/event/revision after complete output preparation; no inferred subjectBYTE/commonID or rawflag learned grant'],
  'not_claimed':['No evidence every file/database lacks learning','No actual DB contents observed','No native book-use/cost/learning/forget rules recovered by this source search','No local emulator experiment rerun','No new source packet/full gameplay routes'],
  'native_inputs':0,'new_native_spans':0,'new_cpp_sources':0,'modified_cpp_sources':0,'complete_route_increment':0,
  'execution':'Python-B file/source/text/hash only; inspected sqlite3/emulator tool sources are never imported or run'})
 print(json.dumps({'source_ready':True,'before_sources':len(STABLE+PUBLICATION_CONTEXT),'retained195':len(RETAINED),'new_full_reads':len(NEW_READ),'new_range_files':1,'context':len(PUBLICATION_CONTEXT),'sites':len(sites),'new_cpp':0}))
def root_context():
 dump('root-before-source-origins.json',capture(ROOT_CONTEXT+LIFETIME_CONTEXT,'root-before',True))
 observed=capture(ROOT_CONTEXT+LIFETIME_CONTEXT,'root-read')
 dump('actual-read-root-context-origins.json',observed)
 sites=[]
 for n,ranges in ROOT_RANGES.items():
  for line,t in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if any(lo<=line<=hi for lo,hi in ranges) and any(w in t for w in WORDS+['native_skills','native_skill_catalog','Context','SharedCredentialServer','stop','reset','get(','same(']):
    sites.append({'path':n,'line':line,'text':t,'role':'Root5 mutable modified definitions or bounded actual reader lifetime context'})
 dump('root-catalog-source-sites.json',sites)
 dump('root-catalog-context-review.json',{
  'actual_read_epoch':observed,'semantic_ranges':ROOT_RANGES,
  'conclusions':[
   'TW Context native_skills trailing default-null preserves legacy aggregate source absence. Application uses the migrated exact same database.native_skill_catalog reader as CN',
   'CN old8 constructor delegates to old9 empty host. Old9 delegates private10 pointer-null; explicit public10 constref delegates private10 exact reader address. The overloads are distinct; actual Application ref10 selects the explicit reader path',
   'Actual controllers Context receives native_skills pointer unchanged. No catalog lookup/import/CN provider/learned grant is constructed by the new reader binding',
   'TW Owner retains exact context.native_skills pointer; bound Factory::get calls Owner::same and rejects a changed reader while preserving null/null legacy compatibility',
   'SqliteDatabase Impl owns the connection and NativeSkillCatalog. Application DB is declared before the same-game host/controllers/listeners and outlives their normal local destruction. Constructor comments retain the external drain/lifetime obligation',
   'Borrowed Context reader is not the strong CatalogBinding reader/store-lifetime/current proof and is not a learned persistence source. CN actual provider still must qualify the complete pinned dataset'],
  'no_new_confirmed_source_defect':True,
  'limits':['Application stored as whole original but semantic review covers only listed source/call/drain ranges','SqliteDatabase.cpp stored whole but only listed ownership/construction/getter ranges were semantically read','No proof of native learned issuer, book-consume atomic transaction, gameplay rights, current database contents or client acceptance'],
  'execution':'Source reads/copies/text/hash only; no C++ build, DB access, SQL/native/codec/runtime invocation'})
 print(json.dumps({'root_context_ready':True,'root_modified_context':len(ROOT_CONTEXT),'lifetime_context':len(LIFETIME_CONTEXT),'sites':len(sites),'cpp_edits_by_agent':0}))
def final():
 current=capture(STABLE+[OWN],'current');context=capture(CONTEXT,'final-context')
 dump('current-source-origins.json',current);dump('peer-final-context-origins.json',context)
 write('initial-original-inputs-list.json',(OUT/'original-inputs.json').read_bytes())
 actual=[{'path':r['absolute_path'],'source_path':r['path'],'copy':r['copy'],'bytes':r['bytes'],'sha256':r['sha256'],'role':'stable actual source' if r in current else 'peer final context only'} for r in current+context]
 (OUT/'original-inputs.json').write_bytes((json.dumps(actual,indent=2)+'\n').encode())
 epochs={n:len(json.loads((OUT/p).read_text())) for n,p in [('before','before-source-origins.json'),('root-before','root-before-source-origins.json'),('initial','initial-source-origins.json'),('refinement','refinement-source-origins.json'),('read-context','actual-read-context-origins.json'),('root-read','actual-read-root-context-origins.json')]}
 dump('findings.json',{'round':196,'new_tool':1,'new_cpp_sources':0,'modified_cpp_sources_by_agent':0,'root_modified_cpp_review_context':5,'source_epochs':epochs,'current':len(current),'final_context':len(context),'full_source_originals':sum(epochs.values())+len(current)+len(context),'actual_original_inputs':len(actual),'retained195_semantic_sources':len(RETAINED),'new_full_semantic_sources':len(NEW_READ),'new_bounded_semantic_file':1,'root_context_semantic_ranges':ROOT_RANGES,'native_inputs':0,'new_native_spans':0,'complete_route_increment':0,'current_excludes':'All peer Roster2/Root5/lifetime2 context and mutable books/catalog/reports/receipts; prior seals remain unchanged','boundary':'Concrete event/caller/transaction and actual reader Context analysis, no DB/SQL/codec/native/emulator/build/test/API/runtime execution'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 members=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files]
 dump('LIST.json',members);members.append({'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())})
 dump('seal.json',{'round':196,'source_only':True,'members':members,'member_count':len(members)})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current':len(current),'context':len(context),'actual_inputs':len(actual),'full_source_originals':sum(epochs.values())+len(current)+len(context),'tool':[r for r in current if r['path']==OWN]},indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',choices=['source-ready','root-context','final'],required=True);a=ap.parse_args()
 {'source-ready':source_ready,'root-context':root_context,'final':final}[a.stage]()
