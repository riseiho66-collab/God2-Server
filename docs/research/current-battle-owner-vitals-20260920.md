# Retained Owner Vitals Consumer

Current image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are hexadecimal RVAs; file offset=RVA, base400000.

## Source and Consumer

The toolbar fixture retains E72D0 with character+90 as its first argument.
Its AC070 callee reads current/maximal HP and MP at argument+5C/+60/+64/+68.
These are character-root+EC/+F0/+F4/+F8, not four attack/defense fields.

Two explicit diagnostic logical records supply those bytes via original code:

- S2C22,25 bytes: existing69EF0 -> E6B40 writer stage supplies maxima from
  logical offsets17 and21 into source+60/+68, alongside its other known stores.
- S2C2B,21 bytes:69EB0 -> E6390 writes logical offsets1 and9 into source+5C/+64,
  and the WORD at17 into source+58. It stops at E63C5, before refresh E63F0
  and the separate companion update AA3F0. Unused record bytes are not promoted
  into additional recovered role fields.

The dedicated writer scratch context is restored before resuming the pending
main call. Whole-character snapshots must match the accumulated native writes.
No received live packet, account data or original monster record is claimed.

## Integration Probe

`test_current_battle_owner_vitals.py` reuses the actual toolbar continuation and
executes its previous assertions. Diagnostic HP/MP current values120/60 exceed
maxima100/50, intentionally exercising both unsigned clamps instead of taking
the zero-maximum early return. Original AC070 is expected to call1060F0 twice
and105680 twice, then return through E72E4 to B129A, ESP=SP-7C.

Writes are bounded to existing UI objects and the two current-value DWORDs;
the complete character, owner, mouse, display and separate battle-renderer
snapshots are reconstructed from the write trace. Native map records must remain
unchanged. The original1112C0 invocation remains a single invocation. Repeating
the completed continuation is rejected. `character_prepared` retains the
pre-consumer packet-written snapshot so that clamp mutations remain observable.

## Limits

These are offline native executions with explicit synthetic record operands and
the existing bounded OS/graphics adapters. They do not establish visible client
rendering, network acceptance, battle completion, monster maxima, damage rules,
or growth formulas. No production C++/Lua policy, runtime emission or DB data is
changed. Full B0D20 and the enclosing initializer still require continuation.

```text
ctest --test-dir build -C Release -R '^current_battle_(character_binding|owner_vitals)$' --output-on-failure
```
