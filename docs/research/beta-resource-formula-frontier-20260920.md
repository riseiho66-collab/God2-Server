# Beta Resource Formula Frontier

## Result

The continuing official-combat-formula search qualified two MP synchronization
writers and one conditional resource clamp. It did not establish an official
damage, defense, critical-hit or MP-debit formula. No custom rule was promoted
and no production database or original client was modified.

Input image SHA256:
`ef373960e2cf455916110f81eaff3935c1d950a46ff7de7b4ef562b01a56405f`.
All code locations below are beta RVAs, mapped base `400000`.

## Executed Writers

`beta_resource_writers.py` executes original instructions with synthetic inputs
and stops at explicit boundaries before presentation calls. It supplies no
replacement implementation of the examined stores or comparisons.

| Entry | Source to role mapping | Stop before |
| --- | --- | --- |
| A7890 | input DWORD +0 -> role +5C; DWORD +8 -> role +64; WORD +10 -> role +58 | A78BC |
| A86B0 | input DWORD +0/+4/+8/+C -> role +5C/+64/+60/+68 | A86E6 |

Role pointer provenance is owner `+76BD0`, matching the independently qualified
MP predicate's read of role `+64`. Twelve cases, including unsigned high-bit
values and UINT32_MAX, verify exact MP copying rather than subtracting a cost.
Only MP copying is asserted by these tests; other stores are listed from static
instructions. These functions alone do not prove all resource writers are known.

Original `87340..87381` checks two nonzero maxima and a nonnegative UI handle.
If those gates pass, its unsigned comparisons implement:

```text
role[5C] = min(role[5C], role[60])
role[64] = min(role[64], role[68])
```

If either maximum is zero or owner WORD `+12068E` is negative, the function
branches to its exit before those stores. Forty native cases verify these gates
and clamps. This is a conditional synchronization/display behavior, not proof
of an authoritative server resource invariant or a skill debit.

## Division Candidate Excluded

After the clamp, `873A2/873C5` divide the current values by the maxima and
`873AF/873C9` multiply by the float at RVA `12CE80`, whose bytes decode to 100.0.
Subsequent calls use the UI handle, including `873E1 -> E02E0`.
This is a resource-ratio presentation path, not attack/defense damage arithmetic.
The ratio branch was inspected statically, not executed by the prefix tests.

An additional linear disassembly scan of `1000..12C000` did not find a direct
arithmetic memory destination at displacement +64 among sub/sbb/dec/add/inc/
imul/and/or/xor. This is a search heuristic only: aliases, alternate offsets,
register arithmetic and bulk copies remain outside that negative result.

## New Fifteen-Field Input Frontier

Main dispatch `63D28..63D3B` indexes table `65DA4` directly with the opcode.
Entry `29` selects `64BEA`, which advances the logical pointer by one and calls
`A7B00`. The original length thunk selected by table `12F4` returns 31.
Thus the caller supplies a 30-byte body, not an inferred arbitrary stat vector.

`A7B00..A7C08` is now executed with fifteen distinct WORD markers, all zeros,
and all 65535 values. Every field is copied unchanged. Input WORD indices map:

```text
0..3   -> role WORD 88, 8A, 8C, 8E
4..8   -> role DWORD 9C, A0, A4, A8, AC (zero extended)
9..14  -> role WORD B0, B2, 94, 92, 98, 96
```

No names are assigned by positional resemblance. Static display function
`A7C20` uses UI controls 19..1D for the five DWORD fields, `%d` at `140414`,
and window handle owner WORD `120632`. These controls must be joined to their
actual UI labels before declaring any field physical/magical attack/defense.
The separate explicit labels at `15414C/154144/15413C/154134` and renderer
tokens 1C..1F are NOT yet proven to identify these five controls.

Another caller `CAC0A..CAC0F` also advances an input pointer by one and calls
the updater. Its opcode and full context remain unresolved. The qualified
updater copies supplied fields; it does not calculate them from four attributes.

## Verification

```powershell
python -B -m tools.strike_lab.beta_resource_writers
python -B -m unittest discover -s tests/research -p 'test_beta*.py' -v
```

Result: 12 synchronization cases, 40 conditional-clamp cases, three 15-field
stat-copy cases, and all 14 beta
regression tests passed. JSON evidence is at
`artifacts/research/beta-unpack-20260920/resource-writers.json`.

The unresolved target remains a computation whose inputs are independently
identified attack/defense/skill parameters and whose output is a battle result.
Resource display math and unchanged server-supplied numbers do not meet that bar.
