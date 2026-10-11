# GOD2 Server-First Result

Verified run: `artifacts/runs/server-first-cpp-final-01`.

- CONNECTED / INITIAL_S2C_SENT / FIRST_RX / INITIAL_HANDLER / FIRST_TX: true.
- Last accepted state: INITIAL_SEED_EXCHANGE, not login or full session compatibility.
- S2C: 19 bytes, little-endian inclusive length 19, 16 zero seed bytes, checksum 0x4B.
- Initial checksum: sum of each preceding byte plus 0x3C, modulo 256.
- Initial frame is cleartext and uncompressed; no initial opcode is consumed.
- Real recv completions were 1, 1, 17 bytes. Handler 0x410E80 consumed 16 decoded bytes.
- Flags changed 1/1/0/0 to 0/1/1/1, seed handler returned 1, connection routine returned 0.
- C2S: 19 bytes at return RVA 0x10F00. Independent seed/proof/transform derivation
  exactly matches the captured wire bytes; not a manually guessed response.
- Existing C++ server accepted the exact proof in ProtocolMode::God2Recovered.
- Next blocker: the next post-seed S2C contract is unknown. No guessed reply is sent.

## Run

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --network-strike --cpp-server --run-id server-first-next-01 --timeout 20
```

Listener exists on 127.0.0.1:2592 before client startup. The runner performs the
accepted startup and synthetic lab login UI actions. Existing Fixture mode remains
the default; recovered mode is loopback-only, fixed-zero-seed, and refuses fixture
packets or unsupported later input. The zero seed is a lab fixture, not secure
production cryptography. No production authentication is implemented.

Binary packets and JSON metadata are in the run's `network/` directory. The exact
seed exchange is preserved under `artifacts/golden/handshake/server-first-cpp-final-01/`
with scope INITIAL_SEED_EXCHANGE_ONLY. InitialRxPath.json, S2C_FRAME_V1.json and
C2S_FRAME_V1.json describe the limited recovered path. Startup compatibility,
original client files and firewall policy were not changed.
