"""187 full source/native originals only; no native/codec/game/DB execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-ui-publication-source-01'
OUT=BASE/'agents/native-spectator-publication'
OWN=['src/game/SharedNativeSpectatorPublication.h','src/game/SharedNativeSpectatorPublication.cpp','src/cn/protocol/CnSpectatorTargetsD0.h','tools/reconstruction/native_spectator_publication187.py']
CONTEXT=['src/game/SharedWorldHost.h','src/game/SharedWorldHost.cpp','src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
 'src/game/SharedTaiwanNativeSpectatorSource.h','src/game/SharedTaiwanNativeSpectatorSource.cpp','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp']
STABLE=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/net/Session.h','src/net/Session.cpp',
 'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
 'src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h','src/protocol/RecoveredSpectator6E.h','src/protocol/RecoveredSpectatorTargetsD0.h']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']+STABLE+CONTEXT
TW=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01/agents/tw-spectator-source'
CN=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01/agents/cn-spectator-native-frontier'
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
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['before','initial','refinement','final'],required=True);args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 if args.stage=='before':
  raw=(BASE/'before-manifest.json').read_bytes()
  if sha(raw)!='4bd04968a085573630848601024f740b49f5e72fcb513b0efdac6c044ab45f13':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[]
  for i,n in enumerate(BEFORE):
   row=index[n];b=(BASE/row['snapshot']).read_bytes()
   if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('before full original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows);dump('new-source-before.json',[{'path':n,'existed_in_actual_fresh_baseline':n in index,'copy':None} for n in OWN])
  original=[]
  for catalog in [TW/'original-inputs.json',CN/'original-inputs.json']:
   for row in json.loads(catalog.read_text(encoding='utf-8')):
    p=Path(row['path']);b=p.read_bytes()
    if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('actual retained native/primary original drift:'+str(p))
    c=f'originals/o{len(original):03d}.bin';write(c,b);original.append({'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'retained actual TW149c/CN own PE or primary full original; no new native span'})
  dump('original-inputs.json',original);dump('native-original-inputs.json',original)
  context=[]
  for base,names in [(TW,['findings.json','retained-native-context-origins.json']), (CN,['findings.json','native-spans.json','instruction-sites.json','primary-source-sites.json','selected-opcode-relations.json']+[f'derived/s{i:02d}.json' for i in range(14)]+[f'raw/s{i:02d}.bin' for i in range(14)])]:
   for n in names:
    p=base/n;b=p.read_bytes();c=f'retained/r{len(context):03d}{p.suffix}';write(c,b);context.append({'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'actual-read retained186 context, not current source pin'})
  # Retain TW complete D0/CD leaf instruction originals, not a receipt standing
  # in for the full mapped image or the actual raw function input.
  tworig=json.loads((TW/'retained-native-context-origins.json').read_text(encoding='utf-8'))
  for row in tworig:
   p=Path(row['path']);b=p.read_bytes()
   if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('retained TW context drift')
   c=f'retained/r{len(context):03d}{p.suffix}';write(c,b);context.append({'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'retained TW185 complete leaf/table/producer originals'})
  dump('retained-native-context-origins.json',context);dump('derived-inputs.json',[])
  print(json.dumps({'before':len(rows),'actual_originals':len(original),'retained_context':len(context)}));return
 if args.stage in ['initial','refinement']:
  dump(args.stage+'-owned-source-origins.json',originals(OWN,args.stage));print(json.dumps({'owned_'+args.stage:4}));return
 current=originals(STABLE+OWN,'current');dump('current-source-origins.json',current)
 dump('root-mixed-final-context-origins.json',originals(CONTEXT,'context-final'))
 for i,n in enumerate(OWN):write(f'diff/n{i:03d}.diff',''.join(difflib.unified_diff([],(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (absent freshbefore)',tofile=n+' (final)')).encode())
 for epoch in ['initial','refinement']:
  for i,row in enumerate(json.loads((OUT/(epoch+'-owned-source-origins.json')).read_text(encoding='utf-8'))):
   write(f'diff/{epoch}{i:03d}.diff',''.join(difflib.unified_diff((OUT/row['copy']).read_text(encoding='utf-8').splitlines(True),
    (ROOT/row['path']).read_text(encoding='utf-8').splitlines(True),fromfile=row['path']+' ('+epoch+')',tofile=row['path']+' (final)')).encode())
 held=[]
 for n,start,end in [('src/net/Session.cpp',1504,1572),('src/cn/net/SharedCredentialConnection.cpp',117,132),('src/cn/net/CnTransportSession.cpp',152,219)]:
  for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if start<=line<=end:held.append({'path':n,'line':line,'source':text})
 dump('held-queue-source-sites.json',held)
 sites=[];csites=[]
 for names,rows in [(OWN[:3],sites),(CONTEXT,csites)]:
  for n in names:
   for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
    if any(s in text for s in ['Spectator','spectator','Status','observe','current','publish','released','retire','remove','same_registration','history','pending','ui_epoch','revision']):rows.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites);dump('root-mixed-context-sites.json',csites)
 dump('stages.json',[
  'Actual same-host ready recipient/original private transport token -> immutable full supplied version-specific CD65/D07 records, explicit issuer UI epoch/revisions',
  'Complete structural segmentation/allocation/history/logical/record budgets before any transport effect; raw slots1..50 separate supplied server domain',
  'Mandatory real WorldOwner Current around whole actual common root/position and exact transport/window/source incarnation -> existing held native publication queue',
  'BeforeRelease qualifies actual current source again, no state-only approval. Only local released completion appends immutable issued history; not native client receipt',
  'Actual TW/CN held approval is posted strand-to-game; CN wrapper inline failure completion checks owner before flags and finishes after source operation ends',
  'False completion returns preallocated original immutable view; checked private absence exhaustion terminalizes source without wrap, rollback or losing true release completion',
  'Weak stored actual transport/issuer, strong pending callback inputs; private immutable observations distinguish Missing/Pending/Published/Retired/Unavailable',
  'Observation Current means still accurate state, including negative states during legitimate battle transition; no rights or rawtarget-to-common mapping follows',
  'Exact epoch retirement/deferred pending removal changes only own bookkeeping, no common/token/native cleanup or retry/rollback'])
 dump('gaps.json',[
  'Actual full logical D0/CD source/identity/window/reset lineage, target namespace and battle permission remain real issuer obligations; no guessed initialflags or targetID cast',
  'TW existing publication API supports ready InWorld here and captures battle generation. It is not extended to InBattle; readonly history is separately observable there',
  'CN own world D0/CD proof independent of TW; native battle default consumption not promoted into a publication consumer',
  'Local queue release only, no distributed atomicity/native client receipt. Retired/stale release preserves committed-prefix facts without reactivating old authority',
  'No automatic F7/reset orA3/CB attribution as issuer epoch; no invented S2C6E ACK/permission/ready success',
  'No Main activation/build/tests/runtime/native/codec/API/DB/SQL/deployment; complete route increment0'])
 dump('findings.json',{'round':187,'new_cpp_sources':3,'modified_cpp_sources':0,'new_tool':1,'before_full_originals':len(BEFORE),
  'initial_owned_originals':4 if (OUT/'initial-owned-source-origins.json').exists() else 0,'refinement_owned_originals':4 if (OUT/'refinement-owned-source-origins.json').exists() else 0,
  'current_full_originals':len(current),'root_mixed_final_context_originals':len(CONTEXT),'source_sites':len(sites),'context_sites':len(csites),
  'source_original_total':len(BEFORE)+4+4+len(current)+len(CONTEXT),'retained_context_originals':len(json.loads((OUT/'retained-native-context-origins.json').read_text(encoding='utf-8'))),
  'held_approval_inline':False,'cn_wrapper_failure_completion_may_be_inline':True,'failure_completion_view_preallocated':True,'private_absence_exhaustion':'terminal no-wrap; released prefix and completion preserved',
  'actual_originals':len(json.loads((OUT/'original-inputs.json').read_text(encoding='utf-8'))),'new_native_spans':0,
  'complete_route_increment':0,'tests_run':False,'runtime_run':False,'codec_run':False,
  'concrete_body':'Actual TW/CN same-host recipient -> complete supplied CD/D0 bytes -> real held publication -> released immutable UI history observation, not new battle permission',
  'exclusions':'RootHost2/Transport2 and mixedTWSource2/Plan2 context only; no mutable root docs/books/catalog/reports/ledger/artifact receipt current pins'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':187,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current_count':len(current),'source_sites':len(sites),'context_sites':len(csites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
