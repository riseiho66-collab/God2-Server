# Network Cross-References

Status: no executable call-site xrefs recovered. Static import presence alone is not a caller or packet direction. PE-001 exposes ws2_32.dll ordinal 12 and wininet.dll InternetOpenA; neither establishes game packet construction.

| API target | Caller RVA | Analyst function | Purpose | Direction | Status |
| --- | --- | --- | --- | --- | --- |
| socket | unknown | unknown | Transport creation to investigate | N/A | Unresolved |
| connect | unknown | unknown | Endpoint connection to investigate | N/A | Unresolved |
| send | unknown | unknown | Outbound bytes to investigate | C2S candidate | Unresolved |
| recv | unknown | unknown | Inbound bytes to investigate | S2C candidate | Unresolved |
| WSASend | unknown | unknown | Scatter/gather send to investigate | C2S candidate | Unresolved |
| WSARecv | unknown | unknown | Receive/completion to investigate | S2C candidate | Unresolved |
| InternetOpenA | unknown | unknown | Internet session initialization | Unknown | Import only |

## Capture Record

Record API/module identity, caller RVA and instruction, actual module base, socket/session correlation, return value, buffer address/length, requested versus actual byte count, completion point for overlapped I/O, call stack, transport endpoint role, and sample ID. Collect outbound bytes before call and inbound bytes after successful return/completion. A pending WSARecv buffer is not received data.

Trace buffer producers/consumers to distinguish raw transport wrappers, framing and business serializers. Include partial sends, repeated receives, reconnect and close paths. Do not label updater traffic as gameplay based only on timing.
