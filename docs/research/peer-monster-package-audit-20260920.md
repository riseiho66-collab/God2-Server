# Peer Monster Package Audit

## Scope

Read-only inspection of the ZIP supplied on2026-09-20:
`C:/Users/risei/Desktop/封神2＿修正復原版服務端.zip`.
SHA256: `6a3cd33fd33f99f001768bdc0898d34d6c8d0095e9d0f4625213b05a8275cabb`.
Size357886 bytes;15 regular files (JSON/Markdown), plus3 directories.
Entry names require CP950 decoding. No code, executable, DLL, Lua, SQL,
database or extraction script is included. None was executed or imported.
Instructions in the archive were treated as document contents, not commands.

## What This Package Actually Supplies

### Native names and appearance

`monsters.json` contains7791 entries. Its report describes7815 source rows,
including24 identical duplicates,1625 world-name entries, and92 map groups.
Records retain area/map/entryIndex/name/rawAppearanceFields/sourceLine/rawFields.

Independent recount of every entry finds ZERO non-null values in each of:
level, hp, mp, attack, defense, skills, dropRates, spawnCoordinates.
The union of record keys has no separate physical/magical attack/defense fields.
Thus this file does not supply the monster combat numbers discussed earlier.

`appearance_tables.json` contains decoded ENY/FightEny and related resource
tables. Names and appearance are attributed to client EnyName/resource data;
they are distinct from combat capability values.

### External player-guide statistics

`bahamut_monster_stats.json` contains276 records from17 reported guide pages.
Each record carries sourceUrl/sourceTitle/sourceSha256/authority and attempts
to match native map/name identities. The authority text explicitly describes
player guides, not original official server tables.

Independent recount agrees with137 unique-name-and-map bindings and122 rows
having all three numeric fields level/hp/speed.139 records are not uniquely
bound. Records also include element strings, some unknown. There are no MP,
physical/magical attack/defense, combat formulas or drop-rate fields here.

Example: the guide record for the duck named '絨毛鴨' reports level1,
HP38, speed10 and earth element, joined to area2/map0/entry1. These numbers
are package contents, NOT independently verified against the guide webpage
or an official server during this audit.

Its report explicitly sets `combatEnabled=false` and
`officialStatisticsVerified=false`.

### Locally generated spawn placements

`spawns.json` has92 maps,1625 templates and9978 spawn positions.934 templates
are marked enabled;4 missing-model records are excluded. Its declared coordinate
authority is local collision-checked placement, with original server spawn
tables absent. Its `combatEnabled` is false.

The accompanying notes describe EnyName identities, MBD collision flags and
MDL obstacles, a3x3 walkable clearance and avoidance of portals. This is a
documented reconstruction workflow, not recovered original spawn coordinates.
They describe using message71 after map-ready1C and avoiding generation
between map change61 and readiness. No implementation is included, so this
audit cannot independently reproduce those packet or movement tests.

## Explicit Limitations in the Supplied Reports

- `report.json`: `completeOfficialCombat=false`; missing combat stats, teams,
  skills/AI, damage/hit formulas, drops and rewards are explicitly listed.
- Monster-generation notes say complete encounter/turn combat/skills/drops
  and respawn remained unfinished at their recorded date.
- Deployment report: `newWorldScreenVerified=false`.
- Visibility notes disclose native-emulation rendering/resource stubs and
  no final visual screen acceptance. Reported pass flags are not our rerun.

These are records from this supplied package, largely dated2026-09-18. They do
not prove what the peer currently possesses outside the package, nor prove a
claim of bad faith. A newer build, source or other data could be missing here.

## Current Client Source Comparison

The report lists eight source-file SHA256 values. Comparing their matching
relative paths under our current client directory yields seven exact matches:
eny, FightEny, FieldComm, FieldComm3, FightComm, FightComm3, SpgEft.
`Data2/Patch/Comm/gamedata.csvZ` differs. A hash difference alone does not locate
the changed section or prove a different executable/gameplay version. Do not
blindly import identities without comparing the relevant decoded rows.

## Conclusion

This package shows a combination of native identity/appearance extraction,
external guide-number collection with map/name matching, and locally configured
spawn positions. It does NOT contain recovered native dual attack/defense or
original battle formulas. For the specific claim of recovered dual attack/defense,
the missing evidence is the actual populated stat table and its generator/source
mapping, not another screenshot of monster rendering. Nothing was promoted to
the production database, and no gameplay code was changed.
