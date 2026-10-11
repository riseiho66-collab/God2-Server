"""184 full actual source originals/accounting only; never runs game/native/codec/DB."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/shared-native-world-transport-source-01'
OUT=BASE/'agents/common-native-transports'
OWN=['src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp','tools/reconstruction/shared_native_world_transports184.py']
CONTEXT=['src/game/SharedTaiwanWorldLifecycle.h','src/game/SharedTaiwanWorldLifecycle.cpp',
 'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp','src/game/SharedTaiwanNativeChatSource.h','src/game/SharedTaiwanNativeChatSource.cpp',
 'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/net/Session.h','src/net/Session.cpp',
 'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
 'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
 'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp','src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h']+CONTEXT
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
  if sha(raw)!='008a860dc868ac80a91cd6410b852f9e4b4623033cf17317288a7ee3da051148':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[]
  for i,n in enumerate(BEFORE):
   row=index[n];b=(BASE/row['snapshot']).read_bytes()
   if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('before full original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows)
  dump('new-source-before.json',[{'path':n,'existed_in_actual_fresh_baseline':n in index,'copy':None} for n in OWN])
  dump('initial-owned-source-origins.json',originals(OWN,'initial'))
  print(json.dumps({'before':len(rows),'owned_initial':3}));return
 if args.stage=='intermediate':
  dump('refinement-before-source-origins.json',originals(OWN,'intermediate'))
  print(json.dumps({'owned_intermediate':3}));return
 before=json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))
 stable=[r['path'] for r in before if r['path'].startswith('src/') and r['path'] not in CONTEXT]+OWN
 current=originals(stable,'current');dump('current-source-origins.json',current)
 dump('root-cn-final-context-origins.json',originals(CONTEXT,'context-final'))
 for i,n in enumerate(OWN):write(f'diff/n{i:03d}.diff',''.join(difflib.unified_diff([], (ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (absent freshbaseline)',tofile=n+' (final)')).encode())
 sites=[]
 for n in OWN[:2]:
  for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if any(s in text for s in ['TokenStorage','SnapshotStorage','::create(','::owns_presence(','::stored(','::tuple(','::qualified(','::bind','::release(','::lookup(','::current(','::registry_current(','ready_characters','ready_lease','same_registry','common_world_','world_admission_current','slots_.','reentered_','battle_generation']):sites.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites)
 contextsites=[]
 for n in CONTEXT:
  for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if any(s in text for s in ['native_transport','common_transports','world_transports','use_common_transport','SharedNativeWorldTransports','transport_source','transport_token','transport_snapshot','registry_current','transports->','transports_']):contextsites.append({'path':n,'line':line,'source':text,'role':'actual-read final epoch context; excluded current pins'})
 dump('root-cn-context-sites.json',contextsites)
 dump('original-inputs.json',[]);dump('native-original-inputs.json',[]);dump('derived-inputs.json',[])
 dump('stages.json',[
  'Actual realready common fullLease/native transport tuple -> strong actual connection acquired before repository callbacks -> bind explicit private token',
  'Registry retains only immutable token identity/fullLease/private generation/weak native pointer; no Session-cleanup-token strong cycle',
  'FullLease lookup -> source-private incarnation/pointer equality -> whole actual ready population -> native tuple pre/post callbacks -> retained StrongSnapshot',
  'Snapshot current repeats exact registry/common/native source qualification and actualTW phase/battle generation; no fabricatedCN battle counter. registry_current performs final private stored token/weak-strong pointer/native pure tuple/TWphase-generation check without repositories or external Current callbacks; never substitutes full current',
  'Exact release only erases private slot; works after Presence release without repo/transport cleanup, cannot delete foreign/successor token',
  'Root/CN actual ready completions bind and cleanup releases token before common cleanup; selected chat delivery optin consumes actual registry snapshot and retains it through queue Current'])
 dump('gaps.json',[
  'Gameowner repository observers must be non-yielding/pure read-only; nested observer or registry release invalidates active source read',
  'Presence/connection readiness is not mute/rate/membership/audience/visibility/map/collision/native actor/fullreply/cipher/window authority; actual WorldOwner remains mandatory',
  'Only actual separately integrated completion/cleanup paths opt into source; no legacy account/world transport replacement or defaultsuccess',
  'No nativeopcode/parser/fullphase inventory claim, Main activation, build/tests/native/runtime/DB/codec execution/deployment; fullroute increment0'])
 dump('findings.json',{'round':184,'new_cpp_sources':2,'modified_cpp_sources':0,'new_tool':1,'before_full_originals':len(before),
  'initial_owned_originals':3,'refinement_owned_originals':3 if (OUT/'refinement-before-source-origins.json').exists() else 0,
  'current_full_originals':len(current),'root_cn_final_context_originals':10,'source_sites':len(sites),'context_sites':len(contextsites),
  'actual_native_inputs':0,'asset_inputs':0,'derived_inputs':0,'complete_route_increment':0,'tests_run':False,'runtime_run':False,
  'concrete_body':'Actual ready native bind/weak token registry/strong snapshot lookup/current/exact release source, with actual lifecycle/chat callers in final context',
  'lifetime':'Registry and tokens weak actual connections; Snapshot alone strong only during scoped caller use; private generation is integration lineage, not native counter',
  'exclusions':'Root/CN ten mutable lifecycle/chat/ready/gameplay source context only; no books/docs/catalog/ledger/reports/artifact receipt current pins'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':184,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current_count':len(current),'source_sites':len(sites),'context_sites':len(contextsites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
