from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
I=A/'round354-client-options-original-response-implementation';O=A/'round354-client-options-independent-source-review'
HEAD='b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,indent=2)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()==HEAD
edits=json.loads((I/'exact-edits-and-inverse.json').read_bytes());assert len(edits)==2
refs=[];inverse=[];whole={}
for r in edits:
    p=r['path'];current=(S/p).read_bytes();before=(I/'before'/p).read_bytes()
    assert current==(I/'candidate'/p).read_bytes()
    assert len(current)==r['after_bytes'] and sha(current)==r['after_sha256']
    assert len(before)==r['before_bytes'] and sha(before)==r['before_sha256']
    assert before==subprocess.check_output(['git','show',HEAD+':'+p],cwd=S)
    restored=current
    for e in reversed(r['edits']):
        new=e['new'].encode();old=e['old'].encode();n=e.get('count',1)
        assert restored.count(new)==n;restored=restored.replace(new,old,n)
    assert restored==before
    put(O/'current'/p,current);put(O/'baseline'/p,before);whole[p]=current
    refs.append(dict(actual_path=(S/p).as_posix(),retained=(Path('current')/p).as_posix(),bytes=len(current),sha256=sha(current),baseline_revision=HEAD,current_candidate=True))
    inverse.append(dict(path=p,before_bytes=len(before),before_sha256=sha(before),current_bytes=len(current),current_sha256=sha(current),whole_inverse_exact=True))
for p in ['src/core/Config.h','src/protocol/TaiwanNativeClientOptions.h','src/protocol/RecoveredWorldRecords.h']:
    b=(S/p).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+p],cwd=S)
    put(O/'current'/p,b);whole[p]=b
    refs.append(dict(actual_path=(S/p).as_posix(),retained=(Path('current')/p).as_posix(),bytes=len(b),sha256=sha(b),baseline_revision=HEAD,frozen_dependency=True))
assert b'owned_client_options_enabled=false' in whole['src/core/Config.h']
js(O/'source-references.json',refs);js(O/'whole-source-inverse-verification.json',inverse)
for name in ['exact-edits-and-inverse.json','candidate-source-invariants.md','failure-draft00.txt']:
    put(O/'implementation-candidate-custody'/name,(I/name).read_bytes())
session_pins={'src/net/Session.h':'74af3bbc1146f2c21f99a3768a662c94748ab514f74592655a829e9c31bc5f2e','src/net/Session.cpp':'b29b89402bd5710dc8ce05298d943f2abacfe6df1c6fc480cdbfb3b14613aba3'}
prior=A/'round353-original-response-independent-source-review';dependencies=[]
for p,h in session_pins.items():
    b=(S/p).read_bytes();assert sha(b)==h and b==(prior/'final'/p).read_bytes()
    assert b==subprocess.check_output(['git','show',HEAD+':'+p],cwd=S)
    whole[p]=b;dependencies.append(dict(actual_path=(S/p).as_posix(),bytes=len(b),sha256=h,retained_prior=(prior/'final'/p).as_posix(),prior_seal_sha256=sha((prior/'SEAL.json').read_bytes()),unchanged_353_hooks=True))
js(O/'unchanged-session353-hook-dependencies.json',dependencies)
cuts=[('src/core/Application.cpp',7410,7529,'complete-options-wrapper-selected-source'),('src/core/Application.cpp',2324,2330,'existing-options-disconnect-retirement'),('src/game/OwnedClientOptions.h',1,49,'complete-transient-state-owner'),('src/net/Session.cpp',331,351,'existing-private-RAII-pending-owner'),('src/net/Session.cpp',2704,2761,'complete-existing-capture-expect-current-hooks')]
cutrows=[]
for p,lo,hi,name in cuts:
    b=whole[p];lines=b.splitlines(keepends=True)
    if p=='src/game/OwnedClientOptions.h':hi=len(lines)
    assert 1<=lo<=hi<=len(lines)
    cut=b''.join(lines[lo-1:hi]);dest=O/'cuts'/(name+'.source');put(dest,cut)
    cutrows.append(dict(actual_source=p,first_line=lo,last_line=hi,retained=dest.relative_to(O).as_posix(),bytes=len(cut),sha256=sha(cut)))
js(O/'exact-source-cuts.json',cutrows)
js(O/'review-manifest.json',dict(verdict='PASS bounded independent two-file source review354',blocking_findings=[],baseline_head=HEAD,changed_sources=2,frozen_full_dependencies=3,unchanged_session353_dependencies=2,full_inverse_exact=True,authorization='Root stablePASS after c28/root/independent earlyPASS',helper_failures=[],helper='capture_options_review354.py',successful_helper_runs=1,tracked_edits=0,product_API_SQL_native_parser_codec_compiler_tests_runtime_executions=0))
put(O/'REPORT.md',b'''# Round354 independent client-options source review

PASS for the stable two-file candidate, without a consequential blocker.
Application719603/5487086c and OwnedClientOptions2243/fd9ffef9 are retained whole.
Exact whole-byte inverses restore published b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650.
Config, projection and parser remain exact; Session353 private hooks remain
74af3/b29b and equal their independently reviewed retained sources.

Actual synchronize gets own callback INIT before game fields and requires its
Written entry. New current includes exact private callback Data, unchanged
account/character/phase/battle, readiness and reentry fence. Previous snapshot
is owning immutable state, so previous Entry survives observations. Failed old
response refuses publication; Pending accepts only the same actual callback
Data. Queued old known WORD may cross a genuinely new/current Written INIT for
the same Session/account/character, without treating obsolete INIT as current
or FIFO Queued as Written/ACK. Replay does not fabricate an initial zero.

Owning next state, actual original S1B frame and merged bytes are prepared
before exact component registration. expect precedes both CAS state publish
and prepared wire.swap. Guards surround registration/publish. If an armed
component cannot reach final response, existing353 matching/final private guard
fails closed, retires epoch and requests close. Registration can allocate and
poison; no SQL mutation/retry/rollback is introduced. Later delegated reject,
phase/battle/epoch change or final response/post/drop failure is explicitly
authorized fail-closed behavior, not accepted mixed transfer authority.

Multiple option records and inner blacklist callbacks reuse the same actual
callback Data. Options ready/disconnect copy/remove public receipt references
without changing private status or epoch; retaining public Data cannot suppress
Session353 RAII failure. No sender TLS receipt is minted for another peer.
Caught reentry poisons rather than allowing an accepting publication.

Existing opaque C1D WORD, selector7/8 bit0200, revision/replay formula and S1B
bytes remain unchanged. CUSTOM0100 is default off, transient/untrusted and
grants no permission/chat/combat/game rule. No native ACK/adoption/full-route
credit follows. General undestroyed-context abort and all transfer/postbattle
variants stay OPEN. Empty/unarmed legacy paths retain existing behavior.

Source-only review: no tracked changes, target/API/SQL/native/parser/codec/
compiler/build/tests/runtime execution. Successful LF custody helper ran once.
Writer's failed prewrite draft is retained as historical custody; not rerun.
''')
for r in refs:assert (O/r['retained']).read_bytes()==Path(r['actual_path']).read_bytes()
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
js(O/'SEAL.json',dict(verdict='PASS bounded independent options source review354',baseline_head=HEAD,member_count=len(members),member_bytes=sum(r['bytes'] for r in members),members=members))
for r in json.loads((O/'SEAL.json').read_bytes())['members']:
    b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
helper=(O/'capture_options_review354.py').read_bytes();assert b'\r' not in helper
print(json.dumps(dict(members=len(members),bytes=sum(r['bytes'] for r in members),seal_bytes=(O/'SEAL.json').stat().st_size,seal_sha256=sha((O/'SEAL.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
