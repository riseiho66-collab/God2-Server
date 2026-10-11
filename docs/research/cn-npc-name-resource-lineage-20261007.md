# CN NPC name resource lineage, 2026-10-07

The retained decoded gamedata source has4461 NPCAppearData input rows and4459
distinct positive selectors, maximum6548. This round connects its conditional
name-prefix projection to the existing D1/F9 owner through an explicitly supplied
resource identity. It does not enable that historical projection for the current
installed asset, whose encoded and decoded hashes differ.

## Source epochs stay separate

| Source | Encoded SHA256 | Decoded SHA256 |
| --- | --- | --- |
| Retained historical gamedata receipt | f8b0762f111c532f1cbb38d66f06b6a4c6c685c278a5dcc98fbaead780e2376f | 1a818c454df37c58f1565b244a1030668cac52bf7ee75bb9a7db3e0bee263b44 |
| Current scene-resource receipt and encoded file | 8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a | 16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3 |

Both reports identify pinned CN executable582F2695..., but an equal executable
does not make these assets equal. The historical decoded file is retained in
God2_opt_source_recovery_20260926_055734/agent_round7_monsterfield/decoded;
its manifest binds its bytes to the pinned executable. The separate historical
cn_skill_books receipt supplies the encoded-source hash and the same decoded
hash. Its original compressed epoch is not present at the currently named path.
The current scene catalog already retains the current encoded/decoded hash pair.
No baseline was refreshed; current names remain unqualified by this old table.

Whole-file CP936 decoding of the historical file fails at offset1618176, in
other source data. NPCAppearData rows are processed as raw bytes with ASCII
section/key/comma boundaries. Their name fields contain no quotation bytes,
all decode as CP936 individually, and all selectors are nonnegative and<7000.
No replacement-character decode, whole-file localization or rewritten field
is used to obtain these names.

## Primary native file and name contract

00428AE0 calls00405A30, which returns0 in this pinned executable, then formats
`%scomm\\%s` and visits24 filename pairs at008863D8, choosing the first member
of each pair. Pair0 is gamedata.csv and pair1 message.csv; both are passed to
00428C80. Existing00449F50 evidence supplies the Data2/Patch root. The dispatcher
matches NPCAppearData and calls0042EAC0. This round retains the new primary
parent/function bytes and filename pointer table, with previous loader evidence
preserved. It does not assume a name in message.csv merely because that file
contains the displayed F9 column titles.

0042EAC0 reads numeric field0 and, when key<7000, copies field1 through its
firstNUL to direct-index storage+124E2+key*94. If the original byte length is>15,
it explicitly writes NUL atname[15]. It updates the signed maximum at+124E0.
The remaining fields are appearance flags/code/component parsing; the whole
94-byte record and unwritten suffix are not reconstructed as combat data.
Some input rows have5 or6 fields rather than9; this name projection uses only
the observed fields0/1 and does not invent missing appearance components.

The native loop processes row order. Key6195 occurs twice with the same name;
key6276 first names五行魔自选包, then五行封自选包. The second row overwrites the
same direct-index name. Generated rows retain the final source line and prefix,
while the artifact retains all4461 ordered input rows and both overwrite events.
64 input names exceed15 bytes. Byte truncation may split a multibyte character;
the raw native prefix is retained, without a Unicode repair or conversion.

## Conditional source connection

CnNpcNameCatalog contains4459 final selector/name prefixes and source lines.
Its gate requires the historical executable/encoded/decoded hashes, positive
actual resource revision and an independently supplied actual signed native
maximum6548. The maximum is not guessed from a packet or treated as an actor ID.
Missing sparse keys return no evidence. The current8A72 resource fails this gate.

SharedSpecialDirectory retains fully supplied native name evidence as before.
If none is supplied and an actual resource identity is supplied, it can use this
strictly matched catalog to project the consumed F9 selector25 names. It checks
the existing name shape and still requires WorldOwner.qualify_delivery for the
actual source snapshot, permission, revision and issuance. No native strings are
added to the F9 wire record. Local array bytes after firstNUL are canonical unread
padding only; they are not native memory evidence or a recovered zero default.

The current installed resource's NPC section still needs its own exact retained
bytes/projection before it can use this path. This round did not run a decoder,
asset loader, client, server or game. It adds no opcode, complete route or new
partial owner chain; the existing D1/F9 owner gains a qualified historical source
projection. Monster double attack/defense, four attributes, five elements and
carried skill repertoire remain unknown; NPC appearance names prove none of them.

Catalog39 baselines and modified source were captured before edits. Original
CN/recovery files and all old manifests are preserved. No database access,
build, tests, runtime, deployment, fonts or text-conversion changes occurred.
