# Current World Scalar Bootstrap Candidate

## Scope And Status

The existing `recovered_world_entry` opt-in now sends one 144-byte lab frame
after the complete, validated `1F00 / 2300 / 1C<id,flag>` initialization tail.
It contains the historical bootstrap prefix `2B / 2C / 24 / 39 / 22`, in its
retained order. `RecoveredWorldStateCandidate.h` preserves all 141 logical bytes.
This is **not** a recovered causal response mapping for the three C2S requests.
It is a deferred bootstrap experiment; current original-client live acceptance
and correct timing remain unverified. It must not be promoted to a production
character-state projection merely because parser tests pass.

The selected character's persisted attributes are not known from this snapshot.
Historical values are never written to SQLite or assigned to a mock gameplay
player. No Lua gameplay behavior changes. Existing configs leave the opt-in off.
No other bootstrap records, strings, inventory, entities, or opaque suffix are sent.
The server remains CharacterSelected, not InWorld. A duplicate tail/unknown
next request still fails closed; movement is not implemented by this change.

## Provenance

`tests/fixtures/recovered-world-state.json` references the previously pinned
source/stream/key hashes in `recovered-world-entry.json`. Source frame absolute
offset 473, length 752, SHA-256:
`32cea8e0a2765036c4dd495179abfd045baaa51a2dfefbb0fe8f33d00ff171ef`.
Its checksum passes with the documented historical key/feedback. The extracted
decoded interval is `[2,143)`, SHA-256:
`e1a39822563136271f9e36d82edcc24e112586784db736dc6221f74763cd9cc0`.
The new 144-byte framing uses the existing zero-seed lab codec, not the old key.

The independent saved decoded-frame hash and the limits of legacy request/reply
associations are in `legacy-world-ready-responses-20260919.md`. The corpus does
not establish a response for C2S23; temporal `1F -> 36` and `1C -> 72/B2`
associations lack paired raw payloads and are not implemented as guessed replies.

## Current Consumer Evidence

Pinned mapped-image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are hexadecimal RVAs; body offsets are decimal, actor offsets hex.
World dispatcher `68B61` uses table `6B5D4`. Its UI object is world+A7F2F6C;
the actor pointer is UI+86888. The optional subordinate actor is actor+D0.

| Opcode | Logical length | Branch / consumers | Direct scalar writes |
| --- | ---: | --- | --- |
| 2B | 21 | 69EB0 -> E6390, AA3F0 | Body DWORD0 -> actor5C; DWORD8 ->64; WORD16 ->58. Optional subordinate DWORD4 ->2C, WORD12 ->34, WORD18 ->28 |
| 2C | 61 | 69EDE -> E6600 | Low WORDs at body0/4/8/12 ->actor88/8A/8C/8E; DWORD16..32 ->A4..B4; WORD36/40 ->B8/BA; DWORD44/48/52/56 ->98/94/A0/9C |
| 24 | 17 | 69F4D -> E71E0 with trailing args zero | DWORD0/4/8/12 ->actor5C/64/60/68; may reduce optional subordinate2C by decrease in actor5C, clamped at zero |
| 39 | 17 | 6A003 -> AA9E0 | No-op if actor+D0 null; otherwise DWORD0/8 ->subordinate2C/30 and WORD4/12 ->34/36 |
| 22 | 25 | 69EF0 -> E6B40 | BYTE0 ->actor26; WORD2 ->90; zero-extended WORD4/6/8/10 ->DWORD78/7C/80/84; WORD12 ->58; DWORD16/20 ->60/68 |

These are actual write widths, not meanings inferred from zeros in one packet.
S2C1F and S2C1C go to the world's default consume branch `6B517`. S2C23 copies
a string through `69F02`; it is not used as a guessed character-name reply.

## Verification Boundaries

`test_current_world_state.py` verifies source hashes, complete historical frame
checksum, exact prefix bytes, original size functions and dispatcher targets.
The C++ 144-byte output passes original `10490/106F0/10750` key/decrypt/checksum.
Its decoded logical buffer is then fed through original `13420/12520/10AF0`,
`13650`, and `13670`, yielding exactly five records and consuming exactly 141
bytes. No socket/API calls are substituted for this parser test.

All five original dispatcher branches and scalar consumers execute separately
with packet bytes ending at a read-only page boundary. Tests cover retained
bytes and nonzero synthetic width probes, with and without actor+D0. Entire
actor/subordinate allocations are compared, including untouched guards.
Rendering/resource refresh helpers E63F0/AC070/AC2C0/AA480/E6710/E6DB0/E72D0
and formatting helper1077C0 are stubbed. Their success, rendered UI, asset
availability, semantic stat names and complete gameplay state are **not** proven.

Real C++ loopback tests feed original-code-generated C2S tail bytes, assert exact
144-byte output, ordering, one-shot behavior, restart/ownership preservation,
and unchanged stored profiles. Wrong ID/order/constants/checksum, truncation and
repetition cannot advance to another state bootstrap. These use a synthetic
network peer, not the original game process. No live game was launched here.

Release build passed; 21 core CTest suites and the combined 96 Python regression
tests passed. The single bounded legacy-evidence agent completed and was closed.

Next: validate actual scene/resource/profile projection and the missing gameplay
contracts. Historical scalar replay is not a substitute for authoritative Lua
starting rules, C++ entity state, persistence, or original-client world E2E.
