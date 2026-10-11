# Current skill identity and selection-state producer, 2026-09-19

## Delivered boundary

The previously pending `1156A0 -> 11B8C0/11B900 -> 11913D` chain now has a
source-backed producer: **11C520** builds selection pointers from the pair
**(kind, one-based ID)** in `Data2/Fight/Spg/cbspec2.bin`. The selection index
is the insertion-order slot in a particular client bank. It is not the ID.
The same ID can occur in each kind; this is not a global skill ID.

The actual source contains 448 populated definitions: kinds 0/1/2/3 contain
121/129/87/111 records. Every populated record's bytes 0/1 equal its direct
addressing ID/kind. This closes the source-record identity gap for this client
table. It does not join SKB book items, monsters, or server-owned skills.

Changes are limited to:

- `src/protocol/RecoveredSkillCommand.h`: exact two-byte state decoder and
  checked source-record offset lookup, alongside the unchanged command parser.
- `tests/test_recovered_skill_command.cpp`: `--identity-batch source_file`
  subprocess interface. Reads one state-word hex string per stdin line.
- `tools/strike_lab/current_skill_identity.py`: source identity decoder and
  bounded client selection-bank consumer preserving insertion order and state.
- `tests/research/test_current_skill_identity.py`: original native producer,
  accessors, command builder, C++ subprocess and source regressions.
- This document.

No CMake, network, session, Lua, world actor, runtime or UI edits. No other
agents or original client processes were started. The server folder has no
Git metadata (`git status --short` reports not a repository); existing files
were inspected directly and patched without reverting other work.

## Legacy evidence read first

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.

XJZ root, relative to the server:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.

| Root / file | SHA-256 |
| --- | --- |
| Classic / `src/God2.ClassicServer.Protocol/OfficialBattleCommandWire.cs` | `06e147cac8ac7aed5df46fdbddd7cd114f0bccd13e2e9f22b11e6f86be4549c5` |
| XJZ / `cpp/xjz_combat_command_contracts.hpp` | `e25f8c5b8e89e6207b0185b640c6e5afd9b70a83251024813820695f26729ea3` |
| XJZ / `evidence-skill-runtime-capture-target-v0.md` | `7cf668ef1cf3427a51d27ace060f026cde193f83d85e7a1d37ddeb40bea576a6` |
| XJZ / `evidence-combat-formula-v0.md` | `1a5ad8fb0a31215db965538b959ce0bed1ac5648735763eaa15b24e687486139` |

Classic provides the action-family label and explicitly withholds runtime
mutation. XJZ defines semantic services and missing capture targets, not the
current source/slot relationship. No legacy formulas or ownership were imported.
Also read all three requested current research documents, existing skill and
battle fixtures/header, battle-flow notes and `recover_combat_skills.py`.

## Exact source and loader

Image, relative to server root:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base `0x400000`; listed addresses are RVAs and image offsets.

Source:
`C:/Users/risei/Desktop/God2/God2/Data2/Fight/Spg/cbspec2.bin`.
112660 bytes; SHA-256
`7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
Tests verify both complete hashes before execution.

| RVA | Concrete instruction evidence |
| --- | --- |
| `110AC1` | EBP = battle object + `144938` |
| `110C21..110C45` | Uses string VA `59C5E4`, `data2\fight\spg\cbspec2.bin`, then calls `12D3B0` with ECX=EBP |
| `12D3CC..12D3F2` | Reads 4 bytes and compares with version string `1.03` at VA `59DB54` |
| `12D417..12D425` | Reads `1B810` bytes unchanged to loader-this + `A7E0444`; `144938 + A7E0444 = A924D7C` |
| `111671..1116A4` | Passes battle + `A924D7C` as argument 9 of selector initializer `11BB80` |
| `11BB86 / 11BBA4` | Stores that pointer at selector + `3518` |
| `117540..117556` | Skips one leading caller byte and passes the next address to `11C520`; returns 1 |

The loader path above was disassembled, not executed with mocked file IO.
Native identity tests map the exact source body `file[4:]` at a synthetic
catalog address, matching that raw-read destination. All identity-producing
instructions execute unchanged. Neither a C++ lookup nor a Python lookup is
substituted for an original instruction/helper.

The four-byte version is followed by four groups. Each group is `0x6E04`
bytes: a DWORD count followed by 256 records of 110 bytes. Only count-declared
records are exposed by the checked source decoder. Other record bytes are
retained unchanged; costs, names, effects and rates are not assigned semantics.

```text
source offset = 8 + kind * 0x6E04 + (ID - 1) * 110
native pointer = catalog body base + source offset - 4
```

For example kind 0 / ID 121 resolves to source offset 13208. It can occupy
selection slot 0, followed by IDs 1 and 65 at slots 1 and 2. Native command
output emits 121, 1, 65, not 0, 1, 2.

## State and slot semantics

| RVA | Established behavior |
| --- | --- |
| `11C52B..11C544` | Read LE WORD; ID=low byte, kind=high byte & `3F`, routing bit=`4000` |
| `11C54D..11C574` | Primary bank byte at selector +4 is signed and must be 0..15; bank stride `2D0`, bank base selector+`10` |
| `11C580..11C5BC` | Search pointer records by both ID and kind; matching slot replaces only stored WORD bit 15 |
| `11C5C7..11C62B` | Append raw WORD and calculated source pointer, increment count, update page count |
| `11C631..11C6B9` | Primary auxiliary pointer list can mirror incoming bit 15 to bank+`25C` indexed by its own matched position |
| `11C6C6..11C6F7` | Alternate bank selector at +`2D10`, unsigned 0..2; stride `54`, bank base selector+`2D14` |
| `11C702..11C741` | Alternate table searches by pair and updates only bit 15 on match |
| `11C745..11C7B2` | Alternate auxiliary state byte at bank+`3C` follows bit 15; append uses same source-pointer calculation and increments count |
| `1156A0..1156DB` | Alternate accessor iff first mode is zero and second nonzero; otherwise primary. Signed selection index comes from battle+`A9DF73C` |
| `11B8C0..11B8F7` | Primary pointer at bank+`CC`+4*slot, count at bank+0; reject signed slot <0 or >=count |
| `11B900..11B940` | Alternate pointer at bank+`14`+4*slot, count at bank+`50`; same signed slot bounds |
| `11913D..11914B` | Kind goes into CH, selected entry byte 0 into CL; parameter DWORD receives ECX |

Primary WORDs begin at bank+4; alternate WORDs begin at bank+0. Their physical
arrays hold 100 and 10 entries respectively. Python `SelectionState` implements
these bounded WORD/pointer-equivalent lists, not auxiliary display mirrors,
pagination, bank-changing handlers or an entire original object. Bank selection
is caller supplied. Duplicate updates do not append or reorder entries.

`parse_state_word` decodes every WORD, including unsupported source identities.
`definition_offset` requires exact source length/version, kind 0..3, nonzero
ID within the group's count (bounded to 255), and matching record ID/kind.
Python additionally validates all declared record prefixes on catalog decode.
These checks are this implementation's supported source subset. The native
producer does not check source population or insertion capacity. A regression
executes ID 122 in kind 0 and observes the original pointer append despite the
source count being 121. No fictitious original rejection rule is claimed.

The incoming bit 14 selects table family but is not part of kind. Bit 15
changes client state but is not part of identity. Neither flag becomes the
command ID or proves ownership, learned status, resource availability or
permission. The C++ command parser still accepts only its previous kind-0,
per-target subset, and `runtime_mutation_enabled` remains false.

## Reproducible verification

```powershell
python -B tests/research/test_current_skill_identity.py -v
python -B tests/research/test_current_skill_command.py -v
```

The identity suite compiles the existing standalone skill fixture with C++20
and warnings as errors under a unique
`artifacts/skill-identity/native-<random>/` directory. It never uses a shared
build tree. Its private generated files are cleaned on success/failure.

- All 65,536 state WORDs pass through the C++ subprocess decoder/source lookup.
  Populated vs absent source identity, both flags and all six kind bits are checked.
- All 448 populated definitions execute the complete original `11C520` producer
  with both routing and state bits: 1,792 native cases. Original accessors return
  the expected pointer, and all 110 bytes equal the actual source record.
- Primary banks 0/7/15 and alternate banks 0/2 retain independent insertion
  order; duplicate updates preserve slot and pointer while replacing bit 15.
- Full native tables of 100/10 entries and duplicate updates agree with the
  bounded model. Accessor indices -1 and count return null. Model overflow fails
  closed; unsafe native overflow is not executed.
- The original producer feeds `1156A0`, both accessors, the `118E50` builder and
  `132E0` queue copier. Twelve kind-0 commands across four bank configurations
  are decoded by the C++ process. Execution stops at `1191EE` before cleanup.
- Source truncation/version/count/identity mismatch, invalid banks, missing
  definitions, invalid slot bounds and malformed WORD lengths are rejected at
  their respective checked boundaries. Existing C++ command assertions run too.

Result: 7 identity tests passed. The unchanged 11-test skill-command Python
suite also passed, including its original native/sequence/guard regressions.
For that compatibility run `tempfile.tempdir` was set to
`artifacts/skill-identity` before invoking its unittest suite, so both executable
builds stayed in unique lane-local directories. No CMake target was added;
there is no proposed CMake change for main to merge.

## Native byte-span hashes

End RVAs are exclusive; hashes are SHA-256 of the exact image slices.

| Start..end | SHA-256 |
| --- | --- |
| `12D3B0..12D43D` | `b5addbd87f026f7508bd18751a150ce832a4fea24444a3be4c665ea446aad2bd` |
| `117540..117559` | `f19355521697b63a9a557a292f81b582302303c157d676c8386bbc822efe4882` |
| `11C520..11C7BF` | `f07f20f890df718aee5d4cfd5fce0c3924bf27f5db10414ee597e8b5f908c64f` |
| `1156A0..1156DE` | `d8eb34f42825616e908b14574aa895ec40a2c304a2a8441061bd7e318648ba7f` |
| `11B8C0..11B943` | `d98f30c48da4b3d0f492159d05e274d55aa8276513282e5ad01ee9133bbda95e` |
| `11913D..11914F` | `1b4ad92cc98999440dbb468c44726d590904a7f45d1c0e7741d337234f6ea2c2` |

## Remaining concrete constraints

`117540` is a real producer wrapper but its caller dispatch/opcode and exact
network record framing were not established. The two-byte API deliberately
does not assert a new S2C opcode or construct a network record. The original
full source file loader and UI initialization were not executed by these tests.

The source relationship is (kind, ID) to this client's cbspec2 definition, not
SKB item ID to learned skill, monster to skill, or authoritative server actor
to permitted cast. The source decoder's checked membership cannot supply any
of those missing relationships. Auxiliary mirrors and the initial source of
the state WORD beyond the wrapper remain outside the implemented consumer.

Next concrete native work: trace callers/dispatch into `117540` and the bank
selection/update handlers around `11C7F0`/`11C8E0`, preserving the established
source binding. Costs, effects, formula/rates, server authority, cast results
and complete battle playability are not claimed by this delivery.
