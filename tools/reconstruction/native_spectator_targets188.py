"""188 source-only original retention/accounting; no native/game/codec execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-target-identity-source-01'
OUT=BASE/'agents/native-spectator-targets'
OWN=['src/game/SharedNativeSpectatorTargets.h','src/game/SharedNativeSpectatorTargets.cpp','tools/reconstruction/native_spectator_targets188.py']
CONTEXT=['src/game/SharedWorldHost.h','src/game/SharedWorldHost.cpp','src/game/SharedTaiwanNativeSpectatorSource.h','src/game/SharedTaiwanNativeSpectatorSource.cpp',
 'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp',
 'src/cn/world/SharedNativeSpectatorSource.h','src/cn/world/SharedNativeSpectatorSource.cpp','src/cn/protocol/CnSpectator6E.h']
STABLE=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
 'src/game/SharedNativeSpectatorPublication.h','src/game/SharedNativeSpectatorPublication.cpp','src/net/Session.h','src/net/Session.cpp',
 'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h',
 'src/protocol/RecoveredSpectatorTargetsD0.h','src/cn/protocol/CnSpectatorTargetsD0.h']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']+STABLE+CONTEXT
PRIOR=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-ui-publication-source-01/agents/native-spectator-publication'
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
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',required=True,choices=['before','initial','refinement','context-read','final']);args=ap.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 if args.stage=='before':
  raw=(BASE/'before-manifest.json').read_bytes()
  if sha(raw)!='6b9ec7faf43f692cdf92df9150845f23f8179dadaf47a42725aa8556509718d6':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[];absent=[]
  for i,n in enumerate(BEFORE):
   if n not in index:absent.append({'path':n,'existed_in_actual_fresh_baseline':False,'copy':None});continue
   r=index[n];b=(BASE/r['snapshot']).read_bytes()
   if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('before full original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows);dump('new-source-before.json',absent+[{'path':n,'existed_in_actual_fresh_baseline':n in index,'copy':None} for n in OWN])
  retained=[]
  for i,n in enumerate(['findings.json','stages.json','gaps.json','held-queue-source-sites.json']):
   p=PRIOR/n;b=p.read_bytes();c=f'retained/r{i:03d}.json';write(c,b);retained.append({'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'prior187 context only, not actual native original/current pin'})
  dump('retained-context-origins.json',retained);dump('original-inputs.json',[]);dump('native-original-inputs.json',[]);dump('derived-inputs.json',[])
  print(json.dumps({'before':len(rows),'absent_peer_context':len(absent),'native_actual_inputs':0,'retained_context':len(retained)}));return
 if args.stage in ['initial','refinement']:
  dump(args.stage+'-owned-source-origins.json',originals(OWN,args.stage));print(json.dumps({'owned_'+args.stage:len(OWN)}));return
 if args.stage=='context-read':
  existing=[n for n in CONTEXT if (ROOT/n).exists()]
  dump('actual-read-context-origins.json',originals(existing,'read-context'))
  dump('actual-read-context-missing.json',[{'path':n,'copy':None,'actual_present_at_capture':False} for n in CONTEXT if n not in existing])
  print(json.dumps({'actual_read_context':len(existing),'missing':len(CONTEXT)-len(existing)}));return
 current=originals(STABLE+OWN,'current');dump('current-source-origins.json',current)
 contexts=originals(CONTEXT,'final-context');dump('root-peer-final-context-origins.json',contexts)
 for i,n in enumerate(OWN):write(f'diff/new{i:03d}.diff',''.join(difflib.unified_diff([],(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (absent freshbefore)',tofile=n+' (final)')).encode())
 for epoch in ['initial','refinement']:
  p=OUT/(epoch+'-owned-source-origins.json')
  if not p.exists():continue
  for i,row in enumerate(json.loads(p.read_text(encoding='utf-8'))):
   write(f'diff/{epoch}{i:03d}.diff',''.join(difflib.unified_diff((OUT/row['copy']).read_text(encoding='utf-8').splitlines(True),
    (ROOT/row['path']).read_text(encoding='utf-8').splitlines(True),fromfile=row['path']+' ('+epoch+')',tofile=row['path']+' (final)')).encode())
 sites=[];csites=[]
 for names,rows in [(OWN[:2],sites),(CONTEXT,csites)]:
  for n in names:
   for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
    if any(s in text for s in ['Spectator','spectator','current','issue','Target','target','Status','resolve','registry','native_ui','context','ordinal','generation','retire']):rows.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites);dump('root-peer-context-sites.json',csites)
 dump('stages.json',[
  'Same actual presence/transport/publication -> complete immutable locally-released Published UI -> exact full record ordinal/event revision/last D0 per slot',
  'Actual supplied core Target and explicit target/issuer generations -> complete deep-owned immutable weak binding batch, all qualification/allocation before replacement',
  'Real issuer/target Current -> actual UI/common full root/saved position/native tuple before/after -> exact registered private token endpoint',
  'Full raw DWORD context resolution preserves Missing/Matched/Ambiguous/Expired/ForeignContext/Unavailable/Retired; no native namespace/rights inference',
  'Same raw context only matched if all corresponding actual objects and generations agree; no first-match conflict or default0/FFFF sentinel handling',
  'Persistent weak target/issuer, temporary strong actual callback objects, immutable copy/move observation and private registry-only endpoint',
  'Exact own incarnation retirement/removal, no common/transport/battle cleanup; private absence exhaustion never wraps'])
 dump('gaps.json',[
  'Concrete real core Target/Issuer/window/reset/flags/source generations and battle/admission rules still mandatory caller obligations; no Main activation',
  'This is an explicit bridge for actually issued D0 UI operands, not recovered universal official target namespace; other raw mode1/rolepool contexts remain separate real-owner domains',
  'D0 operand width is unsigned WORD, but request context remains full DWORD. No masking/truncation/common64 ID cast, FFFF special sentinel or native slot-bound claim',
  'Whole issued binding batch is qualified together; replaced last D0/expired sibling binding requires actual issuer reissue rather than silent filtering',
  'Pure non-yielding repository/issuer/target/UI observers are mandatory; endpoint fences are not distributed atomicity or client receipt',
  'No build/test/runtime/native/codec/API/DB/SQL/deploy; complete gameplay route increment0'])
 before=json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))
 epochs={e:len(json.loads((OUT/(e+'-owned-source-origins.json')).read_text(encoding='utf-8'))) if (OUT/(e+'-owned-source-origins.json')).exists() else 0 for e in ['initial','refinement']}
 read_context=len(json.loads((OUT/'actual-read-context-origins.json').read_text(encoding='utf-8'))) if (OUT/'actual-read-context-origins.json').exists() else 0
 dump('findings.json',{'round':188,'new_cpp_sources':2,'modified_cpp_sources':0,'new_tool':1,'before_full_originals':len(before),
  'epochs':epochs,'current_full_originals':len(current),'root_peer_final_context_originals':len(contexts),
  'source_original_total':len(before)+sum(epochs.values())+read_context+len(current)+len(contexts),'actual_read_context_epoch':read_context,'source_sites':len(sites),'context_sites':len(csites),
  'actual_native_inputs':0,'new_native_spans':0,'retained_context_originals':4,'complete_route_increment':0,
  'tests_run':False,'runtime_run':False,'native_run':False,'codec_run':False,'native_original_scope':'Only stable C++ native record views and retained187 source context read; no new raw native input/disassembly',
  'concrete_body':'Actual released D0 records -> original exact unsigned operands -> actually supplied core Target/generation -> immutable accurate observation; no guessed native rules',
  'exclusions':'RootHost2/TWSource2/CNGameplay2/Plan2 + peerCNSource2/CN6Eheader finalcontext only, no mutable books/catalog/ledger/report/artifact current pins'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':188,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,
  'current_count':len(current),'context_count':len(contexts),'source_sites':len(sites),'context_sites':len(csites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
