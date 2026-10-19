# Three actual G endpoints and accepted world binding, round487

Previous goal turn was progress: a19fa97 introduced shared character custody
and three common-world containers. CUSTOM-0159 now adds TaiwanChannelServers,
the actual three-listener constructor, and binds accepted Sessions to their
chosen world. No build, test, product/native/VM/Lua/codec execution, game SQL,
migration, import/export execution, activation or deployment occurred.

## Actual listener and Session source

The constructor requires exactly three slots in the retained actual native
configuration, an exposed native group0..9, explicit routing bytes and three
complete per-world source sets. It creates three TcpServers in native G mode.
Each has a separate SessionManager and keeps the existing global connection-ID
allocator. Requested port0 is resolved by the kernel; the advertisement uses
the actual bound IPv4/port, preserving status and full route bodies. Mask0007
opens the three slots. No counter or snapshot key is repurposed as a channel ID.

All listeners bind before any accept loop starts or a complete advertisement
is available. Constructor failure synchronously discards each successful bind.
This rollback does not rely on a later posted stop or executor pumping.

Only TcpServer can mint NativeTaiwanChannelBinding from that observed endpoint
and the exact chosen Presence. It holds weak world ownership, immutable native
group/subgroup/endpoint metadata, the game thread and an atomic retirement flag.
Network-held copies do not own an affine world. Actual accepted Session
construction checks socket.local_endpoint against it and retains private
this/64-bit connection-ID/local-endpoint correlation. Endpoint observation or
allocation failure rejects this bound path; the old unbound passive behavior
stays unchanged. There is no public Session rebinding setter.

Native selection, readiness, mixed records and lifecycle construction facades
check GAME ownership before locking their weak world and fence channel validity
before and after the actual supplied callback. The lifecycle itself rejects
another world's binding before repository preparation and checks it again after
observers. Exact cleanup remains unconditional even after binding retirement.
The shared list handoff refuses a retired bound peer before pruning/repository
work and additionally checks the actual native destination group/subgroup.
All existing authentication, issuer lineage, full snapshot key, native authority
and accepted-local-endpoint requirements remain in force.

Stop retires descriptors synchronously before their posted socket shutdown.
Retained Session metadata still names the old channel; it grants no permission
to a new one. A channel fence does not undo arbitrary callback side effects or
replace the original gameplay transaction/current contract.

## Required integration and lifetime boundaries

SourceFactory must build three independent real owners from the selected world
Context, using the same repository and actual serial GAME executor. The one
actual L-issued ticket owner and its explicit capacity policy must be shared;
three independently constructed handoff owners are not equivalent. Supplied
transport callbacks must be the existing revocable weak facades. This trusted
caller contract is not proved by introspecting opaque std::function captures.
GAME owners, worlds and repositories must outlive actual NET plus GAME drain;
stop is not a synchronous completion receipt for Session cleanup.

Application/Main still hosts one G listener and has not selected the new
component. Its per-channel complete gameplay controllers, shared L route/list
composition, actual three client slots, Web target selection on the existing
two paths and durable save/logout/target admission remain open. This source
change alone does not establish playable channel selection or switching.

## Bounded current-native follow-up

Current God2.exe SHA256:
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
Three REA/Ghidra targets closed; all13 original section bytes and headers match
the original in each analysis-only image. Synthetic callers are not native
caller evidence. All addresses below are VAs.

483B00 consumes a signed WORD control and BYTE flags, RET8. It calls483BB0
and returns DWORD1 when flags&02 or(flags&20 and control0), otherwise0.
483BB0 passes WORD UI+232DE4 to507BB0 with manager UI+E2170.507BB0
changes widget flags at manager+818+signedWidget*2A08 and calls GUI/render
helpers41BF30/504500/41B560. This supports a bounded local widget-dismiss
interpretation; its dialog identity and all indirect descendants are unknown.
No target-channel field or new C2S producer was recovered in this path.

The qualified4820A0 caller at482305 tests the result and only then produces
GUI-26;4829CF ignores it. Raw E8 candidate4833B3 still needs its containing
procedure qualified. Continue at46597E case2 downstream of466B00 result2,
and the widget's real creation/opening path. Do not call every dismiss a switch.

Raw evidence and exact external receipt:
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/three-channel-endpoints-round487/native-switch/ui-dismiss-findings-v1.json
SHA256:90ba17e94c1276c25cee3680e9668b4ecf9fbe29955b03e1279f6530c8491231.

## Verification scope

The registered future C++ fixture creates three actual sockets/ports and real
three-world containers, validates advertisement replay, hello/F6 and accepted
Session binding on GAME disconnect, distinct connection IDs and stop revocation.
It includes wrong configuration/source/address/key/port cases, factory failure,
occupied-third-port rollback with immediate first/second rebind, owner-thread
refusal and legacy unbound compatibility. Its explicit synthetic callbacks throw
if authentication, selection, entry, gameplay or storage is reached. They are
not authorities or successful native gameplay. No concurrent NET-thread case
or complete login/switch acceptance is claimed. The fixture was not executed.

The one formal report is static; full-game route credit remains0 and the
denominator/percentage unknown. The full Taiwan-only goal remains active.
