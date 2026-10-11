# Current Taiwan 7A mode4 / MultiMessage1434 bounded contract

2026-09-26. Current God2.exe SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Only current EXE/current Data2 were read. No game process, visible desktop, live DB, Application or shared codec changed. Addresses are **VAs**. The new executable oracle maps PE sections directly from this pinned current EXE; it does not open historical mapped images or retired corpora.

## Result and exact scope

**A bounded nonformatting choice-dialogue branch is mode4, MultiMessage key1434, 28 logical bytes with an explicit zero argument count.** The actual current consumer selects its introduction; actual native pagination produces two pages; the native page/row arithmetic maps seven visible choices to indices0..6; the actual native85 builder and queue append emit those indices. This is suitable input to a narrowly scoped shared codec and own-server UI acceptance test. It is not quest44 completion or authority to reward/advance a character.

Mode2/mode3 are **not separate choice-table modes** in inspected `4C7F10`: like mode1, they use NPCMissionMessage pointer table. The choice branch is mode4 and uses MultiMessage. This namespace distinction was executed with different sentinel pointers in the two synthetic resource tables.

The oracle uses a **loader-equivalent synthetic table containing current raw1434 strings**, with other entries empty, and the verified current total count2995. It does not execute457C20 or claim full GUI rendering/input hit-test acceptance. It stops the incoming route at4C8234 before render; separately executes native4C8780 pagination and native4C8671 click-index arithmetic, then native4C8500→497DC0→4132E0 through queue append, stopping before4C8350 close. No game function return is stubbed and no native instruction bytes are patched. UI/frame/client live acceptance remains separate.

## Logical S2C7A record (scoped constructor)

Offsets include opcode; all multi-byte numbers are little endian.

| Offset | Width | Scoped value / meaning | Native origin |
| --- | --- | --- | --- |
| 0 | 1 | 7A | Dispatch opcode; current length table401324+4*7A points401318, returning-2 |
| 1 | 2 | 28 = complete logical record size | 413521 reads network+2CC5; receiver compares assembled count with this word |
| 3 | 1 | 4 | 4C7F10 reads body+2 to UI+CCC1C; mode4 branch |
| 4 | 1 | opaque context byte | body+3 copied to UI+CCD36, later85 body+4 |
| 5 | 2 | opaque request/correlation word | param[2]→4C81F0→global5B7BFA; later85 body+0 |
| 7 | 2 | MultiMessage key1434 (9A05) | param[3]→UI+CCC1E; table[ key-1 ] at resource+B2C54, stride8 |
| 9 | 2 | reply/control word; this candidate accepts0..32767 | param[4]→5B7BF8; signed gate in4C8500. Original server field semantics unknown |
| 11 | 16 | all zero (no name formatting) | param+10; nonzero first byte enters strncpy/sprintf branch, intentionally excluded |
| 27 | 1 | zero argument count | mode4 copies length-27 bytes from logical+27 into UI+CCC32; no option substitutions/hiding |

**The packet does not append seven labels or seven text IDs.** Labels are already in MultiMessage resource. Do not substitute NPCMission1434 or journal1434 here.

Example uses synthetic request1234/context9A/reply2 solely to distinguish field origins; these values are not recovered original server assignments:

```text
7a1c00049a34129a0502000000000000000000000000000000000000
```

Reply caveats: FFFF stays FFFF and prevents the initial85 in4C8500. Other bit15-set values normalize to low15 and set5B7BEC=1. Existing close-path work records that this flag can produce additional close-path85; this oracle stops before close and the proposed candidate excludes high-bit replies. Do not silently assign original meaning such as accept/complete to reply2.

## MultiMessage source and count

Current resources contain2995 keys in exact order1..2995. Headers are per-file counts; **the consumer bound is the final maximum key**, not the1000 header of file02. `457C20` stores max(unaff_retaddr+1) at resource+B2C50 after subtracting1 from each incoming text key. Its 8-byte row stores BYTE(option count+1), and at+4 a pointer array: index0 introduction, indices1..N labels. `456130` dispatches the literal MultiMessage section to457C20.

| File | Header / rows | Key range | Compressed SHA256 |
| --- | --- | --- | --- |
| MultiMessage01.csvZ | 1000 / 1000 | 1..1000 | `0d573b607f477c0da53c2efa7aeb1881bcb1d38941cf36472cd9a506d13f9985` |
| MultiMessage02.csvZ | 1000 / 1000 | 1001..2000 | `441b2828b6edccdb36098c3aba9d6e631ae351d82e685969d34758b67fe6c10f` |
| MultiMessage03.csvZ | 995 / 995 | 2001..2995 | `e0551afec2108f478f27f2364bd15bd8d7ff999c8f12a087b320d06d23659e4d` |

1434 is a seven-choice table row (native byte8). Introduction and **all seven labels contain no percent sign and no embedded NUL**. This is checked against the pinned CP950 raw bytes before executing native code. The report JSON also includes `raw_hex` and per-rowSHA256 for exact transport/resource investigations.

| Physical line | Namespace key / option ordinal | Exact original text |
| --- | --- | --- |
| 1529 | MultiMessage 1434, ordinal 7 | 很好，孺子可教，即然你決定要在仙界進行修練，就讓本天尊先教導你一些基本的知識吧！ |
| 1530 | MultiMessage 1434, ordinal 1 | 我已經知曉箇中奧妙了！我要進行下一階段的修練。 |
| 1531 | MultiMessage 1434, ordinal 2 | 滑鼠功能 |
| 1532 | MultiMessage 1434, ordinal 3 | 介面概述 |
| 1533 | MultiMessage 1434, ordinal 4 | 買賣說明 |
| 1534 | MultiMessage 1434, ordinal 5 | 交易解惑 |
| 1535 | MultiMessage 1434, ordinal 6 | 組隊釋疑 |
| 1536 | MultiMessage 1434, ordinal 7 | 升級點數配置 |

The introduction is not an acceptance event. Source option1 (“下一階段”) is wire choice0, but the text does not authorize any journal mutation. Neither1434 nor option ordinal is an NPC world ID.

## Native pagination and request origin

Actual4C8780→4FFDF0 and getters, using current CP950 introduction, return page_count2, UI+CCD32 threshold0, UI+CCD34 bias2. Native4C8671 uses:

`choice = (page - threshold) * 5 - bias + visible_row` (16-bit storage).

| Page (zero based) | Click row (zero based) | Wire choice | Resource option ordinal |
| --- | --- | --- | --- |
| 0 | 2 | 0 | 1 |
| 0 | 3 | 1 | 2 |
| 0 | 4 | 2 | 3 |
| 1 | 0 | 3 | 4 |
| 1 | 1 | 4 | 5 |
| 1 | 2 | 5 | 6 |
| 1 | 3 | 6 | 7 |

85 logical request is exactly7 bytes:

| Offset | Width | Origin |
| --- | --- | --- |
| 0 | 1 | 85 |
| 1 | 2 | stored incoming request word5B7BFA |
| 3 | 2 | UI+CCC20 choice, zero based |
| 5 | 1 | incoming context fromUI+CCD36 |
| 6 | 1 | uninitialized stack byte copied by497DC0's6-byte payload; opaque, **not a choice/count** |

Default oracle poisons stackA5 and records e.g choice0 `85341200009aa5`. This final byte is not required to beA5 and must not be checked against a fixed constant by a server.

Native4C8500 permits a final page or mode4 page>=threshold, requires stored reply to be signed nonnegative, then checks only choice0..7. **For1434 it still emits85 for choice7 even though only0..6 exist.** This is explicitly tested. Server must enforce current conversation, current NPC/world binding, catalog key1434, expected request/context, valid choice0..6, and one-time/session lifecycle independently. Native client bounds are insufficient authorization.

## Record bounds measured on actual x86

- Receiver7A uses unsigned whole-record length. Length<2560 reaches normal total-length comparison;2560 branches to rejection41359A;>2560 enters assertion setup413534. Receiver alone accepts lengths0..2 in this slice; these are unsafe content.
- Mode4 header slices3,10,11,12,26 at a mapped-page edge fault reading outside supplied input. Length26 underflows unsigned `length-27` copy. Do not forward short records.
- 27 bytes performs zero tail copy and initializes argument count0 internally;28 explicitly copies count0. Both reached4C8234. The scoped constructor chooses28.
- Tail buffer UI+CCC32 throughUI+CCD31 is256 bytes. Length283 copies256 and preserves the poisoned threshold1234. Length284 copies257 and changes threshold to12EE with markerEE. **The transport limit2559 does not protect this buffer.** A future variable-argument encoder needs stricter content and copy bounds; this branch accepts only28.
- Nonzero tail is a count plus index/string argument stream used by4C8780/4C8920 for substitutions and empty-string suppression. No nonzero-tail branch is qualified here; arbitrary tail bytes must not be enabled based on the header test.
- Key0, bound+1=2996 andFFFF stop at the native assertion path with synthetic table count2995. Valid-key check also requires a populated selected record. Catalog count alone does not certify record availability.

## Executable verification and handoff

From server root:

```powershell
C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe -m tools.strike_lab.current_dialogue_mode4_native_20260926 --output artifacts/reports/current-dialogue-mode4-20260926/native-vectors.json
```

To verify compiled C++ output through the same actual consumer/producer, append `--packet-hex <hex>`; accepted input is exact28-byte mode4/key1434/name16zero/count0/reply0..32767. Request/context are read from that candidate and compared to native85 output. Source/PE pins, condition checks and native instruction budgets remain enabled under Python `-O` (no Python assert used).

Actual runs: default vectors PASS; alternate requestFFFF/contextFF/reply7FFF under `-O` PASS. Every slice must reach an explicit stop within250000 native instructions. Executed categories: four namespace modes; ten choice boundaries(-1..8); seven page/row mappings; five reply gates; three invalid key bounds; two tail-copy markers; twelve receiver lengths; nine packet-edge lengths; an early-page denial. Expected malformed packet faults are recorded as negative vectors, not successful input acceptance. A manually malformed alternate CLI hex was rejected before execution; it produced no report.

Artifacts:

- `tools/strike_lab/current_dialogue_mode4_native_20260926.py`
- `artifacts/reports/current-dialogue-mode4-20260926/native-vectors.json`
- `artifacts/reports/current-dialogue-mode4-20260926/alternate-fields.json`

No full original text-loader run, actual widget hit test/render, network frame roundtrip, or current-client UI acceptance is claimed. Those are mainline integration gates. No original task reward/condition/NPC-event mapping was inferred.

## Executed code span pins

| VA start | End exclusive | Current code SHA256 |
| --- | --- | --- |
| 0x4c7f10 | 0x4c8240 | `a63fa4052cf134f35eab18c0732f4440e80e5a3e1d67ad9a5f57cc3e070ef6f9` |
| 0x4c8500 | 0x4c85a1 | `733bbb918ae48b1058986f235dd7b5a5a0cc7a80616a5c69683ab462c1938a62` |
| 0x4c8671 | 0x4c86ac | `faf05b2ebee1fa40287f36f6312a1af6f488859a5d2dee4ed74511af2b26a06a` |
| 0x41351f | 0x413566 | `1d86ba24c052457ac268e9e1098372e01cba5cd78485de53371b07fc5d46b300` |
| 0x4c8780 | 0x4c8920 | `44204ac39d81ced084640de1d1ff99675eb43281b36da72f8d9621f18b50ff29` |
| 0x497dc0 | 0x497e00 | `977e63efc0e946fc3d0afb2cd20f76701419e30bd339af97d348144ae84f51fc` |
| 0x4ffdf0 | 0x500100 | `67361e3a3e9b625b6bc3fa944deb141353fc290605fa029a289f54ae8ab05972` |
