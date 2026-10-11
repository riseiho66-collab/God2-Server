# Round232: joint owned inventory/native equipment source transaction

This is PHASE1 source integration only. No build, test, native execution,
codec, game, database access, SQL execution, migration, restart or deployment
was performed. TW-first work continues; common CN/web support is preserved.

## Concrete source change

`SqliteOwnedEquipmentTransaction` uses the actual shared Application custody
and native equipment writers, on their identical SQLite connection and game
thread. It rejects unrelated account/character readers, borrowed transactions
and reentry. It owns one BEGIN IMMEDIATE and one outer COMMIT for both whole
populations. This is the atomic storage coordinator missing after230/231;
calling the two standalone public commit methods in sequence is not used.

The existing writers now share private validate/stage implementations with
the coordinator. Their public replace methods still own their transactions,
reject borrowed transactions and return only durable receipts. Private stages
never call an issuer, start/commit a transaction or return public staged tokens.
They retain the original whole owner CAS, permanent globally unique identity
and acquisition receipt registry, immutable item definition/stackability/origin,
strict revision transitions, complete versioned aliases and complete native
1215-byte witness. No canonical ID is derived from native raw20/key/slot.

The coordinator accepts optional complete expected snapshots for each store
and a complete next pair. Both next snapshots must have the identical full
common character root. Existing individual validity/transition checks remain
mandatory. Inside its transaction it compares both stored expected tuples,
the actual common root population, saved position and absence of a pending
battle. Its genuine issuer returns the entire exact next pair at Prepared,
BeforeWrite and BeforeCommit. The final phase occurs after BOTH populations
have been staged and compared. Detected issuer reentry, autocommit changes or
total-change differences poison the operation; no bool-only Current callback
supplies the state. The issuer is a trusted synchronous source with an explicit
no-SQL/no-transaction-operations contract. These observations do not prove an
arbitrary callback never rolled back and opened another transaction internally;
this API is not isolation for arbitrary same-connection SQL callbacks.

Both immutable individual snapshots and a private coordinator-identity receipt
are allocated before the only COMMIT. Failure or exception before that COMMIT
rolls back the whole pair. No provider, reload, retry or allocation occurs after
the durable COMMIT. Copies/moves preserve both valid owned receipts; callers
cannot manufacture a joint receipt from independent single-store receipts.

Joint committed_current owns one consistent read transaction for both full
tuples and current common root/position/battle state. It does not call two
separate public committed_current methods and combine potentially unrelated
observations. Coordinator and both underlying writer identities must match.

## Actual publication/source composition

The existing SharedTaiwanNativeEquipmentPublicationSource has a joint-receipt
construction path. Every source reread in the existing held DA publication
endpoint now checks the joint current pair when that path is selected, plus
its existing actual ready presence lease, actor handle, saved position and
common/visibility ownership checks. It retains the coordinator and complete
receipt strongly. The older delivery-witness-only path remains explicitly
delivery-witness-only, with its original behavior.

StoredSources::owned_equipment_transaction builds this coordinator from the
actual same Application Context's two readers/writers, after identity checks.
StoredSources::owned_equipment_publication_factory retains that exact
coordinator, actual common world and borrowed account/character readers, never
the Context. It accepts a future joint post-COMMIT receipt on the game owner.
Construction performs no reads/writes or schema operations; both existing
explicit storage flags must be supplied. Ordinary Main remains opted out.

## Native provenance and remaining gaps

Native baseline remains149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
The complete equipment witness is50 actual24-byte cache rows (including the
unknown prefix1..3 of every row) followed by an actual full DA15. It is not a
packet and is not inferred from additive3B/41 or a raw20 item instance.

Retained231 native work:432 bytes/137 instruction sites, two bounded spans,
12 opaque CALL boundaries. A full24-byte row may reach49B850 under actual
mode gates. Mode0 skips38..41; mode1 skips30..37/42..45/46..49, so slot34 in
mode1 skips that direct CALL. Receiver helpers remain opaque. This is no proof
that an item-to-DA mapping is globally absent. No new native bytes/opcode or
complete route are claimed by this transaction work.

Still OPEN: genuine acquisition/drop/quest entitlement and common definition
source; actual authenticated C28 dispatcher/input freshness/action and equip/
unequip/slot/Lua rules; exact native item-to-fullcache/DA producer; complete
ordered inventory replies; source/self-local DA and mixed-version fanout;
full2A/once-issued admission/lifecycle/Main suppliers and full TW route
denominator. The readonly231 typed Request is not proof of a fresh network
action. The issuer contract remains a mandatory genuine supplier; its API is
not a fabricated implementation of those gameplay rules.

Atomic storage makes this particular source chain more complete. It does not
make the full equipment route, whole opcode or game complete. Joint snapshot
revision and provenance do not invent an extended wire profile. Stack99 applies
only to qualified stackable common instances; native additive signed30 gates,
bag30 slots, unstackable/PET semantics and numeric expansion remain separately
tracked. Preserve saves/chat/IME/auth/portraits/EXEs/native fonts/conversion/
levels and all STOP/render/refresh helper boundaries.

CUSTOM-0092 remains the label for shared server identity/custody storage policy.
This coordinator adds transaction mechanics to that policy; it introduces no
gameplay rule, item definition, mint entitlement, native mapping or CN custom
game permission. Historical custom registry entries are unchanged.

## Accounting

New C++ files2; modified existing C++ files8. Added one partial source segment;
cumulative218. New complete bidirectional routes0. TW/global completion and
full directional/state/variant denominators remain null. Existing packet index
counts are unchanged. Static source review/accounting is not runtime acceptance.
Full exact before/current sources, diffs, agent deliveries and metadata are
retained outside DesktopGod2 under the232 task archive; old231 seals stay intact.
