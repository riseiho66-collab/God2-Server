# Packet Encoder Research

Client encoder address and real outgoing schemas are unknown. The mock encoder contract is length = payload bytes + 4, then little-endian length/opcode; see PACKET_FORMAT.

Trace each UI/domain action to serializers, then to the transport wrapper. Record allocation and final output size, field write order, string encoding, optional fields, checksums, sequence updates and cipher/compression calls. Capture buffers at each transform boundary to determine order rather than assuming compression precedes encryption.

For a candidate function record RVA, source hash, input data, output bytes, callers and error paths. Distinguish framing from gameplay serialization: one wrapper may serve many opcodes.

Acceptance: a documented input yields matching output on an independent sample, including state-dependent values. Confirm maximum length and overflow behavior. A mock encoder/decoder round trip is not proof about the client's encoder.
