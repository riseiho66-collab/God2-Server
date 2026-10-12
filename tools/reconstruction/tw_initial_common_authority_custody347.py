"""Append source-only boundary cuts, rationale, then derive individual-member seal."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(name, b):
    with (OUT / name).open('xb') as f:
        f.write(b)

def js(name, value):
    put(name, (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode())

extras = []
for relative,lo,hi in [('src/db/SqliteOwnedPkRoomRepository.cpp',73,101),('src/db/SqliteOwnedEquipmentEntryTransaction.cpp',85,105),('src/db/SqliteCompanionRepository.h',127,141)]:
    data=(ROOT/relative).read_bytes()
    lines=data.splitlines(keepends=True)
    assert 1<=lo<=hi<=len(lines)
    b=b''.join(lines[lo-1:hi])
    name='supplement-'+relative.replace('/','__')+'.L'+str(lo)+'-'+str(hi)+'.cut'
    put(name,b)
    extras.append(dict(path=relative,source_bytes=len(data),source_sha256=sha(data),first_line=lo,last_line=hi,first_byte=sum(map(len,lines[:lo-1])),end_byte=sum(map(len,lines[:hi])),file=name,bytes=len(b),sha256=sha(b)))
js('supplement-source-references.json',extras)
captured=json.loads((OUT/'successful-capture/source-references.json').read_bytes())
current=json.loads((OUT/'successful-capture/custody-verification.json').read_bytes())
for row in captured['sources']:
    b=(ROOT/row['path']).read_bytes()
    assert len(b)==row['bytes'] and sha(b)==row['sha256'],row['path']
head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
status=subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,check=True).stdout
put('source-state-final.txt',('HEAD '+head+'\n').encode()+status)
js('route-frontier.json',dict(head=head,source_scope='Current repository source text only, historical provenance explicit; no retired resources.',native_complete_routes=0,new_format_credits=0,implementation_proposed=False,route=dict(direction='TW C2S37 NPC interaction -> C2S85 confirmation -> S2C DB journal +41 scalar occupancy',phase=['CharacterSelected','InWorld'],variant='existing diagnostic_town_quest_progress / CUSTOM0021+0022',authority='server-owned custom Lua transition + private bound conversation + expected saved quest/slot',storage='diagnostic_town_guide_progress / diagnostic_inventory_slots / diagnostic_town_guide_reward, one transaction',reply='prebuilt original RecoveredQuestSync + RecoveredInventory scalar frames; no full25/native1215 producer'),earliest_missing_before_stage143=['authority-qualified common definition_key mapping, independent of native key/token5','authentic acquisition issuer linking event, common owner, globally unused instance ID, quantity, stackability and immutable acquisition receipt','same-event authentic versioned item20 and full25 source alias, separate from scalar item/count','same-owner actual complete native1215 producer with pose/actor/source provenance'],independent_next_lead=dict(existing_receipt='SqliteRecoveredCharacterRepository.cpp:225 diagnostic_town_guide_reward',existing_definition_data='NativeMapItemCatalog.h:25 and import_native_map_items.py:102 historical SOURCE_DISPLAY_ONLY',necessary_evidence='An actual original-server saved acquisition/import producer or explicitly separately authorized server policy connecting that event receipt to common instance/definition and original material source. Current display importer and receipt syntax cannot supply it.',client_recovery_limit='Client consumers may qualify copy/layout/UI semantics; original server reward entitlement and common identity derivation are not established by those consumers.'),coverage_limits='Exact named repository/config/import/creation/reward and matched writer calls only; no global absence claim. Trusted companion import APIs and PK serialization are separate source boundaries, not the common initial bank issuer.'))
report='''# Round347 bounded initial common authority source audit

No closed original-native initial definition/instance/acquisition supplier was found in the explicitly searched current paths. No implementation is proposed from this evidence. The concrete additional authority lead is the existing town-guide reward transaction, which is CUSTOM0021/0022 scalar storage and remains separate from common owned instances and native material.

Snapshot: HEAD 8431708cd2654e419e8a1409f74bc512bc992016, as read by the successful helper; earlier interactive searches were at f5ab47fa8e55ff8c7438284caa23f61c26ca0efe while round346 source publication was pending. Immutable source hashes and exact byte/line boundaries are in successful-capture/source-references.json. The seven current346 source pins are in successful-capture/custody-verification.json; all four core files equal the immutable346 core seal, whose25 individual members/269040B were independently verified. This package never writes tracked sources.

The concrete route is TW C37 NPC interaction -> C85 confirmation -> journal DB and scalar41 reply. Application.cpp:5551..5564 explicitly gates diagnostic config, absence of an existing journal, phase CharacterSelected/InWorld, single record or the selected85+37 pair; native-placement-only mode can reject this diagnostic NPC route. Application.cpp:5576..5598 checks saved movement area2/scene4, custom NPC vicinity, saved progress and the explicitly owned empty slot0 before opening a bound conversation. LuaEngine.cpp:955..973 selects gameplay/town_guide.lua; its whole19-line source labels the stage transition CUSTOM0021 and performs no grants itself. Application.cpp:5607..5664 checks saved location/pending state and the actual bound request/context, prebuilds journal and41 bytes, then calls complete_town_guide through consume_after_commit. DiagnosticQuestConversation.h:81..115 identifies the custom bound confirmation checks and invokes commit before consuming the local confirmation. This is a real conditional existing server authority chain, not a new or currently enabled native route.

SqliteRecoveredCharacterRepository.cpp:200..231 is the complete acquisition transaction. It requires stage2/journal2, positive revisions, an explicitly empty scalar slot, matching source SHA, fresh owner-bound quest/slot reads, and no pending battle; it writes quest stage3, scalar item5569/count1, and the CUSTOM0022 diagnostic_town_guide_reward receipt atomically. The chosen item/count/transition are custom policy. This tuple records account-owned character, quest revision, slot and slot revision, scalar item/count/source hash. It contains no common instance ID or definition_key and no item20/full25/native1215 output. Provisioning at Application.cpp:2430..2435 is explicitly diagnostic-only; Config.h:28 default-off whole bag profile and Application.cpp:7267..7279 require already-installed custody material, with no installer/populator.

The exact pre-mint gap is not another CAS wrapper. OwnedInventoryRepository.h:21..27 requires a distinct common ID, definition_key, quantity/revision/stackability, authentic immutable acquisition receipt and aliases. SqliteOwnedInventoryRepository.cpp:29..60 validates syntax/domain/ordering and unique aliases, not entitlement. Its complete stage_replace at133..168 inserts previously unknown IDs at143 from the already supplied tuple; permanent registry uniqueness prevents duplicate/replayed identities but does not establish the receipt's origin. replace_from_issuer at169..199 and the joint replace at SqliteOwnedEquipmentTransaction.cpp:36..89 enforce guarded three-boundary full-state CAS. They accept a genuine producer rather than create one. NativeEquipmentSnapshotRepository.h:1..52 independently requires exact full1215, client/source identity, saved pose and scene actor. No guessed material is authorized.

Definition/import separation is concrete. NativeItemDefinitionObservation.h:10..18 explicitly qualifies historical149c/70a4/75c3 catalogs, not current ef297, common identity or acquisition. Its private observer at SqliteOwnedInventoryRepository.cpp:214..247 requires both exact historical weapon/armor catalogs and one unique native key; metadataDWORD0/token5 is independent of token0 key. import_native_weapons.py and import_native_armor_20261002.py install only definition tables and report zero player instances. NativeMapItemCatalog.h:25..43 and its complete read at NativeMapItemCatalog.cpp:31..67 validate two historical SPI display rows. import_native_map_items.py:102..119 installs only those sources/rows and explicitly reports inventory_grants=0/gameplay_rules=0. The real map reward5569 native key is therefore not a common definition mapping or a packed inventory instance.

Other matched apparent acquisition paths do not close the bank issuer. SqliteOwnedCharacterCreation.cpp:14..70 creates and verifies only a recovered character row; the whole71-line method/file contains no common item or material writes. CompanionRepository.h:129..141 exposes explicit trusted companion acquisition/import APIs, with no production caller found by the retained src/tools-operations call search; these are separate companion types, not a common item bank authority. SqliteOwnedPkRoomRepository.cpp:73..101 serializes an already supplied OwnedInventorySnapshot/acquisition fields into appearance provenance; it does not mint or define acquisition rules. SqliteOwnedEquipmentEntryTransaction.cpp:85..105 requires pre-existing inventory and equipment tuples, so entry synchronization cannot supply first population. The ordinary supply chain at Application.cpp:4353..4377 and DiagnosticSupplyService.cpp:8..83 consumes a pre-existing scalar under CUSTOM0050/CUSTOM0016, not an initial common supplier.

Actionable independent lead: the actual server-owned receipt at SqliteRecoveredCharacterRepository.cpp:225 is the earliest retained acquisition event in this bounded search with explicit owner/quest/slot revisions. Before using it for common mint143, obtain an actual original-server save/import producer or separately authorized server policy that maps this event to a common definition/instance identity and authentic same-event item20/full25/full1215 source. The current SOURCE_DISPLAY_ONLY importer is the nearest definition provenance input, but its missing rights/identity/material must remain explicit. Client parser/copy behavior alone cannot recover original-server reward entitlement or common ID derivation. This is a precise custody/source gap, not a global assertion that acquisition authority cannot be obtained. No new factory or gameplay activation is justified by this package.

Coverage: four retained exact rg queries cover matched common mint/acquisition/writer calls in src and tools/operations, the named authority APIs, three actual native importers and selected Config fields. Twenty-seven files provide45 exact cuts; three supplementary files preserve serialization/entry/companion boundaries. No large resource JSON, decoded resource or executable image was copied, parsed or executed. No retired corpus was accessed. Earlier failed interactive literal wildcard/path discovery and the initial overlong-range capture failure are preserved in capture-failure.txt; the exclusive corrected helper succeeded once, without overwriting original drafts. These failures support no authority conclusion.

Validation was only source readback/hash/member accounting. No target API, SQL/DB access, codec/importer, native/CRT, VM, compiler, tests, build, deployment or runtime. New native complete routes/formats/whole-route credits:0. Existing CUSTOM labels remain unchanged. All earlier seals remain immutable.
'''
put('REPORT.md',report.encode('utf-8'))
members=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name!='SEAL.json':
        b=p.read_bytes()
        members.append(dict(name=p.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
seal=dict(schema='individual-member-sha256-v1',head=head,member_count=len(members),total_bytes=sum(x['bytes'] for x in members),native_complete_routes=0,members=members)
js('SEAL.json',seal)
for member in members:
    b=(OUT/member['name']).read_bytes()
    assert len(b)==member['bytes'] and sha(b)==member['sha256']
assert sum(x['bytes'] for x in members)==seal['total_bytes']
sealbytes=(OUT/'SEAL.json').read_bytes()
print(json.dumps(dict(head=head,member_count=len(members),total_bytes=seal['total_bytes'],seal_bytes=len(sealbytes),seal_sha256=sha(sealbytes))))
