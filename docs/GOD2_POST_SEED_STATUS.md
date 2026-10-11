# Post-seed transition

Scope: exactly one transition after INITIAL_SEED_EXCHANGE. LOGIN remains false.

## Contract

- Immediate wait: VA 0x4131c0, called at 0x413f28 after successful seed connection.
- Session enabled flag +0x2cb8: written to 1 at 0x413f0f.
- Post-seed codec flags (0,4,8,c): (0,0,1,1); +4 changes 1 to 0 through 0x410950 after first send.
- Readiness caller return VA 0x413452; accumulated packet bytes +0x2cc0 = 0.
- Opcode 1 is the only advancing candidate in this immediate wait. Other opcodes are skipped.
- Opcode length lookup: VA 0x401328 points to 0x401216, which returns 2.
- Payload [0]=1, [1]=session[0x754], observed 0x53. These are bytes, not uint16 opcode.
- Handler 0x413270 compares byte 1 with the wait argument; equality reaches 0x4132ce.
- Clear frame: 05 00 01 53 49. Zero-seed transformed wire: 05 00 FE 51 99.
- Header 2 bytes, payload 2 bytes, checksum 1 byte. No compression.
- Frame-local transform uses the already installed key and feedback. No sequence counter is required here.
- Successful return at 0x413f2d has EAX=0. This is not a verified login result.

## Evidence

Contract discovery: artifacts/runs/post-seed-contract-01/compat-events.jsonl.
First actual C++ acceptance: artifacts/runs/post-seed-cpp-01.
Final reproduction: artifacts/runs/post-seed-cpp-final-03.
New C2S: 176 bytes, return RVA 0x12506; semantics UNKNOWN.
Raw test packets remain local. Metadata does not include plaintext credentials.

Seed alias: artifacts/golden/GOLDEN_SESSION_SEED_V1.json.
Versioned post-seed fixtures: artifacts/golden/post-seed/post-seed-cpp-final-03.
Execution-order table: protocol-core.csv inside the run and golden directories.

## Run

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --network-strike --cpp-server --post-seed --run-id UNIQUE_NAME --timeout 20
```

The original god2_recovered seed-only config remains unchanged. New god2_post_seed mode is loopback-only.
The server tracks Connected, SeedSent, SeedAccepted, PostSeedResponseSent. Only the runtime observer can certify PostSeedAccepted; a successful write is not client acceptance.
The next unimplemented C2S is deliberately rejected by the server. No speculative next response is sent.

Final-01 had an incorrect hand-written expected checksum constant in the evidence reducer, not a client rejection.
Final-02 reached acceptance but artifact finalization failed on duplicate run.json creation. Both runs are retained; final-03 supersedes them.

Next blocker: decode and establish the contract of the observed C2S_0002 before selecting another response.
