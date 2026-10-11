# Native guild war request and display continuation

The owner requires complete bidirectional source connections before any tests.
This continuation recovers missing native war UI semantics from the pinned
original image. It does not enable war actions, change an existing migration,
install a feature, run tests or restart the service.

## Original evidence

`artifacts/integration/packet-connections-20261006/guild-war-static-contract.json`
records exact bytes, SHA256 and disassembly for seven bounded code ranges,
four literal/jump tables, the95/96 lengths and original ProgramMsg rows.
`tools/reconstruction/guild_war_contract.py` reads only the exact mapped image
and original message resource through the verified archive reader. No historical
client or build tree is restored.

The mapped image is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The message source is
`5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`,
decoded `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.

## Recovered routes

`EE6BC..EE7D6` creates a declaration prompt and caches subtype5 and name16.
The modal result8 selects `EE5AF`, which sends the cached17-byte body as native
C2S76, logical18. A matching existing exact raw-type6 client row blocks this
prompt. That display condition is not original server authorization.

`EE7D6..EE8C7` selects removal intent from an existing relation row. Exact raw
types1..3 select76/8 and types4..7 select76/9; the latter uses modal result10.
This decision does not mask the high bit, even though the renderer does.
`EE560`'s eight-entry jump table supplies the result3..10 routing; result7..10
all use the cached76 producer. No additional request fields are invented.

`EBF92..EBFDB` loads the original ProgramMsg keys from197EA8 into197EC0 at
stride8. `F0D50` uses `raw_type&7F` to select those labels:

| Low7 type | ProgramMsg | Original label |
| --- | --- | --- |
| 0 | 9 | empty |
| 1 | 192 | 同盟 |
| 2 | 193 | 同盟邀請中 |
| 3 | 194 | 受邀結盟中 |
| 4 | 195 | 防守 |
| 5 | 196 | 進攻 |
| 6 | 797 | 宣戰 |
| 7 | 798 | 被宣 |

`F0DF3..F0E1C` passes record+5/+6/+7 to `%2d/%2d %02d:00` at1966C4.
These are logical6/7/8 and body5/6/7: three raw month/day/hour display BYTEs.
They are not a countdown. This observation supplies no year, minute, timezone,
expiry, server time unit or authoritative schedule.

`F0FB0` admits at most50 cache rows before duplicate lookup and copies the full
24-byte95 body. Exact raw6/7 append duplicate identities; raw4/5 replace the
first matching identity and scan later matching6/7 entries with swap deletion.
These details matter when reconciling declared and active war rows. The raw80
bit selects a display icon; it does not establish consent or permission.

## Formal source and next implementation

`src/relations53/RelationsRawCodec.h` now has the explicit display-kind enum,
raw month/day/hour accessor and exact unmasked UI removal-intent accessor.
The existing alliance repository uses named display kinds for the same bytes.
This is codec/source integration, not a completed76/5 or76/9 gameplay route.

Immutable schema53 remains restricted to alliance states0/1/2 and subtypes1/8.
Do not rewrite its SQL/history to insert war into that existing state namespace.
War needs a separately registered additive state/event policy, two-guild owner
and WORLD authority, whole read-set/CAS, and the shared95/96 projection scheduler.
Combined alliance/war rows must fit the native50 cap. Transfer/disband and
character lifecycle must retire the correct war authority in the same mutation.
Declaration/cancellation, scheduling/consent/economics, activity/combat effects
and final comprehensive original-client acceptance remain open. Original rules
are not implied by UI labels or a month/day/hour display.

No build, test, emulator, native client execution, live DB write, migration,
feature activation or deployment occurred in this continuation.
