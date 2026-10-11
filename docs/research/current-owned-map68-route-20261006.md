# C2S 68 owned regional-map display branch — 2026-10-06

The current mapped client image is SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The previously pinned native `wrapper-ui-context-static-v3.json` proves four
guarded calls to the wrapper that can queue logical `68 00`. Its selected
large-map row is `UI+232DA8`; the wrapper can also handle an event locally.
Current S2C `3F 01 00` enters `C3890`, which opens that existing large-map
panel. Both the C2S wrapper and this S2C consumer reject the same scene
`+F4 & 3 == 3` condition. This is compatible UI evidence, **not** proof that
the original server answered 68 with 3F. Same-number S2C68 is a separate
13-byte consumer at widget `UI+232DD8` and is not emitted here.

`CUSTOM-0087` now connects a bounded source branch under the existing
`owned_map_views_enabled` configuration:

1. The WORLD parser admits only exact native `68 00`; Application requires
   exactly one such request with idle ticks and at most one trailing 1F.
2. The session must be authenticated, have completed WORLD entry, be in a
   world state with a saved current position and projected owned bag, and have
   no battle reservation, trade, or pending scene transfer.
3. Only saved area2/scene4 item5569 or area4/scene3 item5576 can authorize
   this display. Application searches actual saved slots0..29 and reuses the
   existing source-qualified `RecoveredOwnedMapView::logical` check for item,
   count1, revision, catalog/source bytes, and exact current map row.
4. A qualifying request emits native `3F 01 00` in a world frame. It changes
   no inventory, resource, quest, battle, or saved state. This display-only
   route needs no Lua gameplay calculation.

The handler never treats a client byte as an item grant or uses S2C68 as a
reply. The original 68 request/reply rule, all other map contexts and the
current client's acceptance of this new CUSTOM pairing remain open. The
branch is source-only: no build, test, original-client run, deployment, or
formal service/database change was performed in this connection phase.
