# Chinese chat input boundary, 2026-09-24

The original client ran through its Simplified Chinese Locale Emulator profile
on a private desktop against an isolated copy of the port 2592 configuration
and SQLite save (`artifacts/playtests/private-chat-native-20260924-01/`). It
rendered the Simplified town name correctly. The original game window is a
Unicode HWND, while the external Python input sender has Windows ACP 950.

Three synthetic window-message paths attempted `测试` through the client chat
bar: CP936 bytes via individual ANSI `WM_CHAR`, Unicode `WM_CHAR`, and Unicode
`WM_IME_CHAR`. The speech bubbles showed replacement/question-mark glyphs in
the retained screenshots, so these targeted messages do not establish a
faithful Chinese keyboard/IME input path. No conclusion about normal human
IME input or a client rendering defect follows from this automation result.
The earlier captured original-client CP950 Chinese `0x2F` packet and its
two-language socket replay remain valid separate evidence.

`recovered_chat_server` passed 1/1 after the current server build. It checks
both CP950 and CP936 chat routing, translation and output wire bytes, including
the captured original-client Chinese packet. It is explicitly a socket test,
not original-client visual acceptance. Exact Simplified and Traditional chat
glyphs in an original-client speech bubble remain open. The private test
processes were stopped; the port 2592 server stayed live.
