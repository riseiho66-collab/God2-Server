# Current Monster Inspect Identity: Lane 5

Follow-up: [native pet2 stat labels](current-pet2-stat-labels-20260920.md)
resolves13 numeric controls from the original ROM background and coordinates.
Body10/12/14/16 is attack/defense;24/26/28/2A is strength/constitution/
intelligence/speed. The original unknown-label statements below describe this
lane's earlier boundary; wild identity and original-value gaps remain open.

New concrete source: **S2C FB, 73 logical bytes**, reaches the current second
generation pet panel through `691B0 -> 858B0 -> A52A0`. Original instructions
copy its 72-byte body into a slot-selected record, and original `A40C0` selects
that same record and looks up its metadata key. Twenty numeric display inputs
are newly executed. This is a useful original pet-inspect receiver, **not a
proof of wildmonsterjoin or original wild-monster values**.

The separate S2C3B tooltip now has six source-labelled numeric consumers:
level, current lifespan, strength, constitution, intelligence and speed.
These values come from the received item instance, not NewCombatPet_Category.
No wild-to-pet conversion, stat preservation, capture eligibility, four attack/
defense labels, or complete gameplay attribute model is established.

## Scope and Source Authority

Only the matching new tool, tests and this document are added. No client,
desktop state, production DB, runtime/build/shared file or existing research
helper is modified. No live process, network, UI, battle dispatcher, child
agent or retired XJZ/Classic source is used. Source reads and offline Unicorn
execution are the only analysis operations. The CLI emits JSON to stdout.

All native addresses are hexadecimal RVAs, BASE `400000`, file offset=RVA.
The pinned image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

| Current client file | Raw SHA256 | Decoded SHA256 |
| --- | --- | --- |
| `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` | `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815` |
| `Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` | `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8` |

JSON retains the original source records, line/decoded offsets, raw bytes and
hashes, exact code-span bytes/hashes, actual instruction visits, memory reads,
writes and native call arguments. Changed source/image hashes fail closed.

Prior current-monster numeric/base/combat/rewards/side/identity evidence and
companion instance/state/progression/growth/incubation documents were read
before selecting the new consumer. S2C30/AA040, 31/AA200 and 39/AA9E0 are
already covered by character-binding/state/scalar-bootstrap research; they
are not new findings and are not rerun. Existing 3B store/copy evidence is
reused, without repeating its slot matrix or Quality/Star tests.

Main's EnyName catalog is not recomputed. Names and source labels never join
numeric data here. A future wild join must preserve the actual native key or
the versioned composite source identity, including area/scene/ordinal and
variant context. Pet template key plus inventory slot does not independently
identify a persistent pet instance or its prior wild encounter.

## FB Source to Record to Consumer

Let `M` be the opcode-first message, `B=M+1`, `O` the world owner, and
`P=DWORD[O+232EBC]` the pet2 panel object. Its assertion string at `191658`
names `src/playlib/pmfpet2.cpp`; this is additional context, not field semantics.

| Stage | Exact current native relationship | Evidence |
| --- | --- | --- |
| World dispatch | `DWORD[6B5D4+4*FB] = VA4691B0` | Static table checked |
| Logical length | `DWORD[1324+4*FB] -> 1312`, returns `49h` | Static original function checked |
| Body routing | `691B0` advances M; `691BD -> 858B0` receives tag FB and B; `85C72 -> A52A0`, ECX=P | Newly executed continuously |
| Slot guard | `A52A8` reads B+2; `A52AC -> A5070`, low-byte slots 42..44 | Newly executed |
| Identity guard | `A52BA` reads WORD B+0; `A52CD -> A5090 -> 59A60` | Newly executed |
| Metadata selection | Low WORD key in `6D61..7F58` passes the outer range; getter rejects key `>=7F58`; lookup is `table+B2D40+4*key` | Original guards/getter executed |
| Record store | `A52DE..A52EF` computes `P+48h*(slot-42)`; `A52F3 rep movsd`, 18 DWORDs | Newly executed; stop before A52F5 |
| Inspect selection | `A40DF` reads selected slot at P+D8; `A4105` selects the same 72-byte row; `A4121 -> A5090` validates it | Newly executed |
| Inspect metadata | `A4134` reads the selected row's WORD key; `A413E -> 59A60`; ESI receives the actual parsed metadata pointer | Newly executed; stop before A4151 |

The receiver does not compute any scalar in the copied record. Every one of
the 72 bytes is packet supplied, including zero, high bits and unused fields.
The row key is a native item metadata key. There is no area/scene/ordinal or
variant translation in this executed chain. Identical text is never compared.

Two current NCP source rows, keys **28001 and 28002**, are parsed by original
tokenizer/accessors and complete `59420`, then registered by original `59A20`.
First-match native tag array `1897EC` selects NCP at index34. Native allocations
are staged with the existing zeroed396-byte row precondition, and existing
RomMaps setup is reused. This is not the full gamedata/file loader. The first
row is source line19675, decoded offset2220038, SHA256
`dbbeb3a0d51b7195eb4391a8397dad6def12fc430742f7e216e893b723341f42`.
Record name bytes come from source column4, and metadata byte+122 comes from
column32 via `59820/59829`. Neither is used to synthesize FB numeric values.

## FB Numeric Display Inputs

The following are independent original display slices. Each starts with the
same selected record pointer from the executed selection prefix, and stops
before `1077C0`. Renderer calls and intervening UI effects do not execute.
UI field numbers are exact control indices, **not recovered field names**.
Body offsets are hexadecimal; opcode-first offsets are body offset+1.

| Body input | Extraction | UI field | Stop before call |
| --- | --- | --- | --- |
| DWORD+04 | low14 bits | 1 | A41FC |
| DWORD+04 | bits14..24 | 2 | A4229 |
| DWORD+0C | low14 bits | 3 | A4253 |
| DWORD+0C | bits14..24 | 4 | A4283 |
| BYTE+03 | unsigned byte | 5 | A42A9 |
| WORD+10 / +12 / +14 / +16 | unsigned WORDs | 8 / 9 / A / B | A4343 / A436D / A4394 / A43BB |
| WORD+24 / +26 / +28 / +2A | unsigned WORDs | D / C / E / F | A43E2 / A440C / A4433 / A445A |
| WORD+18 / +1A / +1C / +1E / +20 | unsigned WORDs | 14 / 15 / 16 / 17 / 18 | A4481 / A44AB / A44D2 / A44F9 / A4520 |
| DWORD+08 | bits28..31 / bits24..27 | 11 / 12 | A45E9 / A4613 |

Each stop records `(renderer, handle, control, format, numeric_argument)`.
The handle is consumed/staged as a low WORD; raw upper register bits remain
in the report. Tests compare its low WORD and retain the complete pushed DWORD.
Unsigned numeric extraction is checked with zero,7FFF,8000,FFFF and distinct
packed patterns. These patterns are diagnostics, not observed pet attributes.

Other static leads in this same function remain unexecuted: DWORD+8 low24
floating conversion at A4151..A418A; DWORD+4 high7 bits and literal100 at
A42F8..A431C; category and skill/other packed suffixes from A4525/A462A onward.
Native category lookup uses row BYTE+3C and low nibble of BYTE+2C at
A453E/A4562. No category loader sweep or speculative formula is run.

The first 20 numerical sinks do not by themselves label HP, MP, attributes,
elements, four attack/defense fields or their base/current/max semantics.
In particular WORDs+24..+2A are not called wild four attack/defense here.
Bind the pet2 control definitions/resources before assigning those names.

## 3B Labelled Tooltip Path

The prior executed instance proof supplies `record=M+5`, copied as20 bytes by
`98E2B` to `O+85610+24*slot`, then by `87416` to tooltip UI+3AC4. This lane does
not rerun those existing copies. It executes the previously stopped wrapper
through original `876AC -> 59A60` and stops at `876C9 -> B5BE0`. Stack arguments
retain the instance WORD key, native parsed metadata pointer and instance pointer.
The newly executed type switch reads `(record DWORD+0 >>16)&3F`; value34 uses
selector15 at `BC1D0+33`, table `BC1C4`, reaching **B77DC**. Value32 instead
reaches B6F0E. Packed type and low-WORD identity are separate packet fields;
metadata lookup does not validate their agreement in the executed wrapper.

| Display label | ProgramMsg ID | Instance field | Opcode-first 3B source | Formatter stop |
| --- | --- | --- | --- | --- |
| Level | 84 | BYTE+13 | BYTE M+18 | B783D |
| Current lifespan | 575 | BYTE+11 &7F | BYTE M+16 &7F | B783D |
| Constitution (source C5E9) | 73 | WORD+06 | WORD M+0B | B78AD |
| Strength (source A44F) | 74 | WORD+04 | WORD M+09 | B7920 |
| Intelligence (source B4BC) | 72 | WORD+08 | WORD M+0D | B7993 |
| Speed (source B374) | 75 | WORD+0A | WORD M+0F | B7A03 |

ProgramMsg rows72..75 are decoded offsets89018,89025,89032,89039, physical
lines2098..2101. Row84 is offset89108/line2110; row575 offset97712/line2601.
Source-backed message strings/pointers are explicitly staged; the full message
loader does not run. Actual native inline lookups select the corresponding
one-based label slots, and actual masks/shifts push the numeric arguments.
The formatter `147AF7` never runs. Consequently this proves labelled numeric
arguments, not rendered UI, pet ownership or live protocol acceptance.

These six labels must not be transplanted onto FB fields just because they
look similar, nor onto S2C31 companion fields. The two packets can share a
template/slot vocabulary without proving the same instance or transition.

## Other Path and Exact Missing Join

**S2C E3, 53 bytes**, is an additional static old-pet lead, not executed here.
Table target6919E calls A2B70. Body WORD+1C is an item key, BYTE+26 is slot42..44.
A29A0 admits keys13201..14200 or24001..28000 with nonnull59A60 metadata.
A2BC7 copies52 bytes to `O+9E50+52*slot`. Its inspect continuation at A1CF0
is unqualified by this lane. E3 must not be confused with FB or the3B instance.

The existing capture-result relay and side-flip experiment remain exactly at
their prior boundaries. Their result/status and side change do not establish
an E3/FB/3B emission, a persistent identity conversion or retained wild values.
The exact ASCII literal `wildmonsterjoin` is not present in this pinned image;
this limited observation does not rule out an unnamed native transition.

To prove the proposed wildmonsterjoin interpretation, still required are:

1. An actual capture/recruit transition linking a versioned native wild
   identity/variant to the concrete new pet slot/key and instance lifetime.
2. The original sender of FB/E3/3B values, with the same event/identity, and
   evidence distinguishing preserved wild attributes from new pet generation
   or conversion. A synthetic packet or slot relocation cannot supply this.
3. Pet2 control-label bindings and complete field semantics, followed by any
   still-missing upstream values. Neither schema discovery nor item description
   bonuses qualify wild stats or an all-monster dataset.

`wild_identity_join=null`, `wildmonsterjoin_proven=false`, original wild numeric
values recovered=0, `runtime_eligible=false`. This is not a global absence claim.

## Verification and Stop

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest tests.research.test_current_monster_inspect_identity -v
python -B -m tools.strike_lab.current_monster_inspect_identity --summary
```

**5 tests passed in2.996 seconds, no skips, exit0.** Summary CLI also exited0.
Tests cover actual source parsing/indexing, two native identity/slot cases,
exact18-DWORD FB copies, same-record selection/getter, twenty numeric sinks,
six labelled tooltip fields, changed type routing, two distinct identity
rejection boundaries, changed-image rejection and forbidden renderer entry.
No broad catalog/null sweep is performed. Initial failures were harness-only:
a range endpoint omitted the final bytes of a RET instruction, and a test
incorrectly compared the entire handle DWORD instead of its consumed low WORD.

Original image code is read/execute, packet/instance/metadata inputs are native
read-only, writes are limited to the chosen72-byte row and stack. Metadata
loading reuses only the existing decimal CRT adapter. No game/renderer result
is fabricated. New consumer slices have5000-instruction/one-second bounds;
the reused row parser retains its50000-instruction/one-second bound.

Stopped native execution at A52F5, A4151, the listed formatter/renderer calls,
and identity rejection sites A5390/A50D7. No test process was manually killed;
all synchronous Python test/CLI processes exited. No background test, server,
client, debugger, capture process or worker remains from this lane.

Changed files:

- `docs/research/current-monster-inspect-identity-20260920.md`
- `tools/strike_lab/current_monster_inspect_identity.py`
- `tests/research/test_current_monster_inspect_identity.py`
