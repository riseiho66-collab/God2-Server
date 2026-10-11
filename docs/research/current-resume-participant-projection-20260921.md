# Saved participant resource projection

DiagnosticBattleParticipants now supports explicit enemy current HP1..150 with
unchanged maximum150. Existing callers default150. A snapshot overload validates
active state, nonzero ID/revision, absent winner, exactly slots0/14, correct owned
player identity, server-owned enemy and existing diagnostic maxima120/80 and150/0.
It projects saved player HP/MP to both scalar and friendly bulk records and enemy
HP to its scalar86. Dead participants or unqualified actor sets are rejected.

The helper consumes a BattleSnapshot, not a RNG checkpoint. Full checkpoint codec
and repository validation remain required before a resume caller invokes it. This
keeps the independently compiled native protocol test free of Battle runtime linkage.
An initial test build exposed that dependency; the boundary was corrected without
weakening packet/resource validation.

Release server and bootstrap target build pass; recovered_battle_bootstrap passes.
Tests verify the pending-run values HP88/MP42/enemy96, parse the enemy record to
confirm max150/current96, and compare all bytes for HP1/42/96/150 against the existing
template. Only enemy current HP changes; wrong identity, extra actor, changed maxima,
dead/oversized enemy values are rejected.

No Application resume call or new native-client run yet. Appearance remains the
explicit isolated template, not recovered universal monster construction. Initial
grant/counter semantics must be qualified separately for a fresh resumed client;
these bytes alone do not authorize replay or prove resumed gameplay.
