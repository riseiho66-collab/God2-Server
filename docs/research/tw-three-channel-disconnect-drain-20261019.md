# Actual disconnect completion for channel owners, round488

CUSTOM-0159 extends the actual listener/world binding from c3bdfdb. This round
connects observable disconnect completion to the existing Application and the
three-listener owner. Main still hosts one G listener; three-channel gameplay
and switching remain open. PHASE1 source/static only: no build, test, product,
native, VM, Lua, codec, game SQL, migration, import/export or deployment ran.

## Actual completion source

Previously TcpServer posted SessionManager removal before invoking the actual
application disconnect callback. An empty manager could therefore precede GAME
cleanup. Session now has a separate optional DisconnectCompletion transport
callback. Its actual finish GAME job independently attempts common-world
cleanup, lifecycle abandon and application disconnect, records any exception,
and destroys those exchanged callbacks on GAME before reporting completion.
Best-effort diagnostic logging cannot skip the remaining callbacks or receipt.
Existing Session callers need not supply the new final constructor argument.

TcpServer passes the original application callback directly. Its separate
completion facade holds only a weak listener and posts exact Session-pointer
and full64-ID removal to the acceptor strand after all three callbacks finish.
The manager no longer exposes count-only/ID-only removal. Callback failure is
latched before removal, including callbacks which failed before stop was asked.
The Session's own executor work guards remain held until completion posting.

StopObservation is a copied read-only token privately issued by the actual
listener. Completion requires stopped admission, acknowledgment of outstanding
accept/retry cancellation, zero remaining accepted Sessions and a final marker
on the same per-listener GAME strand as disconnect. That marker carries only
pure atomic state and executor guards. It keeps both run loops alive until it
runs; it retains no affine world, repository or application callback. Repeated
observation uses the same private state. Pending cannot become success through
elapsed time. Complete plus succeeded=false records attempted callbacks with
an exception. Aborted is distinct from Complete and requires explicit host abort.

Async initiation/receipt-post/marker-post failure cannot publish clean success.
Infrastructure abort retires the binding atomically before attempting closes,
so even partial close-post failure blocks further bound GAME authority. A
constructor refusal before SessionManager registration retains the previous
accept policy; a registered start failure aborts instead of losing custody.
An accept which acknowledges after stop closes its socket without admission.

TaiwanChannelServers returns one observation per actual listener and retires
all three before requesting receipts. The existing Application holds receipts
for its actual account and optional G listener. A GAME timer polls every10ms
until both complete; this is an explicit host-service cadence, not a recovered
native switch timeout. It then releases only IoContextPool's work guard.
Existing natural NET join, GAME work release and GAME join remain required.
Callback failure is surfaced after that drain rather than printing clean stop.
Infrastructure abort follows the existing explicit exceptional abort path.

IoContextPool::stop already resets only its work guard, not io_context.stop;
Session already owns NET/GAME work guards through its disconnect callbacks.
This change establishes an explicit observation cut, rather than claiming the
old ordinary stop immediately destroyed its queued callbacks.

Completion is not proof of durable saves, client03 receipt, Session destruction,
all arbitrary work spawned by application callbacks or safe early destruction
of all GAME owners. The existing weak-facade and source-owner lifetime contract
through full NET/GAME drain still applies. No logout wire or ACK order changed.

## Bounded current-client REA

Original God2.exe SHA256 is
aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48.
The analysis-only image preserves all13 original section headers and bytes.
Its synthetic discovery callers are never native caller evidence. The REA
target was closed after the two focused callees were analyzed.

At original VA46597E, state2 calls481590 and4158B0, then returns DWORD6.
481590 calls4F4890/47FBA0/4AFE20, conditionally41E680(-1) when
DWORD[this+CFF60] is nonzero. 4158B0 consists of one RET. Those descendants'
full cleanup effects remain untraced. Together with prior qualified dispatch
and caller evidence this follows GUI-26 ->466B00 result2 ->467860 ->4655E0
state2 ->return6 ->415730(2,2,1): G02, BYTE reason2, flush and wait03.
Unlike return2, 40DE80 case6 does not set local_370/login mode1. No channel
parameters, target admission or durable-save rule were recovered here.

UI+232DE4 widget name and its actual creation/opening writer remain unknown.
The next bounded trace is original .text references to that displacement and
qualification of its writer. Do not label this widget or reason2 as a switch.
The extra dispatch cut in bounded-case2-v1 began inside an instruction; it is
retained and excluded. v2 corrects that cut; the state2 block matches both.

External receipt:
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/three-channel-drain-round488/native-switch/case2-exit-findings-v1.json
SHA256 bbf9f94377241ea1d974d03cf55f97b465c3e303511b606de106ec4f260af75f.
REA ev_90ba0454e3fe07e8d824ebcc800a548795217027be015c65343ae8e964f22ce0.

## Verification and remaining integration

The existing future socket fixture is extended with separate NET/GAME polling,
paused GAME cleanup, reentrant observed stop, failing abandon/disconnect,
unstarted/repeated stops and aggregation of three actual listener receipts.
These are source cases awaiting the later concentrated build/test phase, not
executed acceptance or proof of saves/gameplay. Exactly one formal static
report is reserved for this round after the source pins are sealed.

Remaining: three independent complete gameplay Contexts mounted by Main,
actual three configured native slots, one shared L-issued handoff lineage,
selected Web G endpoint, durable save/scene release/target admission, all six
directed switches and current original-client own-server acceptance. Full-game
route credit stays0; denominator/percentage remain unknown; the goal is active.
