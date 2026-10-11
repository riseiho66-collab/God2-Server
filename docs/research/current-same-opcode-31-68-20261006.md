# Current-native 31/68 directional split, 2026-10-06

The pinned mapped image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses are RVAs at base `0x400000`. The receive-table identities,
bounded original bytes and disassembly are retained in
`artifacts/integration/packet-connections-20261006/same-opcode-31-68-receive-split-v1.json`.
This is static source evidence; no client, test, build or live service ran.

| Direction/opcode | Current-native path | Qualified observation |
| --- | --- | --- |
| C2S `31` | `BF300..BF505` → `961A0` | Two-byte `31 00` candidate after one required and six excluding UI row guards; see `current-wrapper-ui-gates-20261006.md`. |
| S2C `31` | 29-byte leaf `12FA`, dispatch `69FA9` → `AA200` | Updates an existing owned-companion/deity row. `RecoveredDeityState::Status` already preserves this 29-byte record; no request relation to C2S `31` follows. |
| C2S `68` | Four guarded calls in `C3750..C39C3` → `961A0` | Conditional `68 00` candidate from the large-map UI family; wrapper may handle locally without queueing. |
| S2C `68` | 13-byte leaf `1246`, dispatch `6ABF3` → `9BED0` | Reads `WORD` at logical +3, `DWORD` +5, bytes +9/+10; passes a row pointer or zero and these values into a distinct UI receiver. |

For S2C `68`, `6ABFF..6AC36` bounds the unsigned logical +3 word against
the client resource count at `owner+B2C80`, uses `owner+B2C84` as a table
base when in range, and passes either a derived pointer or zero to `9BED0`.
The `9BED0` path checks signed widget index `UI+232DD8`, rejects a zero
table pointer through its native assert path, stores the pointer and other
received values in UI-local fields, then checks that widget's `0x10` flag
before later UI work. Exact original meanings of the fields and the path's
normal rendered result remain unqualified.

The C2S `68` sender family instead references the large-map panel index
`UI+232DA8`; earlier map-panel work locates S2C `3F` as an opener for that
panel. This differentiates immediate UI destinations but does **not** prove
that `3F` answers C2S `68`, or that S2C `68` can never occur after it.
Likewise, S2C `31`'s deity row update cannot be promoted to a C2S `31`
response just because the byte matches. Both C2S opcodes remain outside
the WORLD parser/Application route; no handler, response or completion count
was added. The next action is to recover the C2S UI action's server-owned
context and actual reply sequence, including the map-panel request boundary,
before binding an authoritative server operation.
