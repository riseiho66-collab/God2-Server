# Round332: actual E8/E9 byte receivers and deferred UI event source

RecoveredWorldUiByteUpdates preserves two distinct native S2C logical2/body1
records as opcode kind plus full raw BYTE. E8 and E9 each have independently
qualified length, WORLD dispatch and direct receiver writes. Neither is a
PetEgg list payload. Their source classification changes independent formats
12->14 and unclassified nondefault WORLD rows114->112; completed gameplay
and bidirectional route increments remain0.

## Actual table entries, without adjacency guesses

Pinned149c mapped image and5fc originalPE are read/hash-qualified in place.
All14 captured cuts agree with mapped bytes and original PE offsets:
261codeB/45dataB; the shared length leaf is retained with method novelty0.
E8 WORLD cell46B974 points to46B46E, which advances EBX to body, computes
ECX=Main+A7F2F6C (primary UI U) and calls4E8550. E9 cell46B978 points to
46B480, using the same primary U for4F9980. Their length cells4016C4/C8
both point to complete401216 MOV EAX2/RET. Numeric opcode adjacency does
not imply adjacent WORLD code: the case after4691FD is not automatically E8.
The actual cells qualify each separate source route.

## E8: raw byte into an indirect context

Complete4E8550..4E8576 reads body0 with no mask and copies it to BYTE P15E,
P=DWORD[U+8688C]. It has no direct null/key gate. It then rereads U8688C,
forms that current pointer+90 and invokes complete4E8580..4E8600 with ECX=U.
The codec retains every raw BYTE and does not coerce it to boolean.

The child requires signed WORD U232DDA>=0 before reading BYTE[arg+CE]; since
arg is reread P+90, this source is reread P15E. Whole byte0 and1 select two
UI5068C0 call sequences using handle and controls22h/0Ah/0Bh; other values
return. Handle is reread between calls; opaque UI effects prevent asserting
the final object, same handle or same pointer at a later event. This consumer
is not evidence for an original issuer, item owner, PetEgg state or B1 reply.
Native PUSH uses WORD/AX or CX operands in registers without newly clearing
their upper bits; no canonical DWORD handle identity is inferred. The second
handle read has no added sign gate after the first opaque child.

## E9: primary raw copy, then two direct zero writes

Complete4F9980..4F99B2 reads body0 and stores the full BYTE into U8B747.
It clears WORD U8B744 and BYTE U8B746, in that order after the raw copy.
Then it calls opaque4F7BC0 using U, followed by4B1A80(28h) using U.
No status whitelist, low-bit mask, type/key/slot/ownership predicate or copied
48B array exists in these direct instructions. Children are left opaque:
these initial writes do not certify final state, timer behavior or successful
server operation. The codec performs no UI mutation or emission.

## Actual deferred control/event output source

Complete504620..504C84 (1636B) has two RET8 at504958/504C81; final6cuts
are1850codeB/24dataB, all pinned PE-equal. No descendant was opened.
Actual parent48224A..482261 passes ECX=H=U+E2170 and two distinct pointers:
formal1 to control WORD at caller post-call local+14h; formal2 to event BYTE
at local+10h. Only returned AX becomes the widget DI used for later matching.
MOV EDI,EAX and subsequent DWORD local pushes do not qualify upper register
or local bits; deferred consumers use signed WORD control and BYTE event.

The method initializes control=FFFF and event=0. H+4 supplies pointer P;
entry snapshots DWORDs P1202C/P12018/P12014/P12020. It processes the linked
list at H+14 with opaque UI/resource children, then rereads current nodes.
Each signed nodeWORD0 gives widget W=H+818h+2A08h*index. No ownership or
nonnegative-index boundary is established by this client arithmetic.
An early special path writes event2, clears widgetBYTE14h and returns
nodeWORD0 as AX with control stillFFFF, skipping ordinary feedback tail.

Ordinary selected processing scans106 control records (decimal), each
100bytes (decimal; stride64h), base W+A0h. A nonzero rowBYTE0 and opaque418CD0
predicate select the first matching row. At504B01, BX writes its original
index0..105 to control WORD, even if feedback rowWORD0Ch is negative.
This native control-row identity is not automatically the compact label
index from PetEgg list opening. An alternative widget flag/resource path
can bypass this scan; full ordering remains in the sealed report/TSV.

Ordinary captured P12014/P1202C/P12020/P12018 sources OR event04/01/20/02
respectively. Event01 has a control-dependent suppression gate; multiple bits
can coexist. A separate local gate controls clearing those current source
fields, not whether the event bits are ORed. H+4 is reread for each clear.
The feedback tail may invoke opaque5068C0 and stores paired local tuples
to DWORD H150C1A/H150C1E. These are local UI fields, not queue envelopes.
The no-selected path retains event0/controlFFFF/widgetFFFF. Later children
remain opaque, so no final event lifetime or state lease is inferred.

After the poll returns, the actual parent first calls46D000/4D7230/4D9F20,
then other conditional UI work and signed widget/control gates. Its real
482748/4827A5 dispatches match current U232E9C/U232EA2 and pass these low-width
locals to known330 full4DA730/4DC880. Both action methods invoke opaque49B820
before reading event/control, give bit02 close priority, then require bit20
for their selected actions. Only later4D6BA0 independently queues B1 selector
BYTE. The poll does not serialize output pointers/widget/control fields.
Historical parent/action methods receive new coverage credit0.

This closes a concrete actual UI output alias chain. Writers of P1202C/
P12018/P12014/P12020, H+14 node construction and418CD0 predicate remain
unqualified. They would further explain UI input, not prove server authority.
NonzeroU0A population, true current owned-item state, native operation rules,
issuer, causal responses, storage and recovery remain separate open work.
No synthetic UI state supplier or new gameplay handler is introduced.

## Source integration and scope

Frontier v21 reads immutable v20 as a complete object, requires exactly E8/E9
new independent classes, checks their fixed2/NONDEFAULT/native dispatch rows
and appends only INDEPENDENT_FORMAT_ONLY. Every prior native row field and
named326/328/331 increment remains retained. Existing E5/E6/E7 source, Options
B1 selectors7/8, frozen gameplay and parser behavior remain unchanged.
The new codec is a raw view only; no handler, guessed original server producer,
causal B1/E5/E6/E7 pairing, current owned-item supplier or list writer is added.

Previous331 was progress: actual E7 raw format and genuine same-U zero writer
were published as0f01cd9. This round's adjacent opcode investigation found
different receivers, changing the next recovery action. PetEgg nonzero U0A
population remains open. Array zeroing, local UI events and display predicates
cannot replace actual current full20 ownership or game rules/storage.

External native evidence is under
C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-e8-e9-source-332.
The directory name retains the original bounded investigation scope; actual
E8/E9 receiver identity is as above. Native images are referenced, not copied.
The independent event package is
C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-event-control-source-332.
Its provisional discovery cuts remain preserved; final coverage excludes
discovery duplicates and adjacent unqualified methods. The final report
records the early event2 path separately from ordinary captured-scalar bits.
Historical evidence and any discovery material remain retained without
recrediting old native methods or rerunning historical probes.

TW scoped counts remain C2S156/S2C252/world74(partial50/control11/gap13);
CN C2S156/S2C phase280/length253. New opcode/parser/phase/authority/gameplay
increments0; denominator/TW/whole completion remain null and goal active.
TW/CN/web/shared tables/common64/coin99999999999/stack99/native levels and
frozen saves/fonts/text/features remain required. PHASE1 static source/hash/
PE/Capstone/report only; no builds/tests/runtime/native/VM/codec/gameDB/SQL/
migrate/activate/deploy occurred.
