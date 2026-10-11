# Battle identity cache provenance

## Scope and outcome

The owner's PK-opponent hypothesis is still open. This closes one specific
edge: logical1C variant2000 uses FAC70/FAD20 to retrieve strings and one byte
from an existing world-role cache. These getters do not retrieve attack or
defense. This is not evidence that every opponent packet lacks abilities.
Original identity-bound wild-monster attack/defense recovery remains zero.
No production database or gameplay values changed.

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are RVAs, image base400000.

## Native producer and consumers

- FC960 searches128 entries, stride268(hex)/616(decimal), comparing a DWORD
  identity at owner+18+616*slot. Missing lookup returns signed AX=-1.
- FC1C0 allocates the first entry with identityFFFFFFFF. Full construction
  calls resource/render helpers and is NOT executed by this test.
- FC2C3..FC33F is an intact no-call slice inside FC1C0. It masks the supplied
  record DWORD0 withFFF, stores identity at entry+0, and copies NUL strings
  input+1C/+2C/+3C into entry+4/+14/+24. Entry=owner+18+616*slot.
- FAC70 executes FC960 then reads those three strings. On a missing ID it
  clears the first two outputs only; the third remains untouched.
- FBB50 writes its supplied byte into entry+7B. Its renderer-null branch is
  qualified here, not its nonnull rendering callee.
- FAD20 executes FC960 and reads entry+7B (owner+93+616*slot). Missing ID
  clears the output byte and returns0.
- Existing original1C branch calls these at11626F/1162E4; its owning pointer
  is battle+2C. The prior branch investigation establishes the call sites;
  this new test does not execute the whole battle parser or create a PK match.

## Upstream references and remaining work

Statically inspected direct calls69937/69A1E pass the world owner
world+15383410 into FB460. FB460's callFB49A invokes FC1C0 with its supplied
record and appearance input. This is the same role-pool address used by
current_world_viewport.py, not either NPC pool.

Original world dispatcher68B4E..68B68 indexes table6B5D4 with the logical
opcode byte. Executed dispatch checks establish6F ->695C8,73 ->69A28,
B2 ->6B114. The6F prefix advances EBX past the opcode; its first callee
E9B50 receives the low12-bit identity and two packed15-bit values from
body+0C. Their semantic meaning is not established by this test.

World dispatch call6B125 invokes FBB50 with WORD[logical+1] and
BYTE[logical+3]. The original B2 handler through FBB50/FC960 is executed
with a null renderer, confirming that only entry+7B changes in the cache.
Complete6F payload bounds, constructors and wire framing remain unqualified.
Do not publish a complete wire schema from these checks alone.

FC1C0 also copies other packed fields and invokes nested constructors. These
have NOT all been classified. No assertion of absent attack/defense in the
entire616-byte record, entire client, or all PK packets is warranted.
One nested constructor edge is now qualified: FC130 takes four supplied WORDs
and copies them through FF450 into entry+228+6*i. It also calls FFA20 to
write entry+22C+6*i, taking each packed byte's high3 bits or forcing7 when
entry+61 bit10 is set. In the non-forced branch it preserves the low5 bits
of entry+251+2*i while replacing its high3 bits from the supplied packed byte.
The native FF3C0 constructor references a source-path string at19B664 ending
in `playlib/RoleDoll.cpp` (backslash separators in the image).
These are RoleDoll component storage operations; they are not proof of a
four-attribute or attack/defense tuple. The test does not classify every
consumer of those fields or execute FF3C0's lifecycle cleanup.

Next useful work is the remaining FC1C0 record fields and their consumers,
not another repetition of these string/component setters.

## Executed checks

`tests/research/test_current_battle_identity_cache.py` runs original pinned
instructions under Unicorn with read-only executable image pages, bounded
instruction ranges, a20000-instruction ceiling, and checked return/stack ABI.
There are no substituted native callees in the executed ranges.

Five tests pass:

1. For all128 slots, execute the original copying slice using explicit
   diagnostic strings, then original lookup/string getter, flag setter and
   flag getter. Monitored cache reads are confined to searched identity
   DWORDs, the selected strings, and the selected flag. String getter does
   not write the cache. These are diagnostic provenance checks, not128
   recovered monsters or a completed live PK session.
2. Missing identity visits exactly128 identity DWORDs; string outputs and
   flag output follow the original failure behavior without reading other
   cache fields.
3. Execute the original dispatch for6F/73/B2 and the6F argument-extraction
   prefix with boundary and interior diagnostic packed values. Stop before
   its UI callee, without replacing that callee.
4. Execute B2 -> original setter -> original lookup for five byte values,
   including80/FF. Check exact cache write footprint and stack restoration.
5. Execute all of FC130 and its real FF450/FFA20 callees, both forced7 and
   normal packed-byte paths. Verify four diagnostic WORDs, four byte fields,
   preserved low bits and the exact cache write footprint. No ability values
   are supplied or recovered by this diagnostic.

Reproduce from the server root:

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_identity_cache.py -v
ctest --test-dir build -C Release -R current_battle_identity_cache --output-on-failure
```

CTest registration was regenerated and verified:1/1 focused suite passes.

No captured official opponent data, original ability values, native damage
calculation, full PK, or full playable-world acceptance is claimed.
