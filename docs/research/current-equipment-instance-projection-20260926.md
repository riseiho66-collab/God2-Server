# WPN1/2 equipment instance projection and native response continuation

2026-09-26. Follow-up to `current-player-equipment-frontier-20260926.md`.
Scope is ordinary weapon slot34 and backpack0..29. This lane changed no
Application, DB, client, shared CMake or desktop state. Offline data are explicit
synthetic instances, never recovered ownership or original weapon generation.

## Result and commands

`tools/strike_lab/current_equipment_projection_20260926.py` executes the current
PE's complete3B/41/3C consumers, refresh, equipment sound calls and UI28 producer.
No native game function is replaced or stopped before its return. The only OS
adapter is imported `WinMM.timeGetTime`; it returns a fixed fixture timestamp.
The original sound constructor runs, leaving the genuine absent-device state.

```powershell
python -X utf8 -B -m tools.strike_lab.current_equipment_projection_20260926
python -O -X utf8 -B -m tools.strike_lab.current_equipment_projection_20260926
python -X utf8 -B -m unittest discover -s tests/research -p test_current_equipment_projection.py -v
```

Both interpreter modes PASS with identical reports:

- 72 equip/swap/unequip/re-equip transitions across bag0/12/29,
  clear41/3C, synthetic highWORD0001/8041/FFFF.
- 73 complete49A330 UI requests produce exact28 records through native queue;
  the additional highWORD0000 case also succeeds.
- 16 equipment3C cases vary key0/1/2/FFFF and count0/1/127/255.
- 90 complete sound-entry calls: 54×29D, 36×29E, 90 OS timestamp calls.
- Actual original WPN ROM chunks feed enabled native controls. The original
  binder/action lookup/sprite refresh updates the correct image pointers and
  hides empty equipment. No renderer or sound game callee is stubbed.

Current PE SHA256 is
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
The existing pinned mapped-image metadata parser is accepted only after every
one of its allowed code spans equals this current PE. All new consumer/UI code
runs from this SHA-qualified current PE. Every mandatory check uses explicit
exceptions; `-O` cannot bypass validation. The CLI emits its JSON only after all
checks pass and creates no persistent PASS artifact on failure.

## Packet contract and after-state projection

Widths below include opcode; integers are little-endian:

| Record | Bytes | Observed effect |
|---|---|---|
| `3B count:u8 slot:u8 opaque:u16 instance[20]` | 25 | Copies all20 instance bytes; WPN is nonstackable so count becomes1 |
| `41 key:u16 slot:u8 count:u8` | 5 | Sets signed-byte count and only instance lowWORD; count<=0 clears count/key |
| `3C key:u16 slot:u8 count:u8` | 5 | Bag subtracts count; ordinary equipment30..37 clears count/key regardless of key/count |

Native consumers: RVA98DD0, 991E0, 98FD0 respectively. S2C3C is not an
authoritative identity check: the client will clear equipment even with a wrong
key/count. The server must enforce ownership/revision/request identity itself.

Tested sequence for each affected slot is clear41 (or clear3C for a known
single-count source), then full3B for a nonempty after-state, then41 with absolute
key/count1. On swap both slots are cleared before their complete new instances
are sent. Clear41 is the suitable absolute operation for reusable projection;
3C subtraction is not idempotent for general backpack stacks.

Every nonempty after-state exactly matches the source20bytes, including
nonzero highWORD and all16 additional bytes. The test instances include:

```text
WPN1: 01000100070e151c232a31383f464d545b626970
WPN2: 02000100131a21282f363d444b525960676e757c
```

These bytes are intentionally synthetic and have no recovered enhancement,
durability, attack, grant or legal-instance meaning. Opaque3B bytes are A5/5A to
verify they do not replace any instance byte.

**Empty slot does not mean20 zero bytes in native memory.** Both41 and3C clear
count and lowWORD key while retaining the previous18 bytes. The oracle checks
that exact behavior after uninstalling WPN2 from34. Consumers change only the
addressed inventory slot; UI requests themselves change no inventory records.
Do not send a fake occupied item to erase stale tail or acknowledge pending.

## Pending and repeat operation

UI+85608 is set to1 by producer96550. Ordinary equipment3B with pending!=0
calls sound29D through44E140, returns from the entire native audio path, then
sets pending0. Bag3B never clears this pending. Neither41 nor3C clears it.

| Transition | Resulting pending |
|---|---|
| Equip bag→34 | 0 after real equipment3B |
| Swap bag↔34 | 0 after real equipment3B |
| Unequip34→empty bag, equipment empty | 1 |
| Subsequent UI double-click of that bag item | Produces28 successfully despite1 |
| Subsequent real equipment3B | 0 |

The complete UI request, guard, producer and queue executed after unequip,
proving that this retained field does not block the tested ordinary weapon
double-click path. This does not prove every other client path ignores pending.

## Why nonzero instance bytes still support C2S28

49A330 reads the instance lowWORD key and calls459A60. For a double-click event
bit04 it reads the definition's byte+11A; bit04 selects49B5E0→96550. Native WPN
source rows1/2 at lines4804/4805 produce definition flags `F4 02`. Source flags,
396-byte definition, and20-byte owned instance are separate structures.

The producer branch does not require a nonzero instance highWORD. The oracle
demonstrates0000/0001/8041/FFFF still route28 and preserve supplied instance
bytes. It is incorrect to infer that all these highWORD values are valid
original weapon classes. Fresh tooltip rendering separately switches on
`(instanceDWORD0 >> 16) & 0x3F`, so legal source-backed instances must still be
qualified independently. Successful28 generation is not an enhancement or
equipment-stat formula.

The full49A330 calls49B820→4B5BE0. This oracle deliberately supplies the exact
previously hovered tooltip cache (key, coordinates,20bytes), exercising the
native cache-hit return. It does not stub the tooltip function. It also does
not claim that arbitrary synthetic metadata is safe for a freshly generated
tooltip. Live fresh-tooltip acceptance remains a separate check.

## New complete resource binding and sprite continuation

Native481700 is the missing post-parser item-resource binding edge. When
`DWORD(definitionOwner+D2AA0)==0`, it scans indexed items, adds0x41 to the initial
definition WORD+116 RomMaps group, resolves icon ID at+114 through41AE70, writes
the resulting action at+118, then marks the binding pass complete. Its fallback
searches icon1000 in the first item's group if the requested action is absent.

Current RomMaps row0 (gamedata line58) maps IDs1..6000 to
`data2\ItmImg\WPN01.rom`. Initial WPN parser output is group0/actionFFFF;
**this is not the loaded runtime icon binding**. The oracle runs the complete
481700 loop and41AE70 against original ROM action headers, obtaining:

| Item | Original name | Runtime group/action |
|---|---|---|
| 1 | 菜刀 | 0041 / 0000 |
| 2 | 砍刀 | 0041 / 0001 |

`Data2/ItmImg/WPN01.romZ` compressed SHA256:
`caa72d4dccafacd44a27346f3a8db2e15319960bf003966b835416ed6c189499`.
Decoded SHA256:
`eef95acad680643cdf07f570f124a273f7dfe112061596ef074736732ff9395f`.
There are180 actions; first two ACT_DATA IDs are1/2 and metadata tuples
`(1,0,400,300,1,1)` / `(2,0,400,300,1,1)`.

The harness relocates actual original palette/image/action/step/pool chunks
into the native resource-bank layout. Complete consumers then execute
49B850→5068C0→41EA00→41E710→427160/4271E0 against enabled slot controls.
After each positive projection the sprite image pointer equals the correct
original WPN image chunk; after clear its native visibility state is3 (hidden),
and after positive projection2 (shown). No ROM file-loader or display-device
blitter execution is claimed, and no pixels were captured.

## Audio dependencies and available sources

44D9F0 constructs the sound owner with device pointer0, enable byte+7F19=1.
44DB90 selects a sound channel and calls imported timeGetTime. 44E320 calls
playback only when enable byte!=0, device pointer!=0 and channel<120h.
The tested complete native absent-device path returns normally, allowing the
equipment pending clear. Actual audible playback remains a live device test.

Current `Data2/Snd/commsnd.csvZ` compressed SHA256
`e5704115a5ec39cd97f9712dd5bfb1163e502671faaae65d7f45d9e541a11f0d`, decoded SHA256
`b34f206476b0b307fdbc153b1322c680698fc3bf41f29102a4aa1c1a8cc6dc5f`.

| Sound | Source line | Existing file | Bytes / SHA256 |
|---|---|---|---|
| 29D (669) | 672 | Data2/Snd/ItemEquip.wav | 32554 / f52f5b7d06c7f83f2c7be8bab885af78c0e90b502119968d1f8d345a838e91ea |
| 29E (670) | 673 | Data2/Snd/ItemPlace.wav | 12650 / b0c8e1b4aabb7f30710e754b2fb245194bfd0e561f3a640127b26aa12377d766 |

The oracle validates the source rows, file hashes and RIFF/WAVE headers.
An open inventory panel makes bag3B call29E; equipment3B with pending calls29D.
Existing files prove availability, not successful audio device playback.

## Read-only live acceptance fields

All offsets below are hexadecimal unless stated otherwise. These are read
locations, not instructions to inject values into a running client.

- `slot = UI+8560C+24decimal*index`: signed count at+0; instance20bytes at+4;
  key at+4; full highWORD at+6. Weapon34 instance starts `UI+85940`.
- `DWORD(UI+85608)` pending; `BYTE(UI+85ABC)` last double-click slot.
- `D=DWORD(UI+CFF70)`, definition pointer=`DWORD(D+B2D40+4*key)`;
  CP950 name at definition+8, flags+11A/+11B, source icon ID WORD+114,
  bound resource group/action WORDs+116/+118. `DWORD(D+D2AA0)` is binding status.
- Tooltip cache: `WORD(VA005B7830)` key; `VA005B7838`20bytes; type
  `WORD(VA005926B0)` (12h for this inventory wrapper); x/y WORDs at+2/+4.
  Compare cache bytes to the hovered bag/equipment instance; nonempty cache
  alone does not prove that tooltip was freshly rebuilt after the response.
- `W=UI+E2170`, panel=`int16(UI+232DC8)`, node=`W+818+panel*2A08`;
  node flags&20 means open. Control=`node+A0+slot*64` (stride100 decimal),
  enabled byte+0; absolute RECT four int32 at+10.
- `R=DWORD(W+8)`, node render handle=`WORD(node+4)`; object=`R+10+handle*290`.
  Per-slot action WORD at object+180+2*slot; sprite handle WORD at object+AC+2*slot.
  `S=DWORD(R+4)`, sprite=`S+1258+handle*0xC8`; byte+0 is2 shown/3 hidden;
  image pointer DWORD+8C, palette pointer DWORD+94. Validate handles before reads.
- `audio=DWORD(UI+CFF5C)`: device pointer DWORD+0, enable BYTE+7F19,
  next-channel DWORD+7F0C; NUL filename at audio+4+soundID*25decimal.
  Channel record=`audio+6404+channel*20decimal`: sound WORD+0, state DWORD+4,
  playback object DWORD+C. A successful caller return/pending0 does not prove
  the device played audible audio.

Live integration must compare actual saved20bytes through equip, swap, unequip,
next equip and reconnect, while checking the source-backed icon bindings and
tooltip after real input. Neither this oracle nor the proposed inventory
projection computes player stats, repairs appearance, grants an item, or
establishes an original server C2S28 response-selection policy.
