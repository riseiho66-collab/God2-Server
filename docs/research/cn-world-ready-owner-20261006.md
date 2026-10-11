# CN initial world readiness and common stored-position owner

This is source integration only. No build, test, game/server execution,
production database access or deployment was performed. Native font selection
and Traditional/Simplified text conversion remain independent and unchanged.

## Native paths and aggregate handling

Pinned CN normal initialization0048CAA0 and CF transfer0048FCC0 enqueue
`1F 00`, `23 00`, then `1C handleLE16 0000`. The exact producer815E0 explicitly
initializes its one payload byte;815B0 uses the actor handle's low16 and the
zero return from405A30. Each record is separately locked; capacity and the
background worker can flush between records. The new SharedWorldReady consumes
complete records in relative order across aggregates, including several records
in one aggregate.30 has one zero payload byte;36 has eight opaque bytes copied
from worker+84/+88. Both pass to the mandatory actual bootstrap/control handler
without advancing initialization. The128-record inline processing budget is
local operational policy, not an original game limit.

There is no recovered forced S2C response dependency for these requests.
The required handler must provide actual qualified gameplay/control handling;
no same-opcode reply, empty success handler or fabricated data is supplied here.
C2S1F is not presumed to request the S2C1F selection list.22's phase is open.

Scene restoration0048E3E0 and S2C61→0048EF40 can queue1C without1F/23.
They belong to the actual later gameplay dispatcher, which receives the intact
aggregate remainder after initial entry. This controller's initial three-step
requirement must not be imposed on those later paths. Additional permitted
independent initial controls still require their own contracts.

## Actual common ownership and lifecycle

SharedWorldPresence uses the same RecoveredCharacterRepository and common
recovered_characters IDs as current TW gameplay. Its prepared lease requires a
real existing stored position, including revision, and a native14-bit handle
already reserved by the authoritative scene owner. It does not derive a handle
from a DB ID or create a default spawn. Character, session and handle exclusion
and monotonic generation are explicit integration policy. Actor generation,
original spawn/location rules and cross-process ownership remain open.

SharedWorldReady checks the independently verified account, the current world's
admission ticket/session, the offered character and the exact common lease.
SharedWorldSelection now requires this controller on the same connection and
matches its position and handle against the complete native2A. Its existing
shared map/record check remains. Preparation and activation re-read actual
stored position and ownership; stale revisions reject entry.1C must echo the
reserved handle and pinned metadata0. The required world-publication handler
must finish before later gameplay input is acknowledged.

After publication, the lease tracks identity rather than freezing movement to
the initial saved position. Subsequent movement/persistence belongs to the
actual gameplay owner. Generation-qualified cleanup is held by transport,
independently of the connection wrapper; close, failed bootstrap and failed
entry release the reservation. A late close cannot remove a successor lease.

TW's existing movement/presence owner is unchanged and does not yet enroll in
this common registry. Therefore these guards do not establish active TW/CN
mutual exclusion or a mixed-client world. Both adapters must share this one
registry and actual scene owner at Application integration.

## Creation evidence correction

00448950 sends1B, not17. Ordinary17 completion obtains18 then later reconnects
through A6/07 to refresh the summary;1B instead queues18 and immediately uses
the retained selection for1A. Do not reuse the ordinary17 success sequence.
BeginPlay2A payload7→actor+FC→1B UI+1615C is a proved disable-mask dataflow.
The read-only getter names this UI use without asserting permission or issuer
rules.07 row18 and full portrait/appearance supply remain unknown; local preview
tuples and matching consumers cannot manufacture authoritative07/2A bytes.

## Evidence and open integration

Immutable native deliveries: cn-ready-bootstrap-order-agent-01 (99 files) and
cn-character-create-fields-agent-01 (167 files), under
artifacts/integration/packet-connections-20261006. They contain pinned C, ASM,
original executable bytes and hashes. The main deliverycn-world-ready-owner-01
preserves source snapshots and the prior ledger. Full native07/1F/02/2A and
1D/0A suppliers, authenticated alias/grant lineage, original first placement,
shared actor allocator, bootstrap/control/world-publication implementations,
later dispatcher and actual Application listeners remain unhosted/open.
No new complete bidirectional route is claimed.
