# Server Chinese script conversion (2026-09-23)

## Connected behavior

`CUSTOM-0029` loads the four bundled OpenCC s2t/t2s phrase and character
dictionaries on the first placeholder chat or NPC talk request. The placeholder world chat
handler validates UTF-8, converts each message for each recipient, and sends
the existing `S2C_ChatMessage` packet. Players choose `/lang zh-CN` or
`/lang zh-TW` in chat. The choice lasts for that world session; default is
traditional. Commands return a private confirmation and are not broadcast.
No saved character, account or world data is changed.
The Lua NPC talk route converts only the JSON `text` and `options[*].text`
values for that player, retaining option IDs and other fields.

This is Chinese **script and phrase conversion**, not semantic translation.
The bundled dictionary files come from installed
`opencc-python-reimplemented 0.1.7`, which includes OpenCC dictionary data
under Apache 2.0. `resources/opencc/LICENSE.txt` and `NOTICE.txt` accompany
the data. The server uses a small C++ UTF-8 longest-match reader, not the
OpenCC library's complete segmentation engine. Dictionary SHA-256 values:

| Dictionary | SHA-256 |
| --- | --- |
| STPhrases.txt | a4de4d2471f73cdb7e5b1b22920139aa4e4bbb1ebeea8f1fc341f988aa75c586 |
| STCharacters.txt | 9207708da9f2e2a248f39c457b2fccad26ec42e7efaf47a860e6900464f4cac5 |
| TSPhrases.txt | b2ef895dd4953b4bb77fc8ef8d26a2a9ca6d43a760ed9a1d767672cfafa6324f |
| TSCharacters.txt | 6b5a0a799bea2bb22c001f635eaa3fc2904310f0c08addbff275477a80ecf09a |

## Verification

`cmake --build build --config Release --target chinese-text god2-server`
passed. `ctest --test-dir build -C Release -R '^chinese_text$'` passed.
`python tools/test_chinese_chat.py` started the built server with an isolated
database, logged in two placeholder protocol clients, switched one to
simplified, and verified that identical chat appeared as `漢字遊戲` for the
traditional recipient and `汉字游戏` for the simplified recipient. It also
verified reverse input and switching back to traditional. An isolated Lua NPC
script containing mixed simplified/traditional text rendered its dialogue and
choice label in the selected language over both live sockets, preserving the
choice ID.
The existing fixture combat socket self-test also passed after this change.

## Original client boundary

The current original GOD2 client does not use the placeholder opcodes
`0x1020/0x2020`. A new live UI input in
`artifacts/runs/native-ui-chat-language-20260923-01` produced a checksum-valid
C2S frame with opcode `0x2F`, 54-byte total length, and CP950 Chinese text.
The exact captured plaintext is retained in
`crypto-private/packet-1803.plain.bin`; its decoded visible sentence was
`遊戲邏輯及原客戶端的技能書使用流程尚未接通`, followed by an ASCII `a`. The payload
includes six bytes before text and a NUL terminator. The text came from the
computer-use input path while probing the original chat bar; it is a real
client producer, but its origin in the input method is not a user-authored
chat sample. That observation preceded the native chat integration below.
NPC mission dialogue currently sends a
resource key in original opcode `0x7A`; the text is client-owned. Other labels
are also embedded in client assets. The original 6F actor name uses bounded
legacy byte fields and a language bit, not the placeholder UTF-8 string.
The UI, quest text, item text and names are still client-owned or separately
encoded and are outside native chat routing.

## Native common chat integration (CUSTOM-0030)

The current client producer at unpacked RVA `0x968E0` constructs opcode `0x2F`
with a two-byte logical length, four opaque bytes, up to 254 legacy text bytes,
and a NUL. The captured 54-byte frame parses with this layout. The original
receiver dispatches variable-length opcode `0x5C` at RVA `0x6AE96`; its common
chat branch reads the sender DWORD at logical offset 5, language/type byte at
offset 9, and NUL text at offset 13. `RecoveredChat.h` now parses/encodes those
layouts. The optional channel producer is separate and remains unsupported.

`Application.cpp` routes accepted common chat from a bound, world-ready
character to world-ready recipients in the same movement scene, including the
sender. The client's actual `0x1C` initializer flag selects the source code
page and each recipient's target code page: `0` for CP950 Traditional, `1` for
CP936 Simplified. UTF-8 OpenCC dictionaries convert the script before legacy
encoding. These explicit code pages do not depend on the host Windows locale.
Ticks and movement coalesced with chat are accepted; unrelated mixed record
batches remain unsupported. Invalid source code-page text rejects the batch
without publishing prepared messages. For valid chat, a character unavailable
in one recipient's code page is replaced with `?` only for that recipient; the
sender remains connected. Display text is capped at 254 legacy bytes at a
Unicode character boundary if phrase conversion expands it. The server logs
replacement and truncation counts without logging chat content. This display
fallback is a custom compatibility policy, not a rule recovered from the client.
The service reads the bound movement state for the scene,
including the selected initial scene.

The rebuilt Release server and `chinese_text`, `recovered_world_records`,
`recovered_world_service`, `recovered_movement_service`, and `session_state`
tests passed. A subsequent two-account, two-socket test
(`test_recovered_chat_server.py`) authenticated distinct owned characters,
sent native world tails with language flags 0 and 1, and verified both
directions of CP950/CP936 delivery by decrypting server frames. A second
case put movement and chat frames in one TCP write and checked both the move
acknowledgement and saved coordinates alongside bilingual receipt. A third
case coalesced movement with invalid CP950 and confirmed that no position was
committed or chat delivered. It is
registered as `ctest -R '^recovered_chat_server$'` and passed. Native visual
handler test `current_chat_receive` executes the original mapped client from
RVA `0x6AE96` to its chat UI insertion call, with only the locale helper,
special-command string probes, and final UI insertion stubbed. It confirms
both language-bit values pass the exact CP950/CP936 text and sender identity
to that call. This is stronger than static layout inspection, but still does
not prove rendering. Native visual receipt on both Windows 10 and 11 has not yet
been verified; that remains the acceptance gate for playable bilingual chat.

The later `encode_display` regression uses CP950 `‧` (U+2027), which Windows
CP936 cannot represent. The two-account native socket test confirms the
Traditional client receives the original glyph, the Simplified client receives
`?`, and the sender can exchange another message afterward. The unit test
checks invalid UTF-8 rejection and truncation without splitting a legacy
multibyte character. Both `chinese_text` and `recovered_chat_server` passed
after this change; original-client visual rendering and a Windows 10 host
remain unverified.

## Same-frame movement and chat ordering

The original world framing permits movement `0x2E` and common chat `0x2F`
records in one frame. A two-account socket regression showed the sender
received its own `0x5C` chat display before the `0x5D` movement ACK (first
frame length 25 instead of 5). The chat route now appends the sender's display
frame after the movement ACK in the callback response. Other scene recipients
still receive their own display frames. The same-frame regression then passed
and checked the durable position at scene15/18,12. This establishes wire order
on the tested route, not visual rendering or a general client operation order.

The retained original-client C2S capture `packet-1803.wire.bin` now also runs
through two authenticated server sockets. Its companion plaintext SHA-256 is
`33c8ad06733951011b36d4c9324f230c84fd32a4240e36da3a6ab0d393afb481`;
the fixture checks the 54-byte native frame, checksum and exact re-encoding
before sending the captured wire unchanged. The server delivers its CP950
sentence to the Traditional client and its converted CP936 sentence to the
Simplified client. This validates a real client-produced outbound packet
through the server route. The original client was not connected as either
recipient in this socket regression, so rendered receipt is still open.

## Persistent service dictionary path correction

The persistent service configuration was stored under
`artifacts/playtests/persistent-launch-20260923-06`, not the standard
`config` directory. `Config::load` resolves the default `resources/opencc`
against the configuration directory's parent. For this deployment that meant
`artifacts/playtests/resources/opencc`, which does not exist. This was a real
activation gap: the first native common-chat message raised `Cannot open
Chinese dictionary: ...STPhrases.txt` and disconnected its sender.

`artifacts/playtests/user-position-20260923-01/bilingual_probe.py` reproduced
that failure with two saved-character copies. The isolated config was then
given an absolute `text.dictionary_root` pointing to the bundled dictionaries.
The same two original-format sockets passed bidirectional conversion: account1
Traditional CP950 received `歡迎遊戲` from account2 Simplified `欢迎游戏`; account2
received `汉字游戏` from account1 Traditional `漢字遊戲`. Both positions and SQLite
integrity remained unchanged. All four dictionary file SHA256 values match
the table above.

The persistent config now has the same explicit absolute dictionary path.
Its previous config and consistent database backup are under
`artifacts/playtests/bilingual-enable-20260923-01`; the database backup SHA256
is `e17e17fa4486d3791d1c760db33df906e88816eee942a59a4e1d322e62b07e5b`.
Only the `text` config field changed. The service restarted on
127.0.0.1:2592 as PID7468; synthetic-account login, world entry and NPC
dialogue passed after restart. The original player position remains59,55/
revision9. The isolated two-account socket proof establishes the deployed
config shape, but actual rendered chat on Windows 10/11 remains unverified.
