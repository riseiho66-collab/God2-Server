from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
T = A / 'round357-party-callback-admission-implementation'
HEAD = 'b5a2afd1364c50613525f07757ba31350dad9882'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(r, b):
    p = O / r
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        assert p.read_bytes() == b, ('immutable partial differs', r)
        return
    with p.open('xb') as f:
        f.write(b)

def jout(r, v):
    put(r, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

prior_results = []
for name, digest, count, total in [
    ('round356-party-preview-independent-source-review', '6eafc9830845d169d954f41bc8bfd62a2af9740e27407099447282051d1ef638', 39, 2722597),
    ('round357-party-callback-admission-proposal', 'e746c86ede71552b9c44e5da1a0bd697d18c085a0dc165884cc787dece8f5364', 27, 1140439),
    ('round357-party-callback-admission-implementation', '2a8b77b2c36088a03fdc3fe882df4234c382214c7a4323bf65d34354a555a43b', 57, 6997333),
]:
    p = A / name
    b = (p / ('seal.json' if name.endswith('implementation') else 'SEAL.json')).read_bytes()
    assert sha(b) == digest
    seal = json.loads(b)
    assert seal['member_count'] == len(seal['members']) == count
    assert seal['member_bytes'] == sum(m['bytes'] for m in seal['members']) == total
    for m in seal['members']:
        raw = (p / m['path']).read_bytes()
        assert len(raw) == m['bytes'] and sha(raw) == m['sha256']
    put('upstream/' + name + '-SEAL.json', b)
    prior_results.append(dict(root=p.as_posix(), seal_sha256=digest, member_count=count,
                              member_bytes=total, members=seal['members'], verified_in_place=True))
jout('upstream-individual-verification.json', prior_results)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
pins = {
    'src/net/Session.h': (35537, '05bd0d1379bd0a48eadf4e1bf83ec7f449059b3d7fc45721b8d3223d63b1005f'),
    'src/net/Session.cpp': (240949, '79fc55816b9f69829202a9be7191348e2b845a6c6f7cd7f964c1ce0f9c167faf'),
    'src/core/Application.cpp': (725214, 'ae0cbcdbc4c3f3288efca12e43b3f66206cbb89e0147495752571bd3eb9a2cfc'),
    'src/game/OwnedPartyPreviewTransport.h': (10563, '606419a2c03507644b4de3815818a86b7712b66c987f8cb220b5c8209b069b4b'),
}
refs, current, baseline = [], {}, {}
def capture(rel, retained, b, state):
    put(retained, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained,
                     bytes=len(b), sha256=sha(b), source_state=state, source_head=HEAD))

for rel, (size, digest) in pins.items():
    b = (S / rel).read_bytes()
    assert len(b) == size and sha(b) == digest
    current[rel] = b
    capture(rel, 'current/' + rel, b, 'final current candidate; deliberately differs from immutable HEAD')
    b = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    assert b == (T / 'before' / rel).read_bytes()
    baseline[rel] = b
    capture(rel, 'baseline/' + rel, b, 'immutable published HEAD whole source')
    put('historical-early/' + rel, (T / 'candidate' / rel).read_bytes())

frozen = ['src/game/OwnedPartyDirectory.h', 'src/handlers/OwnedPartyDirectoryService.h',
          'src/game/NativeParty.h', 'src/core/Config.h', 'docs/custom-designs.json',
          'src/protocol/RecoveredParty.h', 'src/protocol/TaiwanNativePartyMenu.h',
          'src/protocol/RecoveredWorldFrame.h', 'src/protocol/RecoveredWorldEntryView.h',
          'src/core/Scheduler.h', 'src/core/Scheduler.cpp']
for rel in frozen:
    b = (S / rel).read_bytes()
    assert b == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    assert b == (A / 'round356-party-preview-independent-source-review/frozen' / rel).read_bytes()
    capture(rel, 'frozen/' + rel, b, 'unchanged published HEAD and independently retained I356 source')
assert len(refs) == 19
jout('source-references.json', refs)

receipt_names = ['apply-receipt.json', 'scope-correction-receipt.json', 'split-correction-receipt.json',
                 'watch-correction-receipt.json', 'peer-watch-correction-receipt.json']
receipts = {}
for name in receipt_names:
    b = (T / name).read_bytes()
    receipts[name] = json.loads(b)
    put('upstream-receipts/' + name, b)
work = current.copy()
proof = []
for name in reversed(receipt_names):
    v = receipts[name]
    edits = v.get('edits', [v])
    for e in reversed(edits):
        rel = e['source']
        old, new = bytes.fromhex(e['before_hex']), bytes.fromhex(e['after_hex'])
        count = e.get('multiplicity', e.get('count', 1))
        assert work[rel].count(new) == count, (name, rel)
        work[rel] = work[rel].replace(new, old)
    proof.append(dict(receipt=name, reversed_edits=len(edits), receipt_sha256=sha((T / name).read_bytes())))
for rel in pins:
    assert work[rel] == baseline[rel], rel
    assert current[rel] == (S / rel).read_bytes()
jout('four-complete-byte-inverses.json', dict(head=HEAD, reverse_receipts=proof,
    inverse_equal_all=True, files=[dict(source=r, baseline_bytes=len(baseline[r]),
    baseline_sha256=sha(baseline[r]), final_bytes=len(current[r]), final_sha256=sha(current[r])) for r in pins]))

specs = [('src/net/Session.h', 175, 190), ('src/net/Session.cpp', 59, 96),
         ('src/net/Session.cpp', 234, 246), ('src/net/Session.cpp', 372, 381),
         ('src/net/Session.cpp', 2153, 2327), ('src/net/Session.cpp', 2774, 2807),
         ('src/core/Application.cpp', 6993, 6999), ('src/core/Application.cpp', 7093, 7107),
         ('src/core/Application.cpp', 7134, 7178), ('src/core/Application.cpp', 7382, 7417),
         ('src/core/Application.cpp', 7457, 7465), ('src/core/Application.cpp', 7485, 7506),
         ('src/game/OwnedPartyPreviewTransport.h', 42, 77),
         ('src/game/OwnedPartyPreviewTransport.h', 99, 123),
         ('src/game/OwnedPartyPreviewTransport.h', 129, 194)]
cuts = []
for i, (rel, lo, hi) in enumerate(specs):
    lines = current[rel].splitlines(keepends=True)
    assert 1 <= lo <= hi <= len(lines)
    b = b''.join(lines[lo - 1:hi])
    retained = 'cuts/%02d-%s-L%d-L%d.txt' % (i, Path(rel).name, lo, hi)
    put(retained, b)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, first_line=lo,
        last_line=hi, bytes=len(b), sha256=sha(b), scope='selected partial excerpt; complete containing file retained'))
jout('source-cuts.json', cuts)
jout('review-history.json', dict(preliminary_read_error='First console-only read used default cp950 and stopped at Application UTF8. No source/artifact mutation; successor explicit UTF8 read succeeded.',
    early_candidates='Historical early four captured unchanged from T/candidate; final corrections separately proven by complete inverse.',
    source_semantic_verdict='PASS', product_execution=False, owner_stop='Finish357 only; no358'))
put('REPORT.md', b'''# Round357 independent callback admission source review

PASS for final four existing files at immutable baseline b5a2afd1364c50613525f07757ba31350dad9882. Nineteen whole-source references retain current4, baseline4 and unchanged11 dependencies; fifteen excerpts are explicitly partial with their containing whole sources. Five literal receipt stages independently reverse all four final files to the exact published whole sources. Early candidates remain historical; they are not final pins. I35639/2722597 and P35727/1140439 each had every member verified in place.

Actual private own callback TLS plus Written INIT supplies Data; callers can only reject Pending, never admit it. Exact callback membership checks recorded thread, TLS Session, current private capture pointer and status pointer independent of status/poison/currentness. This preserves the committed prefix through Options split inner runs, including Failed same-callback state. Non-reading retirement only rejects exact own-callback data; nested Reading reentry rejects the shared current data even for another Session. Generic no-admission accepted semantics retain the original source branch. Party feature, ordinary watch refresh and peer watch catches reject only an actual committed preview prefix, preserving no-prefix legacy behavior.

Independent private Pending Attempt survives game capture, exchange and posted closure; drop/unwind fails Pending even with externally retained Data. Whole final response validity, original normal components and exact raw response fences remain separate and symmetric. Nonempty original bytes enqueue without reframing; empty accepted response creates no Write. The same private Sync guards actual insertion and final admission; locked work has no SQL/log/callback/write/close. Admitted CAS follows original FIFO/log/terminal/resume work and a final pure frozen-source guard. Any throw/drop/stale/close leaves Failed; a true already-queued prefix cannot be rolled back. Admitted is not Written, ACK or native authority.

Prepared registry owns full source INITs, actual strong Sessions, fresh handles, projection buffers and callback receipt before CAS. mark_committed is immediate after Directory CAS; hand_off is only a noalloc/noexcept deferred flag after both model publications. Deferred destructor preserves the owning flight; unfinished committed work closes exact held sources. Existing Scheduler waits actual Admitted, submits once, then settles real Pending/Queued/Failed output attempts. Failed/stale/stop retires exact held handles/peers; allQueued removal does not revoke successful Write data. Preparation role/position/HUD is not a live DB refresh. No target execution, SQL, native, compiler, tests, new rule/format/route credit or358 work occurred. Caller convergence, native Written/ACK/adoption and all variants remain OPEN.
''')
jout('capture-complete.json', dict(status='PASS', source_head=HEAD, whole_count=19,
    cuts_count=len(cuts), current_pins={r:dict(bytes=len(b), sha256=sha(b)) for r,b in current.items()},
    inverse_files=4, prior_packages=3, prior_members=123, prior_bytes=10860369))
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
sb = (O / 'SEAL.json').read_bytes()
hb = Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(status='PASS', member_count=len(members), member_bytes=total,
    seal_bytes=len(sb), seal_sha256=sha(sb), helper_bytes=len(hb), helper_sha256=sha(hb))))
