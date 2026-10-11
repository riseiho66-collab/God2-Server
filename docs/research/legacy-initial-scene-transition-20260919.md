# Legacy Initial Scene Transition, 2026-09-19

## Result

Classic retains a **12-byte S2C 61 map-transition serializer and exact decoded
fixtures**, including area2/scene0 at (283,453), mode1. Its server explicitly
appends a transition after the frozen initial bootstrap to restore persisted
locations. This is a concrete legacy implementation policy, **not proof that
the official captured kind2 2A was followed by a valid ordinary-world transition**.
No alternative retained ordinary-scene 2A was found in this bounded search.
XJZ has no saved rows in the relevant transition/login/profile sample tables.

Main's subsequent finding resolves the apparent atlas mismatch: current
`100180` kind2 uses area/scene0 MDT -> CAN, and
`Data2/map/island01/Island01.can` maps scene15 to record12,
`\x01indoor\groceryl.hmd` (leading byte01). Thus area2/scene15 has an actual
scene mapping despite its absence as a UI atlas row. This is main-provided
evidence; main owns original CAN-loader/path qualification. A later legacy
transition is not required merely to explain the missing UI atlas row, and
this sidecar does not propose altering the retained 2A.

No current image disassembly, UI, live process interaction, production edits,
or atlas regeneration was performed. Only this document was written.

## Source Roots

- `C` = `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`
- `E` = `C/src/God2.ClassicServer.Protocol/Evidence/OfficialProtocolCompletion`
- `R` = `C:/Users/risei/Desktop/God2/God2-Server`
- `X` = `R/artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

Line numbers/offsets/lengths are decimal; opcodes and hex bytes are hexadecimal.
References below identify retained files, not currently available live captures.

## Exact Transition Fixtures

`C/src/God2.ClassicServer.Protocol/OfficialPortalWire.cs:86` defines the codec;
`:89` pins the **legacy** executable SHA to
`6B127086E0C00014DE26137B4EC482801E06E0724C5C05C64561D7F9FF32BD9B`.
`:95` declares C2S activation 0C, S2C prelude BB, and S2C transition 61.
The destination table is at `:105`; serialization is at `:319`.

`C/tests/God2.ClassicServer.Protocol.Tests/OfficialPortalWireTests.cs` retains
these complete decoded-frame hex literals in tests named
`Map_three_result_matches_recovered_client_parser_fixture`,
`Map_nineteen_result_matches_recovered_client_parser_fixture`,
`Hongmeng_biyou_results_match_bidirectional_capture_and_transition_first_order`,
and the two `Stage_three_*` tests. These are saved **plaintext fixtures**, not
newly invented frame bytes and not retrieved original encrypted capture logs.

| Area/scene | X,Y | Mode | Complete decoded transition | Prelude/order |
| --- | --- | --- | --- | --- |
| 4/3 | 196,139 | 0 | `0C0061C400040410031601F7` | `0600BB0000ED`, BB then 61 |
| 4/19 | 28,34 | 2 | `0C0061C40404047200440087` | `0600BB880075`, BB then 61 |
| 2/43 | 52,184 | 3 | `0C0061C20A0202D300700115` | `0600BB0000ED`, 61 then BB |
| 2/0 | 283,453 | 1 | `0C0061020002026D048A0305` | `0600BB880075`, 61 then BB |
| 15/0 | 248,247 | 1 | `0C00610F000F0FE103EE0101` | `0600BB0000ED`, 61 then BB |
| 15/7 | 48,81 | 0 | `0C0061CF010F0FC000A20051` | `0600BB0000ED`, 61 then BB |

Saved evidence identifiers in the destination table:

- 4/3 and 4/19: `PortalMapTransfer-attempt-42950-trace-six-round-trips`.
- 2/43: `PortalCapture/portal-next-elevated-20260811-152341`.
- 2/0: `PortalCapture/portal-biyou-return-20260811-153414`.
- 15/0: `LiveRecovery/Stage3-source-world-identity-sequence-14880`.
- 15/7: `LiveRecovery/Stage3-CGC-S3-portal-map0-area15-to-map7-area15`.

Wire layout from the serializer: frame WORD0 length12; byte2 opcode61;
WORD3 `(scene << 6) | area`; WORD5 preserved opaque word; DWORD7
`mode | (x << 2) | (y << 17)`; byte11 checksum. The opaque word is 0404,
0202, or 0F0F as retained above; its semantic meaning is not established here.
The checksum iterates preceding bytes with `sum = (sum + byte + 0x3C) & 255`
(`OfficialPortalWire.cs:403`). Independent read-only PowerShell arithmetic
recovered all six table tuples and verified all six transition checksums and
both distinct prelude checksums.

These are useful exact input candidates for main's current dispatcher work.
They do not establish the current opcode, current mode behavior, current map
resource loading, or walkability. In particular the legacy 4/19 fixture also
uses mode2; it does not justify changing current 2A kind2 semantics.

## Initial Spawn/Restoration Policy

`C/src/God2.ClassicServer.Runtime/OfficialClientWorldProtocolFrames.cs:129`:

1. Copy the retained 1778-byte post-handshake bootstrap.
2. Replace its player-spawn frame at bootstrap offset6.
3. At `:135`, return immediately for `MapId == 19 && X == 28 && Y == 34`.
   This branch does not additionally test area. It is an implementation default,
   not a decoded map identity proof for the embedded 2A.
4. Otherwise call `SerializeWorldProjectionDestination` with the persisted map,
   explicit area, and position (`:140`); reject an unsupported destination.
5. Encode and append `OrderedDecodedFrames` after the entire bootstrap
   (`:152`). The extra frames total18 bytes, in the table's destination order.

`C/src/God2.ClassicServer.Runtime/AuthoritativeWorldRuntime.cs:510` reaches
this policy with the authoritative character and resolved client area, directly
or through the MariaDB bootstrap wrapper. This is not merely an unused helper.

`C/tests/God2.ClassicServer.Runtime.Tests/RuntimeFoundationTests.cs:405`
checks appended restoration for 4/3 (196,139); `:430` checks 4/19 (29,35);
`:459` checks 15/7 (238,54), transition first. These tests demonstrate server
output policy, not an official initial-login capture. Tests were read, not run.

## Why The Frozen Tail Does Not Close The Gap

The sole retained initial 2A found remains decoded frame `[25,62)` inside the
320-byte outer frame at absolute stream offset153, from
`OfficialClientWorldProtocolFrames.cs:78`:

```text
2A D9 00 80 00 05 10 1B 02 00 00 00 00 01 80 01 60 01 60 31 00 60 00 31 0C C2 03 00 00 46 00 1A 00 00 00 00 00
```

This is the same current area2/scene15/kind2/(17,13) candidate, not an
alternative. Its opcode/body SHA-256 is
`B4CF5BD6CEE76B6EB876D93812BA982ACA22E3DB01C15236FC5DDE430964126D`.
Independent extraction reproduced encoded outer-frame SHA-256
`C2DB6E90071C425F0D3B69952F940C3D979F64879863CBCC6612DF2B954E99B7`
and decoded frame SHA-256
`B0837934E2AA71A0C552160C4F54B20FF8073F81737CC0CF8E19E3B2DB910D3A`.
For original saved-prefix provenance see
`R/docs/research/legacy-world-entry-provenance-20260919.md`.

`E/WorldBootstrapSequence.json:122` labels a later frame
`WorldCompactState61S2C42`, bootstrap offset1555 / absolute offset1574,
length42. Exact saved encrypted bytes from the source constant are:

```text
2A00494EE7819CBBB7E82569440EB16882FFF65C642D003C9384CB3FBADB9B9E79E13991248B189ADD0E
```

SHA-256: `6219821955DC7BA8306262E4A264D1771FD0A8A7DA7918EBD10FBD898F2F5E23`.
Applying the legacy class's fixed `WorldCipherKey` / feedback B0 decoder gives:

```text
2A00616FB11BC6500316B30788B322933D9730B67AD0C85C4C27E13072A3A4EC792842593416FEBFE392
```

The legacy checksum expects **B2**, but the decoded final byte is **92**.
Thus neither the saved `61` label nor this failed decoding establishes a
valid 12-byte map transition or its logical body. No later feedback recovery
or current dispatch analysis was attempted. This is not a claim that the
encrypted frame itself is corrupt.

`E/DecryptedPacketCorpus.20260807.v2.json:1103` separately indexes
`runtime-map-transition`, S2C opcode97/length12, SHA
`958A53D71D62829CAC0D35E4CE7F96CF4174B1BF8A0A6F878BC90CDBD43483CC`,
but carries no plaintext hex and sets crypto/parser/builder verification false.
It cannot supply the missing temporal adjacency. `C/PACKAGE-CONTENTS.md:4`
explicitly excludes runtime output and packet captures. The named portal
capture identifiers were not found as raw capture files in this source tree.

## XJZ Check

Read-only SQLite (`mode=ro`) queries against `X/xjz_evidence.sqlite` returned:

| Table | Saved rows |
| --- | --- |
| teleport_flow_sample | 0 |
| account_login_sync_sample | 0 |
| character_create_sample | 0 |
| character_profile_sync_sample | 0 |

`X/data` is empty. The SQL dump declares `teleport_flow_sample` at
`db-evidence-schema-v0.sql:256883`; no inserts into that sample table were found.
`cpp/xjz_evidence_models.hpp:5392` defines optional source/target coordinates,
`raw_packet_json`, and `packet_path`; the empty table supplies no actual hex.
`cpp/xjz_item_effect_contracts.hpp:42` returns a teleport description in the
item-use result, not a map-entry wire serializer. Searches of C++ contracts
and implementations found no concrete 2A/61 map-entry serializer.
`evidence-transport-service-template-v0.md:22` explicitly sets
`packet_evidence_boundary = 0`, and `:24` leaves actual destinations and
official packet results to future flow samples.

## Handoff

The new actionable evidence is the exact legacy 61 layout, retained fixture
bytes, destination-specific BB ordering, and the implemented post-bootstrap
restoration policy. Both corpora were checked, but neither establishes an
official initial `2A(kind2) -> ordinary scene transition` chronology or supplies
another qualified normal-scene 2A. Main's CAN finding supplies the relevant
current initial-scene route independently of this legacy search. The saved 61
fixtures remain references for later transition qualification, not a reason
to replace 2A or append an initial transition. No default scene substitution
is supported by this research alone.
