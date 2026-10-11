# Current Category-20 Instance Writer Binding

## Result

A concrete original storage writer is now bound to the ACTMIS serial reader.
The pinned current image's logical opcode `0x3B` handler copies an incoming
20-byte instance into a 24-byte-stride storage slot. For category 20, the
instance word at +8 is therefore supplied by logical record bytes 13..14,
little endian. The copy does not synthesize an ACTMIS serial or validate it.

```text
logical record u16 at +13
  -> 98E2B: UI + 85610 + 24*slot + 8
  -> 9142F: view + 22928 + 8
  -> 90A39 -> 91520 -> 91559 -> B5BE0 argument 6
  -> B9F9A: input instance u16 at +8
```

This is an offline native storage/reader binding with synthetic logical input.
It does not establish the original server's choice of serial, a turn-in
request, requirement enforcement, rewards, or live client acceptance.
The UI copy is tested after earlier selection checks, so this does not prove
that category-20 objects can reach that screen through normal interaction.

## Evidence

Only this binary supplies instruction/data evidence to the new oracle:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

All code/table locations below are RVAs, image base `400000`. Object offsets
are relative to the synthetic native object stated. The tool does not import
retired recovery helpers, read retired corpora, or load ACTMIS rows. It fails
closed on any image hash mismatch. Existing parser/display work is not rerun.

| Location | Original behavior |
| --- | --- |
| `1324 + 4*3B` -> `1258` | Native length routine returns 25. |
| `68B4E..68B61` | Reads opcode byte, bounds it by FD, dispatches via `6B5D4`. |
| `6B5D4 + 4*3B` = `6B6C0` | Pointer to `6A029`. |
| `6A029..6A031` | Advances record pointer one byte, passes payload to `98DD0`; UI is outer object + `A7F2F6C`. |
| `98DD8..98DE5` | Signed payload byte +1 must be in [0,50). |
| `98DEB..98E05` | Slots 38..41 may call `961A0` if `[UI+574C0]+24` equals 1. |
| `98E0A..98E26` | Destination is `UI+85610+24*slot`, source is payload +4, count is five dwords. |
| `98E2B` | `rep movsd` stores all 20 bytes, including instance +8. |
| `9140B..9142F` | Signed word index at UI+855F0 selects the same 24-byte slot; copies five dwords into view+22928. |
| `90A1D..90A39` | Passes view+22928 to `91520`. |
| `91520..91559` | Resolves instance low word with real `59A60`; forwards original instance pointer as B5BE0 argument 6. |
| `B5BE0..B5C09` | Real stack prologue leaves argument 6 at `[esp+11AC]`. |
| `B6424..B6440` | Six-bit category 20 selects requirement branch `B9F8D`. |
| `B9F9A` | Reads original instance word +8, observed as a two-byte memory read. |

Logical record fields proven within this slice:

| Offset | Width | Proven role |
| --- | --- | --- |
| 0 | 1 | Opcode 3B |
| 1 | 1 | Outside storage-copy interpretation; no meaning assigned |
| 2 | 1 | Signed slot index, accepted 0..49 |
| 3..4 | 2 | Not used by the bounded copy slice |
| 5..24 | 20 | Opaque instance copied verbatim |
| 13..14 | 2 | Instance +8; category-20 ACTMIS serial consumer input |

No low-word item ID, quantity, quest ID, or name is inferred from fixture
bytes. The lookup key and definition pointer used by the caller test are
explicitly synthetic. Serial probes include 0 and 65535: reaching the read
does not mean the later ACTMIS bounds check accepts those values.

## Execution Boundaries

Unicorn executes unmodified x86 instructions. The image is read/execute only,
logical input is read-only and ends at an unmapped page, and each slice has a
20,000-instruction limit with a required endpoint. Hooks only observe reads,
writes, and endpoints. No native functions, imports, or allocators are stubbed.

1. Execute the native length routine to its return.
2. Enter opcode reading at `68B4E`; execute dispatch, native slot checks, and
   writer. Stop at `98E2D`, immediately after the copy, before definition lookup
   and later slot/UI bookkeeping. Invalid slots return to `6B517` with balanced
   stack and no slot writes. For slots 38..41 the main fixture sets the widget
   state to zero; a separate test observes the alternative `961A0` boundary.
3. Explicitly stage the selection index; execute `9140B..9142F`. Checks before
   `9140B`, including definition eligibility, are not executed or asserted.
4. Execute `90A11` through the original wrapper and lookup to B5BE0. Execute
   its real prologue through `B5C09`; stop before the first global cache write.
5. Keep the native stack/EBP, provide the instance header in EAX as the input
   to the separate `B6424` category-dispatch slice, and stop at `B9F9E` just
   after the serial read. Title, cache, renderer, ACTMIS row parsing, and
   requirement text assembly are excluded.

These are connected memory-provenance slices, not a single full application
execution. Slot memory begins poisoned, and tests check exact 20-byte writes,
other slots, stride padding, adjacent display canaries, packet immutability,
and unchanged image bytes. All 24 nonempty truncated prefixes fault on an
unmapped read. A 24-byte prefix already copies four dwords before faulting;
this copy is not an atomic packet validator. Transport framing is outside
the experiment, and no server codec is added.

## Reproduction

From `God2-Server`:

```powershell
$env:PYTHONPATH = "$PWD/artifacts/tooling/crypto-oracle-python"
python -B -m tools.strike_lab.current_quest_instance
python -B -m tools.strike_lab.current_quest_instance --json
python -B -m unittest discover -s tests/research -p test_current_quest_instance.py -v
```

The tool writes only stdout. JSON includes the exact synthetic logical record
and instruction-RVA/region/offset/width traces. Packet trace offsets are page
relative; its 25-byte fixture begins at page offset 4071.

Verified 2026-09-19: all eight regression tests passed (50 accepted slots,
four rejected slot-byte values, 24 truncated prefixes, four serial/lookup
combinations, all four conditional-widget slots, pin rejection, opaque copy,
and report checks). Both CLI modes exited successfully; the JSON example has
28 observed memory events and serial 169. No live process or socket was used.

## Next Exact Boundary

The server-side serial-selection rule remains OPEN: which original event
constructs a category-20 instance and chooses logical 3B bytes 13..14.
No C2S request contract follows from this incoming storage write. Normal
category-20 reachability through the checks before `9140B` is also OPEN.
The concrete client handoff for further investigation is the 25-byte logical
3B record into `98DD0`, not the ACTMIS parser or text renderer.

Changes are confined to the new `tools/strike_lab/current_quest_instance.py`,
`tests/research/test_current_quest_instance.py`, and this document. Shared
runtime, CMake, and the main lane's embedded worldactor placement are untouched.

## Full ACTMIS Packet-To-Display Composition (2026-09-21)

The new regression composes both existing native slices for all169 current
ACTMIS records. For each serial, a synthetic logical3B record passes original
dispatch/storage, selected-slot copy and tooltip serial read. Its exact20-byte
display instance, not a reconstructed serial-only input, then passes the
original category20 requirement consumer. Assertions compare the label bytes,
ordered lookup IDs and quantities against the original parsed source record.
Slots rotate through all50 positions; record key1234 and lookup names remain
explicit synthetic fixtures. Instance bytes are unchanged by the consumer.

`NativeRequirements.consume_instance` requires exactly20 bytes and category20;
the existing serial/header convenience interface delegates to it. Wrong sizes
and categories fail closed.19 instance/requirements tests and5 import tests
pass. The initial combined dotted test invocation could not import a sibling
test helper; import tests pass under their existing discovery invocation.

This establishes composition across the documented slice boundaries, not one
uninterrupted native receive/UI execution. No server packet is captured here,
no item catalog name join or inventory ownership is established, and no new
quest award/consumption rule is installed. Existing imported ACTMIS records
retain DISPLAY_ONLY authority.

Targeted original disassembly identifies the unresolved UI entry more closely:
RVA91390 rejects negative selected slots and missing event bit20 before the
9140B copy. Control word17 additionally compares view+22900 to the object
pointed to by UI+8688C, calls99A60, then uses native59A60 to resolve the stored
low-word definition. Null definitions branch91494 instead of copying. These
are disassembly observations, not new live or emulator acceptance.99A60 reaches
widget functions106850/1067A0, so earlier widget state cannot be skipped when
qualifying actual input reachability. This is the next concrete native gate;
server serial selection and authoritative quest lifecycle remain open.

## Original Selection Gate Execution (2026-09-21)

`selection_gate` now starts at91390 and runs original checks and helper calls
through the20-byte display copy at9142F, stopping91431. All50 stored slots pass
with control17, event bit20, matching context and a nonnull native59A60 lookup.
The169-record composed test also traverses this gate before its bounded tooltip
and requirement text slices, preserving the actual selected instance bytes.

Fixtures are explicit: widget index0 is inactive at+818; its renderer is staged
with resource indexFFFF, so original1EE10 returns via1EEF6.99A60,106850,1067A0
and1EE10 execute their original instructions; there are no helper stubs, code
patches or suppressed faults. This is not active rendering or live UI input.

Negative selected slot, absent event bit20 and wrong control return without
display writes (stack restored by12 bytes including return and arguments).
Context mismatch stops at914DC before the message call; missing definition
stops91494 before its cleanup branch. Neither path is claimed fully executed.
Every positive case asserts exact copy writes and unchanged pinned image.
Both suites now pass21 tests. The prior disassembly-only gates are therefore
qualified for these staged inputs, not for the current live widget state.
Live packet delivery, active UI interaction and original server selection/
quest consumption and rewards still require independent acceptance.

## Native MIS Definitions At Selection Entry

The source-category column must not be equated with the six-bit instance
category. Current gamedata has21 source rows with category code20, all EQC
definitions; its987 MIS rows use other source category codes. This is a
source observation, not a recovered conversion formula.

The new regression parses each of the987 MIS rows through original59420 and
the existing native metadata oracle, retaining all0x18C definition bytes.
Each native key and definition is then supplied to the selection-gate VM;
original59A60 resolves that real definition before the display copy. Definition
storage is separate from staged widget/context memory and must remain unchanged.
This removes the synthetic nonnull definition body from that test, but not
the staged widget state or the synthetic instance category20/serial1. It does
not assert that every MIS item is an ACTMIS object or assign any quest to an
item. No new gameplay mapping is persisted or activated.

Verification: instance and requirement suites pass22 tests in81.994 seconds,
including all987 MIS definitions and the169 ACTMIS packet-to-display cases.
This run is offline only; live transport/active-widget acceptance remains open.

## C++ Requirement Reference Projection

RecoveredInstanceUpdate::Record now exposes display_requirement_reference()
only when the native six-bit instance category equals20. It projects logical
bytes13..14 as an ACTMIS serial, retaining zero and out-of-catalog values for
source-qualified validation by the caller. This is not a Mission_data ID,
acceptance state, inventory-consumption policy or reward authorization. Other
categories return no reference; the raw lossless record remains unchanged.
Runtime emission and mutation flags remain false.

The standalone C++ test has a separate --requirements inspection mode while
preserving the existing --batch output. Differential checks compare all169
source serials against original B9F9A reads, then cover all64 categories, four
high-bit combinations and serial boundaries0/1/169/170/65535. Guarded parser
and lossless roundtrip tests also exercise the new accessor.

Verification: all9 current_instance_update tests pass in87.878 seconds,
including standalone C++20 compilation with warnings treated as errors.
