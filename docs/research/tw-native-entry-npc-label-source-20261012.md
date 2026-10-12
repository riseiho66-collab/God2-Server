# Round323: preserve the native entry NPC ID label request

Two existing C++ headers gain ten lines: an exact read-only flag projection in
RecoveredWorldEntryView and its forwarding accessor in the actual Entered Scope.
One native field-use crosslink is recovered; no new full source-owner chain,
native opcode, gameplay branch or complete bidirectional route is credited.

## Recovered native source relation

Pinned149c mapped image and original5fc PE agree at all selected cuts. Body DWORD0
bit31 is logical4 bit7:4681EB loads the body DWORD,4681FF shifts31 and468204 stores
the resulting0/1 to world+A7F2F3C. WORLD72 composite variants46A84C/46A990 load that
same world field and push it as4CBD70 argument8. This is structural def-use;
intervening mutations, lifetime and all other uses are not globally closed.

For a new NPC slot,4CBD70's4CC253 reads argument8 at entry-SP+20h and passes it
as4CAFE0 argument6.4CB05D reads that argument,4CB061/063 test/branch on zero.
The nonzero branch formats ASCII `npcid:%d` using the actual NPC row DWORD0,
then4CB087 calls509E70. The guarded text writer copies the NUL-inclusive text
to its display row+81h with optional leading padding for a14-character width.
That width is formatting, not a proved buffer capacity or permitted NPC ID range.

Composite catalog/resource guards and new-slot applicability remain essential.
Existing-slot updates need not recreate the label. No rendered success, valid
resource creation, all-NPC behavior, gameplay privilege or original server
flag-selection rule is inferred. This is not a monster ability/stat field.

Six selected spans total648 code bytes/233 instruction sites and two data cuts
total13 bytes. Relative to the explicitly named315/known reference only,282B/
107sites are outside that union and366B/126sites overlap. These are not global
novelty or full-function/game coverage claims. Complete caller maps are boundary
evidence; only the selected trace and necessary joins have semantic qualification.

## Source projection

`npc_id_label_requested()` returns exactly `(logical[4]&0x80u)!=0` from the
complete received entry. Entered Scope forwards it without reading another
snapshot, constructing native bytes, setting a default, changing layout or
granting authority. It makes this recovered request available to the existing
mandatory scene supplier. No concrete supplier invocation, NPC label publication,
new original frame producer or active Main binding is claimed by this accessor.
The complete raw entry remains unchanged, including every other packed bit.

## Equipment source cut and next work

The actual C28 Action still has no literal three-store mutation caller in the
bounded src/scripts h/cpp/lua search. This does not prove global absence.
320/321 already preserve inventory/equipment/existing-entry and its private
EntryCommitted through the inventory component and held DA factory; another
equivalent wrapper would not supply the missing Action.

The real Action must supply complete next inventory/1215B equipment/full40B
entry, genuine ordered3B/41 count/opaque data and the original rules/phase.
Returned sender Reply bytes accumulate in original mixed-batch order, while
held DA uses a separate qualified observer send. Receipt sharing alone does
not establish complete stat/self/observer reply order or mixed fanout, nor is
this a claim that different recipients require a single global order.
Post-COMMIT output failure cannot undo durable mutation; actual recovery and
fresh response authority remain required. The sealed worker report's text
`414991E0` is a typo; the source address is4991E0. Its original report is retained.

Next native entry work must recover genuine full2A setting authority/B8/B26 and
complete6F DWORD9/17/full81B issuer, rather than infer producers from consumers.
For C28, obtain the actual full-next/rules and response owner before connecting
the existing transaction directly. Full-game direction/phase/state/variant and
deferred-path denominator remains open; these source cuts are not gameplay.

## Counts and phase

TW C2S156 candidates; world74=partial50/control11/unconnected13.67.6% is only
partial world parser coverage. S2C252=fixed230/variable22, nondefault206/default46,
reply48/push11/gated4/unclassified117. Battle indexed110/specialized9;86selectors7/
cases6;83actions23/projections2/outside21. TW unhostedchains3/bindings38 unique34.
CN C2S156; S2C phase280 and length253 are separate scopes; chains35/bindings93
unique71. Mixed282/groups26/pending10/CUSTOM135. All count deltas are0.
Whole-game packets/routes/denominator and TW/overall completion percentages null.

No builds/compiler/tests/runtime/native/VM/emulator/resource codec/game DB SQL,
migration/activation/deployment. Static byte custody and source review only.
Custom registry, shared tables/TW/CN/web, shared64 plan, coin99999999999/stack99,
native levels, accounts/saves/auth/chat/IME/portraits/fonts/text conversion and
client binaries remain unchanged. No new custom rule or balance value is added.
Heavy evidence stays outside Desktop/God2. The native worker stopped with a
capacity error after its candidate was fixed; root read the selected trace,
completed its archive seal and retained the independent bounded review.

External root: `C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-npc-label-source-323`.
Native: `../tw-native-entry-packed-mode-source-323/native-entry`.
C28 source: `../tw-native-owned-equipment-action-source-323/c28-source`.
