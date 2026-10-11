# Native skill MP eligibility

## Newly qualified rule

Two original client predicates were executed to their real returns:

- RVA A9070..A90C1: current selected slot, signed selector byte at 5B6C79,
  page byte at menu+3E8, effective slot = 25 * page + selector.
- RVA A90D0..A910F: explicit signed slot argument, RET 4.

Both follow owner+86888 -> role, role+D0 -> skill menu, and menu+258+4*slot
-> definition. They return false for a missing menu, negative selection/index,
missing skill pointer, or definition BYTE+67 equal to zero. Otherwise:

```text
eligible = uint32(role.current_mp_at_64) >= uint16(definition.cost_at_42)
```

The native CMP/SBB/INC sequence uses unsigned comparison. Equality succeeds.
The BYTE+67 check is nonzero, not `== 1`. Its broader meaning is not assigned
from this predicate alone. A zero-cost definition with that byte zero remains
ineligible. No MP subtraction or other role/definition write occurs here.

Existing `current-battle-vitals-20260920.md` identifies role+64 as current MP
through original named-vitals consumers. The prior MP display consumer at
11BED3 reads this same definition WORD+42.

## Independent source agreement

The native book-binding artifact connects 381 original skill books to battle
definitions. Of these, 243 have an explicitly parsed MP-consumption description.
All 243 numbers equal the paired definition WORD+42; there are zero mismatches.
The other 138 lack that exact description label and are not assigned text
evidence by default. The binding's canonical row hash is checked against each
current original source row before joining.

Pinned inputs:

- Image: 149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763
- cbspec2: 7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51
- gamedata: 70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731

## Execution and bounds

No game callee, branch, comparison or return is replaced. Only original
instructions in the two bounded predicate spans may execute. The image is
read/execute; owner, role, menu and definition pages are read-only during native
execution. Only the private stack is writable. Full role/menu snapshots and
definition bytes must remain unchanged. Both return addresses and ABI stack
cleanup are checked.

The synthetic owner, role and menu are explicit live-in preconditions, not a
qualified full-client initialization. The harness stages 100 slots (four pages
of 25); this is a memory-bound safety restriction, not a native upper-bound
check. The inspected predicates reject negative indices but do not implement
the harness's positive index/page limits. An invalid role pointer is not passed
to native code and no native null-role safety is claimed.

Diagnostic DWORD values 80000000 and FFFFFFFF test unsigned semantics only;
they are not accepted gameplay MP ranges or production defaults. No global
memory-write hook is used, avoiding the earlier REP instrumentation issue.

## Tests and remaining work

`test_current_skill_mp_gate.py`: five methods passed, including all 448
definitions through both predicates at threshold-adjacent MP values, independent
BYTE+67 and WORD/DWORD boundaries, selected-page addressing, missing dependencies,
invalid harness inputs, and all 243 explicit description comparisons.

This qualifies client MP eligibility, not complete authoritative cast validation.
It does not establish learning/ownership, target legality, cooldown, resource
debit timing, refunds, discounts, or base damage/defense/critical arithmetic.
At the initial 2026-09-20 checkpoint, the C++/Lua implementation and database
were unchanged; no guessed formula was enabled and no retired server evidence
was used.

## Read-only catalog projection in the C++20 server (2026-09-23)

`NativeSkillRecord::client_mp_threshold()` now reads the little-endian WORD at
raw record+0x42 from the already pinned and imported `cbspec2` record. Lua
`native_skill_catalog(kind,id).client_mp_threshold` exposes that same value
with the existing source/record provenance. The field is `NATIVE_VERIFIED` for
the current client's eligibility comparison only. Lua `mp_cost`, damage and
multiplier remain absent; no server cast or resource rule changed, and no
database migration or account/save rewrite occurred.
For example, current source kind0/id1 has client threshold5, while the
existing CUSTOM-0012 diagnostic server skill spends8. The different numbers
are retained and labeled: client eligibility does not prove the original
server's debit rule, and the diagnostic cost is not presented as native.

The Release server, `native-skill-catalog` and `native-skill-lua` build. The
original-source import/reader suite passes14 tests, including comparison of
all448 returned C++ values to source WORD+0x42. The Application/Lua suite
passes on all448 original records and requires `mp_cost==nil` alongside the
new field. These checks prove byte-preserving data exposure through C++/Lua,
not the original server's actual debit amount or timing.

```powershell
python tests/research/test_current_skill_mp_gate.py
ctest --test-dir build -C Release -R current_skill_mp_gate --output-on-failure
```
