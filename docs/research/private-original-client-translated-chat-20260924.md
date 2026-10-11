# Original-client bilingual chat receipt with player presence (2026-09-24)

An isolated Windows desktop hosted the disposable original client at port 2598.
The client used its Simplified Chinese Locale Emulator profile. Production
port 2592 and its SQLite save were not changed. The test server and database
were cloned under `artifacts/playtests/private-visibility-chat-20260924-01/`.

The initial town fixture accepted CP936 common chat from a second authenticated
character, but the original client showed no other character or bubble. The
town configuration had no player-presence publication. An attempted duplicate
login as the recipient was correctly rejected by character ownership.

The next isolated fixture used the existing `diagnostic_player_visibility`
mode, its required indoor scene 2/15 and a dedicated database. Its two saved
laboratory characters were placed one tile apart in that copy. The original
client entered the indoor scene and continued sending normal five-second ticks.
A second authenticated native-protocol socket received its original-format
`0x6F` peer-presence record, sent CP936 chat, and received its `0x5C` echo.
The original client screenshot `chinese-live/window-1790205349211229500-03.png`
shows a legible Simplified Chinese `汉字游戏` bubble.

The same peer then reconnected with the Traditional language flag and sent
CP950 `歡迎遊戲`. Its `0x5C` echo retained Traditional bytes. The original
Simplified client screenshot
`translated-traditional/window-1790205423895270800-03.png` shows the
converted `欢迎游戏` bubble. This establishes source CP950 -> server conversion
-> CP936 recipient bytes -> original-client pixels for this indoor laboratory
path. The input source was a synthetic native-protocol socket, not a Chinese
IME action in the original client. Windows 10 was not involved.

`test_visible_peers_exchange_converted_chat_and_keep_movement` now tests the
real server with two distinct authenticated accounts, `0x6F` presence,
CP950/CP936 bidirectional `0x2F`/`0x5C` conversion, a `0x5D` movement ACK,
`0x5E` peer movement, chat after movement and SQLite quick_check. It passed.

Later on 2026-09-24, isolated town mode gained opt-in same-scene player
presence with door and battle lifecycle handling. The new socket and SQLite
evidence is recorded in `private-town-player-presence-20260924.md`.
This visual proof does not imply that every client packet or gameplay system
is connected.
