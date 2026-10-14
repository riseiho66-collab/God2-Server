# TW native actor lookup and wrapper source (2026-10-15)

Round408 connects native Hero key generation and ordinary actor ROM caller
references to the complete pinned bank introduced in407. Existing client
build149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763
and original PE5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde
remain unchanged. Seven complete functions1432B plus77B constants/literals
are individually mapped/PE-equal and statically disassembled. No product code,
client, codec, DBSQL, compiler or tests were executed; unique native credit0.

Actual452460 reads five lowBYTE arguments: family, component kind, component
index, variant and ActType. Family is formatted as BYTE+1 without wrapping.
The exact589140 format is r%d%c%d%02d; width2 is a minimum, not truncation.
588F90 is hex6266687700, thus component order b,f,h,w. The previous407 C
narrative said bhfw; this new original-byte evidence corrects that note without
rewriting its historical capsule. Previous source did not implement that table.

452260 ActType0..2 transforms Body as BYTE(index+3*ActType), Feet using
570C7C={0,1,1}, Head using570C6C={0,0,9,1,5,5,2,6,6,3,7,7,4,8,8}
at index*3+ActType, and Weapon leaves index unchanged. The inverse4522E0
loop qualifies five Head rows. Larger Head indices, component kinds>=4 and
ActType>=3 assertion recovery are outside this safe source subset, never
adjacent-memory table values. All wraps are explicit original BYTE arithmetic,
not narrowing the separate shared64 HP/damage/EXP/coin domains.

452420 reads actual Hero row+2A. A value>=2 adds the sixth BYTE argument modulo
256; smaller values stay unchanged. Missing native lookup returns AL0, but
the qualified C++ API returns absence instead of granting a made-up row/value.
The exact pinned key lookup must still find a real retained row. No source
filename/key equality merges physical rows or makes empty filename valid.

NativeROMRequest owns the exact bank occurrence and complete caller context.
The Hero literal584A04 is backslashData2/Rom/RoleDoll/backslash; Drv58A8A4 is
backslashData2/Rom/Drv/backslash. Actual52F550 cached process-root bytes are
concatenated with these leading-backslash literals and filenames without an
inserted separator, normalization or invented installation root. Hero uses
native-lowercase filename, Drv original raw case. The root is explicitly
supplied, not obtained from a guessed server/client working directory. The
ROM manager/model+1C prefix and actual working directory are separate retained
inputs. The actual manager bank operand is0..511, not source row ordinal or
ROM ACTINDEX. The cache allocator/revision/window owner remains external.

bind_native_rom requires every actual ResourceSelection::Request field to
match the privately generated caller reference. It copies the ROM value into
private const ownership before checking selected original path, whole encoded
bytes and actual full action existence. ResolvedRom retains the private native
request lineage. No file selection, resource decoder, cache write or Current
grant occurs in this adapter. Existing direct-filename bindings retain their
explicit subset contracts. SceneContent already strongly owns the same bank
and pairs complete entry issuer/stored qualification in the actual Context.

Two existing C++ files changed; no new project PY/Lua/CMake/EXE edits. V45 pins
116 current files:114 old pins unchanged,2 updated. Canonical source inventory
is591. Existing CUSTOM-0133 source-adapter provenance is extended; no new native
wire opcode, gameplay grant or claimed complete route is added. TW156/252,
parser77=50partial/11control/16unconnected, pending12/format22/unclassified104,
frontierV27 remain scoped counts. Whole game denominator/percentage stay null.

Next actual implementation is the fresh Context-owned ActorProfile and
complete ReturnScene producer: full ready population/transport witnesses,
actual receiver406, explicit EA405, current resources and complete all-survivor
world/equipment/inventory saved readset joined to the existing final room SQL
cut without callbacks. Opaque6F fields9/17 require explicitly documented
versioned CUSTOM policy if no native authority is available. Source/native
acceptance remain separate; concentrated builds/tests follow all route wiring.
TW100 first stays active; CN/fourWS/sharedtables/saves/453 Traditional names,
client formulas/poison maximumHP/10/fonts/text/shared64/coin99999999999/stack99
and original levels/907 declaration pins remain preserved.