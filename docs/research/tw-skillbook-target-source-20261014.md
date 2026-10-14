# TW target-item producer and skill-book operation boundary

Round380 corrects the overly broad C25 book-use direction in round378. The
native inventory branch, after the equippable mask0x04 arm, tests metadata11A
masks0x01+0x08 before the numeric master ranges. That targeted branch opens
cursor mode7 and retains item/slot/pending
state; it does not queue C25 there. Only the later ordinary, non-targeted branch
reaches the qualified C25 master confirmation or ordinary-use producer. These
branches are conditional native paths, not a claim that every SKB row has the
same flags or that every C26 operation learns a skill.

The existing MED02 self-use evidence already distinguishes target producer
4964D0 from shortcut producer4963C0. Their normal C26 record is seven logical
bytes: opcode26, targetWORD, itemWORD, slotBYTE and opaque tailBYTE. The target
WORD is not interpreted here as quantity, a database character ID, a deity row
key or a skill grant.
The shortcut copies the low WORD through UI8688C; the targeted producer has a
separate actual caller and pending material. Historical native runs and their
synthetic MED inputs are references, not new execution or SKB acceptance.

The newly followed actor-target caller, not restricted here to self, is46611B
in465FA0's operation-12 arm. It
selects the first non-FFFFFFFF DWORD in offsets0,C,4,8 of its supplied four-slot
target candidate array. Main466F6D passes that stack array after actual466E47 calls4FB290.
The latter's whole body and465FA0 were already qualified in round303 and are
reused, not recaptured or counted as new code. Its matching writes carry actor
DWORD0 from a128-entry, stride268 actor pool, using actor48 and cached context
handles. Such a matched native actor ID is distinct from selected deity memory.

Main initializes all four candidates toFFFFFFFF. A stack-relative reading of
466E40 alone is misleading:466E3F PUSH EDX first moves ESP down4, so its following
[ESP+5C] store addresses the original frame+58. The first three stores addressed
original frame+4C/+50/+54. The lookup also clears output0 and writes slots on
matching branches; under the actual initialized caller, an unwritten slot stays
the sentinel. The initial N380 sealed interpretation missed that PUSH and is
retained with an additive correction. Actual matching write, current object/
context/lifetime and normal-return premises remain necessary; raw target equality
alone grants no authority. Opaque movement/resource children do not establish
stable global bindings or server-side target ownership.

Producer4964D0 also has a distinct pending item15C6 branch which queues AD
with twelve body bytes, only selected fields written. This is not normal C26,
not a discovered skill-learning response and not permission to register an AD
handler or zero unknown bytes. Normal C26 carries an unwritten local tail byte;
the producer does not read pending flag U85603.

New raw code141B/39sites is whole4964D0 (121B/31sites) plus the authentic Main
frame prefix (20B/8sites), data0. The Main parent is not claimed complete.
Old303 whole465FA0 (1180B/426sites), whole4FB290 (446B/140sites) and selected
Main338B/97sites are references only. Four prior seals157members/7364185B remain
unchanged; no original image or large archive is copied or native code executed.

Actual Main C26 currently supplies CUSTOM0050 self-player MED use and a
separate custom teleport-gem operation. NativeSupplyCatalog qualifies71 MED02
declarations; SKB6501+ cannot enter that catalog. DiagnosticSupplyService's
existing Lua projection, prebuilt S41/S24 reply and one inventory/resource CAS
are real, but own no skill, selected deity, learning event or S35 state.
Supply Lua receives owning numeric values and has no shown Session/presence,
send/save or event-pump capability. No actual Lua-induced Session-retirement
bug was established, so no speculative guard or unused book coordinator is added.
Legacy CUSTOM0050's actual entry uses the DB character ID within1..3FFF; no
current identity mismatch is established there. The independent scene-handle
profile replaces that legacy whole world callback, including its supply branch.
Its existence does not silently broaden CUSTOM0050 or turn native actor IDs into
database identities generally.

The next operation must independently bind the exact current actor/material
and book instance to the intended shared skill and learning subject, qualify
eligibility, and own one learning/debit/save/replay transaction with complete
native result order. A verified alias, native actor ID, saved S34 presence or
client S35 flag does not supply those rights. C25 and C26 skill-book variants
are explicitly pending; existing MED/map/gem branches remain partial coverage.

TW complete source routes to100% remain first priority. This round does not
complete a gameplay route or add a formula, custom rule, Python file or C++/Lua
behavior. Canonical492/source18's47 pins remain exact. One explicit pending
book-variant group raises pending groups11->12, with no new connected opcode.
Parser77=50partial+11control+16unconnected and frontier26 formats21/gaps105 stay;
whole-game denominator/percentage remain unknown. PHASE1 remains static only: no builds,
tests, runtime/native/VM/codec/gameDBSQL, migration, activation or deployment.
