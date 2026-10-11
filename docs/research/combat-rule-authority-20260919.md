# Current-original combat rule authority, 2026-09-19

## Scope and outcome

Current original client only. The owner's superseding instruction retires all
previously supplied legacy material. It has no reference value for this deliverable.
No legacy source, formula, coefficient, database or filesystem root is required by
the extractor or tests. Existing retired files were not removed or read after that
instruction. Earlier historical investigation is excluded from this report's
evidence and conclusions.

Only these three files belong to this lane:

- `tools/strike_lab/recover_combat_rules.py`
- `tests/research/test_recover_combat_rules.py`
- `docs/research/combat-rule-authority-20260919.md`

The extractor preserves **381 skill books**, **1,202 card-effect descriptions**,
**448 selection definitions** and **nine native byte slices**. There are 243
explicit MP-cost descriptions; the remaining 138 costs stay absent, not zero.
There are **zero recovered authoritative server formulas** in this bounded
inventory. Damage, hit, crit, five-element coefficients and resource deduction
all have `status=unknown`, null formula/coefficients and `runtime_enabled=false`.
This is a limit of the inspected evidence, not a claim that recovery is impossible.

No monster stat catalog, runtime, CMake, game process, UI or network was changed
or run. Python tests execute original instructions in an offline emulator and stop
before graphics calls. No additional research agents were available through the
session's exposed tools.

## Inputs and reproduction

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.recover_combat_rules --summary
python -B -m tools.strike_lab.recover_combat_rules
python -B -m unittest discover -s tests/research -p test_recover_combat_rules.py -v
```

The first command prints counts/status/checksum; the second prints the complete
deterministic JSON to stdout. Neither writes an artifact. The last command passed
**12 tests**, no skips, in **3.028 seconds**. Bytecode writes are disabled by `-B`.
The native tests use the existing `artifacts/tooling/crypto-oracle-python` Unicorn
2.1.4 dependency. No C++ compilation or subprocess fixtures are used.

Optional `--client-root` and `--image` allow relocated copies of the same pinned
inputs. Changed/missing inputs fail; there is no fallback or invented coefficient.
The four data inputs opened by a complete build are asserted by a test that also
requires every file-open mode to be `rb`.

`G = C:/Users/risei/Desktop/God2/God2`

`S = C:/Users/risei/Desktop/God2/God2-Server`

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| G/Data2/Patch/Comm/gamedata.csvZ | 719032 | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| G/Data2/Patch/Comm/ChangeDollEffect.csvZ | 10719 | `535a1c1a690e7f78be7d6e27cf8d212e89ed5230e5c7213c0e4fbe1d3a7d8ef1` |
| G/Data2/Fight/Spg/cbspec2.bin | 112660 | `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51` |
| S/artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin | 3174400 | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |

Canonical inventory SHA-256 (ASCII JSON from `serialize`, including its final LF):
`1036de62202d9d72f634ba49dd376a80485840b25bf1478751f15347b48de6fc`.
The CLI's terminal newline handling is not the definition of this checksum.
The complete JSON also records decoded-table hashes, original row bytes/hashes,
line numbers, offsets, literal fields and native callsite bytes/hashes.

Only `parse_skills` is reused from `recover_combat_skills`; its separate catalog
builder is never invoked. Selection parsing reuses `current_skill_identity`.
The existing battle-command recovery was read as context. No file or symbol named
`current_basic_battle` was present in the bounded workspace search; the available
`tests/research/test_current_battle_command.py` covers command construction, not
combat formulas. No new claim is based on a nonexistent helper.

## Current descriptions and tables

Table lines are one-based, columns and decoded byte offsets zero-based. Text is
decoded strictly as CP950; original bytes remain the authority. Search categories
are explicit text matches, not field semantics. The output retains every source
row, including those with no matching term.

| Rule category | Skill-book description matches | Card-effect description matches | Server authority |
| --- | ---: | ---: | --- |
| Damage | 26 | 312 | Unknown |
| Hit | 1 | 290 | Unknown |
| Crit | 18 | 0 | Unknown |
| Five-element coefficients | 63 | 290 | Unknown |
| Resource cost | 319 | 198 | Unknown |

These are overlapping search counts. In particular, the resource search includes
MP-related descriptions such as restoration; it does not count known deductions.
The crit search covers the explicit terms U+66B4 U+64CA, U+7206 U+64CA and
U+6703 U+5FC3. Zero matching card rows is not proof that crit logic is absent.

Concrete retained examples:

- `gamedata.csvZ`, decoded line 8916, item 6501: column 9 literally states
  `\u4f7f\u7528\u6d88\u8017 5 MP`. This becomes `displayed_mp_cost=5`, while
  `server_resource_cost=null`. Row SHA-256:
  `60ecb5b6d632e5439a280cf53fa2b32755c5dc13b2507b4522b6a74dd1d5c2cb`.
- `ChangeDollEffect.csvZ`, decoded line 7, index 2: raw code `GOD_6421`, raw
  base-value column `50`, description of metal-attack absorption restoring
  `Hp 5%`. Row SHA-256:
  `798ae4c1dca55b705fdbf1af6b7a8b6cc75f674cf3e17d1a9f90494b99f47987`.
- Same table, decoded line 307, index 302: code `SPC_6821`, raw base-value `5`,
  description of increasing a named skill's hit probability `5%`. Row SHA-256:
  `b3819a4bd411a18db434850e94e07cd3fe11376ddc59749e77cf94fc9aa11c30`.
- Same table, decoded line 941, index 936: description of pet physical damage
  reduction `1%`. Row SHA-256:
  `825d7da33bca4cdc70fe70b25b3472a3bb0206d7e110bfd2053b57713c108893`.

The literal `50` versus `5%`, and elsewhere `5` versus `5%`, specifically do not
justify a universal numeric-column divisor. No percent stacking, chance baseline,
element multiplier, proc rule or monster assignment is inferred.

All populated 110-byte `cbspec2.bin` records retain raw bytes, source offsets and
hashes. Only their established `(kind, ID)` identity is normalized. Other bytes
are not assigned cost/effect/rate semantics, and no book-to-selection join is
invented.

## Native arithmetic and authority boundary

Image base is VA `00400000`. Offsets below are RVAs in the mapped image, and end
RVAs are exclusive. Full original bytes and the following hashes are emitted.

| Slice | RVA range | SHA-256 |
| --- | --- | --- |
| Display scaling | `108E70..108F48` | `09157fd5b0162b966b551c07d5b69e7f05847207c6997ca90189ddb2047c3c52` |
| Display clamps | `108F50..108FB1` | `390ccd500da18e3bec4b58ff81d9515dc3c8430593948e30b9f949d07b0f8c13` |
| Supplied divisors | `108FC0..108FFE` | `a762c17f1641215c7c6f61e552d7325e794e8fc8d294224d1a1b9ef0a1281774` |
| x87 truncation | `149630..149657` | `d0a2aca68648a0ae9d5cbfae1b276d4a64d4f797fc0c60f28b64096cdfa3148c` |
| Supplied-value caller | `1173A0..117472` | `6239c4b7175d313bda46166704cb7b507d3901c7d95706173cdc5b73a80daf80` |
| Supplied-value consumer | `12D970..12D9E5` | `5d1ed07aaedeec218a3c890f68a59adf3fcf711998efbb6c3ed4d1a93546d261` |
| Companion consumer | `12D840..12D8B5` | `c3d5d8a6a016118515ea33a9cd375b6c33ec59f38cb5a90e7d4f2e20ac793fa3` |
| Selection producer | `11C520..11C7BF` | `f07f20f890df718aee5d4cfd5fce0c3924bf27f5db10414ee597e8b5f908c64f` |
| Command identity packing | `11913D..11914F` | `1b4ad92cc98999440dbb468c44726d590904a7f45d1c0e7741d337234f6ea2c2` |

The two arithmetic expressions recovered are display operations:

```text
R = this + 0x1c + (handle & 0xffff) * 0xa7e0
valid handle: (handle & 0xffff) < 0x1000
R[A7B0] = min_unsigned(arg2, R[A7A8])
R[A7B4] = min_unsigned(arg3, R[A7AC])

extent0 = low32(trunc_x87(uint32(R[A7B0]) * int16(R[A7A4]) / int32(R[A7A8])))
extent1 = low32(trunc_x87(uint32(R[A7B4]) * int16(R[A7A4]) / int32(R[A7AC])))
```

The quotient description is qualified to finite, representable conversion inputs;
the tests use nonzero divisors. No zero-divisor guard exists in the extracted scale
blocks, and no exceptional-input server policy is invented. Each channel is
conditional on its signed WORD display handle being nonnegative. `149630` forces
truncation for `FISTP`, then restores the x87 control word. The low DWORD is stored
in the rectangle extent before the call to `1BDC0`. That call is never executed by
these tests. The second channel block is entered directly with prepared registers;
the tests do not claim a continuous two-channel render.

The supplied-value chain is also explicit: `1173F9/1173FC` loads buffer DWORDs
`+5/+9`, then `11740A` calls `12D970`. That consumer stores them at actor `+DEC/DF4`
and calls `108FC0` at `12D9BE`, then `108F50` at `12D9DB`. The companion `12D840`
stores supplied fields at `+DE8/DF0`. These are value-copy/display consumers.
Their dispatch opcode, incoming-buffer provenance and exact HP/MP names are not
proved by this lane. They cannot establish how a server computed a damage result.

The selection producer and command packing support identity only. They do not
prove skill ownership, book IDs, resource sufficiency or resource deduction.

## Verification and unresolved semantics

The 12 tests verify repeat builds using only the four pinned inputs, JSON
round-tripping, every table/selection/native byte slice and hash, malformed table
rejection, changed-input rejection, absence versus zero, and non-promotion of
description values. Native checks execute the original clamp/setter/scale and
conversion instructions with synthetic fixtures, including unsigned high-bit
values, negative width/divisor, invalid handles, high-WORD handle truncation and
restoration of the x87 control word. No instructions or helper calls are replaced.
The caller/consumer linkage is static byte evidence, not an executed receive path.

Unresolved: attack/defense-to-damage arithmetic; damage minimum/randomness/caps;
authoritative rounding and modifier ordering; hit/evasion/status probability;
crit trigger/multiplier/flags; five-element coefficients and stacking; skill-book
to selection mapping; actual MP/HP/item deduction and timing/refunds; exact
supplied-value field meanings and packet provenance. No default fills any gap.
