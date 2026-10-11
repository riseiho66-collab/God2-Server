# Current client: expired battle command to next round (2026-09-26)

The current deployed `God2.exe` (SHA-256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`)
produces C2S `35/action2` after its first command window expires. This is a
state-qualified finding, not a global meaning for action2: revival and
reconnect also use that action number. The original server's defense rule and
damage reduction remain unknown.

## Native producer

`tests/research/test_current_action2_timeout.py` checks the installed EXE and
pinned mapped image byte-for-byte at three relevant functions. Native
`1117C4/1117FE` copies entry context byte `+41` into the timer seed;
`1175A6/1175AC` grants it as the remaining window. The current `112C37`
negative-time branch clears that timer at `112D8F`; its first-grant path calls
the native `118E50` C2S35 builder with action value 2 at `112E26/112E2A`.
The complete branch qualification and 30-second diagnostic entry context are
in [current-battle-command-window-20260926.md](current-battle-command-window-20260926.md).

## Server integration and client acceptance

`CUSTOM-0035` replaces the previous empty acceptance **only** in the
quest-gated, default-off isolated town battle. After the initial exact
control, an exact actor-0/side-0 action2 with mask `1,0` consumes the expired
command. The configured monster performs one ordinary attack through the
existing C++/Lua rule; the response is validated and HP/checkpoint committed
atomically. A replay or late attack in the same turn is rejected. The client
must then send its separate C2S35/0B receipt before the server issues the next
`88` cycle and `86/5` grant. No defense mitigation is claimed.

The original-client runs used an isolated SQLite copy, loopback port 2598,
and a port-adjusted disposable copy of the current EXE on a separate Windows
desktop. They did not switch the owner's input desktop or modify the installed
EXE or live port-2592 service.

| Run | Current-client observation | Result |
| --- | --- | --- |
| `private-timeout-round-20260926-02` | First action2 received a 156-byte monster response; HP 100 -> 88 persisted. About three seconds later, client sent 0B mask `1,0`. | Identified the remaining rejection: server expected the ordinary attack receipt mask `0,1` and disconnected. |
| `private-timeout-round-20260926-03` | Exact 0B mask `1,0` accepted after action2; round 2 grant sent; client remained alive and sent further native timers/ticks. | One complete expired command and next-round entry accepted. |
| `private-timeout-round-20260926-04` | Two successive action2/0B pairs accepted; grants for rounds 2 and 3; saved HP 100 -> 88 -> 76, resource revision 1 -> 2 -> 3. | Repeated no-input round continuity accepted by current client. |
| `private-timeout-defeat-20260926-01` | Nine no-input rounds persisted HP 100 -> 0 and exactly one loss settlement. The terminal 0B was accepted. The client then sent C2S 1C payload `04 00 00 00`. | Exposed a post-loss mismatch: the older town gate allowed only victory payload `04 00 01 00` and disconnected. |
| `private-timeout-defeat-20260926-02` | A fresh clone seeded HP 12 for one natural no-input terminal action. HP 0 and one `won:false`/XP 0 settlement persisted. The client's `1C 04 00 00 00` was accepted; a later world tick was accepted and the game window remained alive. | Post-loss context and world continuation accepted by the current client. |
| `private-defeat-relogin-20260926-01` | A fresh backup of the settled HP-0 save logged in through the current client, selected the same character, completed world initialization and restored the indoor scene. HP 0 and the one loss ledger row remained unchanged. | Defeated-save relog and world entry accepted; no resurrection policy is inferred. |

The Release `recovered_battle_service` CTest passes the wrong-context, wrong
receipt, replay, late attack, failed-commit retry and next-turn checks. The
three native timeout research checks pass. The custom-design JSON parses.
The one-turn low-HP fixture is explicitly test-only; it changes no live save.
Its `verify.py` rechecks the ordered action2/0B/1C events, one loss ledger row,
saved HP 0, later world tick and SQLite integrity; it prints
`TIMEOUT_LOSS_CURRENT_CLIENT_PASS`.
The relog fixture's `verify.py` checks world-entry order, unchanged HP/settlement
and SQLite integrity; it prints `DEFEATED_RELOGIN_CURRENT_CLIENT_PASS`.

## Boundary

This evidence covers the client-derived timeout producer, one specific 0B
receipt, an isolated monster attack and repeated grants. It does not validate
the original defense mitigation, every other action2 context, player skill
selection in the current client, rendered defeat presentation, resurrection or
HP recovery after relog, or reconnect from an interrupted timeout.
The test's saved HP and one loss ledger row prove terminal persistence; its
checkpoint mode was not enabled, so battle reconnect remains open. Production
combat needs a separately balanced and accepted rule.
