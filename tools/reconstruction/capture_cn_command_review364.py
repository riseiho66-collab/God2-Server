from pathlib import Path
import hashlib,json,sys,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
O=A/'round364-cn-command-common-definition-independent-source-review'
T=A/'round364-cn-command-common-definition-implementation'
P=A/'round364-cn-command-common-definition-authority'
H='1d22ee991fa4ca899ddef051511bba738a54cb77'
assert len(sys.argv)==4,'required final T seal SHA/member count/member bytes'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert not O.exists(),'exclusive independent review'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==H
helper=Path(__file__).read_bytes()
assert b'\r' not in helper and not helper.startswith(b'\xef\xbb\xbf') and helper.endswith(b'\n') and not helper.endswith(b'\n\n')
def put(rel,b):
 p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
def j(rel,v):put(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
verified=[]
for label,package,expected in [('T364',T,(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))),('A364',P,('dbf7e0308eb4fa057abc53a8348e71e36839d8c6659fee37421dadce8b1af336',46,1841072)),('I363',A/'round363-owned-input-continuation-independent-source-review',('ce7fe33323d90d5db7f890c2298d3c238c47f90f9bb3fefeede60eba031bb88d',47,3325354))]:
 sb=(package/'seal.json').read_bytes();seal=json.loads(sb);assert sha(sb)==expected[0]
 rows=seal['members'];total=0;names=set()
 assert type(seal['member_count']) is int and seal['member_count']==len(rows)==expected[1]
 for v in rows:
  name=v.get('path',v.get('relative_path'));assert isinstance(name,str) and name not in names;names.add(name)
  p=package/name;assert p.resolve().is_relative_to(package.resolve());b=p.read_bytes()
  assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256'];total+=len(b)
 amount=seal.get('member_bytes',seal.get('total_bytes'));assert type(amount) is int and amount==total==expected[2]
 put('upstream/'+label+'-seal.json',sb)
 verified.append(dict(package=str(package),seal_sha256=sha(sb),member_count=len(rows),member_bytes=total,every_member_verified=True))
j('upstream-individual-verification.json',verified)
refs=[];baserefs=[];current={};baseline={}
pins={'src/cn/world/SharedNativeBattleCommandData.h':(6091,'0ff6c0da2ef5821cc30e73f4d78f127ff6a4a2641b896bcb0ff7553834a760b7'),'src/cn/world/SharedNativeBattleCommandData.cpp':(22083,'48a6b16da9b97dcf0438b5edbe4fcef9a06d3f7a9ced57d4e7882ac43bfb4b0b')}
for entry in json.loads((P/'source-references.json').read_bytes()):
 rel=Path(entry['actual_path']).relative_to(R).as_posix();old=Path(entry['retained']).read_bytes()
 assert len(old)==entry['bytes'] and sha(old)==entry['sha256'];baseline[rel]=old
 b=(R/rel).read_bytes();current[rel]=b
 if rel in pins:
  assert len(b)==pins[rel][0] and sha(b)==pins[rel][1]
  put('baseline/'+rel,old);baserefs.append(dict(actual_path=str(R/rel),retained=str(O/'baseline'/rel),bytes=len(old),sha256=sha(old)))
 else:assert b==old,'frozen supplier differs from immutable HEAD: '+rel
 put('current/'+rel,b);refs.append(dict(actual_path=str(R/rel),retained=str(O/'current'/rel),bytes=len(b),sha256=sha(b)))
j('source-references.json',refs);j('baseline-source-references.json',baserefs)
initial=json.loads((T/'exact-edits-and-inverse.json').read_bytes());corr=json.loads((T/'continuation-correction-v3.json').read_bytes())
assert len(initial['edits'])==14 and len(corr['edits'])==5
inverse=[]
for rel in pins:
 b=current[rel]
 for receipt in [corr,initial]:
  for v in reversed(receipt['edits']):
   if v['path']==rel:
    old=bytes.fromhex(v['old_hex']);new=bytes.fromhex(v['new_hex']);assert new and b.count(new)==v['count'];b=b.replace(new,old,v['count'])
 assert b==baseline[rel]==subprocess.check_output(['git','show',H+':'+rel],cwd=R)
 put('inverse/'+rel,b);inverse.append(dict(path=rel,whole_literal_inverse=True,baseline_sha256=sha(b),bytes=len(b)))
j('inverse-verification.json',dict(baseline=H,initial_edits=14,additive_edits=5,files=inverse))
put('history/initial-edits.json',(T/'exact-edits-and-inverse.json').read_bytes());put('history/continuation-correction-v3.json',(T/'continuation-correction-v3.json').read_bytes())
put('history/failed-correction-v2.json',(T/'failed-correction-v2.json').read_bytes());put('history/final-current-pins-v3.json',(T/'final-current-pins-v3.json').read_bytes())
cuts=[]
spec=[('src/cn/world/SharedNativeBattleCommandData.h',40,95),('src/cn/world/SharedNativeBattleCommandData.cpp',11,64),('src/cn/world/SharedNativeBattleCommandData.cpp',125,195),('src/cn/world/SharedNativeBattleCommandData.cpp',196,221),('src/cn/world/SharedNativeBattleCommandData.cpp',237,295),('src/cn/world/SharedNativeBattleCommandData.cpp',297,326),('src/cn/world/SharedNativeBattleCommandGroups.cpp',111,161),('src/cn/assets/CnSharedSkillCatalog.cpp',51,96),('src/db/SharedSkillDefinition.h',12,74),('src/cn/world/CnBattleSkillSelectionSource.cpp',21,38),('src/cn/world/CnBattleSkillSelectionSource.cpp',100,125)]
for n,(rel,a,z) in enumerate(spec):
 ls=current[rel].splitlines(keepends=True);assert 0<a<=z<=len(ls);b=b''.join(ls[a-1:z]);dest=f'cuts/{n:02d}-{Path(rel).stem}-{a}-{z}.txt';put(dest,b)
 cuts.append(dict(actual_path=str(R/rel),retained=str(O/dest),bytes=len(b),sha256=sha(b),first_line=a,last_line=z,source_whole_sha256=sha(current[rel])))
j('cut-references.json',cuts)
report='''# I364 final independent source review

PASS_CORRECTED_V3_SOURCE_ONLY. Two actual modified source files carry the common definition in the existing C35 Resolved callbacks. Immutable baseline 1d22ee991fa4ca899ddef051511bba738a54cb77, initial14 + additive5 whole literal inverse, no new source file. All remaining22 retained whole suppliers are byte-identical to that baseline. A364 historical proposal remains immutable.

Initial single-prepare early PASS was superseded when root found Append->Final re-resolve could replace the common counterpart. Corrected v3 independently reviewed in full: exact strong unconsumed prior Append Input, owned old plan/complete requests, lease/token/same-plan source and old current; full newly resolved prefix matches old domain, raw native fields, used item/slot, owning common value and native captured value. The OLD prefix Row is copied back, retaining its private Snapshot Storage instead of replacing it with a same-key newly minted holder. Actual old/new resource observers are fenced; new group plan must retain issuer/group shared ownership and exact generations, and be Append/Final. No saved input does not borrow an old consumed Single. Pure Item/Opaque-only groups do not receive the new prefix guard; mixed inventory remains its real Current policy and used cells, not a new whole-bank equality rule.

Row common_definition appended at END preserves existing positional field order. Item/Opaque stays absent. Resolve retains exact qualified CN requested-native separately from whole owner-selected common metadata; selection compares the full actual Record. Native raw110 parser and full operand key/domain gates remain. Definition data is not actor/learned/grant/cost authority. Full owning value equality covers all raw/source/profile/text/qualification/owner rules; reread never rebases the retained common material.

One owning resolved_resources_current helper checks resolve completion and before/after preparation observers, and retained current/execute paths. Input current still checks before and after actual DataAuthority.current; execute consumes once before actual settlement. Subsequent actual Result qualifies consumed inventory before-image, not a request to reuse old spent rights. Post-COMMIT mismatch/allocation/observer failures terminate through existing source semantics; no rollback of durable prefix, SQL retry or fake response. Copy/read observers may throw. Sequential observer windows are not a cross-SQLite/network atomic CAS; the final post-allocation old-prefix observer is not a universal immutable whole-catalog cut. Actual Groups current and execution recheck the retained new input.

Private original CN453 qualification remains mandatory, so custom126/150 absent original rows remain unavailable here. Historical TW448 saved prefix/private observation is preserved, not widened into custom/CN native issuer or control/list/actor. Current catalog907 pinned source supplier stays byte-identical. No Context pointer, new authority factory, hosted gameplay, native formula, grant, protocol byte, configuration/default or native acceptance claim added. Credits zero for those categories.

No tracked edits by reviewer, compiler, tests, product/native execution, API or SQL. Upstream A364, T364 and I363 are individually read/hash verified; current/baseline/cuts have separate reference lists. Successful LF helper executes once, seal covers every non-seal member with strict integer sums and containment readback.
'''
put('REPORT.md',report.encode());put('capture_cn_command_review364.py',helper)
j('capture-receipt.json',dict(status='PASS_CORRECTED_V3_SOURCE_ONLY',whole_current_count=len(refs),whole_current_bytes=sum(v['bytes'] for v in refs),baseline_count=len(baserefs),cut_count=len(cuts),cut_bytes=sum(v['bytes'] for v in cuts),upstream_members=sum(v['member_count'] for v in verified),upstream_member_bytes=sum(v['member_bytes'] for v in verified),successful_executions=1))
members=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
seal=dict(status='PASS_CORRECTED_V3_SOURCE_ONLY',member_count=len(members),member_bytes=sum(v['bytes'] for v in members),members=members)
j('seal.json',seal)
for v in members:
 p=O/v['path'];assert p.resolve().is_relative_to(O.resolve());b=p.read_bytes();assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256']
assert json.loads((O/'seal.json').read_bytes())==seal
print(json.dumps(dict(package=str(O),member_count=len(members),member_bytes=seal['member_bytes'],seal_bytes=(O/'seal.json').stat().st_size,seal_sha256=sha((O/'seal.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
