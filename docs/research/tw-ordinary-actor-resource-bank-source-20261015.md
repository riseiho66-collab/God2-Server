# TW ordinary actor resource banks and selected ROM linkage (2026-10-15)

Round407 implements the ordinary world Drv and HeroDoll source banks in C++.
These are distinct from DrvDoll and Fight appearance resources. The whole
client-derived plaintext pins are Drv3899B/92rows/72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0
and HeroDoll37189B/918rows/0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2.
The original mapped build remains149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.

The constructor owns both entire plaintexts, checks SHA256 and exact envelopes,
and retains all1,010 physical rows, CRLF, ordinal/line/offset and every cell.
Raw CP950 comments stay bytes. Drv firstrow isline10/offset206; Hero firstrow
isline26/offset504. Drv comments contain commas:87rows have9cells and5have10.
Hero has886rows with7cells and32with6. No generic quoted CSV interpretation,
empty numeric replacement, locale parsing or UTF8 reinterpretation is used.
The fixed original subset uses unsigned ASCII decimal cells. SHA256 provider
and hash handles use exception-safe lifetimes; no product parser was executed.

Drv32B source lookup uses the native physical ordinal rather than column0's
label; larger/negative WORD aliases are refused by the qualified safe subset.
Hero44B lowercases concatenated source columns0+1 and the ASCII filename;
original fields/rows remain byte-exact. Drv column2 is ActType for452260 key
transformation, not a ROM animation operand. All918 keys are distinct;
shared filenames retain different row identities. Native cached WORD FFFF is
recorded as a constant, never replaced by a fabricated valid resource handle.
Drv row0 and24 Hero rows have genuinely empty filenames. Binding those rows
fails without silently choosing another appearance. Hero column5's lowBYTE
is retained as the native component modifier; other numeric fields retain
source-qualified numeric identity without inventing a gameplay meaning.

ResolvedRom keeps strong ownership of the bank occurrence, actual original
resource selection and immutable parsed ROM. The selected request must name
the exact qualified row filename; selected actual path and whole encoded bytes must
match the ROM. The caller supplies the actual full animation operand; the
existing qualified ROM lookup must find it. Drv/Hero metadata is never used
as an assumed action ID. This qualified direct-filename subset does not yet
construct native wrapper paths or cache-manager operands. ROM action<=256 is
positional, larger values use
the first actual matching ID. Missing action does not become action0. This
join supplies source correspondence, not a native cache index or rendering,
window, actor ownership or full resource Current authority.

The same strong bank reaches the actual private SceneContent, mandatory
complete SceneSupply, paired entry issuer and stored qualification through
StoredSources::with_scene_entry_content and the real Application Context.
Before/after producer and existing CAS/read qualification retain exactly the
same immutable bank identity. Existing overloads preserve their contracts.
No new implicit installation or startup activation is introduced. Full native
2A/6F producers, opaque fields9/17, current world population/interest rules,
all survivor saved equipment/world readsets and full terminal return producer
remain open. Merely making this bank available does not complete those routes.

Evidence is external under20261015/round407-tw-actor-resource-design and
round407-tw-actor-resource-native-source; the root receipt records exact seals,
byte coverage and independent review. New native credit follows that receipt;
previously retained native bytes and table rows receive no new native credit.
The source extends existing CUSTOM-0133 adapter provenance, not native server
permission. CMake's existing src/*.cpp recursion includes the new C++ source.
No new project Python/Lua/CMake/client EXE changes, builds, tests, runtime,
resource codec, game SQL/import/migration/activation or deployment occurred.
TW100 first remains active; full route denominator and percentage remain null
until complete authoritative bidirectional routes are actually connected.
453 Traditional skill names/client formulas, poison maximumHP/10, common CN
and four binaryWS endpoints, saves/fonts/text and shared64 numerics remain.