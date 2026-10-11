# CN primary CRT WinAPI caches and actual lookup sources

PHASE1 file-only static source recovery. No native/API/DLL/emulation/server execution, build/test, gameplay DB access or deployment. Native levels unchanged. CN SHA256 582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.

Two actual cache resolvers00793212 and00754938 have70 rel32 byte candidates. 37 align with metadata-entry rooted CFGs. Each literal argument sequence is preserved separately; missing metadata helpers are not silently promoted into actual function-entry/global reachability claims.

Four immediate pushes recover70 lookup argument sequences, mapping32 UCRT and5 VCRT function IDs to exact ASCII names, encoded function cache slots and DLL candidates in original order. Primary DLL pointer tables have20 and3 entries. These are cache IDs and API names, not packet opcodes or completed routes. Primary bytes, per-call qualification, modules and source spans are retained.

UCRT startup00793E1F initializes32 encoded-null slots at9FA8F8; resolver00793212 decodes ROR32(cell XOR cookie,cookie&31). DecodedFFFFFFFF suppresses retries; decoded0 attempts module lookup/GetProcAddress and publishes encoded success or missing sentinel with actualXCHG. UCRT module helper007932AE uses LoadLibraryExW flag800h and only error57h permits flags0 fallback. Uninit00793F72 argument0 frees nonzero/non-FFFFFFFF cached module handles at9FA8A8..9FA8F8 and clears cells.

VCRT00752BB9 directly calls00754BAF to initialize5 slots at9F9A78, separately from UCRT. Module range has3 cells beginning9F9A6C. Its module-loop00754874 additionally excludes api-ms-/ext-ms- names before the error57h/flags0 fallback. Uninit00754BD8 argument0 frees cached handles and clears cells. No original DLL is loaded by this reader; file IAT values are metadata, never loaded addresses.

Uncached resolver00793329 is a separate GetProcAddress path and is not closed by recovering the32+5 cache IDs. Previous open tail0074A8E2 is retained as primary JMP[AAFD78] declaring IsProcessorFeaturePresent; this still does not observe its loaded target. API names or cache coverage cannot prove absence of runtime VEH/SEH/signal/context modifications elsewhere. CN1E outcome remains unknown.

New packet values/owner chains/source bindings/full bidirectional routes all0; whole-game denominator and completion percent null. Frozen/common runtime source byte-identical; only native decoder provenance gains this reference. Next connect actual missing helper callers and uncached lookup sources while continuing actual auth/permission/guild/replay/full02/03/common-host sources; no invented permission or success response.

Source correction: actual metadata-rooted boundaries at00793DE1 disambiguate an apparent PUSH decode beginning inside an immediate. All70 literal sequences are retained,37 with metadata-rooted argument boundaries and33 as literal candidates only. Initial unsealed69-sequence draft retained; no historical acceptance baseline changed.
