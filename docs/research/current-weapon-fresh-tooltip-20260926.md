# Current WPN1/2 fresh tooltip: complete native formatter return

Date: 2026-09-26. This is a bounded follow-up to the equipment projection oracle,
which previously used an exact tooltip-cache hit. No client process, desktop,
production database, server runtime source or shared build configuration was
modified. Original item generation, ownership, legal enhancement and combat
formulas are not inferred from tooltip acceptance.

## Result

New tool: `tools/strike_lab/current_weapon_fresh_tooltip_20260926.py`.
New regression: `tests/research/test_current_weapon_fresh_tooltip.py`.

**12 cases PASS in normal and optimized Python, identical JSON results:**
WPN1/2 × slot0/1/34 × fresh hover(event0)/double-click(event4).

Each case deliberately starts with a different cache key and different20bytes.
It runs current49A330 through its actual return, including49B820→4B5BE0,
4B4DD0,4B4060,4B45B0→4B4200, original CRT formatters, tooltip positioning and
native widget-open routines. There are zero game callee stubs, no patched game
instructions and no premature stop reported as success. Double-click additionally
runs native guard→96550→132E0 and emits the exact five-byte C2S28. Hover emits
no request. Neither operation mutates inventory before the server response.

The tooltip widget exists and opens, with a deliberately absent renderer
handleFFFF. Native5077C0 still executes its original formatter, and the oracle
captures its completed CP950 text at507822, immediately after the formatter
returns. The main weapon summary is captured only after4B4200 returns.
**Final font drawing/blit and real-client graphical acceptance are not tested.**
The prior oracle's original WPN icon resource binding is reused independently.

```powershell
python -X utf8 -B -m tools.strike_lab.current_weapon_fresh_tooltip_20260926
python -O -X utf8 -B -m tools.strike_lab.current_weapon_fresh_tooltip_20260926
python -X utf8 -B -m unittest discover -s tests/research -p test_current_weapon_fresh_tooltip.py -v
```

Every mandatory gate uses explicit exceptions, so optimization cannot erase
the checks. The tool prints a result only after the complete matrix passes;
failed runs create no persistent PASS report.

## Exact tested instances and original output

These are **CUSTOM_TEST_NOT_NATIVE** synthetic input bytes suitable for the
next isolated own-server acceptance test. They are not native-generated items.
Unknown fields are explicitly zero in this test design, not certified native
defaults or an instruction to rewrite saved player instances.

| Key | Synthetic20byte instance | Exact native name text | Source level text |
|---|---|---|---|
| 1 | `0100010000000018000000000600000000000000` | `(+0)菜刀` | `等級限定(1級)` |
| 2 | `020001000000001e000000000a00000000000000` | `(+0)砍刀` | `等級限定(10級)` |

Correction to the earlier projection report: WPN2 CP950 bytes `ace5a44d` mean
**砍刀**, not 柴刀. The earlier numeric item and ROM action bindings remain the
same. Use source bytes when constructing fixture labels.

First DWORD is key plus highWORD0001. The native fresh tooltip switches on
`(instanceDWORD0 >> 16) & 0x3F`; value1 selects the ordinary weapon branch and
4B45B0. This is separate from the double-click request decision:49A330 obtains
the source definition by lowWORD key and uses definition+11A bit04 to select28.
WPN1/2 source definitions have flags F4/02. A successful request does not itself
validate the highWORD or other instance fields.

In these test instances byte7 is24/30 and byte12 is6/10. Native4B45B0 unpacks
the input and4B4200 formats the following exact strings, including color commands:

```text
WPN1:
/c6品質:+0
能力總和
物攻:+19 ~ +29
魔攻:+3 ~ +9/c9

WPN2:
/c6品質:+0
能力總和
物攻:+25 ~ +35
魔攻:+7 ~ +13/c9
```

Thus the formatter displays ranges, not the raw24/6 or30/10 as a final combat
result. These observed ranges are not a damage formula. The six packed display
values, quality extraction and source level interpretation have separate prior
coverage in `current_weapon_attributes_native_20260926.py`; this lane adds the
previously missing complete fresh tooltip/formatter continuation.

## Source qualification

- Current PE SHA256:
  `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Current gamedata source SHA256:
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
  Original WPN parser rows1/2 are lines4804/4805. Its permitted code ranges
  are compared to the current PE before using the original parser.
- `Data2/Patch/Comm/message.csvZ` compressed SHA256:
  `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`.
- Message decoded SHA256:
  `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.

All1080 current ProgramMsg entries are loaded as exact CP950 source bytes into
the native lookup layout. Empty entries9/497/886 remain empty. This fixture
does not substitute fake labels, null message pointers or hand-written text
formatting. The original compiled CRT executes the actual format strings.

## Read-only physical hover acceptance for the main lane

Use these offsets without injecting memory into the client. Validate handles
and pointers before reading. Offsets below are hexadecimal unless noted.

1. The owned instance is20bytes at `UI+85610+24decimal*slot`; count is at
   `UI+8560C+24decimal*slot`. Weapon34 instance begins `UI+85940`.
2. Before hovering the target, record cache key `WORD(VA005B7830)` and
  20bytes at `VA005B7838`. Hover a different actual item first if necessary to
   prove the target operation cannot take the cache-hit return.
3. After real mouse movement, bounded-poll for cache key and20bytes matching
   the target. Inventory wrapper tooltip type is `WORD(VA005926B0)==12h`;
   cache x/y are WORDs at VA005926B2/B4. No special fixed delay was established
   by this lane; use observed state changes rather than treating sleep as proof.
4. Tooltip panel is `int16(UI+232E56)`. With `W=UI+E2170`, node is
   `W+818+panel*2A08`; WORD(node)&20 means open; WORD(node+4) is its renderer
   handle. Unlike this offline fixture, the live client must have a usable
   renderer before claiming graphical acceptance. Cache match alone is not
   proof of the fresh rendered text.
5. For inventory icons, read the inventory panel `int16(UI+232DC8)` and its
   render handle; `R=DWORD(W+8)`, object=`R+10+handle*290`. Per-slot action WORD
   is object+180+2*slot, sprite handle WORD is object+AC+2*slot. With
   `S=DWORD(R+4)`, sprite=`S+1258+spriteHandle*C8`, its image pointer is+8C.
   Compare against source-backed definition group/action at+116/+118;
   WPN1/2 loaded bindings are group41h, action0/1.
6. After real double-click, verify the emitted28 key/source/flag1 and later
   server after-state. `DWORD(UI+85608)` is pending; ordinary equipment3B
   clears it after the native audio call, while uninstall to empty34 retains1.
   The previous complete projection oracle proves retained1 does not block
   the next tested weapon request. Do not fabricate an occupied equipment
   reply to clear this field.

The main fixture can now use the two explicitly labeled byte vectors and verify
fresh physical hover before equip/swap/unequip/re-equip. Actual-client font and
resource acceptance remains with that isolated client lane. No new source-backed
weapon-to-DA appearance selector was established here; DA mapping remains a
separate evidence requirement and must not be inferred from tooltip class1,
item ID1/2 or icon action0/1.
