# Battle award authority prerequisites

RecoveredBattleExperience describes received-experience DISPLAY fields in
native57-byte89. It explicitly carries no award/persistence authority. Current
RecoveredCharacterRepository stores profiles, resources and positions but has
no battle award ledger or authoritative accumulated character EXP interface.
The live terminal pipeline still sends zero awards; do not relabel it rewarded.

Battle previously marked Finished whenever either side had no living actors,
without retaining the winner. CUSTOM-0007 BattleSnapshot now includes optional
victorious_side. Active battles keep it absent. After a validated hostile action
eliminates a side, the staged snapshot records the surviving side0/1. A valid
living source cannot kill its own side through this damage-only action path.
This uses existing C++ side-elimination rules, not client outcome claims.

The encoder sees the staged result; failure leaves the live snapshot and winner
unchanged. Tests execute actual Lua damage for side0 victory, side1 victory,
encoding failure/retry, one dead party member with a surviving ally, and full
party elimination. This does not assign rewards to every winner or dead ally.

Next: a durable battle identity and atomic exactly-once award ledger, server
policy selecting eligible recipients and amount provenance, then native display
projection only after commit. Keep HP/MP, reward ledger and EXP changes within
one storage transaction; reject mismatched retries and ownership. A display
packet or client control receipt must never authorize a payout. Native EXP
thresholds and monster rewards remain unqualified, and no arbitrary amounts
were seeded by this change. No new runtime reward emission is enabled.
