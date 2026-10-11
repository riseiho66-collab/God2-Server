# Atomic isolated inventory/resource persistence

CUSTOM-0015, repository-only. Migration11 adds an empty diagnostic slot table;
migrations1..10 remain unchanged. No existing owner database was opened for
migration by this work; tests use temporary databases. Future normal migration
adds only an empty table and does not grant items or reinterpret absent rows.

Each explicit slot carries item/count, revision, source SHA256 and design tag.
Slots0..49/count0..127 are a deliberately bounded S2C41-compatible diagnostic
projection, not official capacity/stack rules. Empty slots retain a versioned
item0/count0 tombstone, preventing deletion/recreation ABA. Source hash records
provenance identity; repository does not certify the supplied hash/catalog row.

Concrete SQLite commit_inventory_resources checks owner, exact slot/resource
baselines, valid proposal and absence of any unledgered battle reservation under
one transaction. It stages resource update, writes the slot and checks exact
readback of both before commit. Errors roll both back. It does not interpret
C2S25, raw_tail, numeric healing rules, acquisition or replay request IDs.
Caller owns those policies; stale revisions reject rather than reapply.

Test uses explicit source3107, one unit and proposed MP2->52. This is a
transaction fixture, not runtime item activation. An AFTER UPDATE trigger
aborts the slot write after resource staging: both old values remain. Successful
retry clears slot and updates resources together; stale replay, foreign owner,
slot50/count128 and pending battle writes are rejected. Disk reopen preserves
both states. Server/tests compile; database, recovered_character_repository and
recovered_position_repository CTests pass.

Next: authoritative explicit inventory initialization and item-use validation,
Lua effect/cap policy with field-level native/custom provenance, wire response
prepared before mutation, and native client visibility/use acceptance. Ordinary
logs must not expose credentials. Full gameplay goal remains incomplete.
