from pathlib import Path
import hashlib
import json
import subprocess

S=Path('C:/Users/risei/Desktop/God2/God2-Server')
O=Path(__file__).resolve().parent
HEAD='566923291db5de40dcc7d1a153cde60cfc94d87c'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(r,b):
    p=O/r;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(r,v):put(r,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
I=O.parent/'round362-owned-skill-bootstrap-independent-source-review'
sb=(I/'SEAL.json').read_bytes();v=json.loads(sb)
assert sha(sb)=='b144687f8bbbf98b631f04175a4e83a22979bdbe8b253513906db8e96d882e69'
assert v['member_count']==len(v['members'])==48 and type(v['member_bytes']) is int
assert v['member_bytes']==sum(m['bytes'] for m in v['members'])==2975179
for m in v['members']:
    p=I/m['path'];assert p.resolve().is_relative_to(I.resolve())
    b=p.read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
js('prior-individual-verification.json',dict(root=I.as_posix(),member_count=48,member_bytes=2975179,
    seal_sha256=sha(sb),members=v['members']))
files=['src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp',
    'src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp']
refs=[];data={}
for rel in files:
    b=subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S);data[rel]=b
    retained='published/'+rel;put(retained,b)
    refs.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        source_head=HEAD,source_state='immutable published source; not implementation'))
js('source-references.json',refs)
specs=[('src/net/Session.h',108,125),('src/net/Session.cpp',146,157),
    ('src/net/Session.cpp',330,343),('src/net/Session.cpp',1072,1104),
    ('src/net/Session.cpp',1948,1989),('src/net/Session.cpp',2138,2157),
    ('src/net/Session.cpp',2232,2329),('src/net/Session.cpp',2404,2422),
    ('src/net/Session.cpp',2481,2555),('src/net/Session.cpp',2633,2670)]
cuts=[]
for i,(rel,a,z) in enumerate(specs):
    lines=data[rel].splitlines(keepends=True);assert 1<=a<=z<=len(lines)
    b=b''.join(lines[a-1:z]);retained='cuts/%02d-%s-L%d-L%d.txt'%(i,Path(rel).name,a,z)
    put(retained,b);cuts.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        source_head=HEAD,first_line=a,last_line=z,boundary='selected excerpt; complete source retained'))
js('source-cuts.json',cuts)
js('typed-proposal.json',dict(status='READONLY_CUSTOM0141_PROPOSAL_NOT_IMPLEMENTED',
    files=['src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp'],
    actual_arm='after successful actual App final qualify_owned_bootstrap, same TLS callback and same Impl capture private receipt',
    hold_owner='one exact WorldResponseAttempt, not arbitrary retained Data/Pending status',
    pause=['read','resume_world_input','feed_world after bounded append before parser/staging'],
    success='actual full FIFO frame/attempt/transferred identity Written, old completion bookkeeping/pop succeeds, clear exact hold then original resume once',
    failure='armed Pending failure/post-drop/stale/close/exception retire hold and failclose; no successor resume/durable retry',
    same_batch='already parsed Timer36+C35 batch cannot be retroactively split',
    limits='existing input16384/write max_buffer/max_writes/record8192/timeouts unchanged; unavailable executor convergence OPEN',
    native_ACK=False,native_turn_grant=False,SQL_network_atomic=False,tracked_changes=False))
put('REPORT.md',b'''# Round363 owned bootstrap input continuation design

Readonly source proposal at published566923291db5de40dcc7d1a153cde60cfc94d87c. Five complete sources and ten selected excerpts retain the actual input/parser/game-handoff/FIFO/write/retirement chain; prior I36248/2975179 each member is verified unchanged. Static source/hash/git only. No implementation, tracked edit, product API, SQL, runtime/native/CRT/VM/parser/codec/compiler/build/tests.

Actual gap: accepted world callback enqueues its response and immediately calls resume_world_input before async_write can mark the passive WorldResponseWrite Written. The parser preserves one complete ordinary frame per operation; remaining TCP bytes remain world_input. Round362's custom owned command Written prerequisite can therefore reject a genuine early next frame. This does not imply native client list adoption or turn timing. Already parsed Timer36+C35 within the same native frame/batch cannot be split retroactively; old batch policy stays.

Minimal supported source scope is Session.h/.cpp plus the existing App callsite. After actual typed bootstrap qualifier succeeds, a new owner-specific arm operation validates actual own TLS/game-thread, Pending/current receipt, Impl current callback capture receipt identity, exact phase/battle and no duplicate arm. It marks only that exact privately captured Attempt; a public copy of old Pending Data cannot arm another callback. This is explicit CUSTOM-0141 source policy, not a native ACK/grant or a generic input barrier.

The accepted strand handoff validates the SAME full returned response and original queue budget, installs one exact active Attempt before starting write, and suppresses ordinary input continuation. Guard read and resume_world_input; feed_world appends only under the existing16384 bound, then returns before moving pending records/decoding/staging when held. Preserve all buffered suffix/in-flight bytes/order and original frame/8192-record/skill-sequence limits. No discard, replay-from-beginning, parser split, cancellation/reclassification or fake empty reset is needed. Native PK/other publication overlap or successor phase must fail the opted source rather than adopt it; unopted paths retain their existing priorities/behavior.

Only actual target FIFO-front frame/Attempt/receipt/wire/session/transferred identity and Written CAS can satisfy the hold. Do not resume at that early CAS: old completion observers/logging/bookkeeping/pop/next-write scheduling must first succeed. Then clear the exact active hold before invoking original resume_world_input once. Queued or game callback acceptance is insufficient. Preserve Written as the real passive local fact if later completion fails; the failed continuation is a separate hold state, not demotion of a successful physical write.

Close/fail/drop/post failure must retire exact armed state without taking any game callback/SQL on strand or reading bare game-owned account/character there. Use the private captured immutable tuple and transport-safe phase/battle/close/session checks. Arm source proves the IDs on game; stale phase/epoch/Session must never unblock a successor. Armed Attempt Pending failure/destruction should atomically mark close_requested even if game-to-strand post throws/drops before hold installation. Live strand boundaries failclose/retire; unavailable executor/general shutdown convergence remains OPEN, not fabricated cleanup. Clear installed hold before finish bookkeeping and keep game_busy false during a transport hold so real disconnect can drain.

Completion exceptions while an opted hold exists, including an older FIFO prefix's throwing work, require opted containment/failclose to avoid a permanent pause. No exception-policy change for unarmed passive writes. No locks around logger/source callback/SQL/write/close; strand-owned pointer needs no model callback. Existing bounded queue and timeouts remain, with no invented native deadline. Any already committed action/resources prefix cannot be reversed or retried due to later transport failure.

Existing saved learned readset, common owner rules,361 atomic checkpoint and362 actual advertised keys remain mandatory and unchanged. The barrier only ensures that the original input continuation observes the real local bootstrap write, without manufacturing full primary list/control/actor/grant/MP/nativeCN453 or client acceptance. Root must authorize code scope after baseline. Native method/format/opcode/formula/fullroute credits remain0.
''')
js('capture-complete.json',dict(status='PASS_BOUNDED_READONLY_PROPOSAL',source_head=HEAD,
    whole_count=len(refs),cut_count=len(cuts),prior_members=48,prior_bytes=2975179,
    tracked_edits=False,target_execution=False,native_route_credit=0))
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='SEAL.json':
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
total=sum(m['bytes'] for m in members);assert type(total) is int
js('SEAL.json',dict(status='PASS_BOUNDED_READONLY_PROPOSAL',member_count=len(members),member_bytes=total,members=members))
for m in members:
    b=(O/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
sb=(O/'SEAL.json').read_bytes();hb=Path(__file__).read_bytes()
assert b'\r' not in hb and hb.endswith(b'\n') and not hb.endswith(b'\n\n')
print(json.dumps(dict(member_count=len(members),member_bytes=total,seal_bytes=len(sb),seal_sha256=sha(sb),
    helper_bytes=len(hb),helper_sha256=sha(hb))))
