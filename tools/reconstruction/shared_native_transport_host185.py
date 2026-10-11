"""185 source-original accounting only; no game/native/codec/DB execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/native-world-transport-host-composition-01'
OUT=BASE/'agents/common-host-transports'
OWN=['src/game/SharedWorldHost.h','src/game/SharedWorldHost.cpp','src/core/SharedTaiwanNativeWorldHostPlan.cpp','tools/reconstruction/shared_native_transport_host185.py']
CONTEXT=['src/core/Application.cpp','src/cn/auth/SharedLoginComposition.cpp','src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp']
STABLE=['src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
 'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
 'src/core/SharedWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.h',
 'src/game/SharedTaiwanWorldLifecycle.h','src/game/SharedTaiwanWorldLifecycle.cpp',
 'src/game/SharedTaiwanNativeChatSource.h','src/game/SharedTaiwanNativeChatSource.cpp',
 'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']+OWN[:3]+STABLE+CONTEXT
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,b):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def dump(n,v):write(n,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
def originals(names,folder):
 rows=[]
 for i,n in enumerate(names):
  p=ROOT/n;b=p.read_bytes();c=f'{folder}/s{i:03d}.txt';write(c,b)
  rows.append({'path':n,'absolute_path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
 return rows
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['before','intermediate','final'],required=True);args=parser.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 if args.stage=='before':
  raw=(BASE/'before-manifest.json').read_bytes()
  if sha(raw)!='a859ae7a16f0f7e331ccd54416e6273a9a9149635c108d8d2a8c3a9688323fc9':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[]
  for i,n in enumerate(BEFORE):
   row=index[n];b=(BASE/row['snapshot']).read_bytes()
   if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('before full original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows)
  dump('new-tool-before.json',{'path':OWN[3],'existed_in_actual_fresh_baseline':OWN[3] in index,'copy':None})
  dump('initial-owned-source-origins.json',originals(OWN,'initial'))
  print(json.dumps({'before':len(rows),'owned_initial':4}));return
 if args.stage=='intermediate':
  dump('intermediate-owned-source-origins.json',originals(OWN,'intermediate'));print(json.dumps({'owned_intermediate':4}));return
 before=json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))
 current=originals(STABLE+OWN,'current');dump('current-source-origins.json',current)
 context=originals(CONTEXT,'context-final');dump('root-cn-final-context-origins.json',context)
 index={r['path']:r for r in before}
 for i,n in enumerate(OWN):
  old=(OUT/index[n]['copy']).read_text(encoding='utf-8').splitlines(True) if n in index else []
  write(f'diff/n{i:03d}.diff',''.join(difflib.unified_diff(old,(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (freshbefore)',tofile=n+' (final)')).encode())
 sites=[];contextsites=[]
 for names,rows in [(OWN[:3],sites),(CONTEXT,contextsites)]:
  for n in names:
   for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
    if any(s in text for s in ['SharedNativeWorldTransports','transports','owns_repository','owns_registries','common_world','with_native_chat','SharedTaiwanNativeChatSource::create','SharedTaiwanWorldLifecycle::create','SharedWorldPreparation::create','world_transports']):rows.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites);dump('root-cn-context-sites.json',contextsites)
 dump('original-inputs.json',[]);dump('native-original-inputs.json',[]);dump('derived-inputs.json',[])
 dump('stages.json',[
  'Actual game-owner SharedWorldHost constructs exactly one common presence, visibility and SharedNativeWorldTransports source',
  'Host owns_repository qualifies repository, visibility presence and transport presence; transports getter enforces same game owner',
  'Actual same Context RecordSources::with_native_chat passes Host transports into existing real-authority ChatSource',
  'Root Application sync/async native entry and CN same-host login preparation pass same registry; true ready binds, exact cleanup releases before common cleanup',
  'Registry tokens and slots retain actual connections weakly; chat scoped snapshots retain strong connections and actual full-current/private endpoint fences'])
 dump('gaps.json',[
  'One actual host registry is source composition, not native scene/rights/entry/native fullreply/cipher/loadedwindow authority',
  'Actual native chat WorldOwner, input code page, remaining handlers, resource lifecycle/Current/full5D/nativephase qualifications remain mandatory',
  'Missing supplier never implies empty audience or success; explicit selected route uses common transport, legacy paths retain their semantics',
  'Main incomplete plan remains unactivated; no new complete game route, tests/build/runtime/codec/native/DB/deployment in this phase'])
 dump('findings.json',{'round':185,'modified_cpp_sources':3,'new_cpp_sources':0,'new_tool':1,
  'before_full_originals':len(before),'initial_owned_originals':4,'intermediate_owned_originals':4 if (OUT/'intermediate-owned-source-origins.json').exists() else 0,
  'current_full_originals':len(current),'root_cn_final_context_originals':len(context),'source_sites':len(sites),'context_sites':len(contextsites),
  'actual_native_inputs':0,'asset_inputs':0,'derived_inputs':0,'complete_route_increment':0,'tests_run':False,'runtime_run':False,
  'concrete_body':'One game-owner Host retained registry plus actual same Context native chat construction; entry and CN preparation callers read in separate final context',
  'lifetime':'Transport registry drains before visibility/presence member ownership; retained callers must drain on same game owner with repository alive. Tokens weak, no cleanup Session strong cycle',
  'exclusions':'Root Application and CN three mutable sources final context only; no root books/docs/catalog/ledger/reports/artifact receipts current pins'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':185,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current_count':len(current),'source_sites':len(sites),'context_sites':len(contextsites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
