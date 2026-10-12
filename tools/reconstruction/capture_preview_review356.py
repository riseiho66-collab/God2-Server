from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
I = A / 'round356-party-preview-output-implementation'
HEAD = '6c2d3412e22316d1537323bc13e449f87ddfd03a'

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
ab = (I / 'apply-receipt.json').read_bytes()
cb = (I / 'containment-receipt.json').read_bytes()
apply = json.loads(ab)
contained = json.loads(cb)
assert apply['head'] == HEAD and apply['old_whole_inverse_equal'] and len(apply['edits']) == 8
assert contained['inverse_equal'] and len(contained['edits']) == 3
refs = []
inverse = []
wholes = {}
for pin in apply['candidate']:
    rel = pin['source']
    early = (I / 'candidate' / rel).read_bytes()
    assert len(early) == pin['bytes'] and sha(early) == pin['sha256']
    current = (S / rel).read_bytes()
    is_new = pin['new']
    if is_new:
        assert rel == 'src/game/OwnedPartyPreviewTransport.h'
        assert len(current) == contained['bytes'] and sha(current) == contained['sha256']
        assert current == (I / 'contained-OwnedPartyPreviewTransport.h').read_bytes()
        restored = current
        for e in reversed(contained['edits']):
            after = bytes.fromhex(e['after_hex'])
            assert restored.count(after) == 1
            restored = restored.replace(after, bytes.fromhex(e['before_hex']), 1)
        assert restored == early
        assert not subprocess.check_output(['git', 'ls-tree', HEAD, '--', rel], cwd=S).strip()
        put('history/early-OwnedPartyPreviewTransport.h', early)
        inverse.append(dict(path=rel, new_header_absent_at_HEAD=True, early_bytes=len(early), early_sha256=sha(early),
            current_bytes=len(current), current_sha256=sha(current), containment_three_edits_inverse=True))
    else:
        assert current == early
        old = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
        assert old == (I / 'before' / rel).read_bytes() and sha(old) == pin['before_sha256']
        restored = current
        for e in reversed([e for e in apply['edits'] if e['source'] == rel]):
            after = bytes.fromhex(e['after_hex'])
            assert restored.count(after) == 1
            restored = restored.replace(after, bytes.fromhex(e['before_hex']), 1)
        assert restored == old
        retained = 'baseline/' + rel
        put(retained, old)
        refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(old), sha256=sha(old),
                         source_state='git show ' + HEAD))
        inverse.append(dict(path=rel, before_bytes=len(old), before_sha256=sha(old), current_bytes=len(current),
                            current_sha256=sha(current), exact_whole_inverse=True, current_equals_early_candidate=True))
    retained = 'current/' + rel
    put(retained, current)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(current), sha256=sha(current),
                     source_state='stable candidate with contained new header; differs from HEAD by explicit edits/new file'))
    wholes[rel] = current

frozen = ['src/game/OwnedPartyDirectory.h', 'src/handlers/OwnedPartyDirectoryService.h', 'src/game/NativeParty.h',
          'src/core/Config.h', 'docs/custom-designs.json', 'src/protocol/RecoveredParty.h',
          'src/protocol/TaiwanNativePartyMenu.h', 'src/protocol/RecoveredWorldFrame.h',
          'src/protocol/RecoveredWorldEntryView.h', 'src/core/Scheduler.h', 'src/core/Scheduler.cpp']
for rel in frozen:
    b = (S / rel).read_bytes()
    assert b == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    put('frozen/' + rel, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained='frozen/' + rel, bytes=len(b), sha256=sha(b),
                     source_state='unchanged current equals git show ' + HEAD))
    wholes[rel] = b
assert len(json.loads(wholes['docs/custom-designs.json'])['designs']) == 135
assert b'owned_party_directory_enabled=false' in wholes['src/core/Config.h']

prior = A / 'round355-party-detail-independent-source-review'
prior_seal_bytes = (prior / 'SEAL.json').read_bytes()
assert sha(prior_seal_bytes) == '8bdbf07291823e5afaa44647c4372c1c6cf790b2adf3c1d66f209289367e38cf'
prior_seal = json.loads(prior_seal_bytes)
assert prior_seal['member_count'] == len(prior_seal['members']) == 39
assert prior_seal['member_bytes'] == sum(m['bytes'] for m in prior_seal['members']) == 1893729
for m in prior_seal['members']:
    b = (prior / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
for rel in ['src/game/OwnedPartyDirectory.h', 'src/handlers/OwnedPartyDirectoryService.h']:
    assert (prior / 'current' / rel).read_bytes() == wholes[rel]
put('prior355-SEAL.json', prior_seal_bytes)
jout('prior355-individual-verification.json', dict(package=prior.as_posix(),
    seal_sha256=sha(prior_seal_bytes), member_count=39, member_bytes=1893729,
    members=prior_seal['members'], current_Directory_Service_equal_retained355=True,
    prior_immutable_and_not_rerun=True))

cuts = []
for rel, spans in [
    ('src/net/Session.cpp', [(188, 214), (494, 523), (2626, 2707)]),
    ('src/net/Session.h', [(405, 425)]),
    ('src/core/Application.cpp', [(1400, 1407), (7350, 7390), (7792, 7805), (7830, 7847)]),
    ('src/game/OwnedPartyPreviewTransport.h', [(1, len(wholes['src/game/OwnedPartyPreviewTransport.h'].splitlines()))])]:
    lines = wholes[rel].splitlines(keepends=True)
    for first, last in spans:
        assert 1 <= first <= last <= len(lines)
        b = b''.join(lines[first-1:last])
        retained = 'cuts/' + Path(rel).stem + '-' + str(first) + '-' + str(last) + '.source'
        put(retained, b)
        cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
                         first_line=first, last_line=last, whole_sha256=sha(wholes[rel])))
put('root-apply-receipt.json', ab)
put('root-containment-receipt.json', cb)
jout('source-references.json', refs)
jout('cuts.json', cuts)
jout('exact-inverses-and-new-header-distinction.json', dict(head=HEAD, existing_literal_edits=8,
    new_header_containment_edits=3, files=inverse, frozen_dependencies=frozen))
put('REPORT.md', b'''PASS within bounded independent static four-source review356.

Existing SessionH/CPP/App restore published6c2 exactly through eight literal
edits; separate new header is absent there. The immutable early9158B/fdc header
is retained history; three additive containment edits restore it from final
9320B/cba. Current three existing files equal their original candidates. Eleven
frozen dependencies equal published HEAD, including actual355 Directory/Service,
NativeParty, protocol, custom135/default-off config and existing Scheduler.

Session new trusted-game capture uses exact recorded game thread/Session/private
Written INIT before bare owner fields and preserves the old locked epoch/private
PK predicate. The old own-callback capture keeps its TLS assertion and delegates;
normal response/blacklist/original observers are otherwise exact unchanged. This
adds recipient transport capture only, never peer callback permission/consent.

Courier Source/Recipient/Flight/State own complete actor copies, strong exact
Session objects, fresh separate handles and expected/logical vectors. Captures,
payload validation, all vectors and registry node precede CAS. Capacity bounds
flights/held sources/projections. Prepared is move-only; abandoned precommit
preparation revokes only fresh handles and erases its reserved node, no peer close.
Immediately after actual Directory CAS mark_committed is noexcept/no allocation,
then unchanged NativeParty move and wire publication precede submit. All actual
source observers precede final fresh-recipient current check; old C91 Queued
permission and existing full group/model guards remain intact.

Submit transfers only exact expected bytes into the existing normal output sender
and retains actual returned attempts. Postcommit throw/failure/stale source revokes
fresh handles and closes exact held flight source peers without model rollback,
retry or successor lookup. Final contained settle catches pure-current exceptions;
all-current/all-Queued retires registry without revoking successful Data. Pending
stays registry-owned with no native timeout. Fresh handle revoke is per-Data; it
does not revoke shared own-response/blacklist handles or advance their epoch.

Existing50ms scheduler settles on game owner; stop precedes scheduler/network
shutdown. Owning State/Flight/Prepared destructors retain safe cleanup across
exceptional unwind, with no borrowed local/current callbacks. Actual disconnect/
closing/private epoch invalidation is observed by current and later tick/stop;
there is no new immediate direct disconnect-registry hook. Lock/OS/allocation
success premises of existing noexcept revoke/standard synchronization remain
inherited; no blanket runtime guarantee is asserted.

No consequential source blocker found after three containment corrections:
uncommitted submit errors no longer close; projection count bounded before
reserve; settle current exceptions cannot terminate through its noexcept entry.
Existing actor/role SQL observers, membership/custom rules/native packet recipes,
default-off behavior and generic paths remain unchanged. Caller final response
rejection (peer-only C91 reply empty), Written/socket delivery/native ACK/adoption,
universal mixed transfer/return, all party variants and rule authority remain OPEN.
Static source PASS, not a full gameplay route/native/runtime acceptance claim.
No tracked edits or compiler/build/tests/API/SQL/native/parser/codec/runtime
execution occurred. Successful LF custody helper executed once; no helper rerun.
''')
jout('capture-success.json', dict(status='PASS', head=HEAD, existing_modified_files=3, new_headers=1,
    references=len(refs), cuts=len(cuts), semantic_blockers=[], contained_correction_review=True,
    not_sealed_until_root_stable_signal=True, successful_helper='capture_preview_review356.py', successful_runs=1))
for ref in refs:
    if not ref['retained'].startswith('baseline/'):
        assert (O / ref['retained']).read_bytes() == Path(ref['actual_path']).read_bytes()
print(json.dumps(dict(status='PASS', references=len(refs), cuts=len(cuts), ready_for_seal=True)))
