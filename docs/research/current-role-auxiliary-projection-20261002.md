# Typed role auxiliary snapshot — 2026-10-02

## Implemented boundary

`src/protocol/RecoveredRoleAuxiliaryProjection.h` adds a typed, lossless view
of the existing 61-byte raw self `2C` snapshot. It updates explicitly supplied
signed modifiers or absolute combat totals while preserving every other byte.
It supplies no character starting stats, equipment formula, item roll, buff,
set bonus or resource calculation. The existing raw codec, formal runtime20,
formal database, client and service configuration are unchanged.

The helper is available to a future qualified authoritative producer. It is
not activated by merely constructing a view, and has not been installed as
an equipment-stat producer in Application.

## Original instructions and compiled qualification

Current client SHA256: `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
Mapped original SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The compiled C++20 probe is fed into actual `4E6600`, `4E6710` and `4E6DB0`
instructions. Every executed instruction is compared with the pinned original
image; only external CRT sprintf is adapted. No game consumer is substituted.

Four test groups pass:

- 40 signed-update vectors, including zero, ±2044 and the full int16 edges;
  canonical encoding and repeated projection are byte-stable.
- 16 raw WORD/mask combinations, including both positive and negative bits;
  positive precedence and modulo-WORD negation match native behavior.
- Four combat vectors verify the nonsequential defense/attack wire order,
  all DWORD bits and the original signed `%d` display domain.
- 62 malformed snapshots are rejected without changing the original raw codec.

This is 60/60 current-native consumer cases, not a live-client gameplay
percentage. Receipt and hashes:
`artifacts/research/current-role-auxiliary-projection-20261002/verification.json`.

## Wire and display semantics

Logical offsets include the opcode. Modifier lowWORDs are Con/Str/Int/Speed
at 1/5/9/13; their upperWORDs remain opaque and are preserved. Positive and
negative masks are lowWORDs at 37/41, with bits 2/4/1/8 respectively. Updates
clear only those four bits and set a canonical positive or negative bit for
nonzero supplied modifiers. Signed magnitude uses a widened intermediate,
including −32768. Unknown mask bits and upperWORDs are preserved.

Five element DWORDs at 17..33 are copied without assigning a gameplay formula.
Combat raw DWORDs are physical defense45, physical attack49, magic defense53,
magic attack57. Transport permits all bits. `nonnegative_combat_display`
reports whether the original signed formatter would show nonnegative values;
it neither truncates nor rejects captured values.

The role sheet displays base22 and modifier2C separately. Zero modifiers use
an empty format; the unused vararg contains stack residue and must not be
interpreted as an extra stat. Negative actor RAM is not reserialized as raw
wire: a fresh absolute packet supplies its own magnitude and sign masks.

## Required ordering correction before equipment composition

The new armor oracle's `tooltip_cases` contain the actual native label order
`物防, 魔防, 力, 體, 智, 速`. Therefore armor bytes8/9 mean Str/Con, whereas
self2C fields1/5 mean Con/Str. The existing armor C++ `force,constitution`
operand order follows those labels. The initial armor research prose listed
Con/Str in tooltip order incorrectly; its raw executed evidence proves the
correction. Preserve that old artifact as historical evidence and use the
corrected semantic contract. A same-index armor-to2C array copy is invalid.

## Remaining work

Original equipped stacking, enhancement, set/buff composition and final combat
stat producers remain open. Formal characters without owned role/resources/
auxiliary snapshots do not gain inferred zero or diagnostic starting values.
A future CUSTOM producer needs explicit field origins, balance qualification,
transactional state handling and own-server current-client acceptance before
activation. The raw sign lifecycle on ordinary role-panel opening is being
qualified separately; direct repeated calls to the formatter alone do not
prove a live client defect.

## Reproduce

```powershell
python -X utf8 -B -m unittest discover -s tests/research -p test_current_role_auxiliary_projection_20261002.py -v
```

CTest name: `current_role_auxiliary_projection`, labels
`packet;native-consumer;not-live-acceptance`.
