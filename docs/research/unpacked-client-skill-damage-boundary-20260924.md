# Unpacked client skill and damage boundary (2026-09-24)

The verified clean `God2.unpacked.exe` has SHA-256
`5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`.
Direct PE RVA-to-file comparisons show that its complete native ranges
`12D3B0..12D430`, `126120..126263`, `12CABA..12CB8E`, and
`128A70..128B0D` are byte-identical to the previously executed mapped
client image (`native-master-01-stable.bin`, SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`).
This binds the existing executable research to the actual unpacked file now
used to launch the game; the two files have different whole-file hashes because
one is a PE on disk and the other is a mapped image.

## Located paths

* Skill catalog loader: RVA `12D3B0` reads `Data2/Fight/Spg/cbspec2.bin`.
  The asset holds four banks and 448 populated 110-byte definitions. The
  original loader and its exact destination bytes pass the four read-only
  `test_current_skill_catalog_loader.py` tests.
* Skill effect text: RVA `126120..126263` reads 13 effect-presence WORDs
  at record offsets `4C..64`. It chooses attribute labels and prints a
  caller-supplied amount. Changing a nonzero WORD's magnitude does not
  change the printed amount. This is text formatting, not a damage multiplier.
* Battle result consumer: RVA `12CABA..12CB8E` reads a signed WORD from a
  received logical record at offset `+9` and accumulates/replaces a target
  delta according to selector. RVA `128A70..128B0D` then applies received
  deltas to two actor scalar channels. The seven read-only
  `test_current_damage_formula.py` tests pass against original instructions.

For either actor channel, the **received-value application** is:

```text
sum = (current + received_delta) modulo 2^32
if bit31(sum): next = 0
else if int32(sum) > int32(cap): next = cap
else: next = sum
```

This is not the attack/defense-to-damage formula. The client path above
consumes a value supplied in a battle result; it does not show how the sender
chose that value. The displayed MP fields, targeting mode, effect labels,
and this clamp cannot be promoted into damage, hit, critical, or five-element
coefficients. `recover_combat_rules --summary` currently reports 381 skill
books, 243 displayed MP costs, 1,202 card effects, 448 selection definitions,
and **zero recovered server formulas**; all five rule categories remain unknown.

## What is required next

Trace a real cast from the skill ID through the native C2S command and the
matching S2C battle-result amount, then identify the authoritative server
calculation or collect controlled damage observations while varying one stat
at a time. Verify stat inputs, modifier order, randomness, element rules,
rounding, minimum and cap before enabling a production damage rule.

No combat balance or production formula was changed by this investigation.
