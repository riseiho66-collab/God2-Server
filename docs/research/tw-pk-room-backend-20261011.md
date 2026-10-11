# TW287: one owned PK preparation/admission/basic backend

CUSTOM-0125 adds `OwnedTaiwanPkRoomBackend`, an actual AsyncRoomAuthority
composition assembled only by `SqliteDatabase::make_owned_taiwan_pk_room_backend`.
The factory takes the actual initialized Lua/game executor, common presence
and visibility, explicit pinned Fight archive path, four live source callbacks,
bounded basic coefficients, two-viewer execution order and retry cadence.
It checks nonempty executor/callback/path, exact character/presence/visibility
identity and existing policy bounds before archive I/O or reader assembly.
The existing single-read/hash-pinned Fight loader is reused. The repository
factory requires existing schema; it does not install or populate it. No source
callbacks, prepare/reservation, Session holds, sends or activation run during
construction. The factory was not executed in PHASE1.

One private resolver bundle stores each supplied std::function once; both
Preparation and Admission forward directly to the same callable instances.
Copying a forwarding lambda only copies its shared bundle, so mutable callback
targets cannot silently diverge between the owners. A terminal bundle flag
rejects before/after callbacks, including a stop requested synchronously inside
a preparation resolver. This retains callable objects, not the lifetime of raw
external objects captured by them.

The backend owns one repository issuer, one RoomState, its exact same-DB
Preparation, one scheduled Driver/Lua/Publication and one Admission. Genuine
prepare/current/begin_commit/abandon are forwarded to Admission; synchronous
commit remains false. Full-frame basic dispatch and exact disconnect go to
the retained Driver. Admission's pre-release Bind captures that exact Driver;
it stores original Ticket/Session/hold capabilities and never advances inline.
The original Session ACK/input-prefix staging and private Written checks remain
the transport authority; no timer visit is an idle/acceptance attestation.

Destruction runs Admission, Driver, Preparation, RoomState, then repository;
the resolver bundle survives their forwarders. Database, initialized Lua,
executor and callback dependencies must outlive this composition. Construction,
use, stop and destruction require the actual single-thread game executor;
the concrete Driver additionally proves both bound Session executor identities.
InvitationService retains raw RoomAuthority pointers: its external owner must
drain offers/completions BEFORE stop/final destruction. This factory does not
claim Application owns that drain or solves arbitrary callback self-destruction.

Admission now has a terminal stop seam: invalidate weak entry callbacks first,
cancel without notifying drained invitation completions, preserve its object/map
through source-callback reentry, abandon reserved attempts and close active peers.
Checks after external resolution/preparation prevent retaining a new ticket or
resurrecting a stage after stop. Backend then stops the Driver timer/output.
Stop/abandon are idempotent within the documented same-owner lifetime. Active
room checkpoints/outboxes/locks remain for recovery; no rollback, saved rewards,
lock release, fresh WORLD return, rebind or process restart recovery is invented.

## Bounded native selection recovery

Mapped image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Worker decoded complete `5156A0..5156DE` (62 bytes/16 instructions),
`51B8C0..51B8FA` (58/20), `51B900..51B943` (67/19): 187 bytes/55 instructions.
This is scoped worker evidence, not root independent full-image disassembly.

5156A0 ignores the caller's stack argument and reads Battle+A9DF73C as the
actual selection. It uses manager Battle+A9DC198. Secondary accessor is chosen
only when DWORD Battle+A9E9C38 is zero and A9E9C3C is nonzero; otherwise primary.
Primary uses signed BYTE manager+4, group 0..15; signed index >=0 and below
DWORD count at manager+10+group*2D0, returning stored DWORD pointer at
manager+DC+group*2D0+index*4. Secondary uses unsigned BYTE manager+2D10 <3,
count manager+2D64+group*54 and pointer manager+2D28+group*54+index*4 with the
same signed index guards. Invalid selection returns null. These leaf bodies do
not read/copy/create record+45; the later 5154E0 caller reads that byte for
51EAD0's previously recovered count table.

Next frontier is the concrete group/count/pointer-table writers and selected
record content supplier. No writer instruction address, record ownership,
lifetime, skill ID/name or server skill authority is inferred from these reads.
No new native opcode or completed gameplay route follows from this evidence.

## Accounting and remaining work

Three existing C++ sources modified, one C++ header added; one scoped backend
composition source path. Mixed segments269->270; CUSTOM122->123; reviewed
groups26 unchanged. New opcode0 and complete bidirectional gameplay routes0.
TW C2S candidates156; world parser74 (limited50/control11/unconnected13).
World S2C252 (230 fixed/22 variable); reply48/push11/gated4/unclassified117.
Battle indexed110/specialized9;86 selectors7/cases6;83 actions23/projection2.
TW unhosted owner chains3/bindings38 unique34; CN chains35/bindings93 unique71.
CN historical C2S156/S2C phase-opcode280/length253 use a different scope.
Complete route denominator and TW/whole-game percentages remain unknown/null.

Application pk_rooms remains null. Actual hosting, trusted Fight/seed/basic
policy suppliers and invitation drain owner remain necessary. Skills/action2,
terminal89, saved settlement, lock release, WORLD return, reconnect/restart,
extended64 native wire/object/display and full TW/CN/web routes remain open.
Preserve frozen accounts/saves/auth/chat/IME/fonts/conversion/client binaries.
Web v70..80 reports are metadata pending actual source/commit/server-pairing
review; peer tests/percent/capacity are not server acceptance or measurement.

External full evidence:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-room-backend-287`.
Source worker is a readonly before/design audit; candidate review is separate.
No build/compiler/tests/runtime/native/VM/emulator/asset codec/game DB/SQL,
migration, activation or deployment was performed.
