# CN complete issued login/billing observation at source publication

Round `20261007-cn-login-record-source-observation`, PHASE1 source only.
Previous turn made source progress (catalog108/private verifier token/held
success checks, 75-file seal). Current files were reread before this change.
No native/server/browser/codec/C++ reader/build/test/database/deploy execution.

## Applicable transfer, without redoing old recovery

The paused CN project's `src/protocol/CnAccountBilling.h` already implements
the bounded original S2C0A consumer view recovered in its account-completion
round09. That header was absent from the shared project's `src/cn/protocol`.
It is now copied **byte-identically**, SHA256
`774aab0b001749a707ca96c0982ce15eeaddbe490ada35c00d22bb79bcfad389`.
The old project is not modified/restarted and its DB is not accessed/imported.
Its transferred NATIVE_ACCOUNT_PHASE round09 evidence remains historical;
known billing fields/pay types are reused, not relabeled newly discovered.

`CnAccountBilling` reads complete17-byte0A: pay type at payload0, month/day/
hour/minute at1..4, opaque5, signed16 year6..7, signed32 displayed counters
8..11 and12..15. All16 bytes remain original; private empty constructor cannot
publish a zero-filled reply. Only group types6/7 override display pay type.
Raw8 remains unnamed (native upper-bound assertion allows8 but has no display
case); other raw values are not silently normalized. Type0's partial native
date assertion is not a backend entitlement/calendar rule. This does not
select a type to bypass the client's separate local mutex gate.

## Native flag/UI lineage

Read-only `CnIssuedLoginFlags` exposes original1D payloadA8 as rawBYTE, top2
provider selector, bits4..5 account notice selector, low4 membership notice
operand. It has no setter/default/serializer or server permission inference.
These bit masks were already observed in the old receiver. This round follows
the actual post to its UI owner:0047FE30 stores top2 at network+40EC and sends
window040A;0044AAB0 case040A requires root+45C UI, rereads root+454 network's
40EC (rather than trusting wParam), and calls00449440, which stores UI+17AABE.
0043E260 resets that UI byte0.00446BD0 state7 tests zero only when local
ClientVersion==3;0043E7E0 compares exactly1 when choosing UI control6's
0x13 versusFFFFFFFF operand. All values0..3 remain distinct; UI behavior is
not backend authorization, a player permission, or a new gameplay opcode.
Actual GUI calls, mutexes and provider flows were not invoked or bypassed.

The current encoded `Data2/Client.csvZ` is160B, SHA256
`7ba020c3963bbd20dfdca89f05cd2d9b08c16c0e796f43850dd46e1fc1fa4f93`;
bounded file-only CSVZ expansion is154B, SHA256
`1016d446859cfc67e3dc5118d11ee32fea72c53d64c32fc25d489e380853bee3`.
It contains the ASCII record `ClientVersion,2,...`. Strict CP936 decoding of
the complete comment failed at byte86; original/decoded bytes and that error
are retained. No replacement/codepage guessing/text conversion was performed.
This file observation does not prove the current live resource root/mode:
00422C20/00422C80 can reload another Client.csv during the provider path. The
ClientVersion loader field1 -> owner+124E0 and its getter are separately saved.

## Actual source integration

Previously `NativeData::Current` saw only Scope(account session/verified account)
and checkpoint; it could not inspect the literal complete records queued by
this controller. It now receives a const Observation with exact complete1D/
0A spans and their bounded billing/flag views at Prepared, BeforeIssue and
the real held IO BeforePublish callback. The actual configured native owner
must qualify those bytes against its own issued key/billing/entitlement/current
source; scope-only or desired-client-result predicates are not sufficient.
No configured issuer is introduced or claimed completed by this API change.

The actual account controller retains the original NativeData through its
existing held publication. Its ordered1D/catalog04/05/06/0A output gets a
bounded extra exact wire copy, while the full original1D remains available for
the final observation. All source-owned1D credential bytes are explicitly
cleared on discard or queue completion, and original Login/verifier lifetime
checks remain in place. Observations are callback-scoped; no retention, logging,
translation, Lua exposure or receipt serialization of live account records.
No source/old preparation veto runs after bytes can leave; publication/grant
cleanup and ingress completion retain their existing separate meanings.

TW authentication/Application/admission/transport/encoding/source composition,
CN credential verifier/world selection and all other frozen contexts are
byte-retained. Native wire sizes, flags, payloads, original fonts/conversion,
accounts/saves and levels are unchanged. No default native payload, billing
rules, new tables, client patch or caller-side fallback was added.

## Remaining and accounting

NativeBilling transferred view1, issued flag view1, existing literal-record
issuer observation binding strengthened1; one scoped UI flag lineage saved.
11 current native function envelopes17272B are read/decoded file-only, not
11 routes. Whole-image adjusted/indirect alias closure is unproven. The old
2009B/1212B receiver envelopes match retained evidence; history is not rewritten.
NativeData actual source suppliers still absent: full1D/0A/unknown5/A9..CB,
seed/key/deadline/entitlements/catalog, durable credential revision/ABA/external
write/cross-process authority/revocation, full07/world1F/02/2A/6F/equipment/
scene/ACT/observer sources, TW registry/formal PC/web/WSS hosting and all other
gameplay/numeric extensions remain open. Native opcode/phase/partial-owner/
complete bidirectional route additions0, whole-game total/completed/%null.
The web peer handoff remains the prior SHA-bound source receipt with its
renderReady/releaseEligiblefalse; frontend checks are not server acceptance.
