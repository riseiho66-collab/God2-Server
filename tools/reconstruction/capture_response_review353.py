"""Independent source/hash review custody; no product API/code/SQL execution."""
from pathlib import Path
import hashlib
import json
import subprocess
import difflib

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
A = OUT.parent
HEAD = '618eb9cbce52632f984b45f7409407a4e465c234'
PINS = {
    'src/net/Session.h': (33839, '74af3bbc1146f2c21f99a3768a662c94748ab514f74592655a829e9c31bc5f2e'),
    'src/net/Session.cpp': (233672, 'b29b89402bd5710dc8ce05298d943f2abacfe6df1c6fc480cdbfb3b14613aba3'),
    'src/core/Application.cpp': (718069, '37e0c23b637fceda704ca1719bd37eb0f07f8a9e8758188b6eed64ade5d0351c'),
}
CUTS = [
    ('src/net/Session.h', 175, 190, 'private-response-type'),
    ('src/net/Session.h', 420, 427, 'used-response-api'),
    ('src/net/Session.cpp', 60, 90, 'tls-poison-observation-scope'),
    ('src/net/Session.cpp', 215, 227, 'private-stage-data'),
    ('src/net/Session.cpp', 331, 352, 'armed-failure-raii'),
    ('src/net/Session.cpp', 487, 525, 'epoch-locked-current-peer-vs-own'),
    ('src/net/Session.cpp', 1897, 1920, 'ordered-frame-boundary-components'),
    ('src/net/Session.cpp', 2125, 2137, 'serial-callback-raii-reset'),
    ('src/net/Session.cpp', 2181, 2259, 'final-handoff-and-fifo-atomic-guard'),
    ('src/net/Session.cpp', 2605, 2638, 'actual-initialization-tls-game-current'),
    ('src/net/Session.cpp', 2704, 2761, 'same-callback-registration-current-arm'),
    ('src/core/Application.cpp', 927, 1004, 'own-response-pure-chain-no-peer-node'),
    ('src/core/Application.cpp', 6722, 6766, 'actual-blacklist-callback-owner'),
    ('src/core/Application.cpp', 6770, 6804, 'capture-before-sql-and-pure-current'),
    ('src/core/Application.cpp', 6827, 6850, 'actual-wire-before-own-endpoint'),
    ('src/core/Application.cpp', 6930, 6968, 'replay-original-wire-before-cursor'),
]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(name, raw):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)

def dump(name, value):
    write(name, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

assert not (OUT / 'SEAL.json').exists()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == HEAD
raws = {}
references = []
for name, (size, digest) in PINS.items():
    current = (ROOT / name).read_bytes()
    assert len(current) == size and sha(current) == digest, name
    raws[name] = current
    baseline = subprocess.check_output(['git', 'show', HEAD + ':' + name], cwd=ROOT)
    write('final/' + name, current)
    write('baseline/' + name, baseline)
    delta = ''.join(difflib.unified_diff(baseline.decode().splitlines(keepends=True),
        current.decode().splitlines(keepends=True), fromfile=HEAD + '/' + name, tofile='stable-candidate/' + name))
    write('diff/' + Path(name).name + '.diff', delta.encode())
    references.append({'path': name, 'baseline_head': HEAD, 'baseline_bytes': len(baseline),
        'baseline_sha256': sha(baseline), 'final_bytes': size, 'final_sha256': digest,
        'source_state': 'stable uncommitted candidate; not relabeled HEAD contents'})

session_package = A / 'round353-normal-original-response-transport-implementation'
old_path = session_package / 'candidate/src/net/Session.cpp'
old = old_path.read_bytes()
assert len(old) == 233672 and sha(old) == '50614412e93a756d8016e95ef74a81a369d3c5c554ddedc54365c36fea6845da'
write('history/Session.initial-candidate.cpp', old)
first = b's.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});'
second = b's.writes.push_back({bytes,{}});s.write_bytes+=bytes->size();'
position = old.index(first, old.index(b'if(normal_response) {'))
assert old[:position] + second + old[position + len(first):] == raws['src/net/Session.cpp']
correction = (session_package / 'fifo-counter-corrected/src/net/Session.cpp').read_bytes()
assert correction == raws['src/net/Session.cpp']
app_package = A / 'round353-blacklist-original-response-host-implementation'
assert (app_package / 'Application.candidate.cpp').read_bytes() == raws['src/core/Application.cpp']
dump('history/candidate-correction.json', {'original_path': old_path.as_posix(), 'original_bytes': len(old),
    'original_sha256': sha(old), 'corrected_bytes': len(correction), 'corrected_sha256': sha(correction),
    'exact_single_replacement_byte_offset': position,
    'before': first.decode(), 'after': second.decode(), 'all_other_bytes_equal': True,
    'scope': 'New observed branch only; frozen unobserved branch preserved.'})

cuts = []
for name, first_line, last_line, label in CUTS:
    raw = raws[name]
    lines = raw.splitlines(keepends=True)
    assert 1 <= first_line <= last_line <= len(lines)
    start, end = sum(map(len, lines[:first_line - 1])), sum(map(len, lines[:last_line]))
    content = raw[start:end]
    member = 'cuts/' + label + '.txt'
    write(member, content)
    cuts.append({'path': name, 'first_line': first_line, 'last_line': last_line,
                 'start_byte': start, 'end_byte_exclusive': end, 'member': member,
                 'bytes': len(content), 'sha256': sha(content)})
dump('source-references.json', {'baseline_head': HEAD, 'sources': references, 'cuts': cuts,
    'upstream_candidates_not_mutated': [session_package.as_posix(), app_package.as_posix()]})

native_package = A / 'round353-native-full-movement-issuer-source'
native_seal_raw = (native_package / 'SEAL.json').read_bytes()
assert sha(native_seal_raw) == '1e7ba3cf95516eaa61ca103fecf999d796dbd809176412c70f2b92b2410ab107'
native_seal = json.loads(native_seal_raw)
assert native_seal['member_count'] == len(native_seal['members']) == 47
for item in native_seal['members']:
    raw = (native_package / item['path']).read_bytes()
    assert len(raw) == item['bytes'] and sha(raw) == item['sha256']
dump('native47-prior-unchanged.json', {'path': native_package.as_posix(),
    'seal_sha256': sha(native_seal_raw), 'members_verified': 47,
    'member_bytes': sum(x['bytes'] for x in native_seal['members']), 'all_equal': True,
    'native_sources_researched_or_credited_in_this_review': False})

report = '''# Independent353 original-response source review — PASS

Stable candidate: Session.h33839/74af3bbc..., Session.cpp233672/b29b8940..., Application.cpp718069/37e0c23b.... Baseline352 HEAD618eb9cbce52632f984b45f7409407a4e465c234 is retained separately. These final files are uncommitted candidates, never relabeled as HEAD source. The prior50614412 Session candidate is owned as history, and exact one-site correction proves all other bytes equal.

No consequential blocking flaw found in the reviewed source custody path. This is manual static review of control flow, ownership and failure semantics; no implementation-mirroring tests, target API, SQL, parser/codec/native/runtime/compiler/test execution was performed.

1. Private INIT/thread/TLS identity: capture requires its actual world-record callback and actual NormalWorldInitialization. New Data is created before the database operation. Repeated split inner runs reuse one identical callback Data, while a different INIT/retired current capture poisons instead of replacing it. Current checks exact recorded game thread, Session, INIT/Entry, epoch, phase and battle; own original response intentionally does not require Entry::written. Existing peer push requires Written and remains separate. Public account/character fields are checked only on game; strand guard uses immutable private Entry identity and synchronized/atomic state.

2. Ordered actual wire: Application registers the exact bytes it just appended to its own response vector. Mutation/no-op registration precedes own_response and any new snapshot endpoint; initial replay registration precedes replay snapshot/cursor/done state. Final Session matching scans complete validated frame boundaries, preserving component order and nonoverlap while allowing unrelated original reply frames. The final transport holds unchanged already-framed bytes; it neither decodes/re-encodes nor claims remote adoption.

3. Pure Current: blacklist_chain_current checks own_response even when there are no incoming peer nodes. SQL Current performs no settlement/map mutation/close/SQL reader reentry; same callback current is part of its source predicate. Previous Pending own Data is reusable only in that same callback. Failed own output or prior peer attempt does not become eligible merely because durable DB bytes later coincide. Actual no-op replies are still registered even though changedfalse does not fan out. Copied facade cannot mint INIT or original-response Data; unarmed old sender behavior remains separate.

4. Failure lifecycle: nonempty expected component arms the private failure contract before validation/copy allocation. Any later append/registration/final match/rejection/caught-reentry/strand-post failure leaves Failed, retires synchronized epoch and requests close only for the armed actual recipient. RAII covers unhanded attempts. Empty/unarmed capture preserves legacy behavior. Queued means actual FIFO insertion, never socket Written/native ACK; subsequent close/write failure invalidates current epoch without pretending the FIFO insertion did not occur. Old WorldResponseWrite and native-PK terminal receipt checks remain independent.

5. Final mutex boundary: actual last epoch/phase/INIT/battle/pending guard, FIFO push and Queued transition share one lock. No SQL, source observer, log, actual write or close runs under that lock. New observed branch now pushes successfully before adding write_bytes; the old unobserved branch is unchanged. Allocation at FIFO push can fail before debit/Queued, then normal source failure closes. Writes/log/resume happen after unlock.

6. Limits: expected component copies may allocate AFTER a durable mutation. This implementation does not preallocate every allocation. A failure then retires/closes before a provisional endpoint is admitted and does not retry or rewind SQL. This review does not prove OS/Asio delivery, all callbacks/runtime interleavings, client acceptance, native C28/5D rule authority or full-game completion. Existing defaults/profile/opcodes/storage policies stay as baseline; source-only route/native credits0.

Root and c28 early PASS were received before final sealing permission. Native35347-member authority package is verified unchanged and receives no duplicate semantic coverage. source-references.json includes exact cut offsets/hashes. No upstream candidate or prior seal is altered, and no tracked source is edited by this reviewer.
'''
write('REPORT.md', report.encode())
dump('review-manifest.json', {'verdict': 'PASS bounded manual static source review',
    'blocking_findings': [], 'tracked_edits': 0, 'target_execution': 0, 'SQL_execution': 0,
    'native_parser_codec_compiler_runtime_test_execution': 0, 'helper_failures': [],
    'successful_helper': 'capture_response_review353.py', 'successful_helper_count': 1,
    'seal_authorization': 'Root stable H74af3/CPPb29b/App37e0 after root+c28+independent earlyPASS',
    'prior506_preserved_as_historical': True, 'current_candidate_pins': PINS})
for name, raw in raws.items():
    assert (ROOT / name).read_bytes() == raw, name
members = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        raw = path.read_bytes()
        members.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)})
dump('SEAL.json', {'baseline_head': HEAD, 'member_count': len(members),
    'member_bytes': sum(x['bytes'] for x in members), 'members': members,
    'accounting': 'Individual regular-file sizes; excludes this seal.', 'verdict': 'PASS bounded source review'})
for item in members:
    raw = (OUT / item['path']).read_bytes()
    assert len(raw) == item['bytes'] and sha(raw) == item['sha256']
seal = (OUT / 'SEAL.json').read_bytes()
helper = Path(__file__).read_bytes()
print(json.dumps({'member_count': len(members), 'member_bytes': sum(x['bytes'] for x in members),
    'seal_bytes': len(seal), 'seal_sha256': sha(seal), 'helper_bytes': len(helper), 'helper_sha256': sha(helper)}))
