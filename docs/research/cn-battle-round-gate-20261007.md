# CN BATTLE88 batch and86/5 command gate

Pinned CN582F, static primary recovery and source integration only. Previous
goal round made progress: catalog50 sealed86/0,1,6 raw scalar destinations and
the seven-value/six-target local subtype CFG. No build, tests, runtime, native
API execution, DB access, resource decode or deployment in this round.
Immutable evidence: `artifacts/integration/packet-connections-20261006/cn-battle-round-gate-01`.

## Native88 contract

BATTLE88 is121 logical bytes. Deferred00551D50 selects00552439;
only when its actual progression flag allows does it call0054D450 with the
full logical record and advance the queue. It then stops the current consumer
progression. Queue presence alone is not permission to emit the next round.

0054D450 reads DWORD1 as a native round word. When prior main+A97124
isFFFFFFFF it initializes native current/first round words; otherwise primary
0054D4A5 sets main+A97130 to20. An independent branch later changes current
round word depending on main+A9712C. No official encounter sequence or server
round numbering inferred from these local assignments.

0054D598 calls00561C40 with ECX=main+149DF8 and argument logical+1.
Its fourteen loop iterations use actual side0 base pointers at
owner+38+slot*18, copying DWORD5+slot*8 to actor+DE8 and DWORD9+slot*8
to+DEC. This is a current-pair batch only; maxima+DF0/+DF4 and side1 remain
unchanged by this writer. Every base pointer is dereferenced without a missing
actor fallback. The source projection requires fourteen actual prior objects.

0054D450 also reads byte118 into main+A97144, synchronizes a selected
local role, and0054D5AD calls00561FD0. That reset walks both sides, all14
positions and six layers, clearing object+DF8..+EC3 (204 bytes),+EC4,
effect handles and the layer5 render handle. It is not evidence of a newly
transmitted enemy skill list. The scalar source projection does not emulate
these effects, resource releases or pointer lifetime.

Opaque batch bytes117,119..120 and all caller-supplied round/control bytes
are retained. Only the two known current DWORDs in a supplied slot can be
changed by the typed adapter; no blank actors/rounds or numerical defaults.

## Native86/5 contract and actual clock source

The17-byte logical86 kind5 enters0055236B and0054CD80(full logical).
Native flags are byte3 bit0/bit1. bit0 sets main+A970F8 and stores
byte4 low nibble into selected primary position main+51; bit1 sets+A970FC
and stores byte4 high nibble into secondary position main+52. Existing
granted-channel flags are not reset by this function.14/15 are inspectable
raw nibble values, not qualified native actor slots.

WORD5 is promoted, incremented and displayed in three decimal digits. It
is not duration or a transmitted skill parameter. The current UI handle
gates some display operations; setting flags alone does not prove all actors,
menu state and actual command ownership are ready.

0054CD88 calls timeGetTime;0054CD97/9D reads main+A97130 into+A970D8.
The frame tail00547E46..00547E6F later computes DWORD wraparound
elapsed=now-start, unsigned elapsed/1000, then stores duration-elapsed/1000.
The division is primary MUL10624DD3 followed by SHR high product,6.
This tail is entry-connected from005471F0, including a path that bypasses
its unresolved UI switches00547373 and0054774D. Those indirect cases
remain open; this is no claim of complete UI-producer closure.

00551430 compares the remaining bits as signed: negative values trigger
the timeout path and are set to0; exactly0 is not negative. Sending WORD5=20
does not set a20-second clock. The first88 preserves actual preexisting
duration; later88 changes it to20. The true entry-duration writer still needs
recovery and no server duration/ordering policy is synthesized.

`CnBattleCommandGate` exposes requested channels, native slots and display
counter. Its clock helpers require actual duration/start/current tick; they
project this arithmetic without executing a native clock or issuing timeout
commands.00551430's actual timeout may call0054FFC0, which needs separate
producer/authority recovery before becoming a server command rule.

## Source increment and accounting

Added `CnBattleRoundBatch` and `CnBattleCommandGate`, connected them through
the existing `CnBattleDeferredRecord`, and extended the existing scalar
projection with side0 batch writes. Both records retain complete native bytes.
Batch/gate parsing does not create a common battle authority or supply pointers.
No TW CUSTOM battle core was promoted as CN native rules.

New source phase-opcode binding1 (BATTLE88);86 was already bound in catalog50
and gains only the scoped kind5 variant. New complete routes0/owner chains0.
Actual native admission, current recipient/slot incarnations, full actor reset,
command producer authority, Lua/storage and Application battle hosting remain
missing. Whole-game denominator and completion percent remain null.

Next trace the actual82 transition/entry-duration state and0054FFC0 request
producer. Enemy true attack/defense/attributes/elements/carried skills remain
separate unresolved goals; current display-pair bytes are not base stats.
