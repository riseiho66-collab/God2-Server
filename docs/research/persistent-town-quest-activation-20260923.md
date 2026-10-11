# Persistent town guide activation (2026-09-23)

The persistent loopback service at `127.0.0.1:2592` now enables
`development.diagnostic_town.quest_progress`. Its guide NPC spawning was
already enabled. This is the explicitly labeled CUSTOM-0021/0022/0031 town
guide flow, not a claim that all official quests or rewards have been recovered.

Before activation, the persistent database had no native quest descriptions.
The pinned original-client catalog import added 418 missions and 2,014 display
descriptions. SQLite `quick_check` is `ok`. A consistent pre-activation database
copy is at `artifacts/playtests/quest-enable-20260923-01/persistent-before-quest.sqlite`;
the previous configuration is at `artifacts/playtests/quest-enable-20260923-01/persistent-before-quest.server-config.json`.
The importer also made an automatic database backup under `artifacts/db-backups`.
Comparing parsed configurations confirms that the only configuration value
changed was `quest_progress: false` to `true`.

The isolated database clone and server on port 2593 ran
`artifacts/playtests/quest-enable-20260923-01/probe.py`: dual-socket login,
character selection, world entry, guide spawn, NPC sequence 1606→1607→1606,
three C2S85 confirmations, persistent stage/revision 3, and map item 5569/count1.
It printed `QUEST_THREE_STAGES_AND_REWARD_COMMITTED`. The persistent service
then ran `artifacts/playtests/quest-enable-20260923-01/persistent-smoke.py`
with synthetic laboratory account1: login, world entry, NPC spawn, and first
dialogue key0x1234 passed. The smoke test sent no quest confirmation. Its world
entry provisioned an empty slot0 per CUSTOM-0031, with item/count zero; the
quest progress table remained empty and no item5569 reward was present.

The persistent server was restarted as PID18920 and confirmed listening on
127.0.0.1:2592. Actual rendered gameplay after this activation has not been
verified because the user requested internal automation without taking over
their Windows desktop. The previous movement-related timer patch remains
mechanically tested but its visible black-screen outcome is still unverified.
