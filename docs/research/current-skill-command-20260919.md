# Current kind-0 skill record boundary, 2026-09-19

## Delivery

- `src/protocol/RecoveredSkillCommand.h`: header-only C++20, independent
  `god2::RecoveredSkillCommand::parse_logical(span)` returning `optional<Record>`.
- Input is exactly one 17-byte decrypted logical record, including opcode 0x35.
  It accepts only action 0x03/0x83, selected-entry kind 0, and exactly one bit
  across the first two 14-bit target masks. This is a supported structural subset,
  not a claim that every native skill path has this shape.
- `parse_sequence(span)` additionally validates exactly one caller-delimited
  candidate of 1..14 records, returning `optional<Sequence>` with fixed storage
  and a count of populated records. Every record must satisfy `parse_logical`;
  only the last may lack continuation. Actor, side, context storage and the
  selected-entry byte must agree. Target order, duplicates and each record's
  opaque unwritten byte are preserved. No allocation or runtime integration.
- `runtime_mutation_enabled` remains false. The basic-attack parser is unchanged
  and still rejects every skill record. Shared runtime is untouched.
- Integration registers `tests/test_recovered_skill_command.cpp` as standalone
  C++20 target `recovered-skill-command`, CTest `recovered_skill_command`, with
  warnings treated as errors. No library or runtime linkage is needed. The
  Python suite also compiles and executes it in a private temp directory.

## Legacy evidence read before native work

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.

Read `src/God2.ClassicServer.Protocol/OfficialBattleCommandWire.cs`, SHA-256
`06e147cac8ac7aed5df46fdbddd7cd114f0bccd13e2e9f22b11e6f86be4549c5`.
It names action 3 as Skill, identifies bit 0x80 as continuation and withholds
runtime mutation. Its different-build RVA and three-target-mask interpretation
are not authority for this current image.

XJZ root:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.

- Read `cpp/xjz_combat_command_contracts.hpp`, SHA-256
  `e25f8c5b8e89e6207b0185b640c6e5afd9b70a83251024813820695f26729ea3`.
  Its semantic skill/session service interfaces do not prove current wire fields.
- Read `evidence-skill-runtime-capture-target-v0.md`, SHA-256
  `7cf668ef1cf3427a51d27ace060f026cde193f83d85e7a1d37ddeb40bea576a6`.
  Runtime skill IDs, costs, target restrictions and results are explicitly missing.
- Read `evidence-combat-formula-v0.md`; final damage/hit equations remain outside
  the evidence boundary. None were implemented.

Also read the current battle document/header/tests, `reverse/findings/battle_flow.md`
and `tools/strike_lab/recover_combat_skills.py`. The latter recovers skill-book
metadata, explicitly not a book-item-to-runtime-selection mapping.

## Current instruction authority

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
x86 base 0x400000; RVA equals image offset. Tests verify the entire image hash.

Tests execute original entry RVA 0x118E50 to post-queue boundary 0x1191EE or the
original early return. Real selection lookup 0x1156A0, accessors 0x11B8C0/0x11B900
and queue copier 0x132E0 execute without stubs. Fixtures provide synthetic memory;
no original process, transport, UI or post-queue cleanup runs.

| RVA | Instruction-backed contract |
| --- | --- |
| 0x118E54 / 0x118E79 | Low action byte; unsigned low actor byte must be <=14 |
| 0x118E84 | Signed target count >14 returns early |
| 0x118EAF | Action 3 requires a non-null selected-entry lookup result |
| 0x1156A0..0x1156DB | Passes the signed selection index at this+0xA9DF73C to the chosen accessor |
| 0x11B8DF..0x11B8F2 / 0x11B92B..0x11B93B | Rejects index <0 or >=entry count, then loads a DWORD entry pointer at index*4 |
| 0x118EC4 | Copies full context DWORD from this+0x3C to body+8 |
| 0x118ECE..0x118EDF | Initializes side byte 0, or 1 for first mode zero / second nonzero |
| 0x119075..0x11907A | Reads selected-entry byte 1; kind 0 branches to 0x11913D |
| 0x11913D..0x11914B | Zeroes ECX, loads kind into CH and selected-entry byte 0 into CL, writes DWORD at body+12 |
| 0x119141..0x11914F | this+0x468 ==0 chooses the per-target branch tested here |
| 0x119170..0x119172 | Signed count <=0 queues nothing in this branch |
| 0x119180 / 0x119183 | Reads one target byte and clears only body+4..7 for each iteration |
| 0x11918E..0x1191B4 | Assigns WORD bit(target%14) at body+4+2*(target/14) |
| 0x1191BB / 0x1191C6 | ORs action with 0x80 before last target; restores original low action on last |
| 0x1191CD..0x1191E0 | Requires network +0x2CB8 nonzero, then queues opcode 0x35 and 16 body bytes |

The record contains actor at offset 1, action at 2, side at 3, unwritten stack
byte at 4, target WORDs at 5/7, opaque context DWORD at 9, and selected-entry
byte 0 at offset 13 followed by three zero bytes for kind 0. The selected byte
is retained as `selection_id_byte`; it is not asserted to be a catalog skill ID.
The selection index is separate: it chooses the entry pointer and is not emitted
in this parameter. The shared battle test helper's existing `skill_id` argument
means entry byte 0 only; its name does not establish any catalog identity.

Each in-range target produces a separate record. Input order and duplicates
are preserved, including 14 identical targets. Native output can therefore be
up to 14 records. `parse_logical` still accepts one record per call and exposes
its continuation bit. `parse_sequence` validates an already-delimited sequence;
it does not accumulate packets or authorize execution.

For the supported targets 0..27, the loop only changes masks and action. Actor,
side, context and parameter are initialized before the loop and stay fixed.
This backs the sequence consistency checks. Unwritten body byte 3 is not a
semantic identity and is intentionally not compared across records.

Unlike the basic-attack OR loop, this skill loop assigns the target WORD.
Targets 28..41 replace context's low WORD; 42..55 replace its high WORD. Both
target masks remain empty, so those isolated records are rejected. A later
in-range record can retain context changed by an earlier out-of-subset target;
opaque context cannot establish that the original target list was valid.

## Executed validation

Run from the server root:

```text
python -B tests/research/test_current_skill_command.py -v
python -B tests/research/test_current_battle_command.py -v
```

Both suites passed: 11 skill tests and 6 existing battle tests. Each compiles its
standalone C++20 fixture with warnings as errors. Skill tests execute the C++
assertion mode and feed original-builder output through its `--decode` interface.
The skill fixture also provides `--decode-sequence`, returning one decoded row
per populated record or `reject` for the entire candidate.

- Exhaust all 65,536 WORD values independently in each target group, plus all
  256 byte values at opcode, actor, action, side, unwritten byte and parameter
  offsets. Both groups populated together are rejected.
- Compare every output field for selection bytes 0/1/0x7F/0x80/0x9B/0xFF,
  actor/action DWORD high bits, both side branches and stack poison 0/0xA5/0xFF.
  Write hooks verify only body byte 3 remains unwritten.
- Check target 0/13/14/27 boundaries, ordering, duplicates, fourteen-target
  continuation and terminal flags, signed empty counts, count overflow, missing
  lookup, inactive/disabled modes and disconnected queue guard.
- Execute kind 1/2/3 as negative controls: their nonzero parameter kind byte is
  rejected. Kinds 4/0x80/0xFF queue nothing. Context alias cases above are rejected.
- Reject every truncated length, trailing bytes, concatenated records, a framed
  wrapper, basic attack, unsupported actions, side/actor bounds, empty/multiple
  targets, reserved mask bits and unsupported parameter bytes.
- Compare original-builder sequences of every length 1..14 through the C++
  process in both side modes, preserving target order and duplicates.
- Sequence negatives cover every truncated byte length of a three-record
  candidate, unterminated prefixes, early terminal flags, extra/framed bytes,
  two concatenated sequences, fifteen records, basic attack, invalid fields
  and masks in every record position, and individually valid records with
  inconsistent actor/side/context/selected-entry fields. Different unwritten
  bytes remain accepted and are returned unchanged.
- A skill-local VM setup hook installs two entries before the original builder
  executes. Both native accessors select index 0/1 independently of entry byte
  0/0x9B/0xFF; negative indices, index equal to count, 0x9B and 0x100 produce no
  record. The real lookup, builder and queue copier run without code stubs.
  No shared oracle fixture or battle helper was edited.

## Bounded guard-page verification

Parser inspection found no concrete size-check, indexing or sequence-consistency
defect. `RecoveredSkillCommand.h` is unchanged by this verification patch; no
additional native branch or gameplay behavior is promoted.

The standalone C++ fixture adds `--guard-sequence logical_hex`. The Python test
supplies original-builder output for every count 1..14, alternating side modes
and including target-mask boundaries and duplicate targets. Each candidate is
copied into an OS allocation with inaccessible outer pages. The middle page is
made read-only before parsing, with the input placed first flush against the
leading guard and then flush against the trailing guard. Protection/allocation
failures fail the test; access violations fail the subprocess. Empty input also
runs with its pointer at the trailing inaccessible page, plus a default empty
span. No executable client process or desktop interaction is involved.

Deterministic cases cover:

- Every byte-length prefix of every record-aligned suffix, including empty
  spans and valid terminal suffixes. Partial records and unterminated prefixes
  must fail closed; complete suffixes remain accepted by the existing contract.
- Every single-bit mutation at every byte of multi-record seeds. Only each
  record's opaque unwritten byte may change independently without rejection.
- All 256 paired substitutions across each internal record seam (preceding
  record's final kind-zero byte and following opcode), plus byte insertion and
  deletion immediately before, at and after each seam.
- All 256 values of each record's unwritten byte, varied independently across
  positions, with coordinated changes to all four context bytes and the
  selected-entry byte. Accepted output is serialized in the test and compared
  byte-for-byte with the entire supplied record, preserving order and duplicates.
- Concatenated complete sequences and a fifteen-record candidate with otherwise
  valid headers and continuation flags. Both are rejected.

The Windows run passed 102,502 guarded sequence checks (51,251 candidates placed
at both page edges). Each placement also calls `parse_logical`, rejects incorrect
record lengths and checks lossless output whenever accepted. The 11-test skill
suite and unchanged 6-test battle suite compiled through the existing helper in
private temporary directories with C++20 and warnings as errors. No shared
build/CMake/helper files were edited. `-B` suppresses Python bytecode writes.

This is reproducible bounded testing, not proof for all possible byte strings.
The POSIX `mmap`/`mprotect` implementation is present but was not executed in this
Windows workspace. A guard catches reads crossing the guarded span edge; the
opposite edge is exercised in the second placement. This does not establish
transport framing, provenance or cast authorization.

## Exact remaining boundary

Sequence validation establishes a bounded structural shape, not that the native
invocation's entire output was received. A terminal record alone or a suffix
ending in a terminal record may pass; there is no start marker, original count
or sequence identifier in this subset. Replay, missing prefixes/interior
records, reordered targets, and splices with identical initialized fields cannot
be detected. Caller-supplied boundaries remain necessary; no stream assembler
or transport integration was added.

This does not prove server battle entry,
participant ownership, turn legality, skill ownership, resource costs, target
legality, damage or result encoding. It does not identify the selected-entry byte
with an SKB book/catalog entry. A lone continuation record still parses with
`parse_logical` but is rejected by `parse_sequence`; neither authorizes execution.

The next evidence blocker for runtime integration is the selected-entry
byte/kind to authoritative skill identity mapping and corresponding server cast
validation/result semantics. The this+0x468 !=0 aggregation helper and other
kind branches are outside this patch. Keep mutation disabled; there is no
end-to-end battle or playability claim.
