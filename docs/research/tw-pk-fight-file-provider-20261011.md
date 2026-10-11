# TW282: explicit bounded Fight archive file provider

CUSTOM-0120 is inactive Phase1 source integration. No build/compiler/test,
runtime/native/VM/codec execution, game database SQL, schema installation,
migration, activation or deployment occurred.

## Concrete source connection

TaiwanNativeFightCatalog::from_archive_file now accepts an explicit
std::filesystem::path. The provider copies the path and opens one binary stream
directly with that native path, preserving Windows Unicode names. It performs
one bounded read of audit_size+1 (2,853,352 bytes), accepts only gcount2,853,351
with EOF and no badbit, then supplies those exact bytes to from_archive.
Empty/unopenable/short/extra/non-EOF/bad reads throw. No file_size-before-open,
second open, narrow path conversion, Z suffix, fallback search or resource
decoder is involved. The fixed audit_size is also the existing span factory's
exact length check; the underlying length requirement is unchanged.

The existing factory owns a complete byte copy and verifies SHA256
5500950022f789d1372f92fe2dd6ebee936c2e7f5a04b133c45151f3aabd142d before parsing
JSON, then validates archived identities,3578 rows, sequence, seven fields,
unique keys and numeric syntax. A pathname, reported digest, metadata flag or
valid JSON alone cannot qualify the catalog. Subsequent file changes do not
change the already owned immutable catalog. This does not promise filesystem
immutability, special-file I/O timeouts or original asset decoder fidelity.

SqliteDatabase::make_owned_taiwan_pk_entry_preparation_from_archive connects
this file provider to the established same-Database preparation factory. Pure
checks for migrated/impl/presence/repository identity and all four resolver
owners precede file I/O and writer assembly. It loads a fully qualified catalog,
then delegates to the existing factory. The new method invokes no resolver,
prepare(), room reservation, schema installer or Session transition.

Catalog Storage owns its bytes/rows through shared immutable lifetime. Database,
room repository, presence and resolver owners retain their existing borrowed
lifetime/game-executor contract. The loader does not repair incorrect owner
lifetimes or make SQLite/Session operations thread-safe.

## Exact input and provenance

The existing exact input is the TW266 archived native.json at:

`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-fight-catalog-source-266/root/archived-inputs/current-armor-mapping-sources-20261002-run02/native.json`

TW281 retained its verified extraction witness and actual bytes. It is the
2853351B/550095...abd142d JSON input, not installed HeroDoll_Fight.csvZ. The
36974B/1195af...63338b8 encoded asset and recorded decoded hash remain distinct;
no CSVZ decode or whole-tree restore was performed. Historical c5d8 parsed
Unicode data representation is not current149c code authority or raw CP950 CSV.
The existing current-native selection semantics remain separately qualified.

## Later-grant research remains separate

Bounded reread of retained current149c grant consumer517590..5177B8 confirms
BYTE3 flags, BYTE4 primary/secondary nibbles, and unsigned WORD5+1 converted to
three decimal glyphs. Only the lowest three digits are displayed. That WORD
does not write the88 counter, timer, target mask or a server grant epoch.
Every grant records a new local timer origin and reloads the existing countdown;
slot/controller writes remain flag-dependent.

This is consumer evidence, not an original producer formula. CUSTOM-0110's
initial WORD5=0 and own-slot grant remain initial-only. CUSTOM-0117's fresh88
counter policy is a different explicit source. Later transport epochs, actual
control-mask policy and original labels remain separate. The repository guard
rejecting later grants is unchanged; this work does not reuse initial bytes
as later native authority. Worker terminal gives exact qualified read scopes.

## Hosting and accounting

Application pk_rooms remains null. No Config path/default or invitation enable
is added. A future full owner must explicitly supply the archive path and
actual seed/basic coefficients/order/next masks/Lua lifetime/idle output
scheduling, then close later grants, skills/other35, terminal89, saved settlement,
fresh world return and reconnect/restart. TW281 current durable frozen-profile
source is preserved. The file factory alone is not a hosted PK gameplay route.

Three existing C++ files modified, zero new C++ files. One inactive concrete
file-to-preparation source path added; zero new opcodes/full bidirectional
gameplay routes. Source segments264->265, CUSTOM records117->118, groups26
unchanged. TW C2S candidates156, world parser74 (source50/control11/unconnected13);
S2C252 (230 fixed/22 variable), reply48/push11/gated4 unchanged. Battle110 with
specialized9;86 selectors7/cases6;83 actions23/projection2 unchanged. TW unhosted
chains3, bindings38/unique34; CN chains35, bindings93/unique71 unchanged. CN
historical C2S156/S2C phase-opcode280/length253 remain a separate scope.
Full route denominator and completion percentages remain null.

TW/CN/web/shared64 full objective and frozen saves/auth/chat/IME/fonts/text
conversion/client binaries remain intact. Webv70..75 metadata remains pending
actual source/commit review; no new ACK/credit. Evidence archive:
C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-fight-file-provider-282
