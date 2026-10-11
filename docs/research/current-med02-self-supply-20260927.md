# MED02 self supply: nonzero slots and complete response consumers

Date: 2026-09-27. Scope: current client native protocol/state qualification and
CUSTOM-0016 balance review. This lane changes no runtime, database, or client.
Synthetic state below is `CUSTOM_TEST_NOT_NATIVE`; recovery declarations are
source text, and producer/consumer execution is native client evidence.

## Reproduction and identity

From the server root in PowerShell:

```powershell
$env:PYTHONPATH='artifacts/tooling/crypto-oracle-python'
python -m tools.strike_lab.current_med02_self_supply_20260927 --output artifacts/research/med02-self-supply-20260927.json
python -O -m tools.strike_lab.current_med02_self_supply_20260927 --output artifacts/research/med02-self-supply-20260927-optimized.json
```

Both runs PASS: 17 producer vectors, 2 blocked producers, 4 full response pairs,
1 neutral full24 replay, and 1 active-God damage counterexample. Output uses
explicit checks and is published by replacement only after verification.

- Current `God2.exe` SHA256:
  `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Inherited mapped-image fixture SHA256:
  `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
  Native item parser code spans are compared with the current PE before use.
- Gamedata compressed SHA256:
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`;
  decoded SHA256:
  `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- MED02 source line 6354: item3101 金創藥, declared HP100;
  line6360: item3107 順氣藥, declared MP50. Actual native parser yields flags
  `FB 07` / `FB 01` at definition+11A. The JSON retains parsed record hashes.

The inherited fixture uses actual WPN resources to initialize its graphics
nodes; MED definitions are then installed for item lookup. This does not
qualify MED icons or a fresh medicine tooltip. All relevant game callees run;
there are no game-function substitutes. Native sound remains in its original
absent-device state, and the initialized HUD has no final renderer.

## C2S26: actual nonzero-slot paths

All addresses here are VA at image base00400000; subtract that base for RVA.

1. `0049A330(slot,4)` runs through return with item3101 in slot5 and item3107
   in slot12. The test deliberately supplies a matching tooltip cache. Actual
   source flags choose the target-selection branch, call `004834E0(7,1)`, and
   set UI+85600 WORD item, +85602 BYTE slot, +85603 BYTE1. Cursor mode at
   UI+232F36 becomes7. No26 is queued at this stage, and inventory is unchanged.
2. `00466490(-12,3,this=world)` resolves the self actor and calls `004964D0`.
   Both return normally. Native `004132E0` queues exactly seven logical bytes:
   `26 target:u16 item:u16 slot:u8 opaque_tail:u8`. For the initialized self4,
   significant prefixes are `26 04 00 1D 0C 05` and `26 04 00 23 0C 0C`.
   The last byte is uninitialized local residue, not quantity or a request ID.
3. `004AE520(shortcut0)` with kind0 reaches `004963C0` and directly queues self
   use. It scans bag29 down to0, comparing item WORD and **signed** count BYTE
   greater than0. Duplicate slot29 count1/127 wins; count0/128/255 is skipped
   and slot5/12 wins. All ten variants run the real shortcut dispatcher.
4. Shortcut target is the low WORD of `**(UI+8688C)`, copied unchanged.
   Values1,4,3FFF,4001,FFFF were preserved. This does not authorize spoofed
   targets: server admission must bind the target to its own session actor.
5. UI+866E4=1 suppresses output through both shortcut and target producers.

The inventory branch also checks an existing panel state at UI+232DFE bit20.
The flag04 branch is equipment; flag01+08 selects the target cursor for these
MED rows. `004964D0` has a different special-key15C6 route, not exercised or
authorized by this medicine result. General actor hit testing and physical
keyboard/mouse delivery are outside this emulator; the separate hidden-client
lane supplies that acceptance.

None of these producers decrements a stack, calculates healing, or establishes
server cap, revival, cooldown, battle-use, or God/pet target authority.

## Complete S2C41 + S2C24 and companion preservation

Every pair runs `004991E0` through return, then the actual world24 case from
`00469F4D` through its join `0046B517`. This executes `004E71E0`, `004E72D0`,
`004AC070`, and `004E6DB0`, with an active God pointer, two complete God records,
three pet slot records, and three pet cache records.

| Test input | HP before/after | MP before/after | Final stack |
|---|---:|---:|---:|
|3101, slot5|20 →120|2 →2|2|
|3101, slot5|119 →120|52 →52|1|
|3107, slot12|120 →120|2 →52|2|
|3107, slot12|120 →120|52 →80|0|

All use maxHP120/maxMP80. These supplied operands illustrate CUSTOM-0016;
the client receives results rather than deriving the server recovery rule.

S2C41 is `41 item:u16 slot:u8 count:u8`. With count0, native consumption clears
the item low WORD; remaining instance metadata stays unchanged. S2C24 is
`24 HP:u32 MP:u32 maxHP:u32 maxMP:u32`; role memory instead orders
HP/maxHP/MP/maxMP. Complete God3EC×2, selected pointer/count, pet slot24×3,
and pet cache72×3 are byte-identical before/after all four pairs.

A separate identical24 replay at HP120/MP80 leaves all those records, all50
inventory records, and role resources unchanged. This qualifies a neutral
consumer replay. **Cap no-op with no outbound records is a server policy**;
there is no native consumer invocation to emulate for an absent packet. The
runtime/TCP/hidden-client tests must check no debit, no revision/write, and
unchanged state on that path.

Counterexample: old roleHP100, newHP90, active GodHP37 produces GodHP27.
`004E71E0` subtracts positive player HP loss from selected God+2C, clamping at0,
before overwriting role resources. Thus these results do not bless stale/lower
24 snapshots. The server must maintain an ordered, coherent client baseline;
the qualified supply replies never lower HP. World24 passes mode0; mode6 has
a separate God update path and is not this contract.

`004AC070` also clamps role resources to maxima for client display and formats
the HUD. That local clamp is not evidence of original server debit or healing
rules. No damage/defense formula or God/pet healing rule was recovered here.

### Read-only current-client acceptance fields

- `role = *(UI+86888)`; HP/maxHP/MP/maxMP are four DWORDs at role+5C.
- `actor = *(UI+8688C)`; low WORD at actor is the producer target. Do not use
  role+0 as actor identity.
- Selected God pointer `*(role+D0)`, count BYTE at role+D4;
  God records `role+D8+i*3EC`, with HP/maxHP at record+2C/+30.
- Pet cache base `*(UI+232EBC)`; three72-byte entries.
- Inventory base UI+8560C, stride24; pet slots42..44.
- Pending target binding UI+85600..85603 and cursor mode UI+232F36.

These are observation locations, not instructions to modify client memory.

## Historical references and CUSTOM-0016 balance review

Consulted 2026-09-27; historical community content is not build-matched server
code. The [Bahamut8591 丹藥相關 table](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E4%B8%B9%E8%97%A5%E7%9B%B8%E9%97%9C)
independently lists 金創藥 HP100 and 順氣藥 MP50. Search-index text was readable;
direct retrieval returned403. No exact revision date was exposed. Its other
tiers include HP200/500/1000/2000 and MP100/200/300/500; these are cross-checks,
not additional grants or newly selected values. The retrieved table does not
establish cap behavior, living-only use, one-unit debit, or cooldowns.

The same game's [2008-07-16 recipe reference](https://forum.gamer.com.tw/G2.php?bsn=8395&sn=931)
lists the two medicines at crafting level1 with cost5, whereas the
[2006-05-05 recipe reference](https://forum.gamer.com.tw/G2.php?bsn=8395&sn=26)
lists cost10. This dated discrepancy is a reason not to import prices or
crafting rules into the current build. No such economy change is proposed.

The owner's [17173 仙界傳 portal](https://xjz.17173.com/) is historical mainland
release material; direct root retrieval timed out. A bounded exact-name search
did not recover a qualified player-medicine/cap table. The indexed
[pet guide](https://xjz.17173.com/senso/pet.htm) describes ordinary pet HP/MP
recovery by feeding, which is a distinct target domain. The
[crafting guide](https://xjz.17173.com/add2/add.htm) mentions medicine crafting
without proving player consumption/cap semantics. Page revision dates were
not exposed. Similar drug names in unrelated17173 game pages were excluded.

The retained CUSTOM-0016 choice is explicit: trusted saved living self actor,
`new = old + min(source recovery, max-old)` per resource; debit exactly one
only if either resource increases. Dead self and full relevant resources are
no-ops. Current source values100/50 are unchanged. Self-only, no pending battle,
and no inferred God/pet use bound this integration. Revival, cooldowns,
equipment effects, and unknown targets remain outside the qualified policy.

Balance tradeoffs tested by the supplied operands are concrete: HP20→120
uses the full100; HP119→120 still costs one and wastes99. MP2→52 uses50;
MP52→80 uses28 and wastes22. Full capacity costs nothing, an intentional
CUSTOM deviation whose original-server equivalence is unknown. Fixed healing
also declines proportionally as saved maxima grow: HP100 is100%/10%/1% of
hypothetical max100/1000/10000, assuming enough missing HP. Those are scale
examples, not native player levels or granted stats.

Existing `tests/test_supply_lua.cpp` covers20,475 small-domain inputs, signed32
limits, zero maxMP, invalid inputs, dead/no-op and cap arithmetic; this lane
does not relabel those tests as economy or physical-client acceptance. Source
amounts, coherent cap behavior, no resource decrease and bounded waste are
reviewed here. Long-term price/access/cooldown balance and original server
debit authority remain unverified. Promotion status and actual-client success
must be reported separately by the integrating lane. Replacement should use
qualified original server evidence if recovered, preserving provenance.
