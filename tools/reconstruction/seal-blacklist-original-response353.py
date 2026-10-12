from pathlib import Path
import hashlib,json,subprocess
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round353-blacklist-original-response-host-implementation';S=Path('C:/Users/risei/Desktop/God2/God2-Server');sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,indent=2)+'\n').encode())
head='618eb9cbce52632f984b45f7409407a4e465c234';final=(S/'src/core/Application.cpp').read_bytes();initial=(D/'Application.before.cpp').read_bytes();receipt=json.loads((D/'exact-edits-and-inverse.json').read_bytes())
assert initial==subprocess.check_output(['git','show',head+':src/core/Application.cpp'],cwd=S);assert final==(D/'Application.candidate.cpp').read_bytes() and len(final)==718069 and sha(final)=='37e0c23b637fceda704ca1719bd37eb0f07f8a9e8758188b6eed64ade5d0351c';v=final
for e in reversed(receipt['edits']):
 old=e['old'].encode();new=e['new'].encode();assert v.count(new)==1;v=v.replace(new,old,1)
assert v==initial
rows=[]
for rel in ['src/db/SqliteOwnedBlacklistRepository.cpp','src/db/SqliteOwnedBlacklistRepository.h','src/handlers/OwnedBlacklistService.cpp','src/handlers/OwnedBlacklistService.h']:
 b=(S/rel).read_bytes();assert b==subprocess.check_output(['git','show',head+':'+rel],cwd=S);rows.append(dict(path=rel,bytes=len(b),sha256=sha(b),unchanged=True))
put(D/'Application.final.cpp',final)
js(D/'final-source-manifest.json',dict(head=head,sources=[dict(path='src/core/Application.cpp',bytes=len(final),sha256=sha(final),before_bytes=len(initial),before_sha256=sha(initial))],exact_inverse=True,untouched_source_bytes_preserved=True,frozen_core_Cplusplus=rows,independent_early_review='PASS bounded current3Cplusplus, no native adoption or allvariants'))
for name in ['implement-blacklist-original-response353.py','seal-blacklist-original-response353.py']:
 b=(A/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');put(D/'helpers'/name,b)
put(D/'REPORT.md',b'''# Actual blacklist original-response host custody353

One existing Application changes; unchanged four core repository/service files.
Actual own NormalINIT callback captures independent private response Data before
SQL/replay observation. Split runs reuse same callback Data; a previous Pending
own endpoint cannot be overwritten with a different callback. Map Current first
checks own response even with no peer nodes. Peer copies/refind fences retain
exact own receipt identity; settle clears only peer nodes, not newest endpoint.

Actual appended framed A5/A4 bytes (including no-op) register before owning the
ticket/advancing changed snapshot/fanout. Nonempty tombstone/active replay bytes
register before cursor/snapshot/done advances. Session alone marks actual final
valid response FIFO Queued; provisional endpoint is not Written or client ACK.
Rejected empty replies leave reservation unarmed and continue old semantics.
Missing own INIT/copied facade keeps historical reply behavior without claiming
new custody or live progression. Initial replay without capture is historical,
not credited. Control/re-ready/stop retire pending own source with peer nodes.

Four bounded custody source branches: committed A5 add/A4 remove and nonempty
initial tombstone/active replay. Existing profile/CUSTOM0096/default-off/names/
native bytes/limits unchanged. No SQL retry/rollback or native-method/opcode/
format/parser/handler/phase/full-route credit. Component allocation can fail
after COMMIT; receipt failure retires before live progress, not fake rollback.
Specific armed final-post failure/drop is observed; unrelated context abort,
all control/transfer variants, socket Written and native adoption remain OPEN.
Exact inverse to352 HEAD, PHASE1 no build/test/runtime/native/parser/codec/SQL.
''')
members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
js(D/'seal.json',dict(members=members,member_count=len(members),member_bytes=sum(r['bytes'] for r in members)))
for r in members:
 b=(D/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
print(json.dumps(dict(members=len(members),member_bytes=sum(r['bytes'] for r in members),seal_sha256=sha((D/'seal.json').read_bytes()))))
