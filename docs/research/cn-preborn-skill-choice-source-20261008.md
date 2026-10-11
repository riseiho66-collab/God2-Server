# CN actual preborn skill-choice predicates and common-operation handoff

Round `20261008-cn-preborn-skill-choice-source`; PHASE1 static/source only.
Previous137 was progress: native SKB bindings/common handoff sealed. Saved148
current files before mutation and retained that immutable399-file seal.

## Primary native consumers

Pinned CN PE SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
Five individual primary functions retain2272B and712 entry-rooted instruction
sites with complete local normal CFGs. Helper exceptions, rendered UI and live
native reachability are not implied by those CFGs.

`005331B0` (81B) reads actual selected-list count at this+C3C and pointers from
this+A48; a non-null pointed record matches only when byte1 equals requested
kind and byte0 equals requested ID. Returns1 on an existing match,0 otherwise.
`00532B20` (763B) calls this helper after resolving a candidate's book through
`004D2BB0`; an existing selection prevents insertion. Actual selected count
must also be below unsigned BYTE limit at this+F75 before append.

The insertion excludes WORD book IDs6568..6575,6665..6669,6763..6765 and
6884..6886. The first three intervals use signed-WORD comparisons; the final
interval is exact unsigned16(item-1AE4)<=2. Matched pinned SKB IDs are positive
WORDs. This is a native preborn UI restriction, not a recovered combat rule.

`00533850` (538B) formats the available list: book-reader EAX is retained at
[EBP-8], then site005339B1 reads BYTE `[EAX+12C]`. Nonzero pushes disabled0;
zero calls `005331B0` and passes the inverse duplicate result to `00457A80`.
The actual pinned raw column27 tokens are367 zero,8 one,5 two,3 three,3 four.
Those19 nonzero records exactly match the literal item exclusion intervals.
Agreement of these two consumers does not turn the byte into MP cost, a
class requirement, common ownership or an original server eligibility rule.

`00533BC0` (482B) renders selected entries and compares selected count to F75
in mode1 for its confirmation-button state. The earlier native534810 mode1/
case5 caller and case6 WORD81/83 producer remain bounded prior129 evidence,
retained here without adding a new phase association or claiming all timing.

Book no-match behavior remains caller-specific. In532B20 the out-item address
is the incoming button argument; in533850 and533BC0 it is `[EBP-4]`, without
a visible local initialization in either complete normal CFG. `004D2BB0`
retains that WORD on no match.533850 also later reads book-return EAX+12C.
No zero fallback, missing-book availability, fault behavior or restored native
stack value is invented. The source carries unknown facts for the67 no-match
definitions rather than treating them as ordinary zero-gate books.

## Subject-source distinction and offered list

`00534640` (408B) takes selected-entry pointer from `[UI+430AC]+160` and the
family operand from the WORD reached through `[UI+430A8]`. Existing pinned
mode0 lineage is UI+430A8=object+90; this is **object+90**, not object+0.
Site5346A1 sign-extends the WORD; CDQ/sub/SAR computes signed division by2
toward zero, then only AL is compared to definition byte1.

It retains selected-entry references whose original flags&1 is nonzero and
whose definition kind equals that family byte, or selected-entry signed
WORD>100, or selected-entry byte5B is nonzero. Count/pointer/flags/identity
belong to that actual selected object. No process-memory reader is introduced.
The semantic identity of these raw operands still needs common-source mapping;
they are not level caps, actor IDs or inferred player permissions.

`CnPrebornSubjectState::Snapshot` now separately retains the actual object+90
WORD from already-supplied owning bytes. Existing object+0 identifier is
unchanged. Optional native snapshots remain recovery evidence, never an
operational own-server prerequisite or a pointer-shaped common object key.

## Source increment

Added `CnPrebornSkillChoiceSource::resolve_actual_selection`: resolves actual
shared CN definitions once, optionally with the same actual book supplier.
It owns and preserves WORD ordering and duplicates; request-local repeated
entries record their earlier index. If actual native evidence is supplied,
`CnPrebornSkillReferences` resolves real references and the qualified filter
produces an ordered offered-WORD list and membership facts. Without that
evidence membership remains unknown. A valid definition without SKB also
leaves book gate/exclusion unknown, distinct from missing provider data.

Existing `SharedPrebornWindowSource` calls this resolver before retiring the
issued window, then retains the exact definitions/books/facts through actual
common apply and post-commit delivery qualification. Post-commit code does not
re-run the retired preborn snapshot/window Current. Common owner still must
validate real subject/skill identity, entitlement, rules, transaction/save,
persistent replay, actual new revision and native output. Facts do not grant
or reject a skill by themselves; UI conditions are not server authority.

Actual CN shared rows/catalog/book supplier/common authority/issuer/Application
remain unconfigured. No new protocol, guessed reply, table, DB import/access,
migration or activation. TW source and native book schema/reader unchanged.

## Accounting and full scope

New selection-source resolver1, actual subject-operand projection1, existing
common apply/delivery handoff strengthened1. New packet/phase/network owner/
complete bidirectional routes0. Whole-game denominator/percentage remain null.
Full TW/CN/PC/web/WSS/account/world/all gameplay/numeric64/coin99999999999/
stack99 and later comprehensive testing/repair/recoverable release remain.
No build/test/native/C++/Lua/API/client/server execution, production DB or deploy.
Accounts/saves/auth/chat/IME/portraits/fonts/text conversion/levels/client
binaries and earlier evidence remain unchanged.
