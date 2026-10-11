"""193 static source inventory and full file originals; no native/DB/codec/game execution."""
from pathlib import Path
import argparse, difflib, hashlib, json, re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-selection-source-01/agents/cn-battle-skill-selection-source'
OWN=['src/cn/world/CnBattleSkillSelectionSource.h','src/cn/world/CnBattleSkillSelectionSource.cpp','tools/reconstruction/cn_battle_skill_selection_source193.py']
CONTEXT=['src/cn/world/SharedNativeBattleCommandData.h','src/cn/world/SharedNativeBattleCommandData.cpp','src/cn/world/SharedWorldGameplay.cpp','src/cn/protocol/CnBattleSkillSelection.h']
BEFORE=json.loads((OUT/'before-source-origins.json').read_text())
STABLE=[r['path'] for r in BEFORE if r['path'] not in CONTEXT+['src/core/Application.cpp']]
STABLE += [r['path'] for r in json.loads((OUT/'additional-read-source-origins.json').read_text())]

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
def inventory():
 pattern=re.compile(r'learned|learn_skill|learning|character_skills|selected_deity_has_skill|store_deity|load_deities|skill[s_]\b|subject_',re.I)
 rows=[];sites=[]
 for prefix in ['src/db','src/cn/world','src/handlers','src/game','scripts']:
  for p in sorted((ROOT/prefix).rglob('*')):
   if not p.is_file() or p.suffix not in ['.h','.cpp','.lua']:continue
   b=p.read_bytes();n=p.relative_to(ROOT).as_posix()
   rows.append({'path':n,'bytes':len(b),'sha256':sha(b),'role':'bounded text search population, hash metadata only; not full original copy'})
   for line,t in enumerate(b.decode('utf-8',errors='replace').splitlines(),1):
    if pattern.search(t):sites.append({'path':n,'line':line,'text':t})
 dump('bounded-search-population.json',rows);dump('bounded-search-matches.json',sites)
 dump('inventory-scope.json',{'directories':['src/db','src/cn/world','src/handlers','src/game','scripts'],'suffixes':['.h','.cpp','.lua'],'pattern':pattern.pattern,'source_files':len(rows),'matched_lines':len(sites),'sql':'SQL string text only; no database connection, statements or queries executed','absence':'No direct qualified CN live battle learned persistence/source implementation found in this bounded text inventory; not proof of global absence'})
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',required=True,choices=['tool-initial','initial','refinement','context-read','final']);a=ap.parse_args()
 if a.stage=='tool-initial':dump('tool-initial-source-origins.json',capture(OWN[2:],'tool-initial'));inventory();return
 if a.stage in ['initial','refinement']:dump(a.stage+'-source-origins.json',capture(OWN[:2],a.stage));return
 if a.stage=='context-read':dump('actual-read-context-origins.json',capture(CONTEXT,'read-context'));return
 current=capture(STABLE+OWN,'current');context=capture(CONTEXT,'final-context')
 dump('current-source-origins.json',current);dump('root-peer-final-context-origins.json',context)
 write('initial-original-inputs-list.json',(OUT/'original-inputs.json').read_bytes())
 actual=[{'path':r['absolute_path'],'source_path':r['path'],'copy':r['copy'],'bytes':r['bytes'],'sha256':r['sha256'],'role':'stable source current' if r in current else 'root/peer final context only'} for r in current+context]
 (OUT/'original-inputs.json').write_bytes((json.dumps(actual,indent=2)+'\n').encode())
 for epoch in ['initial','refinement','tool-initial']:
  p=OUT/(epoch+'-source-origins.json')
  if not p.exists():continue
  for i,r in enumerate(json.loads(p.read_text())):
   write(f'diff/{epoch}{i:03}.diff',''.join(difflib.unified_diff((OUT/r['copy']).read_text(encoding='utf-8').splitlines(True),(ROOT/r['path']).read_text(encoding='utf-8').splitlines(True),fromfile=r['path']+' '+epoch,tofile=r['path']+' final')).encode())
 for i,n in enumerate(OWN):write(f'diff/new{i:03}.diff',''.join(difflib.unified_diff([],(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' before absent',tofile=n+' final')).encode())
 sites=[]
 for n in OWN[:2]:
  for line,t in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if any(x in t for x in ['current','Current','resolve','selected','pointer','file_offset','source','catalog','terminal','operation']):sites.append({'path':n,'line':line,'text':t})
 dump('source-sites.json',sites)
 dump('backend-findings.json',[
  {'source':'SqliteCompanionRepository + Migration character_deities/selection','actual':'Complete TW deity declaration19/status29/skills4B records, account/character ownership, trusted import, row and selection CAS revision, retained source SHA/authority/evidence','limit':'TW source SHA and CUSTOM0039/CUSTOM0058 acquisition/diagnostic policy; no demonstrated CN live actor/list learned identity mapping'},
  {'source':'Application diagnostic battle + Battle/RecoveredBattleService/Lua combat','actual':'CUSTOM0058/0059 checks saved selected deity for custom126/150; explicit injected action policies; actual resource settlement persistence','limit':'CUSTOM0007/0008/0006 and diagnostics cannot supply original CN learned/cost/grant/rules'},
  {'source':'CN SubjectSkillPublication/RosterPublication/PrebornWindowSource','actual':'Owned original post-commit records and definition resolution with required real current/save/replay callbacks','limit':'Output/common operation hooks do not implement the missing real live battle learned acquisition/store owner'},
  {'source':'CnPrebornSubjectState/SkillReferences','actual':'Own selected3EC row, ordered pointer/flags, actual bank source, exact group/fileoffset -> actual shared catalog','limit':'Preborn UI namespace is not automatically current CN battle primary/secondary owner'},
  {'source':'193 concrete CnBattleSkillSelectionSource','actual':'Immutable supplied live battle selected list/fullbank -> exact original pointer/fileoffset/110B definition -> shared catalog whole provenance; current source/resource/store qualification','limit':'Actual source supplier, common learned/custody/native actor identity, MP/targets/cost/grant/expiry/replay remain real DataAuthority responsibilities'}])
 dump('gaps.json',[
  'Bounded qualified absence of direct CN live battle learned persistence source in searched source directories; actual TW persisted skills exist, never assert all learned storage absent',
  'Real live battle owner/list/bank snapshot must be supplied with current actual epoch; native raw pointers are not operational process-memory requirements or common IDs',
  'Writer count append has no native safe capacity check; qualified readonly layout uses primary100/secondary10 bounds, not learning/progression limits',
  'Selected pointer/source bank must match exact definition bytes and file offset; key equality is insufficient, raw bit14/bit15 retained without permission inference',
  'Source Current and actual catalog lifetime/reader Current are pure/nonyielding/read-only; no fabricated DB learning table or authority',
  'Optional Data skill_selection is supplied recovery projection, not required process/client-memory access. Selecting it requires both source and actual Read; mismatches reject without same-key fallback',
  'Current retains original list/bank/index snapshot and catalog records, never rebase after settlement; changed or obsolete selection source fails this selected evidence path, actual common learned authority remains necessary in every path',
  'Learning/acquisition/save settlement, native group/cost/target/rules/grant/Core/Main remain OPEN; complete routes increment0',
  'No builds/tests/game/native/codec/API/DB/SQL/runtime/deploy or155/conversion-chain execution'])
 epochs={}
 for e in ['before','additional-read','initial','refinement','tool-initial','actual-read-context']:
  p=OUT/(e+'-source-origins.json')
  if p.exists():epochs[e]=len(json.loads(p.read_text()))
 dump('stages.json',['Factory retains exact strong catalog/private source identity without a database lookup','Actual DataAuthority.catalog_current qualifies reader and store lifetime before every optional native selection read/resolve/current','Actual readonly Native selection owns full component/bank112656/index/flags and selected ordered list; source copies it before observers','Every actual native pointer/file offset/full110B definition matches exact shared record including provenance and record hash','Actual selected signed index and zeroextended full C35 operand must agree; no equal-key search, pointer replacement or generic80 stripping','Retained snapshot current rechecks original native source and exact catalog rows; no post-settlement silent rebase','Data actual common learned/source/cost/target/grant/rules Authority remains mandatory; actual Group callback once/complete reply path unchanged'])
 dump('findings.json',{'round':193,'new_cpp_sources':2,'new_tool':1,'modified_cpp_sources':0,'source_epochs':epochs,'current_originals':len(current),'final_context_originals':len(context),'full_source_originals':sum(epochs.values())+len(current)+len(context),'actual_original_inputs':len(actual),'actual_native_inputs':0,'new_native_spans':0,'source_sites':len(sites),'complete_route_increment':0,'current_exclusions':'Root Data2/Gameplaycpp + native raw selection header context only; Application diagnostic before is historical full input, no current mutable books/catalog/ledger/reports/receipts','executed':'Only Python-B file/source IO and hashes; no C++/native/DB/game/codec execution'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 members=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files]
 dump('LIST.json',members);members.append({'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())})
 dump('seal.json',{'round':193,'source_only':True,'members':members,'member_count':len(members)})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current':len(current),'context':len(context),'full_source_originals':sum(epochs.values())+len(current)+len(context),'actual_inputs':len(actual),'source_sites':len(sites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
