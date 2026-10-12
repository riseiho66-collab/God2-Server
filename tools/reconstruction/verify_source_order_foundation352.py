from pathlib import Path
import hashlib,json,subprocess
O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-blacklist-submitted-chain-source-order-review')
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-blacklist-submitted-chain-host-implementation')
h=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 assert not p.exists(),str(p)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
refs=json.loads((O/'baseline-source-references.json').read_text('utf-8'))
for r in refs:
 b=(O/r['retained']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
 if r.get('head'):
  relative=Path(r['actual_path']).relative_to(S).as_posix()
  exact=subprocess.run(['git','show',r['head']+':'+relative],cwd=S,stdout=subprocess.PIPE,check=True).stdout
  assert b==exact
 else:assert Path(r['actual_path']).read_bytes()==b
C=O/'history/callback-qualified-candidate'
final=(C/'Application.cpp').read_bytes()
assert len(final)==713375 and h(final)=='6fc65b1edb323a8ac423958447af61ef2db2b4b1a4f0e980cc22ce8f42e3e896'
assert (S/'src/core/Application.cpp').read_bytes()==final
for name in ['Application.candidate.cpp','Application.before-callback-qualification.cpp','Application.callback-qualified.cpp']:
 put(O/'history/host-stages'/name,(D/name).read_bytes())
def undo(b,receipt):
 assert len(b)==receipt['after_bytes'] and h(b)==receipt['after_sha256']
 for e in reversed(receipt['edits']):
  pairs=[]
  for nl in ['\n','\r\n']:
   new=e['new'].replace('\r\n','\n').replace('\n',nl).encode();old=e['old'].replace('\r\n','\n').replace('\n',nl).encode()
   if (new,old) not in pairs:pairs.append((new,old))
  matches=[(new,old) for new,old in pairs if b.count(new)==e.get('count',1)]
  assert len(matches)==1,(len(matches),e['new'][:90])
  new,old=matches[0];b=b.replace(new,old,e.get('count',1))
 assert len(b)==receipt['before_bytes'] and h(b)==receipt['before_sha256']
 return b
middle=undo(final,json.loads((C/'callback-qualification-correction.json').read_text('utf-8')))
assert middle==(O/'history/host-stages/Application.candidate.cpp').read_bytes()
original=undo(middle,json.loads((C/'exact-edits-and-inverse.json').read_text('utf-8')))
assert original==(O/'baseline/src/core/Application.cpp').read_bytes()
proof={'verdict':'PASS_STATIC_SOURCE_ORDER_FOUNDATION','baseline_references':len(refs),'baseline_reference_bytes':sum(r['bytes'] for r in refs),'two_stage_whole_inverse_exact':True,'candidate_bytes':len(final),'candidate_sha256':h(final),'scope':'HISTORICAL_FOUNDATION_NOT_FINAL_CANONICAL_SOURCE_FREEZE','source_variants':['PeerPriorPendingA5','PeerPriorPendingA4','SenderPriorIncomingPendingA5','SenderPriorIncomingPendingA4'],'node_limit':256,'node_limit_qualification':'ACTUAL_TRANSPORT_ATTEMPT_ADMISSION_NOT_SOURCE_QUOTA_OR_ACK','no_per_node_snapshots':True,'normal_context_abort':'OPEN','credits':{'opcode':0,'format':0,'parser':0,'handler':0,'native_method':0,'full_route':0},'target_execution':False}
put(O/'foundation-verification.json',(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(proof))
