# Atomic role snapshot and resources

Migration9 adds an EMPTY character_role_snapshots table. It preserves25-byte
logical22, independent signed64 revision and CUSTOM-0013 origin. No existing
character is populated, leveled, reset or assigned synthetic stat values.
The profile/create blob remains untouched; role snapshots are separate state.

load_role checks account ownership and distinguishes an absent row. It validates
length/opcode, revision/provenance, positive diagnostic level and maxHP. The
lossless protocol codec itself remains structurally permissive. These storage
restrictions are custom validity rules, not a recovered native level cap.

commit_role_resources compares BOTH expected role snapshot (possibly absent)
and existing full resource snapshot under BEGIN IMMEDIATE. It checks maxima
agreement, increments revisions, writes full role state and HP/MP, verifies
readback, and commits together. A trigger failure or mismatch rolls back both.
The caller must supply valid current HP/MP; this API does not invent growth,
heal a character or silently choose a clamp rule. Lua remains the rule owner.

Resource-only commits now compare maxima with an existing role snapshot. They
still allow ordinary damage/MP changes but cannot silently diverge from22 state.
Full role updates stage their new snapshot before invoking the same resource
transaction helper, then validate the complete result before commit.

## Verification scope

Repository tests cover absent state, foreign ownership, invalid level/maxima,
initial snapshot, stale resource/role versions, ordinary HP debits, attempted
resource-only max changes and late failure/deletion/revision corruption after
resource writes. They assert both old records and transaction closure after
failure, exact opaque/base-field preservation and untouched account/profile/XP.
Test records are synthetic CUSTOM values, not recovered starting attributes.

This is a storage prerequisite, not live level-up. No Application code invokes
the new role commit yet. Award+XP+level in ONE terminal transaction, persisted
curve identity/unlock state, actual Lua stat growth, client22 live acceptance,
character-list level projection and reconnect remain open. A later integration
must update the role progress snapshot together with XP; it must not reuse stale
progress bytes merely because this lossless row exists. This delivery does not
claim disk/power-loss role snapshot durability or production readiness.
