# CN native SKB bindings and common preborn source handoff

Round `20261008-cn-native-skill-book-bindings-source`; PHASE1, source only.
Previous user-status turn was no progress; resumed the available static native
lookup/resource work. Prior136 sealed output remains immutable. Saved144 current
files before edits, including the unchanged TW NativeSkillBookCatalog reader.

## Actual native source

Pinned CN PE SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
Primary individual recovery files and entry-rooted local normal CFGs are retained;
this is disassembly/file analysis, never native execution or an emulator.

`004D2BB0` (378B) takes BYTE kind, BYTE definition ID and an existing WORD
out-item. It retains actual this at `[EBP-1A8]`; item lookup this is
`[actual_this+65364]`. Primary table `007F3B44` contains four DWORD bases
6500,6600,6700,6800. The formatter/category order is **A,D,C,B** for kind0,1,2,3.
Kind0 uses `SpcA%02d` below100 and `SpcA%3d` at100+; other kinds use their
`%02d` string. Qualified BYTE IDs100..255 occupy three digits without padding.
No localized name is involved.

For offsets1..399, it calls `004283A0` on base+offset; this reader accepts
WORD item IDs below35000 and reads its own table+`B304C+item*4`. For each
non-null row it copies99 DWORDs (396B). Comparing stack copy+11C to the formatted
selector uses `strncmp` with6 bytes for ID<100,7 otherwise. The **first ascending
item ID** wins. A six-byte selector such as SpcA10 also prefixes SpcA100..109;
these candidates must not become an ambiguous database join or pick the last row.

At a match it writes the out-item and returns the item-reader EAX. On no match,
the original out-item is retained and looked up; the decompiler's `void` prototype
does not remove the actual EAX result. This source supplier exposes only whether
an SKB matched; native caller-specific fallback state remains open.

`00428C80` allocates396B per item through `0076C3BF ->00790027`, installs the
actual item-pointer index and calls `0042CFB0` with the native item type.
`0042D6B0` resolves each loaded ItemType name through40 primary tag pointers at
`00886338`; `SKB` is native type6 and `PFD` is type9. This classification is
independent of the ItemType CSV row's ordinal11 for SKB.

`0042CFB0` has a primary39-byte type map at `0042D518` and nine branch targets
at `0042D4F4`. Type6 maps to `0042D41F`: column26 is copied to parsed+11C,
parsed+12B is NUL, then columns27/28/29 go to bytes12C/12D/12E. `004231B0`
returns an empty token for an absent field; `00423270` returns zero for absent,
empty or failed decimal conversion. This does not establish MP/range/cost rules.
The new supplier retains the raw tail strings and does not invent an entire
396-byte parsed item, RomMaps-derived indices, or native integer semantics.

The full search intervals contain386 SKB,65 PFD and47 GEH rows in this pinned
file. PFD type9 maps to the parser default. GEH matches no primary tag; its
zero-initialized type byte remains0, also the default. Neither writes+11C.
Actual calloc uses HeapAlloc flag8, so those bytes remain zero and cannot match
the Spc selectors. The broader ItemType-name census discovered GEH after the
initial abbreviated tag-only census; both interrupted static deliveries are
preserved under attempt-01/02, rather than silently discarded.
Retained section census checks actual item-section names and pointer-range ID
collisions; no non-SKB candidate is silently omitted without this source basis.
Normal CFG completeness excludes helper exceptions and runtime reachability.

## Pinned resource and source increment

Read the already-retained exact resource pair from
`cn-current-npc-name-source-01/inputs/current-gamedata.csv[Z]`; no decoder was run.
Encoded795868B SHA256
`8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a`;
decoded3042675B SHA256
`16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3`.
SKB header line9441 at decoded739098;386 records occupy739107..806862.
229 rows have30 fields,157 have29; all use CRLF without CSV quotes.

The static material preserves all raw rows/hashes/source lines/offsets and each
declared CN definition's selector, ordered matching candidates and first match.
453 definitions yield386 matching books and67 no matches. All five CN-only
definitions have a matching book: kind0/122->6897,0/123->6898,0/124->6698,
0/125->6699,1/130->6697. These remain version-scoped identities; they are not
proved cross-version common gameplay mappings.

Added `CnNativeSkillBookBindings`: owns copied source bytes during hash/parse,
pins both input hashes and build, retains386 owning raw book records, and resolves
native first-match bindings with the **same actual CnSharedSkillCatalog**. It
returns actual shared-table CN definition plus optional matching book. Invalid
source/definition returns no result; a valid definition without SKB is explicit.
Lookup_words preserves raw83 WORD order and duplicates. No pointer access,
process memory, name join, TW fallback, item granting or synthetic entitlement.

Existing `SharedPrebornWindowSource` now accepts an optional supplier and checks
it uses the identical shared catalog. If configured, each selection is resolved
once into owning bindings; definitions are copied from those exact bindings and
both vectors are retained through the existing common apply and post-commit
qualifier. No provider means evidence unavailable, distinct from a definition's
no-book result. Real common subject/skill mapping, eligibility, Lua rules, single
transaction/save/persistent replay and committed output still belong to apply.
No retired preborn Current is queried after the actual common commit.

No new table, `_tw/_cn` split, migration, DB import/access or default issuer.
Existing shared native_skill_catalog/native_data_sources remain the definition
store. TW NativeSkillBookCatalog and its existing396B schema/reader are unchanged;
this raw CN projection is not inserted as a fake complete parsed DB row.
Actual shared CN rows, supplier binding, common authority and Application are
still unconfigured. This is a concrete data-source/handoff increment, not a
complete packet/gameplay route or production result.

## Accounting and preserved goal

New resource-binding supplier1, existing common-operation handoff strengthened1;
new opcode/phase associations/partial network owners/complete routes0.
Full-game denominator and completion percentage remain null. Full TW/CN/PC/web,
WSS, all world/content/combat/social/guild/alliance/town/interior routes, numeric64,
coin99999999999, stack99 and later comprehensive testing/repair/release remain.
No build, tests, APIs, C++/Lua/native/server execution, database or deployment.
Accounts/saves/chat/IME/auth/portraits/fonts/text conversion/levels/client binaries
and earlier evidence are preserved.
