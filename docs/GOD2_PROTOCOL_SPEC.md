# GOD2 Protocol Specification

Revision: research draft 0, client artifact PE-001. **Not a recovered wire specification.** The current executable identity and imports are verified statically; the game contract is unresolved.

## Contract Registry

| Contract | Verified GOD2 result | Evidence needed before implementation |
| --- | --- | --- |
| Transport/endpoints | Unknown | Socket/API call graph and authorized traffic |
| Packet header | Unknown | Length/opcode reads and stream samples |
| C2S/S2C opcodes | Unknown | Serializer/dispatcher links and sample correlation |
| Payload format | Unknown | Typed reads/writes, field constraints and samples |
| Session flow | Unknown | Startup through world traces, retries and failures |
| Crypto | Unknown | Transform boundary, key lifecycle and test vectors |
| Compression | Unknown | Algorithm, activation, order and size limits |
| Checksums/sequence | Unknown, including whether present | Validation/update paths and negative cases |
| Expected server replies | Unknown | Client handlers, ordering and state transitions |
| Heartbeat/timeouts | Unknown | Timers, replies and expiry behavior |

## Mock Development Contract

[PACKET_FORMAT](PACKET_FORMAT.md) and [OPCODE_TABLE](OPCODE_TABLE.md) define an isolated placeholder mode: LE uint16 total length + LE uint16 opcode + payload. These are not statements about GOD2. The requested local state model is Connected -> Handshaked -> Authenticated -> CharacterSelected -> InWorld -> InBattle, with disconnect from any state. Mock login may also start from Connected. The current mock dispatcher allows heartbeat in all non-disconnected states and chat in InWorld. Return from battle, reconnect and real-wire transitions need explicit validation. PACKET_FORMAT documents the implemented mock payload schema and required future wire adapters.

## Flow Recovery Order

1. Establish transport and initial message sender; find any version/key negotiation.
2. Identify login fields, response statuses and connection handoff behavior.
3. Determine list framing/counts, selection identifiers and ownership constraints.
4. Determine world initialization dependencies, spawn order and readiness acknowledgment.
5. Recover movement/chat, NPC and inventory, then battle actions/results.
6. Validate heartbeat, session expiry, failures and reconnect behavior throughout.

Each stage must include expected server responses, not only outbound client requests. Record unsolicited notifications and whether they must precede UI/state transitions.

## Promotion Checklist

A real specification revision names the exact executable hash; documents byte-level schema, constraints and transforms; cites caller/handler evidence; includes original and decoded sample IDs; explains all bytes or marks bounded unknown fields; and passes held-out decode/encode tests plus an authorized controlled client interaction. Round-tripping a self-generated packet is insufficient.

Preserve compatibility adapters between wire packets and domain commands. Recovered field meanings can require handler/domain changes even if the ProtocolSpec interface stays stable. Version the contract and fixtures together; never silently switch placeholder mode to a guessed real mode.
