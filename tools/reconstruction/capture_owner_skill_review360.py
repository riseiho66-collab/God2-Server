from pathlib import Path
import hashlib
import json
import subprocess
import sys

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
T = A / 'round360-common-owner-skill-definition-implementation'
HEAD = 'a4ca93050ec0416325b3d83abf54552a9f244af3'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(rel, b):
    p = O / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def js(rel, v):
    put(rel, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

assert len(sys.argv) == 4, 'Require frozen T seal SHA/member count/integer bytes'
tsha, tcount, tbytes = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
prior = []
for name, sealname, pin, count, total in [
    ('round360-common-owner-skill-authority-frontier', 'SEAL.json',
     'e7bcca8b3b0230bcfe03c9c2a0a5bee422b0884eb5ab2bfaa4e1340bbb9bf122', 48, 1036127),
    ('round359-common-skill-definition-independent-source-review', 'SEAL.json',
     'fe22e4b880ab2a30ce279cf932ecb105940f805058beff42ef2f8f7d15b8cbb7', 52, 2979732),
    (T.name, 'seal.json', tsha, tcount, tbytes)]:
    folder = A / name
    b = (folder / sealname).read_bytes()
    v = json.loads(b)
    size = v.get('member_bytes', v.get('total_bytes'))
    assert sha(b) == pin and type(size) is int
    assert v['member_count'] == len(v['members']) == count
    assert size == sum(m['bytes'] for m in v['members']) == total
    for m in v['members']:
        q = folder / m['path']
        assert q.resolve().is_relative_to(folder.resolve())
        raw = q.read_bytes()
        assert len(raw) == m['bytes'] and sha(raw) == m['sha256']
    prior.append(dict(root=folder.as_posix(), seal_sha256=pin, member_count=count,
        member_bytes=total, members=v['members'], individual_in_place=True))
js('upstream-individual-verification.json', prior)

pins = json.loads((T / 'apply-success.json').read_bytes())['files']
assert len(pins) == 6
refs, current, before = [], {}, {}
for p in pins:
    rel = p['path']
    b = (S / rel).read_bytes()
    assert len(b) == p['bytes'] and sha(b) == p['sha256']
    current[rel] = b
    old = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    assert len(old) == p['before_bytes'] and sha(old) == p['before_sha256']
    before[rel] = old
    for state, raw in [('current', b), ('baseline', old)]:
        retained = state + '/' + rel
        put(retained, raw)
        refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(raw),
            sha256=sha(raw), source_state=state, baseline_head=HEAD))
frozen = ['src/core/Application.cpp', 'src/handlers/RecoveredBattleService.h',
    'src/handlers/RecoveredBattleService.cpp', 'src/game/Battle.cpp',
    'src/db/SqliteCompanionRepository.cpp', 'src/game/SharedTaiwanOwnedDeitySkillSource.cpp',
    'src/cn/world/CnBattleSkillSelectionSource.cpp', 'src/cn/world/SharedBattleSkillPublication.cpp',
    'src/core/Config.h', 'scripts/gameplay/combat.lua', 'scripts/gameplay/combat_health64.lua']
for rel in frozen:
    b = (S / rel).read_bytes()
    assert b == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S), rel
    retained = 'frozen/' + rel
    put(retained, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_state='unchanged published dependency', source_head=HEAD))
js('source-references.json', refs)

rb = (T / 'exact-edits-and-inverse.json').read_bytes()
receipt = json.loads(rb)
work = current.copy()
for e in reversed(receipt['edits']):
    rel = e['path']
    old, new = bytes.fromhex(e['old_hex']), bytes.fromhex(e['new_hex'])
    if new:
        assert work[rel].count(new) == e['count'], rel
        work[rel] = work[rel].replace(new, old)
    else:
        assert e['count'] == 1 and rel == 'src/db/NativeSkillCatalog.cpp'
        anchor = receipt['empty_deletion_inverse_anchor'].encode()
        assert work[rel].count(anchor) == 1
        work[rel] = work[rel].replace(anchor, old + anchor)
for rel, old in before.items():
    assert work[rel] == old, rel
put('exact-edits-and-inverse.json', rb)
js('six-whole-byte-inverse-proof.json', dict(baseline=HEAD, existing_count=6, new_count=0,
    exact_inverse_all=True, empty_deletion_anchored=True, pins=pins))

specs = [('src/db/SharedSkillDefinition.h', 39, 74),
    ('src/db/SharedSkillDefinition.cpp', 1, 29),
    ('src/db/SharedSkillDefinition.cpp', 1004, 1062),
    ('src/db/NativeSkillCatalog.cpp', 109, 127),
    ('src/scripting/LuaEngine.cpp', 127, 178),
    ('src/game/ShunyingSanshazhan.h', 5, 39), ('src/game/ThousandBulls.h', 5, 33)]
cuts = []
for i, (rel, first, last) in enumerate(specs):
    lines = current[rel].splitlines(keepends=True)
    assert 1 <= first <= last <= len(lines), (rel, len(lines))
    b = b''.join(lines[first - 1:last])
    retained = 'cuts/%02d-%s-L%d-L%d.txt' % (i, Path(rel).name, first, last)
    put(retained, b)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        first_line=first, last_line=last, boundary='selected excerpt; complete source retained'))
js('source-cuts.json', cuts)
put('REPORT.md', b'''# Round360 independent common owner skill definition review

PASS for the six frozen candidates. All six whole byte-inverses equal published a4ca93050ec0416325b3d83abf54552a9f244af3, including the explicit anchor for deleted native-absence line. Eleven frozen dependencies remain exact. A360 and I359 plus final implementation every member/count/integer sum/hash were verified in place. Source/hash/git/manual review only; no target C++ API, SQL, resource parser/codec, native/runtime, compiler, build or tests; no tracked edits.

OwnerSkillRule is owning definition metadata derived only from the existing CUSTOM-0058/0059 constants and traditional names. formal_owner_rule does not invoke authorize/owned_action or install Policy. Existing class changes are names-only: physical300%/20MP/three targets and1000%/100MP/all-living14 preserve all old actions, render logic, trial overrides, rules and checkpoint behavior. NativeSkillCatalog retains old actual joined reads and scope; selector validation rejects invalid int64 selectors before narrowing. Only two formal owner keys return common data when both native rows are absent. That result has empty native profiles, absent requested_native/chosen_profile and empty raw/text-source projection; no native110/source/offset is synthesized. Ordinary missing keys remain null. Present unknown profile status/qualification is unchanged, not promoted by owner metadata; all prior907 raw pins/qualifier behavior remain byte-identical through exact inverses.

Lua owns the result's copied table/string values. Owner display_name is separate from native bounded text. owner_rule source_type describes existing owner constants and explicitly keeps gameplay_authority/native_source false. No learned grant, debit, cast, native Current, native format or client adapter is inferred. Old raw/native methods, Main provider wiring, CN private catalog/source/list and old false authority fields remain untouched. This is a common owner definition provider, not a complete CN custom gameplay route.

Boundary clarification to A360: saved selected custom skill readsets can retain126/150, but SharedTaiwanOwnedDeitySkillSource::Observation is explicitly the original Taiwan-native definition path; it must not be called a formal custom or CN issuer. App bootstrap boolean/trial policy is not a retained actual issued87 event or controlled CN actor. Concrete CN definition/selection/list/learned owner bridge, custom client render/target compatibility and actual87 event/revision/flags delivery remain OPEN. Metadata presence does not manufacture those suppliers. Complete original native combat, extended HP formula/wire/client acceptance and full route credits remain separate and unclaimed.
''')
js('capture-complete.json', dict(status='PASS', baseline_head=HEAD, current_count=6, inverse_count=6,
    whole_count=len(refs), cut_count=len(cuts), frozen_count=len(frozen),
    prior_members=sum(p['member_count'] for p in prior), prior_bytes=sum(p['member_bytes'] for p in prior),
    target_execution=False, tracked_edits=False, native_route_credit=0))
for rel, b in current.items():
    assert (S / rel).read_bytes() == b
members = []
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name != 'SEAL.json':
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
total = sum(m['bytes'] for m in members)
assert type(total) is int
js('SEAL.json', dict(status='PASS', member_count=len(members), member_bytes=total, members=members))
for m in members:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
sb = (O / 'SEAL.json').read_bytes()
hb = Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(member_count=len(members), member_bytes=total, seal_bytes=len(sb), seal_sha256=sha(sb),
    helper_bytes=len(hb), helper_sha256=sha(hb))))
