# C2S_0002 -> S2C_0003

Accepted: opcode 0x1d response enters RVA 0x14091, both string comparisons return zero,
copies 172 bytes, consumes the packet, resets the wait timer. The client still awaits a terminal result.
No character/world claims. LOGIN means a proven credential request, NOT authentication success.

## Contract

- Wire length 176, clear uint16 header 176, transformed payload 173 plus checksum 1.
- C2S opcode is one byte, value 4. Existing zero-seed key/feedback applies per frame.
- Builder RVA 0x13e10, input-copy RVA 0xb010, send-return RVA 0x12506.
- Payload [1,25): account input, bounded 24-byte copy, last byte forced NUL.
- Payload [25,157): password input, bounded 132-byte copy, last byte forced NUL.
- Payload [157,165): copied client struct, earlier writer UNKNOWN.
- Payload [165,167): GameSN_God2.DAT decimal value, uint16 below 1000 or zero fallback.
- Payload [167]: constant 0xc8.
- Payload [168,173): copied client struct, earlier writer UNKNOWN.
- All 176 wire bytes are assigned ranges; 13 copied bytes retain unresolved earlier provenance.
- A/B captures change only the controlled account. Logical differences: offsets 6 and 8.
- Both runs have captured logical bytes exactly matching independent wire decode.
- S2C opcode 29 uses the same 172-byte structure; both input strings must match.
- Only the observed zero-flags branch is supported; other flag values are refused.

## Evidence

Frozen request: artifacts/golden/post-seed/C2S_0002.bin and .json (exclusive creation).
Write/dependency/differential maps: artifacts/contracts/c2s0002-v2.
First client acceptance: artifacts/runs/c2s0002-s2c3-01.
Final run: artifacts/runs/c2s0002-s2c3-final-03.
Golden transition and updated protocol-core.csv: artifacts/golden/c2s0002/c2s0002-s2c3-final-03.
Final-01 failed evidence finalization on an unsequenced UI event; final-02 and final-03 supersede it.
Raw/logical fixtures contain synthetic test credentials and remain local. No plaintext credentials are printed in metadata.

## Run

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --network-strike --cpp-server --post-seed --c2s-strike --s2c0003 --lab-case A --run-id UNIQUE_NAME --timeout 20
```

New god2_c2s0002 mode is loopback-only. Existing seed/post-seed configurations stay unchanged.
The C++ parser rejects wrong length, opcode, checksum, string boundaries, constant and config range.
It preserves unknown bytes. Fragmented TCP input is accumulated before parsing, bounded at 176 bytes.
Server RequestReceived/ResponseSent states never imply client acceptance; debugger evidence qualifies that separately.
No credentials are authenticated by this research acknowledgement. No production account service is implemented.

Next blocker: terminal response contract; do not send speculative completion packets.
