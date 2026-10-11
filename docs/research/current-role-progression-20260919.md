# Current Role Progression: Bounded Native Consumer Proof

## Result

New primary proof: **S2C2C -> RVA E6600 receives and stores stat modifiers
and additional stat state.** The first four values are stored as raw WORDs,
then consumed as signed modifiers alongside independently stored base stats.
They are not computed from level or EXP in this consumer. Native execution
checks exact reads, widths, destinations, untouched actor bytes, and signed
formatting operands. This goes beyond the earlier S2C22/2B prefix and E6C90
display audit.

The next consumers also establish client-side health mutation and resolve the
actual `GodLevel` source schema through its loader and text reader. None supplies
original role XP thresholds, level transitions, or per-level stat growth.
Those formulas remain **OPEN**, represented as null, with no fitted or
placeholder formula and no runtime integration.

Only three new owned files were changed: `current_role_progression.py`,
`test_current_role_progression.py`, and this report. Shared runtime, CMake,
and previous recovery scripts were not edited. No retired sources were read.

## Authority and Bounds

All addresses below are hexadecimal RVAs in the mapped image, equal to file
offsets; add `400000` for a virtual address. The image is:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Only two current client data files are read by the tool:

| Current client source | SHA-256 |
| --- | --- |
| `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| `Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |

Every execution starts with hash verification, uses unmodified original
instructions in a read/execute image mapping, and has a maximum of 2,000
instructions and one second. Code hooks enforce explicit instruction ranges;
the final EIP must match the requested endpoint. Memory hooks record reads
and writes. No native callee is replaced or stubbed. UI formatting calls are
excluded by stopping before them. Tests use synthetic operands to establish
client behavior, not purported original server samples or live verification.

## New Stat-State Consumer

The dispatch table entry at `6B5D4 + 4*2C` points to `69EDE`, which advances
past the opcode and calls `E6600` at `69EE6`. The length table entry at
`1324 + 4*2C` points to `1228`, returning 61 logical bytes including opcode.
The tested prefix ends at `E66F8`, before the refresh call to `E6710`.

Body offsets below are decimal. Actor offsets are hexadecimal. The actor is
loaded through `[UI+86888]`. No destination in this table is incremented.

| Body bytes | Actor bytes | Original operation |
| --- | --- | --- |
| 0, 4, 8, 12; 2 bytes each | `88,8A,8C,8E` | Copy raw WORDs |
| 16, 20, 24, 28, 32; 4 bytes each | `A4,A8,AC,B0,B4` | Copy DWORDs |
| 36, 40; 2 bytes each | `B8,BA` | Copy WORDs |
| 44, 48, 52, 56; 4 bytes each | `98,94,A0,9C` | Copy DWORDs |

The four-byte source spacing of the first four entries does **not** imply
four-byte consumption: bytes 2-3, 6-7, 10-11, and 14-15 are not read here.
Likewise bytes 38-39 and 42-43 are not read. Tests compare the complete actor
region against expected byte patches and check the exact packet read set.
The level byte `+26`, EXP display WORD `+58`, base stats `+78..84`, and
HP/MP maxima `+60/+68` remain unchanged by this prefix.

At `E6E61`, the first modifier `actor+88` is tested as signed. The paths
load the base DWORD at `+78` unchanged and pass it to one formatting call.
Separate calls receive a sign-extended modifier with `%d` or `+%d`; zero
uses an empty string. Executed probes cover -32768, -1, 0, 1, and 32767.
The other three adjacent display branches are statically visible at
`E6F19`, `E6FCE`, and `E708C`; only the first branch is executed here.
This proves independent base/modifier display, not automatic level growth.
The game meanings of the additional DWORDs are not assigned by this report.

## Following Received Values

S2C2B's dispatcher calls `E6390` and then **`AA3F0`**, the previously
untraced consumer. With a nonnull `[actor+D0]`, that second consumer copies:

| Body offset / width | Destination relative to `[actor+D0]` |
| --- | --- |
| 4 / 4 | `+2C` |
| 12 / 2 | `+34` |
| 18 / 2 | `+28` |

It passes the last WORD to `AA480`. That display path selects ProgramMsg 165,
whose actual current text is `%6.2f` followed by a fullwidth percent sign.
The first consumer separately uses body offsets 0/4, 8/4, and 16/2 for role
`+5C`, `+64`, and `+58`. Thus the DWORD at body+4 is not a high half of a
64-bit role XP value in these consumers. Body bytes 14-15 are unused in the
two inspected store prefixes. The null companion branch reads no body fields.

The next role consumer `AC070`, reached through `E63F0`, **mutates** current
HP/MP: it unsigned-clamps actor `+5C` to `+60` and `+64` to `+68`, provided
both maxima are nonzero and the signed UI WORD at `+232E50` is nonnegative.
Tests chain the original E6390 stores into that consumer and cover values
above, below, equal to, and across the signed boundary of the maxima. Guard
tests prove no state mutation when either maximum is zero or the panel is
inactive. Native ProgramMsg reads 163 and 164 bind the pairs to health and
magic displays, respectively. This is a client clamp, not a growth formula.

S2C24 supplies another concrete state source: `69F4D` passes the body at
logical packet+1 and mode 0 into `E71E0`. Its logical length is 17. Body DWORDs
0,4,8,12 overwrite actor `+5C,+64,+60,+68`. Before those stores, a role HP
decrease also reduces companion `+2C` by that decrease, floored at zero.
The original unsigned comparisons, equal/decreased/increased cases, floor,
and four role stores execute through `E72A6`. Neither level nor EXP changes.
This is an actual derived health-state value; maxima remain packet inputs.
S2C9F calls the same consumer after `1037D0`; that preceding callee is not
executed here, so this report does not equate the complete 9F and 24 paths.

The role EXP bar path `AC2C0` reads unsigned `actor+58`, multiplies by the
pinned float32 at `171204`, stores float32, reloads it, and calls `149630`.
The test executes the original helper: it saves the x87 control word, sets
truncate mode, performs `FISTP` to a signed 64-bit temporary, restores the
control word, and returns the low DWORD in EAX. The caller pushes this to
UI control 4. Only actor `+58` is read; no actor bytes are written. This
closes the integer-conversion callee previously left unexecuted, but does
not convert absolute EXP into a level or reveal a threshold.

## Actual Source Category Schema

This is a loader/reader proof, not another section-name inventory.
`GodLevel` at native `18A064` is matched at `5668C`, dispatching at `566CD`
to loader `5A880`. The native loader:

1. Stores the declared count as a byte at bank `+D2AC8`.
2. Requests field 1 through `51B30`, whose `51BA0` reader selects that field
   and passes its decimal text to the native `%d` conversion.
3. Decrements positive IDs and uses a 94-byte slot stride at `+D2ACA`.
4. Copies field 0 as a NUL-terminated string through `51AE0/51B60`.

The current four source records at decoded offsets 2483461, 2483471,
2483481, and 2483491 contain IDs 1..4, which populate slots 0..3. Tests
use their exact raw label bytes, verify the numeric-field pointer and `%d`
operand before the CRT call, then explicitly resume after numeric parsing
with the exact source ID. Tokenization, file IO, and `sscanf` are excluded;
the decimal conversion is not claimed as executed. The actual native text
getter, slot arithmetic, and copies execute without substitutions.

Reader `AA360` takes an unsigned byte operand, accesses that slot, and
copies the label to `[actor+D0]+13` before displaying it. This resolves the
table as companion category text, not a role-level XP requirement table.
The original reader compares ordinal **<= signed count byte**: with count
4, ordinal 4 is admitted even though source IDs populated only 0..3.
A canary test preserves this observed behavior; it does not claim the real
caller supplies ordinal 4 or invent an extra category. Ordinal 5 skips copying.

## Open Rules and Verification

Exact single-level/cumulative XP thresholds, level transition, level cap,
HP/MP growth, base attribute growth, and the attribute-point budget remain
OPEN. The already known S2C22 input supplies the level byte and base/max
state; the newly traced paths do not identify their upstream server producer.
There is no justified threshold table or growth formula to install.

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.current_role_progression --client-root C:/Users/risei/Desktop/God2/God2
python -B -m unittest discover -s tests/research -p test_current_role_progression.py -v
```

The first command emits deterministic ASCII JSON with pinned spans, source
records, packet metadata, operand mappings, and explicit OPEN rules. It writes
no artifact or source file. **14 focused tests pass.** The existing local
Unicorn installation is used; no shared build or dependency change is needed.
The separate integration build and 34 selected CTest entries were run by
the integrating agent, which also independently reran all 14 focused tests.
