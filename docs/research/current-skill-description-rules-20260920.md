# Current skill description rule evidence

## Scope

Current-client SKB descriptions only. No retired server archive is opened.
These are source-authored claims, not proven runtime equations. The exporter
does not alter the C++/Lua server, database, or existing skill catalog.

Source: `Data2/Patch/Comm/gamedata.csvZ`.
SHA256: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
All 381 book records are scanned; 61 description fields match the documented
damage/hit/critical/probability/multiplier search terms. This is NOT a count of
recovered formulas or all relevant gameplay rules.

The generated JSON retains the full raw record, CP950 description context,
record hash, decoded byte offset, line, and zero-based column for each entry.
Reviewed annotations are selected by item ID against this hash-pinned source.
Unannotated matching descriptions remain visible rather than being discarded.

## Concrete conditional claims

- Books 6567 and 6663: one own martial/talisman attack damage x2 respectively.
- Books 6568-6570, 6572-6574 and 6665-6669: described family critical damage x2;
  the probability of triggering that critical is not numerically specified.
- Book 6571 distinguishes axe 1-4 protection/random doubled defenses from
  axe 5 counterattack guaranteed critical after being attacked and hit.
- Book 6575 (bow master) gives no numerical damage multiplier. Do not infer x2.
- Book 6871: party deity summon recovery x5 in ordinary scenes, not all healing.
- Book 6884: guaranteed status hit is conditional on enhancement proc and no
  immunity. This does not establish a 100% proc rate or general hit formula.
- Book 6885: critical recovery x2, or critical damage x2 against undead.
- Book 6886: critical ability enhancement x2.
- Books 6890-6893 explicitly exclude the double-damage special ability.
- Books 6604, 6612, 6620, 6628, 6636 describe five rounds of wall damage;
  per-tick damage, scheduling, stacking, and rounding remain unknown.

Book 6873's "adds two times" and book 6573's "speed decreases 1.5 times"
remain ambiguous text, with no normalized factor. Book 6809 describes HP30%
for revival but does not establish the calculation basis or rounding.

## Promotion boundary

All entries retain `authority=description_only`, `executable=false`, and a
null runtime skill identity. The 381 book IDs are not silently joined to the
448 runtime definitions by names. Base damage, defense mitigation, hit/crit
probabilities, rounding, stacking order, identity mapping and execution agreement
still need evidence. Finding a documented conditional multiplier does not
recover the inputs it multiplies.

Follow-up: `current-skill-book-binding-20260920.md` qualifies the original
A8E10 metadata lookup and links all 61 entries to native skill identities in a
separate binding artifact. This text-only ledger intentionally retains its
original null identity and disabled execution fields. The binding does not
resolve base damage, proc rates, rounding, stacking, or runtime formula agreement.

## Reproduction

```powershell
python -m tools.strike_lab.current_skill_description_rules --output artifacts/research/current-skill-description-rules-20260920.json
python tests/research/test_current_skill_description_rules.py
```

Five tests cover provenance/full scan, conditional damage factors and exclusions,
conditional guarantees, ambiguity/durations, and disabled runtime promotion.
