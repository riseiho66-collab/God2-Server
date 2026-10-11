# CN BATTLE deferred records and single-object prefix

Scope: pinned CN582F client, static primary recovery only. No build, tests,
native execution, resource decoding, database access or deployment occurred.
Evidence: `artifacts/integration/packet-connections-20261006/cn-battle-deferred-consumer-01`.

## Receive and consume are separate

The primary selector at 00548669/00548670 uses byte table00548D98
and target table00548C9C. BATTLE1C,38,83,84,85,86,87,88 all select
00548882: resolve logical length through00481170/00567B50, then enqueue
the full logical record through00555450 with ECX=main+A97980.
89 selects0054889A, enqueues into the same owner and sets the receive-drain
stop flag at005488B0. This is not a disconnect or final result observation.
Earlier immutable index rows marked some cases as empty fallthrough labels;
they represent shared labels, not no-op consumers. Historical index preserved.

Native fixed logical lengths are respectively45,2,15,15,2,17,3,121,57.
`CnBattleDeferredRecord` retains exactly those packets and exposes the89
receive-drain marker. This only establishes the queue-record contract; it
does not implement a battle authority, scheduling or any complete route.

00551D50 checks native progression/blocking flags, then00551FA9 peeks the
same main+A97980 queue through00555540.00551FE1 copies the current record
into main+A97180 through00555560 with advance=0. Selector00551FF7/
00551FFE uses byte table00552560 and target table00552538;1C selects
00552005 and calls0054D5E0 at00552008. Afterwards00552010 pushes
advance=1 for the shared00552013..00552023 length/read path. Other cases
can stop or defer progression; no unconditional consumption policy inferred.

00555450 performs split ring writes;00555560 performs split copies and
optional read-cursor advancement.00555540 returns null only when read=write.
Buffer ownership/allocation and actual native progression remain requirements.
These helper contracts are not server defaults, congestion policy or proof
that a full record has been accepted by the rendered client.

## 1C has role-dependent presentation data

0054D5E0 receives the full logical record, not body+1. It divides byte1
by14 for side and takes remainder14 for position.0055E220 uses the actual
battle owner main+149DF8: two sides, fourteen positions, six layer pointers
per position; layer6 aliases0. WORLD71's main+1499FA0 pool is different.
There is no proved world monster instance to battle slot/common identity join.

1C fields recovered from primary instructions:

| Logical offset | Native consumption |
|---|---|
|1 byte|side/position packed in base14|
|2 byte|stored level byte in object-prefix byte7|
|3 WORD|supplied identity, object-prefix WORD0|
|5 WORD|role-kind bits13..14, pose bits10..12, override low byte and other flags|
|7 WORD|role-dependent selector, object-prefix WORD12|
|9..40|32 bytes copied into object-prefix14..45, then role/resource branches may rewrite|
|41 DWORD|object-prefix DWORD8; if bit0 is set, native collapses the value to1|

Primary0054D65A..0054D68C copies all56 bytes of an existing object's
DB0..DE7 prefix into the local buffer; the earlier memset initializes the
local buffer if none exists. The decompiler's partial-copy reconstruction
must not override those primary MOVUPS/MOVQ instructions.
`CnBattleSingleObject::project_before_resource_branch` requires the caller's
actual prior native local buffer and reproduces only the bounded prefix
transformation through0054D760, preserving all untouched bytes. It neither
synthesizes a prior object nor performs later allocation/name/model branches.

The type0 ordinary resource branch uses category byte9, group WORD11 and
ordinal WORD7 with00428500; other role variants use different keys or names.
Raw kind3 also enters a different role-resource table. Later resource lookup
and override00430A50 can change wire pose in the client copy. These variants
are sealed as primary evidence, not emulated in the source prefix projection.
The consumer contains unsafe-looking unchecked paths; source retains their
meaning without constructing packets that rely on them.

The copied32-byte area is a union of presentation fields. It cannot be labeled
double attack/defense, four attributes, five elements, HP/MP or carried skills.
The late self-player path attaches up to50 pointers from00553A50 into
object+DF8; that does not prove an enemy skill list transmitted by1C.
True enemy combat stats and carried skills remain unresolved.

## Accounting and next work

Added two retained protocol sources, one explicit BATTLE1C field/projection
binding, nine primary queue/consumer relationships. New owner chains0;
new complete bidirectional routes0. Application has no CN battle host,
real admission/encounter authority, slot incarnation registry or qualified
common-state publication producer. No new tables or frozen TW changes.
Do not count nine queue cases as nine completed gameplay features.

Next recover battle entry authority and the1C role/resource/allocation
requirements, then86 subtypes and their downstream data updates, without
assuming world IDs are battle slots or that UI fields expose true server stats.
