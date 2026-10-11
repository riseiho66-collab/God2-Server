# CN ready-world mixed C2S source composition, 2026-10-07

This round connects the existing initial-ready owner to the existing movement
and three directory source controllers through `SharedWorldGameplay::compose`.
It supplies bounded source composition, not an activated Application plan or
a completed native gameplay route. The actual common authority implementations,
native reply suppliers and official rules remain required and incomplete.

The factory returns the same `SharedWorldReady` type required by
`SharedWorldSelection::install_selected_ingress`. It binds one connection,
presence registry, visibility registry and generation-qualified actor lease.
It preserves initial `1F00 -> 2300 -> 1C(handle,0)` handling and the existing
entered continuation. Child gameplay controllers attach only after the real
ready owner has activated this lease and the entered continuation has succeeded.
This avoids attempting to attach ready-only controllers during preparation.
There is no replacement login, ready acknowledgement or synthetic authority.

## Bounded input branches

Lengths below are complete C2S records, from retained pinned-CN producer
evidence. They are independent of S2C opcode lengths. Bit0 is read from this
connection's actual offered native07 source; it is a presentation mode, not a
permission or a protocol-version claim.

| C2S | Bytes | Source dispatch scope |
| --- | ---: | --- |
| 2E | 7 | Existing native movement parser and real common movement owner |
| 94 | 9 | Selectors19/23/24 to AE/B0 owner in both native modes;22 recovered generic selectors to AF owner in mode0 |
| A4 | 3 | Selectors19/23/24 with signed one-byte direction FF/01 to AE/B0 owner |
| D1 | 3 | Mode0 selectors25/26 to fixed2105-byte F9 owner and required25 NPC-name projection |
| 30 | 2 | Literal00 payload to independently supplied ongoing control owner |
| 36 | 9 | All eight opaque payload bytes to independently supplied ongoing control owner |

Generic94's22 selectors are00,01,02,03,04,05,06,07,08,09,0A,0B,0C,0E,0F,10,
13,14,1E,1F,20,29. The existing parser owns this set; the dispatcher does not
invent a second divergent selector list. Selector14's distinct AF storage and
fallback requirements remain with the actual supplier. D1(27/28), other B0/94
selectors, ongoing scene1C/transfer and all other opcodes remain open. Unsupported
variants fail this bounded source composition; rejection is not route completion.

The real native periodic worker is gated by active connection state; retained
`cn-ready-bootstrap-order-agent-01/worker-control-contract.json` records30 and36
emission independently of the initial three-record ready sequence. Their server
semantics, replies and any restoration-specific36 conditions are unresolved.
An ongoing background callback is therefore mandatory and distinct from the
initial bootstrap callback. Recognition never substitutes a no-op or a success
reply for this missing authority.

## Ordering and ownership

The dispatcher first parses the entire bounded logical aggregate, retaining
every request byte, including unwritten94 padding, movement stack byte and36
payload. An unknown or truncated tail prevents dispatch of the preceding
records from that aggregate. This shape admission is source implementation,
not a test or proof of official input policy.

It then dispatches individual records in original order. Each child's real
completion must succeed before the next record can run. A pumping/waiting loop
handles inline and deferred completions without recursive stack growth for each
inline record. Duplicate callbacks cannot dispatch the next request twice.
Connection/account/character, ready lease and offered native mode are checked
again between completions. Required suppliers are retained with the composition
because the existing children hold references to them. Transport serializes
logical ingress; an overlapping outstanding batch closes the connection.

Per-request movement transactions, revision checks, Lua-rule calls, peer
publication and native reply bytes remain in the existing owners. This is not
an atomic multi-request transaction. A later failure retains committed position
and performs the existing generation-qualified cleanup; it does not rewind a
move already observed by peers. Directory response order and opaque bytes stay
with the supplied publication. No outgoing opcode or new reply serializer was
added. Mode1 does not attach the mode0-only AF/F9 controllers.

## Retained evidence and limits

The delivery snapshots the prior catalog37 ledger/source hashes, all new source,
unchanged controller context and hashed prior integration receipts from
cn-world-ready-owner-01, cn-shared-movement-owner-01,
cn-native-directory-owner-01, cn-generic-directory-owner-01,
cn-special-directory-owner-01 and cn-summary-world-lineage-01. The worker
control contract is retained separately. No previously sealed artifact is edited.

This adds one unhosted partial source composition and six overlapping C2S
phase/source bindings. It adds no opcode values, no unique phase/opcode values
and no complete bidirectional routes. Production native login/world suppliers,
real ongoing controls, directory data/rules/resource mappings, actual Application
world-preparation use of this factory, and unknown gameplay variants are still
missing. Source counts do not prove the whole-game denominator. Percentage and
whole-game complete count remain unknown.

No compiler, build, tests, runtime, Lua execution, asset loader, client/server,
native acceptance, production database or deployment was run. Native fonts,
Traditional/Simplified conversion and all frozen TW features are unchanged.
