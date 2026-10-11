"""186 source/static original capture only; no native/codec/game/DB execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01'
OUT=BASE/'agents/tw-spectator-source'
OWN=['src/game/SharedTaiwanNativeSpectatorSource.h','src/game/SharedTaiwanNativeSpectatorSource.cpp','src/protocol/RecoveredSpectatorTargetsD0.h','tools/reconstruction/tw_native_spectator_source186.py']
CONTEXT=['src/core/Application.cpp','src/game/SharedTaiwanWorldRecordSource.h','src/game/SharedTaiwanWorldRecordSource.cpp',
 'src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
 'src/game/SharedTaiwanNativeRecordHandlerSource.h','src/game/SharedTaiwanNativeRecordHandlerSource.cpp',
 'src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp']
STABLE=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/net/Session.h','src/net/Session.cpp',
 'src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h','src/protocol/RecoveredSpectator6E.h','src/protocol/RecoveredWorldFrame.h']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']+STABLE+CONTEXT
PRIOR=ROOT/'artifacts/integration/packet-connections-20261006/native-world-transport-host-composition-01/agents/tw-spectator-target-publication'
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
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['before','initial','refinement','final'],required=True);args=parser.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 if args.stage=='before':
  raw=(BASE/'before-manifest.json').read_bytes()
  if sha(raw)!='8200c1fca67e3d2d2b4c42714c0b294e953481731060e78f9bf3a645275529aa':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[]
  for i,n in enumerate(BEFORE):
   row=index[n];b=(BASE/row['snapshot']).read_bytes()
   if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('before full original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows);dump('new-source-before.json',[{'path':n,'existed_in_actual_fresh_baseline':n in index,'copy':None} for n in OWN])
  native=json.loads((PRIOR/'original-inputs.json').read_text(encoding='utf-8'))[0]
  p=Path(native['path']);b=p.read_bytes()
  if sha(b)!=native['sha256'] or len(b)!=native['bytes']:raise RuntimeError('actual native original drift')
  c='originals/native.bin';write(c,b)
  row={'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'retained actual mapped original149c, no new disassembly/native execution'}
  dump('original-inputs.json',[row]);dump('native-original-inputs.json',[row])
  retained=[]
  names=['findings.json','native-spans.json','source-sites.json','instruction-sites.json','data-sites.json']+[f'derived/s{i:02d}.json' for i in range(8)]+[f'raw/s{i:02d}.bin' for i in range(8)]+[f'raw/t{i:02d}.bin' for i in range(4)]
  for i,n in enumerate(names):
   p=PRIOR/n;b=p.read_bytes();c=f'retained/r{i:03d}{p.suffix}';write(c,b);retained.append({'path':str(p.resolve()),'copy':c,'bytes':len(b),'sha256':sha(b),'role':'actual-read retained185 context, not current source pin'})
  dump('retained-native-context-origins.json',retained);dump('derived-inputs.json',[])
  print(json.dumps({'before':len(rows),'actual_native':1,'retained_context':len(retained)}));return
 if args.stage in ['initial','refinement']:
  dump(args.stage+'-owned-source-origins.json',originals(OWN,args.stage));print(json.dumps({'owned_'+args.stage:4}));return
 current=originals(STABLE+OWN,'current');dump('current-source-origins.json',current)
 context=originals(CONTEXT,'context-final');dump('root-mixed-final-context-origins.json',context)
 for i,n in enumerate(OWN):write(f'diff/n{i:03d}.diff',''.join(difflib.unified_diff([],(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (absent freshbefore)',tofile=n+' (final)')).encode())
 sites=[];contextsites=[]
 for names,rows in [(OWN[:3],sites),(CONTEXT,contextsites)]:
  for n in names:
   for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
    if any(s in text for s in ['Spectator','spectator','registry_current','source_revision','expected_post','snapshot(','qualified(','scope','execute(','observed_producer_shape','ready_characters','same_root','terminal','reentered','token','dispatch','Reply']):rows.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites);dump('root-mixed-context-sites.json',contextsites)
 dump('stages.json',[
  'Exact observed C2S6E rawbody preserved, mode1 original DWORD context and unwritten bytes; mode2 actual membership/transition authority solely realOwner',
  'Actual ready fullLease -> strong actual registered Session -> private originalToken retained -> full common root/saved-position snapshot',
  'Pure mandatory Current preexecute is bracketed by same complete actual Scope/privateToken; execute invoked exactly once with original Request',
  'Real Result supplies actual encrypted wire or explicit native noReply and exact expected postphase/battle generation; actual postroot/position/source incarnation requalified',
  'Post current uses originalToken plus callback-free registry endpoint, allows qualified world-battle transitions without using old Snapshot phase freeze',
  'Whole native encrypted envelope boundaries/output budget checked without decode/repack; sender output returns through mixed ordering, no direct send',
  'Failures terminalize only exact source-owned Session/Lease bookkeeping; durable committed prefix is not rolled back/replayed, cleanup does not release common lease/token',
  'Read-only D0 exact7B preserves slot/body1/2WORD without serialization or target identity/default sentinel assumptions'])
 dump('gaps.json',[
  'Actual target namespace/publication/reset/entry/cross-recipient issuer, spectator admission/membership/battle creation and game rules remain mandatory WorldOwner obligations',
  'D0 native leaf has no slot bound; future slot1..50 qualification is separate server domain, not native malformed rejection',
  'WORD FFFF zeroextends to0000FFFF, no inventedFFFFFFFF sentinel or commonID/actorhandle cast',
  'No fake6E ACK/noReply/defaultbattle authority, native cipher/profile issuer must qualify actual wire in Current',
  'Current/repository observers must be pure non-yielding read-only; execute may commit exactly once but must not retain borrowed args/yield/reenter',
  'No complete route/Main activation/native client acceptance/build/tests/runtime/codec/DB/deployment claim'])
 dump('findings.json',{'round':186,'new_cpp_sources':3,'modified_cpp_sources':0,'new_tool':1,'before_full_originals':len(BEFORE),
  'initial_owned_originals':4 if (OUT/'initial-owned-source-origins.json').exists() else 0,'refinement_owned_originals':4 if (OUT/'refinement-owned-source-origins.json').exists() else 0,
  'current_full_originals':len(current),'root_mixed_final_context_originals':len(context),'source_sites':len(sites),'context_sites':len(contextsites),
  'actual_native_originals':1,'new_native_spans':0,'native_scope':'retained185149c actual original/complete leaf context, no new native branch claimed',
  'complete_route_increment':0,'tests_run':False,'runtime_run':False,'codec_run':False,
  'concrete_body':'Actual registered commonready Session typed6E invocation -> real mandatory handler exactly once -> post transition/source/root qualification -> ordered exact wire reply',
  'exclusions':'Root Application/record2/transport2 and mixed adapter2/plan2 final context only; no root books/catalog/ledger/docs/artifact receipts current pins'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':186,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current_count':len(current),'source_sites':len(sites),'context_sites':len(contextsites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
