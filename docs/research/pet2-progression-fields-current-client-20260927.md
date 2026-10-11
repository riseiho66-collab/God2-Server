# Current pet2 progression fields — 2026-09-27

## Integrated contract

`RecoveredPet2Stats::Record` now exposes the level, packed current/maximum
HP/MP, star rank and star rating in the existing owned FB snapshot route.
The repository still retains all 73 logical bytes; restore and slot transfer
alter only the routing slot. No migration, invented stats or growth award is
introduced. The decoder in `recovered_packet_pipeline.py` exposes the same
fields for packet diagnostics.

Evidence uses the pinned mapped image SHA
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
and the original `Data3/Flow/petegg.romZ` label background. The decoded asset
was inspected directly, without a desktop screenshot. Its descriptors and
original instructions are checked by `current_pet2_stat_labels.audit()`.

| Field | Body offset | Native extraction | Consumer RVA / control |
| --- | --- | --- | --- |
| Current HP | 4 | DWORD & 0x3FFF | A41D7 / 1 |
| Current MP | 4 | (DWORD >> 14) & 0x7FF | A4201 / 2 |
| Maximum HP | 12 | DWORD & 0x3FFF | A422E / 3 |
| Maximum MP | 12 | (DWORD >> 14) & 0x7FF | A4258 / 4 |
| Level | 3 | unsigned BYTE, no clamp | A4288 / 5 |
| Star rank 星階 | 8 | DWORD >> 28 | A45C7 / 17 |
| Star rating 星等 | 8 | (DWORD >> 24) & 0xF | A45EE / 18 |

Offsets exclude the FB opcode. Progress remains the separate low24 value of
body+8, interpreted by the original percentage formatter; no accumulated EXP
or next-level requirement is inferred. Current values above maxima are retained
because these are decode-only accessors, not evidence of an original clamp.

## Verification and own-server acceptance

- `test_current_pet2_stats_codec`: 4 tests PASS, including 256 diagnostic
  combinations against unchanged original receiver/panel instruction slices.
  Covers every unsigned level byte, all 16x16 star combinations, all three
  slots and packed HP/MP boundary noise. Original formatter is the existing
  stop-before-call boundary, not a claimed full rendered frame.
- `test_current_pet2_stat_labels`: PASS, seven additional packed-field bindings.
- Rebuilt `owned_companions`: PASS, SQLite load/transfer retains level255,
  packed extrema and star nibbles. These operands are synthetic test values.
- Rebuilt candidate, hidden desktop run
  `artifacts/playtests/private-pet-progression-20260927-01`: PASS. Original
  client restores two synthetic owned instances, then reserve42→active44,
  reserve43/active44 swap and active44→empty42. Each committed snapshot equals
  the read-only native cache. Test levels37/98 and star pairs10/5,5/10 persist.
  HP50/100, MP20/40 and percentage0 are unchanged. User desktop stays selected;
  source fixture DB, live client and port-only private client hashes unchanged.
- Accepted candidate is archived in the Bahamut research directory; reproducible
  receipt verification: `python -X utf8 -B -m
  tools.strike_lab.verify_pet2_progression_acceptance_20260927`.

## Next growth dependency

Star rank/rating are not automatically Bahamut A/B/C/D growth classes. Original
panel RVA A4525 reads body+2C low nibble and body+3C byte, calls 5C9E0 to
validate the pair and 5CA00 to select a CategoryDetailNum name for control16
型態. The getter permits group1..29 and index0..15. The independently decoded
current table includes names 體力A, 力速A, 智速A etc.; this does not establish
a join to the general-map first-generation species/普/頂/晚破/破頂 rows.
Next work must qualify that selector path and species/generation association
before choosing a growth rule. The current creature's FB receive/display values
also do not recover wild-monster attributes or original server growth formulas.

Production binary/PID14720 at localhost2592 was kept running. Production
pet-growth activation remains 0%; native packed-field interface and the three
isolated live transfer stages are qualified. Whole-game completion is unproven.

Later same-day follow-up: the native category selector/name path was qualified,
464 names and1165 NCP definitions were formally promoted with player-state
preservation. Schema36, new service PID19256; growth formula remains disabled.
See `native-pet2-categories-current-client-20260927.md` for the current release.
