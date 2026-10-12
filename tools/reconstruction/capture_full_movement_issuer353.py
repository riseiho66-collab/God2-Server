"""Source/text/hash custody and verification of already retained static cuts only."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
HEAD = '618eb9cbce52632f984b45f7409407a4e465c234'
PRIOR = ROOT / 'artifacts/integration/packet-connections-20261006/tw-native-host-composition-source-01/agents/tw-authority-frontier'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
FULL = [
    'src/game/SharedTaiwanMovement.h', 'src/game/SharedTaiwanMovement.cpp',
    'src/game/SharedTaiwanMovementSource.h', 'src/game/SharedTaiwanMovementSource.cpp',
    'src/game/SharedTaiwanNativeMovementScene.h', 'src/game/SharedTaiwanNativeMovementScene.cpp',
    'src/game/SharedTaiwanNativeMovementHost.h', 'src/game/SharedTaiwanNativeMovementHost.cpp',
    'src/game/TaiwanNativeSceneResourceOwner.h', 'src/game/TaiwanNativeSceneResourceOwner.cpp',
    'src/protocol/RecoveredMovement.h', 'src/protocol/RecoveredNativeMovement.h',
    'src/handlers/RecoveredMovementService.h', 'src/handlers/RecoveredMovementService.cpp',
    'src/scripting/TaiwanMovementRules.h', 'src/scripting/TaiwanMovementRules.cpp',
    'scripts/tw/native_movement.lua',
]
CUTS = [
    ('src/core/Application.cpp', 772, 780, 'application-native-binding-construction'),
    ('src/core/Application.cpp', 6675, 6693, 'application-native-binding-install'),
    ('src/core/Application.cpp', 7475, 7501, 'hosted-normal-movement-receipt'),
    ('src/core/SharedTaiwanNativeWorldHostPlan.cpp', 675, 689, 'host-plan-authentic-binding-delegation'),
    ('src/game/SharedTaiwanNativeMovementScene.h', 70, 96, 'actual-authority-required-contract'),
    ('src/game/SharedTaiwanNativeMovementScene.cpp', 216, 243, 'native-scene-authority-and-permit'),
    ('src/game/TaiwanNativeSceneResourceOwner.cpp', 150, 181, 'resource-owner-real-authority-delegation'),
    ('src/game/SharedTaiwanMovement.cpp', 65, 116, 'full-native-output-before-cas-and-publication'),
    ('src/handlers/RecoveredMovementService.cpp', 520, 540, 'legacy-prepared-sequence-ack-recipe'),
    ('src/handlers/RecoveredMovementService.cpp', 569, 659, 'normal-entry-real-custody-not-native-authority'),
    ('src/net/Session.cpp', 2048, 2084, 'actual-session-movement-callback'),
    ('src/net/Session.cpp', 2108, 2146, 'actual-session-original-output-queue'),
    ('docs/research/current-live-movement-20260920.md', 1, 24, 'historical-owned-loopback-ack-scope'),
    ('docs/research/shared-taiwan-movement-20261007.md', 1, 15, 'historical-native-source-scope'),
]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def dump(name, value):
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

def write(name, raw):
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)

assert not (OUT / 'SEAL.json').exists()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == HEAD
references = []
raws = {}
for name in sorted(set(FULL + [x[0] for x in CUTS])):
    raw = (ROOT / name).read_bytes()
    assert raw == subprocess.check_output(['git', 'show', HEAD + ':' + name], cwd=ROOT), name
    raws[name] = raw
    entry = {'source': name, 'head': HEAD, 'bytes': len(raw), 'sha256': sha(raw), 'current_equals_git_show': True}
    if name in FULL:
        member = 'sources/' + name
        write(member, raw)
        entry['member'] = member
    references.append(entry)
cuts = []
for name, first, last, label in CUTS:
    lines = raws[name].splitlines(keepends=True)
    assert 1 <= first <= last <= len(lines), (name, first, last, len(lines))
    start = sum(map(len, lines[:first - 1]))
    end = sum(map(len, lines[:last]))
    raw = raws[name][start:end]
    member = 'cuts/' + label + '.txt'
    write(member, raw)
    cuts.append({'source': name, 'first_line': first, 'last_line': last,
                 'start_byte': start, 'end_byte_exclusive': end, 'member': member,
                 'bytes': len(raw), 'sha256': sha(raw)})
dump('source-references.json', {'head': HEAD, 'whole_sources': references, 'cuts': cuts})

seal_raw = (PRIOR / 'seal.json').read_bytes()
prior_seal = json.loads(seal_raw)
assert prior_seal['member_count'] == len(prior_seal['members']) == 90
verified = []
for member in prior_seal['members']:
    raw = (PRIOR / member['path']).read_bytes()
    assert len(raw) == member['bytes'] and sha(raw) == member['sha256'], member['path']
    verified.append(member)
write('prior176/seal-original.json', seal_raw)
dump('prior176/individual-verification.json', {'path': PRIOR.as_posix(), 'seal_sha256': sha(seal_raw),
    'member_count': len(verified), 'member_bytes': sum(m['bytes'] for m in verified),
    'members': verified, 'all_equal': True, 'prior_modified': False})
mapped = (PRIOR / 'input/native.bin').read_bytes()
assert sha(mapped) == PIN
spans = json.loads((PRIOR / 'native-spans.json').read_bytes())
selected = []
for span in spans:
    if span['start_rva'] not in {'000692FA', '00103700', '00001216', '001036B0', '00103640'}:
        continue
    start, end = int(span['start_rva'], 16), int(span['end_exclusive_rva'], 16)
    raw = (PRIOR / span['copy']).read_bytes()
    assert raw == mapped[start:end] and len(raw) == span['bytes'] and sha(raw) == span['sha256']
    member = 'native/' + span['start_rva'] + '.bin'
    write(member, raw)
    item = dict(span)
    item['prior_member'] = span['copy']
    item['member'] = member
    item['mapped_equal'] = True
    item['coverage'] = 'known prior176 retained static span; no new method or authority credit'
    selected.append(item)
assert len(selected) == 5
dump('native/selected-retained-spans.json', {'mapped_image_path': (PRIOR / 'input/native.bin').as_posix(),
    'mapped_sha256': PIN, 'image_copied': False, 'new_pe_qualification': False,
    'original_pe_scope': 'Prior176 retained evidence; this audit checks existing mapped cuts, not a new PE extraction.',
    'spans': selected})
for name in ['historical-trace-scope.json', 'input/g03.csv', 'input/g06.json']:
    write('prior176/' + name, (PRIOR / name).read_bytes())

dump('issuer-frontier.json', {
    'hosted_legacy': 'Actual normal-entry whole-material movement calls prepare_move_batch: required sequence(slot+1)%40 and prebuilt RecoveredMovement::ack(request.sequence). Actual private receipt/one joint commit do not establish native fullBYTE/timing/reset rules.',
    'full_native_chain': ['Application make_taiwan_movement Context', 'SharedTaiwanMovementSource actual Factory',
        'SharedTaiwanNativeMovementScene::authorize Candidate', 'installed actual_authority->authorize(candidate)',
        'retained complete Permit full_native_ack/current/publish', 'full framing before CAS',
        'actual actor/pending publication', 'Session original response queue'],
    'earliest_missing_concrete_supplier': 'TaiwanNativeSceneResourceOwner::Input.authority H40 -> entry->actual_authority CPP169: a genuine immutable original server pending/timing/reset/permission ticket and exact original5D BYTE, whose current/publish qualify the actual scene/ring/owner incarnation.',
    'consumer_evidence': '4692FA..469345 stores receivedBYTE world+231 then calls503700 and46CC00. It never compares that BYTE to a request sequence and does not test the pop return before publishing. Empty pop branch does not write the output point; no legitimate empty-pending success inferred.',
    'surviving_golden_scope': 'Directory name is not authority: protocol-core.csv has seed exchange/opcode1 only; session LOGIN=false/POST_SEED_ACCEPTED. Existing doc5d01 refers to owned-loopback probe, not original server output.',
    'missing_original_trace': 'A retained original-server movement event/producer with full2E request, exact5D byte, authenticated owner/phase, time/pending/reset state and corresponding real commit/publication event is required to qualify a native issuer; no capture is executed in PHASE1.',
    'client_timing_limit': 'Native client elapsed/path/ring code is local presentation/pending behavior, not proof of original server admission/rate/ACK rules.',
    'permitted_next_integration_if_supplier_obtained': 'A concrete Scene::Authority implementation strongly owns the genuine immutable pending/timing source and produces exact Permit; current/publish recheck one-use actual owner. Existing controller/host/Session chain already carries full bytes without echo construction.',
    'implementation_proposed_now': False, 'reason': 'No source-qualified full originalBYTE/timing supplier in the selected present path; another adapter or echo would only move the unknown.',
    'separate_open_domains': ['original common acquisition', 'genuine per-instance full25', 'complete native1215'],
    'new_method_credit': 0, 'new_route_credit': 0, 'native_acceptance_credit': 0})
dump('capture-scope.json', {'source_reads_hashes_git_show_only': True,
    'native_operation': 'hash existing mapped149c and compare known5 tiny retained static spans; serialize their existing disassembly metadata',
    'old_helper_reruns': 0, 'new_disassembly_execution': 0, 'CRT_executed_or_newly_read': False,
    'retired_corpus_reads': 0, 'tracked_edits': 0, 'target_or_API_execution': 0, 'SQL_execution': 0,
    'runtime_compiler_test_codec_resource_parser_execution': 0,
    'readonly_discovery_errors': ['Literal Session.* Windows path failed; corrected through rg --files to src/net/Session.cpp/.h.',
        'Literal docs movement* Windows paths failed; corrected to filename-discovered specific documents.'],
    'helper_failures': [], 'success_count': 1})
report = '''# Round353 independent full native movement issuer source

Pinned source HEAD618eb9cbce52632f984b45f7409407a4e465c234. No tracked files changed. This audit independently separates real current hosted legacy response custody, full-native source transport and original server authority.

Actual Application772..780 creates the configured make_taiwan_movement binding and6675..6693 installs it in the actual dispatcher. SharedTaiwanNativeWorldHostPlan675..689 preserves that real binding. SharedTaiwanMovement65..116 accepts a complete WorldOwner authorization, frames its exact full5D before the only position CAS, and requires actual scene/actor publication plus observer publication before returning it. Session2048..2084 invokes the actual game callback and2108..2146 carries its unchanged already-framed output to the bounded strand queue. Those are real transport/storage/lifetime seams; they do not derive ACK semantics.

The earliest full-native issuer boundary is concrete: SharedTaiwanNativeMovementScene216..243 calls authority_->authorize(candidate). TaiwanNativeSceneResourceOwner150..181 delegates to the installed entry->actual_authority and preserves its Permit full_native_ack. Input.authority at its header40 is mandatory. Permit must own the exact full byte and true pre-CAS pending/timing/reset/permission source plus one-use current/publication behavior. This wrapper's real resource and owner checks do not generate the byte, pending state or server timing policy.

The currently hosted ordinary normal-entry route Application7475..7501 calls move_committed_with_owned_material_and_receipt. It uses the same prepare_move_batch520..540 recipe: sequence(slot+1)%40, per-axis adjacent movement, navigation check, and RecoveredMovement::ack(request.sequence). Its actual private initialization/current receipt, one joint position/material commit and original prebuilt response ownership are genuine. The preserved ACK recipe is a legacy policy; the mutation receipt is not an original full5D issuer or timing ticket. No behavior change is proposed to that frozen path.

Retained prior176 is independently verified: every90 sealed member's individual size/hash matches. Five known spans are checked against the retained mapped149c image in place, including the actual5D length leaf, selected WORLD case4692FA..469345 and complete ring pop503700..503741. No image is copied and no original native instruction executes. The case stores BYTE[packet+1] at world+231, invokes503700 and then46CC00 without comparing the byte to an input sequence and without testing pop output status. The pop's empty branch does not write the output point. These consumer/local pending effects cannot justify an original-server echo, rejection byte, empty-pending success or authoritative admission/rate rule. No new method identity is credited.

The retained golden directory name native-movement-ack-20260920-02 is misleading if treated as current movement authority: its418-byte CSV contains only seed/post-seed exchange and opcode1, and its393-byte session says LOGIN=false, POST_SEED_ACCEPTED. The historical live-movement document1..24 explicitly scopes the5d01 consumption to an owned loopback server/native-function probe. Neither is an original server5D producer. Prior176 preserved this distinction; it is not refreshed into new acceptance here.

The next actionable supplier is the genuine original server movement event or producer behind Input.authority: exact2E request, full5D byte, actual owner/phase/time/pending/reset state and corresponding commit/publication event. A qualified concrete Scene::Authority could then supply its immutable ticket and exact Permit through the already existing chain. Client path/ring/elapsed presentation alone cannot supply that server admission policy. No new factory, unhosted getter, guessed quota, echo/default BYTE or C++ change is justified now. This is a scoped supplier gap, not a global absence claim. Common acquisition/full25/full1215 remain separate OPEN domains. Full route/native acceptance credits0.

source-references.json preserves whole current source hashes and exact selected line/byte cuts; prior176/individual-verification.json accounts every immutable prior member; native/selected-retained-spans.json owns only bounded known cuts and existing instruction metadata. All target/API/runtime/native/CRT/VM/SQL/resource-parser/codec/compiler/test/import/deploy counts0. Original prior seals and canonical sources remain unchanged. capture-scope.json preserves readonly filename discovery corrections. The single LF helper was executed once.
'''
write('REPORT.md', report.encode())
for name, raw in raws.items():
    assert (ROOT / name).read_bytes() == raw, name
members = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        raw = path.read_bytes()
        members.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)})
dump('SEAL.json', {'head': HEAD, 'member_count': len(members),
    'member_bytes': sum(x['bytes'] for x in members), 'members': members,
    'accounting': 'individual regular-file sizes, excluding this seal', 'source_only': True})
for member in members:
    raw = (OUT / member['path']).read_bytes()
    assert len(raw) == member['bytes'] and sha(raw) == member['sha256']
seal = (OUT / 'SEAL.json').read_bytes()
print(json.dumps({'head': HEAD, 'member_count': len(members), 'member_bytes': sum(x['bytes'] for x in members),
    'seal_bytes': len(seal), 'seal_sha256': sha(seal), 'prior_members_verified': len(verified),
    'prior_member_bytes': sum(x['bytes'] for x in verified)}))
