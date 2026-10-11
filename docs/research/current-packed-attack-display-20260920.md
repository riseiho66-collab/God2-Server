# Packed attack/defense display provenance

## Qualified edge

Pinned image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses are hexadecimal RVAs, image base400000.

The original B5BE0 display routine reads a supplied20-byte packed record.
B6424..B6447 selects by `(DWORD[record] >> 16) & 63`, subtracts1, and
uses selector tableBC1D0 and target tableBC188.
Executed cases1/25 reachB88E3; cases2/26 reachB8BEE.
Static inspected callsB8B59/B8E64 invokeB45B0/B4690 respectively, using
the incoming record reloaded from stack+11AC. The entire display routine
and these intervening formatting calls were not executed by this probe.

Original B45B0/B4690 execute up to entry of B4200, building:

| Display branch | First label | Second label |
| --- | --- | --- |
| B45B0 | ProgramMsg520, physical attack | ProgramMsg522, magical attack |
| B4690 | ProgramMsg521, physical defense | ProgramMsg523, magical defense |

In both branches the two displayed numeric arguments are:

```text
first  = BYTE[record+7] + 256 * ((DWORD[record+10] >> 28) & 3)
second = BYTE[record+C] + 256 * ((DWORD[record+10] >> 30) & 3)
```

Offsets10/C above are hexadecimal. Four additional arguments use bytes8..B
plus individual high bits24..27 and labels74/73/72/75(decimal). Their gameplay
meaning is not inferred here. The10-bit attack/defense arguments range0..1023.
This establishes the display extraction, NOT a combat formula or base stat.

## Evidence boundary

The category-dependent display and supplied instance record do not establish
a monster ID, original species data, or a recoverable wild monster table.
Do not reuse these record bits as a monster decoder. The original instance
value producer for categories1/2/25/26 remains to be traced. Existing
companion paths also reach B5BE0, but do not thereby prove that these four
categories are companions or monsters.

Recovered original wild attack/defense values:0. Database promotions:0.
The C++ receive-contract Record now exposes the read-only
`display_combat_arguments()` projection for categories1/2/25/26 only. Other
categories return nullopt. It returns the two message IDs and extracted
formatter input values; no final tooltip/combat-value claim is made.
Runtime emission and mutation remain disabled; no gameplay handler, Lua rule,
database value, packet builder or send path is enabled.

The data-table `client_category_code` must not be equated to these packed
category bits: current source parsing finds1/2 across many sections and no
25/26 rows. Native section-selector evidence is recorded below; matching
integers or apparent label names alone are insufficient.

## Reproduction

`tests/research/test_current_packed_attack_display.py` reuses the pinned-image
VM harness, executes real instructions, stops before B4200, and does not
replace any callee. Tests cover four original category dispatches and both
formatters across all combinations of the two high-bit fields and low-byte
boundaries0/255. It checks labels, numeric arguments, return target, argument
pointers and unchanged input bytes. These are synthetic diagnostic records.

```powershell
python -B -m unittest tests.research.test_current_packed_attack_display -v
```

Four tests pass. Full tooltip rendering, fresh runtime, combat calculations
and authoritative original monster values are not claimed.

The existing C++ instance codec test now checks the projection on its guarded
input suite, and explicitly covers all64 category bit patterns, all256 final
byte values, and low-byte boundaries0/255. Input ownership and roundtrip are
preserved. The standalone C++20 fixture compiled with warnings-as-errors and
passed, reporting29,552 existing guarded checks in addition to the new
32,768 display-projection combinations. These counts are not recovered data.

## Metadata range refinement

Follow-up original instruction execution establishes a second source: B4200
reads metadata+11C/+11D to decide whether to format a single number or a range.
B4409..B452A passes `value-spread` and `value+spread` to format string1926F4
(`\n%s:+%d ~ +%d`); a zero spread passes the unchanged value to1926EC
(`\n%s:+%d`). There is no zero clamp in the executed arithmetic. This is a
display interval, not proof of random damage selection or a combat formula.

The pinned item loader's native tag table1897EC binds first-match WPN/EQU to
selectors1/2 and TWP/TEQ to25/26. All four select59721 in59420's branch table.
The real loader reads zero-based source fields26/27 into metadata+11C/+11D.
The existing NativeItemMetadata harness now permits those four source sections
and executes the complete59420 parser, original index store,59A60 lookup and
resource getter, using its previously declared decimal CRT adapter only.

Current gamedata.csvZ source SHA256:
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.

| Source first record | Physical line | Original fields26/27 | Native bytes11C/11D |
| --- | --- | --- | --- |
| WPN:1 | 4804 | 5,3 | 5,3 |
| EQU:1001 | 5435 | 0,0 | 0,0 |
| TWP:19001 | 15478 | 6,4 | 6,4 |
| TEQ:20001 | 16108 | 0,0 | 0,0 |

These are four tested metadata records, not an all-equipment or monster-stat
recovery claim. Source metadata and supplied packed instance values are
separate inputs. The two original formatter branches are tested for both
components, spread0/3/5/255 and value0/1/1023, stopping before the CRT call.
Message count0 exercises the native missing-label path; no message result or
renderer is fabricated. Source-loaded bytes are checked separately from
the synthetic arithmetic boundary cases.
