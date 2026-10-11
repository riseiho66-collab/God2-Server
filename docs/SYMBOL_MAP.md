# Symbol Map

Addresses use the preferred base 0x00400000 for PE-001. Runtime VA = actual module base + RVA. Unknown addresses are written as unknown, not invented hexadecimal values.

| Preferred VA | RVA | Analyst name | Confidence | Evidence / notes |
| --- | --- | --- | --- | --- |
| 0x00702001 | 0x00302001 | PackedEntryPoint | Observed static | PE-001 optional header, .aspack; not original entry |
| 0x0054A3E8 | 0x0014A3E8 | OEP_Candidate | Unverified | REQ-001; outside raw-backed .text |
| unknown | unknown | NetworkSession_SendPacket | Unknown | Requires send/WSASend data-flow proof |
| unknown | unknown | NetworkSession_RecvPacket | Unknown | Requires recv/completion and accumulation proof |
| unknown | unknown | PacketEncoder_Encode | Unknown | Requires framing/transform write path |
| unknown | unknown | PacketDecoder_Decode | Unknown | Requires framing/transform read path |
| unknown | unknown | OpcodeDispatcher_Dispatch | Unknown | Requires opcode-to-handler branch evidence |

For each future symbol record artifact SHA256, function extent, tool database revision, callers/callees, analyst rationale, sample IDs and counterevidence. Names describe observed roles, not official symbols. IDA/Ghidra maps link here to prevent conflicting address authorities.
