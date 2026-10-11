# Current-native S2C battle dispatch frontier, 2026-10-06

The verified mapped image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The original bytes, bounded disassembly and complete indexed table are in
`artifacts/integration/packet-connections-20261006/s2c-battle-dispatch-frontier-v1.json`.
`tools/reconstruction/s2c_battle_dispatch_frontier.py` reads them without
running a client, build, gameplay test or live server. Earlier battle research
identified individual paths; this ledger-facing census distinguishes the
entire battle opcode switch from the WORLD receive table.

The battle queue dispatch at `114332..114358` subtracts `0x1C`, checks the
index against `0x6D`, reads one byte from `11465C..1146CA`, then selects
one of ten DWORD targets at `114634..11465C`. Within the inclusive
`1C..89` range there are **110** indexed opcode values: **nine** specialized
and **101** mapped to battle default `1145C0`. Out-of-range values also
branch to `1145C0` at this switch; this does not describe earlier framing or
other client states.

| S2C opcode | Battle case RVA | Current known boundary |
| --- | --- | --- |
| `1C` | `114358` | Battle participant/identity branch |
| `38` | `114525` | Skill selection branch |
| `83` | `11436B` | Action/result family with further action dispatch |
| `84` | `1143DD` | Effect/action branch |
| `85` | `114449` | Battle queue/control branch |
| `86` | `114464` | Further subtype switch |
| `87` | `114518` | Skill pointer branch |
| `88` | `114538` | Bulk vitals/cycle branch |
| `89` | `114582` | Result/experience/exit branch |

All nine use the **default** entry in the previously inventoried WORLD
dispatch table. Therefore the 46 supported-length WORLD-default opcodes
contain at least these nine battle-specialized cases. Across these two
specific states, `206` WORLD non-default plus `9` battle-only-specialized
gives **215 distinct opcodes with a specialized table entry in at least one
state**. This remains an entry count, not 215 gameplay packet types,
completed routes, or a whole-game denominator.

For battle S2C `86`, `114464..11447A` dispatches logical byte +1 values
`0..6` through seven DWORD entries at `1146CC..1146E8`. Values `0` and `6`
share case RVA `11447A`; the other cases are `1→11449E`, `2→1144D8`,
`3→1144AE`, `4→1144C8`, `5→1144BE`. Shared code does not prove identical
subtype meaning. This is seven selector values and six case addresses,
separate from the nine opcode count. The `83` action subdispatches, record
contents, state timing, authoritative server source and native client
acceptance remain separately open. No new formal packet route was connected
or deployed in this round.
