# Protocol Lab

PLACEHOLDER - waiting for real GOD2 reverse engineering result

These opcode values are placeholders. They are NOT verified GOD2 opcodes.
Replace them after reverse engineering God2.exe.

The current frame is a little-endian uint16 total length followed by a
little-endian uint16 opcode and payload. Total length includes the four-byte
header, with a maximum of 65535 bytes. Payload scalars use little endian;
floats use IEEE 754 binary32. Strings have a uint16 byte count followed by
exactly that many bytes (embedded NULs are preserved). Fixed strings consume
the entire field, return text before its first NUL, and are zero-padded on
write. Oversize fixed strings are rejected, never silently truncated.

## Replay

The parent build supplies the executable target for `src/tools/replay_main.cpp`.
Example invocations, assuming its target is named `protocol_replay`:

```text
protocol_replay "07 00 01 10 aa bb cc"
protocol_replay --file tools/protocol_lab/sample_packets/heartbeat.hex
```

No arguments reads hex text from stdin. Hex may be contiguous or separated by
ASCII whitespace between complete bytes. Prefixes, punctuation, comments,
odd digits and non-hex characters are rejected. Input files are hex text,
not binary captures. Exit status is 0 for success and 1 for errors.
Empty input is a valid empty stream. Output includes length, opcode and payload
hex for every complete frame, plus an explicit reason on failure.

`ProtocolReplayTool(ProtocolSpec&)` borrows its spec. `parse_hex(string_view)`
returns `vector<uint8_t>` and throws `runtime_error` on bad syntax.
`replay_hex(string_view)` returns `ReplayResult` with `status` (`DecodeResult`),
`packets`, `lengths`, and `remaining_bytes`. `print(result, ostream&)` prints it.
Lengths describe header plus decoded payload under the identity placeholder
protocol; wire-length reporting must be extended when transforms are recovered.
Each replay starts a fresh input buffer. A truncated final frame is a replay
error because the supplied capture has ended; the streaming decoder instead
returns success and retains partial input for the next receive.

The decoder appends packets to the supplied output vector. On an invalid frame,
previous complete packets remain delivered and the invalid bytes remain buffered.
The caller must close or reset that stream rather than retrying unchanged bytes.
CryptoPipeline and CompressionPipeline accept only the exact mode `none`.
Their identity operations make no claim about actual GOD2 transformations.

Tests expose `void test_packet()`, `void test_decoder()`, and
`void test_protocol_replay()` to the parent harness, without defining a main.
