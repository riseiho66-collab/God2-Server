# 牛轉仙界踏 server integration — 2026-09-30

CUSTOM-0059 implements owner-requested kind0/id150, physical1000%, all living
opponents and one100MP charge. This is a new custom skill, not a recovered native
balance formula. Existing CUSTOM-0058 / skill126 remains separately authorized.

## Qualified native evidence

The current `Data2/Fight/Spg/cbspec2.bin` original record0/73 is 鯨吞亂舞
(raw name 水生-特殊攻擊-3). Its record begins at7928; WORD+0x42 at7994 is
`64 00`, or100MP. Record SHA256 is
`2b4f992ef03b483b4dd1f539cdd4b733dacc085412a190d0aa9ee27ed287105f`.
Reach+0x44 and mode+0x45 are both5. Do not confuse0/77 鯨吞式 (0MP, single
target) or1/129 鯨吞亂舞 (120MP) with this full-target0/73 record.
The MP-field consumer evidence is in `current-skill-mp-gate-20260920.md`.

Native0051EAD0(mode5) returns count1/combined1. Native00518E50 calls0051E910;
case5 sets the clicked side's target mask to0x3FFF. It does not enumerate alive
actors or emit fourteen target commands. The pinned original image
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
has SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The original producer executed successfully against guarded memory for both
sides and multiple clicked slots. The adapter uses one terminal03 command and
the native full-side marker; client byte encoding is not invented.

`tests/research/test_thousand_bulls_command.py` checks the original producer,
0/73 record identity and the narrow150 parser exception. Existing126 retains
its incremental distinct-target grammar. Structural acceptance does not grant
ownership or authorize a friendly-side/full-side command.

## Authority and settlement

`ThousandBulls::authorize` installs a distinct policy key with target limit14.
The service requires one complete opposite-side0x3FFF command, derives all
current living opponents from the authoritative battle snapshot, and rejects
empty/friendly/subset/continuation commands. It ignores dead or absent slots.
Formal Application authorization requires the selected owned deity to contain
saved kind0/id150. No player grants, books or acquisition rules are introduced.

The existing transactional battle route computes physical1000% before its
existing defense/critical policy, charges100MP once and settles each target
once. There is one83/type3 result per target carrying total actual HP lost,
plus the initial caster MP86 and final barrier-delayed88 cycle snapshot. Per-target
HP86 is deliberately omitted: its native handler applies HP immediately before
the four-phase timeline, causing duplicate client-side HP subtraction. At most14 result records reach
the native14-entry actor arrays. The encoder rejects values exceeding the
native signed16 damage range before committing; it does not silently truncate.

Four damage phases are **presentation of that authoritative total**, not four
additional hits. At30fps, ticks70/110/150/190 occur within240ticks (8seconds).
For actual loss D the cumulative amounts are floor(D*20/100), floor(D*45/100),
floor(D*75/100), D; successive differences are the four shown values.
Arithmetic uses64-bit products. The parts sum exactly toD even for low remaining
HP, zero damage and integer remainders. Any positive D retains a positive final
part, allowing death presentation after the fourth phase. The client adapter
owns timed number/HP rendering; the server does not send56 repeated records or
replay the whole animation per target. Client rendering acceptance must be
verified separately from server/unit success.

## Isolation and database preparation

`diagnostic_thousand_bulls_manual` defaultsfalse and requires the existing
strict `diagnostic_shunying_manual` isolation. Its150-only selectable/seed is
temporary; normal126 fixture behavior remains unchanged whenfalse.

The new private config/DB is under
`artifacts/playtests/private-shunying-manual-thousand-bulls-20260930-01`,
loopback port2598. The prior private trial DB was copied with SQLite backup.
It had no native catalog/registry, so only those records and their source
metadata were copied from the already-qualified shunying-production release
snapshot before candidate registration. All gameplay tables were compared
unchanged. Existing temporary character6 retains its prior9999HP/MP; no formal
character resources were changed. Both source file hashes are preserved in
`registration-report.json`. This preparation did not start a server.

The candidate-only registrar reserves122..149 except126, preserves active126
verbatim, adds150 as pending_client_integration, and expands the registry's
target limit to14. It refuses identity collisions and unreviewed dependencies.
The source DB is opened read-only; no production migration was executed.

## Verification and limits

Parent-run compiled CTests passed: `owned_companions`, `shunying_sanshazhan`,
`thousand_bulls`, `recovered_battle_service`, `config`,
`register_thousand_bulls_candidate`, `thousand_bulls_native_command`.
The candidate registrar additionally passed its new active126 preservation
case (4/4 disposable DB tests). The frozen chat gate passed in the parent run.

The broader old `test_current_skill_command.py` suite passed13 cases and had
one source-identity error: its whole native catalog SHA pin predates installed
custom126 in the current client. No pin was weakened and no source restored.
The independently pinned original0/73 record and native executable oracle pass.
This source-fixture limitation is not a claim that the entire old suite passed.

Build targets are `god2-server`, `thousand-bulls`, `shunying-sanshazhan`,
`recovered-battle-service`, `owned_companions` and `god2-tests` (config suite).
Live animation, sound, four-number timing and owner acceptance are pending the
parent's private current-client session. Arithmetic success is not formal
balance approval or production deployment.

## Autonomous TCP fixture follow-up

`tools/skills/thousand_bulls_blackbox.cpp` runs in a separate test executable
on an ephemeral loopback listener. The real Session performs seed exchange,
credential packet parsing, character selection, world tail and world command
dispatch. Its account handlers and battle admission are synthetic and trusted;
it opens no DB and never touches the running private or formal server.

Eighteen scenarios passed: each side with1/2/14 living targets over two casts;
each side rejecting friendly, subset and pre-receipt duplicate commands;
insufficientMP rejection; all14 lethal targets; and a sparse battle where only
the last opposing slot is living. Fragmented frames do not settle early. Each
cast spends100MP, computes31*1000%-13=297 exactly once per living target, emits
one83 total per target without HP86, and preserves the final88 action barrier.
An accepted native0B receipt rearms the next cast without HP/MP changes.

The test compares actual TCP bytes against an independent record-layout oracle.
`artifacts/custom-skills/thousand-bulls/blackbox-server-wire.json` stores those
received frames, including both sides and sparse lethal cases, for the native
adapter oracle. `python -m tools.skills.thousand_bulls_blackbox` records the
executable/log hashes. The CTest target is `thousand_bulls_blackbox`.

Invalid or forged low-MP input fails closed at Session with unchanged state.
This does not establish same-connection recovery after bypassing the native
client's MP eligibility gate. Full Application authentication, database
persistence and native renderer behavior are separately tested by the parent;
the TCP fixture must not be described as that complete acceptance.
