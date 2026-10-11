# Native monster level and hidden client acceptance

## Recovered contract

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The native logical length table entry for78 resolves to4012AC (`MOV EAX,5`).
Dispatch46A64B passes logical+1 to4CC840. The low WORD is an existing world
monster instance identity; the high WORD is its supplied level.4CCF80 looks up
the existing instance. This is not an EnyName ordinal or NPC selector.

4CC840 formats the supplied level through the actual native text renderer:
levels0..30 use the raw level,31..99 use the native band table59415C,100 or
greater select the native special label594320.4CC8F4 caches the low BYTE at
actor+17B. The server retains the complete WORD and does not silently truncate
the stored or transmitted level. The native label behavior is not a growth
formula or an exact numerical label for levels above30.

## Implementation

`RecoveredMonsterLevel.h`: exact five-byte78 parse/encode.
Schema35 `world_monster_levels`: level0..65535, qualified scene and existing71
instance foreign key, matching origin and nonempty provenance. Production reads
exclude `ISOLATED_TEST_ONLY`. The world projection queues78 after its71 record,
before an unrelated72. There are no default levels or invented source rows.

Both native world pools are256 records at+70, stride1D8 (1D878 bytes), not512.
The repository rejects an overflowing projection.

## Actual own-server client acceptance

`private-native-blackbox-20260927-02` used the current port-only client, real
loopback server2598, and hidden God2Lab desktop. No screenshots, memory writes,
code injection or desktop switching were used. Read-only checks confirmed:

* NPC3793, tile124/126, facing5, active native sprite/resource45.
* Monster123, tile128/126, facing6, active native sprite/resource44.
* Monster78 level27 cached at+17B, still correct after movement.
* Player movement saved in Kunlun4/3 and the client remained alive.

The first test correctly failed: NPC type0/index88 was not a current-map
resource. Following461580 established that type6 invokes the global ordinary
NPC resource route. The isolated fixture now carries logical byte6=66, keeping
the upper bits. This is a test operand, not a recovered original placement.

`private-native-blackbox-20260927-03` reopened persisted rows on a new hidden
desktop without reseeding/importing them. Exact native instance/facing/position
and level checks passed again. Saved display and level rows were unchanged.

Meaningful automated checks cover all65536 WORD levels, exact logical size,
wrong opcode, orphan level rejection, production exclusion, level ordering,
native pool overflow, atomic battle persistence and122 native arithmetic cases.

## Limits

The coordinates and level27 above are explicitly isolated acceptance operands.
They do not establish any monster's original spawn, actual level, attack,
defense, growth or skill formula. No verified original world placement/level
rows were available for the formal database. Battle83/0D actual client
application is a separate gate; source arithmetic/unit success alone does not
meet that gate. It subsequently passed in `private-native-blackbox-20260927-13`:
native monster HP150->120, native player MP26->16, saved MP16, no following86
or88 correction snapshots. The alive outcome logical14=28 was necessary;
logical14=0 selected death and produced client HP0 despite server HP120.
`Battle::apply_native_deltas` now rejects unqualified outcomes and results
whose live/dead state contradicts their staged HP. This does not recover a
damage-generation formula. Side1 MP was uninitialized native CDCDCDCD because
the bootstrap supplied HP only; that field is not fabricated into a zero/stat.
