from pathlib import Path
import hashlib,json,subprocess
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round352-blacklist-submitted-chain-host-implementation';S=Path('C:/Users/risei/Desktop/God2/God2-Server')
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,indent=2)+'\n').encode())
head='31d79bad16484d0a2021a938cb1a99b58231ba14';final=(S/'src/core/Application.cpp').read_bytes();initial=(D/'Application.before.cpp').read_bytes()
assert initial==subprocess.check_output(['git','show',head+':src/core/Application.cpp'],cwd=S)
assert final==(D/'Application.callback-qualified.cpp').read_bytes() and len(final)==713375 and sha(final)=='6fc65b1edb323a8ac423958447af61ef2db2b4b1a4f0e980cc22ce8f42e3e896'
v=final
for filename in reversed(['exact-edits-and-inverse.json','callback-qualification-correction.json']):
 r=json.loads((D/filename).read_bytes());assert len(v)==r['after_bytes'] and sha(v)==r['after_sha256']
 for e in reversed(r['edits']):
  old=e['old'].encode();new=e['new'].encode();assert v.count(new)==1;v=v.replace(new,old,1)
 assert len(v)==r['before_bytes'] and sha(v)==r['before_sha256']
assert v==initial
stable=['src/db/SqliteOwnedBlacklistRepository.cpp','src/db/SqliteOwnedBlacklistRepository.h','src/handlers/OwnedBlacklistService.cpp','src/handlers/OwnedBlacklistService.h','src/net/Session.cpp','src/net/Session.h'];rows=[]
for rel in stable:
 b=(S/rel).read_bytes();assert b==subprocess.check_output(['git','show',head+':'+rel],cwd=S);rows.append(dict(path=rel,bytes=len(b),sha256=sha(b),unchanged=True))
put(D/'Application.final.cpp',final)
js(D/'final-source-manifest.json',dict(head=head,sources=[dict(path='src/core/Application.cpp',bytes=len(final),sha256=sha(final),before_bytes=len(initial),before_sha256=sha(initial))],composed_exact_inverse=True,untouched_source_bytes_preserved=True,frozen_related_Cplusplus=rows,independent_early_review='Conditional static PASS, full outer failure and native adoption remain open'))
for name in ['implement-blacklist-submitted-chain352.py','qualify-blacklist-chain-callback352.py','seal-blacklist-submitted-chain352.py']:
 b=(A/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');put(D/'helpers'/name,b)
put(D/'REPORT.md',b'''# Actual bounded blacklist ordered-submitted chain source352

One existing Application file changes. Prior six core/Session files are exact.
Actual peer Pending A5/A4 attempts may chain in successful single-game-thread
post order to the same concrete Session strand. Only actual attempt nodes are
retained, at most256 matching existing local transport max_writes. Each node
owns one preallocated21B buffer, handle, prior link and status; no per-node
complete snapshots or fictitious original-reply Queued nodes. Latest map
snapshot is the immutable actual core after of ordered submission, not FIFO
insertion, socket Written, native adoption or ACK. All Queued clears attempts
without advancing/rewinding that endpoint. Current checks are pure.

An actual sender with prior incoming Pending is qualified by its own private
NormalWorldInitialization/TLS and matching chain before SQL. Its original A5/A4
is appended before source endpoint advances. A copied facade cannot mint live
progress; its no-chain legacy reply remains. Strong peers/nodes/buffers precede
SQL; no retry or rollback after durable commit. Valid no-op/rejection semantics
remain. Cap/no-node rejection closes only an actual pending chain after a real
changed edge would be skipped, never merely because an unchanged no-op arrives.
Failures retire affected actual chains; control/transfer paths remain bounded.

Four conditional state variants: peer priorPending A5/A4 and sender priorIncoming
Pending A5/A4. No opcode/format/parser/handler/phase/native-method/full-route
credit. Outer callback rejection, final response validation, terminal post or
context abort do not attest own Queued or universal convergence. All variants,
transfer/postbattle and native adoption remain OPEN. Default opt-in stays off.
Two successful source stages compose an exact inverse to351 HEAD. PHASE1 static
only: no compiler/build/test/runtime/native/codec/gameDBSQL/activation/deploy.
''')
members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
js(D/'seal.json',dict(members=members,member_count=len(members),member_bytes=sum(r['bytes'] for r in members)))
for r in members:
 b=(D/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
print(json.dumps(dict(members=len(members),member_bytes=sum(r['bytes'] for r in members),seal_sha256=sha((D/'seal.json').read_bytes()))))
