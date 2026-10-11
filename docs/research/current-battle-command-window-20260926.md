# Current-client battle command window (2026-09-26)

The current unpacked `God2.exe` (SHA-256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`)
entered the quest-gated isolated battle, but its command menu expired about one
second after the initial status batch. This round connected the missing initial
window byte in **S2C82 battle entry** to the actual client display and later
**C2S35/action2** expiry record. It does not establish a physical skill cast.

## Native source and the corrected field

The pinned mapped client image remains
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
(SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`).
Its `111409..111412` copies the second battle-entry context DWORD into battle
object `+40`; `1117C4` reads byte `+41` and `1117FE` stores it in `+A9E9C70`.
The `117590` grant path copies that value to remaining-time storage `+A9E9C18`;
the `113C14..113C39` path subtracts elapsed clock time from the same storage.
Thus logical `82 00 00 00 00 00 1e 00 00` selects byte value 30 for this
client's first command window. The original server's chosen length and complete
expiry policy are not recovered. `CUSTOM-0033` uses 30 only in the default-off
quest-gated town diagnostic; other entry contexts remain as before.

An earlier attempt set `S2C86/5` logical offsets 5..6 to 30. `1175E9` reads
that WORD for command-window label rendering, but the isolated client still
expired after about one second. That change was removed. It is not the initial
window source in this run.

## Private current-client evidence

Every run used a fresh SQLite backup of the pinned stage-3 save, with only its
cloned position moved to indoor scene 15 (18,12). The current client was copied
with one startup-port byte changed to 2598; the installed `God2.exe` and the
owner's port-2592 service were not modified. The game ran on a separate Windows
desktop. The database and server configuration are in each run directory.

| Run | Entry context / observation | Result |
| --- | --- | --- |
| `private-skill-ui-20260926-13` | Zero context, native `88` at 02:36:33.888, `35/action2` at 02:36:34.928 | 1.040 s; client then displayed automatic defense |
| `private-skill-ui-20260926-14` | `86/5` WORD+5 set to 30 while entry context stayed zero | Still expired after about one second; this server change was removed |
| `private-skill-ui-20260926-16` | Entry context B=`00001e00` | Original battle menu displayed 28 seconds remaining; screenshot is `battle-ui/window-1790362170303312100-03.png` |
| `private-skill-ui-20260926-18` | Same context, no user input, `88` at 02:54:06.303 and `35/action2` at 02:54:37.348 | 31.045 s; client remained alive, no battle settlement or character resource mutation |

The source's `RecoveredBattleEntry::encode_logical` emits the precise nine
logical bytes, and `recovered_battle_bootstrap` checks the byte position. The
Release server used in runs 15–18 has SHA-256
`61d55fad42fde3e0245e7d0650ff64f7af964c19e397f20fa68fc65f04ca5c34`.
The test passed 1/1. The current original client emitted its normal timer
notifications throughout the extended command window.

## Remaining packet boundary

The physical skill path is still unqualified. A targeted private `PostMessageW`
click on the visible skill button left native selection/mode unchanged. The same
injection method left the ordinary attack button unchanged, so these attempts
cannot distinguish unavailable skill binding from battle UI input routing.
Earlier native-function evidence establishes a skill producer and the server
has an isolated skill-settlement rule; neither substitutes for a current-client
physical cast, MP deduction, damage and world return in one live transaction.
Do not mark general battle/skill packet support complete from this timer fix.
The later [action2 timeout playtest](current-action2-timeout-20260926.md)
connects two successive no-input turns through the current client's separate
`35/0B` receipts and server grants; it does not validate the physical skill path.
