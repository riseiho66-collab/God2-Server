from pathlib import Path
import subprocess,json,hashlib
R=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
O=A/'round365-tw-command-common-definition-authority';H='5a21cb97abb20c40080d4bf6be1a67cc4a071278'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert not O.exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==H
files=['src/game/SharedTaiwanNativeSkillCommandSource.h','src/game/SharedTaiwanNativeSkillCommandSource.cpp','src/game/SharedTaiwanIssuedSkillSource.h','src/game/SharedTaiwanIssuedSkillSource.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/NativeSkillSource.h','src/protocol/TaiwanNativeSkillCommand.h','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/core/SharedWorldHostPlan.h','src/game/SharedTaiwanWorldRecordSource.h','src/game/SharedTaiwanWorldRecordSource.cpp']
raw={rel:subprocess.check_output(['git','show',H+':'+rel],cwd=R) for rel in files}
spec=[(files[0],27,66),(files[1],44,84),(files[1],101,145),(files[2],22,112),(files[3],344,365),(files[4],12,74),(files[7],103,126),(files[11],198,221)]
for rel,a,z in spec:assert 0<a<=z<=len(raw[rel].splitlines(keepends=True)),'preflight source line boundary'
helper=Path(__file__).read_bytes();assert not helper.startswith(b'\xef\xbb\xbf') and b'\r' not in helper and helper.endswith(b'\n') and not helper.endswith(b'\n\n')
def put(rel,b):
 p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
def j(rel,v):put(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
refs=[]
for rel,b in raw.items():
 dst='baseline/'+rel;put(dst,b);refs.append(dict(actual_path=str(R/rel),retained=str(O/dst),bytes=len(b),sha256=sha(b)))
j('source-references.json',refs)
cuts=[]
for i,(rel,a,z) in enumerate(spec):
 b=b''.join(raw[rel].splitlines(keepends=True)[a-1:z]);dst=f'cuts/{i:02d}-{Path(rel).stem}-{a}-{z}.txt';put(dst,b)
 cuts.append(dict(actual_path=str(R/rel),retained=str(O/dst),bytes=len(b),sha256=sha(b),first_line=a,last_line=z,source_head=H,source_whole_sha256=sha(raw[rel])))
j('cut-references.json',cuts)
j('source-custody.json',dict(head=H,source_state='all wholes/cuts committed baseline, NOT candidate current',whole_count=len(refs),whole_bytes=sum(v['bytes'] for v in refs),cut_count=len(cuts),cut_bytes=sum(v['bytes'] for v in cuts),working_two_observations=[dict(actual_path=str(R/p),bytes=len((R/p).read_bytes()),sha256=sha((R/p).read_bytes()),baseline_sha256=sha(raw[p])) for p in files[:2]]))
prior=A/'round364-cn-command-common-definition-independent-source-review';sb=(prior/'seal.json').read_bytes();ss=json.loads(sb)
assert sha(sb)=='b79479ff446c632bbc075faa659752291fe44a98042859421db76464596df168'
assert type(ss['member_count']) is int and ss['member_count']==len(ss['members'])==54
total=0;names=set()
for v in ss['members']:
 assert v['path'] not in names;names.add(v['path']);p=prior/v['path'];assert p.resolve().is_relative_to(prior.resolve());b=p.read_bytes()
 assert type(v['bytes']) is int and v['bytes']==len(b) and sha(b)==v['sha256'];total+=len(b)
assert type(ss['member_bytes']) is int and total==ss['member_bytes']==1916806
j('prior-individual-verification.json',dict(package=str(prior),seal_sha256=sha(sb),member_count=54,member_bytes=total,every_member_verified=True))
report='''# A365 TW command common-definition authority design

PASS_SOURCE_DESIGN. All fifteen whole source snapshots and eight exact cuts are immutable committed baseline 5a21cb97abb20c40080d4bf6be1a67cc4a071278; the two future modified sources are not captured as current candidates. No tracked source modification or product execution by this audit.

Actual existing dispatch captures owned requests and private Scope, then obtains actual issued primary/secondary selection and digest-checked original TW definition. Existing WorldOwner qualification/current/action/after_action all receive const Scope. Append owning optional SharedSkillDefinition common_definition{} at the Scope END, preserving virtual signatures and original three-member aggregate construction. Capture common via NativeSkillCatalog.lookup_shared_definition_main; requested_native MUST exist and match the complete digestchecked TW record and complete actual issued definition. Chosen common profile can be CN by owner policy but never replaces the requested TW native record or native grammar.

The initial base scope has no common value and is used only for original lease/epoch/position/native gates. Attach one privately owned common value before the first qualification callback. Every enriched preaction definition_current requires common present; it rechecks original digest/full TW row and freshly observed requestedTW plus whole common equality, preserving ready/reentry/issued fences around actual observers. Do not treat absent common as a compatibility bypass, re-enrich after observers, silently rebase the base epoch or use metadata equality to replace private actor/grant identity. Scope storage and original expected rows are owned across observations; callbacks remain const borrowed/nonyielding and may not retain arguments. Existing reentry invalidation and strong actual Session/owner lifetimes stay intact.

The existing qualification/current grammar still verifies issued BYTE actor/side, formation limits, full records/sequence and all actual WorldOwner learned/controlled-actor/grant/MP/targets/rules authority. The client MP threshold is not server charge. Definition presence and formal owner metadata grant nothing. Every preaction Current must see the same owning common material as action.

After actual action, pass exactly the retained Scope to after_action. Do NOT query old catalog, old common Current, consumed grant or old learned/resource snapshot after durable mutation. Existing actual next-receipt, ready(false), complete encrypted reply/envelope budgets and failclosed invalidation remain the contract. No rollback/retry of durable prefix. Observer/current observations are sequential, not cross-SQLite/network atomic CAS; no native ACK or fresh-client cache guarantee.

Actual HostPlan with_native_skills existing caller (209..221) requires common Context repository/presence/catalog, exclusive actual issued source and supplied real WorldOwner. This proposal strengthens the existing conditional callback handoff; it does not construct a missing concrete WorldOwner or activate Main. Historical TW native rows/image/grammar remain original; owner150 absence or unsupported original skill remains rejected by the native branch. Custom126/150 in both regions, CN adapter/host, full-route completion and native formulas remain separate authority work. No new source-policy grant, qualifier, fake native row, protocol field or unused Context pointer.

Next action: authorized two-file candidate implementation followed by independent review of base-versus-enriched checks, first callback provenance, callback windows, no-rebase full equality, and absence of postaction catalog queries. Full gameplay/source/native acceptance credits zero for this bounded design audit. Prior I364 every member verified in place. Phase1 only source text/git/hash/copy metadata, no build/compiler/test/runtime/native/API/SQL/import/codec/decoder.
'''
put('REPORT.md',report.encode());put('capture_tw_command_authority365.py',helper)
j('capture-receipt.json',dict(status='PASS_SOURCE_DESIGN',successful_executions=1,head=H,whole_count=len(refs),cut_count=len(cuts),source_mutations=0))
m=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  b=p.read_bytes();m.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
seal=dict(status='PASS_SOURCE_DESIGN',member_count=len(m),member_bytes=sum(v['bytes'] for v in m),members=m);j('seal.json',seal)
for v in m:
 p=O/v['path'];assert p.resolve().is_relative_to(O.resolve());b=p.read_bytes();assert type(v['bytes']) is int and len(b)==v['bytes'] and sha(b)==v['sha256']
assert json.loads((O/'seal.json').read_bytes())==seal
print(json.dumps(dict(package=str(O),member_count=len(m),member_bytes=seal['member_bytes'],seal_bytes=(O/'seal.json').stat().st_size,seal_sha256=sha((O/'seal.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
