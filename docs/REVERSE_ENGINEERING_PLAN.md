# Protocol Research Plan

## Evidence Pipeline

Start with [PE-001](CLIENT_REVERSE_NOTES.md). Restore an analysis image under [the restore plan](EXE_RESTORE_PLAN.md), then work outward from network APIs to packet construction and inward from receive buffers to dispatch. TCP read boundaries are not packet boundaries. The presence of wininet does not identify the game transport.

Each finding needs: evidence ID, source hash, tool/version, file offset or module-relative RVA, preferred/runtime base, direction, observation, interpretation, confidence, sample references, contradictory evidence and reviewer/date. Use statuses **observed static**, **observed runtime**, **corroborated**, **hypothesis**, **unknown**, and **placeholder**. Promote a hypothesis only when its stated validation check passes.

## Work Packages

| Work | Method | Exit evidence |
| --- | --- | --- |
| Restore | Trace unpack transition and reconstruct imports | Separate hashed dump/repair, unresolved-IAT list |
| Network boundary | Trace resolved API callers and completions | API-to-wrapper graph and buffer ownership |
| Framing | Follow receive accumulation and length checks | Offsets, size semantics, limits, split/coalesced fixtures |
| Transforms | Trace bytes before/after crypto/compression | Order, parameters, key/state lifecycle, vectors |
| Dispatch | Trace discriminator reads to branch/table | Direction/state-aware handler map |
| Payloads | Trace typed reads/writes and UI/world consumers | Width, signedness, encoding, counts and constraints |
| Flows | Correlate local actions with ordered messages | Request/reply, unsolicited updates, timeouts and errors |
| Compatibility | Decode held-out artifacts and controlled sessions | Reproducible expected output and no unexplained bytes |

Recover handshake, login, character list/selection and world entry before movement/chat, NPC/inventory and battle. Track heartbeat independently because it may span several states. Avoid assigning all packets after an action to that action: background updates and acknowledgments require correlation.

## Verification Matrix

Framing must cover empty payload, minimum/maximum valid length, invalid short/oversize length, header split at every boundary, payload fragmentation, two concatenated frames and truncated EOF. Payloads need empty and non-ASCII strings, invalid counts, extra bytes, invalid enums and negative/out-of-range values where applicable. Stateful transforms need fresh sessions, consecutive packets and reconnect cases.

Keep raw observations immutable, decoded interpretations versioned, and synthetic fixtures visibly labeled. Decompiler output is an analyst aid, not recovered source. Findings remain attached to this client hash; another release requires comparison.

## Current Progress

Completed: original PE hash, header/section parsing, on-disk import enumeration and candidate address-range check. Pending: every dynamic restore, IAT repair, xref, packet capture and real-protocol acceptance gate. [GOD2_PROTOCOL_SPEC](GOD2_PROTOCOL_SPEC.md) is the contract registry, not a claim of completion.
