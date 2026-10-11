# Current Battle Owner Bridge

This is an offline, current-image continuation proof, not original monster
numeric recovery, a complete battle initializer, visible rendering, or a live
client/server acceptance run. No monster value is eligible for database import.

## Memory and Source Ownership

The previous offline owner address, `08330000`, was unsafe: its embedded panel
range `owner+E2170..owner+232DA4` overlapped the character at `08520000`.
The owner now occupies a separate `30000000..30240000` allocation with outer
canaries. Character packet bindings and the battle selector use this SAME owner,
not a second detached UI object. The large battle object remains at `20000000`.

Only the pinned current mapped image is executed, BASE `400000`, RVA=file offset:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
No retired server source, process/UI automation, network connection or image
instruction patch is used.

Explicit preparation runs original descriptor stores `817CA..81895`, followed
by the actual `819DD..81A08` caller and `104160/1041A0` panel constructor.
The original panel arguments retain mode `2,0`; a negative selector is NOT used
to suppress its sprite/text creation. Renderer, input, resource and message
pointers are explicit harness bindings, not captured startup state. Unqualified
descriptor fields remain poisoned. This is not the full `817C0` constructor.
Preparation writes are collected and constrained to the owner, renderers,
surface and explicit display snapshot. World graphics no longer reuse the
battle renderer: owner `CFF60` points to `31400000`, whose bank is `31000000`.
The actual FieldComm3 reader loads all 65 records; selected original preload
iterations load only slots 2, 15, 31 and 33. Slot 2 is DTitleGui, not the skill
resource occupying battle bank slot 2. Current MIS03 is also loaded separately
into the owner bank for the original item resolver. Allocation capacity remains
an explicit fixture input, not a captured world constructor argument.

The native global renderer reset during battle initialization remains intact.
Original leave-call island `81C12..81C1D -> 1042C0` now releases the cached owner
sprite first, including original `1B330` and text release `27570`. Native store
`104306` sets the cached WORD handle to `FFFF`. This is not the complete world
exit function. Later `1041A0` therefore recreates the background from the correct
world bank instead of accidentally reusing a battle sprite after reset. Both
real renderers participate in the global reset. Live graphics ownership remains
unproved, but the offline world and battle resources are now distinct.

## Appearance Producer and Retained Call

The pending `11177D` continuation requires character `+28`. Missing appearance
is rejected before execution. An explicit 36-byte diagnostic world body is
staged through original stores `68328..6834B` on the SAME character:

| Original writer RVA | Destination | Source |
| --- | --- | --- |
| `68330` | character `+4584`, DWORD | body bytes 12..15 |
| `6833F` | character `+4588`, DWORD | body bytes 16..19 |
| `68348` | character `+28`, DWORD | body byte 13 shifted right 5 |

The diagnostic bytes are not captured appearance, monster stats, or a species
assignment. The pending CPU context/stack survive this explicit producer stage.
Unwritten character bytes, including `+1C`, still fail the read-ownership guard.

The retained stack then executes `11177D -> 111791 -> 81C20` with mode 1. It
executes original `1041A0`, `104470`, `1B960 -> 25C80`, `83410 -> 1A920`, and
the call at `81F08`. No game return is fabricated and entry `1112C0` remains a
single invocation. In particular:

- `25CB3` writes one visibility byte to the surface record selected by the real
  renderer handle: `surface + resource_index*200 + 125B`.
- Native mouse snapshot writes owner `+232EC0` and the state WORD `+232F36`.
- Native code copies character WORD `+28` to `+92`.
- All 64 selector DWORDs at owner `+232DA4` are filled with `FFFFFFFF`.
- Character/catalog bytes outside their qualified writes and owner canaries
  remain unchanged; complete owner snapshots reconstruct from observed writes.

Execution stops BEFORE `C3080`: EIP=`4C3080`, ESP=`SP-3C`, return address
`481F0D`, next argument the SAME character. This is a reached call boundary,
not an executed/returned `C3080`; the boundary is excluded from call counts.

## Verification and Remaining Work

```powershell
ctest --test-dir build -C Release -R '^current_battle_(bootstrap|owner_bridge)$' --output-on-failure
```

The updated focused bridge suite passes 7/7 in148.732s. It checks mapping
separation, original bindings and
constructor writes, exact appearance production, retained call stack, actual
surface setter, source/catalog retention, and missing/repeated-stage rejection.
The baseline is included because this change touches shared bootstrap
preconditions.

The corrected separate-bank baseline subsequently passes21/21 through CTest
in148.33s; its former item-image bank expectation was stale. The test now
checks the actual owner renderer/bank before checking the returned resource.

The next stage now executes the actual `C3080` prefix on this retained stack,
creates its map panel and three text slots, and stops before `C3640`. See
[map panel continuation](current-battle-owner-map-panel-20260920.md). Remaining
work includes clock integration, the rest of `C3080`/`81C20`, and the full
initializer return. Original source provenance is still
required for each requested wild/BOSS numeric field. Received synthetic scalars,
successful UI construction or a packet consumer alone cannot supply those values.
