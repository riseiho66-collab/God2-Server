# Current Battle Owner Map Panel

Offline current-image continuation only. This does not recover monster base
stats, finish battle initialization, render a live client, or establish playable
client/server combat. No monster data is eligible for database promotion.

## Correct Resource Ownership

The pinned current image is `native-master-01-stable.bin`, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All game addresses below are RVAs relative to `400000`.

The actual `815C0` FieldComm3 reader loads 65 records in the same VM. Four
selected original `81620..8167B` loop iterations retain their source indices:

| Slot | Current original file |
| --- | --- |
| 2 | Data3/Flow/DTitleGui.romZ |
| 15 | Data3/Flow/martrom.romZ |
| 31 | Data3/Flow/BaseInterface.romZ |
| 33 | Data3/Flow/Cuse.romZ |

Raw and decoded hashes are pinned in `OWNER_UI_ASSETS`. Original resource
parsing/decompression and renderer construction run normally; explicit external
file/graphics services remain harness adapters. This is not all-65 asset preload.
World bank `31000000` and renderer `31400000` are separate from battle graphics.
Both banks also receive the same pinned MIS03 source through its original loader.
The bank allocation capacity is an explicit 4 MiB diagnostic precondition.

Before the native battle global reset, the original leave caller invokes
`1042C0`; its `104306` store invalidates the cached owner handle after native
sprite/text release. This selected leave island does not prove the whole world
exit. The retained owner bridge subsequently recreates its actual world sprite.
Neither a slot number nor a pre-reset stale handle substitutes for that resource.

## Retained Continuation

Entry remains the same single `1112C0` invocation used by the prior tests.
From the previous pending `C3080` call, ESP=`SP-3C`, original instructions now:

- Copy the original rectangle at VA `592FE0`.
- Call `104EA0 -> 104F50` with the native world group/action arguments.
- Store the returned window WORD at owner `+232DA6`.
- Call original `107710` three times for the three initial text slots, including
  the real CRT string copy and native text/sprite operations.
- Execute the call at `C3119`, stopping BEFORE the first `C3640` instruction.

The exact boundary is EIP=`4C3640`, ESP=`SP-F4`, with real return address
`4C311E`. No return is fabricated and no game call is skipped in this prefix.
The battle renderer remains byte-for-byte unchanged during this stage; the
new panel uses the owner renderer and source rectangle. Owner memory reconstructs
exactly from observed native writes, character/catalog bytes remain unchanged,
and outer owner canaries survive. Unwritten character clock fields still fail
the read guard; the tests do not fill them with zeros to progress.

## Verification and Boundary

Direct tests: owner resource preparation 3/3, updated owner bridge 7/7, retained
map panel 3/3. The map-panel run takes145.714s because it includes the real
resource and prior battle prefix setup. New suites are registered in CTest;
the shared bootstrap baseline is also included in regression runs.

Registered owner-resource and map-panel suites pass in41.53s and149.93s.
The first baseline run exposed its stale item-image expectation for the old
battle bank. After checking the correct owner renderer/bank in that assertion,
the complete baseline passes21/21 in148.33s. Final selected CTest with both
scalar suites passes3/3 in153.13s; those scalar suites contain9 and19 tests.

The separate [world clock proof](current-world-clock-20260920.md) executes the
original S2C1A writer and clock arithmetic with explicit packet/OS samples;
13/13 lightweight tests pass independently. It is NOT yet joined to the retained
map-panel stack and does not mean this C3640 call returned.

Next dependencies include source-owned clock fields, actual formatting, map
metadata, the remaining C3080/81C20 bodies, and full battle initializer return.
None of these UI/clock proofs yields original monster HP, attacks, defenses,
skills, experience, capture rules or drop rates. Synthetic inputs qualify only
native code behavior; original numeric recovery requires identity-bound sources.
