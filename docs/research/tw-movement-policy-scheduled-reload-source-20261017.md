# Scheduled whole-version ordinary movement policy reload — Round443

The actual CUSTOM-0150 DB-selected Taiwan movement path now reads immutable configuration from memory during resource selection, authority adoption and each movement authorization. The existing per-authorize repository SQL has been removed. Initial cache creation retains one strict full-table load; later loads belong to the real Application GAME Scheduler and an explicitly selected reload interval.

## Actual owner, registration and scheduling

Application constructs OwnedOrdinaryMovementPolicyReloads after the existing Database and before Context suppliers, on the same GAME thread. The new LAST Context owner is passed to the actual Sources and StoredSources helpers. Their required chrono::milliseconds interval has no default. After the original strict cache load and profile bind succeed, the helper registers exactly that owning cache with the actual owner and captures the same Binding in the original resource supplier. Registration capacity uses the existing configured max_sessions as an owner-source structural bound, not a gameplay parameter or number of database rows.

The existing50ms Scheduler polls the owner before world.update. Each due source loads at most once per poll and advances its next due time; delayed polls do not cause catch-up bursts. Positive interval, clock conversion/deadline overflow, duplicate registration, configured capacity, thread ownership and reentry are checked. There is no new timer, native packet/command, polling from input, arbitrary interval default or independent database.

## Pure input observations and failure authority

Binding::observe only returns the installed immutable profile observation and never invokes a repository. The actual resource input, Authority::adopt and Authority::authorize use this method. Their remaining grammar, Lua, population, current-ticket, before/after, sequence, fractional credit, clock, position and sole-CAS code remains unchanged. The existing immutable observation pins the policy chosen for the actual transaction. Normal GAME events serialize reload and movement; caught observer reentry poisons/rejects before authority can be granted.

Round442's narrow InvalidSnapshot path remains: only a cleanly ended read with ownership fences may reject candidate contents and retain the exact old whole snapshot. Startup has no fallback. Valid higher versions publish once as a whole table and invalidate old current observations; there is no mixed-version publication or reset of live movement credits/sequence/pose.

SQL, transaction, lifetime, allocation and reentry failures are fatal. Since these now arise outside movement callbacks, explicit reload retires the cache and the owner revokes every registered cache before rethrowing to Scheduler's existing error logger. Scheduler catching an exception cannot leave old cached policy authority available. A failed owner stays closed, never retries SQL, and later input rejects unavailable Bindings. Normal stop revokes before other GAME callbacks/listeners; a late RAII guard revokes on exceptional active-stage unwind before earlier listener/vault/source drains. Before that guard exists no listener or Scheduler has started; the owner still dies on GAME before Database teardown. No virtual callback or game rule runs during pure revocation.

## Qualification and remaining work

Seven existing C++ files change; no new C++/Lua/Python/CMake files. Independent review covers actual Application Context/Scheduler/lifetime, both helper families, same-cache registration, pure input callsites, chosen-version guards, bounded scheduling and fatal revocation. V79 retains172 of179 source pins and updates7; canonical833 to835. This is one real partial source integration, zero complete bidirectional routes and zero packet-count changes. Whole-game denominator and percentage remain unknown.

No build, test, product, native, VM, codec, game SQL, schema, migration, export/import, activation or deployment was executed. This source does not claim a general all-domain reload service, installed movement rules or a default Main native scene host. Actual MySQL8 backend/full consistent lossless export/full constraints/atomic publication/import, other typed game-domain DB consumers, original native movement/rate/reset/scene/client ACK/Main/all-writer/affine IO/atomic fanout/full inventory and complete route inventory remain open.

The full TW100-first/shared CN/four binaryWS/all-system DB goal stays active and incomplete. Preserve453 Traditional-primary/clientBIN skills/current-maximum-HP poison tenth/custom126150/original907/shared64/coins99999999999/stack99/native levels/saves/fonts/IME/auth/text/English DB fields/per-table Chinese TXT.5070 GPU remains authorized when useful and unused.
