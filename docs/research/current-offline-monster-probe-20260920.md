# Current Offline Monster Experiment, 2026-09-20

## Question and Result

Owner supplied another developer's claim: disable packets, enter a single-player
world, and recover original monster capabilities from original client files.
This experiment tests the LOCAL FILE -> NATIVE MONSTER CONSTRUCTION part.
It does NOT yet reproduce their live offline-world implementation.

Two real current monster ROMs load through original instructions. The retained
normal-participant caller now executes its real six-actor reset, render-object
creation, ROM command traversal and metadata copy, returning at RVA11602A.
No HP/MP update or combat-result record is supplied. Known actor vital fields
remain native CD reset fill, not recovered numbers. New authoritative original
monster capability values: **0**. No production data is changed.

An explicit synthetic45-byte1C identity/selection record is still used to select
the source. Thus this is NOT a claim that all packets were disabled in a running
client. No live client, network backend, login/world loop or screen is involved.
The result neither verifies nor refutes the other implementation's data claim.

## Sources and Execution

Image is the existing hash-pinned `native-master-01-stable.bin`, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
RVA equals file offset; BASE400000. No instruction is patched.

Existing original row writers supply EnyName generation1/area1/scene0/ordinal1
and its FightEny resource row15. This occurrence is not a global monster-ID
stat join. See the [identity investigation](current-monster-identity-backtrace-20260920.md).

| Side | Original file | Decoded bytes |
| --- | --- | --- |
| 0 | `data2/fight/eny1/eny1015.romz` | 98,134 |
| 1 | `data2/fight/eny/eny5015.romz` | 103,903 |

Raw/decoded file hashes are enforced in `current_monster_resource_initialization.py`
and included in the generated JSON. The original120650 miss continuation calls
29820, decompresses with1EC0 and parses through2A1D0, inserts the actual name-cache
entry and returns via1207C9 to115FC7 on the same VM and pending stack. No successful
resource handle is substituted. Loader output is compared with the pinned source.

Offline ownership preparation is explicitly separate from process startup:

- Original1AA10 builds a renderer/pool bound to the loaded bank.
- Explicit slots bind168 allocated actors. Original11FDE0 resets each actor;
  type4 owns a separate effect record initialized by11C9F0 and11CA30.
- Original11F4C5..11F4EF copies the image's224-byte position table.
- The optional effect owner is explicitly absent. CRT/file/memory/critical-section
  adapters are inherited bounded platform adapters, not replacement game logic.
- Preparation restores the pending participant CPU, stack and SEH pointer.

The original pending caller then continues without skipped game calls:

`115FC7 -> 116000 -> 120000 -> six11FDE0 calls -> 116025 -> 1216C0 -> 11602A`

This includes actual121630/1E130 sequence-name reads,12A7C0/12A710 mapping,
1AFE0 render allocation,1E070 resource selection,1CD40 command accumulation,
14DWORD metadata copy at121A4A and120970 selection reset. Both sides return
real render handle0. The render record/sequence count and command accumulator
are graphics-related observations, not newly identified combat attributes.

For actor+DE8/+DEC/+DF0/+DF4 the ONLY writes in this resumed segment are
11FDFE's CDCDCDCD reset stores. Every actor's trailing guard remains unchanged.
The source1C bytes and original code remain unchanged. Four attributes and
attack/defense remain null/unknown in the report; no value is inferred from fill.

## Separate Default Initializer

The earlier static finding is now executed as two clearly separate native
islands: caller1165C1 through12CCD0's real call/prologue, then12D219..12D329.
The actual caller creates two pairs `(1,1)`. Side0 writes those constants to
the four HP/MP fields; side1 skips them. The pending resource-return state is
restored afterward. This is NOT execution of the intervening display body or
completion of115C90, and the constants are NOT original monster HP/MP.

## Remaining Boundary

11602A is before attachment construction, final display/metadata setup,
world/event loop and combat. No executable single-player entry has been run.
The separate [entry audit](current-offline-world-entry-audit-20260920.md) found
an internal NULL-input68160 ->688D0 fallback, but no supported launch switch.
The alternateEEE0 ->64910 construction path is an unproved entry lead.
An experimental offline host could intentionally invoke such a path; doing so
would require initialized owners and must be labelled a modification, not an
original startup observation or proof of a local combat-stat producer.

## Reproduction

```powershell
python -B -m unittest tests.research.test_current_offline_monster_probe tests.research.test_current_monster_resource_initialization tests.research.test_current_stat_packet_return_path -v
python -B -m tools.strike_lab.current_offline_monster_probe --output artifacts/research/offline-monster-probe-20260920.json
```

The first focused run caught a test expectation error: Unicorn reports15 visits
for REP MOVSD with14 actual writes, including the zero-count terminating visit.
The corrected test verifies both15 visits and exactly14 DWORD destination writes;
no client instruction or result was changed to satisfy the test.

Final focused unittest run:13/13 passed in13.683s. Regenerated CMake and ran
six selected CTest suites (base stats, side initialization, identity backtrace,
resource initialization, offline monster probe, packet return path):6/6 passed
in24.59s. An earlier command used an incorrect test-name prefix and selected
zero tests; that command is not counted as verification. The CLI report was
generated at `artifacts/research/offline-monster-probe-20260920.json`.
Both bounded workers were reviewed and closed. Main independently checked four
native call targets in the entry audit, without claiming startup execution.
