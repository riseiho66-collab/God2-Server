# Current world-entry map fields

## Evidence

Current image: `native-master-01-stable.bin`, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
No retired archive was read for this qualification.

- RVA 681CF reads body+24; 681D5 masks area with 0x3f.
- 681D8..681E5 rejects area zero and area >=17.
- 68265..68298 and 682F1..68310 pass area and the low WORD shifted
  right six to the resource/group and scene loaders. Scene is ten bits.
- 6865C..68672 stores area as WORD actor+0x18 and scene as DWORD actor+0x14.
- 68636..68659 independently stores body+28 low two bits at actor+0x10
  and world+0x22c. This is NOT the area field. Existing baseline value is 2.

## Implementation and verification

Added explicit area/scene overloads to `RecoveredWorldEntry`, preserving the
existing overloads and checksum/encryption path. Invalid fields reject before
truncation. This does not validate map existence, kind, coordinates or collision.
No production handler or saved character was changed.

Compiled wire frames were decoded by the current native decoder and projected
through the current actor consumer. Six map pairs include town (2,4), baseline
(2,15), and boundary/byte-crossing cases. Tests check resource arguments, actor
area/scene, unchanged kind/coordinates and all unrelated body bytes. Six invalid
inputs reject. Initial test incorrectly equated actor+0x10 with area; native
disassembly identified the independent kind field, and assertions now check both.

Four selected native consumer regressions passed (2.350s); CTest
`recovered_world_entry` passed. The legacy-source test was not executed.

## Remaining live gate

Resource helpers in this test are stubs. This is packet field qualification,
NOT live town entry, asset loading, rendering or walkability acceptance.
Town CityI1 is area 2 / scene 4 / kind 0, while the old indoor fixture uses
kind 2. The MDT navigation path still needs qualification before connecting
this overload to a live town entry; do not reuse indoor collision.

## Explicit kind and native town selection

The extended encoder now accepts an explicit two-bit kind, defaulting to 2 for
backward compatibility. Values 0..3 are representable; that does not certify
every kind/map combination. Native projection tests check all four bit values,
unchanged map/coordinates/other fields, and rejection of overflowing inputs.
C++ assertions verify explicit (2,15,2) remains byte-identical to the baseline
across all 49 profile variant combinations.

`test_current_scene_resolver.py::test_town_packet_selects_native_outdoor_loader`
executes compiled (area2, scene4, kind0) wire through the native decoder and
actor projection, then original 1004F5 scene initialization. Native catalog
lookup, CAN loading/index selection and 6C520 wrapper reach 44B80 with exactly
`\\Data2\\map\\island01\\CityI1\\cityi1.mdt`. No path or branch outcome is
substituted. Coordinates (110,110) are test inputs, NOT a certified spawn.
The existing CRT/allocator adapters and actor resource stubs remain explicit.
Execution stops BEFORE 44B80 creates resources. This proves selection, not
terrain loading, navigation, graphics or a live world session.

Five selected native entry tests passed (2.675s); all three scene resolver tests
passed (1.196s); recovered_world_entry CTest passed. Retired archives were not
read. Current town MDT decodes as v1.2, MAPNUM 9 9, with dwG.rom, materials and
tile definitions; sibling MBD/MDL/MMB files exist but their navigation semantics
are not yet qualified. Disassembly identifies next loader chain 44B80 -> 394B0
construction -> 3C280 load, with surface/resource owners. Do not infer passability
from MDT material letters or fabricate a 9x9 movement grid.
