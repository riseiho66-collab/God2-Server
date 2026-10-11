# Current-original monster EXP evidence, 2026-09-19

## Result and scope

**No source-backed per-monster base-EXP records recovered in this bounded scope.**
The new extractor emits an empty evidence list and explicit JSON nulls for
unproven semantics. The zero record count means no proven records, never zero
monster EXP. It does not generate a native monster EXP table from guesses.

Positive result: the pinned current original image has an opcode 0x89 consumer
that displays separate recipient EXP values. Offsets +5 and +9 feed different
recipient messages. They must not be described as base and credited stages of
one player's award. This is a packet/display contract, not an award formula.

Owner's superseding directive is effective: Classic and XJZ are RETIRED and have
no reference value for this deliverable. Earlier exploration is rejected
historical context only; no values, formulas, identities, parsers, fixtures, or
roots from it enter the extractor or tests. Those files remain physically on
disk and were not deleted or read after retirement. The earlier monster audit
and recover_monsters were consulted before the directive; neither is a dependency
or authority for the current result.

Only the following three files were created:

- `tools/strike_lab/recover_monster_experience.py`
- `tests/research/test_recover_monster_experience.py`
- `docs/research/monster-experience-evidence-20260919.md`

No runtime, CMake, client file, shared source, UI, game process, capture session,
network service, or role/companion-growth implementation was changed or run.
Tests execute copied original instructions inside synthetic Unicorn memory.

## Exact original inputs

`G = C:/Users/risei/Desktop/God2/God2`

`S = C:/Users/risei/Desktop/God2/God2-Server`

All five complete input SHA-256 values are pinned; mismatch fails closed.
The extractor uses the existing read-only `omega_assets.decode_csvz` helper.
It opens only the four listed client tables and explicitly supplied image.
Tests use the existing `S/artifacts/tooling/crypto-oracle-python` dependency.
No retired corpus or historical packet fixture is required.

| Exact path | SHA-256 |
| --- | --- |
| G/Data2/Patch/Comm/gamedata.csvZ | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| G/Data2/Patch/Comm/message.csvZ | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |
| G/Data2/Patch/eny.csvZ | `6aa84aeb0399e39e0db27eeebf9bb0f8b274fcbd609e1b83be3542a5d53f294c` |
| G/Data2/Patch/FightEny.csvZ | `887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a` |
| S/artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |

The mapped x86 image is 3,174,400 bytes, base VA 0x400000; RVA equals
file offset. Source bytes, decoded hashes, exact line offsets, record hashes,
native span bytes/hashes, and absolute source paths are retained in stdout JSON.
The decoded message-table SHA-256 is
`370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.

## Verified current consumers

All offsets below are from the beginning of the logical record, including opcode.
These facts are derived independently from current instructions and current text.

| Current location | Verified fact |
| --- | --- |
| RVA 0x1324 + 4*0x89 = 0x1548 | Size-table pointer targets VA 0x401240 |
| RVA 0x1240 | `mov eax,0x39; ret`: 57-byte logical size |
| RVA 0x1193C4..0x1193E6 | Reads record opcode; compressed map 0x119A04[0x89] = 24; target table 0x119908[24] points to RVA 0x1195CC |
| RVA 0x1195CC..0x1195E1 | Passes the record and queried length to queue copier 0x11D4E0 using owner+0xA9EA4B0 |
| RVA 0x114332..0x114357 | Queued opcode minus 0x1C selects map 0x11465C[0x6D] = 8, table 0x114634[8] points to 0x114582 |
| RVA 0x114597..0x11459E | Calls consumer 0x118BF0 with the copied logical record |
| RVA 0x11125F..0x1112A4 | Original initialization loop binds ten ProgramMsg pointers to globals VA 0x5B8B48 onward |
| RVA 0x19BE68..0x19BE7B | Ten uint16 message IDs: 293,294,295,296,297,298,299,300,397,398 |
| RVA 0x118BF8 | Branch selector reads record DWORD +49 (not +53) |
| RVA 0x118C6F..0x118C86 | DWORD +5 is the argument for global VA 0x5B8B50 / ProgramMsg 295 |
| RVA 0x118C87..0x118C9E | DWORD +9 is the argument for global VA 0x5B8B54 / ProgramMsg 296 |
| RVA 0x118C9F..0x118CBA | DWORDs +13 and +53, in that order, are arguments for VA 0x5B8B58 / ProgramMsg 297 |
| RVA 0x852B0..0x852CE | Shared formatting routine passes the format string and variadic argument pointer to its formatting helper |

The EXP display block is conditional. Consumer entry dispatches on +49; the
branch starting 0x118C0B examines four entries starting +17, stride 8. Other
flags can select alternative messages. This report does not infer full victory,
loss, inventory, or reward-commit semantics from those branches.

Current `message.csvZ` physical lines, decoded CP950:

| Section / ID | Line | Literal format | Record SHA-256, including CRLF |
| --- | ---: | --- | --- |
| ProgramMsg 295 | 2321 | 主角 獲得經驗 %d | `a8bc3ae180944ce8e660cacbd5333ce7b912d211aed7c58dcaafeb0c04717de5` |
| ProgramMsg 296 | 2322 | 神仙 獲得經驗 %d | `a3f584300bc9a554027f65bfe331360126e3149eb34fd532db6ded0f1f90f305` |
| ProgramMsg 297 | 2323 | 戰寵/洞府經驗 %d/%d | `f03df3b71f22a057ce3bc1f593fe08fe0a89ec732c46f1165ef1be1fa47a0afc` |

These are 32-bit loads passed unchanged to `%d`. Signed display formatting does
not establish the server's legal EXP range, arithmetic width, or overflow policy.
There is no monster ID argument in these display loads and no demonstrated
lookup of a per-monster base-EXP table in this bounded slice.

## Distinct evidence classes

| Category | Current evidence and limit |
| --- | --- |
| Monster base EXP | Unknown. No authenticated monster/value rows recovered. |
| Received award display | The three recipient formats and four record offsets above are verified. They do not establish persistent XP mutation or the formula producing them. |
| Player level penalties | Unknown. No level-difference formula recovered. |
| Party split | Unknown. No divisor, weights, range, or participation rule recovered. |
| Event/item modifiers | Text evidence only: SystemMessage 512/513 (lines 587/588) describes a timed battle-EXP item and repeat-use restriction; 1480 (1555) describes an event usable with items; 1521 (1596) describes conflicting event effects; 1645 (1720) includes time and percent placeholders. No multiplier values, stacking arithmetic, or native trigger binding proved. |
| Player/pet/companion thresholds | Unknown and outside this implementation. Award-display DWORDs and percentage placeholders are not level requirements. |
| Visual/card/PET identities | No joins performed. `eny.csvZ` and `FightEny.csvZ` each contain 215 visual definitions; headers are retained, absent EXP is not filled. |
| gamedata markers | Exact lexical marker inventory retained. EnyName grouping, PET sections, and other opaque numeric columns receive no EXP semantics. |

No candidate numeric monster base EXP values are emitted. Message text about
modifiers is only a research lead; it is not an executable original rule.
The absence result is bounded to the four named tables and traced image slices,
not an assertion that every original file/function has been exhausted.

## Reproduction and verification

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

Extractor, stdout only (no generated artifact writes):

```powershell
python -B -m tools.strike_lab.recover_monster_experience --client C:/Users/risei/Desktop/God2/God2 --image artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin
```

Focused tests:

```powershell
python -B -m unittest discover -s tests/research -p test_recover_monster_experience.py -v
```

Final result: **7 tests passed**, exit 0, 0.986 seconds. The extractor CLI also
completed successfully; its stdout JSON parsed with PowerShell `ConvertFrom-Json`
and reported zero proven monster base-EXP records and `runtime_eligible=false`.

The suite checks byte-exact message provenance, fail-closed hash pins, missing
messages, deterministic CLI output, explicit unknowns, and both original opcode
dispatch slices. It executes the original message-binding loop and three EXP
argument-loading blocks with deliberately unequal synthetic DWORDs, including
zero and high-bit values. Synthetic sentinels are never exported as evidence
of actual monster awards. Execution stops before formatting/UI calls; no helpers
are stubbed, and no claim of a full live settlement is made.

The extractor itself uses Python standard library plus the existing CSVZ decoder;
Unicorn is required only for instruction tests. Initial verification exposed a
dependency search-path issue and an incorrectly targeted negative-test mutation;
both were corrected within the owned test file before the final run.
