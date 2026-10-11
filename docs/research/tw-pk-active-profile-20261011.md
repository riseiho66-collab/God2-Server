# TW281: current durable binding to the admitted PK profile

Static source work only. CUSTOM-0119 remains opt-in and inactive. No build,
compiler, gameplay test, runtime, native client, VM, codec execution, database
SQL, migration, activation or deployment was performed.

## Removed concrete dependency

TW280's basic/control dispatcher required the caller to supply a separately
current profile digest, but Application had no concrete issuer. The new
no-profile-argument overload obtains that binding through the actual privately
bound RoomState and its current shared Battle. It preserves the old explicit
profile seam for existing trusted adapters; it does not relabel that older seam
as internally qualified.

`SqliteOwnedPkRoomRepository::require_active_owned_profile` validates the
original repository issuer and complete private combat/appearance/player/vital/
initial-grant/initial-context graph. All sources must use its actual connection.
Existing complete Input validation recomputes the internal domain-separated
digest, and the complete serialized retained readset must match the Ticket.
Legacy hash-only inputs cannot acquire this new source qualification.

One explicit BEGIN read snapshot then checks:

- All thirteen main tables consumed by the PK and owner readers exist; relevant
  TEMP names/table associations cannot shadow them. Existing PK DDL/version
  checks perform no installation.
- The durable room is active with exact full readset/design and both member
  locks. Existing saved role/resources/position equality and independent-battle
  exclusion remain in force. Exactly two member rows are required.
- The complete canonical persisted checkpoint equals the actual RoomState
  Battle checkpoint, including RNG, HP/MP, numeric profile, identity and revision.
  Admitted topology/immutable actor properties remain bound. Revision1 must
  equal the original initial checkpoint; no reseeding or reconstruction of the
  current battle is used.
- The full persisted round decodes consistently with checkpoint revision,
  active state, private contexts, headers and initial notification bounds.

Only after successful read commit does the method return the admitted digest.
`OwnedPkRoomState::current_owned_profile` derives the Ticket and expected full
checkpoint internally from its actual runtime-claimed Room. Native/scalar
callers cannot provide this expected checkpoint through the dispatcher.

The new dispatcher overload checks the exact Session/private Written binding,
copies server basic coefficients, obtains this current durable binding, then
delegates to TW280's complete-frame preflight and private control/basic path.
Read-only qualification can occur before classification; every record is still
classified before any durable control/intent mutation. Unsupported mixed
suffixes never leave a committed prefix. Tick-only still requires the binding.

The explicit paired basic resolver also obtains the concrete binding and
requalifies it before/after each pure Rule callback alongside its original
snapshot/round/transport/reentry fences. This is preparation-time evidence;
existing write transactions retain full checkpoint/round/readset CAS and own
grant/outbox guards. A read snapshot is not a future lease, a Session+SQL atomic
operation, or permission to reuse a stored digest indefinitely.

## Frozen battle data is intentional

The existing repository policy invokes recursive `stored_current` only while
RESERVED. That helper traverses the complete prebattle world/inventory/equipment/
root/pose/auxiliary/text graph. Live Current additionally requires the original
prebattle Session phase and lease, which intentionally expire at battle entry.
Neither helper belongs in active profile qualification.

Active combat keeps its admitted immutable attributes, appearance and text.
Current combat HP/MP and RNG come from the one shared Battle/checkpoint; saved
resource rows remain unchanged until the separate terminal settlement policy.
The new method preserves existing saved role/resources/position checks without
equating saved HP/MP to combat HP/MP. It does not refresh auxiliary totals,
inventory, equipment or title during a fight. CUSTOM-0106 stored-total adoption
remains custom, not recovered original formulas or learned-skill permission.

## Fight archive research and next hosting step

The bounded worker audit located the exact existing archived JSON input:

`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-fight-catalog-source-266/root/archived-inputs/current-armor-mapping-sources-20261002-run02/native.json`

It is 2,853,351 bytes, SHA256
5500950022f789d1372f92fe2dd6ebee936c2e7f5a04b133c45151f3aabd142d.
The retained extraction receipt has archive_verified=true. Current installed
HeroDoll_Fight.csvZ remains 36,974 bytes with encoded pin1195af...63338b8, but
CSVZ is not the JSON factory input and was not decoded here. Historical c5d8
parsed Unicode fields and current149c consumer semantics remain distinct;
recorded decoded metadata is not a newly reproduced decoder result.

TaiwanNativeFightCatalog already validates the complete JSON pin, row count,
sequence and keys before returning its privately owned catalog. Application
has no filesystem provider/configured archive path yet. The next source action
is an explicit single-open binary reader bounded to exact size plus one byte,
rejecting short/extra/bad reads before the existing factory. Do not use native
TextFile suffix/fallback selection, decode resources or restore a whole tree.

## Remaining scope and accounting

Application pk_rooms remains null. Trusted seed/basic coefficients, server
order/next masks, Lua lifetime, explicit idle-boundary output scheduling, later
grants, skills/action2/other35 variants, terminal89, saved awards/settlement,
fresh world return and reconnect/restart still require complete composition.
The new binding closes the basic dispatcher's external current-profile source
dependency; it does not supply these other owners or activate a PK host.

Four existing C++ files modified; zero new C++ files. One inactive concrete active
profile source chain added, zero complete bidirectional gameplay routes or
opcodes. Source segments263->264, CUSTOM records116->117, groups26 unchanged.
TW C2S candidates156, world parser74 (limited source50/control11/unconnected13);
S2C252 (230 fixed/22 variable), reply48/push11/gated4 unchanged. Battle110 with
specialized9;86 selectors7/cases6;83 actions23/projection2 unchanged. TW unhosted
chains3, bindings38/unique34; CN chains35, bindings93/unique71 unchanged. CN
historical C2S156/S2C phase-opcode280/length253 remain a separate inventory.
Whole route denominator and completion percentages remain null.

TW/CN/web/shared64 full objective and frozen saves/auth/chat/IME/fonts/text
conversion/client binaries remain intact. Prior webv70..75 metadata pending
actual source/commit review remains pending; no new ACK or integration credit.
Evidence: C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-live-profile-281
