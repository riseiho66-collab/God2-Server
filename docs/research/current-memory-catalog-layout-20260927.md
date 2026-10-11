# Current loaded catalogs: memory address and field provenance

Date: 2026-09-27. Scope: bounded current Taiwan image/source inspection, followed by
an offline native execution of the NPC catalog cache writer. The parent lane owns
the real hidden-client read-only memory capture. This tool opens no process.

## Reproduction and identity

```
python -m tools.strike_lab.current_memory_catalog_layout_20260927
python -O -m tools.strike_lab.current_memory_catalog_layout_20260927
```

Both runs pass: 11 compact code ranges match the mapped evidence byte-for-byte;
eight full native `45BA30` executions return correctly with the exact expected
94-byte output. Source inventory contains **4,043 NPCAppearData rows**, maximum
selector 6,224. Two valid short rows have five fields: 1156 聶萍 and 3472
機關人蘿蔔號; 4,041 have nine fields. Capacity/highest selector/defined row count
are three different quantities.

- Current EXE SHA256: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Mapped image SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Gamedata packed SHA256: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Gamedata decoded SHA256: `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.

Evidence: `artifacts/research/memory-catalog-layout-20260927/evidence.json` and
the eleven `*.asm.tsv` files. Every range records VA, exclusive end, raw file
offset, SHA256 and instruction bytes. No analysis project was changed.

## Catalog owner and independent anchors

Parent capture `live-memory-catalog-20260927-02/memory-result.json` observed:

| NPCAppearData selector | Source line | Name | Name address |
|---|---:|---|---|
| 2936 | 1707 | 廚師梁禎 | `00635D36` |
| 2938 | 1709 | 阿銀嬸 | `00635DF2` |
| 2939 | 1710 | 馬老伯 | `00635E50` |

All three independently produce catalog owner **C=`005E053C`** by subtracting
`0x121EA + selector*94`. These are run-observed addresses, not an ASLR-independent
locator. In the world, `C=DWORD(W+AA36480)`; the UI dialogue code also uses
`DWORD(UI+CFF70)`. Validate the resulting object against names and Mission
count/base before reading larger arrays. Do not assume a similarly named offset
in another class is the same object.

## NPC record: 28 source bytes plus a server-writable tail

The array is inline at `C+121EA`, indexed **directly** by selector, stride `5E`
(94). `signedWORD(C+121E8)` is the highest loaded selector. Constructor
`4558D0` handles 7,000 slots. Loader `4570F0` writes:

| Relative offset | Size | Exact source / meaning established here |
|---|---:|---|
| `00` | 16 | NPCAppearData column 1 name; final byte forced NUL if longer than 15 |
| `10` | 2 | low14 = column3; bit14 = column4 & 1; bit15 = composite resource discriminator |
| `12` | 2 | column2 appearance resource code |
| `14` | 2 | body component pair, column7 `b` token |
| `16` | 2 | face component pair, column6 `f` token |
| `18` | 2 | head component pair, column5 `h` token |
| `1A` | 2 | weapon component pair, column8 `w` token |

Columns above are zero-based, including selector at column0. Component parsing
is conditional on appearance code 5001..5003 and matching token letter. The
resource category nibble is derived from that code; token bytes supply the
remaining packed category/ordinal fields. The two short rows do not supply
component tokens. A missing token is not evidence of a hidden coordinate.

**The remaining 66 bytes are not all original local definitions.** Native world
dispatch case F8 reaches `46AAD6`: load `C`, increment the logical packet pointer
past the opcode, push that body pointer, call `45BA30` at `46AADE`. There is no
local formula between body and cache. The body selector is DWORD at +8. Writer:

| NPC record offset | Body offset | Size | Established use |
|---|---|---:|---|
| `1C` | `00` | 1 | display mode/cache selector, also consumed by S2C72 |
| `1D` | `04` | 1 | displayed as Level by `4CDC70` |
| `1E` | `78` | 2 | signed modifier used in level text formatting |
| `20` | `34` | 16 | copied as four DWORDs, then used as **a string** by `4CDC70` |
| `30` | `4D` | NUL-terminated | status/board text; empty body selects ProgramMessage 1001 or 887 |
| `55` | `45` | 4 | opaque server-supplied value; no coordinate/stat name assigned |
| `59` | `49` | 4 | opaque server-supplied value; no coordinate/stat name assigned |

The string copy is not bounded in this native function; the final byte `5D` is
not otherwise written by the demonstrated fixed field copies. Do not derive a
safe outgoing F8 serializer just from these writes. Eight offline fixtures use
nonempty bounded strings, four valid selectors and level bytes17/255, executing
the entire function without replacing native callees. A poisoned prefix remains
exactly unchanged; only the specified tail bytes change. This proves copy
provenance, not valid native gameplay values.

Constructor `4558D0` clears only record byte offsets `00,1C,1D,20,30`, not the
whole 94 bytes. Therefore unused bytes cannot be promoted into meaningful
defaults. The four DWORD copies at `20` are specifically **not evidence for four
attack/defense values**. No NPC world x/y/facing is loaded by `4570F0`.

Relevant raw ranges:

- `4570F0..457624` exclusive, raw `566F0`, SHA256 `0c96c892a886bb19d43439f39ca61888784970e3c59ca47ee2b3de2c3a1f93be`.
- `45BA30..45BB04`, raw `5B030`, SHA256 `12cd2e709f671bd5647596a90224619bd6832407a6a8a1f76a518e93f4d5016c`.
- `46AAD6..46AB27`, raw `6A0D6`, SHA256 `c95ae544c798f9ad17091086ea013ac71c69e4c3174777a72d1783cf2242144e`.
- `4CDC70..4CDE92`, raw `CD270`, SHA256 `901f914115682b0996259462b9b492f8250eaf4364345e73d60811b757febe81`.

## EnyName: namespace and 26-byte display record

`45A1A0` loads these tables; `45A000` and `45A0A0` resolve them. Read
`C+D2D9C + area*8` for areas0..16: DWORD descriptor count, then DWORD descriptor
pointer. Each descriptor is 12 bytes: sceneDWORD+0, recordCountDWORD+4,
recordBaseDWORD+8. A one-based ordinal selects `recordBase+(ordinal-1)*26`.
Area0 is also used by companion/following display namespaces; it is not proof
of a wild encounter.

| Record offset | Size | Native writer source |
|---|---:|---|
| `00` | 1 | high4=CSVcol2, bit0=col3&1, bits1..3=col5&7 |
| `01` | 1 | low byte of CSVcol4 resource code |
| **`02`** | **16** | **name**, CSVcol1 copied at most15, byte17 forced NUL |
| `12` | 2 | body pair from CSVcol8 |
| `14` | 2 | face pair from CSVcol7 |
| `16` | 2 | head pair from CSVcol6 |
| `18` | 2 | weapon pair from CSVcol9 |

The first WORD is two separately written packed bytes, not a name or ordinary
numeric stat. The eight component bytes are parsed only for composite resource
5001..5003 with bit0 set. No x/y, rates, HP/MP, attack/defense or server instance
identity is loaded into this 26-byte definition.

`DWORD(C+D2E24)` points to the original allocation of 7,815 records. Descriptor
roots expose 7,791 records, 96 groups: a repeated source area7 header replaces
24 earlier records' descriptor references. Reading arena orphans may recover
source display bytes, but does not create new visible lookup entries or spawns.
The source ordinal column is not used to compute the loader address; sequence
within the group defines the ordinal used by `45A0A0`.

Range `45A1A0..45A55F`, raw `597A0`, SHA256
`41a48f978dd728a30012b734e5d30688fabd297c66b5c9a16d9ed5c4f6c37727`.

## Quest/dialogue pointers for the next read-only pass

| Table | Owner fields | Record shape and indexing |
|---|---|---|
| Mission_data | countDWORD `D2AC0`, tableDWORD `D2AC4` | 40 bytes, questID-1; signed countWORD+0; name+2; char**+24hex |
| NPCMissionMessage | max signedWORD `B2C48`, char** `B2C4C` | textID-1 pointer; source payload follows first comma |
| NPCNormalMessage | max signedWORD `B2C3A`, tableDWORD `B2C3C` | **44 bytes, textID directly**; validBYTE+0; textDWORD+4 |

NPCNormal is not a char** or an ID-1 array. `4578B0` writes its validity byte and
string pointer and leaves other fields outside this source writer's scope.
Mission_data expected418 records and2014 description strings were already
compared against source by the parent live run02. Read pointer arrays and strings
with bounded readable-region checks; require a NUL within each chosen limit.
Quest IDs, NPC appearance selectors, NPC text IDs and live NPC world identities
remain separate namespaces even if numeric values happen to match.

## Live pool boundary

Loaded NPC definitions at C are distinct from `N=W+1539AED8`: 256 live records
at `N+70`, stride`1D8`. Live records have identityDWORD+0 (FFFFFFFF empty),
facingWORD+8, tile x/yDWORD+10/+14 and render positions+18/+1C. Those values
are supplied through the qualified world receive/movement paths covered in the
prior position-writer reports. A catalog name hit alone does not establish any
live pool record, map/scene placement, encounter, event or reward.

The new positive finding is a clear **server-to-catalog F8 cache writer**. The
unknown tail fields remain unknown. This bounded inspection does not assert
that every other unanalysed field or code range lacks useful authority.
