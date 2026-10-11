# Current Monster Local Stat Fallback, 2026-09-20

## Bounded Result

**No monster-identity-derived intrinsic attribute value or formula was found
in the inspected constructor dataflow. Newly recovered authoritative monster
values: 0.** This is a static audit, not new native execution and not a claim
that the entire client lacks such data.

There is an important local initializer beyond the previously executed
frontier: **`116617 -> 12CCD0` initializes actor+DE8/+DEC/+DF0/+DF4 from four
immediate constants `1`, on side0 only.** These are real scalar-store
instructions, not merely display copies, but their source is not monster
identity, a local monster stat table, or supplied numeric fields in 1C.
Side1 skips this particular block at `12D21F -> 12D329`. Do not infer equal
enemy/friendly attributes, official HP/MP=1, or completed recruitment.

The distinction matters: the earlier constructor-prefix result that reset
leaves `CDCDCDCD` in those fields remains correct at its stopping point.
It is not a complete post-constructor result. Main owns the separate native
reset/omitted-value experiment; this lane did not run or manufacture it.

## Authority and Scope

Only the current mapped image was inspected:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image BASE is `400000`; every RVA below is also a raw file offset. Addresses
marked VA include the base. Other offsets are hexadecimal unless explicitly
marked decimal.

Prerequisites read, not rerun:
`current-monster-side-initialization-20260920.md` and
`current-participant-metadata-semantics-20260920.md`. The previously executed
normal-1C path still ends before `1206E0`, with ROM load
`1206E5 -> 29820` unresolved by that oracle. The analysis below follows original
instructions statically beyond that boundary; it does not supply a successful
game-function return or claim a continuous executable constructor.

Notation: `B` is battle owner; `M=B+144938` is manager; `A` is an actor selected
by side/slot/type through `11E6E0`; `T` is the caller's 56-byte metadata buffer;
`R=[M+C]` is the render-resource owner. Normal enemy means the existing tested
packet variant `0400`, type0. No ID counterfactual or EnyName-loader experiment
was duplicated; those belong to main's ID lane.

## Post-Resource Entry and Reset

| Writer/call RVA | Source -> destination or effect |
| --- | --- |
| `115FC7` | `120650` return AX -> selected FightEny record WORD+0, a runtime resource handle |
| `115FCE,115FDA,115FDF,115FE7,115FED` | FightEny WORD+4 low10 -> T+4 low10; preserve T+4 upper22 bits |
| `116000 -> 120000` | Reset side/slot before the resource-handle validity check at `116009` |
| `120020 -> 11E6E0` | Iterate the same side/slot over types0..5, not a monster-ID stat-table lookup |
| `120244 -> 11FDE0` | Reset each selected actor; existing `11FDFE` fills its ECC bytes with immediate `CDCDCDCD` |
| `11FECD,11FED7` | Immediate VA `59CF80,59CFD8` -> A+D94,A+D98, respectively |
| `11FFC7,11FFD2` | Clear metadata DB0..DE7, then set its first WORD to FFFF |
| `120263..120277` | Clear slot bit in M+2F4+4*side |
| `116025 -> 1216C0` | Arguments: resource handle, side, slot, type0, auxiliary selector, T |

The full `120000..120283` body was read. Other direct writes invalidate handle
fields: +1A,+20,+2,+4,+14,+26/+28/+2A,+2C2,+2D8..30F,+674..6FF. It releases
associated objects through the calls listed below. Neither its arithmetic
nor the known reset fill is a monster capability calculation. Reset's four
known vital fields are outside the subsequent metadata zero-fill.

## Complete Named Helpers and Resource Numbers

The complete bodies of `121630`, `1216C0`, `12A7C0`, `12A710`, and `120970`
were disassembled, including both side branches and their returns.

| Source/producer | Reader -> destination/consumer | Static interpretation |
| --- | --- | --- |
| Resource descriptor `D=[R+C]+1514*handle` | `1E158` checks D+108C; `1E162/1E169` returns `[D+1090+4*sequence]+18` | Sequence string pointer, not a scalar result |
| That string from `12164C/121683 -> 1E130` | Side0 sequence1: NUL scan `12165E`, final-byte compare `'1'` at `121669`; side1 sequence0: `121695`, compare `'5'` at `1216A0` | Boolean suffix match -> A+1E5 at `12171C`; not the ROM file path itself |
| Suffix match, for type<=3 or type6 | `121730,121735,12173C,121742` put flag1 at A+1E4 and VA `5B8FC4` in both A+D94/D98 | Select common sequence mapping; otherwise A+1E4=0 at `12174A` |
| Reset-written A+D94/D98 | `12A7DF -> 12A7E6` selects `[A+D94+4*side]` -> A+D90 | `12A7C0` does not read its handle argument for a numeric lookup |
| Same A+D94/D98 | `12A727/12A72A` select -> A+D90; `12A740` finds type3 and `12A749/12A74C` switches that actor's mapping too | Entire `12A710` is pointer selection plus lookup |
| D+108C | `121785` compare >=B0 -> A+1E3 at `121795` | Resource sequence-count threshold; `1E158/1E15E` use the same field as sequence-index bound |
| Selected A+D90 mapping BYTE+0 or +14 | `1217B0` or `1217A3` -> SI -> A+0 at `12181D/12196F`, passed to `1BF30/1AFE0` | Resource-sequence selection, not attack/defense or four-dimensional speed |
| M+A7FBCCC/+A7FBCD0 + 8*(14*side+slot) | `121934/12193C`, `121943/12194D` -> A+1D4/+1D6 -> `121995 -> 1AFE0` | Position inputs; diagnostic literal explicitly calls them x/y |
| Auxiliary argument low3 bits | `1217B4..1217D2` -> A+234 bits4..6 -> `12188C/1219AF -> 1E070` | Selects an indexed resource pointer, not an intrinsic scalar |
| `1AFE0` return AX | `1219A0` -> A+1A; original input handle -> A+24 at `121919/121896` | Distinct render-object and resource handles |
| Mapping BYTE+11 and resource handle | `121A1F/121A24 -> 1CD40(handle,sequence,6)` -> WORD A+1DA at `121A29` | ROM command-stream accumulator described below; no stat semantics promoted |
| T, if nonnull | `121A3F/121A4A` copies 14 DWORDs -> A+DB0..DE7 | Existing metadata-copy edge, not new authority |
| Actor lookup over side0..1, slot0..13, type0 | `120991 -> 11E6E0`, `120998` sets each A+1E1=0; caller `121A65` selects current actor with1 | Selection state, not numerical capabilities |

Default mapping bytes are exact pinned-image data: RVA `19CF80..19CFD7`
contains `00,02,...,AE`; `19CFD8..19D02F` contains `01,03,...,AF`.
These are 88-byte mappings per side, not pairs of monster stats. The alternate
mapping's RVA `1B8FC4..1B901B` is all zero in the pinned snapshot; its runtime
producer was not followed. Snapshot zeros are **not** original monster values.

`1CD40..1CDE3` was fully read, with its nine-entry jump table at `1CDE4` decoded
as data, not instructions. `1CD76` loads a sequence pointer from D+1090;
`1CD81` reads its +10 list count and `1CD94/1CD99` traverse pointer entries
starting at +30. Ten-byte commands are parsed: opcode1 at `1CDAB` loads signed
WORD+2 as weight, opcode2 at `1CDB4` resets weight to1, opcode8 at
`1CDBE..1CDCE` adds weight when WORD+2 is nonzero and WORD+4 matches argument6;
opcode0 advances the outer list. The return is that sum, narrowed to WORD in
A+1DA. This is a concrete ROM-number source, but no connection to HP/MP,
attack/defense, constitution/strength/intelligence/speed is established.
It is not a speed formula merely because an animation stream contains counts.

`1E070..1E128` was also read: it bounds the auxiliary index by
render-record+34 -> count+4, loads the indexed pointer at +8+4*index, and writes
render-record+2C/+44 at `1E0DC/1E0E4`, plus a downstream resource pointer at
`1E11D`. No actor vital destination is used there. `11E770..11E793` only
formats into a local buffer via `146CF7`; literal RVA `19D7D8` is
`CreatObj h=%d (%d,%d) type=%d pal=%d nRomIdx=%d x/y(%d/%d)`.

## Remaining 115C90 Tail

The tail was read through its actual `116628 RET 4`. Bytes after `11662A`
are not part of the function. Normal0400 success flows through:

`116166 -> 1161B4 -> 1161E8 -> 1161FE (conditional) -> 11620B ->
11646C -> 1165C1 -> 116617 -> 116628`.

| Call/site | Concrete source and writes in inspected body |
| --- | --- |
| `1161E8 -> 1221B0` | B+A9DF740/A9DF744 WORD inputs plus constants A,59,1388 and T. `12220F` stores supplied handle in A+1C; `122222/12228A` store `1F040` returns in A+4/+14. T+8 flags drive A+1EA=9 and A+DB8 bit clears at `1222DF,1222FC,12231C`; calls `129870`, then `126270`. No identity-to-stat formula in this body. |
| `1161FE -> 121F20` | Conditional on `[[B+83458]+528]>=0`; this input and constant0 feed `1F040/1AFE0`. Returns -> A+2/+20/+16 at `121F71,12200B,122078`; supplied handle -> A+22 at `121FE9`. |
| `11620B -> 1220E0` | M+A7FBC6C WORD and caller constant0 -> `122153 -> 1F040`; return handle -> A+10 at `12215C`. |
| `11646C..1164DE` | Empty string at VA5B4640 -> B+98 and B+258, each indexed by 16*(14*side+slot). Normal0400 skips the variant4000 name/ID-search branch at `1164F0`. |
| `116617 -> 12CCD0` | Display/metadata setup and the side0 scalar initialization below. Entire body through `12D354 RET 24` was read. |

The intervening variant2000 branch `116226..116467` is not taken for normal0400.
Its role-name calls `FAC70/FAD20` and local-role skill pointer copies
`11641C -> 11B8C0 -> 11645C` are not a monster-base-stat source. Likewise the
alternate owner+121EA/stride94 path `11608B..116112 -> 1177C0` is not substituted
for the normal enemy branch. Those callees were not re-expanded.

### Exact Constant-to-Vital Stores

Let `S` be ESP immediately before `1165CA` (the first final-call argument push).
`1165D1` sets ESI=1. The four caller writes and corresponding callee stores are:

| Caller writer | Stable local address | `12CCD0` source read | Actor writer |
| --- | --- | --- | --- |
| `1165D9`: `[ESP+80]=ESI` | S+7C | `12D2FF/12D303`: argument4 DWORD+0 | `12D305`: A+DE8=1 |
| `1165E0`: `[ESP+84]=ESI` | S+80 | `12D30B`: argument4 DWORD+4 | `12D312`: A+DEC=1 |
| `1165E7`: `[ESP+78]=ESI` | S+74 | `12D30E/12D318`: argument5 DWORD+0 | `12D31A`: A+DF0=1 |
| `1165EB`: `[ESP+7C]=ESI` | S+78 | `12D320`: argument5 DWORD+4 | `12D323`: A+DF4=1 |

`1165F3` takes the pointer S+74; `1165FB` takes S+7C; argument pushes at
`116602/11660B` pass those two different pairs. At the callee's stable post-
prologue ESP, side is +60, slot +64, T +68, argument4 +6C, argument5 +70.
`12D219/12D21D/12D21F` tests side and branches directly to `12D329` if nonzero.
Side0 obtains its type0 actor at `12D232 -> 11E6E0`; the four writes at
`12D2FF..12D323` still occur when the earlier display-handle/flag checks skip
bar setup. This statement presumes a valid actor pointer and reaching the tail.

The same pairs are separately copied to display records by
`12D2CF -> 108F50` and `12D2E9 -> 108FC0`. Their fully read bodies write into
display-record storage of stride A7E0; those calls are not the actor writers.
Thus this finding cannot be dismissed as display-only, but it equally cannot
be promoted to a local intrinsic HP/MP table. The four ones are explicit
initialization constants. No packet scalar, monster ID, EnyName numeric field,
ROM counter or formula is used to produce them in this caller.

Normal `12CCD0` also formats the already-supplied metadata level through
`12D02A..12D09F` and `147AF7`; format literals at `194310/194318/194320` are
`Lv:%d`, `Lv:%s`, `Lv:???`. The original normal-name lookup is
`12D0D9 -> 5A0A0` using T+E/+10/+C, followed by the already-qualified name
copy at `12D132/12D151/12D15C`. It is not a new HP/MP producer. The low10
metadata selector merged from FightEny is passed at `12D184..12D214` to
`10BF00` with the display handle. That callee was not expanded here.

After the vital block, T+8 flags select tag0,9,or95 at `12D329..12D342`, then
`12D348 -> 126430`. Full bodies `126270..12642B` and `126430..1267B1` were
read: direct actor writes update status bits DB8, state1EA/1DE, attachment
handles +6..E and byte fields +18/+19; manager+2F4 slot bits also change.
They delegate positioning and pose/resource work to the remaining calls below.
This is not a claim that all transitive effects have been executed or excluded.

## Explicit Remaining Boundaries

No genuine monster-stat source was found for a new intrinsic-stat native
oracle. Consequently this lane does not propose a fabricated-value slice or
add tests around assumed stats. The constant-store addresses above are a
handoff to main's already-planned native experiment, not a second execution.

| Boundary not expanded or not completed here | Exact entering calls / unresolved provenance |
| --- | --- |
| ROM loader and resource-descriptor production | Existing `1206E5 -> 29820`; producer of `[R+C]`, D+108C/+1090 sequence pointers and sequence command payloads not traced. No ROM preload performed. |
| Runtime alternate sequence mapping and positions | Producer of VA5B8FC4 and M+A7FBCCC/+A7FBCD0 not traced; their exact consumers are above. Snapshot/table numbers are not promoted to stats. |
| Reset's resource cleanup | `120032 -> 11CFB0`; `12004C/120232 -> 2DE30`; `120077/1200F1/1201A9 -> 1B330`; `1201FC -> 1093F0`; `12020C/120220 -> 11FD70`. `120290` itself was read, but its `1202C7 -> 1B330` was not expanded. |
| Constructor render allocation/update | `121864 -> 1BF30`, `1218CB -> 1B330`, `121995 -> 1AFE0`; their full transitive effects and returns are not newly qualified. |
| Tail attachment internals | `122219/122281`, `121F68/12206F`, `122153 -> 1F040`; `122002 -> 1AFE0`; handle-indexed `1B560` calls at `122259/1222C1/121FA8/122042/1220BA/12219A`. Inputs/returned-handle stores were traced, not fabricated. |
| Display construction and optional metadata lookups | `12CE2A -> 108300`, `12CE46 -> 108690`, `12D2B5 -> 108CD0`, `12D2FA -> 109200`; `12D104 -> 5A120`, `12D16B -> 5A860`, `12D17B -> 109880`, `12D0BF -> 109F80`, `12D214 -> 10BF00`. `108F50/108FC0 -> 108E70` remains unexpanded. Prior text setters/lookup are reused evidence, not rerun. |
| Status/pose subtree | `1222D4/12678A -> 129870`: only prefix `129870..12994F` was inspected; the rest was not audited. `126458 -> 12A200`, `1262CB -> 120AE0`, `1262D9/12667D/126736 -> 120B90`, `126300 -> 1F180`, `126352 -> 1F040`, `1263AF/126566 -> 1BF30`, `126422 -> 1B560`, and `1265B0/1265DC/126608 -> 10BF00` not expanded. `1267A7 -> 1267C0` requires tag59, not the 0/9/95 passed by this tail. |

The complete `12CCD0` body also contains non-normal branches through
`12CFB3 -> 59A60`, `12CF45/12D1B4 -> 109E70`, `12CF65/12D1D4 -> 109F80`,
`12CFCA/12D1A1 -> 1097D0`, `12CFDE -> 109880`, `12D1FF -> 109C10`.
They were identified but not substituted into normal0400's source chain.
Diagnostic/CRT leaves `2B10/2C70/147AF7/146CF7` were not executed.

For the ID-route report: following identity to metadata, an EnyName name, or a
ROM selection does not establish an identity-to-capability mapping. This audit
adds no intrinsic numeric table join. It does establish where side0 gets local
ones and where the specified constructor consumes resource-sequence numbers.
Unknown transitive resource/state code remains explicitly bounded above;
neither an official capture nor old archives are required to continue local
analysis, and neither was used as a reason to stop.

## Verification and Handoff

Read-only Capstone disassembly against the hash-checked pinned image completed.
Seventeen byte checks passed: fourteen exact instruction encodings covering
the immediate producer, both pair pointers, call, side gate and four actor
stores, plus the two 88-byte mapping patterns and 88-byte snapshot-zero block.
These are static integrity checks, **not 17 native tests**. No original
instructions were executed in this lane and no runtime values were invented.

Root span checksums (end offsets exclusive):

| Raw span | SHA256 |
| --- | --- |
| `115FC7..11662B` | `d1f1d18a01316b38019538e0c8609c06b52244df3c617803cbe1db4b37450d60` |
| `120000..120284` | `ab4998044bf4585308847ee024d931590a0d81ca74ce5a715dbed0f34fa05779` |
| `121630..1216B2` | `804c8902465bac162d14ae5ae316c1080a6fce84f31db6443c18cffae7bf1158` |
| `1216C0..121AB4` | `e1bd0fe1120b6f2c1a87cce57e607c320ffb9a7256892ce57818b9b3180d1cf2` |
| `12A710..12A756` | `a1b6a4fa0133b88f4dc37e59b4a9d4a6938562ee715491b00897179ccd185326` |
| `12A7C0..12A7F0` | `423c6c6c48c39f68f03f191c15cd0c97c65eb769132170c6c36e349ef9cb1118` |
| `120970..1209BD` | `06e98a3e416fe2bb93f4a4489cc966bd0f56d0b2cac1ffd0e3a985836b34f46b` |
| `12CCD0..12D357` | `b2355757b1d452027d2e7b609b292696e13276288f202df912fa3f4793d2e247` |

Only this new document was added. No tool/test code, existing file, CMake,
status, database, production code, GUI/network surface or retired archive was
changed/accessed. No child worker or background process was started. All
read-only commands completed; no active process remains from this lane.
