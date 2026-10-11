# First-generation E3 owned combat pets — 2026-09-27

## Current formal status

Release `artifacts/releases/native-pet1-20260927-01` is INSTALLED. Schema37 adds
2070 current COM definitions and supports owned E3 snapshots in the existing
three cells42/43/44. The configured server uses the same accepted candidate
`ea8029cca06a122957915a69969290a0c70eb869097a4d433e9d2ccb447eccd3`.
No pet was granted, no growth rule activated, no client/config changed. Every
preexisting player row, revision and provenance was checked while stopped;
all other schemas and old migration history were retained. The shared table's
CHECK intentionally expands from FB73 to FB73 OR E353, with no second capacity.
The prior binary/schema36 save is backed up in that release.

## Pinned native authority

Current client SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Mapped image:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Current gamedata raw/decoded:
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` /
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.

All COM keys24001..26070 execute unchanged loader59420, index59A20,
getter59A60 and icon consumer9B720. Native tag selector32, not33.
Every396-byte parsed record and raw source row is retained; cached JSON pin
`48779aff006267371dcbce6c7813c521025496c82ad69e7c083bdcb8b2a204f2`.
COM descriptions explicitly identify combat pets; NCP descriptions identify
second-generation combat pets. PET descriptions include transport beasts and
must not be substituted for COM. This does not establish a community growth
grade/species join or authoritative wild-monster attributes.

E3 logical53/body52: world case46919E calls4A2B70. Native slot guard4A2980
accepts42..44. 4A29A0 permits key ranges3391..3778 or5DC1..6D60 and requires
an actual native metadata pointer. The enabled server currently accepts only
imported COM/type32 instances; the other native range/type13 remains unqualified.
4A2B70 copies13 DWORDs into UI+A6D8+(slot-42)*52. Its full inactive-panel
return was executed unchanged, with exact copy/canary and stack/register checks.

Original panel constructor4A19F0 loads bank36/action27(FPet_BGOpen), close28;
ROM `Data3/Flow/petegg.romZ` shares the pinned file with FB's distinct action75.
The original decoded image was inspected directly, not a desktop screenshot.
Numeric descriptors at RVA190E38 have32 controls. `current_pet1_stat_labels.py`
checks original reads, shifts/masks, controls and numeric consumer1077C0.

| Display field | E3 body representation |
|---|---|
| Current/max HP | WORD+0 / WORD+2 |
| Current/max MP | WORD+4 / WORD+6 |
| Level | unsigned BYTE+23h |
| Physical attack/defense | DWORD+8 / +Ch low12 bits |
| Magical attack/defense | DWORD+10h / +14h low12 bits |
| Strength/constitution | DWORD+10h bits12..21 /22..31 |
| Intelligence/speed | DWORD+14h bits12..21 /22..31 |
| Strength bonus | DWORD+18h bits24..31 |
| Constitution/intelligence/speed bonuses | BYTE+1Eh/+1Fh/+20h |
| Metal/wood | DWORD+8 bits12..21 /22..31 |
| Water/fire | DWORD+Ch bits12..21 /22..31 |
| Earth | DWORD+18h low10 bits |
| EXP percentage display | DWORD+18h bits10..23, multiplied by binary32(.01) |
| Life display | unsigned BYTE+22h, displayed against100 |
| Remaining points | WORD+24h |
| Rebirth count | unsigned BYTE+27h |
| Fusion expiry raw | DWORD+30h; timezone/unit not qualified |

These received combat values are server results. They do not recover an attack,
defense, HP/MP, growth or XP-threshold calculation. The EXP field is not cumulative
XP. The codec preserves every byte, including unclassified skill/flag fields.

## C++ runtime route and storage

`RecoveredPet1Stats` decodes the above widths independently from FB. The C++
repository validates actual COM catalog/type32, account/character ownership,
source key/slot and revision, and forbids changes during a pending battle.
`store_pet1` is a trusted acquisition/import API; no network request grants pets.

The existing world-ready C2S28 owned selection route now supports E3 and FB.
CUSTOM-0039 remains the explicit server selection policy: reserve42/43 selects
active44; returning44 picks the first actually empty reserve42 then43. Swaps
commit both snapshots atomically before sending. Opaque bytes, provenance and
ownership follow each instance; only the native routing byte changes (E3
logical+27h versus FB logical+3). Clear41 is sent for BOTH old cells before
metadata replacement, because native4A2C90 selects the52/72-byte clear using
the previous inventory type32/34. Restore splits records at native frame limits.

## Actual acceptance and limitations

`private-pet1-mixed-20260927-02` passed with the unchanged current original
private-port client against our C++ server on a hidden desktop. Five real native
inventory drags selected E3, swapped FB against it, returned FB, selected E3
again and returned E3 to an actually empty reserve. SQLite and read-only native
inventory/cache observations match full snapshots after every action. Both old
generation caches were cleared after transitions. Client remained alive;
input desktop, source save and both client files were unchanged.

An initial test failed by assuming an unused FB cache was zero: its first bytes
were uninitialized before any FB arrival. The oracle now checks the occupied
generation and the clear appropriate to retained type. It separately verifies
both old caches after the tested mixed transitions; it does not rewrite memory.

Tests:25 original numeric consumers across256 level/packed-boundary vectors;
structural lengths/slots/key gates and opaque roundtrip; populated schema36
migration, mixed swaps, injected second-write rollback, missing catalog/type/
ownership rejection, capacity and reload; original source rows and importer
conflict/cache rejection; six prior same-candidate transport regressions; mixed
E3/FB socket transfers and exact restore after restart.

Historical fixture logged a nonfatal native action.cpp/img diagnostic. The
subsequent native trace isolated synthetic deity100, whose portrait action99
exceeds Pic_God's42 actions; it was not a missing pet inventory image.
`private-deity-portrait-20260927-04` qualifies both generation inventory images
through five transfers (12 occupied sprite checks), two native deity HUD mode
entries and zero diagnostics against the formally installed portrait guard.
Original00481700 binds preloadFFFF after adding41h to each ROM bank.
See `deity-portrait-current-client-20260927.md`. Open pet-panel interaction and
battle skills remain outside this acceptance scope.

Bahamut first-generation grades, initial stats, exact level-award boundaries,
manual-point award rules, XP thresholds, capture/recruitment and battle-pet skill
execution remain OPEN. No community growth row was activated. Formal native
COM catalog2070/2070 and the scoped owned E3/FB route are accepted; native
growth-formula activation remains0%. No global game completion percentage is
derived from these counts.
