# Packet Handler Map

No real GOD2 handler address or opcode has been recovered. The table below is an investigation map of logical responsibilities, not a discovered dispatcher.

| Meaning | Real opcode / direction | Client handler RVA | Expected research context | Payload schema | Server implementation status |
| --- | --- | --- | --- | --- | --- |
| Handshake | unknown / both | unknown | Connection startup | unknown | Mock handler implemented |
| Login | unknown / both | unknown | Login UI and result handling | unknown | Mock handler; real authentication unsupported |
| Character list / select | unknown / both | unknown | Character screen | unknown | Repository-backed mock handlers |
| Enter world / spawn | unknown / both | unknown | Map transition | unknown | Mock entry and spawn broadcast implemented |
| Heartbeat | unknown / both | unknown | Timers across session states | unknown | Mock handler implemented |
| Movement / chat | unknown / both | unknown | World input and notifications | unknown | Persisted movement and map chat implemented |
| NPC / inventory | unknown / both | unknown | Dialogue/items | unknown | Lua NPC hook implemented; inventory deferred |
| Battle | unknown / both | unknown | Battle entry/action/result | unknown | Placeholder only |

## Required Handler Record

Opcode (width and representation), direction, handler RVA/preferred VA, source hash, registration/dispatch evidence, allowed wire/session state, meaning, payload field order/types/constraints, optional fields, response sequence, error behavior, ownership checks, sample IDs, confidence and server implementation/test references.

Keep server handler registration distinct from a client handler address. C2S meaning may be recovered from a client encoder without any matching inbound client dispatcher. A matching numeric opcode in two directions does not establish shared meaning.
