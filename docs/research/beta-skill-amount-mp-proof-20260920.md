# Beta Skill Amount And MP Evidence

## Result

Continued beyond the restored image and static packet table: 333 real beta skill
definitions passed 3330 original action-prefix runs, 60 original stat-text gate
runs and 2850 original MP eligibility runs. Five regression tests passed.
These are distinct bounded claims, not proof of complete gameplay or original
monster base stats, damage formulas, critical chance, or MP debit timing.

Inputs remain read-only. No production data, gameplay formulas, current client
decoder, or original client files were modified. The helper agent was closed.

## Pins And Reproduction

- Beta mapped image SHA256:
  `ef373960e2cf455916110f81eaff3935c1d950a46ff7de7b4ef562b01a56405f`.
- Beta `Data2/Fight/Spg/cbspec2.bin` SHA256:
  `df6c7ab8ad6a83011a4055e7d9572240e0a366792a09158dd0d9cc56726c45f8`.
- Output: `artifacts/research/beta-unpack-20260920/skill-amount-probe.json`.
- Code addresses below are beta RVAs, base `400000`; other offsets are labeled.

```powershell
python -B -m tools.strike_lab.beta_skill_amount_probe
python -B -m unittest discover -s tests/research -p test_beta_skill_amount_probe.py -v
```

## Packet Amount To Actor

Static provenance: beta logical opcode `80` has length-function result 17 and
dispatches to `C8CD0`. At `C8DB3`, the receiver sets the action pointer to packet
plus one. It retains this pointer at stack `+2C`, retrieves it at `C90A9`, and
passes it at `C90D7..C90DE` to `DCD30`. The original receiver has additional
selection/preparation behavior, including group-specific target choices; it is
not executed end to end in this probe.

Native execution starts at `DCD30` with a staged action pointer and valid
source/target arguments. For action 3, the original code binds the actual
108-byte definition through `DCFE8`, executes original state preparation
`DB200`, reads WORD action `+E` at `DD05C`, and calls `DB940` at `DD077`.
Original lookup `CF200` and helper `D2F80` also execute without replacements.
`DBA59` writes that supplied WORD into source actor `+26C + index*2`.
Execution stops at `DBA61`, immediately after this store and before presentation.

Thus action `+E` corresponds to logical packet `+15`, including the opcode.
All 333 definitions were tested against WORDs 0, 1, 32767, 32768, 65535, at
source side/slot 0/0 and 1/13: 3330 passing runs. Both actor sides are exercised,
not every slot. The stored WORD always equals the injected logical WORD and
the skill pointer matches the exact source record. Definition bytes stay intact.

This proves unchanged supplied-amount propagation on this action branch. It
does not prove that every packet path lacks computation or that these diagnostic
values ever came from an official server. Group/target arguments are deliberately
staged for isolation and are not an assertion of legal live targeting.

## Dual Attack/Defense Text Gates

Original `D6BE0..D6D20` is executed separately. Only the CRT formatter call is
intercepted, recording its original format pointer and argument instead of
rendering text. Diagnostic records enable one WORD at a time:

| Record WORD | Original test | Format pointer RVA |
| --- | --- | --- |
| 5E | D6CC1 | 154B58 |
| 60 | D6CD8 | 154B48 |
| 62 | D6CEF | 154B38 |
| 64 | D6D06 | 154B28 |

For each field, values 0, 1, 65535 were crossed with supplied signed amounts
-32768, -1, 0, 1, 32767. All 60 cases pass: zero suppresses the format call;
either nonzero value produces one call with the same supplied amount. Therefore
these four WORDs are gates in this consumer, not multipliers or base stats here.
Static caller `D634A` sign-extends the actor WORD `+26C` before calling `D6BE0`.
The caller's entire presentation path was not executed.

## Native MP Eligibility

Two complete predicate functions are executed: `84500` (selected/page entry)
and `84560` (indexed entry). With a valid staged role, menu and skill pointer,
index/page zero, both compute:

```text
eligible = (skill.byte_67 != 0) AND
           (role.DWORD_64 >= unsigned(skill.WORD_42))
```

The comparison is unsigned. WORD `+42` is independently labeled by the native
`%s MP=%d` consumer documented in the prior report. BYTE `+67` is a necessary
nonzero eligibility condition; no broader meaning is assigned to that flag.

All 333 real definitions were tested with distinct values from {0, cost-1
clamped at zero, cost, cost+1, UINT32_MAX}, through both entries: 2850 runs.
Role and menu snapshots remain unchanged. These functions do not debit MP.
The current client's prior predicate must not be silently substituted for this
beta predicate, which includes its own explicit `+67` gate.

## Additional Static Search

Pointer-led analysis from actor `+E98` and `+DCC` found category/ID dispatch,
target-mode byte `+45`, signed byte `+66`, and the qualified display path.
No additional requested WORD consumer qualified as a damage formula in this
bounded sweep. A WORD `+60` candidate at `BC3E9` is relative to a different row
base (actual row field `+48`); a supposed `+62` access at `C8C7D` lies in table
data. Neither is accepted as a skill or monster stat operation.

This was not exhaustive alias analysis. The alternate pointer banks populated
at `CD0F3`/`CD279`, MP state-update producers, and further packet consumers
remain independent targets. No unknown monster value was filled with a default.
