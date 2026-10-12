from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
HEAD = 'b5a2afd1364c50613525f07757ba31350dad9882'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(rel, b):
    p = O / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def jout(rel, v):
    put(rel, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

prior = A / 'round356-inventory-acquisition-frontier-source'
sb = (prior / 'SEAL.json').read_bytes()
assert sha(sb) == 'ff6a681f0e2d4f6c6c08ae790c6a23d4200fe4864cb3bf47460599914d145c1b'
seal = json.loads(sb)
assert seal['member_count'] == len(seal['members']) == 44
assert seal['member_bytes'] == sum(m['bytes'] for m in seal['members']) == 1006244
for m in seal['members']:
    b = (prior / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
put('prior356A-SEAL.json', sb)
jout('prior356A-individual-verification.json', dict(root=prior.as_posix(), seal_sha256=sha(sb),
    member_count=44, member_bytes=1006244, members=seal['members'], verified_in_place=True, unchanged=True))
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
paths = [
    'src/core/Application.cpp', 'src/db/SqliteDatabase.h', 'src/db/SqliteDatabase.cpp', 'src/main.cpp',
    'src/db/OwnedInventoryRepository.h', 'src/db/SqliteOwnedInventoryRepository.h', 'src/db/SqliteOwnedInventoryRepository.cpp',
    'src/db/NativeEquipmentSnapshotRepository.h', 'src/db/SqliteNativeEquipmentSnapshotRepository.h',
    'src/db/SqliteNativeEquipmentSnapshotRepository.cpp', 'src/db/NativeWorldEntrySnapshotRepository.h',
    'src/db/SqliteNativeWorldEntrySnapshotRepository.h', 'src/db/SqliteNativeWorldEntrySnapshotRepository.cpp',
    'src/db/SqliteArmorSlotRepository.h', 'src/db/SqliteArmorSlotRepository.cpp',
    'src/db/SqliteWeaponSlotRepository.h', 'src/db/SqliteWeaponSlotRepository.cpp',
    'src/game/SharedTaiwanOwnedBagMoveSource.h', 'src/game/SharedTaiwanOwnedBagMoveSource.cpp',
    'src/game/TaiwanOwnedBagItemMaterial.h', 'src/db/NativeItemDefinitionObservation.h',
    'tools/strike_lab/private_armor_transfer_20261002.py',
    'tools/strike_lab/private_weapon_rejection_20260927.py',
    'tools/strike_lab/run_private_owned_companions.py',
]
assert len(paths) == len(set(paths)) == 24
refs = []
wholes = {}
for rel in sorted(paths):
    b = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    retained = 'published/' + rel
    put(retained, b)
    live = (S / rel).read_bytes()
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_head=HEAD, source_state='immutable git show published HEAD; source text only, no imports/execution',
        working_at_capture_bytes=len(live), working_at_capture_sha256=sha(live), working_equals_published=live == b))
    wholes[rel] = b
jout('source-references.json', refs)
specs = [
    ('tools/strike_lab/private_armor_transfer_20261002.py', 28, 36, 'source pin and explicitly synthetic origin'),
    ('tools/strike_lab/private_armor_transfer_20261002.py', 56, 79, 'complete instance/fixture_rows producers'),
    ('tools/strike_lab/private_armor_transfer_20261002.py', 247, 272, 'complete guarded seed_migrated_clone operation'),
    ('tools/strike_lab/private_weapon_rejection_20260927.py', 1, 8, 'explicit disposable synthetic operand scope'),
    ('tools/strike_lab/private_weapon_rejection_20260927.py', 96, 124, 'selected original writer metadata input/insert; partial containing function'),
    ('tools/strike_lab/run_private_owned_companions.py', 1, 8, 'explicit synthetic scope'),
    ('tools/strike_lab/run_private_owned_companions.py', 60, 80, 'complete seed_weapon_transfers source producer'),
    ('src/db/SqliteArmorSlotRepository.cpp', 108, 130, 'selected owner/full snapshot storage reads; containing whole file retained'),
    ('src/db/SqliteArmorSlotRepository.cpp', 131, 184, 'selected move/opaque20 preservation; containing whole file retained'),
    ('src/db/SqliteWeaponSlotRepository.h', 20, 46, 'no acquisition API and existing-before whole-instance move contract'),
    ('src/db/SqliteDatabase.cpp', 214, 236, 'borrowed common/witness writer construction; no population'),
    ('src/main.cpp', 55, 78, 'explicit schema install CLI; no donor/acquisition population'),
    ('src/core/Application.cpp', 7564, 7590, 'actual hosted normal C24 same-DB full-material consumer'),
    ('src/game/SharedTaiwanOwnedBagMoveSource.cpp', 38, 92, 'selected complete-before bank/material alias guards; partial planner'),
    ('src/game/SharedTaiwanOwnedBagMoveSource.cpp', 206, 282, 'selected NormalEntryOwner guarded before/actual transaction; full class retained in whole source'),
    ('src/db/SqliteOwnedInventoryRepository.cpp', 120, 145, 'identity preservation and before-mint permanent registry boundary'),
    ('src/db/SqliteNativeEquipmentSnapshotRepository.h', 25, 63, 'external complete issuer/receipt delivery witness contract'),
    ('src/db/NativeItemDefinitionObservation.h', 9, 44, 'historical396/native key observation distinct from common identity/acquisition'),
]
assert len(specs) == 18
cuts = []
for rel, first, last, scope in specs:
    lines = wholes[rel].splitlines(keepends=True)
    assert 1 <= first <= last <= len(lines), (rel, first, last, len(lines))
    b = b''.join(lines[first-1:last])
    retained = 'cuts/' + Path(rel).stem + '-' + str(first) + '-' + str(last) + '.source'
    put(retained, b)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_head=HEAD, first_line=first, last_line=last, whole_sha256=sha(wholes[rel]), scope=scope))
jout('cuts.json', cuts)
jout('donor-source-contract-frontier.json', dict(selected_existing_persisted20_producers=[
    dict(source='private_armor_transfer_20261002.py', operation='instance -> fixture_rows -> seed_migrated_clone',
         material='packed native-key/selector plus16 zero bytes and explicit test dimension bytes', origin='CUSTOM_TEST_NOT_NATIVE'),
    dict(source='run_private_owned_companions.py', operation='seed_weapon_transfers',
         material='two literal20 operands and explicit scalar slots', origin='CUSTOM_TEST_NOT_NATIVE'),
    dict(source='private_weapon_rejection_20260927.py', operation='restricted_metadata_hex -> legacy metadata insert',
         material='caller-supplied20 checked against historical396 name/restriction', origin='CUSTOM_TEST_NOT_NATIVE')],
    genuine_issuer_qualified=False, all_are_private_clone_sources_not_ordinary_Main_grants=True,
    actual_main_normal_C24='requires existing common inventory + native1215 same-DB before tuple; consumes, does not install/populate',
    selected_repository_API='load/plan/move preserves existing opaque20/origin/provenance; no acquisition API',
    NativeWorldEntry='version-keyed raw entry delivery witness, not owned inventory/full25 acquisition origin',
    earliest_required_source='replace synthetic seed/input with actual authoritative same-event original full25 and full cache+DA witness tied to already-owned stable common definition/instance/original acquisition, before global registry mint',
    no_original_acquisition_from_label_or_definition=True, no_global_absence=True, no_new_factory=True,
    next_actual_location='upstream actual acquisition/save exporter that supplies donor full25/original witness/common binding; selected seed functions are exclusion boundary, not qualified integration source'))
put('REPORT.md', b'''PASS bounded genuine donor material source frontier357; zero authority credit.

Prior356A44/1006244B was verified member by member in place, unchanged. Twenty-four
immutable published b5a2afd1364c50613525f07757ba31350dad9882 whole current-repository
sources and eighteen exact line cuts are retained. Working digests are separate;
concurrent Application callback changes are not relabeled the immutable source.
Every harness below was read only as text; no import/SQL/native/codec/runtime ran.

New upstream closure, beyond already-known2A/trade settlement: actual legacy20
population declarations were found in three current private-clone source writers.
Armor instance56..62 packs key/selector plus16 zero bytes then test dimension
bytes; fixture_rows feeds seed_migrated_clone247..272. ORIGIN at36 is explicitly
CUSTOM_TEST_NOT_NATIVE. The clone guard requires isolated test ownership and
deletes/replaces diagnostic scalar and legacy overlay rows; it writes no common
stable instance/acquisition registry or genuine full25/native1215 witness.
run_private_owned_companions60..80 writes two literal20 weapon operands, explicit
scalar slots and synthetic provenance/CUSTOM0046. Restricted weapon writer96..124
accepts caller hex20, checks width/key/TWP bits plus historical396 restriction
text and writes it as CUSTOM_TEST_NOT_NATIVE. A catalog check does not turn that
hex operand into native acquired instance authority. These actual declarations
explain how admitted opaque20 can reach the legacy donor population; they are
not genuine current-save/native capture material or ordinary Main grants.

Armor/weapon repositories expose existing saved reads and whole-instance moves;
headers explicitly deny acquisition API. Move operations preserve supplied20,
origin/provenance/physical revisions. They can consume labels such as native
capture verified, but selected actual seed sources do not supply a same-event
native capture/acquisition binding. No stored row or actual save was accessed,
and no global statement about other possible producers follows from this scope.

SqliteDatabase constructs borrowed common inventory and native snapshot writers,
not source populations. Main explicit snapshot schema install is structural.
Actual Main normal C24 at7564 requires already-existing same-connection common
inventory/native witness, then binds the genuine Session/movement owner. Its
planner checks full50 bank, aliases, root/pose/actor and source-qualified material;
NormalEntryOwner observes before and moves that existing population. This actual
consumer cannot supply missing initial donor rights. NativeWorldEntrySnapshot is
a separate version-keyed raw entry delivery witness; its APIs cannot synthesize
inventory/full25/cache1215 identity from entry shape or DA. Full equipment writer
requires a real external complete issuer and cannot make an acquisition from a
stored raw delivery witness. Historical396 NativeItemDefinitionObservation
expressly separates native token0 lookup from common ID/owned20/acquisition.

Concrete earliest action remains BEFORE mint143, now with exact upstream exclusion
locations: an actual authoritative acquisition/save exporter must replace the
synthetic seed/input, supplying same-event original full25 plus full50x24 cache
and independent DA witness, bound to genuine stable common definition/instance/
immutable original acquisition. No public adapter can infer that tuple from the
selected label, literal20, historical restriction or receipt syntax. Once it is
qualified, its owner must participate in the real multi-owner settlement boundary
from356 rather than two single-owner replacements or postcommit remint. This
audit does not repeat or recredit the2A offer method or existing trade seam.

No implementation is qualified from these selected producers. No guessed IDs,
random acquisition, zero prefix, grant/importer/new factory, SQL execution or
native acceptance was added. Same-owner C24 CUSTOM0094 and legacy overlay0066/
0046 stay separate from common0092 identity and original server authority. Full
gameplay denominator/authority/route credits remain unknown/zero. Owner instructed
stop at end of357: only this audit and separately requested callback proposal/
implementation review are in scope; no358 or scope extension will be started.
''')
jout('capture-success.json', dict(status='PASS bounded source audit357', head=HEAD,
    whole_sources=24, exact_cuts=18, prior356A_members=44, prior356A_bytes=1006244,
    genuine_donor_qualified=False, new_authority_credits=0, tracked_edits=0,
    executions_target_SQL_API_native_codec_parser_build_compiler_tests_runtime=0,
    successful_helper='capture_genuine_donor_material357.py', successful_runs=1, failures=[]))
for ref in refs:
    rel = str(Path(ref['actual_path']).relative_to(S)).replace('\\', '/')
    assert (O / ref['retained']).read_bytes() == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
members = []
for p in sorted(O.rglob('*')):
    if p.is_file():
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
jout('SEAL.json', dict(status='PASS bounded source audit357', head=HEAD,
    member_count=len(members), member_bytes=sum(m['bytes'] for m in members), members=members))
final = json.loads((O / 'SEAL.json').read_bytes())
assert final['member_count'] == len(final['members']) and final['member_bytes'] == sum(m['bytes'] for m in final['members'])
for m in final['members']:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
hb = Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(status='PASS', member_count=final['member_count'], member_bytes=final['member_bytes'],
    seal_bytes=(O / 'SEAL.json').stat().st_size, seal_sha256=sha((O / 'SEAL.json').read_bytes()),
    helper_bytes=len(hb), helper_sha256=sha(hb))))
