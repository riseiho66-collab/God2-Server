# Packet decoder DLL

Binary: `build-strike-lab/Release/God2Probe.dll` (debugger-host extension).

`!God2Probe.packet wire_address length codec_address ["output_base"]` reads the x86 target's
256-byte key at codec+0x2420 and feedback at codec+0x2556, then prints a
`GOD2_PACKET` JSON record. It does not write target memory.

The runner invokes this command automatically for complete sends returning at
0x412506, where ESI is the recovered codec pointer. Records are saved as
`packet-decode-NNNN.json`. The RX observer also captures before decode at
0x410A30 and correlates actual plaintext/checksum return at 0x410A3E. TX input
is captured at 0x410690 and compared at the known send return. These new live
hooks have only orchestration tests, not a fresh-client qualification.

An output base saves paired `.wire.bin` and `.plain.bin` files (CREATE_NEW,
never overwrite). The runner stores them under `crypto-private`, with per-packet
JSON and `protocol-core.csv` from FrameParser and identification-only
OpcodeDispatcher. The placeholder gameplay dispatcher is never invoked.
Credential plaintext exists only in binary research evidence, not JSON/logs.
This directory is not encrypted and does not establish a new ACL boundary;
treat its binary files as sensitive evidence. Key identity is SHA-256, not key bytes.

Supported: verified uncompressed framing, 4 through 258 bytes, exact declared
length, recovered transform and checksum. Unsupported compression, bad framing
or checksum mismatch fail closed without plaintext. Known 176-byte credential
frames have their plaintext redacted in debugger logs; key bytes are not logged.

The exported `God2DecodePacket` also accepts explicit wire/key/feedback buffers
for offline use. `God2EncodePacket` implements the instruction-proven inverse
for valid clear frames. Negative return values leave output buffers untouched.

Actual DLL tests verify the captured six-byte frame:

```text
wire:  06 00 a3 a3 fd d5
plain: 06 00 a6 00 00 d8
```

Five DLL tests passed, including frozen prefix packets and rejection cases.
Live debugger command integration and a new client session have not yet been
qualified. This does not establish a post-selection response contract.

## Session-global recovery

Per-packet brute and automatic checksum-failure fallback are disabled.
The legacy `God2BrutePacket` ABI returns `RECOVERY_MANIFEST_REQUIRED`, tested=0.
Use the runner's offline entry, which returns before any client launch:

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --recover-crypto --crypto-manifest private-session.json --crypto-output artifacts/crypto/unique-run
```

`God2RecoverCrypto` receives bounded JSON. Required fields are session_id,
model=`packet_reset`, tx_key_hex/rx_key_hex (256 bytes each), packets. Each
packet has direction, wire_hex, state_before/state_after (directional labels),
and optional known_plaintext_hex, allowed_opcodes, constants [{offset,value}],
expected_state_before. The CLI additionally requires increasing seq identities.
At least one exact plaintext oracle in each direction is required before search.

BruteCandidateEngine searches 65,536 states per direction using 4..8 CPU
workers, thread-local vectors and no JSON in the hot loop. Each packet hard-prunes
the same survivors. TX/RX are kept separate. Reports contain rejection counts,
per-packet survivor counts, state/constraint flags and differential offsets.
No candidate plaintext is serialized. At most 256 surviving parameter records
per direction are serialized, with explicit count/truncation metadata.
Equivalent rotated keys with identical feedback are identified as mathematically
equivalent states, not a request for more indistinguishable packets.

The exact 6-byte oracle is a permanent regression. Historical same-session replay
`artifacts/crypto/decrypt-strike-02/decrypt-candidates.json` reports C2S 65536->1->1
and S2C 65536->15->1->1->1. Status is UNIQUE_CANDIDATE, CRYPTO_RECOVERED=false.
Opaque state labels are caller assertions, not proof of runtime parser behavior.

Fresh runtime qualification is intentionally not implemented as an automatic
promotion from supplied booleans. The current auditor checks evidence references
but always returns RUNTIME_VALIDATION_REQUIRED until a qualified capture adapter
binds fresh key/connection, both directions, multiple packets and actual opcode/
state acceptance. The UI transport is unavailable and the server profile still
uses the zero-seed fixture. See GOD2_CRYPTO_RUNTIME_QUALIFICATION.md for gaps.
