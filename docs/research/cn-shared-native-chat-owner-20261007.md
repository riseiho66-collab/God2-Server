# CN native chat to shared recipient source, 2026-10-07

This round adds a conditional source composition, not a hosted or completed
gameplay route. The pinned CN executable remains
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
Bounded upstream sources and native receipt are copied into
`artifacts/integration/packet-connections-20261006/cn-shared-native-chat-owner-01`.
No build, test, game/Lua execution, database access, client changes or deployment
was performed. Python only seals static source/native byte accounting.

## Source composition

`SharedWorldGameplay` now splits complete native2F requests in its mixed ready
world stream and dispatches them in existing authority order. Before any batch
effects, the entire aggregate must have supported shapes. SharedNativeChat
attaches only to the actual ready CN connection and generation-qualified common
presence lease. Sources must supply a real chat WorldOwner and the retained
ChineseText converter; no default audience or success response is installed.

The bounded input forms are PlayerText channels0/1/3/13/18 and NamedWhisper
channels2/9 with `$<raw target name> <body>`. Board commands, control-bearing
battle text, other channels and unresolved markers remain unconnected. Shape
classification grants no permission. All reserved and opaque request fields,
claimed language tag and original request text go to the authority unchanged.
The pinned CN incoming text uses explicit CP936, not a claimed bit or OS locale.
Raw target-name identity is never converted; only the body becomes internal UTF8.

The authority must supply a nonzero source revision, actual recipient leases,
actual CN/TW transports and complete native5C envelopes with actual body ranges
and original-body UTF8 provenance. It owns permissions, scope, native actor
identity, bubble/presence ordering, loaded client destination capacity, prefixes,
names, native header values and rate/mute decisions. No common character ID is
truncated into a native actor and no zero-filled CN header is fabricated.

For each recipient, the adapter retains all bytes before/after the true body
and all opaque header bytes, converts only the original body to the actual
recipient's Traditional/Simplified preference, then uses explicit CP936/CP950
encoding and a character-boundary budget. Replacement/truncation metadata is
returned to the mandatory authority qualifier. The old supplied body is not
decoded and compared with the original UTF8: recipient wire encoding can already
have lost characters. Its semantic origin and body boundaries require authority
qualification instead. Outgoing CN uses CP936/tag0, independently of script
preference, avoiding native double conversion. TW uses the actual session's
existing language/codepage boundary and a separate bounded envelope path.

Every recipient must already be registered and ready in the same common presence
registry, with its actual session/account/character/generation. Both source and
recipient saved-position snapshots and publication authority are rechecked
before output. Duplicate recipient incarnations are rejected. Outputs retain
authority order. Queue acceptance does not establish delivery/rendered/native
acceptance; failure after a partial fanout does not promise rollback. Existing
CN cleanup releases the source generation. The frozen TW Application chat,
RecoveredChat serializer, IME, StreamerPresentation and native fonts are unchanged.
This source supplies CN input -> conditional CN/TW output; the frozen TW input
pipeline has not been enrolled into CN fanout automatically.

## Native evidence boundaries

2F is9..262 bytes, totalWORD1, channel3 low7, claimed tag3 bit7,
reserved4, opaqueWORD5, nonempty terminated text7. WORD5 is not a proven actorID.
The short decompiled004B1390 body and004B1706 shared tail belong to one flow;
the primary contiguous004B1390..004B1A10 bytes are retained, not counted twice.

5C carries totalWORD1, actorDWORD5, channel/tag9, text13. CN variable records
must be below0xA00. Bytes3/4/10/11/12 and authoritative server issuance rules
remain unknown. World0048FCC0 and battle005485F0 share some text consumers but
are distinct phase/variant branches; battle structured05/16 text remains open.
0053FB30 has native script/codepage conversion;00405A30 returns0 in this pin.
The client's repeat-message and channel18 producer throttles are not recovered
server permission/rate rules. Channel labels and strings are clues, not audience
proof. No CUSTOM party/guild/private handlers are imported as native CN rules.

## Accounting and next work

Five new C++ files (three bounded imports, two conditional owner files), two
modified C++ gameplay files and one catalog-tool change. One additional CN
unhosted partial owner chain; two CN world bindings2F/5C and one TW world5C
recipient binding. No new opcode, complete bidirectional route or actual
production supplier. Final unique binding counts are taken from catalog42.
Endpoint counts remain separate from route/game completion; the whole-game
denominator and percentage remain unknown.

Continue native authority/header and actual recipient issuance recovery, then
connect concrete shared audience sources and actual Application hosting without
rewriting the frozen TW input pipeline. Board/structured/battle chat, all native
state variants and TW input -> CN recipients still require source recovery.
Monster double attack/defense, attributes/elements and carried skill repertoire
remain unrelated pending primary-data work; chat headers/names do not supply them.
