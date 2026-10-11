# Current world music, 2026-09-19

Placement follow-up: `continue_music()` now obtains the actor pointer from its
host's `actor_address` (default unchanged). The new embedded-world host uses
the actual world-relative address and extends the joined scene tail through
`100930`; see `current-embedded-world-20260919.md`. The standalone fixture's
original placement limitation described below still applies to that fixture.

Scope: current original music resolver `F76E0`, registry `F7380/F7400`,
playback `F7520`, and caller interval `10078F..1007B0`. All code offsets below
are RVAs unless marked VA. Mapped-image file offsets equal RVAs; image base
is `00400000`. No retired client source or executable was read.

Evidence image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
(3,174,400 bytes), SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The existing native host verifies this identity before mapping it.

## Integration API

```python
from .current_world_music import NativeWorldMusicMixin
from .current_world_viewport import NativeWorldViewport

class MusicViewport(NativeWorldMusicMixin, NativeWorldViewport):
    pass

native = MusicViewport()
native.install_music(absent_device_fixture=True)
```

Installation preserves CPU context and the complete existing 0x80000-byte
scratch stack. It preserves parser fields at `MESSAGES+4/+8`, verifies and
reuses a populated scene catalog, and refuses to replace a nonnull sound
owner. It allocates and executes the real sound constructor with a null device;
event override is an explicit zero fixture input. Installation is one-shot.
No CMake, shared scene, viewport, or camera file is changed by this sidecar.

After actor/scene loading, main may directly run its continuous
`_slice(0x10078f, 0x100831)` with `ESI=WORLD`, `EDI=ACTOR`, and its original
caller stack. Do not call `continue_music()` first when testing that joined
interval. This sidecar owns no code after `1007B0`; the main viewport oracle
owns `46520/103C70`. The joint test composes the mixin with the existing
`NativeWorldViewport` without changing its inheritance or any shared file.

Independent probes are `resolve_music(area, kind, scene, combat=False)`,
`play_music_without_device(slot, event=0)`, and `continue_music()`.
The last executes exactly `10078F..1007B0` using the actor already in memory.
All three preserve CPU context and stack even on exceptions, while retaining
native music memory changes and observation logs. `music_preserve_caller()`
also exposes this context manager for external probes. `music_state()` reports
current index, playing flag, device pointer, registry paths and sound slots;
it does not label EAX residue from the void-like `F7520` as sound success.

Standalone host: `NativeWorldMusic(absent_device_fixture=True)`, inheriting
`NativeColdWorldActor`. Dependencies are the existing pinned-image host,
Unicorn, current source parser/decompressor, and its CRT/MFC/current-directory
adapters. The only new service implementation is bounded CRT `calloc` at
`147E23`, accepted only from return RVA `59AAD` with `(144, 0x1A4)`.
Native constructors, readers, lookups, resolver, path builder, sound-slot
lookup and playback functions are not stubbed or patched. Hooks on game
functions only record observations or reject an unqualified device branch.

## Exact Sources And Reader

Actual current file: `God2/Data2/Patch/Comm/gamedata.csvZ`.
Compressed SHA-256:
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
Decoded SHA-256:
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.

The selection table is `Map_City_Coordniate`, not a separate invented music
table. Its header is decoded source line 21019; 144 records are lines
21020..21163, decoded byte interval `[2462531, 2483449)` including CRLF.
Offsets refer to the decoded original bytes, not the compressed container.

The helper checks both hashes and all fixed-field bounds before native work.
It executes original `1760/1EC0/17B0` on the complete compressed file and checks
the entire decoded output against the pinned source. This larger source has
an explicit 300,000,000-instruction / 90-second decompression bound. A missing
catalog is then loaded from its actual row interval, with CRT text-mode
CRLF-to-LF translation, through the original dispatch and complete reader:

| Evidence | Offset / behavior |
|---|---|
| Dispatch section literal | VA `58A08C`: `Map_City_Coordniate` |
| Section comparison / call | `565AB..565EC`, call `59A80`; return `565F1` |
| Reader allocation | `59A97..59AA8`: `144 * 1A4` via CRT calloc |
| Table storage | `MESSAGES+D2ABA`: signed WORD count; `+D2ABC`: pointer |
| Row loop | `59AC8/59ACA` invokes `51A90`; repeats through `59D67` |
| Line/token reader | `51AAB`: CRT fgets, return `51AB0`; `51AC6`: `51BE0` |
| Field 8 | `59C20` reads string; `59C2E..59C47` copies into record `+30` |
| Field 9 | `59C52` reads string; `59C60..59C79` copies into record `+70` |
| Packed area / scene | record `+F0`: area low 6 bits, scene upper 10 |
| Kind | record `+F4`, low 2 bits |
| Exact scene lookup | `59D80`; searches all rows, returns first match |
| Area/kind lookup | `59E00`; searches all rows, returns first match |

When the main scene already loaded its table, installation verifies every
record's selector and both music strings against the same pinned source and
keeps that pointer. It does not reload or replace the main scene catalog.
The independent cold host exercises the full reader rather than copying
Python-generated records. Top-level loading of unrelated gamedata sections
is not claimed; the bounded dispatch starts with the verified section name,
count, and row-stream position.

## Caller And Selection

`10078F` reads kind from `ACTOR+10`; `100794` reads scene from `+14`;
`100798` reads area from `+18`. It pushes zero at `10079C`, then scene, kind,
area, and calls `F76E0` at `1007A3`. The effective arguments are WORDs:
`(area=2, kind=2, scene=15, mode=0)`. Upper halves of word-loaded registers
are not additional selector bits. `1007A8` pushes the returned index and
`1007AB` calls `F7520`; its return is exactly `1007B0`.

| Mode | Native lookup sequence | String field |
|---|---|---|
| 0 | exact `(area, scene)` at `F7774`; first `(area, kind=0)` at `F7796`; first `(area=1, kind=0)` at `F77B9` | `+30` |
| nonzero | exact `(area, scene)` at `F76FC`; first `(area, supplied kind)` at `F7721`; first `(area=2, kind=0)` at `F7744` | `+70` |

Thus normal-mode fallback deliberately ignores supplied kind 2. Initial
area 2 / scene 15 is absent from the table; the first area 2 / kind 0 record
is CityI1, area 2 / scene 4, line **21082**. Its decoded row byte span is
`[2470868, 2470997)`; music field 8 is `[2470903, 2470931)`:
`data2\Music\city\city_I1.wav`. `F77A5` calls `F7400`, return `F77AA`.
On a freshly constructed registry this returns **slot 4**.

The same row's combat field 9 occupies `[2470932, 2470958)`:
`data\Music\Fight\att_e.wav`. Initial combat-mode probe `(2,2,15,1)`
falls through to the global area-2/kind-0 lookup, return `F7758`.
Changing only kind to 3 selects the first area-2 cave row through the local
kind fallback, return `F7735`, with the same combat path bytes.

Source-selected direct variants tested include `(1,0)`, `(1,12)`, `(2,0)`,
`(2,2)`, `(2,4)`, `(2,43)`, `(16,9)`, each with its source kind and both
music columns. Normal/combat direct registry calls return to `F7788/F7710`.
Additional explicitly synthetic missing-scene probes cover global fallbacks.

`F7380`, called by the world constructor at `65418`, fills 30 sound slots with
`FFFF`, clears the 30 x 128-byte registry and playing flag, and copies four
image seed strings from VAs `59A62C`, `59A6AC`, `59A72C`, `59A7AC`:
`\data2\music\Fight\att01.wav` through `att04.wav`. Count becomes 4 at
world `+15AAD380`; paths start `+15AAC480`; slots start `+15AAC444`;
playing is `+15AAD384`. `F7400` deduplicates case-insensitively through CRT
`151DE0`, otherwise appends and returns an index. Native capacity is 30;
the current catalog contains 38 distinct case-folded paths across both
columns, so registering the entire catalog in a single lifetime is not
claimed safe. Loader tests load all rows without registering all paths.

## Playback And Device Boundary

`F7520` reads world `+A87D9C4`. A positive event or input `FFFF` substitutes
an image pointer from VA `59A82C + 4*event`: event 0 is the empty string,
1 is `\data2\music\XMas.wav`, 2 is `\data2\music\NewYear.wav`.
The wrapper bounds event inputs to these three entries; it does not invent
additional entries. Native signed index checks are at `F755A/F7564`;
current-index suppression is at `F756D/F7573` using VA `59A628`.

For a new valid index, `F75D7` runs `12F550` to build the original full path.
If its sound slot is negative, `F75F4` calls `4DD90`. This scans 32 CString
paths at sound-owner `+7A84`, then finds a free slot in `+6408`, stride `14`.
The returned slot is stored even if subsequent playback fails.

`F7620` calls `4E660(slot, path, 1, 1, 0, 0, 0)`. At `4E67B` EAX is zeroed;
`4E67D/4E680` tests the device pointer at `[sound_owner]` and jumps directly
to `4E76A` if null. Its normal SEH/stack epilogue returns 0 with `ret 1C`.
`F7625/F7627` then branches to `F7661`, writing current index `FFFF`.
It does **not** call `4EC90` or set world playing to 1. Initial result:
registry index 4, cached sound slot 0, current -1, playing 0, device 0.

This null device is an explicit supported **fixture branch**, not evidence of
the state of a running user's client. The real sound constructor `4D9F0`
executes unchanged, including CString construction, decompressor construction,
and its null-device write at `4DA3A`. Original object allocation is `15360`
bytes at `DB2C`; constructor call `DB4E`; owner assignment `DB61` to root
`+430`. World binding reads that root field at `649E6` and writes world
`+A7E05E8` at `649FD`. The sidecar supplies this owner binding explicitly.

Original device initialization is separately called at `DB67 -> 4DE30`.
It allocates a `74`-byte wrapper, calls `140040`, then `1400A0` at `4DEA0`.
The creation path calls thunk `143DC2` (indirect slot VA `57005C`) at
`1400AC`, and only on success invokes the device vtable at `+18` (`1400CE`).
A negative initializer result takes `4DEA9..4DECC`, diagnostics/destruction,
and clears the owner device at `4DEC6`. This initialization path and device
creation are **not executed** by this fixture.

On the device-present path `4E660` additionally checks slot `<32` and a
nonempty path, allocates/reuses a buffer, and calls the file loader `4E080`.
`4E08E` opens the selected path in `rb`, then reads its bytes before
`4E103 -> 4ED30`. Those calls are unreachable in the tested null-device
branch. Observation hooks fail closed if a nonnull device, `4E080`, or the
success-marker call `4EC90` is reached. There are no fake device handles or
successful sound returns. No live audio or WAV decoding is claimed.

## Actual Current Audio Files

These exact current files were read and SHA-pinned in tests. Each begins
with a RIFF/WAVE container header; no playback follows from file presence.

| File under God2 | Bytes | SHA-256 |
|---|---:|---|
| `Data2/Music/City/City_I1.wav` | 1813818 | `64860c40c510bdaabadf2d92ab44c425e732b4d4214fcd210d1bcbaa965c93d1` |
| `Data2/Music/Field/field_i01.wav` | 3426648 | `4e79f25102fdf523f9cd7cb4e75ed12d87d22ed81872f55edb47581535d498b0` |
| `Data2/Music/maze/MAZE_I01.WAV` | 3274430 | `77ba30ed95727ce93f6e7c3fb47fea0a7cebf3b7e7bf86a11add3a9c6dfff42e` |

Literal current catalog paths `Data/Music/Fight/att_e.wav` and `att_s.wav`
are absent, as is the image event path `Data2/Music/NewYear.wav`. The current
tree does contain `Data/Music/NewYear.wav`, but there is no native evidence
here authorizing substitution. Paths remain byte-exact. The null-device
branch does not open any of these files, including the present initial WAV.

## Verification

Run only the owned research tests:

```powershell
python -m unittest discover -s tests/research -p test_current_world_music.py -v
```

Final bounded run: **9 tests passed in 179.129 seconds**, including the
continuous music/viewport integration test; process exit status 0.

The suite verifies complete original decompression/reader dispatch, all
loaded music fields, exact initial and source-selected resolver paths,
event and invalid-index behavior, native playback failure and cached-slot
retry, source identity rejection, nonnull-device rejection, and full caller
register/stack preservation. Its composition test installs on the existing
viewport host, preserves the scene catalog, runs original cold actor/scene
loading with the current body fixture, then executes **continuously from
`10078F` to `100831`**, covering music and the main's native camera/pool
propagation. It checks world/indoor/NPC/role camera `(840,240)` from original
`(1240,540)`, while the optional renderer remains its native null input.
The independent `continue_music()` API is also tested without modifying
that camera or the caller. The body is only runtime input; no retired
provenance file is opened.

Next boundary: `100831` compares byte `[ESI+1539684C]` with 2, branching to
`1008B1` on equality. It reads the world's embedded actor, whereas the existing
actor/scene fixture constructs its actor at `ACTOR=07800000`. That is distinct
from `WORLD+1539683C`. The main task reported that extension to `100930`
took a different UI branch and failed at `1077FA` because the embedded actor
was not initialized. This sidecar stops before `100831`, does not copy actor
fields into the embedded object, and does not claim movement-ring/message
initialization or the longer interval. Original actor placement must be
resolved before extending that boundary.
