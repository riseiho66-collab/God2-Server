# Skill Formula Investigation: Numeric Effect Fields

## Executed Result

Original126120..126262 was executed through its real RET0C, including original
CRT sprintf147AF7, for all448 current cbspec2 definitions. The13 WORDs at
record+4C,+4E,...,+64 are tested for zero. For each nonzero WORD the routine
appends a corresponding attribute label and the SAME signed caller amount.
It does not multiply by the WORD or derive the amount from actor attack/defense.

In order, the original CP950 labels identify metal, wood, earth, water, fire,
strength (label uses wrist), constitution, intelligence, speed, physical attack,
physical defense, magical attack and magical defense. They describe this text
consumer only, not a complete authoritative server skill effect specification.

The file and image are hash-pinned using the existing current-only identities:

- cbspec2.bin:7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51
- native image:149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763

No retired archive or inferred coefficient is used. Image is read/execute;
all executed code must stay in126120..126263 or original CRT147000..16F000.
Only private stack and bounded output writes are allowed. Source record and
output canaries are checked. No game function or formatter is stubbed.

## Counterfactuals

All448 actual records use a diagnostic amount-37; expected output and every
formatter argument are checked. Actual record reads must be exactly13 WORD
reads at4C..64, including fields whose value is zero. A further325 cases vary
each field independently over1,2,100,32768,65535 and the caller amount over
-32768,-1,0,1,32767. Changing nonzero field magnitude does not change output.
All-zero flags produce an empty string. Invalid record lengths/types and
non-integer/out-of-range signed-WORD inputs are rejected before native entry.

Local unittest result:3 methods passed in11.673 seconds. These are effect-text
consumer tests, NOT448 recovered damage formulas or live-client acceptance.

## Static Upstream Evidence

Addresses are RVAs, base400000, mapped file offset=RVA. This section is static
disassembly evidence, not a continuous executed receive-to-display claim.

- 125866 loads actor+EC4 (selected skill definition).
- 125874 sign-extends actor+28A, then125884 passes it to126120.
- 12B60D obtains an explicit stack argument;12B619 stores its low WORD into
  actor+28A+2*actor[239]. There is no coefficient multiplication in this store.
- 12C845 loads a WORD from received-record pointer+8;12C855 pushes it as the
  fifth argument for12B060 at12C860. That is the stack+60 operand after the
  callee's3C-byte locals and four saved registers. The full intervening branch
  path to12B619 remains unexecuted; this is a candidate source edge, not a
  newly certified wire opcode/length contract.

Separately11BED3 reads definition WORD+42 into the `%s MP=%d` formatter argument.
That identifies an MP display value at this consumer, not a debit/affordability
rule or proof of damage magnitude.

## Independent Hit/Critical Review

A read-only bounded review of previously unexecuted02F570 found coordinate
differences, a24-step scale, rounding and float stores used by motion at123088/
123093. The pinned span02F570..02F660 hash is
a339f94c2086636422d8db43f08f2131a8d5fefe57fd716c2b82a6c4480f3551.
It is not promoted as a hit probability or critical multiplier. This was a
static review, not a new executable test. The reviewing subagent was closed.

## Still Unresolved

Attack/defense-to-damage, skill damage coefficients, hit/crit probabilities,
element interaction, rounding order and authoritative effect-duration rules
remain unverified. This investigation rules out treating these particular
display-consumed values as magnitude coefficients; it does not prove that
formula-producing code/data is absent from the entire client.
No production Lua/C++ combat rule or database value was changed.
