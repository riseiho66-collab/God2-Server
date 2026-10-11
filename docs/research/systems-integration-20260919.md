# Five-lane systems integration, 2026-09-19

Owner request: delegate more concrete game-system work and internal black-box
verification, preserving C++20/Lua architecture and current-client evidence.
Five workers completed and were closed. No agent remains assigned to this batch.

## Delivered boundaries

| Lane | Deliverable | Not established |
| --- | --- | --- |
| NPC | Original catalog, ROMZ/ROM resource load, 120 decoded image buffers, real pool allocation and scalar writes through CC690 | Scene projection, rendered NPC, live placement acceptance |
| Inventory | RecoveredInventory: bounded S2C41 decoder and 50-slot occupancy-clear projection; native populate/clear/idempotence | Starting inventory, item grants, effects, complete equipment refresh |
| Quest | RecoveredQuestSync: DB subtype 4/5 decoder, 15-slot empty-journal projection, original native consumer | Quest eligibility, progression, completion, rewards, open UI |
| Combat | RecoveredBattleCommand: current 17-byte C2S35 basic-attack structural decoder | Authoritative battle/turn/ownership checks, skill effects, damage |
| Teleport | Strict provenance-preserving importer, five retained coordinate edges, current S2C61 scalar oracle | Cross-build coordinate equivalence and live transitions; zero runtime-eligible edges |

Inventory and quest empty projections require an independently authoritative
empty state. Missing database rows are NOT such proof. These projections are
not automatically emitted at world entry. Combat parsing does not authorize
mutation. Historical NPC area15/scene7 is not initial area2/scene15.

## Parent integration

- Added RecoveredWorldFrame for the existing zero-seed laboratory connection.
  World-ready and movement decoders share this bounded transport implementation.
  This is not fresh-session general crypto recovery or an opcode grammar.
- Original queue/encoder equality is tested through the 256-byte key wrap and
  logical lengths 1..2560. Permanent oracle: wire 0600A3A3FDD5 decodes in the
  original client to full plaintext 0600A60000D8, logical A60000.
- Standalone frame tests cover every logical size, reversible round trips,
  checksum/truncation rejection and 4096 arbitrary bounded inputs.
- Registered frame, inventory, quest and battle fixtures in CMake/CTest.
  Inventory/quest assertions explicitly remain enabled under Release/NDEBUG.
- Audited the NPC oracle's low page: only three exact native FS:[0] SEH
  instructions may access it. Chain restoration and rejection of a genuine
  non-SEH null load are tested. No unrestricted null page masks an error.
- No DB schema, Lua gameplay policy, default runtime activation or guessed
  combat/stat/quest rule was introduced.

## Verification

Full Release build passed. Existing Session.cpp getenv C4996 warnings remain.
Core CTest: 30/30 passed. The unrelated artifact_vault, runtime_evidence,
gate_review, counter_resolution and runtime_environment suites were excluded
from this focused run, not reported as tested.

Parent reran 38 Python tests across current_npc_spawn, recover_teleports,
current_inventory, current_quest_sync, current_battle_command and
current_world_frame; all passed. Native slices use documented synthetic
environments and are not live original-client E2E acceptance.

After the integrated Release build, another 27 tests passed across
current_world_ready_builder, current_movement, current_periodic_tick,
recovered_world_entry_server, recovered_movement_server and
recovered_periodic_tick_server. These cover original native builders plus our
own loopback server, including fragmentation/coalescing, invalid state,
transaction failure, restart persistence and movement-ring wrap. Total for
these two disjoint Python selections: 65/65 passed.

See each lane's current-*-20260919 evidence document for exact native addresses,
image hashes, allowed adapters and unqualified boundaries.

## Remaining playable frontier

The previously reported 10% overall figure remains a rough planning estimate,
not measured original-client acceptance or a test-pass percentage. This batch
does not establish a rendered, normally playable world. Next work must qualify
real scene/resource state, authoritative inventory/quest/battle state, and the
actual client-service workflow before enabling their corresponding mutations.
Do not reinterpret structural protocol tests as recovered game rules.
