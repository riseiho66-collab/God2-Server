from pathlib import Path
import subprocess,hashlib,json,sys
R=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');H='5a21cb97abb20c40080d4bf6be1a67cc4a071278'
O=A/'round365-tw-command-common-definition-independent-source-review';T=A/'round365-tw-command-common-definition-implementation';P=A/'round365-tw-command-common-definition-authority'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert len(sys.argv)==4,'T seal sha/count/bytes required'
assert not O.exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==H
helper=Path(__file__).read_bytes();assert b'\r' not in helper and not helper.startswith(b'\xef\xbb\xbf') and helper.endswith(b'\n') and not helper.endswith(b'\n\n')
def put(rel,b):
 p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
def j(rel,v):put(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
verified=[]
for label,d,expected in [('T365',T,(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))),('A365',P,('9dbc6558e6cdd72630e90c1fef9201218967e8ce85e05216882f9016ce05b2e0',30,1024675)),('I364',A/'round364-cn-command-common-definition-independent-source-review',('b79479ff446c632bbc075faa659752291fe44a98042859421db76464596df168',54,1916806))]:
 sb=(d/'seal.json').read_bytes();s=json.loads(sb);assert sha(sb)==expected[0];rows=s['members'];assert type(s['member_count']) is int and s['member_count']==len(rows)==expected[1]
 names=set();total=0
 for v in rows:
  name=v.get('path',v.get('relative_path'));assert isinstance(name,str) and name not in names;names.add(name);p=d/name;assert p.resolve().is_relative_to(d.resolve());b=p.read_bytes()
  assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256'];total+=len(b)
 amount=s.get('member_bytes',s.get('total_bytes'));assert type(amount) is int and amount==total==expected[2]
 put('upstream/'+label+'-seal.json',sb);verified.append(dict(package=str(d),seal_sha256=sha(sb),member_count=len(rows),member_bytes=total,every_member_verified=True))
j('upstream-individual-verification.json',verified)
pins={'src/game/SharedTaiwanNativeSkillCommandSource.h':(4137,'df661e92a22debf2faf451bb86b13a574b19f83743e60ada37304355385b6f3a'),'src/game/SharedTaiwanNativeSkillCommandSource.cpp':(12588,'0afbafcac12b57716a8b9168230e447f7021a23a17d4268811be3bbbe14517b7')}
current={};baseline={};refs=[];base=[]
for v in json.loads((P/'source-references.json').read_bytes()):
 rel=Path(v['actual_path']).relative_to(R).as_posix();old=Path(v['retained']).read_bytes();assert len(old)==v['bytes'] and sha(old)==v['sha256'];baseline[rel]=old
 b=(R/rel).read_bytes();current[rel]=b
 if rel in pins:
  assert len(b)==pins[rel][0] and sha(b)==pins[rel][1];put('baseline/'+rel,old);base.append(dict(actual_path=str(R/rel),retained=str(O/'baseline'/rel),bytes=len(old),sha256=sha(old)))
 else:assert b==old,'frozen source changed '+rel
 put('current/'+rel,b);refs.append(dict(actual_path=str(R/rel),retained=str(O/'current'/rel),bytes=len(b),sha256=sha(b)))
j('source-references.json',refs);j('baseline-source-references.json',base)
e=json.loads((T/'exact-edits-and-inverse.json').read_bytes());assert e['baseline']==H and len(e['edits'])==6
inverse=[]
for rel in pins:
 b=current[rel]
 for v in reversed(e['edits']):
  if v['path']==rel:
   a=bytes.fromhex(v['old_hex']);z=bytes.fromhex(v['new_hex']);assert z and b.count(z)==v['count'];b=b.replace(z,a,v['count'])
 assert b==baseline[rel]==subprocess.check_output(['git','show',H+':'+rel],cwd=R);put('inverse/'+rel,b);inverse.append(dict(path=rel,bytes=len(b),sha256=sha(b),whole_literal_inverse=True))
j('inverse-verification.json',dict(baseline=H,edits=6,files=inverse));put('history/exact-edits-and-inverse.json',(T/'exact-edits-and-inverse.json').read_bytes())
cpp='src/game/SharedTaiwanNativeSkillCommandSource.cpp';marker=b'            // Intended mutation consumes old grant/resources.'
assert current[cpp].split(marker,1)[1]==baseline[cpp].split(marker,1)[1],'postaction and release/create tail changed'
j('postaction-tail-exact.json',dict(marker=marker.decode(),unchanged_from_baseline=True,tail_bytes=len(current[cpp].split(marker,1)[1]),sha256=sha(current[cpp].split(marker,1)[1])))
spec=[('src/game/SharedTaiwanNativeSkillCommandSource.h',28,69),(cpp,44,95),(cpp,107,161),('src/db/NativeSkillCatalog.cpp',103,126),('src/game/SharedTaiwanIssuedSkillSource.cpp',344,365),('src/core/SharedTaiwanNativeWorldHostPlan.cpp',198,221),('src/db/SharedSkillDefinition.h',12,74)]
cuts=[]
for i,(rel,a,z) in enumerate(spec):
 ls=current[rel].splitlines(keepends=True);assert 0<a<=z<=len(ls);b=b''.join(ls[a-1:z]);dst=f'cuts/{i:02d}-{Path(rel).stem}-{a}-{z}.txt';put(dst,b)
 cuts.append(dict(actual_path=str(R/rel),retained=str(O/dst),bytes=len(b),sha256=sha(b),first_line=a,last_line=z,source_whole_sha256=sha(current[rel])))
j('cut-references.json',cuts)
report='''# I365 independent TW command common-definition source review

PASS_SOURCE_ONLY, stable actual two-file candidate. Fifteen current full references, baseline two and seven cuts separately listed; thirteen frozen suppliers remain exact committed 5a21cb97abb20c40080d4bf6be1a67cc4a071278. Six literal edits reverse both complete source files exactly to baseline. Upstream implementation, proposal and prior I364 verified per member with strict integer sums and containment. No tracked edits or product execution by reviewer.

Scope END appends owning optional common_definition{}, keeping original three-member aggregate and all four virtual callback signatures. Base capture retains actual presence/position/battle tuple. Original issued primary/secondary/actor/side, digest, image and whole TW record checks run before enrichment. Shared requested_native must exist and exactly equal that TW definition; selected CN common parameter base never replaces native TW command fields. After attach, definition_current rejects absent common, rechecks original digest/full row and requestedTW/full owning common equality. Same private scope reaches qualification, both current checks, action and after_action; no later re-enrichment/rebase. Existing callback observer pre/post checks, strong Session/owner lifetime and reentry invalidation remain.

Original native parsing/sequence/actor/side/formation limits, learned/controlled-actor/grant/MP/target/rules owner responsibilities, complete encrypted reply budgets and release behavior remain. Common metadata and client MP threshold are not server cost or native grant authority. Base_current is used only before enriched callback admission, never as an empty-common fallback to action.

Entire post-action comment/receipt/reply/ready(false)/after_action/release/create tail is byte-exact baseline. After real action this adapter does not query consumed old catalog/common/issued/grant Current. Same retained owning Scope is passed to actual next-receipt qualification. Publication failure cannot undo or retry durable prefix; exceptions retain original invalidation path. No new retry/rollback or fake success.

All observer cuts remain sequential, not SQLite/network atomic CAS or native ACK. The existing HostPlan requires actual common Context/catalog/presence/exclusive issued source and real WorldOwner, which is not fabricated or activated. Historical missing TW-native/custom rows remain missing; CN126/150 compatibility, learned/actor/list host, native formulas, acceptance and full bidirectional route remain separate. This is existing callback data handoff source integration, not their completion. Credits zero for those categories. No compiler/tests/runtime/native/API/SQL/resource decoder/codec/importer execution.
'''
put('REPORT.md',report.encode());put('capture_tw_command_review365.py',helper)
j('capture-receipt.json',dict(status='PASS_SOURCE_ONLY',successful_executions=1,current_whole_count=len(refs),current_whole_bytes=sum(v['bytes'] for v in refs),baseline_whole_count=len(base),cut_count=len(cuts),upstream_member_count=sum(v['member_count'] for v in verified),upstream_member_bytes=sum(v['member_bytes'] for v in verified)))
m=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  b=p.read_bytes();m.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
s=dict(status='PASS_SOURCE_ONLY',member_count=len(m),member_bytes=sum(v['bytes'] for v in m),members=m);j('seal.json',s)
for v in m:
 p=O/v['path'];assert p.resolve().is_relative_to(O.resolve());b=p.read_bytes();assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256']
assert json.loads((O/'seal.json').read_bytes())==s
print(json.dumps(dict(package=str(O),member_count=len(m),member_bytes=s['member_bytes'],seal_bytes=(O/'seal.json').stat().st_size,seal_sha256=sha((O/'seal.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
