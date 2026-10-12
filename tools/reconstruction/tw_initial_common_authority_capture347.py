"""Source bytes, hashes and rg text only. Never import or execute target modules."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent / 'successful-capture'
OUT.mkdir(exist_ok=False)
BASE = OUT.parent.parent

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(name, data):
    p = OUT / name
    with p.open('xb') as f:
        f.write(data)

def js(name, value):
    put(name, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))

def command(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, check=False)
    if p.returncode not in (0, 1):
        raise RuntimeError(str(args) + ': ' + p.stderr.decode('utf-8', errors='replace'))
    return p.returncode, p.stdout, p.stderr

head = command(['git', 'rev-parse', 'HEAD'])[1].decode('ascii').strip()
queries = [
    ('writer-calls', ['rg','-n','owned_item_instances|acquisition_record|replace_from_issuer\\(|store_deity\\(|store_pet1\\(|store_pet2\\(','src','tools/operations','--glob','*.cpp','--glob','*.h','--glob','*.py']),
    ('authority-paths', ['rg','-n','complete_town_guide|provision_town_reward_slot|create_owned_snapshot|owned_inventory_storage|owned_inventory_writer|native_declared_policy','src/core/Application.cpp','src/db','src/handlers','src/game']),
    ('import-boundaries', ['rg','-n','CREATE TABLE|INSERT INTO|def import_catalog|AUTHORITY=|player_instances_created|inventory_grants|CURRENT_SOURCE_SHA','tools/strike_lab/import_native_weapons.py','tools/strike_lab/import_native_armor_20261002.py','tools/strike_lab/import_native_map_items.py']),
    ('config-boundaries', ['rg','-n','owned_whole_bag_moves_enabled|diagnostic_town_quest_progress|owned_supply_enabled','src/core/Config.h','src/core/Config.cpp']),
]
query_receipts = []
for name, args in queries:
    rc, stdout, stderr = command(args)
    put(name + '.txt', stdout)
    query_receipts.append(dict(name=name, argv=args, returncode=rc, bytes=len(stdout), sha256=sha(stdout), stderr=stderr.decode('utf-8', errors='replace')))
js('search-coverage.json', query_receipts)

specs = {
    'src/db/OwnedInventoryRepository.h': [(1,61)],
    'src/db/SqliteOwnedInventoryRepository.h': [(12,74)],
    'src/db/SqliteOwnedInventoryRepository.cpp': [(29,60),(112,199),(214,247),(285,311)],
    'src/db/SqliteOwnedEquipmentTransaction.h': [(10,54)],
    'src/db/SqliteOwnedEquipmentTransaction.cpp': [(36,89)],
    'src/db/SqliteOwnedCharacterCreation.cpp': [(1,71)],
    'src/db/SqliteRecoveredCharacterRepository.h': [(61,86)],
    'src/db/SqliteRecoveredCharacterRepository.cpp': [(115,142),(171,232)],
    'src/db/SqliteDatabase.cpp': [(216,224),(238,249),(263,296)],
    'src/db/NativeEquipmentSnapshotRepository.h': [(1,52)],
    'src/db/NativeItemDefinitionObservation.h': [(1,44)],
    'src/db/NativeMapItemCatalog.h': [(1,43)],
    'src/db/NativeMapItemCatalog.cpp': [(31,77)],
    'src/core/Application.cpp': [(2426,2435),(4353,4377),(5551,5605),(5607,5664),(7267,7279)],
    'src/core/Config.h': [(28,30),(90,96)],
    'src/core/Config.cpp': [(1,38),(280,285),(644,645),(703,711)],
    'src/handlers/DiagnosticQuestConversation.h': [(1,129)],
    'src/handlers/DiagnosticSupplyService.cpp': [(8,83)],
    'src/handlers/RecoveredFruitQuests.h': [(12,23),(78,91)],
    'src/protocol/RecoveredQuestAction.h': [(9,18)],
    'src/protocol/RecoveredNpcInteraction.h': [(8,18)],
    'src/protocol/RecoveredInventory.h': [(9,35)],
    'src/scripting/LuaEngine.cpp': [(955,973)],
    'scripts/gameplay/town_guide.lua': [(1,19)],
    'tools/strike_lab/import_native_weapons.py': [(1,46),(127,142)],
    'tools/strike_lab/import_native_armor_20261002.py': [(1,48),(124,139)],
    'tools/strike_lab/import_native_map_items.py': [(1,47),(102,119)],
}
sources, cuts = [], []
for relative, ranges in specs.items():
    data = (ROOT / relative).read_bytes()
    lines = data.splitlines(keepends=True)
    sources.append(dict(path=relative, bytes=len(data), sha256=sha(data), line_count=len(lines), snapshot='working bytes at head '+head))
    for lo, hi in ranges:
        if not (1 <= lo <= hi <= len(lines)):
            raise ValueError((relative, lo, hi, len(lines)))
        raw = b''.join(lines[lo-1:hi])
        cutname = relative.replace('/', '__') + '.L' + str(lo) + '-' + str(hi) + '.cut'
        put(cutname, raw)
        cuts.append(dict(source=relative, first_line=lo, last_line=hi, first_byte=sum(map(len,lines[:lo-1])), end_byte=sum(map(len,lines[:hi])), file=cutname, bytes=len(raw), sha256=sha(raw)))
js('source-references.json', dict(head_start=head, sources=sources, cuts=cuts))
core = BASE / 'round346-owned-mutation-receipt-implementation'
seal_data = (core / 'SEAL.json').read_bytes()
seal = json.loads(seal_data)
verified = []
for item in seal['members']:
    b = (core / item['name']).read_bytes()
    assert len(b) == item['bytes'] and sha(b) == item['sha256'], item['name']
    verified.append(dict(name=item['name'], bytes=len(b), sha256=sha(b)))
assert len(verified) == seal['member_count'] and sum(x['bytes'] for x in verified) == seal['total_bytes']
pins = []
for path in ['src/game/SharedTaiwanOwnedBagMoveSource.h','src/game/SharedTaiwanOwnedBagMoveSource.cpp','src/handlers/RecoveredMovementService.h','src/handlers/RecoveredMovementService.cpp','src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp']:
    b = (ROOT / path).read_bytes()
    pins.append(dict(path=path, bytes=len(b), sha256=sha(b)))
for item in seal['frozen_sources']:
    pin = next(x for x in pins if x['path'] == item['path'])
    assert pin['bytes'] == item['after_bytes'] and pin['sha256'] == item['after_sha256']
for source in sources:
    current = (ROOT / source['path']).read_bytes()
    assert len(current) == source['bytes'] and sha(current) == source['sha256'], source['path']
js('custody-verification.json', dict(head_start=head, head_end=command(['git','rev-parse','HEAD'])[1].decode('ascii').strip(), core_seal_sha256=sha(seal_data), verified_members=verified, member_count=len(verified), total_bytes=sum(x['bytes'] for x in verified), current_seven_source_pins=pins, all_cut_sources_unchanged_during_capture=True, target_execution=False, SQL_execution=False, repository_writes=False))
print(json.dumps(dict(sources=len(sources), cuts=len(cuts), head=head)))
