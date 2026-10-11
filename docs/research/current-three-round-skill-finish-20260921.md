# Three-round diagnostic skill completion

Configuration now permits terminal diagnostic rounds3 only with isolated skill
settlement and animations. One-round terminal retains its explicit1000% power;
three-round terminal uses existing CUSTOM-0012 power150%, fee8, no criticals.
No production turn rules, rewards or native damage formulas are claimed.

Run native-player-three-round-skill-finish-20260921-01 reached two skill rounds
but rejected native control action0B after the second retaliation: target masks
were1/0 rather than the previously fixed0/1. Native packet-decode-0607.json
contains exact logical35000b0000010000000000000000000000. It is a captured
control notification, not authorization for arbitrary target-mask changes.

Run -02 qualified the third skill and five animations but the final control
retained that same friendly mask (packet-decode-0642.json). The service now
uses an explicit default-off diagnostic_three_round_friendly_receipts policy
only on this Application three-round path. It requires owned session, isolated
single-action policy, retaliation, action already received, one standalone
control and internal revision5 OR finished revision6. Other revisions retain
the existing mask. Replays remain rejected. This is narrow runtime evidence,
not a general original turn/ack rule. Both failed runs remain unqualified.

Authoritative run -03: NATIVE_MOVEMENT_PATH_COMPLETED; three native skill
commands; enemy HP150 ->96 ->42 ->0; player HP100 ->88 ->76; MP50 ->42 ->34 ->26.
Exactly8 scalar updates occur (three costs, three enemy HP, two retaliations).
All five animation batches complete1/1 without fallback. Original result panel,
world return and three-step movement complete. Disk resources are HP76/max120,
MP26/max80, revision4, CUSTOM-0012. No final retaliation occurs.

Unit tests cover exact second and finished-third receipts, wrong masks at
revision3/5/6/7 and replay rejection. An initial test accidentally retained a
second living enemy and correctly failed its finished assertion; it was fixed
to construct a two-participant terminal fixture, not by weakening the assertion.
Native evidence regression checks the full scalar sequence and persistence.

Scope remains owned-server native-function probes, not physical UI/visual
acceptance or production balance. Result awards remain zero. New-character
starting rules, sustained encounters/recovery, normal battle initiation and
full gameplay remain open.
