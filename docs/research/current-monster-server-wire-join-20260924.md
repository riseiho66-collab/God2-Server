# Current monster identity → server source → battle wire

The present server does **not** have a qualified original wild-monster stat row.
This audit follows the exact diagnostic battle constructor and its logical
outbound records; it does not promote its test values to original balance.

## Observed chain

`Application.cpp` calls `diagnostic_battle_player_participants(...)` when the
diagnostic player appearance is enabled. That builder supplies an enemy at
battle position 14. The compiled builder's actual logical output was decoded
by `monster_identity_wire_audit.py`, rather than inferring packet bytes solely
from source code.

| Link | Actual outgoing value | Source / scope |
| --- | --- | --- |
| `S2C 1C`, enemy position +1 | 14 | Diagnostic participant template |
| `1C` displayed level +2 | 0 | Diagnostic zero; original level unknown |
| `1C` identity WORD +3 | 0 | Diagnostic zero; native consumer retains this word, but species-ID meaning is unproved |
| `1C` variant WORD +5 | `0x0400` | Native normal enemy display route |
| `1C` ordinal WORD +7, area BYTE +9, scene WORD +11 | 1, 1, 0 | Matches one visible EnyName **display** row in the current client catalog |
| `S2C 86` subtype 0, position 14, DWORD +5/+9 | max HP 150, current HP 150 | `CUSTOM-0009` diagnostic constant, not a source monster stat |
| Enemy MP `86` subtype 1 | No record sent | No claim that original enemy MP is zero |
| Server `BattleActor` position 14 | HP 150, attack 20, defense 25, speed 13, remaining scalar 6 | `CUSTOM-0012` fixture in `Application.cpp`; attack/defense are **not** carried by this initial `1C/86` batch |

The same client `(area=1, scene=0, ordinal=1)` display row is at decoded
`gamedata.csvZ` line 21699, offset 2500917, row SHA256
`34e14a591490fd9f6444f8776bcc7f0cc39699dfd78a13b2feb097c3636c5f32`.
Its CP950 name bytes `a454b84fc06e` decode to **三碑鴨**; an earlier PowerShell
console display of those characters was garbled, but the JSON Unicode code
points and raw-byte decode agree. All 21 original numeric fields in the
readable catalog remain null. The same name bytes appear at a second visible
client display key `(area=0, scene=2, ordinal=212)`, source line 25617. This
is a concrete name collision: a historical guide row labelled 三碑鴨 cannot be
joined to either key by its name alone.

The configured server's imported native map catalog maps packet `area=1,
scene=0` to **聖樵原野** (source line 21020). This is a region-plus-name
cross-check for the display row, but still not a server stat row or proof of
the monster's numeric variant. The current diagnostic quest battle is reached
through area 2/scene 15; that area/scene has no normal EnyName group in the
current client catalog. Its borrowed 聖樵原野 display identity is explicitly a
test appearance, not an original quest monster assignment.
The earlier native backtrace proves this tuple selects the EnyName resource;
it does not prove that the tuple, source label 1, or packet identity word 0 is
an original server monster template key.

At the time of this audit, `god2.db` and the persistent playtest SQLite database
had no monster/enemy named tables. A later [EnyName display catalog import](native-enyname-sqlite-import-20260926.md)
added a provenance-bearing display lookup table to the formal server schema,
but did not recover a monster stat table or a packet sender. This bounded
schema check is not proof that no other original server package exists. Current battle HP and damage are generated
by the server's diagnostic C++/Lua battle state. The later diagnostic `S2C 83`
contains an HP display delta at WORD +9; it is a result of the custom rule, not
an original damage formula or a carrier of attack/defense base attributes.

## Remaining authoritative join

To recover original combat values, first obtain a build-matched original server
monster row (or an official server packet capture plus its sender/source). Then
verify the row's key against the `1C` identity fields, and compare the sender's
actual `86` HP/MP, `83` outcome, and any separate attribute messages. A
display-name or ROM match alone cannot qualify a numeric join. The original
server sender and original stat row are currently unavailable in this workspace;
therefore original HP, level, MP, attributes, attack, defense and damage remain
open, with zero recovered monster stat tuples.

Verification performed: isolated Release build of `god2-server` and
`recovered-battle-bootstrap`; the latter's assertions passed. The read-only
audit ran against both SQLite databases and produced
`artifacts/research/monster-identity-wire-audit-20260924.json`. The persistent
server was not restarted and player data was not changed.
