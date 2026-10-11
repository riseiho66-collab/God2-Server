# Town common chat channel (2026-09-24)

The running 2592 service already had authenticated common chat: original-client
C2S `0x2F`, server S2C `0x5C`, CP950/CP936 conversion and same-scene delivery.
The prior live log at 08:57–08:59 recorded 92 movement records and 31 ticks,
but no chat records (variant 13). No server-initiated common chat was emitted,
so an empty lower-left channel during solo movement was expected.

The original 2.40.83 receiver at `46AE96` calls the actor bubble routine
`FB690`, then routes ordinary category 0 to panel routine `475E00`. The
targeted original-code regression now crosses both calls. `475E00` tests the
client's common-channel visibility flag at its settings byte `+449C`, bit 4;
when set it calls `47DE00` with category 0, color `00FFFFFF` and the message
text. When clear it skips panel insertion. The test stubs UI callees and
does not claim rendered pixels or the user's current filter setting.

CUSTOM-0034 adds one localized common-channel welcome on the first accepted
world tick in opt-in diagnostic town mode. It uses reserved sender ID
`0x7FFFFFFF`, preserving player identity and missing the original actor bubble
lookup, and sends the language-specific legacy bytes in the current
S2C `0x5C` envelope. It does not repeat on later ticks. An isolated socket
test with the same player-visibility mode as the live service confirmed CP950
and CP936 recipients each receive one correct line. Native receiver and
panel-filter tests, config tests and related movement/door tests passed. The
native no-actor lookup test executes original `FB690` with a 128-slot empty
actor table and confirms this reserved sender returns before bubble rendering.

## Common-channel preference default fix

The owner's current screenshot shows text in the actor bubble with an empty
lower-left chat panel. The matching native receiver test proves these are two
separate display paths: the `0x5C` handler creates the bubble first, then the
panel drops category 0 when option bit 4 is clear. This identifies a client
preference cause for the reported symptom; it is distinct from the server's
common-chat route.

`God2LauncherSupport.cpp` now patches the generated unpacked-client image at
the verified preference-load path (`RVA 0xF5041`). It preserves the loaded
channel bits and ORs in only `0x10` before the original preference refresh, so
common chat is enabled by default and other filters remain unchanged. The
patch is part of the generated `God2.exe` image; it adds no injected DLL or
separate runtime patch file. The support helper retains the original unpacked
client hash check, and its file version remains `1.0.0.0`.

The helper was rebuilt and installed with embedded loopback endpoint resource
902 preserved. A generated client from `/self-test` was checked structurally
and its trampoline executed in an isolated x86 emulator: saved flags `0x00A5`
became `0x00B5`, the original refresh call ran, and execution resumed at the
original continuation. `tests.research.test_current_chat_receive` passed 3/3,
including the native channel-filter and both-language receive paths. The
owner's current `God2.exe` was replaced while no game process was running;
`God2.unpacked.exe` and the selected zh-TW setting were preserved. The next
client launch regenerates language-specific images with the same preference
fix.

The latest screenshot itself does not expose whether its bubble came from the
server response or the client's local send preview. Therefore this patch
addresses the proven panel filter, while rendered confirmation of a sent
message on the newly patched executable remains an open live acceptance step.

The previous live process had no connected clients when it was stopped.
The corrected `build-town-visibility/Release/god2-server.exe` Release binary
now listens on 127.0.0.1:2592 (PID 16396) with
`artifacts/releases/town-chat-welcome-20260924/server-config.json` and the
existing persistent SQLite database. Startup completed, SQLite quick_check
is `ok`, and the Island01 experimental route remains disabled.
