# GOD2 Reverse Research Workspace

This directory records evidence for the server contract, not recovered official source. Original client SHA256 and PE details are in [CLIENT_REVERSE_NOTES](../docs/CLIENT_REVERSE_NOTES.md). Only static inspection was performed. No client was executed or altered.

## Evidence Classes

- **PE-001 / observed static:** exact original file hash, PE32 headers, sections, entry metadata and on-disk import descriptors.
- **REQ-001 / unverified:** user-provided OEP candidate 0x0054A3E8. No execution trace establishes it.
- **Placeholder:** synthetic framework header and opcode values; never client observations.
- **Unknown:** all actual wire schemas, wrappers, dispatchers and gameplay flows pending research.

## Navigation

| Location | Contents |
| --- | --- |
| findings/oep_notes.md, imports.md, sibling_executable.md | Static findings, separate executable comparison and restoration limitations |
| findings/send_recv_xrefs.md | API-to-wrapper research method |
| findings/packet_*.md, opcode_*.md | Framing, transformations and dispatch investigation |
| findings/*_flow.md | Flow-specific questions and acceptance checks |
| samples/raw_packets | Original authorized captures, currently none |
| samples/decoded_packets | Versioned interpretations, currently none |
| samples/hex_notes | Synthetic framing notes separated from captures |
| ida, ghidra | Analysis setup and symbol provenance |
| x32dbg | Planned restoration and breakpoint records |

## Sample Metadata

Every future sample records ID, client hash, source type (capture/memory/synthetic), collection date, direction, session label, local action, stream offset, timestamp, pre/post-transform boundary, tool/version, raw artifact hash, redaction status and related finding IDs. Preserve chronological ordering and receive/send fragmentation independently of decoded frame boundaries.

Store no credentials in shared captures. If redaction is necessary, retain a clearly marked derived artifact and explain changed offsets/checksums; do not silently alter original evidence. Do not upload proprietary binaries or whole debugger databases as substitutes for concise findings.

## Promotion Workflow

Record observations here, cross-link verified symbols and handlers into docs, and promote only corroborated wire facts into GOD2_PROTOCOL_SPEC. Include counterexamples and unknown trailing bytes. No recovered sample or repaired executable is present in this task's output. See [research plan](../docs/REVERSE_ENGINEERING_PLAN.md) for gates.
