# Current pet2 D6 revert request — 2026-09-30

## Delivered boundary

`RecoveredPet2Revert` adds the exact native C2S D6 grammar. The separate
`RecoveredPet2RevertGate` checks authenticated ownership, the completed world
lease, battle reservations, saved inventory and an owned FB generation pet.
Every gate result is an explicit denial; the terminal result is
`effect_unqualified`. No item is consumed, pet changed, previous state invented
or S2C success generated. This is transport/admission coverage, **not completed
revert gameplay**. Application/parser integration is present in the main task's candidate.

Current C2S28 selection and E3/FB restore remain untouched by this lane. The
separate current C2S24 reserve reorder work is not part of this result.

## Independent current sources

- Mapped current client image:
  `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Current `../God2/Data2/Patch/Comm/gamedata.csvZ`, raw SHA256
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`,
  decoded SHA256
  `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Current native instruction runner `current_stat_packet_return_path.py`:
  unchanged `A5682 -> A57FF -> 132E0 -> A5807 RET8`, with existing pinned
  instruction boundaries. No live process, desktop, client modification or
  retired corpus was used.

All addresses are hexadecimal RVAs, with image base `400000`. The producer
queues exactly four logical bytes: `D6 item_slot pet_slot option`. All three
fields are unmodified unsigned wire bytes; no arithmetic rounding is involved.

| Native control | Option | Required inventory key | Current MIS02 identity |
| --- | --- | --- | --- |
| `17` | 4 | `4010` / 16400 | 戰寵型態還原石 |
| `18` | 1 | `400F` / 16399 | 戰寵天賦還原石 |
| `19` | 2 | `400F` / 16399 | 戰寵天賦還原石 |
| `1A` | 3 | `400F` / 16399 | 戰寵天賦還原石 |

`A5741..A5783` and `A578B..A57ED` search 30 inventory records of stride24.
The record count byte must be signed-positive, and the item key is its DWORD+4
masked to 16 bits. The matched index becomes payload byte0; panel+D8 becomes
payload byte1; the control chooses byte2. The current item descriptions say
these stones restore the last changed talent/category to its preceding value.
Those descriptions identify the operation's intent; they establish neither
the previous values nor consumption counts, validation/cost rules or a reply.
The three talent options are retained by number; specific talent names are not
guessed.

On inventory miss, the original code still sends D6. The unwritten first
payload byte retains event flags `20` or `60`. This is why structural decode
preserves all bytes, while `has_qualified_operands` independently requires
item slots0..29, pet slots42..44 and options1..4. Invalid bytes are never clamped
to a legitimate item or pet slot. D6 must not be parsed using the S2C D6 length.

## Admission and storage

The gate reuses existing owner checks in `owned_pending_battle`,
`load_inventory_slot` and `load_pet2_slots`. Its decisions distinguish a missing
item, incorrect item, wrong source hash, absent/wrong-generation pet, pending
battle, invalid operands and unqualified effect. The item key is independently
derived from the option rather than accepted from a client claim.

No migration or CUSTOM gameplay rule is introduced. Existing schema rows and
their provenance remain authoritative for ownership only. Present FB bytes do
not authorize fabricating an earlier category or talent; item prose does not
authorize a consumption transaction. Repository faults still propagate to the
application's existing error handling.

The main runtime route should accept one D6 with idle ticks only, reject mixed
mutations before any callback, log `OWNED_PET2_REVERT_DENIED` with the gate's
reason and original operands, and retain the connection without emitting a
success record. Recognizing a denied request must not be reported as completed
revert gameplay or as current-client acceptance.

## Verification

- `python -B -m unittest tests.research.test_current_stat_packet_return_path -v`:
  existing 4 tests passed.
- `python -B -m unittest tests.research.test_native_pet2_revert_contract -v`:
  3 tests passed in0.758s. This executes36 exact native producer combinations
  (item slots0/7/29, all3 pet slots, all4 options),8 native inventory-miss cases,
  and verifies both current item rows against the pinned raw/decoded source.
  The test decodes only the selected original rows; unrelated byte sequences in
  the larger current file are not silently replaced to force whole-file CP950.
- `tests/companion/test_pet2_revert.cpp`: independent MSVC x64 C++20 `/W4`
  build and execution passed without warnings. Covers768 raw-byte roundtrips,
  393216 operand combinations, truncation/length/opcode failures, current
  inventory-key mapping, ownership, readiness, battle reservation, missing and
  incorrect inventory/source/pet cases, all4 valid-operation denials, unchanged
  full FB bytes/revision, and no stone consumption. Each gate call compares
  `sqlite3_total_changes` before/after. All state is an in-memory synthetic DB.
- Independent executable:
  `artifacts/research/native-pet2-revert-20260930/build/test-pet2-revert.exe`.
  The new gate/codec/test were compiled from current source and linked to the
  existing `build-town-visibility/Release/god2_core.lib` and its SQLite/Lua/
  spdlog libraries. A complete main-task candidate build remains separate.

## Remaining acceptance

Actual current-client D6 behavior is untested in this lane. The initial safe
route gate must demonstrate a native panel request reaching this explicit
denial while preserving its connection, saved snapshot and item count. Before
enabling successful reversion, recover the authoritative previous talent/
category history, exact option-to-history association, eligibility and item
consumption rules, full response sequence and its state requirements. The
native neighboring update path `A5A40` and preview/tooltip controls remain
concrete next trace locations; no C2S D6 to S2C FB causal pairing is asserted.
Then implement an atomic history/item/pet transaction and verify successful
reversion with the unchanged current original client against our own server.

Effect activation and actual-client acceptance for this D6 operation remain
0%; no overall playability percentage is derived from codec/test counts.

## Candidate TCP follow-up and independent review

The rebuilt candidate was copied to
`artifacts/research/native-pet2-revert-20260930/build/god2-server-d6-candidate.exe`
before launch, SHA256
`8e24ec1f21c7197b9387d31d7380b9defa9cb2d7203cbfb1ac2f03d7c24f5b1a`.
`tests/research/test_pet2_revert_server.py` passes3/3 in10.255s against that
binary over real loopback login/character sockets. Each test runs a bounded
private server with a cloned synthetic fixture; source DB and its SHA256 stay
unchanged. No original client/UI process or formal service was started/stopped.

Covered TCP cases:

- All4 qualified options deny with `effect_unqualified`, retain an open
  connection and send no S2C reply; fragmented TCP input and idle ticks in the
  same logical frame are included.
- Native no-match raw slots20/60, wrong pet slot/option, missing stone, wrong
  stone key/source, and empty pet44 receive their explicit gate decisions.
- D6 mixed with24 reserve reorder,28 selection,67 deity selection,21 allocation
  and a second D6 is rejected before mutation, in both orders (10 batches).
- A D6 before the first owned projection denies as `not_world_ready`; the
  subsequent projection and valid D6 still work. A truncated3-byte logical D6
  closes the malformed connection without mutating storage.
- Each denial compares all rows in9 owned/related tables, including positions,
  inventory, complete companion snapshots, revisions, resources and battle
  tables; no row changes. A subsequent framed6D control confirms the socket
  remains usable. All logs explicitly say `no_state_change no_success_reply`.

The review caught a concrete Application construction error before this run:
`database.recovered_characters()` exposes the base interface, while the gate
requires SQLite inventory/pending-battle methods. Main-task wiring now passes
its existing `supply_repository` concrete reference. The gate itself was not
weakened. The private fixture DB basename was corrected to
`town-diagnostic-accounts.db` to satisfy the existing diagnostic isolation gate.

Independent review of the separate C2S24 reserve implementation found no
additional blocking defect: world-ready/mixed-batch admission precedes the
callback; its transaction rechecks owner, complete snapshots and revisions,
rejects pending battles, reads back all3 cells, and rolls back if either write
or precommit frame generation fails. Generation-specific clear/append ordering
is preserved and the largest two-FB reply is216 logical bytes, below2560.
This review is not counted as original-client acceptance.
