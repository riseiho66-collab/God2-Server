# Packet Header Research

Real GOD2 header: unknown. The [four-byte placeholder](../../docs/PACKET_FORMAT.md) is a server-development fixture, not PE evidence.

## Questions To Resolve

| Field | Current result | Validation approach |
| --- | --- | --- |
| Length | Unknown | Locate bounded read and receive-accumulator consumption; compare full frames |
| Opcode | Unknown | Follow discriminator into switch/table and verify write-side counterpart |
| Endian | Unknown | Inspect byte operations and non-symmetric sample values |
| Sequence | Presence unknown | Compare consecutive frames and state updates |
| Checksum | Presence unknown | Find computation, covered bytes and failure branch |
| Flags | Presence unknown | Trace branches and optional payload layout |
| Header size | Unknown | Test minimum frame and alternate modes |

Determine whether length includes header, transform envelope or uncompressed size. Preserve initial-handshake framing separately if it differs from post-login traffic. Do not assume fixed offsets just because several packets share a prefix.

Acceptance requires split/coalesced-stream examples, malformed-length handling, maximum bounds and independent samples. Store offset/width/type/coverage/evidence per field, with unknown bytes explicitly bounded.
