# Current-native S2C83 action frontier, 2026-10-06

The pinned mapped image SHA-256 is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
`tools/reconstruction/s2c_battle83_action_frontier.py` reads its complete
first selector table, first target table and actor-action target table,
then saves raw bytes, bounded instructions and all 23 rows in
`artifacts/integration/packet-connections-20261006/s2c-battle83-action-frontier-v1.json`.
No native client, build, test or service was run.

S2C `83` has a 15-byte logical length. The battle opcode dispatcher selects
`11436B`; the WORLD table uses its default entry. The first action switch
at `116C80..116C9C` subtracts one from the action byte and accepts
`01..17` hexadecimal, using 23 selector bytes at `1171D4..1171EB` and
ten target DWORDs at `1171AC..1171D4`. Values outside that range branch
to `117152` at this switch. The later actor switch at
`12C5B6..12C5D3` uses another 23-target DWORD table
`12CC3C..12CC98` and has its own out-of-range target `12CC15`.

| Action | First case RVA | Actor case RVA |
| --- | --- | --- |
| `01` | `116C9C` | `12C5D3` |
| `02` | `117152` | `12C645` |
| `03` | `116CF5` | `12C731` |
| `04` | `1170CE` | `12C92C` |
| `05` | `1170D5` | `12C99E` |
| `06` | `117152` | `12C9BF` |
| `07` | `116ECD` | `12C6CC` |
| `08` | `116CC8` | `12C69F` |
| `09` | `11714B` | `12C899` |
| `0A` | `117152` | `12CC15` |
| `0B` | `117152` | `12CC15` |
| `0C` | `117152` | `12C672` |
| `0D` | `117142` | `12CA2D` |
| `0E` | `1170CE` | `12C704` |
| `0F` | `116CB2` | `12C5D3` |
| `10` | `117152` | `12CC15` |
| `11` | `117152` | `12CC15` |
| `12` | `116CB2` | `12C5D3` |
| `13` | `117152` | `12CC15` |
| `14` | `117152` | `12C8F2` |
| `15` | `117152` | `12CC15` |
| `16` | `117152` | `12CC15` |
| `17` | `116CF5` | `12C731` |

The first stage has ten distinct case addresses; the actor stage has
fourteen. `03` and `17` share both case addresses, but the action byte can
still affect later behavior and resources. Sharing a case is not evidence
that a server may emit one as the other. `RecoveredBattleAttackPresentation`
only qualifies **`01` basic and `03` scalar one-target attack presentation**;
its parser deliberately rejects `17`. `RecoveredBattleDelta` covers an
independent bounded `0D` branch, while the `07` effect route remains
diagnostic. The other 21 selector values are outside the current scalar
projection; this is not a claim that all 21 lack other source research.

These are nested action values inside one opcode, not 23 additional opcode
types or 23 connected gameplay routes. Original effects, formulas, ownership,
server timing and all C2S/S2C causal paths still require individual recovery
and source integration. This round added no authoritative 83 gameplay branch
or formal deployment.
