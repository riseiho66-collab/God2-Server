# Native pet2 categories: storage, owned route and formal release

## Qualified original data

Current `Data2/Patch/Comm/NewCombatPet_Category.csvZ` SHA
`80c2b7d366d2ef0264df78f20de1b20fa21e14f6592f56676b090f83ddc064c6`,
decoded SHA `f8d1a1c22e8fc9195dd625ffc244e2ebbcee07492116976feece0bd9d26b813b`.
The source literally declares469 rows but supplies464, group1..29/index0..15.
All464 names were loaded by original row code5C6A6..5C9B5, then selected by
unchanged FB caller A4525..A4567 and original gate5C9E0/getter5CA00. High nibble
noise and upper register noise are explicit test operands. Native input labels
and complete raw records are preserved; no growth coefficient is generated.

FB body+2C low nibble supplies category index; body+3C unsigned byte supplies
group. Original gate accepts1..29 and0..15. Category getter returns22 bytes,
including the CP950 NUL-terminated name, for original panel control16 型態.
Example qualified labels: (1,2) 力速A; (29,15) 智速E. There are27 distinct name
byte strings across464 indexed rows. Neither letter suffix nor star rank/rating
proves a join to Bahamut 普/頂/晚破/破頂 or its species/generation grouping.

The six original flags are not reinterpreted as growth values. Y writes1 in the
qualified row slice; N leaves the supplied allocation bytes untouched. The
import stores raw source flags but exposes only qualified names. Original row
code does not read columns9..11, including Base100_Index37. No base statistic,
probability or formula is inferred from those literal columns.

## C++/SQLite integration

- Migration36 adds `native_pet2_category_source` and
  `native_pet2_category_rows`. No saved player row or previous migration SQL
  is rewritten.
- `NativePet2CategoryCatalog` checks all464 ordered keys and a fixed complete
  canonical dataset SHA `de6cada4b90996515a0e371eb8d503a39718b45a9103b9259c1f7f483b569772`.
  Truncation, source mismatch, orphan rows and changed raw/name bytes reject.
  Missing/unimported or original-invalid selectors stay explicitly absent.
- `RecoveredPet2Stats::Record::category_selector()` exposes the native pair.
  `SqliteCompanionRepository::load_pet2_slots` resolves display metadata on
  authenticated owned loads. Acquisition results and slot transfers preserve
  the resolved category and the entire native instance. World restore and
  select/swap/return log the resolved pair; no speculative packet or formula
  is sent and no name-only species join is made.

## Acceptance and repairs

Native importer tests:3 PASS. Actual original caller/getter returns the exact
name for every row. C++ tests cover4096 group/index inputs (all256 group bytes,
16 low-nibble indices), packet immutability and transactionally rolled-back
corruption cases. Owned persistence/selection C++ test PASS. Six same-candidate
server transport/restart/negative-owner tests PASS.

Hidden original-client receipt:
`artifacts/playtests/private-pet-categories-20260927-01/run-result.json` PASS.
Two synthetic owned instances use category pairs(1,2),(29,15), levels37/98,
star pairs10/5 and5/10. Complete SQLite records equal read-only client caches
after reserve42→active44, reserve43/active44 swap and active44→empty42.
Server logs confirm both initial category resolutions and all three committed
destination pairs. Source fixture DB and both client binaries are unchanged;
desktop selection is unchanged. These instance numbers are synthetic operands,
not recovered original starting stats. A rendered open category panel was not
part of this live test; original category name selection was executed offline.

Initial importer tests exposed a Windows temporary-file cleanup lock. The DB
is now closed before its temporary directory exits; tests reran successfully.
Initial release stage01 used `stage.db`, which the diagnostic configuration
correctly rejected. Stage02 preserves the required `town-diagnostic-accounts.db`
basename and passed. No failed stage touched the active server or live saves.

## Formal promotion

Release `artifacts/releases/native-pet2-category-20260927-02` is INSTALLED.
Same accepted candidate SHA:
`0bd2e21cde26444c32ba6faef88d3c590a4e3a6ad7d1f7179cc4b796e5a31785`.
Fresh original NCP extraction/parser verified1165 native definition records,
then both NCP metadata and the464 category rows were imported into the formal
configured database. This is static definition metadata, not wild-monster stats
or player-owned acquisitions. No pet instance was granted.

All previous player tables and old migration history were compared before
service restart and remained identical. Original binary and SQLite backups are
retained in the release. Production config/client hashes are unchanged.
Schema36; localhost2592 service PID19256 confirmed listening. Post-release
verification also opens the formal category catalog read-only through C++ and
checks its entire pinned dataset. No negative mutations are run against live DB.

Formal source catalog integration:1165/1165 NCP and464/464 categories (100%).
Three isolated owned transfer stages:3/3 (100%). Original pet-growth formula
activation:0%. Whole-game playability remains incomplete and unmeasured.

## Next targeted recovery

Original logical E3 is53 bytes (52-byte body), dispatched6919E→A2B70,
not the FB73-byte/72-body path. A2B70 validates body+26 slot42..44 and
body+1C metadata key via A2980/A29A0, then copies13 DWORDs to
UI+9E50+slot*52. Accepted native key ranges are3391..3778 and5DC1..6D60,
and actual native metadata lookup is additionally required. Its field meanings,
generation/species binding, growth-class encoding and owned persistence are
not yet qualified. Continue this distinct path before applying the general-map
first-generation growth table to FB instances.
