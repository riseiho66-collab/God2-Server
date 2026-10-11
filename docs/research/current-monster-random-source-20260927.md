# Current monster random-source frontier, 2026-09-27

## Scope and result

The current reconstruction contains 23 exported non-CRT functions referring to
`_rand`. A bounded raw direct-call scan of the original `.text` finds 50 E8
target candidates to VA `00547D7F`. These counts are neither spawn entries nor
proven active callers. This pass supplies no complete native monster spawn or
encounter rule. Indirect calls and other local encounter paths remain open.

Tool: `tools/strike_lab/current_monster_random_source_20260927.py`.
Receipts: `artifacts/research/monster-random-source-20260927/evidence.json` and
`evidence-optimized.json`. Both PASS, byte-identical SHA256
`fbf007a65e842e4722ca7616d864044f1da9c15ffc68452cf934e833c3da5cc2`.
No RNG, full world update, client process or production mutation is executed.

The pinned mapped image is `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`;
the current God2.exe is `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
The original `.text` has 64 byte differences from the current patched client;
all selected rand call bytes, nine lead function envelopes and three unexported
helper ranges match. The later `.imefix` section lies outside the original
image and is explicitly excluded, not mistaken for original game logic.

## Examined leads

* `00454210`: the rand branch chooses among existing resource-name strings
  when an `eny.csv` resource is unavailable. This branch supplies a filename,
  not a world spawn record. The loader's resource offsets cannot be coordinates.
* `00466B00`: under actor flag bit8, random parity negates requested movement
  offsets or changes the selected destination. The target enters
  `005024C0 -> 00502B90 -> 00502700 -> 00468950`, the movement/path and outgoing
  walking chain. These offsets are movement input, not new monster placement.
  This is a static matched-code trace, not a full execution of the world update
  or qualification of the status flag's original name.
* `004D7900 -> 004D7DB0`: random values 30..32 select an actor-local WORD+52;
  the setter bounds the selector below58. This inspected setter does not write
  a map ID, world position or monster identity. Its animation/state meaning
  needs its surrounding consumer; it is not an encounter distribution.
* `0047FC60`: values DC..E1 are randomized within that six-value range. Known
  callers read local UI/effect bytes; the value alone is not a spawn template.

## Previously unexported random callers

Two complete machine-code envelopes, `00474AB0..00474B8D` (72 instructions)
and `00475400..00475527` (93), respectively construct a `%04dtest` named record
and alter a selected 44-byte UI-list record through `00474DB0`/`00475630`.
The inspected callees use owner+41C24 list counts and owner+40B7C records;
they do not install the world monster pool. No raw E8/E9 incoming target was
found for these two entry points. This does not exclude computed calls.

`00411200..00411259` (42 instructions) produces distinct random WORD indices;
one raw incoming candidate is `004113ED`. Its gameplay authority remains
unqualified. The `0051A908` random call remains an unexported-parent lead;
only its call bytes are qualified here. Neither is silently classified as a
monster source or discarded as globally irrelevant.

The nearby `004CDBC8` call belongs to the already separately decoded
`004CDBC0` byte selector: DC maps to DC..E1, other bytes pass through. See
`current-npc-position-writers-20260927.md` and its additional-instruction
receipt. It has no identified active caller and is not a new spawn table.

## Reproduce

```powershell
python -m tools.strike_lab.current_monster_random_source_20260927 --output artifacts/research/monster-random-source-20260927/evidence.json
python -O -m tools.strike_lab.current_monster_random_source_20260927 --output artifacts/research/monster-random-source-20260927/evidence-optimized.json
```

Continue with the incoming source of S2C71 and S2C82, plus unresolved computed
callers/local trigger boundaries. A client's position consumer proves the
wire contract; it does not reconstruct coordinates the original server chose.
