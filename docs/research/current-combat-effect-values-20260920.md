# Current ChangeDollEffect Consumer Proof

## Result

The current native loader stores an **index WORD and description pointer** in an
eight-byte record. It does not select category, effect-code or basic-value fields
after tokenization. The followed consumer retrieves that description, executes
the original `%s: %s` formatter and appends its output to a text buffer.

**No attack/defense/hit/crit/element formula producer is proved by this edge.**
This is not a claim that such formulas are absent elsewhere in the client. In
particular, `50`, `5`, `1` and `-100` in the sampled basic-value fields do not
become numeric runtime coefficients through this loader. Descriptions containing
percentages are preserved text, not evidence authorizing server multipliers.

## Scope And Pins

Only the current client `Data2/Patch/Comm/ChangeDollEffect.csvZ` and the pinned
mapped native image from `recover_combat_rules` are used. RVA equals file offset;
the execution base is `0x400000`. PE section interpretation is not used.

| Input | SHA-256 |
| --- | --- |
| Encoded csvZ | `535a1c1a690e7f78be7d6e27cf8d212e89ed5230e5c7213c0e4fbe1d3a7d8ef1` |
| Decoded source | `565620cfafa678e13b76b833631d7c13fb55abeb30f5e0981dc24b15b317de08` |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |

The source contains 1,202 data records. **Native source-record coverage is four
sampled records**, IDs 2, 302, 936 and 1201, not full-source execution. Additional
synthetic counterfactuals and malformed inputs are not source coverage.

| ID | One-based line | Decoded byte offset | Code | Basic value |
| --- | --- | --- | --- | --- |
| 2 | 7 | 193 | `GOD_6421` | `50` |
| 302 | 307 | 12749 | `SPC_6821` | `5` |
| 936 | 941 | 38367 | `AMU_20` | `1` |
| 1201 | 1206 | 50409 | `GOD_6446` | `-100` |

The CLI emits each exact row hash (excluding CRLF), source offset, stored record,
allocation length, column-access trace, formatter arguments and resulting bytes.
CP950 source text is compared byte-for-byte and emitted as hex, without relying
on translated descriptions.

## Executed Dataflow

1. Original tokenizer `0x51BE0` splits source bytes into `owner+0x78+column*0x17C`
   slots. These are 380-byte buffers, with at most 379 content bytes plus NUL.
   Effect code and basic value are strings here, not integers of an inferred width.
2. Header comparison at `0x56E85` reaches call `0x56EC6` into loader `0x5BEB0`.
   Original numeric conversion reaches native `sscanf` at `0x1480B4`.
   At `0x5BEDF`, original calloc arguments are `(1203, 8)`; execution stops before
   the call. The row-table owner field is `+0xD2AB4` (DWORD pointer).
3. Row slice `0x5BF0C` converts column 0 via `0x51B30` and `0x51B50`.
   The DWORD index is bounds-checked before `0x5BF49` stores AX at `table+index*8`.
   Column 4 is selected through `0x51AE0`. Actual getter requests are `[0,0,4,4]`;
   memory-read hooks observe only token columns 0 and 4 during the row slice.
4. At `0x5BF77` execution stops before malloc with native `strlen(description)+1`
   on the stack. A separately declared allocation-result pointer is supplied to
   continuation `0x5BF7C`; `0x5BF8D` stores it at record `+4`, then original REP
   instructions copy the NUL-terminated description. Record `+2..+3` are untouched
   by this slice, proved with `A5` canaries, not falsely described as value fields.
   Owner `+0xD2AB8` is a WORD high-water count; the getter guard reads it signed.
5. Next consumer `0xBB8B4` reads the high WORD of the fixture item-instance DWORD
   at `+4`. Call `0xBB8D5` reaches `0x5C120` for the index guard; call `0xBB8F7`
   reaches lookup `0x5C0B0`, which copies the eight-byte record to its return buffer.
6. The returned record `+4` supplies the description argument. Call `0xBB935`
   executes original `sprintf` at `0x147AF7`, with format at RVA `0x190178`.
   Original append instructions produce `effect-fixture: <source description>`.
   Execution stops at `0xBB97C`, the following slot boundary. No text percentage
   is parsed, scaled, rounded or capped in this executed consumer.

## Explicit Boundaries

This is staged original-native execution, not a continuous file-load or gameplay
claim. csvZ decoding and CRLF-to-LF text-mode normalization occur outside Unicorn.
File-reader `0x51A90`, calloc `0x147E23` and malloc `0x147973` are not executed or
stubbed. A prepared table pointer and per-row allocation-return pointer are
explicit live-ins between native stages. The consumer owner, item effect ID and
label pointer are fixtures; `effect-fixture` is not claimed as recovered UI text.
The original image is read/execute-only, with no instruction patches. A separate
fixture return sentinel terminates calls. Each native stage is capped at 100,000
instructions and one second. VMs are reused across cases within each test.

## Reproduction

From the server root:

```powershell
python -B -m unittest discover -s tests/research -p test_current_combat_effect_values.py -v
python -B -m tools.strike_lab.current_combat_effect_values
```

Final local run: six methods passed in 1.127 seconds (1.436 seconds command wall
time). CLI subprocess completed with exit 0 in 0.519 seconds under a 15-second
timeout; its JSON reported exactly 1,202 source records and four native samples.
The owner independently reported six passing tests in 1.044 seconds and handled
CMake registration separately; no CMake edit was made in this lane.
They exercise four distinct pinned source records, six independent category/code/
basic-value mutations, one description mutation with a deliberately failing
unchanged-output oracle, three rejected native indices, eleven malformed input
cases and two accepted tokenizer boundaries. Exact `bytes` type validation
precedes normalization, so `str`, `None` and bytes subclasses raise `ValueError`.

Neither runtime rules nor databases, bootstrap code, CMake, earlier research
lanes or shared status files were changed. This deliverable narrows coefficient
provenance for this source: its selected runtime edge is description storage and
formatting. An independent arithmetic producer remains necessary before using
these source basic values as authoritative server combat rules.
