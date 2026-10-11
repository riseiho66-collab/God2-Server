# Current GOD definitions and owned selection

## Evidence and scope

Current Taiwan client: `God2.exe` SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Mapped native image: `native-master-01-stable.bin` SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Current gamedata source SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
Addresses below are VAs at image base400000.

GOD is recognized through native ItemType, not through a separate parser.
ItemType has46 rows, calloc stride642h; the GOD row is ordinal2. Original
004591C0..00459350 parses all46 rows. GOD is absent from the36 first-match
item tags and retains zero selector at category+63D. Original00459380 lookup
returns ordinal2/selector0. Dispatcher004561A7..004561D7 calls004599B0, which
indexes via00459A20 and invokes the generic396-byte parser00459420.

`current_deity_metadata.py` executes the original tokenizer, all category row
slices, original section lookup and all34 GOD row parsers. Allocation/stream
fixtures are explicit; this is not execution of the full file/heap loader.
Output guards and read-only category allocation bound the native writes.
The parsed category allocation SHA is
`9f98d098d88e36428ed9af7a25576703baf5d38b1310b8b0ea78f000a9bcee0c`.

Original header is `GOD,34` on physical line6127; records are lines6128..6161,
metadata keys2801..2834. Source and parsed cache SHA256:
`ed8c71d8bc2d276b4534df1389138f98096fce78f9128c451f9d110faba484df`.
Keep every raw source field and original parsed byte. For example field5=1791
in the first row is not promoted as attack, price, cost or a formula without
a qualified semantic consumer. Model strings likewise do not establish spawn
coordinates or recruitment rules.

## Original-client checks

The hidden client loads all34 entries. A read-only observer compares all396
bytes with the original parser, normalizing only icon binder+116..119.
Original binding of source icon1 is bank65/action0. Native owned keys1/2
read names姜子牙/鄧嬋玉 from metadata, ignoring deliberately different packet
names. This is separate from HUD bank5/action0/1 with ACT IDs1001/1002.

The GOD panel callback004A8AA0 uses controls40/41 for previous/next selection;
the actual jump table004A8DE4 resolves40->004A8C88 and41->004A8CB3.
They invoke004A9950/004A9910 and producer004962E0 for C2S67. Control42 is skill
paging, not deity selection. Native mode0 closes the panel through F11 route
004AD800->004A8990; mode1 opens it via004A87C0 and updates HUD through004AE150.
Input loop005048BC..00504934 requires widget flag20h. Flag10h is not an
input-enabled panel. The widget linked list at UI+E2170+14 controls hit order;
only preceding input-enabled widgets can consume a click first. Control bit80h
affects drawing and must not be used as an input visibility flag.
The separate Ctrl+S route requires native modifier handling; unmodified S
does not prove opening the panel.

Failed private runs are retained and are not acceptance. Run01 failed on an
observer NameError; runs02..04 also exposed an observer function split that
left key-up unreachable after a helper return. Runs05..06 could not open the
panel via the attempted shortcut. Runs07..12 exposed the observer's incorrect
widget flag and hit-order interpretations; retained overlap records were not
proof of visible panels masking the button. Original input-loop tracing fixed
the observer. No client/UI-memory patch was introduced.
No failure modified production saves or either client EXE. These failures
qualify observer repairs; they are not recovered gameplay or formula data.

`artifacts/playtests/private-deity-templates-20260927-13/run-result.json` is
accepted against candidate SHA256
`cbe14bdad5428258c3973c51f7782380a7c7127cab0d674b63bd78c65b6b2588`.
It compares all34 live metadata rows and the two owned names, performs all five
mixed-generation pet drags with sprite checks, and then clicks native controls
41/40. Selection revisions are (key2,rev2) -> (key1,rev3); HUDs are actual
bank5/action1/ACT1002 -> bank5/action0/ACT1001 with valid image resources.
No NATIVE_CLIENT_DIAGNOSTIC appears. Original and port-only client files,
source DB and input desktop remain unchanged. Initial instance stats/skills
are synthetic fixture operands, not native acquisition or formula authority.

CTest `native_deity_metadata` passes both full source/parser/category and
atomic/idempotent conflict/corruption tests. `native_deity_templates_server`
passes native low-key restore, actual C2S67 response, mixed E3/FB transfer and
process restart/lossless persistence against the exact accepted candidate.

`artifacts/releases/native-deity-metadata-20260927-01` is INSTALLED. Formal
schema37 contains34 GOD +1165 NCP definitions (1199 combined) and2070 COM
definitions. Listener PID2684 remains running without restart. The import
transaction proves every non-catalog table, every schema and existing catalog
rows unchanged;4 accounts/3 characters are preserved, no owned deity is
granted. The exact34-row live readback matches the pinned cache.

Scoped progress: native GOD definition import34/34 (100%). Two native-template
owned selection/portrait flows passed; all34 playable acquisition/skills/
battle/growth flows are not claimed. Original deity growth activation remains0%.

## Runtime integration and remaining work

`SqliteCompanionRepository::template_keys` already reads familyGOD metadata
keys2801..2834 and qualifies the source hash before mapping to owned keys1..34.
Owned restoration/select_deity uses that catalog, owner validation, pending
battle exclusion and persistent revisions. All owned fixture statistics remain
CUSTOM_TEST_NOT_NATIVE under CUSTOM-0039; this import grants no instances.

Catalog promotion uses one BEGIN IMMEDIATE transaction. Every table schema,
every existing catalog row and every non-catalog saved row must remain exact
before commit. Only34 GOD definitions may be appended. No full-DB rollback,
client changes, binary changes or service restart is required.

Unresolved: original recruitment/acquisition, starting statistics, growth,
EXP thresholds, skills/costs, combat calculations and all-GOD playable flows.
Metadata/selection acceptance cannot be reported as these systems completed.
