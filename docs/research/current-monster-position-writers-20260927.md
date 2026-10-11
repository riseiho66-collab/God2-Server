# Current monster-pool position and walking writers (2026-09-27)

## Result and boundary

This bounded pass recovered **zero complete authoritative wild-monster
placement or encounter records**. A usable record still needs map identity,
monster catalog identity, coordinates/region, and the original triggering rule.
No new spawn coordinates or encounter formula are justified by this pass.

It did establish the distinction between packet-driven monster displays and
locally positioned following companions, the exact monster display namespace
fields, and additional unexported walking helpers. This is not a claim that
the entire client or every computed call has been exhausted.

Only the current supplied PE, its matched mapped image, saved read-only Ghidra
project, and current reconstruction were used. No retired corpus, live client,
production database, or runtime code was changed. No desktop interaction.

## Reproduction and identities

```powershell
& 'C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe' `
  tools/strike_lab/current_monster_position_writers_20260927.py
# Repeat byte validation and native vectors without reopening Ghidra:
& 'C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe' `
  tools/strike_lab/current_monster_position_writers_20260927.py --reuse-export
```

Evidence directory: `artifacts/research/monster-position-writers-20260927/`.
The tool rejects implicit reuse of an existing export receipt. A fresh full
export needs a new `--output` directory. It reuses the generic Java template
from the preceding NPC census; no prior findings are silently executed as code.

- Current `God2.exe` SHA256:
  `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Mapped evidence SHA256:
  `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Saved-program executable SHA checked before read-only export.
- 76 selected saved functions, 224 incoming references, 15,037 instruction rows
  (including repeated caller context) exactly matched to both PE and mapped image.
- 229 raw E8 call candidates to the selected entries/gap entries, scanning
  original `.text` **despite its retained RW section flags**, plus executable
  sections. These are candidates; known boundaries are separately recorded.
- 140 native Unicorn vectors passed: 12 movement-builder vectors and 128 monster
  constructor prefixes. No game callee was replaced; execution stops at explicit
  bounds before downstream queue or map/renderer processing.
- `evidence.json` contains each exported function's VA extent, raw PE offset,
  range SHA256, incoming refs, vectors, gap ranges and packet jump-table entries.

## Packet-driven monster display

The world switch is `00468AE0`, table `0046B5D4`. Do not infer opcodes from
neighboring source files or adjacent switch cases.

| Logical opcode | Actual dispatch target | Behavior relevant here |
|---|---|---|
| `70` | `0046B517` | Default branch; not monster appearance |
| `71` | `0046A3B4` | Catalog lookup, then ordinary/composite monster appearance |
| `5F` | `0046A677` | `004CCB10`, existing monster movement |
| `74` | `0046A65D` | `004CC990`, remove low-WORD instance identity |
| `78` | `0046A64B` | `004CC840`, existing display level label; no position write |

Let `L` point to the logical opcode byte, `P=L+1`. At `0046A3B4..0046A3D4`,
the arguments to `0045A0A0` are loaded directly from the received record:

| Field | Native origin / interpretation |
|---|---|
| EnyName area | `L[5] & 0x3F` |
| EnyName scene/group | `LE16(L+5) >> 6` |
| EnyName catalog ordinal | `LE16(L+19) >> 3`, one-based |
| Display instance identity | `LE32(P) & 0xFFFF` |
| Facing | `LE32(P) >> 29`, three bits |
| Tile X | `(LE32(P+8) >> 2) & 0x7FFF` |
| Tile Y | `LE32(P+8) >> 17` |
| Optional resource override | `(LE32(P) >> 16) & 0xFF`; nonzero calls `0045A120` |

`0045A0A0` requires area <17 and ordinal !=0, then matches the supplied scene
and checks ordinal <= that group's count. Its records are 26 bytes. Neither
the display instance identity nor the current player's map is substituted for
these explicit namespace arguments. Thus a join `instance_id = EnyName ordinal`
is unsupported.

Ordinary resource resolution uses `00461980/004618B0`, validates a resource
handle <512, and calls `004CB120` at `0046A5B3`. Composite resolution uses
`00461040`, requires four nonnegative component handles, and calls `004CB720`
at `0046A536`. Resource 0x3D and source flags adjust display fields; they do
not supply map placement or encounter conditions.

The pool is `M = W+153B8758`; 256 records start at `M+70`, stride `1D8`:

- `+00`: DWORD instance identity; `FFFFFFFF` is unused.
- `+08`: WORD facing; `+10/+14`: DWORD tile coordinates.
- `+18/+1C`: screen-position floating-point values.
- `+34`: bounded path queue; `+180/+184/+188/+18C`: position snapshots.

The 128 constructor vectors exercise both `004CB120` and `004CB720`, newly
allocated and already existing slots, all eight directions, and four coordinate
patterns including 15-bit truncation. They stop at `4CB492/4CBA6B` for new
records and `4CB265/4CB841` for existing records, after identity/position/facing
writes and before map/rendering work. They are **not full graphical acceptance**.

`004CCB10` resolves an existing identity, then `004CD8D0` takes target packed
coordinates plus caller-supplied previous WORD X/Y at `P+12/P+14`. If current
position differs from previous position by more than one tile on either axis,
it corrects the position, rebuilds the queue through `0045FD80`, and stores
previous/target snapshots. This is received movement reconciliation.

## All discovered constructor callers and companion separation

Raw direct-call scanning and saved incoming refs agree on these callers:

| Target | Caller instruction | Context |
|---|---|---|
| `004CB120` | `0046A5B3` | S2C71 ordinary resource |
| `004CB120` | `0046CB87` | Local following companion |
| `004CB720` | `0046A536` | S2C71 composite resource |
| `004CB720` | `0046CB66` | Local following companion |

No whole-image literal pointer to either constructor was found. This does not
exclude a computed address or an interior entry.

`0046C6A0(owner, pet_selector, flags)` builds a display identity `owner|8000`.
It resolves area **0**, with scene/group **2**, **13** (`selector&4000`), or
**3** (`selector&8000`), using ordinal `selector&3FFF`. For self, it starts with
the player's existing `W+224/+228` coordinates; for remote owners it obtains
the existing actor's coordinates through `004FAD70`. `004FADC0` searches nearby
walkable cells, falling back to the owner position. These are genuine local
positions, but are follower placement relative to a known owner, not wild
monster spawn data.

All discovered incoming calls to this builder:

- `00469B91`: world S2C3A companion update.
- `00501244`, `005015E3`: `005011C0` scene/player positioning initialization,
  using owned player state (`+48` companion selector), including reset branch.

`0046CC00` updates that owner's synthetic companion display; its only found
incoming calls are `0046933B` (S2C5D movement acknowledgment dequeues existing
player coordinates) and `00469B20` (S2C5E remote movement). Its call
`0046CD26→004CCC00` appends a target coordinate to the display queue. It has
no caller that loads a local wild-monster placement table in this census.

## Position-writer classes (shared pool machinery)

The preceding NPC writer pass applies to the shared CPMonster structure. The
additional owner scan here contains 28 monster-pool base references.

| Writer / family | Position source |
|---|---|
| `004CA680` | Initializes 256 zeroed records, all identities unused; no spawn |
| `004CB120/004CB720` | S2C71 record or owner-relative following-pet record |
| `004CCB10→004CD8D0` | S2C5F previous/target coordinates and path reconciliation |
| `004CCC00→004CD7D0` | Following-pet target appended to queue |
| `004CA800/004CAAC0` | Existing record path queue advanced into current XY |
| `004CD3E0` | Direction selected from queued coordinate delta |
| `004CACD0/004CDAA0/004CDB10` | Screen interpolation / tile-to-render updates |
| `004CA760/004CA7B0`, wrappers `00503CB0/00503C70` | Map viewport offset changes |
| `004CCEC0` (unexported) | Caller-supplied signed WORD XY setter; no found raw direct or literal pointer caller |
| `004CA730/004CCE10/004CC990` | Invalidates/removes records |

The extra pool use at `0046B4FC→004CC910` writes the following companion's name
using `owner|8000`; it does not instantiate or position a wild monster.

## Walking, path lengths and encounter boundary

Observed chain:

`005024C0 → 00502B90 → [00502BF0 or 005035B0] → 00502700 → 00468950 → 00415790`.

`00502700` derives an adjacent direction, configures movement animation/speed,
and queues the destination at `W+234` through `005036B0`. This is a 40-entry
coordinate queue, not evidence of a 40-step encounter rule. `W+34` is a cursor
into the path at `W+3C`; `W+38` is its length. `00502570/005029A0` advance the
animation/path and update the player's position, not a recovered encounter
probability counter. `00415AB0` is simply a return in this build.

`00468950` updates map coordinate widgets through `004C3C20/004C3E30` and, when
`W+15396840 !=0`, closes appropriate UI then calls the movement producer.
`004C3A70` formats the displayed X/Y, optionally modulo map dimensions;
`004C3E30` positions another map widget. These are not encounter-zone lookups.

`00415790` appends C2S **2E**, payload six bytes:
`X:u16, Y:u16, mode:u8, untouched-stack-byte:u8`. Twelve pinned native vectors
vary X/Y/mode and poison the stack with 00/5A/FF; the sixth byte follows that
poison. It must not be interpreted as a recovered encounter counter or trigger.
Execution stops at original `004132E0`, before mutating the real send queue.

Pathability `00446FF0` reads the ordinary map's 63×63 passability window or
delegates indoor mode to `00436B60`. The visited callers test 0/1/2 for routing.
No monster identity or encounter table is read by those caller branches.

Clicking an existing world monster in `00466B00` selects a pool instance,
excludes identities with bit8000 (followers), gets its current coordinates,
and may walk toward it through `005024C0`. This does not demonstrate a local
random spawn or identify the authoritative server encounter response rule.
The existing S2C82 world→battle context boundary remains separate.

## Unexported code checked, and what remains open

The saved export is not complete code recovery. This pass inspected raw ranges
and kept qualified instruction spans separate from embedded tables:

| Entry | Checked behavior |
|---|---|
| `005028F0` | Map/screen coordinate conversion and 400/300 screen-offset arithmetic |
| `00502EE0` | Sprite creation using caller parameters |
| `00502F20` | Eight-direction candidate coordinate, then `00446FF0` pathability |
| `00503010` | Five radii × eight directions search using `00502F20`; output caller XY on failure |
| `005030A0` | Deterministic path-neighbor selection using caller XY, passability, prior path entry |
| `0046CD60/0046CD80` | Static initialization and atexit registration |

`00502FE4..00503003` is an eight-address direction jump table, not instructions.
The preliminary `movement-gap-disassembly.txt` is retained as exploratory
output; only `qualified-gap-instructions.tsv` and ranges/hashes in evidence.json
are used for claims. New raw call `00503053→00502F20` is inside these checked
ranges. Five other raw calls absent from Ghidra refs are the already checked
shared-pool gap functions from the NPC pass; none is a new constructor caller.

Related random helper `004CDBC0..004CDBDE` (prior NPC evidence) accepts a byte:
DC returns `rand()%6+DC`, otherwise returns that byte. No discovered raw E8
caller or whole-image literal pointer refers to its entry; it writes no pool
position. Its location near CPMonster is insufficient to call it a wild-monster
selector. Raw offset CD1C0, SHA256
`e992a3cd2914a4eeac50e1b6728137dd725bed051e8224006ba2829633a31469`.

Still open: computed/indirect callers and code outside the bounded families;
the original server's choice of S2C71/82 records and triggering conditions;
full original map→encounter-region→monster composition authority. An actual
server record/capture or a newly identified local loader that connects all
those fields is needed before integrating native encounter placement. The
separate parent lane handles random/text xrefs. This lane stops here.
