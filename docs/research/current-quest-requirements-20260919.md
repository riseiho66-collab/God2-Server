# Current ACTMIS Parser and Requirement Consumer

## Result

The original current client establishes this relationship:

```text
category = (input_instance.dword_at_0 >> 16) & 63
category 20 -> input_instance.word_at_8 = ACTMIS serial
ACTMIS serial -> resource.ACTMIS[serial - 1], stride 20 bytes
```

This is a requirement-text consumer, not a Mission_data journal join or a
server quest implementation. The low 16 bits of the instance header do not
select the ACTMIS row. No main/side/reward classification is inferred from text.

Only the pinned original image and current `Data2/Patch/Comm/ActMis.csvZ`
are evidence inputs. No retired implementation was used as authority or read
for this proof. No runtime/shared files, build configuration, UI, client
process, inventory behavior, or journal tests are involved.

## Evidence Pins

| Input | SHA-256 |
| --- | --- |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `ActMis.csvZ` | `e1e35ee689d12ef265be8620b21f856709976896a46edeb9f31c15622041accf` |
| Decoded ACTMIS | `10f76969d60d3a46fdd937510f1b480bc12a07b4a07b7f98774fa6df9df97548` |

All addresses below are RVAs, with image base `0x400000`.

## Parser Proof

`56434..56475` compares the section name against `ACTMIS` at `18A0DC`
and calls `58780`. The section-dispatch test executes that comparison and
observes the real loader entry and count argument, 169.

The row tokenizer `51BE0` consumes the exact decoded original CRLF row.
Its ten field buffers have stride `0x17C`, starting at resource `+0x78`.
`51B30` / `51B50` call the actual numeric parser `51BA0`, including its
original CRT conversion code. The oracle does not supply parsed numbers
as replacement function results.

`587C4..587E5` parses column 1, subtracts one, and rejects signed indices
outside `[0, section_count)`. Row order is not the key. `58817..58820`
uses that index with stride 20; `588D4..588E0` maintains a signed-word
high-water count at resource `+B2C58`, with the table pointer at `+B2C5C`.

| Record offset | Native write | Source |
| --- | --- | --- |
| `+0`, dword | `58820` | Pointer to copied column 2 label bytes |
| `+4..7`, bytes | `5888F` | Quantities, columns 4/6/8/10; low 8 bits |
| `+8..15`, words | `58873` | Lookup keys, columns 3/5/7/9; low 16 bits |
| `+16`, byte | `588CC` | Count of pairs whose narrowed key AND quantity are nonzero |
| `+17..19` | No write in row slice | Zeroed fixture allocation padding |

The original 169 rows each have one populated leading pair. For example,
serial 1 (physical line 5) yields key 5156, quantity 5; serial 169 (line 173)
yields key 15508, quantity 6. Raw fields, line endings, preamble and source
hashes are retained in the optional JSON report, allowing exact reconstruction
of the decoded source.

## New Consumer

`B6424..B6440` dispatches the six-bit category using the original tables
at `BC1D0` and `BC188`: category 20 maps to slot 11, target `B9F8D`.
At that target, the input instance pointer is `[esp+11AC]` and the resource
pointer is `[ebp+CFF70]`.

`B9F9A` reads the instance word at `+8`. `B9F9E..B9FB7` rejects zero and
serials exceeding the signed resource count. `B9FBD..B9FC6` selects the
20-byte ACTMIS record. `B9FD2..B9FFE` copies its label into the local text
buffer `[esp+3BC]` before checking the pair count.

`BA000` reads the byte count. `BA01C` reads each word key, and the real
`59A60` lookup resolves it through resource `+B2D40 + key*4`, returning zero
for keys `>= 0x7F58`. A null definition skips that pair's formatting.
For a non-null definition, `BA032` zero-extends the quantity byte, and
`BA045` calls the original formatter with definition `+8` as the name and
the format at `19288C`: `\n%s x %d`. The result is appended to the label.
Execution stops at `BBBCE`, after this requirement branch joins subsequent
description processing. No renderer or other description branch is run.

The consumer iterates the first N slots, where N is the stored pair count.
It does not compact populated slots or scan all four for nonzero pairs.
The adversarial row `[(0,0),(5156,5),(5157,7),(0,0)]` gets count 2 but reads
keys `[0,5156]`; the third pair is not visited. This is a native read behavior,
not a proposed server rule. Width probes also prove that `65536` becomes
key zero and `256` becomes quantity zero before the count is computed.

## Reproduction and Boundaries

From `God2-Server`, using the existing offline Unicorn dependency:

```powershell
$env:PYTHONPATH = "$PWD\artifacts\tooling\crypto-oracle-python"
python -B -m tools.strike_lab.current_quest_requirements
python -B -m unittest discover -s tests/research -p test_current_quest_requirements.py -v
python -B -m tools.strike_lab.current_quest_requirements --json
```

The tool emits to stdout and writes no files. It verifies all 169 original
rows through native parsing and consumer reads. The nine tests additionally
cover section dispatch, reordered keys, rejected keys, signed count behavior,
field narrowing, sparse slots, missing lookup entries, zero pairs, and
unchanged source records/input/image. Memory-read hooks record instruction
RVA, record offset and width; hooks observe execution without changing it.

The image is mapped read/execute only. Execution is bounded to 200,000
instructions per slice and must reach a declared endpoint. No game-function
stubs, patched code, simulated rewards or OS import replacements are used.

The file reader and allocators are outside the slice: table memory is
preallocated; row execution starts at `587C4` after tokenization, stops before
the allocator call at `58807`, and resumes at `5880C` with allocated label
storage as an explicit input. The current row's native key and stack state
are retained across this boundary. This does not test file loading or heap
allocation success.

Consumer instances are staged inputs, not captured server packets. Lookup
entries point either to null or to the explicitly synthetic name
`lookup-fixture`. The actual lookup and formatter execute; the name fixture
isolates the key/quantity contract. No join to an item catalog or item
ownership assertion is claimed. Exact original ACTMIS labels and numbers
remain the source data under test.

## Exact Next Rule Gap: OPEN

The missing producer contract is who assigns the ACTMIS serial to the
category-20 input instance's word at `+8`, and when a server validates and
consumes the selected quantities during turn-in. Trace that writer/request
contract next, using `B9F9A` as the concrete reader anchor. This slice only
assembles text; it does not compare owned quantities, accept a quest, or
authorize completion. Requirement enforcement and reward selection/issuance
remain **OPEN**. An equality with a Mission_data ID or a daily-table key is
not established by this consumer.

Update2026-09-21: current_quest_instance qualifies the logical3B storage writer
and bounded UI copy to this instance. The composed169-record regression now
passes exact native-copied instance bytes into this consumer and checks all
source labels, ordered item IDs and quantities. See the current quest instance
report for slice boundaries and the remaining91390 UI gate. The unknown is
original server serial selection and actual turn-in policy, not the already
identified logical3B field-to-instance copy. No completion/reward authority is
inferred from requirement presentation.
