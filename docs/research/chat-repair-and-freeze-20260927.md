# Chat repair and owner freeze — 2026-09-27

## Reproduced causes and repair

1. Scene-arrival payload low WORD is the authenticated local character ID,
   not a literal fixture ID 4. Receipt 02000000 from character 2 was wrongly
   rejected after a room transfer. Qualified current native producers and
   owner/config tests now enforce the actual session identity (1..3FFF).
2. Chat before the first standalone periodic tick was rejected because the
   completed world tail had registered pending presence but had not published
   it. Real-client baseline `private-chat-identity23-20260927-01` reproduced
   the disconnect. The chat route now admits already-owned, committed presence
   after world-tail acceptance. Existing native 6F actor binding precedes 5C
   chat so the peer's bubble renderer can find the sender. Pending transfers
   remain gated. Recipients match both area and scene.

This is a general session repair, with no test/test1 or character 2/3 special
cases in production. Name ownership, encoding, language conversion, framing,
movement ACK order, IME, client binaries and database contents are preserved.

## Actual current-client acceptance

Receipt: `artifacts/playtests/private-chat-identity23-20260927-03/run-result.json`.
Candidate SHA256: `3bd85f4c925275427c7de576424b11b0ce75304261e2ee4760a32b5692dc29d6`.

Two different saved identities use a disposable backup of the formal database
and a hidden desktop; only cloned positions are relocated. Current client is
unchanged except the private copy's test port. All owned processes were cleaned
up and the user's input desktop was unchanged.

- Immediate login chat: visible channel 0 and archive contain `test: early2`.
- Room return and immediate chat: both clients contain `test: after-room2`.
- Reverse chat: both clients contain `test1: reply3`.
- Both peer actor bindings exist. Both received bubbles have native renderer
  line count 1 and valid graphic handle 15 (0050A090 consumer fields +56/+A4).
- All other cloned saved rows and schemas were unchanged; live source files
  were unchanged. This is memory readback, not screenshot/pixel verification.
- Three original receiver routing tests pass. Diagnostic owner/door test passes.

All 3 tested messaging scenarios pass (100% of this scoped regression set).
This is not exhaustive all-channel/load testing or whole-game completion.

## Deployment and freeze

Release: `artifacts/releases/native-scene-identity-chat-fix-20260927-02`.
Managed server restarted and listening at 127.0.0.1:2592, PID 31612 at verification.
Executable SHA matches the tested candidate. Config, client and live saved data
were preserved during deployment; no database replacement occurred.

`frozen-chat.json` pins the native chat dispatcher, protocol and scene receipt
rules to this acceptance. `verify_frozen_chat_20260927` verifies them read-only,
and the managed release helper rejects drift before stopping the server.
Only a newly reported defect or an explicit owner instruction authorizes a new
baseline, with fresh actual-client evidence. This is an enforced release gate
and developer rule; it is not an operating-system write permission lock.
