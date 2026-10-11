# Current Native Battle Entry, 2026-09-19

## Current: Native Receive Return And Formal Wire

Main now starts the actual68AE0 function, including the original stack probe,
native13420/13650 acquisition, dispatcher, all closed-UI cleanup and13670 reset.
It returns EAX=4 with RET4 stack cleanup and all callee-saved registers restored.
The prior function-island and closed-UI-only findings below remain narrower
historical proof steps, not the current boundary of this explicit fixture.

For a following complete83/84/86/89 record,13420 preloads exactly that record
into NET+2CC4. The82 sentinel at68B39 exits without another world dispatch or
another13670 reset, preserving its length at NET+2CC0 for the battle phase.
Remaining coalesced records stay in the decoded queue. Partial83 lengths1..14
are preserved on return4. An empty remaining queue reaches the actual10D20
socket-poll boundary and stops; no select/socket result is invented.

The formal Release recovered-world-frame executable encodes82 plus the next
record. Original10490 expands the lab's zero seed,10AB0/10A10 invokes original
decryption and checksum, fills the native decoded queue, then68AE0 executes
the whole receive function described above. No Python plaintext copy fills
that queue in wire mode. Corrupt checksums are rejected by the original decoder
before dispatch. The full frame must be supplied; TCP read/assembly is outside
this proof. Raw field authority, battle initialization and live E2E remain open.

All17 entry tests pass in1.607s, including key-wrap and2559-byte logical batches
preserving169 queued battle records after the first was preloaded. A native
harness bug was also fixed: each run clears its previous stop marker, so a
reused VM cannot mistake instruction-budget exhaustion for earlier success.
The regression explicitly reproduces that old stale-stop hazard.

## Main Continuation: Closed UI Path

After the worker handoff below, main extended the same uninterrupted dispatch
run through original857E0,814F0 andA7550 to6B517. With explicitly inactive UI
controls,6AE40 now actually writes return-state4. No callee return is replaced.
This does NOT execute the return/queue tail at6B517 or the main initializer.

The fixture supplies fifteen negative handles for857E0;18 additional negative
WORD handles for814F0/A7550; a nonnull control object with its+24 field zero;
UI+88790=0; and explicit UI+23D5E4/+23D5E8 values. BC2E0's original data-global
write sets5926B0 toFFFF. Category3 additionally executes C9C00 and clears both
category DWORDs; other tested categories preserve them. This is synthetic
closed-UI state, not a claim about every live client's open panels.

The test runs handle values-32768/-1 and categories0/3/FFFFFFFF. It verifies
17 exact callee entries, real stack restoration, state4, and the complete
ordered nonstack write set. All13 tests pass in0.225s. Active-panel cleanup
branches, queue continuation at6B517, and initialization still need evidence.
The worker's narrower stop at814F0 below remains valid for its older fixture.

## Integration Finding

**S2C logical opcode `82`, total logical length 9 bytes, is the world-to-battle
transition trigger.** Its two fields are raw little-endian DWORDs. Their original
gameplay meanings and server authority are not established by this task.

| Logical bytes | Native world write | Native initialization use |
| --- | --- | --- |
| `+0`: `82` | World dispatch table entry selects `6AE12` | Battle dispatcher defaults this opcode; it is not a battle-phase entry handler |
| `+1..+4`: DWORD A | Transition context `T+28` at `6AE22` | Copied to battle object `B+3C` at `11140C`; also retained in copied context at `B+70` |
| `+5..+8`: DWORD B | Transition context `T+2C` at `6AE2A` | Copied to `B+40` at `111412`, also `B+74`; its low byte equals `FF` sets `B+A9EA4C8` to 1, otherwise 0 |

The packet contract is logical bytes, not an encrypted/framed wire packet.
No server producer or transition to server-side `InBattle` is authorized by the
native findings alone. The separately implemented C2S35/action1 route still needs
authoritative battle creation and valid entry fields. This task changes no runtime.

## Identity And Scope

Only input image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base VA `400000`; all code/table addresses below are RVA = file offset.
Object offsets and lengths are hexadecimal unless stated otherwise.
No retired client evidence or leads were used.

## Original Instruction Proof

The native length wrapper `15840 -> 1000 -> 1200` executes the original length
table lookup. Entry `1324 + 82*4` selects `12D0`: `B8 09 00 00 00 C3`, returning 9.
This is executed, not inferred from the largest field read.

| RVA | Original bytes | Effect |
| --- | --- | --- |
| `68B50` | `8A 03` | Load opcode from `[EBX]` after EAX was cleared |
| `68B61` | `FF 24 85 D4 B5 46 00` | Jump through world table `6B5D4` |
| `6B7DC` | `12 AE 46 00` | World table entry `82` points to VA `46AE12` |
| `6AE12` | `8B 84 24 04 17 00 00` | Load transition-context pointer from dispatcher argument `[ESP+1704]` |
| `6AE19` | `8B 4B 01` | Read first DWORD from logical record `+1` |
| `6AE22` | `89 48 28` | Write first DWORD to `T+28` |
| `6AE25` | `8B 53 05` | Read second DWORD from logical record `+5` |
| `6AE2A` | `89 50 2C` | Write second DWORD to `T+2C` |
| `6AE2D` | `E8 AE A9 01 00` | Call `857E0`, this = world object `+A7F2F6C` |
| `6AE34` | `E8 B7 66 01 00` | Call `814F0`, same this |
| `6AE3B` | `E8 10 C7 03 00` | Call `A7550`, same this |
| `6AE40` | `C7 44 24 2C 04 00 00 00` | Set dispatch return-state local `[ESP+2C] = 4` |
| `6B5C2` | `8B 44 24 2C` | Load that return state into EAX |
| `67159` | `83 E8 04 74 32` | Caller recognizes return 4 and branches to `67190` |
| `1113BF` | `80 7B 2C FF 0F 94 C1` | Compare `byte[T+2C]` with `FF`; SETE CL (ECX previously zeroed) |
| `111409` | `8B 43 28 89 45 3C` | Copy `T+28` to `B+3C` |
| `11140F` | `8B 4B 2C 89 4D 40` | Copy `T+2C` to `B+40` |
| `111415` | `B9 FB 00 00 00 F3 A5` | Copy `FB` DWORDs (1004 decimal bytes) from T to `B+48` |

After the handler, queue consumption occurs through `6B51F -> 13670`.
`68B31` explicitly compares the last opcode with `82`; `68B39` branches to
the dispatcher exit when equal. Thus this opcode also ends that world receive
pass, rather than continuing to process following records as world traffic.
These intervening queue operations are static evidence, not executed here.

## Static Connection To Actual Initialization

The original call/return path is:

1. Main function `655E0`, state 3 arm: `6564E -> 67860` (world loop),
   passing T = its local `ESP+238`.
2. World loop `67A63 -> 66B00`; `67154 -> 68AE0` passes T to the world dispatcher.
3. Handler `6AE12` consumes `82`. After its three calls it selects 4.
   `67159 -> 67190` recognizes 4. All branches of that arm store caller-local
   state 4 (`671BF`, `671EE`, `6720B`), then run the ordinary world tail.
   `67685` retrieves that local for return. `67A68` exits the world loop when
   the result differs from 3, preserving EAX=4.
4. `65653..65659` forwards that return to the main state switch at `6563D`.
   Table `65A14[4]` points to `6565B`. This arm performs multiple intervening
   services before `65836 -> 1112C0`, the actual battle initializer.
5. The initializer receives a descriptor whose `+4` is T. `1113B6..1113BF`
   retrieves T and tests its second field's low byte. `111409..11141A` performs
   the battle-state writes and full context copy above.
6. After initialization and further services, `658D9 -> 115770` enters the
   battle loop on the same object loaded from world `+A7E05EC`.
   `115828` writes `B+A9EA4C4=1`; `11582E` writes `B+A9DF6C0=0`.
   `115A4C -> 1140C0` calls the routine containing the requested dispatcher.
7. `114315` reads the queued opcode; `11431C -> 15840` gets its native length;
   `11432D -> 11D3D0` copies from the battle queue. `114332..114351` dispatches
   through selector table `11465C` and jump table `114634`.

**Do not send `82` only after switching the client to its battle dispatcher.**
Original execution of `114332` sends `82` to default `1145C0`; `83` selects
`11436B`. The entry trigger belongs to the world receive phase.

## Executed Boundary And Next Call

The harness executes original image instructions in sparse Unicorn memory.
It never patches code, replaces a callee, sets a synthetic return value to pass
a call, or resumes a stopped run beyond its unqualified boundary.

| Independently started island | Last proven boundary | Qualification |
| --- | --- | --- |
| World opcode load `68B4E`, real indirect dispatch, both field writes | Stop before `6AE2D -> 857E0` | Only record bytes, context pointer, and stack locals are supplied |
| Same start, explicitly fifteen signed -1 cleanup handles | Stop before **`6AE34 -> 814F0`** | Executes all of `857E0`, five negative-handle branches of `6D340`, ten of `6E490`, and real returns |
| State suffix `6AE40` | `6B517` | Independent prerequisite: preceding three calls have returned; does not establish that they did |
| Main return-state selector `65653`, EAX=4 | Before `6569B -> 66920` | Independent return=4 fixture; optional connection object explicitly null |
| Initializer `1112C0` | Before `1113D8 -> 181B0` | Explicit descriptor/component pointers, preexisting resource pointer, empty string-table fixture |
| Initializer copy `111409` | Before `111424 -> 11FC40` | Independent post-service register fixture; source context bytes come from the executed world prefix |
| Battle switch `114332` | Selected case address, before executing it | Independent post-queue fixture; queue copy is not stubbed or claimed executed |

**Immediate next qualification: `814F0`, called at `6AE34`.** On the tested
negative-handle fixture the dispatcher return-state local is still **3** at this
stop. After that callee, `A7550` remains before the state-4 write. For active
nonnegative handles, the first cleanup's additional paths are unqualified;
the baseline boundary remains `6AE2D -> 857E0`.

This proves a current-native entry contract and a static connection to actual
battle initialization. It does **not** prove continuous world-to-battle execution,
successful resource initialization, a rendered battle, field authority, enemy
creation, or server combat acceptance. Starting the later islands is explicitly
not evidence that the earlier unqualified calls returned.

## Reproduction

Run from the server root; `-B` prevents bytecode artifacts:

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_entry.py -v
python -B tools/strike_lab/current_battle_entry.py
```

Uses existing `artifacts/tooling/crypto-oracle-python` Unicorn 2.1.4; installs
nothing. Twelve focused tests cover identity rejection, original byte and call
witnesses, exact record validation, extreme DWORD values, unchanged surrounding
context, cleanup counts and real return stack, state selection, initialization
writes/copy extent, low-byte sentinel behavior, distinct dispatcher routing, and
failure on unknown control flow or exhausted instruction budget. Logical record
length rejection is a harness guard; it is not attributed to the native handler.
These tests are separate from main's selected54 suite.

Owned files only: `tools/strike_lab/current_battle_entry.py`,
`tests/research/test_current_battle_entry.py`, and this note.
