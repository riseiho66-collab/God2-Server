# Packet Decoder Research

No real decoder address or algorithm is recovered. Trace receive completion into any persistent accumulator and follow reads until a packet object or handler invocation is produced.

Record minimum bytes needed, peek versus consume behavior, declared-length coverage, maximum frame, header variants, transform order, checksum/sequence validation and invalid-frame policy. Determine whether decompression output has an independent bound. Observe how trailing bytes and partial frames survive the next receive.

Required fixtures: every header split, a payload split, concatenated frames, an incomplete trailing frame, invalid short length, oversize length, truncated stream, and transform failure if applicable. Record consumed byte count and residual buffer for each.

Acceptance: held-out raw streams decode to the observed handler inputs with no accidental loss of trailing data. The research must distinguish socket reads from logical packets. Mock behavior is documented separately in PACKET_FORMAT.
