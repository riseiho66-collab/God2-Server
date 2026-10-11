# Current Battle Learned Skills, 2026-09-20

## Scope and Evidence

`NativeBattleLearnedSkills` composes with `NativeBattleCharacterBinding` and
executes the original S2C34 dispatcher and writer in the caller's existing VM.
It stops before refresh, diagnostic calls, or assertions. It does not load
cbspec2, construct a character, infer owned skills, or qualify later consumers.

Only the current image is used, at base `00400000`, with RVA = file offset:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The standalone tests use the current source resource:

`artifacts/capture_work/host-20260918-1430/client/Data2/Fight/Spg/cbspec2.bin`

SHA-256: `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.

**Raw-fixture boundary:** tests directly map this file's payload after its
four-byte `1.03` header. Those bytes are not claimed to be native-loaded.
Synthetic S2C30/S2C34 packets exercise original code; they are not account data.
There are no archives, network, UI, live processes, child agents, game stubs,
or formula/ownership assumptions in this proof.

## Logical Packet and Catalog

The current length table at `1324+34*4` points to `1264`, which returns **4**.
The dispatch table at `6B5D4+34*4` points to `69FDF`. The original `inc ebx`
skips the opcode before `69FE7` calls `AA660`.

| Logical offset | Width | Meaning |
| --- | --- | --- |
| 0 | BYTE | Opcode 34 |
| 1 | BYTE | Unsigned key, compared with an existing row's WORD key |
| 2 | BYTE | Catalog bank, qualified here as 0..3 |
| 3 | BYTE | One-based entry, 1..255 and within the populated bank count |

No extra field, padding, framing, or encoded transport bytes belong to this
four-byte logical packet. It must be supplied explicitly as `bytes`.

The catalog payload is `1B810` bytes: four banks of `6E04`, each with a DWORD
count followed by 256 slots of `6E` bytes. Current source counts are
121, 129, 87, and 111. Record byte 0 is entry identity and byte 1 is bank.
Entry 256 cannot be expressed in this packet; zero enters native assertion
code and is rejected. The helper also rejects empty or mismatched records.

For `C = battle+A924D7C`, the original pointer formula is:

`C + bank*6E04 + entry*6E - 6A`

This is an address calculation, not a skill formula or ownership determination.
The helper validates record boundaries, identities, nonzero payload, and bank
counts; provenance remains main's responsibility.

## Original Publication and Writer

`publish_catalog_pointer()` executes `687EB..68804` with ECX explicitly staged
as battle owner and EBP as actor root. `687EB` adds `A924D7C`; `687FE` publishes
ECX to `root+4504 = source+4474`. The contiguous slice also writes zero to
`root+A8` at `687F1` and shifts temporary EAX at `687FB`. The preceding manager
read at `687DB` is not executed or claimed. CPU context is restored afterward.

Rows are the binding's existing `source+D8+i*3EC`, with source=`root+90` and
row count at `source+D4`. The tests create these rows with the unchanged
`NativeBattleCharacterBinding` original reset and S2C30 packet-name branch.
Integration must retain main's existing rows and must not reset them here.

| Native instruction | Effect |
| --- | --- |
| `AA692..AA699` | Compare unsigned packet key with row WORD key |
| `AA69F..AA6A6` | Skip a matching row whose learned count is at least 100 |
| `AA6F5..AA70A` | Read existing pointers at row+258; compare record bank and entry |
| `AA76E` | Clear one byte at row+1F1+old_count |
| `AA780` | Read catalog pointer from source+4474 |
| `AA7A8` | Store computed pointer at row+258+4*old_count |
| `AA7B9` | Increment byte count at row+1F0 |
| `AA7BF` | First refresh call, never executed here |

The native pointer store does not itself dereference a newly appended catalog
record. Qualification of that record is host-side validation against same-VM
memory. Subsequent duplicate searches do dereference its identity bytes in
original code. Tests check both kinds of evidence separately.

`write_learned_skill(raw)` returns the binding-style trace with `outcome`,
`row` (or None), and `pointer` (the validated candidate catalog address):

| Outcome | Stop | Scope |
| --- | --- | --- |
| `appended` | `AA7BF` | Exactly flag, pointer, and count committed; refresh pending |
| `duplicate` | `AA72B` | Original duplicate comparison reached; no actor write; diagnostic setup/call not executed |
| `full` | `69FEC` | Original count-100 skip and return; duplicate identity is not inspected |
| `no_matching_row` | `69FEC` | Original zero-count or bounded row search and return |

Duplicate completion is deliberately not claimed: `AA747` would call `2B10`.
Static continuation compares the found index to the count and skips insertion,
but that continuation is not executed by this proof. Full capacity is tested
with both a duplicate and a new candidate. All 100 slots are first populated
by original S2C34 writes using actual nonzero current catalog records.

## Guards and State

The binding pins the full image hash. Every executable interval is compared
against the bytes in the supplied VM, and its runner guards every executed PC.
Disjoint ranges exclude assertions, diagnostic setup, and all refresh code.
Each run has a 30,000-instruction limit and one-second timeout. No call is
stubbed or skipped to fabricate a successful return.

Reads are limited to the actor, catalog, exact four-byte packet, source-pointer
slot, and dedicated scratch stack. Writes are limited to the exact three
append fields or two publication fields, plus scratch stack. Storage spans
must be mapped with appropriate permissions, disjoint, and fit 32-bit addresses.
The catalog is never written by this helper.

Preflight rejects row counts above 16, matching learned counts above 100,
ambiguous matching row keys, malformed packet lengths, bad publication/source
pointers, and invalid existing learned pointers when the native path scans
them. Existing pointers must target aligned populated records in the supplied
catalog, with identities matching those record slots. A full row skips pointer
validation because original code does not read those pointers on that path.
This proves the full-row no-op, not the validity of its preexisting skills.

CPU context, including pending EIP/ESP and flags, is restored on success or
execution failure; hooks are removed. Memory is not transactional: native and
scratch writes remain. Discard or requalify VM memory after an execution guard
failure. Preflight rejection occurs before actor or packet mutation.

## Integration Contract

Main owns the native loader and bootstrap. Original constructor caller
`110C21..110C45` invokes `12D3B0`; the loader's destination is
`manager+A7E0444`, which main must qualify as `battle+A924D7C`. The loader
reads `1B810` payload bytes at `12D425` after validating the four-byte version.
This helper does not duplicate that loader or prove the manager/battle alias.

After main has loaded that catalog in the same VM and established existing
character rows and original packet-source publication:

```python
from tools.strike_lab.current_battle_learned_skills import NativeBattleLearnedSkills

learned = NativeBattleLearnedSkills(character_binding, battle=BATTLE)
publication = learned.publish_catalog_pointer()
trace = learned.write_learned_skill(explicit_four_byte_logical_packet)
```

`character_binding` is main's existing `NativeBattleCharacterBinding`, with
the same VM, root, packet-routing owner, and dedicated scratch buffers. If the
original actor tail already published the qualified pointer, omit publication
to avoid repeating its `root+A8` clear. An appended result retains original
learned state but does not resume or qualify refresh. Main's pending CPU state
is restored. No subsequent skill consumer is authorized by this writer proof.

## Verification

From the server workspace:

```text
python -B -m unittest tests.research.test_current_battle_learned_skills -v
```

The assigned tests cover exact publication/append footprints, actual nonzero
records across all banks, native duplicate reads, 100-slot capacity, sixteen
S2C30 rows, missing/unsigned keys, exact packet length, malformed inputs,
pointer/count bounds, code identity, scratch isolation, and CPU/hook recovery.
Result: **12 tests passed** (bounded unittest run, approximately three seconds).
Only this document and the assigned helper/test files are changed.
