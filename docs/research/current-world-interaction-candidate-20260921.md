# World Interaction Producer Candidate

## Scope

Pinned current image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
RVA equals mapped image offset; image base400000. No retired data is an
authority. This investigation follows world input toward NPC dialogue, but
does NOT establish that opcode6E is an NPC dialogue request. No production
codec, handler, world placement, quest identity or reward is enabled.

## Executed Producer

Original 97D40 reads argument2 as a signed32-bit value. Negative values
return without appending. Nonnegative values append opcode6E and eight
payload bytes through original132E0. Logical record layout:

| Offset | Width | Observed source |
| --- | --- | --- |
| 0 | 1 | 6E |
| 1 | 1 | Low byte of argument1 |
| 2..4 | 3 | Uninitialized native stack residue |
| 5..8 | 4 | Argument2, little endian |

Original ret8 balances both arguments. Twelve executed cases cover target
0,1,12345678,7FFFFFFF,80000000,FFFFFFFF with two poisoned stack patterns.
Five additional cases prove argument1 narrowing. Actual queue append runs
without substituted game functions; UI/queue/stack/arguments are synthetic.
The native image stays read/execute and execution is instruction-bounded.
No real client, socket or input event is exercised by this oracle.

## Caller Evidence and Remaining Meaning

Decoded direct calls at66274,66642,7B738,1130A8 target97D40. The first two
pass selector1 with a selected target. 1130A8 passes selector2/target0,
so treating every6E as NPC talk is already unjustified. Branch66229 selects
the first nonnegative entry in the order offsets4,8,0,C, calls FAC70 on
world+15383410, then passes its selected value to97D40. FAC70 performs a
FC960 lookup and copies three strings from a stride616 object. These are
instruction observations, not proof that the object is a quest NPC.

Do not interpret stack residue as zero padding, authentication or quest ID.
Do not install an arbitrary6E->7A response to hide the unidentified branch.
Next concrete step: trace the action selector into66229/66639 and identify
its target registry against the known NPC pool and world input dispatch.
Native actor identity/range/eligibility and the actual NPC-talk request are
still open. Existing qualified85 remains dialogue response only.

## Reproduction

`python -B -m tools.strike_lab.current_world_interaction_request`

`ctest --test-dir build -C Release -R current_quest_variable_length --output-on-failure`

The report goes to stdout; it does not overwrite runtime evidence. Tests
include the existing quest dialogue real-run regressions. Producer success
is not quest gameplay or normal UI acceptance.

## Follow-up: Role Pool, Not the NPC Pool

The existing current-image identity-cache proof identifies world+15383410
as the role pool (FC960 lookup,616-byte stride), distinct from the two NPC
pools world+1539AED8/153B8758 (472-byte stride). 65FA0 adds24 to its signed
action argument and dispatches via6643C; action-17 selects66229 and6E.
This excludes that selected-target path as evidence of NPC talk. It does not
classify every possible use of6E. The actual first-NPC-pool branch66D75
leads instead to96750/opcode37; see current-npc-interaction-20260921.md.
