"""Round183 full source originals and static source accounting only; no native/codec run."""
from pathlib import Path
import argparse,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/integration/packet-connections-20261006/native-common-actor-name-source-01'
OUT=BASE/'agents/common-actor-name-source'
OWN=['src/game/SharedNativeActorNameSource.h','src/game/SharedNativeActorNameSource.cpp',
 'tools/reconstruction/native_actor_name_source183.py']
CONTEXT=['src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
 'src/game/SharedTaiwanWorldEntered.cpp','src/cn/world/SharedWorldReady.cpp',
 'src/game/SharedPublishedChatNameSource.h','src/game/SharedPublishedChatNameSource.cpp']
BEFORE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']+CONTEXT[:2]+[
 'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/game/RecoveredCharacter.h','src/game/RecoveredPosition.h',
 'src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp','src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
 'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp','src/protocol/RecoveredRemoteActor.h','src/cn/protocol/CnRemoteActor.h',
 'src/net/Session.h','src/net/Session.cpp','src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp']
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
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['before','final'],required=True)
 args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 if args.stage=='before':
  raw=(BASE/'before-manifest.json').read_bytes()
  if sha(raw)!='c1972084a5d17f328e1ce38beb193364cde4ef79c1372b0a7917dd0d018d616a':raise RuntimeError('freshbefore drift')
  index={r['path']:r for r in json.loads(raw.decode('utf-8-sig'))};rows=[]
  for i,n in enumerate(BEFORE):
   row=index[n];b=(BASE/row['snapshot']).read_bytes()
   if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise RuntimeError('source before original drift:'+n)
   c=f'before/b{i:03d}.txt';write(c,b);rows.append({'path':n,'absolute_path':str((ROOT/n).resolve()),'copy':c,'bytes':len(b),'sha256':sha(b)})
  dump('before-source-origins.json',rows)
  dump('new-source-before.json',[{'path':n,'existed':n in index,'copy':None} for n in OWN])
  dump('root-before-context-origins.json',originals(CONTEXT[:2],'context-before'))
  print(json.dumps({'before':len(rows),'root_context':2}));return
 before=json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))
 stable=[r['path'] for r in before if r['path'].startswith('src/') and r['path'] not in CONTEXT]+OWN
 current=originals(stable,'current');dump('current-source-origins.json',current)
 dump('root-final-context-origins.json',originals(CONTEXT,'context-final'))
 for i,n in enumerate(OWN):write(f'diff/n{i:03d}.diff',''.join(difflib.unified_diff([], (ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile=n+' (absent baseline)',tofile=n+' (final)')).encode())
 sites=[]
 for n in OWN[:2]:
  for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if any(s in text for s in ['::create(','::owns_presence(','::project(','::current(','::project_owned(','ready_characters','state.current','source.actor_handle','std::fill_n','parse_logical','from_encoded','from_utf8','source_revision','common_name_source','receiver_bound','same_row']):sites.append({'path':n,'line':line,'source':text})
 dump('source-sites.json',sites)
 contextsites=[]
 for n in CONTEXT:
  for line,text in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines(),1):
   if any(s in text for s in ['common_name_source','project_common_name','common_name_current','supplied_records','projected_records','native_name_codepage','native_name_page','native_page','native_encoded']):contextsites.append({'path':n,'line':line,'source':text,'role':'actual-read final root context, excluded current pins'})
 dump('root-context-sites.json',contextsites)
 dump('original-inputs.json',[]);dump('native-original-inputs.json',[]);dump('derived-inputs.json',[])
 dump('stages.json',['Owned actual complete native model/strong receiver/full source and recipient lease before real callbacks',
  'Mandatory actual receiver rawState revision/936-or-950 page/Current; TW same actual loaded selector, CNtag0 only',
  'Complete real ready-character population -> exact active source full64 root/profile/name_codepage -> strict original UTF8 -> actual receiver strict encoded original',
  'Zero only logical29..44 then copy encoded original+NUL; preserve all other complete81 bytes; parse actual native model',
  'RealState Current and exact source/root/position requalification before/after projection; actual receiver fulltuple and pending-or-ready lease checked',
  'Root actual visibility publication points opt into common_name_source; helper.current exact complete projected bytes, no appearance/visibility/permission inference'])
 dump('gaps.json',['Actual receiver rawState issuer/window/lifecycle Current and profile must be supplied; no region/language/ACP/global default',
  'Source must be actual active ready root; pending new source/name creation/adapted TW or CNtag1/name aliases remain unqualified by this source',
  'Initial recipient readiness/admission/battle/resource/visibility/full5D/full6F authority stays actual publisher; helper is not ready activation or permission',
  'No Main activation/build/tests/runtime/codec/native acceptance/deployment; complete packet route increment0 and full-game denominator still unknown'])
 dump('findings.json',{'round':183,'new_cpp_sources':2,'modified_cpp_sources':0,'new_source_tool':1,'before_full_originals':len(before),
  'current_full_originals':len(current),'root_before_context_originals':2,'extra_before_originals':4,'root_final_context_originals':6,'source_sites':len(sites),'context_sites':len(contextsites),
  'initial_owned_full_originals':3,'refinement_before_owned_originals':3,
  'native_inputs':0,'actual_asset_inputs':0,'derived_inputs':0,'complete_route_increment':0,'tests_run':False,'runtime_run':False,
  'concrete_change':'Actual common stored original name produces only full native6F firstname field; explicit attached exact source is mandatory; no generic nameproof-only shell or empty/default success',
  'observer_contract':'Actual repository/rawState observers must be pure read-only non-yielding; no pumping/sends/writes/retained borrowed args. Final actualCurrent follows last source root read; this is not distributed atomicity or native acceptance.',
  'cross_page_identity_context':'Root PublishedName separately strictly qualifies same stored original Unicode at C2S target input page and actual preceding6F name page; byte inequality is allowed, no script/alias change',
  'current_pin_exclusions':'Root Visibility/WorldEntered/WorldReady/PublishedName six mutable sources, root books/ledger/catalog/reports/docs and artifact receipts'})
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['LIST.json','seal.json'])
 listing=[{'path':p.relative_to(OUT).as_posix(),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in files];dump('LIST.json',listing)
 members=listing+[{'path':'LIST.json','bytes':len((OUT/'LIST.json').read_bytes()),'sha256':sha((OUT/'LIST.json').read_bytes())}]
 dump('seal.json',{'round':183,'members':members,'member_count':len(members),'source_only':True})
 print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_with_seal':len(members)+1,'current_count':len(current),'source_sites':len(sites),'context_sites':len(contextsites),'owned':[r for r in current if r['path'] in OWN]},indent=2))
if __name__=='__main__':main()
