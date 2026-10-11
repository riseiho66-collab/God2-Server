# MP update versus skill debit

## New retained-state execution

`NativeSkillMpSync` keeps the same role, menu, skill definition and native VM
between the following explicitly separate stages:

1. Run original A9070 or A90D0 skill eligibility predicate to its real return.
2. Enter logical S2C2B dispatch at 69EB0, execute its real E6390 call, and stop
   at E63C5 before UI refresh and companion continuation.
3. Run the same original eligibility predicate twice against the retained role.

The receive stage executes these original writes:

| Logical packet offset | Destination | Store RVA |
| --- | --- | --- |
| 1 DWORD | role+5C (current HP) | E639F |
| 9 DWORD | role+64 (current MP) | E63AB |
| 17 WORD | role+58 (not renamed here) | E63B8 |

The MP write is an absolute replacement, not `old_mp - skill_cost`. For a
diagnostic cost 50 and prior MP 100, a received value 80 produces MP 80, not
50. Repeated eligibility checks do not debit it. Values 50 and 49 respectively
pass and fail the cost gate when definition+67 is nonzero.

The test covers all 448 original definitions through both predicates, with
received values at cost, just below cost, and above cost. The skill and menu
are not rebuilt between receive and recheck. Whole-role snapshots verify the
three expected receive writes and absence of predicate mutation. Packet input
and all other input pages are read-only; role write access is enabled only for
the bounded receive stage and restored in a finally block.

## Strict boundary

These are offline original instructions with explicit staged preconditions.
No network session, player skill click, animation, transport decryption, or
entire client receive function is claimed. The E63C5 stop is before refresh;
the following eligibility entry is a new invocation, not a fabricated return
from an omitted UI callee. Invalid logical opcode/size is rejected by the
harness, not asserted as an original malformed-packet safety check.

This proves when this particular client state changes relative to the tested
receive event. It does NOT prove when the original server charges MP, whether
it charges rejected/interrupted casts, or whether discounts/refunds apply.
The injected MP values are diagnostic inputs, not captured official decisions.

The prior 83/0D result path also applies received signed amounts through the
128AC0 MP accumulator/clamp. Static direct-call inspection additionally finds
128E53 and 12BF3B calling that helper with stored action/accumulator amounts.
Those additional paths are not executed by this new test and do not establish
that an amount was computed from a skill cost.

Current image SHA256:
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
The same pinned cbspec2 definitions as current-skill-mp-gate are used. No legacy
archive, production database, C++/Lua gameplay rule or official network is used.

## Verification

```powershell
python tests/research/test_current_skill_mp_sync.py
ctest --test-dir build -C Release -R "current_skill_mp_(gate|sync)" --output-on-failure
```

Three tests cover retained-state transitions, diagnostic absolute-value updates,
and malformed fixture rejection. This is not completion of authoritative MP
charging or damage/defense/critical formulas.
