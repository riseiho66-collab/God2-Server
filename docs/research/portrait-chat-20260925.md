# Owned world portrait and named common chat — 2026-09-25

## Defects and fixes

The local 2A world-entry serializer projected model variants but retained a historical four-byte HUD portrait block. For test1 this sent 6000310c instead of the selected 2000210c. The screenshot's model and selection were correct while the HUD used the retained portrait.

Current mapped image SHA256 149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763 provides the native field correspondence (addresses are RVAs):

- 68370 copies body20..23 into actor+458C.
- ABCED passes that actor block to ABE80.
- ABE80..ABFBC selects the HUD sex/category, hairstyle, face, ornament and color from that block.
- 8067..810B selects equivalent character-selection layers from W20, W22, W23, W24. Their resource category banks differ by 17, while layer indices and color agree.
- RecoveredWorldEntry now supplies C36, zero accessory (matching selection), C38, C39. Model component selectors, coordinates and identity remain unchanged.

Common S2C5C already carries sender identity but native 6AE96 sends the provided text unchanged to its display routes. The server now looks up the selected character under the authenticated account and prefixes its persisted name plus colon/space. The chat request cannot choose another speaker. Message translation remains per recipient; the name is not phrase-translated. Display encoding retains its 254-byte bound and truncates only at complete characters. Names retain the existing profile code-page convention; this change does not establish cross-language re-login for non-ASCII stored names. The supplied string is also passed to the bubble route, so the bubble can contain the name prefix. System welcome text remains unnamed.

## Verification

- Native selection/HUD differential: 42 sex/color/style/face combinations passed, original render-call arguments observed in Unicorn. Draw calls are intercepted: these are not pixel comparisons.
- Original world-entry decoder and actor tests: eight tests passed, including 49 model-variant pairs and portrait bytes reaching actor+458C.
- Real isolated C++ server common chat tests: bidirectional CP950/CP936, distinct sender names, captured native request, movement batching, malformed text, substituted characters and 254-byte long Chinese truncation.
- Town presence: both tests passed, including doors, battle leave/rejoin and named chat after return.
- Indoor visible peer bilingual chat with movement passed.
- Native chat receiver and panel filter: three tests passed.
- Live port2592: test and test1 both authenticated with their original credentials. Both received portrait bytes equal to their character-selection records. Each chat echo and peer receipt contained the correct name prefix. SQLite quick_check returned ok. No accounts/passwords/profile records were changed and no movement was sent.

The large-chat test exposed a test-reader bug (zip stopped decoding after the first 256 key bytes). Its decoder now cycles the key like the native/server envelope; the server did not need an encryption change.

## Deployment

No active player TCP connections were present at replacement. Built build/Release/god2-server.exe was copied to build-town-visibility/Release/god2-server.exe. SHA256: 79BD5EB311E6E8E0E0F3C887BBF8079CB591653D30FCC41999002257AE20EA5C. Live PID16168 listens on2592 with the existing town-chat-welcome configuration and persistent save. A previous executable is retained under artifacts/runs/portrait-chat-20260925/god2-server.before.exe.

Client EXE and launcher were unchanged. No foreground desktop input or graphical capture was performed. Pixel-level acceptance is not claimed. Live result: artifacts/runs/portrait-chat-20260925/live-verification.json.
