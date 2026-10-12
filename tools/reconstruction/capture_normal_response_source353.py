from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
I=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round353-normal-original-response-transport-implementation')
P=I.parent/'round353-blacklist-original-response-custody-proposal'
head='618eb9cbce52632f984b45f7409407a4e465c234'
h=lambda b:hashlib.sha256(b).hexdigest()
def put(rel,b):
 p=I/rel;assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def jout(rel,o):put(rel,(json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode())
edits=json.loads((I/'exact-edits-and-inverse.json').read_text());corr=json.loads((I/'fifo-counter-correction.json').read_text());refs=[];before=[];checks=[]
for e in edits:
 rel=e['path'];old=(I/'before'/rel).read_bytes();candidate=(I/'candidate'/rel).read_bytes();current=(S/rel).read_bytes()
 assert h(old)==e['before_sha256'] and len(old)==e['before_bytes']
 assert subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout==old
 assert h(candidate)==e['after_sha256'] and len(candidate)==e['after_bytes']
 inverse=candidate
 for x in reversed(e['edits']):
  a=x['new'].encode();b=x['old'].encode();assert inverse.count(a)==x['count'],(rel,a[:70],inverse.count(a));inverse=inverse.replace(a,b)
 assert inverse==old
 if rel.endswith('.cpp'):
  assert h(current)==corr['after_sha256'] and current==candidate.replace(corr['old'].encode(),corr['new'].encode())
  assert current.count(corr['new'].encode())==1 and current.replace(corr['new'].encode(),corr['old'].encode())==candidate
  assert (I/'fifo-counter-corrected'/rel).read_bytes()==current
 else:assert current==candidate
 put('final/'+rel,current)
 refs.append({'actual_path':str(S/rel),'retained':'final/'+rel,'bytes':len(current),'sha256':h(current)})
 before.append({'actual_path':str(S/rel),'retained':'before/'+rel,'bytes':len(old),'sha256':h(old),'head':head})
 checks.append({'path':rel,'git_head_before_exact':True,'literal_inverse_stage1_exact':True,'stage2_counter_only_exact':True,'current_final_exact':True})
jout('source-references.json',refs)
jout('before-manifest-correction.json',{'reason':'Original 3-byte empty array retained; Windows slash filtering omitted metadata only. Whole before files were preserved.','original_manifest_sha256':h((I/'before-manifest.json').read_bytes()),'references':before})
# Verify and retain selected historical dependencies, no product script execution.
prior=json.loads((P/'source-references.json').read_text());index=[]
for r in prior:
 b=(P/r['retained']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256'];index.append({'original_path':str(P/r['retained']),'bytes':len(b),'sha256':h(b),'head':head})
put('dependencies/historical-source-references.json',(P/'source-references.json').read_bytes())
cuts=json.loads((P/'selected-source-cuts.json').read_text())
for c in cuts:
 b=(P/c['retained']).read_bytes();assert len(b)==c['bytes'] and h(b)==c['sha256'];put('dependencies/'+c['retained'],b)
put('dependencies/selected-source-cuts.json',(P/'selected-source-cuts.json').read_bytes())
jout('dependencies/original-whole-source-index.json',index)
# Original else path remains exact; old terminal/nativePK marker semantics preserved.
cpp=(S/'src/net/Session.cpp').read_bytes();oldcpp=(I/'before/src/net/Session.cpp').read_bytes()
legacy=b's.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});'
assert oldcpp.count(legacy)>=1 and cpp.count(legacy)>=1
observed=b's.writes.push_back({bytes,{}});s.write_bytes+=bytes->size();'
assert cpp.count(observed)==1
# The complete inverse above is stronger than an invented default-path simulation.
jout('static-source-proof.json',{'verdict':'PASS','references':len(refs),'reference_bytes':sum(r['bytes'] for r in refs),'checks':checks,'legacy_else_counter_order_retained':True,'new_observed_counter_push_before_debit':True,'dependencies_historical_whole_verified':len(index),'selected_nonwhole_dependency_cuts':len(cuts),'target_execution':False,'db_sql_execution':False,'build_test_execution':False})
for r in refs:assert (S/Path(r['actual_path']).relative_to(S)).read_bytes()==(I/r['retained']).read_bytes()
print(json.dumps({'verdict':'PASS','current_references':len(refs),'current_bytes':sum(r['bytes'] for r in refs),'before_corrected':len(before),'historical_dependencies_verified':len(index),'selected_cuts':len(cuts),'sha256':{Path(r['actual_path']).name:r['sha256'] for r in refs}}))
