# Current Battle Character Binding, 2026-09-20

## Result

The original producer is the current player actor's state block at `root+90`,
not ProgramMsg and not the preselection 1F body. There is an executable,
same-VM proof from original reset and packet writers through the actual
`1116A4 -> 11BB80` call, stopping at `11BC2A`, immediately after the two
source-byte reads. All sixteen row pointers are checked.

Main's distinct `CHARACTER_ROOT=08520000` is supported. The source passed as
argument 7 is `08520090`. This result does not qualify the remainder of
11BB80 or the later skill-list readers. No third-window code is executed.

## Evidence Identity

Only the current mapped image is opened by the helper and tests:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Image base `00400000`; addresses below are hexadecimal RVAs, equal to file
offsets. The helper verifies the complete file hash and compares every executed
range against bytes mapped in the supplied VM before running it. It uses strict
instruction ranges, write bounds, a one-second timeout and 30,000-instruction
limit per stage. No imports or game callees are replaced.

The current-character-context document/test code was read for its current 1F
boundary only. Its historical references were not followed. No archives,
historical fixtures, UI, network, runtime, database, CMake or child agents were
used. Every packet in this regression is explicitly synthetic.

## Original Writers

| Stage | Current original behavior |
| --- | --- |
| `68120..6814A` | Takes actor root as argument. `68135` writes count zero to root+164; `6813B` writes FF to root+15F; `68142` clears root+160; `68148` clears exactly 3EC0 bytes at root+168. Stops before the UI reset call. |
| `81C81..81C87` | Computes EDI = root+90 from EBX=root. |
| `81D0A -> E7C80..E7CB1` | Passes that EDI to the original publication writer; `E7CAB` stores it at UI+86888. The intermediate UI operations between these explicit stages are not executed or claimed. |
| `69F85 -> AA040..AA1B5` / S2C30 | Appends a row at source+D8+count*3EC. Writes WORD key at `AA08B`; copies name on the qualified packet-name branch; increments source+D4 at `AA184`. A negative packet key also sets source+D0 to the new row and source+CF to count-1 at `AA1AD`. Stops before refresh. |
| `69FA9 -> AA200..AA2AF` / S2C31 | Searches existing rows by signed-byte key, writes row scalars at +02, +28, +38..+3F, +44..+57 and +5A. Stops before the selection/paging/refresh suffix. |
| `69EF0 -> E6B40..E6BD4` / S2C22 | Writes source+26,+58,+60,+68,+78,+7C,+80,+84,+90. Does not produce source+CF, source+D4, or any row. Stops before refresh. |

Reset zeros are actual original writes. They are not default character stats
or test-supplied zero counts. The proof appends sixteen explicit nonzero keys
100..115, selects the final row with negative S2C30 key -115, and applies
nonzero S2C31 scalars to every row before the battle consumer runs. A nonzero
S2C22 probe supplies the tested role scalar fields. All unproduced actor bytes
remain the explicit caller snapshot, including poison used to mark unknowns.

The bounded S2C30 helper supports only the packet-name branch: absolute signed
key 100..127, a NUL within the 16-byte packet name, and trailing flag !=1.
These are synthetic branch probes, not claims of owned characters, catalog
identities, or canonical server packets. Other keys need the original 59A60
name lookup through UI+CFF70. Flag 1 has a separate duplicate/skill-count
path. Neither is silently substituted with empty resources or guessed names.

## Battle Read Proof

Let `R` be root, `S=R+90`, `B` be battle, and `C=B+A9DC198` be the selector.

| Original instruction | Proven value |
| --- | --- |
| `111323..111326` | B+14 = DWORD[descriptor+10] = R |
| `111667..111677` | ECX = DWORD[B+14]+90 = S |
| `111685`, `1116A4` | Push S as argument 7 and execute the actual call |
| `11BB9A..11BBAA` | Read argument 7 and compute first row S+D8 |
| `11BBEA`, `11BC01` | Sixteen stores to C+2D4+i*2D0, each equal to S+D8+i*3EC = R+168+i*3EC |
| `11BC18`, `11BC1E` | Read byte S+CF = R+15F and store C+4 |
| `11BC21`, `11BC27` | Read byte S+D4 = R+164 and store C+5 |

Observed source reads are exactly `(11BC18,R+15F,1)` and
`(11BC21,R+164,1)`. The prefix constructs row pointers but does not dereference
row contents. The actor snapshot remains identical across the consumer stage.
The test observes selected index 15 and count 16, and every original pointer
store. This is not a zero-count loop bypass.

Argument 8 is WORD-only: `11166A` changes AX, leaving the upper EAX bits opaque;
`11BB80` reads the WORD. The probe starts EAX=BEEF9876 and the native window
WORD=1234, observes pushed BEEF1234 and selector WORD 1234. No full-DWORD handle
equality is asserted. All caller registers, including its pending EIP and ESP,
are restored after each helper stage.

Argument 3 is PANELS (`B+A9EA59C`), the ESI value produced by `11162D` in
main. The prefix helper stages that exact value, separately from its `ui`
packet-routing owner. It does not execute the earlier third-window work.
The prefix through 11BC2A has not read argument 3 yet; the regression checks
its pushed value without claiming its later dereferences are qualified.

## Reusable Helper

`tools/strike_lab/current_battle_character_binding.py` exposes
`NativeBattleCharacterBinding(vm, root=..., ui=..., sp=..., packet=...)`.
It operates directly on the existing VM. UI here denotes the original
packet-writer owner's memory; no UI execution occurs.

The caller owns mappings for a dedicated scratch stack, a 29-byte packet
buffer, UI+86874..UI+8688B, and any battle/descriptor storage it uses. Keep
scratch separate from the pending main stack. `prepare_new_root(snapshot)`
requires exactly 469C explicit bytes and refuses any existing mapping overlap.
For an already qualified actor in the same VM, omit that method. No snapshot
is copied from a second VM.

Explicit preparation order for the bounded synthetic proof:

1. Prepare the new root from the explicit opaque snapshot.
2. Run `reset_rows()` and `bind_packet_source()`.
3. Apply explicit S2C30 records with `append_named_row(raw)`, S2C31 records
   with `write_row_scalars(raw)`, and S2C22 with `write_role_scalars(raw)`.
4. Main's descriptor+10 already points at CHARACTER_ROOT. For independent
   callers only, `bind_descriptor(descriptor)` writes that one fixture slot;
   `publish_battle_source(descriptor=..., battle=...)` runs the original
   `111323..111329` writer. A completed bootstrap has already done this.
5. `prove_consumer_prefix(battle=...)` runs the original argument construction
   and call, stopping at 11BC2A. It restores CPU context, while retaining native
   selector writes. Main may instead resume its own pending call to the same
   boundary and observe those writes itself.

Do not reset an already populated actor as an integration shortcut. The helper
does not auto-reset or auto-fill records. Its preparation methods are explicit
stages, not a claim that the skipped caller/UI work has been executed.

## Exact Remaining Inputs

The prefix proof does not establish real character ownership, stats, selected
row, or learned skills. Real inputs must be supplied as qualified current
packets or an explicitly qualified same-VM actor state. 1F and ProgramMsg
cannot substitute for those inputs.

Current-image disassembly identifies the separate learned-skill producer:
S2C34 dispatch `69FDF..69FEC -> AA660`. It matches a WORD row key against the
packet's unsigned key byte, uses row+1F0 as its existing learned-skill count,
searches existing pointers at row+258, and writes a new pointer at `AA7A8`
before incrementing the count at `AA7B9`. The pointer is computed from
source+4474 = root+4504, packet byte 2 (bank), and packet byte 3 (entry):

`catalog_base + bank*6E04 + entry*6E - 6A`

Those byte positions include the opcode. The original actor tail writes
root+4504 at `687FE` after adding A924D7C to its owner pointer at `687EB`.
This ties the source's pointer-bearing rows to a same-VM catalog allocation.
It is static evidence here; S2C34 is not executed by this sidecar and its packet
length, full prerequisites, and catalog population are not qualified here.

Consequently, a later skill-list proof needs the current original catalog
producer in the same VM, actual nonzero S2C34 records and existing learned
state, and qualification of subsequent flags/list selection consumers. The
native reset's empty skill arrays are not offered as evidence that a character
has no skills. Do not continue later skill consumers on the basis of this
prefix result alone. Low-key S2C30 also needs the original name metadata
resource mentioned above.

## Verification

From `C:/Users/risei/Desktop/God2/God2-Server`:

```text
python -B -m unittest tests.research.test_current_battle_character_binding -v
```

Eight tests cover exact native reset writes, original source publication,
S2C22's excluded footprint, sixteen nonzero row insertions/status updates,
actual battle call and memory-read trace, WORD-only argument 8, unknown-input
rejection, current dispatch/length entries, and modified-code rejection.
Result: **8 tests passed**, including the corrected nine-byte name assertion.
Only the assigned helper, test, and this document were created. Shared modules
and main's bootstrap tests were not edited or run.
