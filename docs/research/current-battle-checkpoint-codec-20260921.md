# Checkpoint storage codec

CUSTOM-0007 BattleCheckpointCodec defines canonical JSON for server storage, not
a native packet. Nine required fields: version, design_id, engine, id, revision,
state, winner, actors, rng. Actor array has28 slots, each null or10 exact integer
fields in BattleActor declaration order. Integers are not parsed through double.

Decoder limits input to32768 bytes and nesting depth5. Negative/floating/bool
numeric fields, narrowing overflow, absent/extra fields, wrong actor shape,
unknown provenance/runtime and contradictory domain states are rejected. Complete
Battle::restore validation runs before canonical re-encoding comparison; duplicate
keys and noncanonical text are rejected instead of silently normalizing storage.
This format is intentionally not a permissive manual import format.

Engine tag includes library version/update (current MSVC STL); incompatibility
requires a deliberate migration, never an implicit reseed. Existing checkpoint
core independently validates bounded state words and runtime serialization layout.

Release server and battle-transaction build passed. Tests encode/decode active and
finished battles, compare exact continuation including critical rolls and response
bytes, preserve identities above2^53 through uint64 max, and reject12 malformed
JSON field variants, duplicate keys, deep nesting, oversized input and sampled
truncations. Core invalid-checkpoint tests remain enabled.

Not yet durable: no database table, atomic checkpoint/resource transaction,
authorized policy/control receipt snapshot, reconnect admission or client resume
is installed. No gameplay percentage increase or native formula claim follows
from this codec. Next integration must persist policy identity and resource CAS
alongside battle state, not write this JSON in an unrelated best-effort log.
