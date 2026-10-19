# Actual Application gameplay ownership boundary, round489

Previous goal turn was progress: a7a0771 connected actual GAME disconnect
observations to listener/account/G shutdown. CUSTOM-0159 now changes the actual
Main -> run_server -> Application path to own its complete gameplay cohort
separately from the process host's database/account-hashing lifetime. Only one
cohort is instantiated so far; no three-channel activation or acceptance is
claimed. No build, test, product/native, Lua/VM/codec, game SQL, migration,
import/export, activation or deployment ran in this PHASE1 source-only round.

## Mounted GAME ownership

ApplicationGameFrame is a move-only C++20 standard coroutine frame, rather than
another Asio event loop. Its initial execution builds the actual existing
cohort and reaches one pure nonthrowing Hold after startup readiness. Existing
Lua, World, services, PK/party/trade/bank/conversation/presence state, registries,
source owners, all callback custody chains, scheduler and guards retain their
lexical storage and reverse teardown order. Reference-captured callbacks do not
outlive a temporary builder's stack. The coroutine lambda object is declared
before the frame and remains stable and alive through finish and destruction.

Actual Database and account authentication owner/worker pool are now outside
that frame, on the same actual GAME thread. The account owner outlives worker
pool join. Per-cohort login facade variables stay inside the frame; moving one
cohort's final facade does not consume a shared template intended for others.
RecoveredOwnedCompanions remains mutable per-cohort state, not an immutable
catalog. No database schema, persisted data or protocol bytes changed.

The process host runs the single existing game.run after require_held succeeds.
The main host naturally joins NET, publishes an atomic joined flag, then resets
its GAME work guard. GAME runs remaining outstanding work before returning.
Only after acquiring the actual NET-join flag does it resume this held frame's
shutdown tail, call the existing Lua server_stop hook, surface prior disconnect
callback failure and destroy the cohort on GAME. Listener observations alone
do not authorize this final resume. No nested event pumping, new runtime thread,
extra scheduler, polling loop or implicit gameplay/default data was introduced.

The frame checks its actual GAME thread, refuses moved-from/repeated/reentrant
completion and accepts no other awaitable. A separate active-resume latch covers
the entire resume call, including return_void and local destructors. No done()
query is used to detect an executing coroutine: it is consulted only after a
known Holding suspension or after resume returns. A second Hold cannot create
an untracked suspension; it is rejected through promise error handling. The
destructor clears its handle before destroying suspended locals so reentrant
cleanup cannot resume a partially destroyed frame. Wrong-thread/active frame
destruction or movement terminates rather than destroying live GAME storage.

Startup and shutdown exceptions are retained by the coroutine promise and
re-thrown on the host GAME path. Existing exceptional startup/event-loop abort
remains separate from normal drain and is not proved safe by this extraction.
The frame does not certify saves, native ACKs or permission to switch channels.

## Remaining three-cohort assembly

Main currently calls the default run_server without a native SharedWorldHostPlan.
Application still creates one common_world/Context only when that explicit plan
is selected. The new frame is mounted, but its source exports/listeners/signal
orchestration have not yet been separated for three simultaneous cohorts.

Next move the actual G packet/disconnect/authentication/character source set,
actual L list issue/current/complete adapters, tick and retirement out through
owned exports while keeping each frame suspended. Construct three complete
independent cohorts against the same repositories, shared character custody
and one actual L-issued handoff lineage. Each native plan needs its own private
Owner: copying the existing plan preserves its single cached Owner and correctly
fails when asked to own another world. Do not copy final reference-capturing
handlers or run three blocking/nested copies of Application.

All three tick/retirement cohorts, Lua VMs, world peers, PK/trade/party state,
conversation/cache/initial-publication chains must stay independent. Shared guild
storage needs explicit mutation invalidation across the union of qualified
audiences; blindly duplicating cached coordinators can leave stale panels.
The one L listener must route issuance by the actual selected channel, and
current/completion by that same retained issued receipt, not a latest selector.
Three actual client slots, endpoint configuration/Main selection, the existing
two Web paths, durable save/logout/target admission, all six directed switches
and current-client own-server acceptance remain OPEN.

## Current-original REA follow-up

Current God2.exe SHA256:
aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48.
The analysis-only image retains all13 original section headers and bytes;
synthetic discovery callers are not original callers. Eight focused procedures
were analyzed and the REA target was closed.

483BD0 creates the widget and at483C10 stores its lowWORD handle toUI+232DE4.
The numeric19000 creation argument has not been established as a resource ID.
483B40 accepts encoded message character data, not a bare DWORD resource number:
476570 parses an initial number and typed substitutions, resolves formatting,
then50F580 writes the resulting text and507B20 opens the widget.483A80 opens
encoded text and setsDWORD UI+232F68=1;483AB0 opens direct text and sets the
same flag.483A50/483A60/483A70 are each a single RET.

Reused qualified4820A0 evidence proves the flag distinction: zero calls the
message dismissal and ignores its return; nonzero plus confirmed dismissal
selects GUI-26 and the previously traced world exit. This is a shared message
widget with exit-required mode, not a channel-selection dialog. No fixed title
or channel target was recovered. Qualify containing functions and actual text
at469294->483A80 and465DC5/46B5BD/501FA6->483AB0 next.

The initial string probe incorrectly considered58F0E8/58F108 as C strings;
those interpretations are excluded as binary geometry/style data. One helper
saved complete JSON before its stdout failed with a cp950 encoding error. It
was retained and not rerun; the native REA evidence succeeded independently.

External receipt:
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/three-channel-application-round489/native-switch/widget-identity-findings-v1.json
SHA2566422dc5d9f33b43fc2e615163538cbfd72e275fde7a6d2c05b8f8c4bb4c57499.
REA ev_8580d8e8d7d94e2e98283803dd00492022c7adaa7bbf0462789c83170fa90604.

## Static verification scope

Future C++ source cases exercise actual queued NET->GAME use of frame-owned
local storage, explicit natural drain before finish, owner-thread destruction,
startup/shutdown errors, missing/repeated Hold, moved-from/foreign-thread access
and reentry during completion/destruction. They are not executed gameplay or
server/database acceptance. Source comparison separately checks the retained
gameplay body against the prior commit, excluding the two moved auth owner/pool
declarations. One formal static report is reserved after final source sealing;
gameplay route credit stays0, denominator/percentage remain unknown and the
full Taiwan-only goal remains active.
