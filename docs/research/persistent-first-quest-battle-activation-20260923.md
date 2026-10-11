# Persistent first quest battle activation (2026-09-23)

The loopback service on `127.0.0.1:2592` now enables one completed town-guide
encounter through the existing natural doorway route. The battle gate requires
the authenticated owned character at indoor area 2 / scene 15 / (18,12), guide
stage 3, the source-pinned map item 5569 in slot 0, and no previous settled
CUSTOM-0012 battle. A cold relogin cannot repeat a settled fight. The doorway
back to town remains active after settlement.

This is a clearly labeled custom introductory fight, not a recovered normal
wild-monster encounter. It has one decisive action, zero experience, and the
existing diagnostic HP/MP values; no original damage formula, enemy statistics,
encounter frequency or general combat balance is claimed. It is connected so
the original client can now play through the first quest-linked combat and
return. Broad repeatable combat remains separate work.

The exact ten configuration changes are the eight `diagnostic_battle_*` boolean
flags listed in `artifacts/playtests/quest-battle-enable-20260923-01/prepare-result.json`
plus `diagnostic_town.battle_after_quest` and `door_after_battle`. All changed
from false to true. The previous configuration and a consistent SQLite backup
are `before.server-config.json` and `town-diagnostic-accounts.db` in that
directory. The backup quick check returned `ok`; the pre-activation config SHA256
is `99eb86fd1f188aed5dd461353f1fa7f44ab6af45405f7570c76496a7da68fc7d`.

The candidate configuration started an isolated service on port 2599 with a
database backup and returned the 19-byte native handshake. The current Release
server ran all five `battle-natural-20260923-01/run_all.py` original-format
socket cases: missing reward refusal, settlement, indoor cold reconnect,
town-door-battle-return, and town cold reconnect. Earlier physical original
client testing in `private-battle-ui-20260923-01` clicked a target, completed
this one-round fight, returned to the indoor map, moved, took the doorway to
town, and relogged. That physical test used an isolated save with the same
battle flags; it did not use the persistent player database.

After activation, the persistent service ran as PID 7180 with executable SHA256
`9cecc537ee90d16d574349794374f15a942e287d1a4ce0050f98af39db109f40`
and configuration SHA256
`34e9445bb318cbe20d5780567bfcf5ebbfb142e0e9ac28235c3fc5f09cbd5ec2`.
The production login/world/NPC dialogue smoke passed. The player's character 2
still had town position (2,4,59,55), revision 9; there were zero quest progress
and battle settlement rows. SQLite `quick_check` returned `ok`, and port 2592
was listening. No persistent player battle was triggered during activation.
