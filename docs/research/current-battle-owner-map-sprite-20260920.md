# Retained Battle Initializer: Map Control

Follow-up: `current-battle-owner-map-label-20260920.md` supplies the coordinate
fields through their original writer and executes the retained label call to
C3348. The original sprite-stage boundary and evidence below remain unchanged.

## Scope

Current-image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
RVA equals mapped-file offset; image base is 400000 hexadecimal.

`continue_owner_map_sprite` extends the existing same-VM map metadata stage.
It starts at C332C, with the pending native five arguments and ESP=SP-104,
and stops at C3331 immediately after the original 105C20 call. No argument,
register, game instruction, or game-function return is replaced for this step.
The pre-existing bounded OS CopyRect adapter remains part of the offline VM;
this is not a live Windows client execution.

The resource comes from the earlier original map lookup: metadata panel words
47/1, control 4, original rectangle at VA5B7AA8, and the existing world-panel
handle. It is not a fabricated monster, combat formula, or server event.

The retained state must first call the existing `load_owner_map` producer.
That executes the original 816B0..816DC load on a separate scratch stack,
selecting the pinned area-2 asset through the original 170E48 table and loading
it into group47 of the world bank. Its context save/restore preserves the entire
pending CPU context and main stack; this is explicit prerequisite preparation,
not proof that normal world startup reached this producer in a live process.
The regression compares the pending stack/EIP/ESP before and after that load.

## Checked Operations

- 105C20 must reach its RET14 at 105D3C, restoring ESP to SP-F0.
- Real 18B80 registers a mouse rectangle; the control's WORD+8 index must point
  to an occupied record whose rectangle equals control+10..+1F.
- Real 1E7C0 and 1EF00 must execute, excluding the no-op early-return branch.
- Control type changes from 0 to 10 hexadecimal.
- Owner and mouse object snapshots reconstruct from observed native writes.
- The separate battle renderer, character source and bound map records remain
  unchanged. The original 1112C0 entry count remains one.
- The continuation is single-use and requires the exact retained stack boundary.

The first diagnostic run stopped at RVA18BAD writing MOUSE+0C90. Inspection
confirmed this is the original 24-byte mouse-region allocator, not an unknown
object. The write guard was extended to the existing MOUSE object with complete
snapshot accounting; no memory was invented to bypass the failure.

The second diagnostic reached native 2C70 from 1E8D3 (return address1E8D8):
1E710 returned no resource for the requested map graphic. The prior fixture had
map metadata but had never run the dynamic map resource loader. The continuation
now rejects a missing `owner_map_loaded` prerequisite before any execution,
and the regression explicitly executes that original loader before retrying on
a fresh VM. The diagnostic is not ignored or converted into a successful return.

A subsequent full-call run exposed catalog corruption. A catalog write hook
located the first changed byte at native RVA147B7D, the `_chkstk` return-address
push, during the map load rather than sprite creation. Original 29839 loads
EAX=D554 before calling `_chkstk`; the old scratch ESP had only8000 bytes below
it in a10000-byte allocation. The native stack therefore extended into the
preceding catalog allocation. The host scratch allocation is now20000 bytes,
with ESP at+1F000. The original stack-probe code is unchanged. The regression
rejects every changed catalog write during loading and compares its whole byte
snapshot afterwards, in addition to verifying the decoded source fields.

The original image parser also exceeded its prior100-million-instruction
budget at2C178. Its bound is now500 million with a240-second emulator timeout;
the registered whole-fixture timeout is600 seconds. Pinned input bounds remain
4 MiB compressed and8 MiB decoded. No image parser is replaced by host output.

## Remaining Boundary

C3331 next reads the character pointer from owner+8688C and subsequently
character WORDs+0C/+08 before C3B60. Those coordinate fields and the subsequent
UI continuation are not proven by this step. Full 1112C0 return, original-client
battle E2E, server battle policy and wild monster numeric data remain incomplete.
Production C++/Lua logic, runtime emission and database values are unchanged.

## Verification Command

Final registered CTest passed1/1 in252.37 seconds, containing both native
control-return and full source/write-footprint test methods. It rebuilt the
retained initializer and loaded the pinned map on a fresh VM. The independent
command-gate regression also passed9/9. Earlier failed runs are retained above
as diagnostic history, not counted as successful verification. No live client
or network test was run in this follow-up.

```text
ctest --test-dir build -C Release -R '^current_battle_owner_map_sprite$' --output-on-failure
```
