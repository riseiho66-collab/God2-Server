# Current Battle HP/MP Decode

## Result

The current client proves the four field identities below. This closes the
previous gap between raw battle scalar copying and named role HP/MP use.
It does not recover any species' original values or damage formula.

| Battle actor offset (hex) | Meaning | Role source offset (hex) |
| --- | --- | --- |
| DE8 | Current HP | 5C |
| DEC | Current MP | 64 |
| DF0 | Maximum HP | 60 |
| DF4 | Maximum MP | 68 |

The S2C logical `86` record is exactly 17 bytes. Packet offsets below are
decimal, including opcode at offset 0:

| Offset | Size | Meaning |
| --- | --- | --- |
| 0 | 1 | Opcode 86 hex |
| 1 | 1 | 0 = HP pair, 1 = MP pair |
| 2 | 1 | Position 0..27; side = position/14, slot = position%14 |
| 3 | 2 | Uninterpreted; retained losslessly |
| 5 | 4 | Maximum, little-endian DWORD |
| 9 | 4 | Current, little-endian DWORD |
| 13 | 4 | Uninterpreted; retained losslessly |

One record carries ONE pair, not all four values. The callback combines that
updated pair with the other pair already retained on the actor. Raw storage
is not clamped here; current > maximum is not rejected by the codec. Signed
formatting later does not change the storage width.

## Executed Evidence

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE=400000; instruction addresses below are RVAs in hex.

The new test executes continuously from `114332`, through the real dispatcher,
`117230/1173A0`, original lookup and scalar setter, then actual `E71E0`.
It stops BEFORE `E72A6`, after the role stores and before UI refresh. No game
function is replaced or given a fabricated successful return. Existing native
test machinery is reused; graphics handle -1 is an explicit no-display input.

- Kind0: packet+9/+5 -> `12D86C/12D875` -> actor DE8/DF0.
- Kind1: packet+9/+5 -> `12D99C/12D9A5` -> actor DEC/DF4.
- Caller loads all four actor DWORDs and passes their actual stack buffer.
- `E7234/E7240/E724C/E7259` store them to role 5C/64/60/68.
- Both callers select callback mode 0. Kind1 does this by literal `PUSH 0`
  at `117452`, not by forwarding its packet subtype.
- Consecutive HP then MP invocations retain the same VM, actor and role memory.
  Only the next packet and separate call stack are staged between invocations.
- Optional companion HP-decrease behavior executes as original instructions;
  the following MP update does not subtract the same HP loss a second time.

The naming check then executes SEPARATE display-reader slices
`AC132..AC167` and `AC16C..AC1A4` against those retained role values. These
select the actual ProgramMsg pointers and prepare the real format-call
arguments. They stop at the formatter CALL, without pretending to execute
the intervening UI calls or render text.

The pinned current `message.csvZ` source gives ProgramMsg 163 (blood/HP) and
164 (magic/MP), exact CP950 bytes `a6e5b6713a2025642f2564` and
`aa6bb34e3a2025642f2564`. Format arguments are current then maximum. Source
hashes and physical rows are in the independent
[scalar audit](current-battle-scalar-semantics-audit-20260920.md).

## Enemy-Side Difference

Side1 HP calls the SAME `12D840` setter via `12D956`, preserving the named
field layout. Existing original side1 execution is reused in new C++/native
differential tests. Side1 kind1 instead returns at `1173D7 -> 117463`, before
lookup or writes. The codec explicitly reports this as unsupported actor
update, while preserving all received bytes.

This is not proof that monsters have no MP. Their retained DEC/DF4 can be
consumed by the two-channel display. Their initial source remains unresolved.
Actor existence, actor+1A gate and resource readiness remain prerequisites;
the codec's supported-branch flag is not a promise that every native state
successfully applies the update.

## Implementation and Verification

- `src/protocol/RecoveredBattleVitals.h`: owning C++20 lossless codec, named
  HP/MP accessors, exact length/opcode/kind/position validation and opaque bytes.
- `current_protocol_coverage.py`: classified as CODEC_ONLY, not a runtime route.
- `test_current_battle_vitals.py`: 5/5 tests, all14 local positions, both kinds,
  full-width boundary values, callback gates, companion branch and source labels.
- `test_recovered_battle_vitals_codec.py`: 2/2 tests. 280 explicit diagnostic
  cases across both sides/all28 positions agree with original stores or the
  actual ignored branch. Malformed length/opcode/kind/position cases reject.
- C++ standalone tests also cover every byte value in each payload position,
  copy ownership, exact round trips and input bounds.

Release codec build succeeds. Selected registered CTest: 7/7 in40.25s,
including prior scalar9/9, side1 scalar19/19, new vitals5/5, differential2/2,
initial-participant8/8 and independent map-metadata7/7 plus the C++ suite.
Protocol coverage separately passes13/13 in12.355s.

No runtime emission, server gameplay mutation, Lua rule change, monster
database import or live-client acceptance is claimed. Diagnostic numeric
inputs test field behavior; they are never promoted as original monster data.
Next original-value gap is an identity-qualified producer/initialization
source, not the HP/MP field order just resolved here.
