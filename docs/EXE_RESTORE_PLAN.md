# Executable Restore Plan

Status: planned dynamic research only. The current task performed static reads of the original God2.exe; all steps involving execution remain undone. Input identity is [PE-001](CLIENT_REVERSE_NOTES.md).

## Procedure And Required Records

1. Preserve the original and its SHA256. Make a separate working copy in an isolated research workspace; record tool versions and host architecture. Do not overwrite the installed client.
2. Load the working copy into x32dbg or a suitable 32-bit OllyDbg environment. Record actual module base, loaded modules and initial entry RVA 0x00302001. Use only an authorized isolated environment.
3. Observe the ASPack-family unpacking transition. Record memory writes and control transfer into restored code; do not infer completion merely from reaching an address.
4. Try an execution breakpoint at actual_module_base + 0x0014A3E8, corresponding to preferred VA 0x0054A3E8. This is an unverified OEP candidate. If it never executes, hits too early, or returns to the stub, retain the trace and investigate another transition.
5. At a justified unpack-complete point, dump the mapped image to a new artifact. Record actual base, candidate entry RVA, memory regions, dump method and timestamp. Preserve the untouched dump separately from repairs.
6. Use Scylla or ImportREC to reconstruct imports from the mapped process. Check thunk bounds, module ownership, ordinals, unresolved entries and indirect/delay-loaded APIs. A tool's success dialog is not sufficient evidence.
7. Save a distinct God2_unpacked.exe only after recording its provenance and repaired entry/import metadata. Record SHA256 for raw dump and repaired image separately. The filename is a target artifact; no such result was created here.
8. Load the reconstructed image in IDA or Ghidra with correct x86 architecture and image base. Validate section mapping and representative disassembly around the candidate transition and import callers.
9. Locate ws2_32, wininet and socket-related imports, including dynamically resolved APIs. Trace connect, socket, send, recv, WSASend and WSARecv callers. Distinguish patch/update HTTP from game traffic.
10. Name SendPacket, RecvPacket, PacketEncoder and PacketDecoder only after control/data flow supports those roles. Record RVA, caller graph, buffer ownership and confidence.
11. Find opcode extraction and dispatch, including state-specific switches/tables. Trace selected handlers in both directions back to framing and transforms.
12. Promote evidence to [OPCODE_TABLE](OPCODE_TABLE.md), [PACKET_FORMAT](PACKET_FORMAT.md), and [PACKET_HANDLER_MAP](PACKET_HANDLER_MAP.md), preserving unknowns and sample references.

## Acceptance Gates

- Unpack: coherent restored code and recorded transition; original and dump hashes retained.
- OEP: observed execution at a justified application entry boundary; a plausible function prologue alone is insufficient.
- IAT: reconstructed descriptors/thunks map to identified exports; unresolved entries are enumerated, not silently dropped.
- Analysis image: entry, imports and representative callers disassemble consistently; rebasing rules are recorded.
- Protocol: enough evidence exists to reproduce stream decoding and required server replies from held-out samples.

If a gate fails, keep the artifact labeled partial and document the failure. Do not rename partial repair as verified restoration. Runtime integrity/anti-cheat bypass, official service interaction and full client source reconstruction are outside this plan's scope.
