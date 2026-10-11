# Current live memory recovery — 2026-09-27

## Actual execution and scope

Owner requested live-memory investigation during the collect-quest implementation
round. `current_live_memory_catalog_20260927.py` starts the existing exact-port
private copy of the current unpacked client on the existing hidden desktop
runner. It reads with `QUERY_LIMITED_INFORMATION | VM_READ`. It performs no
process memory writes, injection, screenshot, desktop switch, account login,
server fixture injection or external connection. Source-qualified data only is
retained; arbitrary process memory is not saved.

Final successful run:
`artifacts/research/live-memory-catalog-20260927-07/memory-result.json`.
Worker desktop `God2Lab-24228-546027968`; input desktop remained `Default`.
Owned client was closed. Source client, private client and formal config hashes
were unchanged. Formal service PID13112 remained running with executable SHA
`a6e9202d6b7d7649af8c8dbb814fe316c3a6ddc288141e7edf050b633420b93f`.

Earlier attempts corrected reader assumptions: the full quest title includes
`[新手任務]`; empty NPC names are valid source entries; EnyName names start at
record+2, not record+0. These were investigation tool errors, not client patches.
Runs06 and07 successfully read all final static catalogs; run07 also qualified
the four quests' twenty dialogue strings in actual memory.

## Positive memory findings

| Catalog | Actual memory qualification | Interpretation |
|---|---|---|
| Mission_data | 418 records ×40 bytes, all names/counts and 2,014 pointed-to descriptions compared to pinned source | Loaded display catalog; no prerequisites or reward authority inferred from pointer layout |
| NPCAppearData | 4,043 source records read as94 bytes by exact sparse ID; source names compared | Current loaded NPC definitions, not world spawn records |
| EnyName | 7,815 allocated26-byte records, all source names compared;96 descriptor groups/counts/pointers independently matched | Display lookup occurrences; includes pet area0, not7,815 unique wild monsters |
| NPCMissionMessage | Twenty original offer/incomplete/completion/idle strings for234/236/237/238 compared byte-for-byte through actual char** | Dialogue is loaded; inferred state-to-text joins are still custom |

Three independent NPC source IDs2936/2938/2939 derive the same catalog owner
`C=005E053C`. `C+D2AC0/D2AC4` independently validates the418-row quest root.
Heap addresses vary by process and are preserved per run rather than hardcoded
as production authority. NPC highwater is6224; the source has4,043 definitions,
not6,224 continuous NPCs. Two valid short CSV rows1156 and3472 have only five
fields and must not be dropped by a nine-field-only scanner.

The two long Mission descriptions reproduce the native379-byte truncation:
mission60 description9 source416 bytes, mission168 description2 source380 bytes.
Original source text remains intact. This is not a discovered server rule.

## A newly qualified server-written cache

See `current-memory-catalog-layout-20260927.md` and its tool/artifact directory.
Eleven current PE/mapped-image spans match; eight original F8 writer executions
passed normal and optimized checks with complete94-byte after-state comparison.

NPC records' first28 bytes are source name/appearance fields. The remaining66
bytes include fields written by S2C F8 through world dispatcher46AAD6 and
45BA30. Four consecutive DWORDs at+20hex are interpreted by the client as a
string; they are not four attack/defense numbers. +1D is displayed as level,
+1E is a signed display modifier; +55/+59 remain opaque. All4,043 observed
pre-login tails in the final live run were zero. That observation proves only
the captured state, not a universal absence or meaningful zero combat values.

World NPC/monster pools are separate from the catalog. Native coordinates,
facing and instance identities in those pools are received state. This read did
not capture an original server's world session and does not recover full native
spawn, encounter, quest transition, reward or four combat-stat authority.

## Implementation delivered alongside the memory investigation

`CUSTOM-0051`: `InferredQuestRules.h` and `FruitVillageQuestRules.h` implement
four immutable source-backed collect recipes, explicit provenance, prerequisite
and version checks, material-debit plans, once-only completion, EXP/reputation
reward plans and full read-set revalidation. Historical wiki rewards/levels and
missing policies are explicitly adopted custom fields. The two standalone
x64 Release CTest targets passed; separate Win32 tests passed103 and94 checks.

These are **IMPLEMENTED_NOT_ROUTED**: no Application handler, transactional
storage adapter, material acquisition, NPC spawning or current-client quest
completion has been added. They are not four completed playable quests. No
existing saved account, character, inventory or formal NPC policy was modified.

## Next concrete memory work

1. Read the initialized world from the current application+440 in an isolated
   own-server session and verify its catalog-owner binding before reading the
  256-entry NPC/monster pools. Tag all own-server-issued records by provenance.
2. Trace original F8 producer/layout boundaries and opaque+55/+59 consumers;
   compare before/after cache records rather than calling raw integers stats.
3. Follow selected monster runtime actors back to1C/71 receive inputs and actual
   four combat-stat stores; keep source definitions, received state and formula
   authority distinct.
4. Add the collect quest transaction adapter and authenticated dialogue route,
   then qualify real-client journal/reward/relogin behavior before activation.

Overall engineering planning estimate remains11%; this is not measured packet
coverage or playable completion. Full original NPC/monster placements and
original quest gameplay acceptance remain open.
