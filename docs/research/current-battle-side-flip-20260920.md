# Current Battle Side Flip Probe

## Question and Bounded Result

Can moving an enemy actor onto the allied side expose original monster values?
The current native update code does have side-dependent field availability.
The first diagnostic probe confirms a useful branch difference, but NOT original
monster base-stat recovery or a complete recruitment/ownership conversion.

Using the pinned current image (SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`), the test runs
the original `114332` dispatcher on the same VM and same 4096-byte actor:

1. Logical `86/1`, position14..27 (side1), returns to original `1144A6` without
   actor lookup or writes.
2. The harness explicitly moves the SAME actor pointer to the corresponding
   slot0..13 (side0), clearing the old lookup slot. The actor bytes do not change.
   This is a diagnostic input change, not execution of a native capture path.
3. The same packet payload, with only the position changed, now executes
   original `1173A0 -> 12D970` and two real `11E6E0` lookups. It writes packet
   DWORD+9 to actor+DEC and packet DWORD+5 to actor+DF4.
4. A second update with different explicit values changes those same two fields
   to the new payload values. Every other actor byte stays identical. The code
   image remains byte-for-byte unchanged.

All 14 paired slots are tested. Explicit invalid display handle `-1` and local
marker `-1` select genuine no-display/no-local-callback native branches. No
callee return is fabricated. Numeric values are diagnostic patterns, not monster
HP/MP measurements; untouched fields retain poison rather than guessed defaults.

## What This Establishes

Changing side can expose a receiver branch that the opposing side does not use.
For this exact subtype it does not compute or retrieve hidden original numbers:
the two admitted fields still come directly from the supplied server packet.
The experiment is useful for field discovery, not an original-data source.

This does NOT rule out additional information in other original spawn, capture,
companion, local-character or property-panel paths. Those must be investigated
separately with source-owned inputs. In particular, retained wild stats, newly
generated captured-pet stats and attributes computed from pet growth data must
not be conflated. No side0 label alone certifies wild-monster stat provenance.

## Reproduction

```powershell
python -B tests/research/test_current_battle_scalar_result.py -v
```

Nine tests pass in2.018s, including the new same-actor side-flip test over all14
paired positions. The test is part of the existing registered scalar CTest suite.
Registered scalar and side1 suites pass9/9 and19/19 in2.14s and2.65s; the
combined run including the21-test battle bootstrap passes3/3 suites in153.13s.
No live UI, official server, current private server or database mutation is used.
