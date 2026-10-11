# Continuous Current Battle Initializer, 2026-09-19

## Latest Boundary: Source Transfer, 2026-09-20

**One continuous normal `1112C0` run now reaches `11149B`, before loading
B+`83458`.** It executes the earlier nonnull registry reset, source DWORD reads,
`111484 -> 205A0` and its real `RET 14`, then the manager-source read and write.
No source constructor, resource-handle binding, live entry, or full initializer
completion is claimed. No stopped run is resumed and no native return is faked.

Two additional optional pre-call snapshots select the new extent:

| Input | Fixture binding and exact size | Stop without the next snapshot |
| --- | --- | --- |
| `source_state` | SOURCE=`06900000`, size `8C`; normal prefix derives B+`18` from renderer+`A0` | `111489`, before loading manager+`14` |
| `manager_source_state` | MANAGER_SOURCE=`06D00000`, size `410`; explicitly bind manager+`14` (B+`14494C`) before the run | `11149B`, before loading B+`83458` |

Both require the earlier explicit display and registry snapshots. The principal
proof retains one nonnull registry entry in position 19 and a poisoned pool;
all 4096 slots reset natively before these new instructions. Snapshots have
nonzero poison and guards. Supplying storage is not proof of its authoritative
origin; no CSV records, indexes, or runtime handles are supplied here.

| RVA | Original bytes | Executed effect |
| --- | --- | --- |
| `111469` | `8B 88 88 00 00 00` | Read source+`88` |
| `11146F` | `8B 90 84 00 00 00` | Read source+`84` |
| `111478` | `51 52 57 8B 88 A8 00 00 00 57 6A 01` | Push source values, two native-zero EDI values and selector 1; obtain display this |
| `111484` | `E8 17 F1 F0 FF` | Call original `205A0` |
| `205C2/205C9` | `89 72 08` / `89 72 0C` | Write display+`18/+1C` = 0 |
| `205D0/205D7` | `89 34 08` / `89 42 14` | Write display+`20/+24` = source+`84/+88` |
| `205E0` | `C2 14 00` | Return with all five arguments popped |
| `111489` | `8B 85 4C 49 14 00` | Read pointer at B+`14494C` = manager+`14` |
| `11148F` | `8B 88 0C 04 00 00` | Read manager-source+`40C` |
| `111495` | `89 88 04 04 00 00` | Copy that DWORD to manager-source+`404` |
| `11149B` | `8B 95 58 34 08 00` | **Not executed:** load B+`83458` |

The dimension fixture uses `913/577`, intentionally different from the prior
display fixture's `640/480`. Tests verify all four writes of this invocation,
the neighboring display entries, the unchanged complete source snapshot, and
guards. A second complete source-only run uses `FFFFFFFF/80000001`: original
code preserves all bits without validation or normalization, then stops before
the unavailable manager pointer is read. These values are synthetic test inputs,
not proposed game defaults or server policy.

The manager snapshot starts with `+404=31415926` and `+40C=CAFEBABE`. Its entire
`410` bytes are compared after the run: only `+404..+407` changes, and the native
write log attributes that single DWORD to `111495`. At the final stop ESP is
entry ESP minus `1C`, EAX = MANAGER_SOURCE, ECX = `CAFEBABE`, and the memory page
containing B+`83458` remains unmapped.

**Next need belongs to main's FightComm3 binding work.** The immediately
following instructions load B+`83458` at `11149B`, read its DWORD `+630` at
`1114A3`, then call **`1114AA -> 11FBF0`**. This harness does not perform those
reads or calls and does not substitute CSV indexes for runtime handles. Main's
reported original CSV-loading/handle-binding investigation was not duplicated.

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_initializer.py -v
python -B tools/strike_lab/current_battle_initializer.py --source-prefix
```

**20 tests pass**, retaining all 15 prior tests and adding five focused source
tests. The source-prefix report records 2972279 instruction visits, with
`initializer_returned=false`. The new invocation is the 33rd original `205A0`
call/return; the first 32 belong to the earlier display reset. All older optional
boundaries remain available. Only the initializer, its test, and this note changed.

## Previous Extent: Nonnull Registry Reset

**Continuous original execution now reaches `111469`, before the source-object
read there.** Supply both `display_state` and `registry_state` to `initialize`.
The run starts normally at `1112C0` once, crosses the display reset and
`111461 -> 1AD10`, executes a meaningful nonnull registry reset through its
real return, then executes `111466`. No skip/resume, fake return, instruction
patch, live device, runtime launch, or battle-completion claim is involved.

The proof fixture is an explicit twenty-entry registry: entries 0..18 null,
entry 19 nonnull. Its backing snapshot is a repeating byte ramp, not an empty
or pre-reset pool. This final entry is actually visited and reset. Incoming
ECX is deliberately `DEAD0000`, an unmapped fixture value loaded from
B+`A9DF6C8`; `1AD10` ignores it and loads each this pointer from the registry.

| RVA | Original bytes | Proven effect |
| --- | --- | --- |
| `111461` | `E8 AA 98 F0 FF` | Call `1AD10` |
| `1AD11` | `BE D8 4E 5B 00` | Set registry iterator to VA `5B4ED8` |
| `1AD16` | `8B 0E 85 C9 74 05` | Read entry into ECX and skip null only |
| `1AD1C` | `E8 0F 00 00 00` | Call `1AD30` for the nonnull pool |
| `1AD21` | `83 C6 04 81 FE 28 4F 5B 00 7C EA` | Advance through 20 entries, end-exclusive VA `5B4F28` |
| `1AD38` | `8D 51 10` | First slot starts at pool+`10` |
| `1AD42` | `66 89 72 10` | Store the current slot index as WORD at slot+`10` |
| `1AD96` | `81 C2 90 02 00` | Advance slot by `290` bytes |
| `1AD9F` | `81 FE 00 10 00 00` | Compare slot count against 4096 decimal |
| `1ADCD` | `C3` | Real pool-reset return |
| `1AD2D` | `C3` | Real registry-scan return |
| `111466` | `8B 45 18` | Load source pointer from B+`18` into EAX |
| `111469` | `8B 88 88 00 00 00` | **Not executed:** read source DWORD `+88` |

`1AD30` requires pool storage of `10 + 4096*290 = 290010` bytes. For each
slot S, native code writes the following offsets; all other bytes are preserved:

- Bytes `00,09,0A,98,99` become zero.
- WORDs `0E,2E,288` become `FFFF`; WORDs `70,254,286` become zero.
- WORD `10` becomes the slot's index, 0..4095 decimal, not zero for every slot.
- Byte spans `[AC,254)`, `[256,278)`, and `[27A,286)` become `FF`.

All bytes of the full nonnull pool are compared, including the untouched
16-byte header and preserved gaps. Both pool guards and bytes immediately
outside the registry remain unchanged. All twenty registry pointer values
remain unchanged. Native execution reaches `1AD16` twenty times, `1AD30` and
its return once, and the two-array inner loop 4096*106 times. The earlier 168
battle-record resets and display reset also finish in this same run.

### Precise Next State

At the stop, EIP is VA `511469`, EAX = `[B+18]` = fixture `06900000`,
and ESP is entry ESP minus `1C`. That source page is intentionally unmapped.
The source pointer came from `[renderer+A0]` during the normal initializer
prefix; registry reset did not create or bind its backing object.

The next required source fields are DWORDs `+88` (`111469`) and `+84`
(`11146F`). They are passed to **`111484 -> 205A0`** with selector 1 and two
zero arguments, this = `[B+C]+A8`. `205A0` itself already executes during the
earlier display reset, but this invocation and these source values are not
qualified. Stop before reading them; do not invent them from the display
snapshot dimensions. Later manager/source-resource reads remain outside scope.

The optional registry interface validates twenty explicit snapshots/None values
and exact pool sizes, and requires explicit display storage. All snapshots are
installed before the sole native start; only the executed code mutates them
during the run. The executed configuration qualifies one nonnull final entry,
not a live registry's provenance or every possible registry arrangement.

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_initializer.py -v
python -B tools/strike_lab/current_battle_initializer.py --registry-prefix
```

**15 tests pass**, including main's prior 11 tests and four registry tests. The
registry report records 2972245 instruction visits including REP iterations,
one registry return, one pool-reset return, and `initializer_returned=false`.
The prior no-display and display-only boundaries remain available unchanged.
Only this note, `current_battle_initializer.py`, and its test file were edited.

## Previous Extent: Display Reset

An explicit `display_state` snapshot now extends the same original1112C0 run
through20580 and its three callees to11145B, before the next object-pointer
load/call1AD10. The default narrower fixture still stops at111456 as documented
below. No stopped run is resumed and no callee is skipped or replaced.

The storage size is F66E8 +3096*8C. Tests supply a poisoned snapshot with
explicit synthetic640x480 dimensions, not a client or server default. Original
273C0 calls205A0 32 times (31 zeroed entries, then entry0 dimensions);27400
initializes5000 stride-C8 slots and two counters;27450 clears low flag bits in
3096 stride-8C records. Every byte of the full snapshot and its surrounding
guards is compared, including preserved fields. Rendering/device construction
and actual on-screen output are not executed.

A second integration test feeds context produced by the formal C++ frame and
original world receive function into this initializer. The two DWORDs retain
their exact bits through both stages. These are two explicit native stages
with independently supplied object state, NOT uninterrupted execution of the
intervening main loop or live E2E. All11 tests pass in4.868s. The worker was
closed after main independently reproduced its original9 tests.

For the display-only fixture the boundary remains11145B, loading B+A9DF6C8 before111461 ->1AD10. The latter
consults the global renderer registry5B4ED8..5B4F28 and may call1AD30 for each
nonnull entry. No registry contents or successful renderer initialization are
inferred. Subsequent source-object/resource initialization remains open.

## Baseline Without Display Storage

**One continuous original run from `1112C0` reaches `111456`, stopping before
its call to `20580`.** The former `1113D8 -> 181B0` boundary is crossed through
the real callee and return. The queue reset, context transfer, complete
`11FC40` battle-manager reset, and all 168 record initializations also execute
and return natively. Nine focused tests pass.

At the stop, EIP = VA `511456`, EBP = fixture BATTLE `05000000`,
ECX = fixture DISPLAY `06B00000`, and ESP = entry ESP minus `1C`.
The call at `111456` has not executed. The initializer has not returned.

This is an offline initializer-prefix qualification. It is not continuous
world/TCP entry, live battle acceptance, battle creation, or server authority.
Main owns the world queue tail and TCP entry work. Only the three new initializer
files are owned here; `current_battle_entry.py` is imported but not modified.

## Pinned Input

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base VA `400000`; code addresses are RVA = file offset. Offsets and sizes below
are hexadecimal except explicitly decimal counts. No retired data or leads,
resource files, database, host UI, process attachment, or subagents are used.

## Original Execution

| Caller RVA | Callee | Executed effect |
| --- | --- | --- |
| `1113D8` | `181B0` | `33 C0 89 01 89 41 04 C3`: clear exactly two DWORDs in the supplied input object and return |
| `1113E3` | `11D350` | Check queue backing at `Q+4`; clear `Q+8` and `Q+C`; preserve backing and capacity |
| `111424` | `11FC40` | Reset the full battle record arena, pointer table, attachments, and manager scalar state |
| `11FC94` | `11E6E0` | Resolve each original side/slot/type pointer; 168 real returns |
| `11FCA4` | `11FDE0` | Initialize each `ECC`-byte record, including signed WORD `+1A=-1`; 168 real returns |
| `11FCB7` | `11CA30` | Bind each record's shared attachment to the prebound manager renderer; 168 returns |
| `11CA52` | `11CA90` | Reset attachment state; 168 returns |
| `11CA9A` | `11CFB0` | For repeat bindings, inspect four inactive handles and return; 140 returns |
| `11FD32` | `12AEA0` | Set manager `+2E0/+2E4=1` and associated byte flags |
| `111456` | `20580` | **Not executed: next boundary** |

The `11FC40` loop bounds are original instructions, not harness iteration:
`11FCCE: 83 FE 06`, `11FCE5: 83 FD 0E`, `11FCF9: 83 FE 02`.
They produce 2 sides x 14 slots x 6 types = 168 records.
`11FC51: B9 78 6D 02 00` and `11FC64: F3 AB` first clear
`26D78` DWORDs, or `9B5E0` bytes. The manager is reached by its original call
from the initializer; it is not started independently.

Let B be the battle object and M = B+`144938`:

- Arena A = M+`A7FBDAC`; record i is A+i*`ECC`.
- Original pointer table M+`38` contains all 168 record pointers.
- Attachment bank H = M+`A89738C` = A+`9B5E0`, immediately after the arena.
- There are 28 attachments of stride `2C`; six types share each side/slot's
  attachment. Every record's `+EC8` receives its corresponding attachment.
- Fresh attachments start with `+28=0` in this fixture. The first of each six
  native binds initializes its handles to `FFFF` and stores the renderer;
  subsequent binds take the original inactive-handle cleanup path. These
  intermediate inactive values are produced by original code, not supplied
  during execution.

## State Proven Continuously

The incoming `3EC`-byte context T is copied by original `11141A` to B+`48`.
The earlier packet fields remain raw: T+`28` -> B+`3C` and T+`2C` -> B+`40`,
also retained in the context copy at B+`70/+74`.
`1113BF` tests the low byte of T+`2C` against `FF` and stores its equality flag
at B+`A9EA4C8`. No gameplay meaning is assigned to these fields.

After the manager returns at `11FD6D`, original initializer instructions set
B+`6C=0`, B+`A9E9C74=0`, B+`64=T[18]`, B+`51=FF`, B+`52=FF`, and B+`68=3`.
The tests compare the entire copied context with precisely those subsequent
overwrites. Source T remains unchanged. Queue indices and B+`A9EA4C4` are zero.

## Explicit State Requirements

Every fixture write occurs before the single native run. The harness supplies a
descriptor, root component pointers, the preexisting B+`28` resource pointer,
an explicitly empty string table, writable string-cache globals, input memory,
the arena and attachment bank, and a prebound manager renderer pointer M+`C`.
These are pre-call assumptions; construction and loading of the objects are
not claimed executed. No external resource content is needed by this prefix.

Q = B+`A9EA4B0` has an explicit backing pointer and capacity `1000`; its old
indices are `120/240`. The real queue reset leaves the backing bytes untouched.
With Q+`4=0`, the run instead stops at **`11D367 -> 2C70`**, before the native
assertion call. It has cleared the input object but has not copied the context
or reset the queue indices. No buffer allocation is invented inside a hook.

With an attachment already bound and its first handle set to 7, execution instead
stops at **`11CFE5 -> 1B330`**, before active renderer-record cleanup. The actual
pushed address is renderer+`10`+7*`290`. Thus active prior attachments are not
silently treated as inactive or passed with a fake success.

The normal next call is `111456: E8 25 F1 F0 FF`, targeting `20580`.
Its this pointer D comes from `[B+C]+A8`. The prefix already writes
D+`F66E0` at `111403`, so setting this pointer to null cannot legitimately bypass
the next reset. This fixture maps only the state needed so far.

**The baseline fixture stops before the display-manager object D is reset.** Static
inspection of `20580` shows calls to `273C0`, `27400`, and `27450`:

- `273C0` reads D's first two DWORDs and uses `205A0` to reset 31 indexed entries.
- `27400` resets 5000 decimal slots, stride `C8`, starting at D+`1258`, and
  writes counters D+`F5558/+F555C`.
- `27450` updates 3096 decimal flags, stride `8C`, starting at D+`F66E8`.

These three callees are not executed by the baseline fixture. Their
memory requirements identify the next bounded continuation; no display backing
storage, dimensions, live device, or successful display reset is inferred from
the current sparse fixture. Later initializer calls also remain unqualified.

## Reproduction And Checks

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_initializer.py -v
python -B tools/strike_lab/current_battle_initializer.py
```

The existing Unicorn dependency is reused; nothing is installed. The normal
report records 424165 instruction visits including REP iterations and
`initializer_returned=false`. Nine tests check the single normal entry, call and
real-return counts, exact stop registers/stack, queue/input preservation, raw
entry fields and complete context copy, every record/attachment mapping, guards
before the arena and after the adjacent attachment bank, both earlier failure
boundaries, original instruction bytes, and unchanged executable ranges.
Unknown control flow and instruction-budget exhaustion fail closed through the
existing `NativeRun` guard. No code patch, service stub, fake return, or
skip/resume is used.
