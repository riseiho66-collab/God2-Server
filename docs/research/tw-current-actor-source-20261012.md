# TW current actor sources and native replacement lifetime, round301

PHASE1 static source/native recovery. Parent commit:
`a33f86edcee32840bf354b7b64407679a7ddef33`. No production source change,
build, tests, native execution, codec execution, DB/SQL execution or deployment.
This adds concrete source/lifetime evidence, not a completed gameplay route.

## Correction: the entry lease is not a stationary-character restriction

The stationary-only interpretation in round298 and the round300 frontier is
superseded. Their historical documents and sealed evidence remain unchanged.
The existing code separates immutable accepted-entry lineage from current pose:

- `SharedWorldPresence::prepare` retains the original `Lease.position`.
  `ready_lease` does not rebase it after movement; current saved pose is obtained
  separately through `saved_position`.
- `SqliteNativeWorldEntrySnapshotRepository::load` returns the original stored
  full2A frame/root/position. Its current account/character join proves ownership,
  not equality of current pose/profile to every entry field.
- `OwnedTaiwanPkAppearanceSource::observe` compares original entry position to
  `Lease.position` and checks original full2A geometry as lineage. Independently,
  `State::current` compares current saved pose to the joint equipment witness's
  position, with the exact joint committed observation and private Session guards.
- The room's `owned_appearance_current` compares equipment position to the
  current Pair peer position, not to original `Lease.position`. The reserved SQL
  fence repeats current saved-position/equipment and whole-observation checks.

There is already a conditional, actual configured custody-movement chain:

`SharedTaiwanNativeWorldHostPlan::Sources/StoredSources::with_owned_inventory_movement`
→ actual same-DB joint writer/context owner → native movement host/source
→ `SharedTaiwanMovement::move_owned`
→ `SqliteOwnedEquipmentTransaction::move_position_from_current` (CUSTOM0095).

That operation uses one actual IMMEDIATE transaction: exact source/root/readset,
scene/rules/ack/publication checks before mutation; CAS of recovered position;
equipment witness position/revision/provenance update; complete inventory tuple
and all1215 native equipment bytes, including DA15, retained; final checks and
one commit. It does not rewrite the original world-entry row. PK preparation's
same-DB factory obtains a fresh `observe_committed` and current Peer position.

This is existing conditional source, so round301 earns **zero new source
branches**. The noncustody movement branch can leave equipment stale and must
continue rejecting that mismatch. Actual scene/rules/custody ownership cannot be
replaced with an always-true callback. Original full2A lineage, exact current
position, whole inventory/equipment tuples, same-DB ownership and CUSTOM0105
transform/scalar restrictions remain mandatory. Changed common root/profile is
not qualified merely by a position update.

Separate identity restrictions remain: room comparisons require both
lease.character and lease.actor_handle to equal Pair.character; player identity
also requires character <=0x0FFF. This investigation does not relax them.
Application's `pk_rooms` remains uninstantiated, and its passive recovered
movement view does not implicitly establish the native host/custody composition.

## Native full6F replacement needs a fresh complete body

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Pinned original PE:
`5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`.
Selected code/data bytes match exact PE section offsets; this is not a claim
that entire mapped and PE images are globally equivalent.

Actual6F tail4699F1..469A28 calls4FB460..4FB4E5. New body DWORD0 low12bits
select the actor ID. Lookup4FC960..4FC98A scans128 slots at stride0x268. An
existing slot is passed to4FC560, then4FC1C0 always receives the **new body**.
Successful insertion can call4FD7A0/4FB8E0; those children remain opaque.

Complete selected removal4FC560..4FC654 frees qualified resource handles and
nested objects and clears actor+4C, movement98/9C and name's first byte. It sets
ID=-1 **only if pool+13418==1**; it is not unconditional slot retirement.
Selected removal has no direct actor+220 access, but opaque children prevent a
global absence claim. Actor+1EC passes as nested cleanup `this`; actor+220 then
corresponds to nested+34. Selected50E200..50E305/50DC90..50DCB4 do not directly
access nested+34; external children remain open.

Pool initialization4FABB0..4FAC54 zeros128 records of0x268bytes and establishes
ID/sentinels. This initialization includes+220 but authorizes no zero gameplay
value. Retained insertion4FC1C0..4FC553 reads new body+10 at4FC26D, storing it
to actor+220 at4FC277: logical DWORD17 remains exact opaque input. Neither
old-slot reuse nor pool initialization recovers its original meaning/producer.

The actual self initializer465427..46543A→500180..50025E, plus selected
50075D..5007EC, excludes a false counterpart: Main+22C receives saved aggregate
arg+10 BYTE, while Main+220/Main+21C are output coordinates from449330 followed
by Main+220 minus0x12C. Main+220 is not remote actor+220. Complete500180/449330
and original DWORD17 producer remain unqualified.

## Packed marker fields have current-state and deferred consumers

6F logical DWORD1 bits12..13 are stored at remote actor+260 by4FC39A..4FC3A2.
Initial4FD50F..4FD540 uses selector1..3 as50BF00(type3, selector+6), unless the
scalar264 override applies. Local2A bodyDWORD0 bits14..15 enter role+4694 at
46826B..468275; selected50048B..5004C0 uses the same presentation call.

Actual world36 case469C6B and503958..503968 overwrite local role+4694 from
incoming bodyWORD6 high2bits. Thus initial2A is not current selector authority.
Selected remote36/37 handler4FBC30 masks low14bits for existing-actor lookup,
retains actor+260 and can reapply that retained value. The self and remote
updates are asymmetric; a source issuer must preserve that distinction.

6F DWORD1 bits21..24 enter actor+7A at4FC38C..4FC397. Actual world table
46B5D4[36]=469C6B and [37]=469C09 reaches4FBC30 through469CFE/469C61 after
resource setup4614A0. For an existing actor, permitted display mode, no higher
override and positive signed bodyBYTE4>100, the retained value enters
50BF00(type0). It does not create a missing actor. Cached4FBEC0 also uses+7A
in its selected branch; its callers are not qualified here.

Local2A bodyDWORD4 bits3..7 enter role+94 WORD at4687D4..468813. Self update
503A0C..503A25 uses that WORD through the same type0 presentation path when
its scalar pointer WORD>100, handle is valid and no higher override wins.
Self input is5bits; remote input is4bits. Actual50BF73..50BF7E compares signed
WORD input to9 and clamps values above9, then uses action14+value. Equal
rendering cannot prove raw-field equality or justify discarding high bits.
These are display dependencies, not recovered level/rank/job/PK/permission
rules or original server mappings. Resource meanings and41F040 remain open.

The world-table capture includes1024bytes, whose final words include padding
and instruction bytes. Only the actual36/37 target entries support this finding;
the capture does not prove256 valid targets or the table's semantic extent.
The distinct seven-entry50BF00 selector table is qualified separately.

## Evidence accounting and next source cut

Archive: `C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-current-actor-source-301`.
Workers captured full inputs but report bounded manual scopes, not whole-client
or whole-repository review:

- current-source: existing current-pose lineage correction, zero source edits;
  raw seal9e6f638507be8adfb0f5b318de5aeee026fdcf00be93e173f596723e0ccc36b7.
- native-220:11 qualified spans2234B/707 instruction sites, including3 prior
  overlaps989B/318sites;8 new selections1245B/389sites. Canonical closure
  8f9e113cfcaaa4aeb9a1eb10d49ee0037c9566558829a20c7cd0130967ec811c;
  distinct raw seal-file hash686246adfb3616e2cbac654ce377ceb512ac2e12087950d90248c22628bed43a.
- native-prefix:9 qualified spans6238B/2017sites;7 new selections versus298
  4711B/1500sites,2 retained spans1527B/517sites, data captures1084B with the
  world-table extent caveat above. Selected2A also overlaps20260919 research;
  these selection counts are not global new coverage. Raw seal
  f76544db1d2c482ad37995c7be91712d1d90b78551f87adabb19e33a1bfda142.

Interpackage overlaps are not deduplicated into a whole-client coverage figure.
Misaligned/truncated exploratory disassembly is retained but excluded from
qualified spans. Logical DWORD9, DWORD17 meaning/original producer, second
DWORD low5, remaining packed selectors/status and original current remote
producer rules stay open. Mandatory81bytes cannot be synthesized from zeros,
diagnostic cached6F, old entry2A or similar-looking offsets.

The next fullactor source must compose actual common current position/joint
equipment with current marker/state and resource observations, exact opaque
inputs and complete directed visibility eligibility. Existing original entry
lineage remains one necessary fence, not the entire current model. Fresh full
body/resource versions are necessary across native replacement. Then connect
actual configured native host/backend/Application; paired final consume/output,
normal publication/marker retirement, durableFinished recovery, skills/rewards,
companion current HP and shared64 TW/CN/web wire/object/display remain open.

Source edits0, new CUSTOM0, new source branches0, new opcodes0, complete routes0.
Mixed source segments281/CUSTOM134/groups26 unchanged. TW C2S candidate union156;
world parser74=limited50/control11/unconnected13. S2C length252=fixed230/variable22,
reply48/push11/gated4/unclassified117. Battle indexed110/specialized9;
86selectors7/cases6;83actions23/projections2 unchanged. Unhosted TW chains3,
bindings38/unique34; CN chains35, bindings93/unique71. CN historical C2S156,
S2C phase-opcode280 and length253 are distinct scopes; CN increment0. Whole-game
route count/denominator and TW/game completion percentages remain null. These
are inventory/accounting figures, not connected-gameplay or acceptance totals.
