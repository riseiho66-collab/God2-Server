from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
A = OUT.parent
I = A / 'round355-party-detail-response-implementation'
HEAD = 'b934e539e9d0cb279e2d6b58678afdb7b555dcf9'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(p, b):
    p = OUT / p
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        assert p.read_bytes() == b  # Preserve and verify original partials.
        return
    with p.open('xb') as f:
        f.write(b)

def jout(p, value):
    put(p, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == HEAD
edits_bytes = (I / 'literal-edits-and-inverse.json').read_bytes()
edits = json.loads(edits_bytes)
pins_bytes = (I / 'initial-final-pins.json').read_bytes()
pins = json.loads(pins_bytes)
assert edits['head'] == HEAD and edits['exact_inverse'] and len(edits['edits']) == 13
references = []
inverse = []
sources = {}
for pin in pins:
    rel = pin['path']
    current = (ROOT / rel).read_bytes()
    assert len(current) == pin['bytes'] and sha(current) == pin['sha256']
    old = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=ROOT)
    assert len(old) == pin['before_bytes'] and sha(old) == pin['before_sha256']
    assert (I / 'before' / rel).read_bytes() == old
    assert (I / 'before-v2' / rel).read_bytes() == old
    restored = current
    for e in reversed([e for e in edits['edits'] if e['path'] == rel]):
        before = e['before'].encode('utf-8')
        after = e['after'].encode('utf-8')
        assert restored.count(after) == 1
        restored = restored.replace(after, before, 1)
    assert restored == old
    for stage, value in [('current', current), ('baseline', old)]:
        retained = stage + '/' + rel
        put(retained, value)
        references.append({'actual_path': str(ROOT / rel).replace('\\', '/'), 'retained': retained,
                           'bytes': len(value), 'sha256': sha(value),
                           'source_state': 'current uncommitted candidate' if stage == 'current' else 'git show ' + HEAD})
    inverse.append({'path': rel, 'before_bytes': len(old), 'before_sha256': sha(old),
                    'current_bytes': len(current), 'current_sha256': sha(current), 'exact_inverse': True,
                    'root_before_and_before_v2_equal_git_show': True})
    sources[rel] = current

frozen = ['src/net/Session.h', 'src/net/Session.cpp', 'src/core/Config.h', 'src/game/NativeParty.h',
          'src/protocol/TaiwanNativePartyMenu.h', 'src/protocol/RecoveredWorldFrame.h',
          'src/protocol/RecoveredWorldEntryView.h']
for rel in frozen:
    b = (ROOT / rel).read_bytes()
    assert b == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=ROOT)
    retained = 'frozen/' + rel
    put(retained, b)
    references.append({'actual_path': str(ROOT / rel).replace('\\', '/'), 'retained': retained,
                       'bytes': len(b), 'sha256': sha(b), 'source_state': 'frozen current equals git show ' + HEAD})
    sources[rel] = b

prior = A / 'round353-original-response-independent-source-review'
seal_bytes = (prior / 'SEAL.json').read_bytes()
assert sha(seal_bytes) == '540177a88ee5b7073518ab2880a1144048eda9b09b697b3a74626da39b8014ef'
seal = json.loads(seal_bytes)
members = []
for m in seal['members']:
    b = (prior / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
    members.append(m)
assert len(members) == seal['member_count'] == 32
assert sum(m['bytes'] for m in members) == seal['member_bytes'] == 2294474
for rel in ['src/net/Session.h', 'src/net/Session.cpp']:
    # Identify the final retained full source from the member list, never a partial cut.
    b = sources[rel]
    matches = [m for m in members if m['bytes'] == len(b) and m['sha256'] == sha(b)]
    assert matches and any((prior / m['path']).read_bytes() == b for m in matches)
jout('prior-session353-member-verification.json', {'package': str(prior).replace('\\', '/'),
     'seal_sha256': sha(seal_bytes), 'member_count': len(members), 'member_bytes': sum(m['bytes'] for m in members),
     'members': members, 'final_current_Session_wholes_equal_retained353': True})

cuts = []
for rel, spans in [
    ('src/core/Application.cpp', [(6984, 7035), (7036, 7139), (7140, 7245), (7246, 7374)]),
    ('src/handlers/OwnedPartyDirectoryService.h', [(15, 32), (141, 178), (240, 278)]),
    ('src/net/Session.cpp', [(331, 351), (494, 523), (1886, 1917), (2194, 2259), (2704, 2761)])]:
    lines = sources[rel].splitlines(keepends=True)
    for first, last in spans:
        assert 1 <= first <= last <= len(lines)
        b = b''.join(lines[first-1:last])
        retained = 'cuts/' + Path(rel).stem + '-' + str(first) + '-' + str(last) + '.source'
        put(retained, b)
        cuts.append({'actual_path': str(ROOT / rel).replace('\\', '/'), 'retained': retained,
                     'first_line': first, 'last_line': last, 'bytes': len(b), 'sha256': sha(b),
                     'whole_source_sha256': sha(sources[rel])})
put('root-literal-edits-and-inverse.json', edits_bytes)
put('root-initial-final-pins.json', pins_bytes)
helper = I / 'helpers' / 'apply_party_response_custody355_v2.py'
hb = helper.read_bytes()
assert b'\r' not in hb
jout('root-successful-generation-reference.json', {'actual_path': str(helper).replace('\\', '/'),
     'bytes': len(hb), 'sha256': sha(hb), 'LF': True, 'not_rerun': True})
jout('source-references.json', references)
jout('cuts.json', cuts)
jout('three-file-exact-inverse.json', {'baseline_head': HEAD, 'edit_count': 13, 'files': inverse,
     'frozen_dependencies': frozen, 'no_tracked_writes_from_review': True})
report = '''PASS — bounded independent static source review, round355.

The three current candidate files are retained whole and reverse exactly to
published b934e539e9d0cb279e2d6b58678afdb7b555dcf9 using the thirteen literal
edits. Root before and before-v2 snapshots equal those exact published bytes.
Seven frozen dependency files equal published HEAD, including unchanged Session.
The prior353 review seal and every individual member were verified in place.

C90 retires its old private permission before source observations (Application
7170..7185). After genuine Written INIT and actual actor observations, it captures
its own actual callback receipt before allocating the new state/frame (7234..7240).
The same owning receipt goes to Detail and Presentation (7259..7262). Complete
AB logical/frame/merged bytes exist before expect_normal_world_response (7315,
7363); registration precedes CAS. The post-registration guards are pure private
callback/INIT, reentry, party state and exact COW snapshot checks (7364..7368).
The original framed component is appended to the returned wire, without a new
transport or mutation of the packet recipe. A later omitted/rejected/phase-changed
armed response is handled by existing353 final-wire/RAII failure, not SQL rollback.

C91 requires current Queued receipt before preparing the old membership adapter
(7266), and again after every observer before publication (7351). The service
helper checks Queued on both sides of current_on_game; it deliberately does not
require the old Queued receipt to be the new callback's capture. Pending cannot
authorize C91, including C90+C91 in one callback. Failed or absent cannot grant.

Watch and final retained Presentation fence require a non-Failed current receipt
while allowing provisional Pending. Identity, complete member readsets, party
participants/size and existing private Written INIT guards are preserved. Actual
old permission retirement, C8D/window closure, ready/disconnect, sender bytes,
CUSTOM policies and default-off config are literal unchanged except listed edits.
Public receipt copies do not keep the private pending RAII wrapper alive and
source retirement does not revoke shared callback Data used by options/blacklist.

Existing Session predicates under Sync inspect immutable/atomic state without
SQL/callback/log/send/write/close. Its strand last guard, FIFO push and Queued CAS
share the lock; failure/close/write follow outside it. Registered components must
match in order at final frame boundaries. Queued proves FIFO insertion only, not
socket Written, native acceptance or client adoption. Generic unarmed flow and
old WorldResponseWrite/native PK paths remain separate and unchanged.

No consequential source defect found in this bounded delta. No compiler, test,
runtime, native, parser/codec, API or SQL execution occurred. Peer C91 preview
transport, adoption, universal mixed transfer/return and whole native party rules
remain OPEN. No route/format/native-acceptance completion credit is asserted.
'''
put('REPORT.md', report.encode('utf-8'))
jout('capture-success.json', {'status': 'PASS', 'baseline_head': HEAD, 'candidate_files': inverse,
     'reference_count': len(references), 'cut_count': len(cuts), 'static_source_only': True})
print(json.dumps({'status': 'PASS', 'references': len(references), 'cuts': len(cuts)}))
