# Send/Receive Cross-References

Current result: no recovered caller addresses. [Network xref registry](../../docs/NETWORK_XREFS.md) is authoritative. An import descriptor does not identify an instruction calling that import.

After restoration, locate direct and indirect calls through resolved network thunks. Follow outbound producers toward packet assembly, and inbound consumers toward accumulation, transform, length validation and dispatch. Investigate dynamically resolved APIs and overlapped completion routines as well as synchronous send/recv.

For each candidate record API, instruction RVA, containing function, callers, socket identity, buffer pointer, requested/actual size, return/completion status, direction and sample ID. Capture receive bytes only after completion. Track ownership through queued or copied buffers; a wrapper may submit fragments rather than complete packets.

Acceptance: at least one traced data path in each relevant direction, including partial I/O behavior, with wrapper role supported by bytes and callers. Separate HTTP/update traffic from game traffic. SendPacket and RecvPacket remain proposed analyst names until this evidence exists.
