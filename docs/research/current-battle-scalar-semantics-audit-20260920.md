# Current Battle Scalar Semantics Audit

Independent read-only audit, 2026-09-20. The battle entity fields can be named
`DE8=current HP`, `DEC=current MP`, `DF0=max HP`, `DF4=max MP` by their exact
forwarding into the already identified role HP/MP consumer. Side1 uses the
same HP setter and field layout, so the HP field names carry over. This does
not recover a monster species' original numeric values, an MP initialization
source, or a damage/stat-generation formula.

Only this document is added. Other sources/tests are read-only. No new oracle,
codec, test, database, runtime, preload, UI or network operation is implemented.
Main owns the proposed continuous callback test and recovered vitals codec.

## Authority

Pinned current mapped image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All instruction addresses below are RVAs; BASE=`400000`, RVA=file offset.
The full image hash was checked before independently disassembling the cited
spans. No retired source or historical packet supplied evidence.

Reused proofs: `current_role_progression.py`, its existing native tests,
`current_battle_scalar_result.py`, `current_battle_side1_scalars.py`, and their
tests/docs. The audit also called the read-only `current_role_progression.evidence`
source reader to verify current ProgramMsg 163/164 bytes and provenance.
No native suite was rerun and no new continuous callback execution is claimed
by this document. The cross-function conclusion below is a static composition
of original instructions and existing separately executed native proofs.

Notation: `B` is battle, `T=B+144938`, `R=B+A9E9CB0` is the copied logical
record, `E` is a battle entity, `U=[B+20]` is callback owner, and
`A=[U+86888]` is the role source object. `A` is not implicitly the character
root: in the current bootstrap it is the separately bound root+90 source.

## Subtype Versus Actor Selection

**Inside 117230/1173A0, EBP is the record pointer and EBP+1 is the packet
subtype.** It is not an actor-object byte or the entity lookup's type selector.
Do not carry the outer dispatcher EBP meaning into these callee frames.

| RVA | Exact witness |
| --- | --- |
| `114464/11446C` | Form `B+A9E9CB1` and load its BYTE, copied record subtype |
| `11446E/114473` | Bound to 0..6 and select the table at VA `5146CC` |
| table `1146CC+0*4`, `1146CC+6*4` | Both contain VA `51447A`; subtype 0 and 6 share 117230 |
| `11447A/11447D` | Push EDI=R, call 117230 |
| table `1146CC+1*4`, `11449E/1144A1` | Subtype 1 pushes R and calls 1173A0 |
| `117235` / `1173A5` | Load the incoming pointer into EBP from `[ESP+1C]` |
| `11728F` / `1172EA` | Load BYTE `[EBP+1]`, the actual subtype |
| `117279..117280`, `1173E7..1173EE` | Entity lookup explicitly receives `(side=0,slot,selector=0)` |

The lookup's third argument is a distinct selector. `11E6E0` reads it at
`11E6E0`; `11E6E6..11E6EC` aliases selector 6 to 0. Both audited battle
callers nevertheless push literal 0. That alias does not make packet subtype
and actor selector interchangeable. The pointer load at `11E75A` implements
`T+38+24*(side*14+slot)+4*selector` after the low-byte bounds checks.

## Callback Arguments

At E71E0 entry, the four arguments are:

| Stack | Proven source / interpretation |
| --- | --- |
| `+04` | Pointer to a stack payload prepared by 117230/1173A0 |
| `+08` | DWORD `[B+A9E9C40]`; retained context, no actor-type meaning assigned |
| `+0C` | Argument whose low BYTE comes from `[B+76]`; later display mode |
| `+10` | Destination discriminator, consumed as a BYTE by E71E0 |
| ECX | `[B+20]`, owner U |

Subtype 0: `1172CA/1172D0/1172D6/1172E0` load E's four DWORDs into payload
`+0/+4/+8/+C`; `1172EA` loads subtype 0 into CL, `1172FE` pushes ECX as
argument 4, and `117309` calls E71E0 (return `11730E`). ECX's upper bits need
not be zero. E71E0 tests only AL loaded from argument 4 at `E71E0/E71E5`.

Subtype 1: `117421/117427/11742D/117437` prepare the same four-field payload,
but **117452 pushes literal DWORD 0**, then `11745E` calls E71E0 (return
`117463`). Subtype 1 is therefore not forwarded as callback discriminator 1.
Confusing these would falsely select E71E0's assertion path.

Both full-snapshot callbacks require side0, the selected slot matching BYTE
`B+51`, and signed entity WORD `E+1A >= 0`. Those gates follow the setter;
they do not gate the earlier entity scalar writes.

Subtype 6, statically audited but outside the old 0/1 scalar oracle: the shared
117230 path skips 12D840 via `117294 -> 11731D`. On the local/gated path,
`11732F/117332` read `R+9/R+5` and initialize only payload `+0/+8` at
`117339/117343`. `117335` pushes EAX whose low BYTE is 6, and `117351` calls
E71E0 (return `117356`). Payload `+4/+C` remain uninitialized stack bytes.
E71E0's discriminator-6 branch reads only `+0/+8` at `E7276/E7287`, writing
`[A+D0]+2C/+30` at `E7278/E728A`. It does not read the absent MP pair.
Do not fill those holes and then claim a native four-field read.
Other nonzero discriminator bytes reach assertion `E729E -> 2C70`;
6 with a null subordinate also reaches that assertion path.

Argument 4 is thus semantically a role/subordinate destination discriminator
inside E71E0, sourced from the subtype only on the 117230 routes. It is not
the actor lookup selector. Keep argument 3's display mode separate from it.

## Four-Field Identity

| Entity field | Setter and logical record source | Callback payload loads: subtype 0 / 1 | E71E0 target store | AC070 label/argument witness |
| --- | --- | --- | --- | --- |
| `DE8`: current HP | `12D86C`, R+9 for subtype 0 | `1172CA` / `117421`, payload+0 | `E7231/E7234` -> A+5C | `AC156` loads current; ProgramMsg 163 at `AC149`, call `AC167` |
| `DEC`: current MP | `12D99C`, R+9 for subtype 1 | `1172D0` / `117427`, payload+4 | `E723D/E7240` -> A+64 | `AC193` loads current; ProgramMsg 164 at `AC186`, call `AC1A4` |
| `DF0`: max HP | `12D875`, R+5 for subtype 0 | `1172D6` / `11742D`, payload+8 | `E7249/E724C` -> A+60 | `AC153` loads maximum; same ProgramMsg 163 call |
| `DF4`: max MP | `12D9A5`, R+5 for subtype 1 | `1172E0` / `117437`, payload+C | `E7255/E7259` -> A+68 | `AC190` loads maximum; same ProgramMsg 164 call |

The 17-byte logical 86 record supplies only one current/max pair in these
subtypes. The four-field callback snapshot combines that updated pair with
the entity's retained other pair; it is not four scalar DWORDs carried by one
86 packet. Bytes `R+3..4` and `R+13..16` remain opaque in these paths.

On callback discriminator 0, original `E71E0..E72A6` copies the four values
without deriving maxima. Before the copies, an HP decrease can reduce the
optional subordinate's `+2C`, floored at zero (`E720A..E7224`). This is a
specific derived subordinate state update, not an attack/defense formula.

The real refresh edge is `E72B9 -> E72D0`, then `E72DF -> AC070`.
At `E72A6/E72AA`, the callback forwards its original third/second arguments;
AC070 receives `(A,context,mode)`. Its later subordinate-display guards are
`AC1BA` context nonzero and `AC1C4` mode bit0. These arguments are not evidence
that context is a monster identity or mode is the fourth-argument discriminator.

AC070 reads the two maxima at `AC07B/AC08A`; zero maximum or negative signed
panel WORD at `AC095` exits. It unsigned-clamps A+5C against A+60 at
`AC0A2/AC0A7` and A+64 against A+68 at `AC0AA/AC0AF`. Role state can therefore
change here; the battle E fields were raw copies and are not clamped by this
role consumer. The later `%d` display is not evidence for signed storage.

## ProgramMsg Evidence

Current `Data2/Patch/Comm/message.csvZ` SHA-256:
`5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`.
Decoded SHA-256:
`370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.

| ID | Exact source row | Physical source | Native selection |
| --- | --- | --- | --- |
| 163 | hex `3136332ca6e5b6713a2025642f25640d0a`; CP950 label means blood/HP, format `%d/%d` | line 2189, decoded offset 90241; row SHA `5182232e266a45ffae2e71097a40d1c2d349798243c61c8da63cbda2173b5d18` | `AC138` checks A3, `AC149` reads pointer-array +288 = index 162 |
| 164 | hex `3136342caa6bb34e3a2025642f25640d0a`; CP950 label means magic, format `%d/%d` | line 2190, decoded offset 90258; row SHA `d207f4f5981057f525f836f06240f5719dde9b1b543690d24a0813df84c66bf0` | `AC175` checks A4, `AC186` reads pointer-array +28C = index 163 |

The formatting call at `AC167` has effective arguments
`(controller,panel,2,ProgramMsg163,currentHP,maxHP)`; `AC1A4` has
`(controller,panel,3,ProgramMsg164,currentMP,maxMP)`. Right-to-left pushes are
`AC159/AC161` for HP max/current, and `AC196/AC197` for MP max/current.
Controller is owner+E2170 and panel is the WORD at owner+232E50.

Existing `test_current_role_progression.py` already executes the E71E0 stores,
unsigned clamps and guards, and the native ProgramMsg pointer selections.
Its message-selection test stops at `AC153` and `AC190`, before the numeric
argument loads. Thus main's proposed `AC132..AC167` and `AC16C..AC1A4` slices
add useful actual argument evidence. They must remain labeled as separate
slices from the continuous battle callback, and must not claim the formatter
or UI call executed when stopping at its CALL instruction.

## Side1 Decision

**Safe naming:** side1 E+DE8/DF0 are the same current/max HP fields. The exact
native route is `117388 -> 12D8C0`, then `12D956 -> 12D840(1,slot,value9,value5)`.
The wrapper and setter each call original `11E6E0(1,slot,0)` at `12D8DA` and
`12D852`; both select `T+38+24*(14+slot)`. No alternate side1 field layout or
numeric conversion occurs at the shared stores `12D86C/12D875`.
Existing side1 tests execute this continuously from 114332 for admitted paths.

| Side1 consumer RVA | Exact dependency and limit |
| --- | --- |
| `12D8E1/12D8E7` | Wrapper reads E+1A without null check; unsigned WORD >=1000 returns. Null is a real fault. Display/resource work may stop before HP stores. |
| `12D86C/12D875` | Write current HP from R+9 and max HP from R+5; preserve DEC/DF4 |
| `12D87D` | Read retained max MP, E+DF4 |
| `12D889/12D88A/12D88E` | Supply `(handle,new maxHP,retained maxMP)` to 108FC0. New maxHP is still in ECX from `12D868`; no DF0 memory reread is required. |
| `12D893/12D899/12D8AB` | Read E+DEC and E+DE8, supply `(handle,currentHP,retained currentMP)` to 108F50 |
| `1173D7 -> 117463` | Subtype 1 side1 returns before entity lookup, scalar stores or callback |

The two-channel display can therefore consume retained MP even though this
side1 receive branch only updates HP. Existing display proofs establish
channel 0/1 numerators at D+A7B0/A7B4 and divisors at D+A7A8/A7AC, with unsigned
display clamps and signed-divisor rendering arithmetic. There is no side1
E71E0 local-owner callback in these completed paths.

This establishes field purpose, not all source provenance. It does **not**
prove that monsters lack MP, that retained DEC/DF4 are zero, where their initial
values originate, whether a received side1 pair equals species base stats, or
how server HP/maxHP is produced. Side1 position/slot and `[B+83458]`'s first
DWORD are not independently proven monster-species identities here.
Subtype 6 also reaches the side1 wrapper statically because the side test
precedes the subtype check in 117230; the old side1 test contract covers only
0/1, so no new dynamic subtype-6 claim is made.

## Handoff Boundary

Main can close the continuous proof at E72A6 after the original stores with
explicit U, A and optional subordinate bindings. Stop before E72A6 executes
when claiming only scalar state; the UI refresh begins afterward. Keep its
separate format-pointer/numeric-argument slices explicit. A recovered codec
may name the audited fields and pairs while leaving species values, missing
side1 MP sources, combat formulas and runtime/DB promotion unclaimed.
