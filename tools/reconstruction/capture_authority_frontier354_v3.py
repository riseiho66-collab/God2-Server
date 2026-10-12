from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
O=A/'round354-tw-unconnected-authority-source'
D=A/'tw-native-world-control-authority-frontier-354'
HEAD='b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        assert p.read_bytes()==b,str(p)
        return
    with p.open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()==HEAD
paths=['AGENTS.md','docs/GOAL_ACCEPTANCE.md','docs/custom-designs.json','src/core/Application.cpp','src/core/Config.h','src/core/Config.cpp','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/net/Session.h','src/protocol/RecoveredWorldRecords.h','src/protocol/RecoveredSpectatorClose.h','src/handlers/OwnedPkInvitationService.h','src/handlers/OwnedTaiwanPkRoomBackend.h','src/handlers/OwnedTaiwanPkEntryPreparation.h','src/handlers/OwnedTaiwanPkBasicDriver.h','src/handlers/OwnedTaiwanPkLuaBasicOwner.h','src/handlers/OwnedPkOutboxPublication.h','src/game/OwnedTaiwanPkAppearanceSource.h','src/game/OwnedTaiwanPkCombatSource.h','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp','src/game/SharedTaiwanNativeSpectatorSource.h','src/game/SharedTaiwanNativeSpectatorSource.cpp','src/game/SharedTaiwanNativeRecordHandlerSource.cpp','src/handlers/OwnedBeastFoodReadset.h','src/db/NativePfdSourceCatalog.h','scripts/gameplay/pk_invitation.lua']
references=[];contents={}
for p in paths:
    b=subprocess.check_output(['git','show',HEAD+':'+p],cwd=S)
    dest=O/'source'/p;put(dest,b);contents[p]=b
    references.append(dict(actual_path=(S/p).as_posix(),retained=dest.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b),HEAD_exact=True,source_revision=HEAD,source_custody='immutable git show; current App authorized edits excluded'))
js(O/'source-references.json',references)
base=json.loads((D/'before-manifest.json').read_bytes());assert base['head']==HEAD
base_rows={r['path']:r for r in base['members']};overlap=[]
for r in references:
    p=Path(r['actual_path']).relative_to(S).as_posix()
    if p in base_rows:
        x=base_rows[p];b=(D/'before'/p).read_bytes()
        assert len(b)==x['bytes'] and sha(b)==x['sha256'] and b==contents[p]
        overlap.append(p)
js(O/'root-baseline-overlap.json',dict(head=HEAD,root_baseline_manifest_sha256=sha((D/'before-manifest.json').read_bytes()),matched_current_paths=overlap,only_overlap_verified=True))

lp='artifacts/integration/packet-connections-20261006/packet-route-ledger.json'
lb=(S/lp).read_bytes();ledger=json.loads(lb)
unconnected=ledger['world_unconnected_gameplay_opcodes'];pending=ledger['pending_world_source_groups']
assert len(unconnected)==13 and len(pending)==10
js(O/'ledger-selected-current-frontier.json',dict(actual_path=(S/lp).as_posix(),bytes=len(lb),sha256=sha(lb),world_unconnected_gameplay_opcodes=unconnected,pending_world_source_groups=pending,projection_only=True,whole_ledger_not_copied=True))
design=json.loads(contents['docs/custom-designs.json']);assert len(design['designs'])==135
assert b'bool owned_pk_invitation_enabled=false;' in contents['src/core/Config.h']
assert b'std::unique_ptr<OwnedPkInvitationService::RoomAuthority> pk_rooms;' in contents['src/core/Application.cpp']
assert b'},[&]{return pk_rooms.get();});' in contents['src/core/Application.cpp']
assert b'must never be wired as an accepting handler' in contents['src/handlers/OwnedBeastFoodReadset.h']
cuts=[('src/core/Application.cpp',718,730,'actual-common-plan-construction'),('src/core/Application.cpp',2177,2321,'actual-PK-room-pointer-and-peer-observer'),('src/core/Application.cpp',2754,2774,'actual-hosted-invitation-only-dispatch'),('src/core/Application.cpp',6687,6705,'actual-selected-record-parser-flags'),('src/db/SqliteDatabase.cpp',427,524,'complete-concrete-PK-backend-constructor'),('src/handlers/OwnedTaiwanPkEntryPreparation.h',24,51,'exact-PK-source-constructor-contract'),('src/handlers/OwnedTaiwanPkEntryPreparation.h',56,155,'PK-selected-prepare-source-reads'),('src/game/OwnedTaiwanPkAppearanceSource.h',151,202,'PK-appearance-full-material-predicates'),('src/game/SharedTaiwanNativeSpectatorSource.h',66,88,'CloseOwner-and-binding-contract'),('src/game/SharedTaiwanNativeSpectatorSource.cpp',224,240,'actual-close-install-selection'),('src/handlers/OwnedPkOutboxPublication.h',608,641,'selected-terminal-return-source-requirements'),('src/handlers/OwnedBeastFoodReadset.h',12,87,'candidate-only-complete-readset-contract')]
cutrows=[]
for p,lo,hi,name in cuts:
    lines=contents[p].splitlines(keepends=True);assert 1<=lo<=hi<=len(lines),(p,len(lines),hi)
    b=b''.join(lines[lo-1:hi]);dest=O/'cuts'/(name+'.source');put(dest,b)
    cutrows.append(dict(source_path=p,first_line=lo,last_line=hi,retained=dest.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b),scope='selected exact line cut; enclosing complete whole source retained'))
js(O/'exact-line-cuts.json',cutrows)

frontier=[dict(rank=1,opcodes=['69','35'],actual_hosted_ingress='Application.cpp2754..2774 and 6628',current_owner='OwnedPkInvitationService; actual pk_rooms getter empty at2184/2319',closed_existing_seams=['CUSTOM0086 invitation peer/rule/expiry/invalidation','SqliteDatabase.cpp427..524 builds concrete CUSTOM0125 AsyncRoomAuthority on same DB/game owner','private initialization/Written, native entry hold, paired checkpoint/outbox and scheduler are concrete contracts','CUSTOM0106 uses actual stored role/resources/auxiliary under explicit policy'],earliest_supplier_gap='Factory438..449 needs true common presence/visibility and real Session/ownINIT/peer resolvers plus explicitly supplied trusted seed, four BasicParameters, execution order/retry; Configuration currently supplies invitation bool only. EntryPreparation117..123 then needs actual same-DB complete joint/native2A/DA/bank, real ready lease/private Written.',endstate_gap='Configured terminal ReturnSceneSource needs genuine full actor/resources/selection/current WORLD return; constructor483..505 adds text/guild owners but does not supply missing actor material.',next_action='Qualify one concrete eligible existing-saved pair from the actual common host and recover/select explicit already-authorized seed/basic-policy/complete return owner before installing backend. Existing normal INIT alone cannot mint common lease/material; do not install schema or invite now.',implement_now=False),dict(rank=2,opcodes=['A3','CB'],actual_hosted_ingress='Application.cpp6691/6698 only propagates explicitly selected binding flag',current_owner='SharedTaiwanNativeSpectatorSource::CloseOwner abstract; actual create224..240 sets close_dispatch only when supplied',closed_existing_seams=['real ready presence/transport token/root/UI observations','opaque native request and once execution/original encrypted reply ordering retained'],earliest_supplier_gap='Real native window publication/owner and its close rights/state transition/exact reply are not supplied by current selected factory. Header66..74 deliberately delegates all to CloseOwner. Opaque saved-this high byte is not nonce or permission.',next_action='Trace actual server window issuer/CD-D0 publication and matching game owner; recover close operation/result semantics there before implementing a concrete CloseOwner. A cleanup/no_reply guess would invent authority.',implement_now=False),dict(rank=3,opcodes=['6B'],actual_hosted_ingress='Session.h344 flag false; RecoveredWorldRecords235 parser-only; no Application lane0 effect owner',current_owner='OwnedBeastFoodReadset captures entire saved bag and selected beast custody in one read transaction',closed_existing_seams=['real saved owner/readset identity and revisions','historical PFD declarations/provenance and selected metadata match'],earliest_supplier_gap='PFD membership includes special transformation declarations and supplies no food eligibility/effect amount/cap, consumption transaction or genuine S2C response. Readset header12..17 forbids accepting-handler use.',next_action='Recover original food effect/reward/consumption/result authority for one selected PFD item/beast before writing; mutation must recapture/CAS full candidate readset in same owned transaction. UI1/30 and quantity99 domains do not supply rights.',implement_now=False)]
js(O/'ranked-next-source-frontier.json',dict(head=HEAD,subset_only=True,rank_basis='distance from an actual hosted owner plus concrete rules/storage/reply; not pending-group count',selected_opcodes=['69','35','A3','CB','6B'],ranked=frontier,no_closed_supplier_in_this_subset=True,new_full_route_credits=0,new_native_credits=0,whole_game_denominator=None))
put(O/'REPORT.md',b'''# Round354 bounded authoritative route supplier audit

Current source snapshot: b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650.
The ledger retains 13 unconnected opcodes and 10 pending groups. The finite
implementation ranking covers five opcodes in three source families, not the
whole gameplay inventory and not an authority count. No tracked changes.

1. 69/35 has the closest concrete integration seam. Application2184 retains
   an empty RoomAuthority;2319 returns that pointer and2754..2774 handles only
   the invitation transport. Config.h31 has only the default-false switch.
   SqliteDatabase427..524 now builds an actual AsyncRoomAuthority, same-DB
   preparation/admission/basic driver, later timer, paired checkpoint/outbox,
   concrete terminal saved-resource handling and optional return owner. This
   is substantive existing code, not an assertion that the old source-group
   prose exhausts current implementation. The basic driver does not supply
   original native rules. CUSTOM0106 adopts actual saved stats, not recovered
   current149c stat aggregation; CUSTOM0123 accepts only explicit basic policy.

   Earliest unsupplied constructor operands: actual common presence/visibility,
   concrete both-Session/ownINIT/peer resolvers, trusted uint32 seed, four basic
   coefficients, two-view order and retry. Current Config has no such policy
   supplier. EntryPreparation56..155 requires real ready leases and both own
   Written INITs, joint committed observation and actual full appearance.
   Appearance151..202 requires matching whole native2A, DA, bank/common roots,
   actor and pose; an existing scalar character or a borrowed sender TLS
   receipt cannot replace them. Factory483..505 supplies text/guild ownership
   but explicitly leaves full actor/resources/selection to a true return owner.
   Outbox608..641 fails a configured missing/stale return and preserves durable
   prefixes. Do not clear this dependency through a placeholder or preparation-
   only terminal path. Next qualifying trace should select one genuinely
   existing-saved common pair, explicit established policy and complete return
   supplier; only then wire backend into pk_rooms and C35 dispatch/lifetime.

2. A3/CB is a smaller native input shape but lacks a real operation owner.
   SharedTaiwanNativeSpectatorSource.h66..74 delegates window/opcode/opaque byte,
   phase/rights/complete reply to independent CloseOwner. Actual create224..240
   requires publication when close is selected and exposes close_dispatch only
   then. Application6691/6698 propagates availability, not rights. Current source
   references inspected expose the abstract seam and selected factory, not a
   supplied concrete window-close authority. Native opaque highBYTE does not
   encode a proven lease. Next source is the actual server CD/D0 window issuer
   and same game owner state/reply; cleanup or guessed noReply is insufficient.

3. 6B lane0 has a consistent saved readset, not an effect rule. Its entire
   OwnedBeastFoodReadset source captures full bag/selected custody/selection in
   one read transaction and compares revisions. Header12..17 explicitly forbids
   accepting-handler use: historical PFD includes special transformations.
   Eligibility, effect amount/cap, one consume/CAS writer and actual causal
   native reply remain needed before Main can enable the false parser flag.

No selected family supplies all required authority now, so no C++ increment is
proposed. This is a bounded missing-supplier result, not global absence or a new
unused factory. Existing native shapes, true saved state, CUSTOM135/defaults,
frozen features and CN separation are preserved. Route/native credits are zero;
TW whole-route denominator and percentages remain unknown.

Custody retains 27 immutable whole source files from exact published HEAD,
12 exact selected line cuts with complete enclosing files, current ledger13/10
metadata projection and in-place whole-ledger hash (no full ledger copy).
Discovery initially returned truncated filename/source outputs; bounded direct
reads and exact retained whole files provide the evidence. Original helper stopped on current App changing under authorized options edits;
its partials and failure receipt remain exact. No product execution occurred. Successful LF custody helper ran once;
no compiler/tests/native/API/parser/codec/SQL/runtime/import/deploy execution.
''')
js(O/'manifest.json',dict(head=HEAD,verdict='BOUNDed SOURCE FRONTIER; no immediately qualified integration in selected subset',whole_sources=len(paths),selected_line_cuts=len(cuts),unconnected_set_count=13,pending_group_count=10,selected_families=3,custom_designs=135,tracked_edits=0,implementation_proposed=False,new_route_credits=0,helper_failures=['original current App==HEAD assertion; authorized concurrent options edits; immutable HEAD successor'],execution='source/hash/git reads only',capture_helper='capture_authority_frontier354_v3.py',successful_capture_count=1))
assert (S/lp).read_bytes()==lb
for r in references:assert (O/r['retained']).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+Path(r['actual_path']).relative_to(S).as_posix()],cwd=S)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()==HEAD
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
js(O/'SEAL.json',dict(head=HEAD,member_count=len(members),member_bytes=sum(r['bytes'] for r in members),members=members))
seal=json.loads((O/'SEAL.json').read_bytes())
for r in seal['members']:
    b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
helper=(O/'capture_authority_frontier354_v3.py').read_bytes();assert b'\r' not in helper
print(json.dumps(dict(head=HEAD,members=len(members),bytes=sum(r['bytes'] for r in members),seal_bytes=(O/'SEAL.json').stat().st_size,seal_sha256=sha((O/'SEAL.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
