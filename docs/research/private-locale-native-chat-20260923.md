# Private desktop locale and native chat check, 2026-09-23

The disposable original client was launched on a private Windows desktop by
`God2PrivateDesktop.exe`, through the same `LEProc.exe -run` Simplified Chinese
profile used by the native C++ launcher. The user's input desktop was never
switched. On this Windows 11 Traditional Chinese host, the client displayed
the Simplified town name `枫华镇` legibly in
`artifacts/playtests/private-battle-ui-20260923-01/locale-chat-fixed-self/window-1790166608254782100-03.png`.
Earlier direct launches without LE showed GDI text corruption. This is a
Windows 11 observation; Windows 10 remains untested.

The original client itself sent ASCII `hello` through its normal chat bar on
the private desktop. The private server accepted native opcode `0x2F`, and the
same original client rendered a `hello` speech bubble in the screenshot above.
Before the fix, identical UI input caused `WORLD_FRAME_REJECTED` with a
13-byte decoded record. Metadata logging showed a nonzero four-byte client
header (`80 76 00 00`) while the prior captured sample had all zeros. The
previous zero-only parser was too restrictive. The original `0x4968E0`
producer disassembly also updates only part of that local header, so its four
bytes cannot be treated as a mandatory all-zero constant. The parser now
preserves those bytes without trusting them for sender identity or broadcast
scope; the authenticated character and movement scene remain authoritative.

`recovered_world_records`, `recovered_chat_server`, and
`current_chat_receive` passed after the change. The rebuilt persistent server
at `127.0.0.1:2592` returned its 19-byte handshake and the SQLite
`quick_check` returned `ok`; its diagnostic battle flag remains off. Exact
Simplified Chinese glyph receipt in the original client's chat bubble remains
unverified: direct Unicode and ANSI `WM_CHAR` automation did not generate
reliable Chinese input. Native socket tests do confirm CP950/CP936 conversion
and the original client's mapped receive handler accepts both. This visual
gap is not counted as completed bilingual playability.
