# Current NPC resource groups

The actor oracle now loads the current client's NPCList into its original
message/catalog object. This removes an empty-table assumption at the resource
preload dependency; it does not yet execute the skipped preload phase or spawn
NPCs in a rendered world.

## Authority

Read both legacy references first:

- XJZ `evidence-gamedata-npc-list-v0.md` and
  `evidence-npc-visual-service-binding-v0.md` report 451 rows / 1508 bindings,
  but leave runtime group meaning unqualified.
- Classic `tools/God2.GameplayContentRecovery/OfficialClientExtractor.cs`
  preserves NPCList as grouping evidence, not world coordinates.

Current `Data2/Patch/Comm/gamedata.csvZ` is pinned to raw SHA-256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
and decoded SHA-256
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
It contains 451 rows, 251 groups and 1509 resource codes. The old count is not
copied into the current build. Area 2 / scene 15 has codes 21 and 2143.

## Native execution

The pinned image remains
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

- Original tokenizer RVA 51BE0 receives actual source lines with LF preserved.
- Original row body 5A91D..5AA3F performs scene grouping, append and resource
  quotient/remainder conversion. These routines are not replaced by Python.
- Original lookup 5AA70 resolves every loaded group and rejects absent scenes.
- Native storage is MESSAGES+D2E4A, 17 area blocks of 9941 bytes; scene records
  have a 142-byte stride with up to 70 resource pairs.
- The full source is bounded before execution: row width 2..7, area 0..16,
  scene 0..255, positive signed-DWORD codes and native group capacities.
- Initial group bytes are `0F 02 00 15 02 8F`: scene 15, count 2,
  category/ordinal pairs (0,21) and (2,143). These are not server NPC IDs or
  placement coordinates.

All 251 groups are compared with independently parsed source codes, including
appended rows, empty groups and zeroed unused slots. Invalid area and absent
scene queries also execute original code. Stack balance is checked per row.

## Verification and boundary

`python -B -m unittest discover -s tests/research -p test_current_world_actor.py -v`
passed all 8 tests in 66.323 seconds, including the previous actor regression
and its 49 C++ packet -> native decoder -> resource/actor profiles.

This is offline native emulation with explicit bounded memory/resources. The
file-open/whole-loader loop is not executed for this table; real row parsing is.
Calls 5A000, 607D0 and 61AD0 in actor phase 68290..68315 remain unjoined. EnyName
loading, cold resource-bank loading, device presentation and full original-client
world acceptance are not claimed. No gameplay coordinates or formulas changed.

Follow-up: `current-world-enemy-groups-20260919.md` supersedes the skipped-range
description above. The original EnyName loader, 5A000 and 607D0 are now executed;
the remaining unjoined range is 682F1..68315 / cold bank preload 61AD0.

## Separate live startup observation

Run `live-menu-connect-20260919-01` used the original working-copy client and
own loopback C++ post-seed server, with the bounded zero-UI-prefix runner.
Its internal UI helpers were disabled; external @oai/sky main-menu clicks were
performed and observed separately. The first click focused/highlighted the menu;
the second reached the account/password dialog. No credentials or dialog input
were entered. This is not an entirely zero-input run.

No memory warning occurred and WSAStartup completed. No socket/connect/TX/RX
occurred before HARD_TIMEOUT. This is neither a successful login nor server
rejection. Desktop tool policy prohibits authentication-dialog automation;
no alternative input mechanism was used to bypass it, and no owner testing was
requested. Historical accepted post-selection evidence remains unchanged.

After termination no God2, god2-server or cdb process remained. The originally
absent display.settings and ctserver.ini were absent again, ddraw.ini matched
original-config-2.bin, and pagefile evidence records host_modified=false.
