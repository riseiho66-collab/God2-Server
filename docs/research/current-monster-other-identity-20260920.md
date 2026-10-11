# Current 1C Other Identity Branches

This bounded delivery executes original dispatch field2000 at `116149` and
field6000 at `11608B`. Field2000 copies prepared metadata into an existing
participant actor, then prepares the call to `1221B0`. Field6000 indexes the
current `NPCAppearData` namespace, copies its selected name into metadata,
constructs a 14-byte appearance request, and executes the prefix of `1177C0`
through the branch to `1182B9`. No name, art, field value, or namespace label
is used to infer BOSS status, monster classification, stats, skills or drops.

Only three new files belong to this delivery:

- `tools/strike_lab/current_monster_other_identity.py`
- `tests/research/test_current_monster_other_identity.py`
- `docs/research/current-monster-other-identity-20260920.md`

The prior variant helper/tests are unchanged. The complete EnyName loader,
prior4051 alternate-identity sweep, prior256 selector sweep and main's retained
`1116A9` continuation are not executed. No bootstrap, build registration,
shared document, database, runtime, UI, network or live-client change occurs.

## Current Evidence

All code addresses below are hexadecimal RVAs, equal to mapped-image file
offsets; x86 BASE is `400000`.

- Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Current client source: `Data2/Patch/Comm/gamedata.csvZ`.
  SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded SHA256:
  `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- `NPCAppearData` section: decoded `[7887,140789)`, header line115,
  rows116..4158, declared4043. Section SHA256
  `da509feb26fc89ebdc6adc82cc70d42956e7ba47a0952ea05f55d4b7f2ee35e3`.

| Span, end exclusive | SHA256 |
| --- | --- |
| `57147..5717D`, name/address projection | `7ebff872a2d628a7e8f8d1737a0f19cd5286d71a0f3c7a6c629f964b9e73abb8` |
| `575EA..575FC`, maximum projection | `47db5799fad32e0192a5cd721f58c7d61a48b12d16e435e9e69ec8d4d5a4623d` |
| `11608B..116149`, field6000 | `fd5e2a880a4fd32c9cd0cd04997559f93d589312104c29f6f524f44404dd1233` |
| `116149..11616B`, actor metadata copy | `5c4dcb15c1b5bbaf6b40a0cbbad276b72f0cfb8b10e9dbffa9ccab821d5a08d2` |
| `1161B4..1161E8`, next actor call arguments | `3cb2bf6cf9b3c2dca495f3bf386265ca848a0ced9f263d21065ae6064d6cb009` |
| `1177C0..117823`, next appearance consumer prefix | `73144836aedc5e83903c3a39b8e25fe2888eec5e8aebf2e41e83e30cf7b58ec5` |

The JSON report hashes all additional executed/reference spans and records
per-case instruction/read/write traces. A span hash is not a claim that every
branch in that span executed. Names suffixed `_static` are static references.

## Namespace Authority

The current image string at `18A12C` is `NPCAppearData`; static header dispatch
`56272..562B8` compares that string and calls original loader `570F0`.
Its static ID guard at `5712B` compares source column0 with7000. Original
`57147..5717D` computes `manager + 121EA + 94*ID` and copies source column1
including its NUL terminator. Original `575EA..575FC` updates the signed WORD
maximum at manager `+121E8`.

This lane reuses the pinned current-source reader and structural section
parser. It independently stages the parsed source ID at loader-local `+10`
and source name at loader-local `+3C`, then executes those two original loader
projections for every source row. **The complete loader, CSV tokenization,
appearance packing, table constructor and surrounding initialization do not
execute.** The resulting table is a partial native ID/name projection with
explicitly staged source locals, not a complete native loader output.

Current source bounds are checked before native execution:4043 distinct IDs,
all positive and below7000, maximum6224, no name longer than15 bytes. Names
therefore need no truncation in this source projection. The signed maximum
is produced by the original maximum-update instructions from a declared
zero-initialized fixture count. The projections execute141018 instruction
events, including repeated string instructions.

Every one of the4043 source rows is then exercised through the actual field6000
packet branch. The report preserves each source occurrence's index, selector,
raw row, fields, hash, decoded offset, line, name bytes and native pointer.
Names are byte strings; they are not used to classify or deduplicate entities.

| Namespace quantity | Exact result |
| --- | ---: |
| Declared source rows / distinct source selectors | 4043 / 4043 |
| Native maximum selector | 6224 |
| Native field6000 source joins checked | 4043 |
| Inclusive slots0..6224 without a source row | 2182 |
| Qualified monster stat/skill/drop assignments | 0 |

This is an appearance-namespace coverage count, not an added monster/species
denominator. The namespace name alone does not establish an entity category.

## Field2000 Dataflow

The probe starts at original `115C90` with a synthetic exact45-byte 1C packet,
an independently staged participant table and an explicit diagnostic actor.
Original `11E6E0` selects type0 from `manager + 38 + 24*slot`, with packet
slot0..27 split into side and position. This lane checks all28 slots.

For a nonnull actor, the prefix copies its existing56 metadata bytes into
the stack, then applies packet fields. WORD packet+3 supplies metadata+0,
WORD+7 supplies metadata+12, and packet bytes9..40 supply metadata+14..45.
Opaque trailing metadata bytes46..55 are inherited from the diagnostic actor.
The variant/level/state packing in the shared prefix executes as original
code; none of those synthetic values is an original monster attribute.

The field2000 jump reaches `116149`, which reads signed actor WORD+1A.
`11615C` copies all56 prepared bytes into **actor+DB0..DE7**, before testing
the saved handle against-1. Memory guards and actor canaries prove that only
those56 actor bytes change in the qualified path. No source table is queried
by this branch before the stopping point; packet WORD+3 is not turned into an
NPCAppearData or EnyName lookup here.

For handle other than-1, the original argument preparation reaches the call
instruction **`1161E8 -> 1221B0`** and stops before executing it. ECX is the
participant manager. Eight actual stack arguments are retained in the trace:
the WORD from battle+`A9DF740`, constant10, the WORD from battle+`A9DF744`,
constant59h, constant1388h, side, position, metadata pointer. The WORD/byte
operands are pushed in32-bit registers whose upper bits may retain diagnostic
poison; the report preserves the raw arguments, and tests compare the relevant
WORD/byte widths. No subsequent callee interpretation is asserted.

Handle-1 still receives the metadata copy, then reaches **`11619D -> 2B10`**;
the diagnostic callee does not execute. A null actor has no native guard at
`116149` and attempts to read address1A. The negative test observes this fault;
the harness does not map page0 or fabricate an actor to satisfy it.

## Field6000 Dataflow

`11608B` reads the source manager through battle+28 and uses metadata lowWORD,
previously copied from **packet WORD+3**, as the unsigned selector. This is
different from the EnyName branch's ordinal at WORD+7.

`116097` sign-extends manager WORD+121E8. The inclusive guard accepts selector
at or below that signed maximum. Accepted selection computes exactly
`manager + 121EA + 94*selector`. There is no presence bitmap or lower-bound
check in this instruction sequence: zero and holes also pass the comparison.
For an in-range selector with no source row, the harness stops at **1160B9**,
before its name scan; it never treats fixture-zeroed holes as source records.

For a declared source row, original `1160BE..1160DF` copies its NUL-terminated
name into stack metadata+14. The next instructions read DWORDs from record
`+14h` and `+18h`. Those eight bytes are **explicitly staged diagnostics**, not
values recovered by this partial loader projection and not numeric stats.
The probe varies all-zero, distinct-byte and all-FF diagnostic DWORDs.

`1160E1..11610E` assembles this14-byte request at the parent frame+2C:

| Request bytes | Executed producer |
| --- | --- |
| +0 | zero |
| +1 | original packet slot byte+1 |
| +2 | constant1 |
| +3..6 | selected record DWORD+14h |
| +7..10 | selected record DWORD+18h |
| +11..13 | zero |

Original **`116112 -> 1177C0`** executes, with ECX=battle and the request pointer
on the stack. Its entry is observed without substituting a result. Original
`1177FF..11781D` sees request type1 and zero WORD+12, so it jumps to
**1182B9**. Execution stops there before further participant/appearance work.
The ChangeDollCard guard/lookup calls are bypassed. `116117`, the caller return
continuation, is not yet reached. In this bounded valid-row path the original
actor metadata remains unchanged; only the stack metadata/request changes.

If selector exceeds the signed maximum, `11611D` instead copies the string at
image VA5B4640 into metadata+14. That pinned image byte is NUL; the observed
copy clears only the first name byte and retains the remaining packet tail.
This reports the captured image input, not a claim about all live string state.
The fallback then executes the same actor copy at116149 and stops at1161E8
or11619D, depending on the diagnostic actor handle. It does not call1177C0.

## Verification and Frontier

```powershell
python -B tests/research/test_current_monster_other_identity.py -v
python -B -m tools.strike_lab.current_monster_other_identity
```

**6 focused tests passed in6.777 seconds.** They cover all4043 source projections
and joins, all28 field2000 slots, actual actor writes and call arguments,
actual nested appearance-prefix dispatch, independent appearance/register/stack
poisons, signed maximum and inclusive boundary, sparse slots, null actor,
handle-1 behavior, source/image pins, instruction budget and JSON authority.
The tool emits JSON to stdout and creates no evidence artifact or runtime data.
Execution uses the bundled Unicorn runtime, unchanged original instructions,
explicit read/write ranges and a2500-instruction bound per invocation. There
are no substituted CRT/OS/game callees in this lane.

The previous variant tool/test hashes were checked before and after this work:

- Tool: `953c8b7d7f62b18fbf54fa5963e5bcf7bc316a301aeb2e5f4b87714ee91400f8`.
- Tests: `6988f9ca742707b86fef1de71984f9d9cb2cb82a0491fc9b6cbfeddde2dbf704`.

Exact remaining continuations are **1182B9** inside1177C0, its eventual caller
return **116117**, and the prepared but unexecuted **1161E8 -> 1221B0** call.
The invalid-handle diagnostic **11619D -> 2B10** and sparse-slot scan **1160B9**
are also explicit stopping points. Original full NPC appearance packing and
actor provenance are still needed before promoting appearance bytes. Original
1C sender/classifier evidence and identity-bound stat/skill/drop producers
remain unresolved. ALL-monsters including BOSS coverage remains unqualified.
This delivery stops here for main review; no broader completion claim follows.
