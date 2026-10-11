# TW native19 to common saved-state removal

PHASE1 source integration only. No build, tests, native/client/server execution,
database access, migrations or deployment. Previous round catalog73 made raw
prepared/active shared occupancy mandatory for the conditional CN19 source.
This round adds the corresponding explicit TW Session callback adapter. The
original Application/Session/auth implementation remains unchanged. Historical
acceptance references are retained as records, with the missing receipt noted
below. Native levels, curves, limits, fields and displays stay unchanged.

## Existing authoritative boundary

Current `Application.cpp` lines574..605 attach the existing TW
`Session::RecoveredCharacterHandlers::delete_character` callback. It constructs
RecoveredC2S0002 with mode0, original16-byte account/password and byte167=C8,
uses the actual RecoveredAccountLogin, matches the authenticated account and
stored native slot/name, rejects actual legacy World/Movement occupancy, applies
existing schema52/53 CUSTOM guild-owner policy, then calls legacy erase_owned.
The bundled callback cannot be used as an observing common permission predicate:
it performs deletion itself. Wrapping it after a shared precheck would also omit
common offer invalidation and transaction-time raw occupancy checks.

`Session.cpp` admits native19 only in its actual preselection character route,
requires account/nonselected identity before the game-executor callback, queues
the existing TW02 boolean response, and handles02/04 terminal through03/drain.
It does not have an actual shared-delete callback installed by default.
Historical native producer4152E0, consumer415475 and local deletion/list-refresh
chain40C251/405A67 are retained from current-character-logout-delete-20260927.md.
Its UI13 receipt applies to the historical isolated legacy route, not this new
shared adapter or current dual-client gameplay. Historical native baselines and
zero/candidate reply tails are not silently refreshed or promoted.
The original UI13 run-result.json is currently absent at its recorded repository
path. This round retains the historical Markdown reference and explicitly records
that missing primary receipt; it does not claim the original evidence is complete,
recreate that report or execute a new native acceptance in PHASE1. Necessary
current-native acceptance must be obtained in the later authorized test phase.

## Concrete additive adapter

`SharedTaiwanCharacterRemoval::handler(Sources)` returns the same actual Session
callback type. Explicit complete sources are required: actual AccountRepository,
actual RecoveredAccountLogin, actual common SqliteRecoveredCharacterRepository,
same TW/CN SharedWorldAdmission and bound SharedCharacterRemovalPresence, plus
an actual policy preparation supplier. It never creates independent CN storage,
defaults to an empty registry or falls back to the bundled legacy callback.

The new read-only `RecoveredAccountLogin::owns_repository` comparison requires
that actual Login belongs to the declared common account repository. The presence
observer already requires the exact common character repository. The host must
bind these to actual Application instances and the same TW/CN preparation
registry; declaration identity is not proof of Application hosting. Actual objects
must outlive the callback and all work stays on the serial game owner.

The handler checks the actual connection is Authenticated, nonselected, not ready
and not closing, binds its actual Session object/id/account, and rejects reentrant
operations. It reuses the exact existing TW login mode0 semantics, so local account
registration stays disabled even when Login allows mode4 elsewhere. Existing exact
identity/ASCII fallback/password verification is reused, not rewritten. No display
locale, CP936/CP950 conversion or arbitrary account registration is introduced.

Owned slot/name must resolve to one complete common stored character snapshot;
ambiguous duplicate slots fail instead of choosing iteration order. Raw names are
compared as bytes with the original14-byte stored-name domain. The operation uses
a fresh server-created Attempt pointer and common account/session/character/slot;
credentials are never placed in Scope, policy, admission, SQL or evidence. This
pointer is an in-process lifetime identity, not persistent semantic replay proof.

The mandatory preparation supplier observes the copied common row and returns an
actual Current predicate. No supplier receives credentials or incoming name as
authority. Common raw prepared/active and legacy occupancy are checked before
and after preparation, and the complete stored row is read again before SQL.
Required policy and actual connection identity are checked both before and after
policy at each BeforeErase/BeforeCommit phase through the existing concrete
SharedCharacterRemoval writer. Full row CAS and all TW/CN offer invalidations
remain inseparable from the transaction. BeforeCommit must not infer permission
from a root/guild row already staged absent; the actual guild/rule/replay owner
must retain and qualify its own proper snapshot/generation.

Successful COMMIT/apply returns committed truth directly into the existing
Session bool callback; no post-COMMIT veto is turned into a fabricated failure.
TW02 framing, queue ownership and02/04->03 handling stay in existing Session.
This round does not qualify every23-byte02 tail, introduce a new native issuer,
claim queue completion/native receipt, or add post-COMMIT crash/replay recovery.
Actual failure policy still needs its native source; absence alone never permits
deletion, and TW CUSTOM guild constraints are not imported as CN native rules.

## Hosting and remaining scope

The actual dual-client host must explicitly assign the returned handler to its
TW RecoveredCharacterHandlers before constructing actual Sessions, supplying
real policy authority and all common registries. This source increment does not
install it into frozen production Application, alter the legacy accepted route,
start a listener, bypass native reply qualification or claim global TW-initiated
cross-version deletion safety. Future hosting must preserve existing schema51/52/53
guild-owner/authentication constraints and connect the actual native rules, rather
than supply a default-true predicate. Cross-process exclusion and semantic durable
operation/receipt/recovery remain open, as do CN1E and full02/03 native suppliers.
No new table/schema, save-policy expansion, world-entry default, numeric/level or
client/font changes are made. The SQL writer/cleanup policy is unchanged.

## Accounting

One new conditional TW partial owner chain; two source associations in the exact
character-connection-preselection phase: TW C2S19 and its existing S2C02 return
path. They are not new opcode values or completed whole native reply variants.
TW unhosted source associations become10/10 distinct phase values and partial
owners3; CN remains71/53 and29 owners, total32. No new complete bidirectional
route; global packet/route denominator and completion percentage remain null.
