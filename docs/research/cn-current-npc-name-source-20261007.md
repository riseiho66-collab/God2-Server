# Current CN NPC name source, 2026-10-07

This round statically restores the current pinned encoded gamedata resource and
connects its actual NPCAppearData name projection to the existing conditional
F9 owner. The historical resource/catalog and all previous source receipts stay
unchanged. Native loaded-state, permissions and gameplay publication are still
required; this data/source connection is not a native acceptance run or a full
star/bounty gameplay route.

## Exact resource identity and static recovery

Current executable SHA256 is582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.
Encoded Data2/Patch/Comm/gamedata.csvZ has SHA256
8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a.
Statically recovered bytes have SHA256
16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3,
3042675 bytes, exactly the already retained current scene-resource receipt.

The bounded Python static resource extractor is snapshotted before use. Its
0045A060 contract checks signature0516 and declared length, then reads the LZSS
token stream. It initializes the observed first0xFEE ring bytes and rejects any
reference to the uninitialized remainder. It runs solely on copied input bytes.
No native asset loader, executable, Lua, gameplay or test was run. Static resource
extraction occurred and is explicitly recorded; it is not concealed as an
unchanged-input read. No new acceptance baseline replaces the historical pair.

## Current names and historical difference

Current NPCAppearData has4466 ordered input rows,4464 final selectors, maximum6553.
Each row retains its physical line, decoded offset, raw record hash/bytes and
name prefix through the native firstNUL/truncation.64 source names exceed15 bytes.
They retain native byte truncation, including any split multibyte character.
Raw byte parsing is used for this section; no whole-file replacement decode or
Unicode normalization is used. All source selectors are nonnegative and<7000,
and name fields have no quotation bytes and individually decode as CP936.

All4459 historical final records and consumed name prefixes are unchanged.
There are no removed keys. Exactly five current selectors are added:

| Native selector | Current source line | Name |
| --- | ---: | --- |
| 6549 | 4581 | 欧冶子 |
| 6550 | 4582 | 月汐自选宝匣 |
| 6551 | 4583 | 星火自选宝匣 |
| 6552 | 4584 | 灵曜仙官 |
| 6553 | 4585 | 新神仙火套男 |

Key6195 repeats with an identical name. Key6276 repeats with五行魔自选包 followed
by五行封自选包; the last direct-index loader write wins. Both overwrite events
are retained. Appearance-source identity/name keys are not common actor IDs,
spawn rules, monster combat values, equipment ownership or carried skills.

## Source integration

CnCurrentNpcNameCatalog contains the4464 final current name prefixes separately
from CnNpcNameCatalog's historical4459 entries. Each profile requires its own
encoded/decoded hashes, the pinned executable, positive actual resource revision
and independently supplied actual native maximum. The maximum is not inferred
from a packet or automatically asserted as observed live state.

SharedSpecialDirectory's existing selector25 path selects a current or historical
projection only by exact resource identity. It still accepts fully supplied name
evidence and requires the real WorldOwner to qualify loaded source, revision,
permissions, capacities and native issuance. Missing sparse keys fail; there is
no fallback from a current missing key to the historical namespace. Array bytes
after firstNUL are local unread evidence padding only, never native-memory claims
or new wire fields. F9 remains the complete2105-byte supplied record; names are
client-resource lookup proof, not an appended S2C string serializer.

This closes the static current-name-source gap found in catalog40. It does not
close actual resource-loaded-state, source revision/native maximum observation,
star/bounty common data/rules or production Application supplier gaps. New native
opcode values, new phase/opcode bindings and complete bidirectional routes are0.
Whole-game route total/percentage remains unknown. No DB access, client/server
execution, build, tests, native acceptance, deployment, fonts or text-conversion
changes occurred. Previous goal turn is progress: historical resource lineage,
raw names and the current/historical mismatch changed this round's action.
