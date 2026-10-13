from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
T = A / 'round358-party-courier-lifecycle-implementation'
HEAD = '81566a8a7efb75e7ea768bb5f767e1e5f1ad9324'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(rel, b):
    p = O / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def jout(rel, v):
    put(rel, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
prior = []
for name, seal_name, pin, count, total in [
    ('round357-party-callback-independent-source-review', 'SEAL.json', 'b71176941db5b8a405787865451797d2d6d5a1cd4628ddbea6dd6c7bc8bda5be', 56, 3849652),
    ('round358-party-courier-lifecycle-proposal', 'seal.json', 'b2b8cc897f6e5a17770ef7c1e650296415b2fb149c95c815c790f1900b4c0677', 52, 2189835),
]:
    p = A / name
    raw = (p / seal_name).read_bytes()
    assert sha(raw) == pin
    seal = json.loads(raw)
    assert seal['member_count'] == len(seal['members']) == count
    assert seal['member_bytes'] == sum(m['bytes'] for m in seal['members']) == total
    for m in seal['members']:
        b = (p / m['path']).read_bytes()
        assert len(b) == m['bytes'] and sha(b) == m['sha256']
    put('upstream/' + name + '-seal.json', raw)
    prior.append(dict(root=p.as_posix(), seal_sha256=pin, member_count=count, member_bytes=total,
                     members=seal['members'], verified_in_place=True))
# T seal is captured only after root/independent semantic freeze. Every member
# and integer accounting is independently read back; source pins are below.
raw = (T / 'seal.json').read_bytes()
assert sha(raw) == '16607d3e71488e9abfd58506c64c85ec1d4b96ed1803683eab8a1ada2d552a33'
seal = json.loads(raw)
assert seal['member_count'] == len(seal['members']) == 21
assert seal['member_bytes'] == sum(m['bytes'] for m in seal['members']) == 3018178
for m in seal['members']:
    b = (T / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
put('upstream/round358-party-courier-lifecycle-implementation-seal.json', raw)
prior.append(dict(root=T.as_posix(), seal_sha256=sha(raw), member_count=seal['member_count'],
    member_bytes=seal['member_bytes'], members=seal['members'], verified_in_place=True))
jout('upstream-individual-verification.json', prior)

pins = {
    'src/core/Application.cpp': (725471, '0c04d4fe669dc5ec0037e1232482954297f079c5f88cbcfa6cf03d0ac98a753c'),
    'src/game/OwnedPartyPreviewTransport.h': (11345, '5bf2245a69e7a17fdb24c9ec5eef3fcae36fec192984ac33e7d10fdbb90fa6f8'),
}
refs, current, baseline = [], {}, {}
for rel, (size, digest) in pins.items():
    b = (S / rel).read_bytes()
    assert len(b) == size and sha(b) == digest
    assert b == (T / 'candidate' / rel).read_bytes()
    current[rel] = b
    for folder, raw, state in [
        ('current', b, 'frozen final candidate; deliberately differs from immutable published HEAD'),
        ('baseline', subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S), 'immutable published HEAD source'),
    ]:
        if folder == 'baseline':
            baseline[rel] = raw
            assert raw == (T / 'before' / rel).read_bytes()
        retained = folder + '/' + rel
        put(retained, raw)
        refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(raw),
            sha256=sha(raw), source_head=HEAD, source_state=state))
frozen = ['src/net/Session.h', 'src/net/Session.cpp', 'src/game/OwnedPartyDirectory.h',
    'src/handlers/OwnedPartyDirectoryService.h', 'src/game/NativeParty.h', 'src/core/Config.h',
    'docs/custom-designs.json', 'src/core/Scheduler.h', 'src/core/Scheduler.cpp',
    'src/net/TcpServer.cpp', 'src/net/IoContextPool.cpp']
for rel in frozen:
    b = (S / rel).read_bytes()
    assert b == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    retained = 'frozen/' + rel
    put(retained, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b),
        sha256=sha(b), source_head=HEAD, source_state='unchanged published HEAD full source'))
jout('source-references.json', refs)
rb = (T / 'apply-receipt.json').read_bytes()
receipt = json.loads(rb)
put('apply-receipt.json', rb)
work = current.copy()
for e in reversed(receipt['edits']):
    rel = e['source']
    old, new = bytes.fromhex(e['before_hex']), bytes.fromhex(e['after_hex'])
    assert work[rel].count(new) == e.get('multiplicity', 1)
    work[rel] = work[rel].replace(new, old)
assert len(receipt['edits']) == 3
for rel in pins:
    assert work[rel] == baseline[rel]
    assert (S / rel).read_bytes() == current[rel]
jout('two-complete-byte-inverses.json', dict(head=HEAD, edit_count=3, inverse_equal=True,
    files=[dict(source=r, before_bytes=len(baseline[r]), before_sha256=sha(baseline[r]),
        final_bytes=len(current[r]), final_sha256=sha(current[r])) for r in pins]))
specs = [('src/core/Application.cpp', 2325, 2341), ('src/core/Application.cpp', 7148, 7154),
    ('src/game/OwnedPartyPreviewTransport.h', 42, 77), ('src/game/OwnedPartyPreviewTransport.h', 79, 118),
    ('src/game/OwnedPartyPreviewTransport.h', 168, 209), ('src/net/Session.cpp', 2534, 2567),
    ('src/net/Session.cpp', 3662, 3666), ('src/core/Scheduler.cpp', 1, 15)]
cuts = []
for i, (rel, lo, hi) in enumerate(specs):
    raw = current.get(rel, (S / rel).read_bytes())
    lines = raw.splitlines(keepends=True)
    assert 1 <= lo <= hi <= len(lines)
    b = b''.join(lines[lo - 1:hi])
    retained = 'cuts/%02d-%s-L%d-L%d.txt' % (i, Path(rel).name, lo, hi)
    put(retained, b)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, first_line=lo, last_line=hi,
                     bytes=len(b), sha256=sha(b), boundary='selected excerpt; whole containing source retained'))
jout('source-cuts.json', cuts)
put('REPORT.md', b'''# Round358 independent actual party courier lifecycle review

PASS for exactly two existing current sources; three inserted source deltas independently reverse to whole published81566a8a7efb75e7ea768bb5f767e1e5f1ad9324. Fifteen standard whole references are current2/baseline2/frozen11; eight bounded cuts retain method/hook context. Prior I357, P358 and final T358 seals each had all individual members and integer byte accounting verified in place. Current Application intentionally differs from immutable authority snapshots. No tracked edits, target/API/SQL/native/compiler/test execution occurred.

retire_source requires the actual State game thread before registry access and returns when stopped. Matching is exact strong source peer.get()==&source, never IDs or successor lookup. It holds the shared Flight, invokes existing retire(committed), decrements the exact node source count and erases once. Session::close synchronously retires output and sets close_requested then posts to strand; it does not invoke on_disconnect inline. Thus existing contained close handling does not reenter the game list scan under the source premise. The scan itself introduces no allocation or source callback; existing close may allocate its post and already catches that exception in Flight::retire. No blanket no-allocation or executor convergence guarantee is claimed.

Uncommitted retirement revokes only fresh handles, current becomes false before actual preCAS fence, and later Prepared destruction finds no list node so cannot double-decrement or close peers. Committed deferred/partially submitted flights retire exact held sources, preserving already-queued partial reality without rollback/retry. AllQueued successful flights already lack a node, so later retirement cannot revoke their queued Write Data. Stop/Scheduler/private admission semantics remain byte-identical outside the three insertions.

Application invokes the new method as the first actual on_disconnect statement and first actual Directory world_ready wrapper statement before local throwing observers; feature pointer-null preserves default-off behavior. Actual hooks delivered is the limit: Session::finish posts a job whose logger/common cleanup can throw before Application on_disconnect, and dropped posts/general context convergence remain OPEN. The actual ready receipt still retires old INIT; no new Written INIT, native ACK, consent/allvariants, issuer/full50 or complete route is inferred. Runtime acceptance is unexecuted. Owner formula priority resumes after this finite source review.
''')
jout('capture-complete.json', dict(status='PASS', source_head=HEAD, whole_count=len(refs), cut_count=len(cuts),
    inverse_files=2, edits=3, upstream_packages=len(prior), upstream_members=sum(p['member_count'] for p in prior),
    upstream_bytes=sum(p['member_bytes'] for p in prior), source_semantic_verdict='PASS', authority_credit=0))
members = []
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name != 'SEAL.json':
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
total = sum(m['bytes'] for m in members)
assert isinstance(total, int)
jout('SEAL.json', dict(status='PASS', member_count=len(members), member_bytes=total, members=members))
for m in members:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
sb, hb = (O / 'SEAL.json').read_bytes(), Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(status='PASS', member_count=len(members), member_bytes=total,
    seal_bytes=len(sb), seal_sha256=sha(sb), helper_bytes=len(hb), helper_sha256=sha(hb))))
