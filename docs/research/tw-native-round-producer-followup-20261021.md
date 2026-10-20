# Native round producer follow-up, pass7

Status: PHASE1 SOURCE_STATIC_ONLY. No build, test, target/game, VM, codec,
game SQL, migration or deployment ran. No core source changed in this lane.
This is a bounded client write/alias and UI investigation, not recovery of an
original server counter, speed comparator or scheduling rule.

## Input and reuse

Original `God2.exe` SHA256 remains
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
Evidence root D:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass7/native-round`.

The explicit independent analysis copy `D/round-independent-pass7.analysis-pe.bin`
is 3,238,912 bytes, SHA256
`e447ed88994f5716182c8d44a099d835080f608cb627d0002ac3ee1acf51020c`.
Its purpose is a separate analysis/cache path during parallel material research;
it is not an executable deployment. All13 original PE sections were checked
byte-identical. Extra CALL seeds belong only to the analyst section and do not
establish native callers. `round-analysis-input-provenance-v1.json` pins the
original, previous analysis input, section offsets and hashes. No saved analysis
database was shared or modified. One REA CLI session was used, then closed;
`close-round-pass7-a.json` and `helper-cleanup-round-pass7-a.json` record target
closure and natural CLI exit0. The parent helper shell also exited0.

The pass6 K pulse, S88 consumer and timeout-pair findings remain the baseline:
[pass6 native research](tw-native-role-timeout-k-pulse-20261021.md).
Their unchanged consumer behavior is not counted as a new server rule here.
The older [speed backtrace](current-battle-speed-backtrace-20260920.md) uses its
own149c image and prior bounded runtime evidence; this pass neither reran that
VM nor upgrades fixed-slot animation activation into initiative.

## Latch6C: bounded computed-alias review

B denotes CWar. Latch L is DWORD `B+A9E9C6C`, distinct from the S88 counter
DWORDs64/68 and the manager's actor-completion counts.

The complete loaded-image byte search for literal displacements
`A9E9C00..A9E9CFF` returned269 matches in41 recovered containing procedures.
All41 instruction bodies were inspected:11 existing instruction receipts were
reused and30 additional bodies were retained. No indexed memory operand with
a control-page displacement appeared in these bodies. The derived review
`control-page-alias-review-derived-v2.json` lists every source receipt/hash,
effective-address formation and direct L instruction.

Only eight control-page LEA sites occurred:

| Formed address | Caller/use | Recovered write bound |
| --- | --- | --- |
| `B+...C58`, `C5A`, `C5C`, `C5E` | `5112C0 → 41FE00` graphics action dimensions | each output is one WORD; occupied range58..5F, below L |
| `B+...C80` | `512620 → 512430` selected-target count | writes one DWORD at80..83; other writes are to the separate44C target buffer |
| `B+...C7A` | `515770 → 483150` selected item/shortcut result | direct writes and forwarded49E9D0→49E8F0→49EAB0 write offsets0..3 only, range7A..7D |
| `B+...CB0`, `CB1` | `5140C0` received-record scratch and appearance view | start above L; explicit copy/consumer accesses in the reviewed path are nonnegative |

The four direct L instructions are unchanged:

- `516751`: DWORD store from zeroed EBX, first-effect516740.
- `516AF4`: DWORD store from zeroed EDI, first generic S83 effect516AE0.
- `518B9C`: DWORD read into EAX; receiver compares it with1.
- `518BAE`: DWORD store from zeroed EBX when that test matched.

No set-to1 or pointer escaping to L was recovered in this scope. This improves
the prior literal-only check by closing these concrete nearby out-parameter
routes; it is not a global no-alias proof. A computed base formed outside this
page, indirect target or unrelated bulk write remains outside the bound.
In particular, absence of a recovered setter is insufficient to declare that
all original executions always initialize L to zero.

The native value-flow API does not close that gap. The grant-root graph retained
714 nodes/766 edges and twelve decompilations, but reports `truncated:true`,
unavailable parameter bindings, call-depth/decompilation limits and unknown
alias dependencies. `next_offset:null` means no further node page, not complete
whole-program coverage. Do not use this graph to certify the missing setter.

Evidence: `control-page-literal-alias-candidates-pass7-v2.json`
(`ev_0ef235b0d11fcdc768ccb4de54680217813b863f44c2b949daa35b5fa9c5298e`),
`timer-output-alias-and-role-ui-state-pass7-v5.json`,
`computed-control-outparameter-bounds-pass7-v8.json`,
`forwarded-control-pointer-write-bounds-pass7-v9.json`,
`drag-control-output-alias-final-pass7-v10.json`, and the three raw latch
instruction receipts v5/v6. The v1 derived candidate mistakenly included a
SUB reading elapsed time as an address candidate; v2 explicitly removes that
false candidate and preserves v1 for audit.

## What the ordinary UI actually enables

For one selection widget W, `50CAA0(index,value)` writes DWORD
`W+148+4*index=value`; a zero value also chooses its disabled color.
`50D8A0` checks this exact enabled entry before returning a hit/keyboard
selection, and `50D310` refuses to select a disabled entry. This is a real
selection gate, distinct from merely changing an icon's palette.

The primary action widget is `B+AB3B428`, and the secondary action widget is
`B+AB3B670`. The recovered constructors50FB10/50FF00 enable their nine/five
entries with1. Their click callbacks50FE40/5103B0 call50D8A0 on those exact
widgets; primary maps index+1, secondary maps `[1,2,3,6,9]` as already recovered.
The corresponding main/secondary bar is shown by50FDC0/510300, selected through
5120B0 from A/B role-control flags. These visibility and hit-selection steps
do not inspect both actors' HP or require a pet pair before action9.

All direct50CAA0 callers were retained. In the reviewed CWar range, the main
and secondary constructor loops initialize their entries; dynamic calls belong
to separate item/skill subwidgets. For example511C30 checks server-supplied
item-button mask84;51C050/51C1F0 inspect the corresponding per-choice bit80
and disable empty choices. These are separate widget owners, not evidence that
the primary action9 entry is enabled/disabled by a recovered death rule.
Generic UI calls elsewhere and indirect writes were not exhaustively proven
to affect no CWar widget. The supported conclusion is the bounded shown-bar
and actual selection chain, not universal UI-state coverage.

S86/5's517590 write-set confirms the existing additive-control contract:
bit0 sets A38 and primary B51, bit1 sets secondary B3C and B52. Absent bits do
not clear old flags. The receiver updates timer10/18 and role displays, not
counter64/68 or L. Command518E50's common A-first cleanup remains the source
of consumption. This was already reflected in the PvE projection; it is not
a newly discovered defect. A mask-zero grant packet cannot be repurposed as
a general revocation packet. Original server authority remains independent
of the client widget gate.

Evidence: `control-enable-writers-pass7-v2.json`,
`role-control-and-ui-enable-producers-pass7-v3.json`,
`button-enabled-value-setters-pass7-v4.json`
(`ev_540f9cd2ec7ae8a69faae11ec344f5e519d629a0f8591415a2523f3610bbb3af`),
`incoming-button-enabled-setter-pass7-v4.json`, and widget-base/hit assembly
receipts v8/v9. Interior queries50FC40/5101A0 resolved to containing
50FB10/50FF00; they are not new distinct functions.

## K, counters and the remaining server input

The pass6 exact K relation is retained: manager `M=B+144938`, persistent mode
`M+2E0`, one-shot pulse `M+2E4=B+144C1C`. Actual52AEA0 writes both; reset and
eligible queue-idle paths set1, first-effect paths set0, and515770 consumes only
the pulse. K is not the entry context_b field. No new sender-side counter rule
was recovered from these UI or alias paths.

S88 supplies the DWORD which the client stores/compares. The initial receiver
populates64 and68; later receptions normally update64, with L's conditional
one-reception suppression. This constrains a compatible explicit producer,
but does not identify how the original server generated that value. Neither
the timer-reset field nor a main/secondary grant is that counter's source.

The client queues supplied animation groups and activates actors by its known
slot scan. That playback mechanism supplies no authoritative participant speed,
initiative comparator, ties, skill priorities, modifiers or RNG ordering rule.
Those inputs and the sender assigning S83 groups/S88 counters are the exact
missing authority. Inferring their numeric values from this consumer is
underdetermined. Existing CUSTOM scheduling must remain labelled as such.

Usable source contract: preserve additive control and A-first role consumption,
retain genuine group/counter widths and the already qualified queue boundaries,
and keep widget eligibility separate from authoritative actor/grant checks.
No additional core defect requiring a change was demonstrated by this lane.

Next meaningful client trace, if needed, is a specific discovered incoming
writer/alias that reaches L or a source carrying identity-bound speed/ordering
data. Repeating the same S88 consumer, slot-scan, whole-object byte search or
timer display would not recover the original server producer. Native runtime
timing, Windows compatibility and end-to-end acceptance remain unperformed.
