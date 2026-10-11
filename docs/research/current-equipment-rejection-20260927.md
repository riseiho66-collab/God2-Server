# Current ordinary equipment refusal presentation — 2026-09-27

## Result and boundary

The current client accepts **S2C02 SystemMessage27** through its ordinary world
dispatcher. The pinned source text is `%s 無法使用或裝備。` (display mode 1).
This is a truthful generic rejection hint for a server-refused C2S28. Selecting
this message for a server policy is a presentation decision, **not recovery of
the original server's C2S28 response selection or equipment legality rules**.

The new offline oracle executes the current world switch case, formatter,
chat archive, normal visible chat ring and widget refresh to the original world
switch join. All game callees execute original instructions. Refresh uses an
absent-widget sentinel; this does not establish final rendering or actual
client/server acceptance. The independent hidden-client lane must verify the
newly appended native chat record and subsequent real legal equip.

No item, stat, role or balance mutation is needed to display this refusal.
**UI+85608 stays 1** after refusal. A subsequent actual native cached-tooltip
WPN1 request still queues C2S28 successfully. Do not manufacture an occupied
equipment 3B response to clear this flag, and do not describe the hint as an
operation completion acknowledgement.

## Exact contract

All addresses below are VA at image base `00400000`; subtract the base for RVA.

| Logical byte | Width | Meaning / verified safe server choice |
|---|---:|---|
| 0 | 1 | opcode `02` |
| 1 | 2 LE | SystemMessage ID `27` |
| 3 | 2 LE | source-qualified item key, e.g. `19071` |
| 5 | 16 | inline name fallback; send all zero when using the item key |
| 21 | 1 | text variant; send `0` |
| 22 | 1 | opaque byte; send `0` |

Logical length is exactly **23**; existing native framing adds its three-byte
header. `401324+4*2` points at `401234`, whose exact instructions are
`mov eax,17h; ret`. Do not reuse a different variable-length hint layout.

For TWP19071, safe suggested logical bytes:

```text
021b007f4a000000000000000000000000000000000000
```

World dispatcher `46929E` advances the message pointer past opcode, derives
UI at `world+A7F2F6C`, calls `484E00`, then joins at `46B517`.
`484AE0` reads ID/body+0, item/body+2, inline name/body+4 and variant/body+20.
It masks variant with `7F`; 0 and 80 were equivalent. Zero ID, ID 1951 beyond
the pinned 1950 count, variant 3 and FF all returned without chat output.
The opaque final byte is not used by this formatter; oracle messages carry A5
there to avoid accidentally treating it as a mandatory zero.

`UI+CFF70` is the resource object. `resource+B2C60` points to 16-byte message
records; signed WORD `resource+B2C64` holds count. Record `(id-1)*16` contains
display mode at +0 and three variant string pointers at +4/+8/+12.
For nonzero item key, `459A60` resolves its definition and +8 supplies the name.
The original formatter `547AF7` wraps the item as `/c3<name>/c9`, then formats
the source message. Inline names have no native bounded-string guarantee:
never transmit an unterminated 16-byte inline field. This is not a generic safe
serializer for arbitrary catalog format strings: use qualified ID27 only.

Mode 1 at `484E69` calls `47DE00(4, FF80FF, text)`; mode 2 uses channel5 and mode0
uses popup code. Those alternate display modes are outside this result.
Message807 has a separate `UI+232EAC=1` side effect in `484E00`; ID27 does not.

## Current source pins

Source `../God2/Data2/Patch/Comm/message.csvZ`, SystemMessage27 physical line102:

* compressed SHA256 `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`
* decoded SHA256 `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`
* current EXE SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`

The JSON includes original CP950 row bytes, line and row SHA. Native source
parser code spans are compared to the current EXE before WPN/TWP definitions
are used. The one pinned SystemMessage record is relocated directly into its
native memory layout; the CSV loader itself is outside this oracle.

Other source wording cannot be substituted indiscriminately: SystemMessage23
is ability-insufficient, 25 profession-incompatible, and 866 explicitly names
**神仙** sex mismatch. Ordinary-player rejection must not use a deity-specific
message or invent a reason. SystemMessage and ProgramMsg are separate tables.

## Read-only actual-client acceptance fields

At current UI `world+A7F2F6C`:

* archive ring is inline at `UI+39E20`;
* visible ring pointer is DWORD at `UI+39DE8`;
* `UI+39E18==0` selects normal chat: this channel4 message appends both rings;
  private-chat mode appends archive only. This is a visibility condition, not
  packet rejection;
* equip pending is DWORD at `UI+85608`;
* 50 inventory records begin `UI+8560C`, stride24, full instance at record+4.

Each ring has capacity200 and this layout:

| Relative offset | Meaning |
|---|---|
| `128*i` | NUL-terminated CP950 row, storage128 bytes |
| `6400+i` | channel byte |
| `64C8+4*i` | color DWORD |
| `67E8` | count, capped200 |
| `67EC` | oldest/read index |
| `67F0` | next write index |

Capture `next_write` **before** the request and check newly appended slots after
it; do not scan all memory for an old source string. `45FF00` manages wrap and
long CP950 line splitting. For the four tested WPN1/2 and TWP19071/19072 names,
ID27 occupies exactly one row. Native channel4 prefix is ASCII `1A4`, from
`58EBE8+4*4`; it is fixed text, not a pointer table. TWP19071 exact row:

```text
3141342f6333afabb8cb2db6dda6e5b1febcae2f633920b54caa6ba8cfa5cea9ceb8cbb3c6a143
```

Expected channel4/color `00FF80FF`, pending unchanged, all slot bytes unchanged,
and a later legal equip should still succeed. The emulator also verifies the
entire 0x5000-byte synthetic role region is unchanged. Actual-client acceptance
must use saved before/after resources and real transferred instance readback;
the absence of an error alone is insufficient.

## Reproduction

```powershell
python -m tools.strike_lab.current_equipment_rejection_20260927 --output artifacts/research/equipment-rejection-20260927.json
python -O -m tools.strike_lab.current_equipment_rejection_20260927 --output artifacts/research/equipment-rejection-20260927-optimized.json
```

Both pass **16 full native world refusals and 4 invalid-message guards**. Cases
cross four source item keys, variant0/80, and normal/private chat. Each refusal
also runs a subsequent complete cached-tooltip ordinary C2S28 producer. Every
assertion relevant to qualification is an explicit throwing `require`; `-O`
does not remove checks. A result is atomically replaced only after all checks
pass, so a failing run cannot publish a fresh PASS. Existing historical output
is not evidence that a later failed run passed.

No server runtime, production DB, current client binary or UI was changed by
this research tool.
