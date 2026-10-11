"""194 file/source originals and accounting only; no game/native/codec/database execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-publication-source-01/agents/shared-battle-skill-publication'
OWN=['src/cn/world/SharedBattleSkillPublication.h','src/cn/world/SharedBattleSkillPublication.cpp','tools/reconstruction/shared_battle_skill_publication194.py']
CONTEXT=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/cn/protocol/CnBattleSkillUpdate87.h','src/cn/protocol/CnBattleDeferredRecord.h']
STABLE=[r['path'] for r in json.loads((OUT/'before-source-origins.json').read_text()) if r['path'] not in CONTEXT]
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,b):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def dump(n,x):write(n,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def capture(names,folder):
 rows=[]
 for i,n in enumerate(names):
  b=(ROOT/n).read_bytes();c=f'{folder}/s{i:03}.txt';write(c,b)
  rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
 return rows
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',required=True,choices=['tool-initial','refinement','callback-refinement','context-read','final']);a=ap.parse_args()
 if a.stage=='tool-initial':dump('tool-initial-source-origins.json',capture(OWN[2:],'tool-initial'));return
 if a.stage=='refinement':dump('refinement-source-origins.json',capture(OWN[:2],'refinement'));return
 if a.stage=='callback-refinement':dump('callback-refinement-source-origins.json',capture(OWN[:2],'callback-refinement'));return
 if a.stage=='context-read':dump('actual-read-context-origins.json',capture(CONTEXT,'read-context'));return
 current=capture(STABLE+OWN,'current');context=capture(CONTEXT,'final-context')
 dump('current-source-origins.json',current);dump('root-peer-final-context-origins.json',context)
 write('initial-original-inputs-list.json',(OUT/'original-inputs.json').read_bytes())
 actual=[{'path':r['absolute_path'],'source_path':r['path'],'copy':r['copy'],'bytes':r['bytes'],'sha256':r['sha256'],'role':'stable current source' if r in current else 'root/peer final context only'} for r in current+context]
 (OUT/'original-inputs.json').write_bytes((json.dumps(actual,indent=2)+'\n').encode())
 for epoch in ['initial','refinement','callback-refinement','tool-initial']:
  p=OUT/(epoch+'-source-origins.json')
  if not p.exists():continue
  for i,r in enumerate(json.loads(p.read_text())):
   write(f'diff/{epoch}{i:03}.diff',''.join(difflib.unified_diff((OUT/r['copy']).read_text(encoding='utf-8').splitlines(True),(ROOT/r['path']).read_text(encoding='utf-8').splitlines(True),fromfile=r['path']+' '+epoch,tofile=r['path']+' final')).encode())
 for i,n in enumerate(OWN):write(f'diff/new{i:03}.diff',''.join(difflib.unified_diff([],(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' actual freshbefore absent',tofile=n+' final')).encode())
 sites=[];contexts=[]
 for names,dest in [(OWN[:2],sites),(CONTEXT,contexts)]:
  for n in names:
   for line,t in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
    if any(x in t for x in ['current','Current','publish','Publication','release','Release','catalog','scope','Scope','stage','Stage','receipt','Receipt','token','Token','terminal','bind','pending','Pending']):dest.append({'path':n,'line':line,'text':t})
 dump('source-sites.json',sites);dump('context-sites.json',contexts)
 dump('stages.json',[
  'Actual same host presence/transports and exact strong catalog/store lifetime/reader/WorldOwner -> publisher factory, no database/current observer in create/bind',
  'Bind actual weak CN connection/full Lease once before ready; first actual ready publish acquires existing exact private registered Token, never creates registration',
  'Full actual root/saved position/private Token snapshots before and after pure real catalog_current; actual owner qualifies store lifetime before every borrowed lookup',
  'Complete supplied native87 raw3B records and WORD flags/list/state/order deep-owned; exact source/fileoffset/hash/raw110 definition via shared catalog, no encode/default flags',
  'Whole batch/output and immutable qualified/unqualified receipt alternatives allocated before real held queue effects',
  'Preparation observer Stage ends before real held send; approval has its own Stage, busy/submitting reject external reentry and inline completion is deferred with monotonic true release fact',
  'BeforeQueue / actual posted BeforeRelease / actual completion AfterRelease qualify retained definitions and current receiver/root, preserving fresh saved-position changes across async stages',
  'True local held release is irrevocable; immutable receipt stores original full Plan/Token/definitions and post_release_current fact, never ACK/client acceptance/learning grant',
  'Caught reentry or failed qualification terminalizes this source; cancellation after submit waits actual transport release result and closes only captured old connection, no common/token/core cleanup or replay'])
 dump('gaps.json',[
  'Actual common committed learned event, save revision, native battle/list/slot epoch, resource/profile, rules/replay/ownership/rights still require real WorldOwner; definition or flag presence does not qualify them',
  'Generic SubjectSkillPublication remains frozen WORLD34/35; native87 new source does not rewrite it or assume common subject identity from native keys',
  'Actual deferred87 consumer5523F6 directly calls554750; retained54DEF0 body adapter is not claimed as actual live phase caller',
  'Raw native writer kind is six bits; catalog path qualifies four actual declared banks and exact IDs, not guessed unknown rows or transformed flags',
  'Positive explicit budgets are operational frame/memory limits, not native100/10 skill capacities; actual issuer owns list capacity/reset/selection',
  'Completion true means locally released held batch only; post_release_current false causes terminal/captured connection close but cannot retract released prefix or cause retry',
  'Cancelled already-submitted operation awaits actual original transport completion; no fabricated unsent false before late true release fact',
  'A send exception after actual inline local release preserves true completion and preallocated unqualified receipt; terminal cleanup does not erase the prefix',
  'Main/new persistent learned supplier/Core rules/cost/grant/native acceptance remain OPEN; complete routes increment0',
  'No builds/tests/native/codec/API/runtime/database/SQL/deploy/155 execution'])
 epoch_paths={'before':'before-source-origins.json','initial':'initial-source-origins.json','refinement':'refinement-source-origins.json','callback-refinement':'callback-refinement-source-origins.json','tool-initial':'tool-initial-source-origins.json','actual-read-context':'actual-read-context-origins.json'}
 epochs={k:len(json.loads((OUT/n).read_text())) for k,n in epoch_paths.items() if (OUT/n).exists()}
 dump('findings.json',{'round':194,'new_cpp_sources':2,'modified_cpp_sources':0,'new_tool':1,'source_epochs':epochs,'current_originals':len(current),'final_context_originals':len(context),'full_source_originals':sum(epochs.values())+len(current)+len(context),'actual_original_inputs':len(actual),'actual_native_inputs':0,'new_native_spans':0,'source_sites':len(sites),'context_sites':len(contexts),'complete_route_increment':0,'current_exclusions':'Root Gameplay2/generic deferred header and peer native update header final context only; no mutable books/catalog/ledger/reports/artifact receipts','executed':'Python-B file/source copies, diffs, hashes and inventories only; no game/native/DB/codec execution'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 members=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files]
 dump('LIST.json',members);members.append({'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())})
 dump('seal.json',{'round':194,'source_only':True,'members':members,'member_count':len(members)})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current':len(current),'context':len(context),'full_source_originals':sum(epochs.values())+len(current)+len(context),'actual_inputs':len(actual),'source_sites':len(sites),'context_sites':len(contexts),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
