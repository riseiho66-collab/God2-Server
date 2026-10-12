from pathlib import Path
import hashlib,json,subprocess
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012');D=A/'round351-blacklist-live-owner-host-implementation';S=Path('C:/Users/risei/Desktop/God2/God2-Server')
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,indent=2)+'\n').encode())
final=(S/'src/core/Application.cpp').read_bytes();initial=(D/'Application.before.cpp').read_bytes()
assert initial==subprocess.check_output(['git','show','7486b393c5e87a95f57c779d517e2b4727dcc663:src/core/Application.cpp'],cwd=S)
assert final==(D/'Application.reject-ready-corrected.cpp').read_bytes()
steps=[('exact-edits-and-inverse.json','before','after'),('pending-sender-correction.json','old','new'),('reject-ready-correction.json','old','new')]
v=final
for filename,oldkey,newkey in reversed(steps):
 r=json.loads((D/filename).read_bytes());assert len(v)==r['after_bytes'] and sha(v)==r['after_sha256']
 edits=r.get('edits',[r])
 for e in reversed(edits):
  old=e[oldkey].encode();new=e[newkey].encode();assert v.count(new)==1;v=v.replace(new,old,1)
 assert len(v)==r['before_bytes'] and sha(v)==r['before_sha256']
assert v==initial
put(D/'Application.final.cpp',final)
js(D/'final-source-manifest.json',dict(head='7486b393c5e87a95f57c779d517e2b4727dcc663',sources=[dict(path='src/core/Application.cpp',bytes=len(final),sha256=sha(final),before_bytes=len(initial),before_sha256=sha(initial))],composed_exact_inverse=True,untouched_source_bytes_preserved=True))
helpers=['implement-blacklist-host351.py','implement-blacklist-host351-mixed-newline-successor.py','implement-blacklist-host351-scoped-successor.py','correct-blacklist-pending-sender351.py','correct-blacklist-reject-ready351.py','seal-blacklist-host351.py']
for name in helpers:
 b=(A/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');put(D/'helpers'/name,b)
js(D/'failed-stage-summary.json',dict(failed_stages=[dict(helper=helpers[0],reason='Expected CRLF BlacklistReplay anchor occurs zero times in mixed-newline source',tracked_mutations=False),dict(helper=helpers[1],reason='Generic world_records wrapper anchor occurs twice; scope was ambiguous',tracked_mutations=False)],successor=helpers[2],prior_helpers_immutable=True,all_successful_stages_executed_once=True))
report='''# Actual blacklist live-owner host source351

Scope is one real Application wrapper using existing CUSTOM-0096 C89/C8A.
Actual committed A5 logical21 and A4 logical5 retain original CP950 identity.
Sender preserves native no-op replies and valid reject empty replies. Actual
typed before/after changes fan out only to exact same owner idle ready peers
whose own private normal-world handle and complete submitted snapshot match.
Strong peers, copied map values, delivery nodes and 21-byte buffers precede SQL.
Private owned before/after alias pointers do not allocate after COMMIT.
Submission exceptions revoke and close only an actual attempted delivery;
durable SQL is never retried or rolled back after delivery failure.

An actual pending incoming delta stops a competing sender operation before
SQL and retires/closes that connection. A previous pending peer delta cannot
chain a new mutation losslessly in this branch; that peer is retired/closed.
Queued progression requires exact pending/handle/snapshot identity and current
game-owner transport guard. Queued is FIFO insertion, never Written or ACK.
Pure stale/ineligible peers are disabled without closing. Sender or peer actual
before mismatch permanently disables live eligibility for that incarnation;
an accidental later database equality cannot revive it. Re-ready creates a new
actual replay source. Control runs revoke before old handlers; only actual
successful own Tick and private NormalInit/Written recapture output. Stop,
disconnect, re-ready and destructor ordering retire before borrowed owners.

The two initial source helper failures wrote no tracked source. Their immutable
code is retained; final scoped successor and corrections compose an exact byte
inverse to original350 HEAD. Pending-sender hazard and valid rejection findings
were corrected with separate candidate/inverse stages, never overwritten.
Seven aggregate C++ source files changed across host/core/Session packages.
No new gameplay rule, custom ID, opcode, format, parser or complete full route.
This is idle ready TW same-owner source integration, not all blacklist variants,
lossless pending chains, other contacts, native acceptance or whole-game100%.
PHASE1 source-only; no build/test/runtime/native/codec/gameDBSQL/deployment.
'''
put(D/'REPORT.md',report.encode())
members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
js(D/'seal.json',dict(members=members,member_count=len(members),member_bytes=sum(r['bytes'] for r in members)))
for r in members:
 b=(D/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
print(json.dumps(dict(members=len(members),member_bytes=sum(r['bytes'] for r in members),seal_sha256=sha((D/'seal.json').read_bytes()))))
