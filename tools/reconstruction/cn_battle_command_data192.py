"""192 battle data file/source originals and hashes only; no game/native/codec execution."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-data-source-01/agents/cn-battle-command-data'
OWN=['src/cn/world/SharedNativeBattleCommandData.h','src/cn/world/SharedNativeBattleCommandData.cpp','tools/reconstruction/cn_battle_command_data192.py']
CONTEXT=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/cn/protocol/CnBattleSkillDefinition.h','src/cn/protocol/CnBattleInventorySlot.h']
STABLE=['src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/cn/world/SharedNativeBattleCommandGroups.h','src/cn/world/SharedNativeBattleCommandGroups.cpp','src/cn/world/SharedNativeBattleCommandSource.h','src/cn/world/SharedNativeBattleCommandSource.cpp','src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp','src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/cn/protocol/CnBattleCommand35.h','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h']
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
  'Actual per-connection Data Configuration -> Groups Authority -> original command Source, three mutually exclusive Gameplay selections',
  'Mandatory actual catalog_current establishes lifetime/reader/catalog binding before concrete shared-store lookup; all strong owners retained',
  'Real Authority supplies exact ordered domains; raw skill03/17/83/97 hex requires full zeroextended operand<=FFFF -> actual shared CN skill lookup -> pinned110B readonly fields plus whole provenance',
  'Raw item05/0C high signed slotBYTE, middleBYTEzero, lowWORDitem -> actual complete dictionary36B exactslot/item comparison; preserve all quantity/opaque bytes',
  'Complete snapshot pre/post rereads compare same full dictionary/generation; memory budget not native capacity38 or50',
  'All physical requests including Opaque remain owned and ordered; common root/source position pre/post remain original Source obligation',
  'Pure Current retains original catalog rows/before inventory image; post-cost inventory Current uses actual Result rather than silent baseline replacement',
  'Single/Final real execute_group consumes one input before callback; Group private receipt retains actual result/reply; Append never settles',
  'Every public qualification failure/throw/caught reentry monotonically terminal; deferred input destruction under active guard; no common/Core cost cancellation'])
 dump('gaps.json',[
  'Native runtime selected skill-pointer lineage and common learned identity/MP/range/grant/expiry/replay/cost remain actual DataAuthority obligations; definition presence is not permission',
  'InventoryRepository/Inventory placeholders and TW CUSTOM OwnedBagProjectionService are not CN authority; actual complete inventory dictionary source/ownership mapping must be supplied',
  'Getter slot0..37 differs from updater slot0..49; client scan30..37 and selectedbyte29 edge retained, no automatic correction/custody inference',
  'Quantity signedBYTE and raw itemWORD preserved, no cap or use charge; actual post retained beforeimage Current must qualify settled outcome via actual Result',
  'Data cache is a bounded observation retained until replaced/terminal/destruction/last strong wrapper reference; Group release clears only Group local pending, does not mean Core cancellation or direct Data release hook',
  'Exact hex03/17/83/97 (17hex=23decimal) only; no0x11/0x91 skill branch, no global80 stripping, high unqualified bits remain opaque or fail selected-domain resolution',
  'NoReply existing Source runs pre/after-execute/before-queue; held native replies additionally before/after-release. Do not claim five callbacks always run',
  'Real official costs/group/Core/rules/target/grant/native replies/Main activation remain OPEN; complete routes increment0',
  'No build/tests/runtime/native/codec/API/DB/SQL/deploy or prohibited155/conversion chain'])
 counts={}
 for e in ['before','initial','refinement','tool-initial']:
  counts[e]=len(json.loads((OUT/(e+'-source-origins.json')).read_text(encoding='utf-8')))
 counts['actual-read-context']=len(json.loads((OUT/'actual-read-context-origins.json').read_text(encoding='utf-8')))
 dump('findings.json',{'round':192,'new_cpp_sources':2,'modified_cpp_sources':0,'new_tool':1,'source_epochs':counts,'current_originals':len(current),'final_context_originals':len(context),'full_source_originals':sum(counts.values())+len(current)+len(context),'source_sites':len(sites),'context_sites':len(contexts),'actual_native_inputs':0,'new_native_spans':0,'complete_route_increment':0,'before_scope':'Actual freshbefore1373 full originals, own3 and peer2 views absent','refinements':'Mandatory actual catalog binding before borrowed reader lookup; every public early failure terminal/deferred cleanup','current_exclusions':'Root Gameplay2 and native readonly view2 finalcontext only, no books/catalog/report/ledger/artifact receipts','tests_run':False,'native_run':False,'runtime_run':False,'codec_run':False,'route_scope':'Concrete CN shared catalog lookup/provenance plus actual supplied complete inventory dictionary -> once Group callback source; existence never authorizes skill/item/cost'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 members=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files]
 dump('LIST.json',members)
 members.append({'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())})
 dump('seal.json',{'round':192,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current':len(current),'context':len(context),'full_source_originals':sum(counts.values())+len(current)+len(context),'sites':len(sites),'context_sites':len(contexts),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
