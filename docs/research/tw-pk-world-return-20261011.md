# TW290: retained-world return and the server ownership boundary

This round recovers actual native return consumers and corrects the next source
integration target. It does not add a return packet or activate a room backend.
The preceding TW289 two-owner HP/MP transaction remains unchanged.

## Native continuation recovered

Input is the retained mapped image, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
This identity qualifies the mapped bytes used here, not whole-image equivalence
to an original PE or runtime behavior. Exact selected bounds, raw bytes,
instruction listings, exploratory corrections and scope totals are retained in
the external native-worker archive below.
The selected scope is11 code spans/8,247 bytes/2,394 instruction sites and four
data spans/85 bytes. It includes historical overlaps and is not a globally new
coverage total. The main continuation is an aligned arm, not the whole main
function;46C6A0 is qualified only through its zero-second-argument branch.

The actual main state table at465A14 has eight DWORD targets:
`46595C,4659A0,46597E,465644,46565B,4659C2,4659FB,4659D9`.
After the retained battle-return path, the main function stores local state3;
465949 reads that state and465957 returns to465638. Index3 dispatches to465644,
which supplies its actual stack238 object to467860. The complete467860 world
loop invokes466B00 repeatedly while its result is3; another result returns to
the main dispatcher. The shutdown path using main-ownerFC6B4 returns0.

The selected complete466B00 body actually calls world dispatcher468AE0 at
467154, forwarding the parent T pointer from its stack. Dispatcher result4 is
one route into the battle arm. This establishes a real local world/battle/main
continuation, not a server Session phase transition or a new client ACK.
The state3 arm itself does not issue a fresh2A or replay the login tail.
Opaque children and subsequent dispatcher effects remain unqualified; this is
not a claim that the entire resumed world can never receive2A.

The previously explored502210 helper spans502210..5024B8 (exclusive end). It consumes
aggregate DWORD40/50/5C, main-owner state and cached resource words, updates
packed presentation state and calls resource/presentation children. Its full
top does not read the assumed aggregate identity at+0 or HP/MP. Calling it an
"aggregate-to-actor initializer" was too broad. It does not establish a fresh
character identity, server resource update or revival policy.

Complete500C60..5011BA and5011C0..50160D recover further retained-aggregate
readers.500C60 writes aggregate30/50/5C as well as rendering from existing
resources; it is not a pure packet parser.5011C0's actual return branch takes
the explicit aggregate, while its null branch selects the retained main-owner
aggregate. Its WORD0/48 forwarding through46C6A0 is a qualified UI/context key
operation; it does not establish a common character-ID mapping. Nonzero arg2
in46C6A0 and the opaque appearance/resource children remain open.
The retained world aggregate used by465BC0 is not a reconstructed37-byte
logical2A record (the existing framed entry is40 bytes). Forwarding that
aggregate through presentation helpers does not establish an authoritative
server serializer for it.

Two further misleading leads were resolved:466910 is RET4, and467D70 computes
a mask from a zero-extended BYTE before calling the local removal helper4CC990.
Neither is a recovered tick sender. Complete4FAC70..4FAD19 is a169-byte
text/catalog accessor: it calls4FC960 and copies NUL strings from record+1C,
+2C and+3C into three supplied buffers. The earlier timer/network speculation
and immediate185-byte arithmetic estimate are explicitly superseded. The
native worker preserves the exploratory epoch; no timer, transport or new0B
acknowledgement is inferred from it.
The next native targets are468AE0's resumed-world queue/dispatch causality,
4FB290 on the actual main-owner input/catalog context, and the real outbound
clock/control producer. No timer or transport meaning has yet been assigned
to4FB290. Full saved-aggregate writers and role/companion update sources remain
separate open work.

## Actual server sources and the distinction from login

`Session::normal_world_initialization_current[_on_game]` requires the exact
private original entry and initialization objects, an unretired ready entry,
CharacterSelected/InWorld state, and its original battle generation.
`Session::set_state` increments that generation both when entering and leaving
InBattle. Merely setting InWorld after PK cannot make the old transcript
current. Copying its frame/tail or loading stored bytes cannot mint a new
NormalWorldInitialization either.

Actual PK admission keeps the original common presence and common transport
identity. It withdraws visibility through the paired TaiwanPkDeparture marker;
it does not release the common lease. SharedWorldPresence's ready lease remains
active independently of Session's battle phase until its exact release.
Calling the existing common lifecycle release would revoke that identity and
lease. The original Fresh login lifecycle is therefore not automatically a
return owner.

The visibility departure-current predicate is deliberately pre-release: it
accepts genuine Held/Committed entry transports, not terminal Written holds
after their pending token clears. Its marker still blocks visibility after
that predicate stops qualifying. Visibility.release performs teardown, poisons
and retires the old departure/edges; it does not authorize a successful resume
or generate current native appearance/recipient sets. There is no existing
paired PK resume API to invoke.

RecoveredRoleVitals::encode provides native logical24 with four DWORD resource
fields, but HP loss can also reduce companion HP. The actual Application
fresh-entry path queues player resources before companion binding; its later
optional restoration path explicitly avoids resending24. Reusing that encoder
as a generic post-PK update would skip these semantics and is not justified.
This round leaves the frozen player/companion paths unchanged.

## Corrected source integration target

Earlier frontier records explored fresh normal initialization/presence/visibility
as a return requirement. Those records remain historical. This recovery shows
that fresh2A plus login-tail replay is an unproven plan, not a native prerequisite.
The concrete target is a dedicated retained-world resume owner, with the
following still-missing joins:

- Actual native exit/readiness or subsequent producer boundary that can select
  return timing and supported wire policy. A full local89 write, main state3,
  submitted flags or a saved HP/MP ledger alone does not establish that event.
- The actual retained aggregate, player/companion resource and native world
  update mapping; presentation children are insufficient authority.
- The same original Sessions, leases and departure incarnation, a new
  generation-bound world capability, retirement of battle input/publication,
  and requalified incoming/outward visibility on the common world.
- Durable completion and member-lock release ordered with that genuine return,
  including disconnect, owner loss, retry and process restart.

The TW289 saved-resource guard remains the persistence prerequisite: both exact
resource rows and its privately rederived full ledger must remain current.
It cannot be promoted into a world-ready or native-ACK receipt. There is no
truthful consumer yet for an otherwise unused terminal-resource wrapper, so no
such C++ API or custom return policy is introduced merely to increase counts.

## Accounting and limits

This is concrete static native recovery and source-owner qualification.
C++ modifications0/new C++0; new opcode0; newly connected source branches0;
new complete bidirectional routes0. Existing mixed source segments272,
CUSTOM records125 and reviewed source groups26 remain unchanged.

TW C2S candidates156/world parser74 (limited source50/control11/unconnected13).
World S2C252 (fixed230/variable22), registered replies48/push11/gated4,
unclassified117. Battle indexed110/specialized9;86selectors7/cases6;
83actions23/scalar projections2. TW unhosted owner chains3/bindings38(unique34);
CN chains35/bindings93(unique71). CN historical C2S156/S2Cphaseopcode280/
length253 is a different scope. Full route denominator and TW/whole-game
completion percentages remain unknown/null.

Application hosting, rewards/EXP/revival, complete skill/action and extended64
wire/object/display paths, full TW/CN/web support and eventual comprehensive
acceptance remain required. Original accounts/saves, authentication, chat/IME,
fonts/text conversion, NativeParty and native executables are unchanged.
No compiler/build/tests/runtime/native execution/VM/emulator/asset codec/
game DB/SQL/migration/activation/deployment was performed.

Evidence archive:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-world-return-290`.
Worker findings retain exact manual read scopes; retained whole-file bytes are
not a claim of whole-file or opaque-child manual certification.
