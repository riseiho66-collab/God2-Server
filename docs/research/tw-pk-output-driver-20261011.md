# TW286: scheduled basic driver and native selection count table

CUSTOM-0124, Phase1 static source/instruction recovery only. No build/compiler,
tests, game/runtime/native/client/VM/emulator/asset codec/game DB/SQL/migration,
activation or deployment. No gameplay acceptance or full hosted PK claim.

## Concrete scheduled source

OwnedTaiwanPkBasicDriver owns the285 LuaBasicOwner, hence one private
Publication bound to the same actual RoomState. It retains genuine Ticket,
two Sessions and private committed holds through Admission.bind. Pair/index
map nodes are preallocated before the underlying bind publishes. The actual
Session game executors must equal the supplied timer executor, checked through
new identity-only native_pk_game_executor_matches; native authority still
requires original private holds, not this boolean or scalar thread identity.
All operations/destruction stay on that actual single-thread game executor.
Admission drains/dies first; Lua/rooms/repository/executor outlive the driver.

One coalesced asio::steady_timer invokes later game visits only. Explicit
cadence1..1000ms is bounded CUSTOM transport retry policy, no default/native
round/count clock. No resolution/pump from bind, input or write callbacks.
Actual fullframe dispatch marks a bound pair dirty and arms; pending private
entry/fullwrite/output retries later. Genuine no-work Idle clears dirty until
next real input. Each dirty retained pair is visited at most once per tick.
Only one wait can be armed; stop is terminal, so cancelled stale callbacks
cannot restart it. Weak lifetime invalidates queued callbacks on destruction;
callbacks retain neither Lua nor a naked driver. No caller supplied Rule/masks/
templates/stat/seed are added. Pair cap256 matches existing retained owner.

Only actual Ready plus private Written/cleared pending resolves, with existing
single shared Battle/profile/checkpoint/reentry fences and internal Lua basic
policy. New private scheduled-turn seam means a later game visit, NOT strand
idle certification. Existing advance_at_idle external contract is preserved.
Grants/ResultsControl/Terminal publishes through existing source-qualified
Session sender. Initialrevision1 remains Admission's entry writer; Collect
never resolves. When a phase has no pending rows, no flight/token is installed
and the visit returns Idle instead of polling forever. Resolved/OutputVisited
are not fullwrite/remoteACK/client acceptance.

## Actual transport barrier retained

Existing send_native_pk_output installs exact atomic pending and stages on its
strand. stage_native_pk_output waits game_busy. The actual ordinary callback
ACK sets game_busy false, enqueues its response, then resume_world_input
observes pending and stages PK output. Buffered partial world/staged records/
unfinished skill prefixes still reject; release checks prefixes again after
source before-write qualification. Timer never reads strand-owned game_busy,
read_inflight or input buffers, and one post/time delay proves no readiness.
No frozen transport branch is weakened or old bytes discarded/reclassified.
Unreceived TCP bytes and conservative rejection of genuine pipelined input
remain limits, not a claim of accepting every fast native window.

Timer/allocation/reentry failure or revoked entry closes the retained pair and
keeps room/checkpoint/outboxes/locks for recovery. Reentry closes immediately,
so even a caught callback is visible to existing pure Rule fences before shared
settle. Stop cancels the wait and retires pairs; exact-instance disconnect is
idempotent even after stop/peer failure. Durable settlement can precede a later
strand prefix rejection; that result stays retained, no rollback or atomic
network claim. No saved economy settlement, abandon, resend/reset, WORLD return,
reconnect/restart owner or Application/config installation is supplied.

## Native count source (independent bounded worker)

Exact mapped149c SHA149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Complete51EAD0..51EB2E:94B/27 instructions SHA68a507ca16b73bc18917ca892afe05101d9da083d244f265f9823c2295157b3f.
Normal signedDWORDindex1..17 returns DWORDtable571BB0[index]. Actual515614
receives zeroextended selectedrecordBYTE45 and outpointer Battle468;515619
stores returnedEAX into Battle45C. Full normal helper does not read ECXmanager.
This count is a native fixed-table lookup, distinct from51F2A0 bit populations.

Exact72Btable571BB0..571BF8 SHA df17e805dc3e4753e97e082f83aba452443a31116daca9a21c51ab2ae6ebe342.
Valid entries1..17: [1,2,3,4,1,1,1,1,1,1,1,1,2,7,1,3,2]. OutputDWORDflag is0
for indices13/14/16 and1 for other valid indices. Index0 table entry is context
only, not safe normal input. Invalid indices call opaque402C70 then may fall
through if it returns; no assertion/throw/termination behavior is recovered.

This applies to5154E0's ordinary setup path (Battle464=3) and can be bypassed by
its mode47 metadata predicate. Not a universal basic1/initial/later0B formula,
server balance, target occupancy or accepted gameplay. SelectedrecordBYTE45
producer/resource/skill mapping and table/mask upstream lifecycle remain open.
Worker recovered94newcodeB/27ins+72dataB (68validreadB); not globalclientcoverage.
Root read worker findings, not an independent fullinstruction audit.

## Counts and remaining work

Four existing C++ files modified and one new header added; one scoped scheduled
owner source. Mixed268->269, CUSTOM121->122, groups26. Newopcodes0/full complete
bidirectional gameplay routes0. TW C2S156 candidates/worldparser74 (limitedsource
50/control11/unconnected13), S2C252=230fixed+22variable, reply48/push11/gated4;
battle110/specialized9/86selectors7/cases6/83actions23/projection2 unchanged.
TW unhostedchains3/bindings38/unique34;CN35/bindings93/unique71. CN historical
C2S156/S2Cphaseopcode280/length253 distinct scope. Full denominator/TW/fullgame
percent null. Formal PK host remains absent: actual Fight/seed/coeff/order policy,
admission/driver/Application composition, skills/action2, terminal89/savedsettle/
lock release/fresh WORLD return/reconnect/restart and shared64 wire still need
owners. TW/CN/web/frozen saves/auth/chat/IME/native fonts/conversion/clients are
preserved. Webv70..79 metadata pending actual source pairing, no ACK/credit.

Evidence: C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-output-driver-286
