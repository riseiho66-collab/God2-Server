# Bounded teleport trigger follow-up — 2026-09-27

Read-only current EXE/source review and isolated original-code execution. No
client/server/UI process, src/Lua/config change, or gameplay acceptance.
Current EXE SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Read the September26 teleport UI/routing/authority reports first; their menu
receiver/selection contract and authority gaps remain in force.

## C2S6D candidates

- `004A6760`: case `param1=1`, `(short)param2+1B=24` (param2=9) checks
  `0050E7D0`, then dispatches6D. The sibling `param1=0/case24` toggles another
  local window through `004C7460`; neither branch constructs the teleport body.
  Native gate `0050E7D0` returns `[ECX+24]==0`. The outer function first rejects
  when the valid dialog at UI+232E68 has flag20; its param1=1 group additionally
  rejects when `004F96B0` returns nonzero. The actual GUI label is unqualified.
- `00503AD0`: same state gate, then dispatch6D through world+ A7F2F6C. Its
  discovered caller is world main loop `00467860`: if Z/X/C checks fail,
  `00418440(2D)` succeeds and calls503AD0. `418440` tests418370 then consumes
  key state through4182A0; 2D is the supplied key code. Naming it Insert relies
  on the keyboard binding being the ordinary Windows virtual-key mapping,
  which was not fully traced here.
- `00501810`: incoming world dispatcher `00468AE0` case4A calls it unless
  world+30==8, in which case the update is deferred at world+A7F2F44. The
  function rebuilds local character components from the received appearance,
  saving world+AA364AC at entry, and queues6D at its tail only if that saved
  flag was nonzero. This is not a local teleport menu opening routine.
- The gated object is a renderer component group: `0050E310` hides its four
  handles through41B740/41BF30 and stores object+24/+28=1; `0050E790` switches
  that state, invoking50E580/50E640. This qualifies a display-state relationship,
  not an authoritative service meaning for C2S6D. None of the inspected callers
  invokes menu receiver4F6360 or builds its28-byte context/destination storage.

## Actual teleport-item producer distinction

`current_teleport_trigger_followup_20260927.py` executes all46 current ItemType
row slices and native59380 lookup: SPI is ordinal9, parser selector0. It then
executes original59420 for5571/5601/5605/5609; all yield flags+11A=`F1`.
Their source rows are8238/8268/8272/8276 respectively.

The original inventory use event `0049A330(slot,4)` takes bit1-enabled,
bit4-clear, bit8-clear metadata through the ordinary branch to
`0049A6B3 -> 00496350 -> 004132E0`. All four selected items emit logical25.
The emulator adapts away only49B820 tooltip presentation; metadata lookup,
category/item comparisons, request producer and queue execute original code.
The native producer still refuses nonzero UI+866E4. No menu construction occurs.

The separate owned-slot shortcut `00496390 -> 004963C0` is **different**:
item/100 equal55 or53 calls96350; other categories with bit4-clear emit26.
Thus5571 emits25, while5601/5605/5609 emit26 here. This entire shortcut chain
executes without stubs, for slots0 and29. Do not use a shortcut probe to stand
in for the actual inventory use event or assume one item has one universal
opcode. The26 producer includes local identity, item and slot; its trailing
byte remains opaque in this fixture. No new26 server contract is asserted.

Evidence: `artifacts/research/current-teleport-trigger-followup-20260927.json`,
12 native route vectors accepted, ten inspected code spans match current PE.
This establishes producer behavior with synthetic owned inventory/UI state;
it does not establish a real UI click, grant, effect, or original service reply.

## Next step and remaining boundary

The useful isolated action is real backpack use of5571 or5601 and capture of
the exact25 request. Pairing its server result with6D still needs authority:
current item text describes single-destination return (5601 consumed), so it
does not establish a five-city offer. Do not install6D→menu or25→menu from this
evidence. An explicitly labeled owned-server offer/selection renderer probe can
qualify the6D UI separately, while item context, arrival, fees/cooldown and
atomic item deduction remain separate unresolved decisions. NPC interaction
for a source-placed teleport actor remains another lead; this lane did not
invent placements, infer contexts061E..0622 from item IDs, or choose arrivals.
