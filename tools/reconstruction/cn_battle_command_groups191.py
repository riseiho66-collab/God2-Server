"""191 file/source originals and hashes only; no game/native/codec execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-group-source-01/agents/cn-battle-command-groups'
OWN=['src/cn/world/SharedNativeBattleCommandGroups.h','src/cn/world/SharedNativeBattleCommandGroups.cpp','tools/reconstruction/cn_battle_command_groups191.py']
CONTEXT=['src/cn/world/SharedNativeBattleCommandSource.h','src/cn/world/SharedNativeBattleCommandSource.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
STABLE=['src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp','src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/cn/protocol/CnBattleCommand35.h','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h']
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,b):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def dump(n,x):write(n,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def capture(names,folder):
 rows=[]
 for i,n in enumerate(names):
  b=(ROOT/n).read_bytes();c=f'{folder}/s{i:03d}.txt';write(c,b)
  rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
 return rows
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',required=True,choices=['tool-initial','context-read','final']);args=ap.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 if args.stage=='tool-initial':dump('tool-initial-source-origins.json',capture(OWN[2:],'tool-initial'));return
 if args.stage=='context-read':dump('actual-read-context-origins.json',capture(CONTEXT,'read-context'));return
 current=capture(STABLE+OWN,'current');dump('current-source-origins.json',current)
 context=capture(CONTEXT,'final-context');dump('root-peer-final-context-origins.json',context)
 # Preserve the initial empty native/source-input epoch; final actual source
 # list is current-only, and mutable callers are clearly final context.
 write('initial-original-inputs-list.json',(OUT/'original-inputs.json').read_bytes())
 actual=[{'path':r['absolute_path'],'source_path':r['path'],'copy':r['copy'],'bytes':r['bytes'],'sha256':r['sha256'],
  'role':'stable current source' if r in current else 'root/peer final context only, not current pin'} for r in current+context]
 (OUT/'original-inputs.json').write_bytes((json.dumps(actual,indent=2)+'\n').encode())
 for i,n in enumerate(OWN):
  write(f'diff/new{i:03d}.diff',''.join(difflib.unified_diff([], (ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (actual freshbefore absent)',tofile=n+' (final)')).encode())
 for epoch in ['initial','refinement','tool-initial']:
  rows=json.loads((OUT/(epoch+'-source-origins.json')).read_text(encoding='utf-8'))
  for i,r in enumerate(rows):
   write(f'diff/{epoch}{i:03d}.diff',''.join(difflib.unified_diff((OUT/r['copy']).read_text(encoding='utf-8').splitlines(True),(ROOT/r['path']).read_text(encoding='utf-8').splitlines(True),fromfile=r['path']+' ('+epoch+')',tofile=r['path']+' (final)')).encode())
 sites=[];contexts=[]
 for names,dest in [(OWN[:2],sites),(CONTEXT,contexts)]:
  for n in names:
   for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
    if any(s in text for s in ['current','Current','Authority','authority','group','Group','scope','Scope','Receipt','receipt','release','pending','prepare','execute','evidence','native_token','registration']):dest.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites);dump('context-sites.json',contexts)
 dump('stages.json',[
  'Actual same connection/full lease and original private native token acquired strongly before callbacks; permanent receiver weak',
  'BeforeExecute pure real Authority.prepare decides Single/Append/Final and actual issuer/group capability plus explicit generations, including zero',
  'Complete physical17B requests copied/allocated in arrival order under explicit positive budgets; no native default14, masking, truncation or duplicate inference',
  'Append retains owned pending group and only returns explicit intermediate Reply; no cost/settlement execution',
  'Single/Final consume prepared once, final requires same actual prior issuer/group incarnation; one real execute_group and no retry or rollback',
  'Private immutable receipt owns exact request/token/Plan/group and underlying actual Result; post checks verify receipt/source/result before real Authority.current',
  'Source wrapper separately rereads entire ready common root and saved position before/after adapter current; adapter registry fence is not independent root authority',
  'Caught reentry/exact release monotonically terminalizes and defers local pending destruction until callback unwind; no common/token/core cleanup',
  'Root actual Gameplay selects exactly one direct or grouped owner and sends adapter through existing ordered held command source'])
 dump('gaps.json',[
  'Actual official server continuation/group consumer, MP/item cost, actor mapping, grant, expiry and replay rules remain supplied Authority obligations; no recovered rule implementation claimed',
  'No part inferred only from command kind80, no duplicate suppression or specialWORD universal targetmask',
  'Full common root/position observers are provided by actual command Source; adapter receives exact supplied Scope and current token, not independently queried repository roots',
  'Append real explicit intermediate reply requires qualified native semantics; missing prepare/current/execute result terminalizes, no default ACK/noReply',
  'Once group committed prefix and locally released native reply cannot be rolled back or replayed; no distributed atomicity claim',
  'Real provider, battle/window/grant lifecycle, native replies and Application Main activation remain OPEN; complete routes increment0',
  'No build/tests/C++/native/runtime/codec/API/DB/SQL/deployment or stopped155/conversion chain'])
 counts={}
 for e in ['before','initial','refinement','tool-initial']:
  counts[e]=len(json.loads((OUT/(e+'-source-origins.json')).read_text(encoding='utf-8')))
 counts['actual-read-context']=len(json.loads((OUT/'actual-read-context-origins.json').read_text(encoding='utf-8')))
 dump('findings.json',{'round':191,'new_cpp_sources':2,'modified_cpp_sources':0,'new_tool':1,'source_epochs':counts,'current_originals':len(current),'final_context_originals':len(context),'full_source_originals':sum(counts.values())+len(current)+len(context),'source_sites':len(sites),'context_sites':len(contexts),'actual_native_inputs':0,'new_native_spans':0,'complete_route_increment':0,'before_scope':'Actual freshbefore1365 full originals; own new3 absent; no old seal modification','refinements':'Terminal callback-unwind cleanup plus accept exact real generation0, not a native nonzero constraint','current_exclusions':'Peer command Source2 and Root Gameplay2 context only; no root mutable books/catalog/report/ledger/artifact pins','tests_run':False,'native_run':False,'runtime_run':False,'codec_run':False,'route_scope':'Once group-callback buffering source with mandatory actual Authority; no completed official native rules'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 members=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files]
 dump('LIST.json',members)
 members.append({'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())})
 dump('seal.json',{'round':191,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current':len(current),'context':len(context),'full_source_originals':sum(counts.values())+len(current)+len(context),'sites':len(sites),'context_sites':len(contexts),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
