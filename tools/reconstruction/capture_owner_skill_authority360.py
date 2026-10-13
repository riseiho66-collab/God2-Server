from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
HEAD = 'a4ca93050ec0416325b3d83abf54552a9f244af3'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(r, b):
    p = O / r
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def js(r, v):
    put(r, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

I = O.parent / 'round359-common-skill-definition-independent-source-review'
sb = (I / 'SEAL.json').read_bytes()
v = json.loads(sb)
assert sha(sb) == 'fe22e4b880ab2a30ce279cf932ecb105940f805058beff42ef2f8f7d15b8cbb7'
assert v['member_count'] == len(v['members']) == 52
assert type(v['member_bytes']) is int and v['member_bytes'] == sum(m['bytes'] for m in v['members']) == 2979732
for m in v['members']:
    b = (I / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
js('prior-individual-verification.json', dict(root=I.as_posix(), seal_sha256=sha(sb), member_count=52,
    member_bytes=2979732, members=v['members'], verified_in_place=True))

files = ['src/core/Application.cpp', 'src/game/ShunyingSanshazhan.h', 'src/game/ThousandBulls.h',
    'src/handlers/RecoveredBattleService.h', 'src/handlers/RecoveredBattleService.cpp',
    'src/game/Battle.h', 'src/game/Battle.cpp', 'src/game/BattleCheckpointCodec.h',
    'src/game/BattleCheckpointCodec.cpp', 'src/db/SqliteCompanionRepository.h',
    'src/db/SqliteCompanionRepository.cpp', 'src/game/SharedTaiwanOwnedDeitySkillSource.h',
    'src/game/SharedTaiwanOwnedDeitySkillSource.cpp', 'src/cn/world/CnBattleSkillSelectionSource.h',
    'src/cn/world/CnBattleSkillSelectionSource.cpp', 'src/cn/world/SharedBattleSkillPublication.h',
    'src/cn/world/SharedBattleSkillPublication.cpp', 'src/cn/world/SharedNativeBattleCommandData.h',
    'src/cn/world/SharedNativeBattleCommandData.cpp', 'src/cn/world/SharedWorldGameplay.cpp',
    'scripts/gameplay/combat.lua', 'scripts/gameplay/combat_health64.lua']
data = {}
refs = []
for rel in files:
    b = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    data[rel] = b
    retained = 'published/' + rel
    put(retained, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_head=HEAD, source_state='immutable published whole source; not a current candidate'))
assert len(refs) == 22
js('source-references.json', refs)
working = (S / 'src/core/Application.cpp').read_bytes()
js('working-Application-observation.json', dict(actual_path=(S / 'src/core/Application.cpp').as_posix(),
    bytes=len(working), sha256=sha(working), published_head=HEAD,
    equal_published=working == data['src/core/Application.cpp'],
    disposition='one read-only working observation; independent current implementation may change later'))

specs = [('src/core/Application.cpp', 6070, 6123), ('src/core/Application.cpp', 6138, 6230),
    ('src/core/Application.cpp', 6306, 6336), ('src/core/Application.cpp', 6458, 6473),
    ('src/game/ShunyingSanshazhan.h', 5, 37), ('src/game/ThousandBulls.h', 5, 32),
    ('src/handlers/RecoveredBattleService.cpp', 319, 350),
    ('src/handlers/RecoveredBattleService.cpp', 438, 487), ('src/game/Battle.cpp', 128, 194),
    ('src/db/SqliteCompanionRepository.cpp', 97, 108),
    ('src/db/SqliteCompanionRepository.cpp', 270, 373),
    ('src/db/SqliteCompanionRepository.cpp', 405, 435),
    ('src/game/SharedTaiwanOwnedDeitySkillSource.cpp', 47, 94),
    ('src/cn/world/CnBattleSkillSelectionSource.cpp', 9, 19),
    ('src/cn/world/CnBattleSkillSelectionSource.cpp', 87, 124),
    ('src/cn/world/SharedNativeBattleCommandData.cpp', 114, 135),
    ('src/cn/world/SharedBattleSkillPublication.cpp', 174, 198),
    ('src/cn/world/SharedWorldGameplay.cpp', 141, 150)]
cuts = []
for i, (rel, start, end) in enumerate(specs):
    lines = data[rel].splitlines(keepends=True)
    assert 1 <= start <= end <= len(lines)
    b = b''.join(lines[start - 1:end])
    retained = 'cuts/%02d-%s-L%d-L%d.txt' % (i, Path(rel).name, start, end)
    put(retained, b)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_head=HEAD, first_line=start, last_line=end, boundary='selected excerpt; whole method source retained'))
js('source-cuts.json', cuts)
js('typed-frontier.json', dict(status='bounded source authority audit; no implementation',
    owner_skills=[dict(kind=0, id=126, policy='CUSTOM-0058', physical_power_percent=300, mp_cost=20,
        max_targets=3, source='ShunyingSanshazhan::owned_action'),
        dict(kind=0, id=150, policy='CUSTOM-0059', physical_power_percent=1000, mp_cost=100,
        max_targets=14, source='ThousandBulls::owned_action', all_living_opponents=True)],
    ownership='saved selected owned deity skill rows; catalog/request membership is insufficient',
    missing_cn=['actual custom-client definition/list incarnation for0/126 and0/150',
        'concrete hosted CN owner connecting saved learned readset and real actor/Session epochs',
        'genuine committed learned event/revision and original native87 flags/order supplier if publication is used',
        'qualified CN custom render/target/selection adapter; original453 cannot be fabricated'],
    native_route_credits=0, native_method_credits=0, target_execution=False))
put('REPORT.md', b'''# Round360 common owner skill authority frontier

Bounded source audit at published a4ca93050ec0416325b3d83abf54552a9f244af3. Twenty-two whole sources and eighteen scoped cuts are immutable HEAD evidence. Working Application is a separately labelled single digest observation, never asserted equal to a later candidate. Prior I35952/2979732 was verified member by member without modification. Source/hash/git reads only; no C++ API, SQL, DB, resource parser/codec, native execution, compiler, build or tests.

The two owner skills already have concrete shared rules: ShunyingSanshazhan::owned_action is physical300%, one20MP cost, max3 targets; ThousandBulls::owned_action is physical1000%, one100MP cost and every living opponent up to14. These are CUSTOM-0058/0059 owner rules, not original client formulas. The old trial Shunying authorize deliberately accepts its supplied trial action; factoring a common owner spec must preserve that trial override. Presentation clones/four phase losses do not create actors or independently apply damage/charge MP. Original full110 source metadata is a presentation/client profile, not a new learned grant.

Actual App6113..6229 reads selected_deity_has_skill before authorizing the owned actions; this is inside the existing diagnostic_combat encounter/policy branch. It is not a concrete CN battle owner. The stronger existing supplier is load_selected_deity_skill/selected_deity_skill_current plus SharedTaiwanOwnedDeitySkillSource::Observation: exact saved selection/deity/skill bytes and revision, exact catalog110, real presence/Session/phase/battle-generation scope and observer fences. The simple bootstrap boolean is not that retained live readset. SqliteCompanionRepository::store_deity preserves supplied snapshots/provenance; a supplied import record does not recover an acquisition or learning rule.

RecoveredBattleService accepts only the bound trusted policy key, authenticates request actor/context, validates sequence/masks and special all-living target domain. Battle::act validates controller/life/revision and distinct living enemies, checks available MP before the rule, stages all target damage/RNG, subtracts MP once, prepares exact reply, then commits its in-memory snapshot. Service uses a staged Battle, prepares reply/counter first, invokes existing commit/checkpoint callbacks, then publishes bound Battle/action latch. Application's saved resource/checkpoint path remains the inherited diagnostic policy. Current Lua combat is labelled CUSTOM-0006; the shared metadata provider is not a recovered damage formula or automatic MP debit. This audit adds no timer/poison rule.

Concrete CN boundary: CnBattleSkillSelectionSource::resolve/current/selected retain an actual native list snapshot and require its full definition to equal CnSharedSkillCatalog::expected_source original CN raw110 and original source offset/digest. Original CN453 has neither kind0/id126 nor0/150. Common descriptor availability cannot produce those original rows or native Current. SharedNativeBattleCommandData likewise retains exact native selection when configured; the alternative catalog lookup still requires external common learned/actor authority. SharedBattleSkillPublication requires actual original87 records/flags/order, actual committed learned event/revision, exact native catalog and concrete WorldOwner's store/recipient/battle/list/resource qualification. SharedWorldGameplay only installs/binds an already supplied source. No Application construction or concrete owner/supplier for those two custom CN skills was found in this bounded actual callsite search; this is not a global absence claim.

Smallest supported implementation is to make the existing two owner specs a single common truth and expose them to the common definition result while preserving TW/trial/checkpoint behavior. That does not close the CN acquisition/selection/output route. The next genuine supplier must bind the actual saved learned readset to the real CN actor/list incarnation and explicit custom client definition/render/target adapter, with a real event/revision/flags source if original87 publication is selected. Do not manufacture OriginalCN, native Current, a learned grant, generic WorldOwner, remint, or zero/default wire fields. Independent candidate review will be separate after authorized changes freeze. Native method/full-route/acceptance credits remain0.
''')
js('capture-complete.json', dict(status='PASS bounded audit', source_head=HEAD,
    whole_count=len(refs), cut_count=len(cuts), prior_members=52, prior_bytes=2979732,
    tracked_edits=False, target_execution=False, native_route_credit=0))
members = []
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name != 'SEAL.json':
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
total = sum(m['bytes'] for m in members)
assert type(total) is int
js('SEAL.json', dict(status='PASS bounded audit', member_count=len(members), member_bytes=total, members=members))
for m in members:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
sb = (O / 'SEAL.json').read_bytes()
hb = Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(member_count=len(members), member_bytes=total, seal_bytes=len(sb), seal_sha256=sha(sb),
    helper_bytes=len(hb), helper_sha256=sha(hb))))
