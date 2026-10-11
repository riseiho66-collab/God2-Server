"""189 source-only exact UI retirement ticket originals; no native/game/codec execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-close-record-source-01'
OUT=BASE/'agents/native-spectator-close-targets'
OWN=['src/game/SharedNativeSpectatorTargets.h','src/game/SharedNativeSpectatorTargets.cpp','tools/reconstruction/native_spectator_close_targets189.py']
CONTEXT=['src/protocol/RecoveredWorldRecords.h','src/game/SharedTaiwanNativeRecordHandlerSource.cpp',
 'src/game/SharedTaiwanWorldRecordSource.h','src/game/SharedTaiwanWorldRecordSource.cpp','src/net/Session.h','src/net/Session.cpp',
 'src/core/Application.cpp','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp',
 'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/game/SharedTaiwanNativeSpectatorSource.h',
 'src/game/SharedTaiwanNativeSpectatorSource.cpp','src/cn/world/SharedNativeSpectatorSource.h','src/cn/world/SharedNativeSpectatorSource.cpp',
 'src/protocol/RecoveredSpectatorClose.h','src/cn/protocol/CnSpectatorClose.h']
STABLE=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
 'src/game/SharedNativeSpectatorPublication.h','src/game/SharedNativeSpectatorPublication.cpp',
 'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h',
 'src/protocol/RecoveredSpectatorTargetsD0.h','src/cn/protocol/CnSpectatorTargetsD0.h']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']+STABLE+OWN[:2]+CONTEXT
PRIOR=ROOT/'artifacts/integration/packet-connections-20261006/native-spectator-target-identity-source-01/agents/native-spectator-targets'
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
  if sha(raw)!='1c7a98ae5abd06ccdfac7d83e41370d6524df074295a6afb20a318d3a779a309':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[];absent=[]
  for i,n in enumerate(BEFORE):
   if n not in index:absent.append({'path':n,'existed_in_actual_fresh_baseline':False,'copy':None});continue
   r=index[n];b=(BASE/r['snapshot']).read_bytes()
   if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise RuntimeError('before full original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows);dump('new-source-before.json',absent+[{'path':n,'existed_in_actual_fresh_baseline':n in index,'copy':None} for n in OWN])
  retained=[]
  for i,n in enumerate(['findings.json','stages.json','gaps.json','source-sites.json']):
   p=PRIOR/n;b=p.read_bytes();c=f'retained/r{i:03d}.json';write(c,b);retained.append({'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'prior188 source context only, not actual native original/current pin'})
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
 baseline={r['path']:r for r in json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))}
 for i,n in enumerate(OWN):
  old=(OUT/baseline[n]['copy']).read_text(encoding='utf-8').splitlines(True) if n in baseline else []
  write(f'diff/owned{i:03d}.diff',''.join(difflib.unified_diff(old,(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (actual freshbefore)',tofile=n+' (final)')).encode())
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
  'Existing actual issued D0 binding entry retains exact copied immutable Publication Observation; its core/receiver remain weak',
  'Real WindowOwner captures retirement_for_ui(savedUI) before close using stored issuedUI plus exact private publication.same/registry proof only',
  'Immutable UiRetirement carries private source/entry identity, full token/lease, exact issued observation/epoch/generation; no context or target search',
  'retire_for_ui(ticket) after actual close/common cleanup matches only that exact source-owned entry; no repository/real Current/permission call',
  'Same epoch/UI reissue creates a new private target entry and cannot be retired by an older captured ticket; no tombstone or budget reinterpretation',
  'Only own retired flag changes, no shared registry removal/common lease release/target ID/native generation fabrication or automatic A3/CB admission'])
 dump('gaps.json',[
  'Actual WindowOwner must independently qualify close opcode/opaque byte/window/reset/rules and execute real core cleanup; no automatic permission or guessed ACK',
  'Capture ticket before publication/token registry retirement; cleanup later uses its immutable exact private identity even after actual common release',
  'Capture requires original issued UI still publication.same/current-private-view; a later CD/D0/history revision, even with same D0/epoch, requires actual issuer reissue/synchronization before new capture',
  'A saved epoch/lease or newly guessed context0 cannot replace original issuedUI proof; fresh unrelated post-issue UI snapshots are not universal cleanup capabilities',
  'Issued original UI retained strongly as immutable bytes/private cap, with actual core/receiver weak; no new ownership cycle',
  'Existing Target issue/resolve/current and whole-batch real issuer authority remain mandatory; no tombstones or native counter reinterpretation',
  'No build/test/runtime/native/codec/API/DB/SQL/deploy; complete gameplay route increment0'])
 before=json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))
 epochs={e:len(json.loads((OUT/(e+'-owned-source-origins.json')).read_text(encoding='utf-8'))) if (OUT/(e+'-owned-source-origins.json')).exists() else 0 for e in ['initial','refinement']}
 read_context=len(json.loads((OUT/'actual-read-context-origins.json').read_text(encoding='utf-8'))) if (OUT/'actual-read-context-origins.json').exists() else 0
 dump('findings.json',{'round':189,'new_cpp_sources':0,'modified_cpp_sources':2,'new_tool':1,'before_full_originals':len(before),
  'epochs':epochs,'current_full_originals':len(current),'root_peer_final_context_originals':len(contexts),
  'source_original_total':len(before)+sum(epochs.values())+read_context+len(current)+len(contexts),'actual_read_context_epoch':read_context,'source_sites':len(sites),'context_sites':len(csites),
  'actual_native_inputs':0,'new_native_spans':0,'retained_context_originals':4,'complete_route_increment':0,
  'modified_before_originals':2,'new_tool_before_absent':True,'refinement_scope':'No CPP change after initial ticket implementation; tool clarification of strict issuedUI/current-view capture limitation only',
  'capture_scope':'Only exact stored issued UI current private lineage; later publication revision requires real issuer reissue',
  'tests_run':False,'runtime_run':False,'native_run':False,'codec_run':False,'native_original_scope':'Only stable C++ publication/target and native record view sources plus retained188 context; no new raw native input/disassembly',
  'concrete_body':'Original issued UI private proof -> exact UiRetirement ticket -> real WindowOwner close -> own exact target entry retirement, no repo/default authority',
  'exclusions':'Root11 + peerTW/CN Source4 + nativeCloseHeaders2 finalcontext only; no mutable books/catalog/ledger/report/artifact current pins'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':189,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,
  'current_count':len(current),'context_count':len(contexts),'source_sites':len(sites),'context_sites':len(csites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
