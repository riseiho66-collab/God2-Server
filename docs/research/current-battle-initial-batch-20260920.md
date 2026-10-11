# Current Battle Initial Batch Evidence

## Typed Server Bootstrap Builder (2026-09-20)

`src/protocol/RecoveredBattleBootstrap.h` now assembles explicit 82 context,
45-byte 1C identities and 17-byte 86 vitals into the existing zero-seed envelope.
It preserves every supplied opaque identity/vital byte. Identity accessors expose
only the qualified offsets, and area/scene accessors are restricted to variant
0400. Identity parsing does not certify resource availability or native values.

CUSTOM-0005 records the chosen per-actor ordering and consistency policy.
There are no production default actors, stats, context fields or automatic
Application emissions. Enemy MP is rejected because the qualified receiver
does not apply it; the client not receiving MP is not proof that enemies have
no MP in authoritative gameplay. This API does not change Session state.

Verification: Release target built; four selected CTests passed. The battle-entry
suite passed 19/19, including a new independent Python expected-byte comparison
against `recovered-battle-bootstrap --diagnostic-wire`. That diagnostic uses two
synthetic actors, at positions 0 and 14, and is never a production catalog.
The original codec and full closed-UI world receive function return state 4,
retain the first 45-byte identity in lookahead and preserve the remaining scalar
and identity records exactly. This does not execute the battle actor constructors
to completion or certify rendered/live combat. Next integration requires validated
resource bindings and initialization, then a session-owned battle service with
C++ authoritative mutation and Lua rules; fixture JSON is not a native reply.

## Known Receivers, Not a Captured Official Sequence

The current original length function15840 independently returns:

| Logical opcode | Bytes including opcode | Qualified information |
| --- | ---: | --- |
| 82 | 9 | Transition context, two raw DWORDs; not a complete monster record |
| 1C | 45 | Participant construction input; displayed level byte and enemy identity routing are already qualified |
| 86 | 17 | Per-position scalar update; subtypes0/1 copy two transmitted DWORDs into actor storage |

Image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
See the existing monster-base-stats and battle-scalar-result proofs for exact
field reads, widths, branches and remaining unknown meanings. A reader/field
proof is not an original official numerical value.

A large network read, a recovered protocol data frame and a logical record
are distinct boundaries. The current receiver supports multiple logical records
in one decoded frame. The existence of these consumers does not prove every
official encounter used this order or included every attribute in its first batch.

## New Mixed-Batch Regression

The formal C++ recovered-world-frame encoder creates diagnostic frames with an
82 record followed by1,14 or28 groups of one1C and two86 records. These counts
are test coverage, not a recovered encounter population or sender policy.
The largest logical stream is2221 bytes. All identity/scalar payloads in this
test are explicit synthetic patterns.

The original codec decodes the complete frame; original68AE0 then consumes the
82 transition and returns state4. The first45-byte1C remains intact in the
lookahead buffer, the cursor is exactly54, and EVERY remaining byte of all mixed
records stays intact in the receive buffer. The pending battle records are not
misparsed as one huge monster structure or discarded at the mode transition.

This qualifies transport/record preservation only. It does NOT execute the full
battle initializer or consume all queued records into visible actors. It also
does not supply an official capture or recover HP, MP, attacks, defenses, skills,
experience, capturability or loot values from the synthetic payloads.

## Verification

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_entry.py -v
```

18/18 tests pass in2.200s. The suite includes the new mixed-batch preservation
case plus existing frame decoding, checksum failure, partial lookahead,
transition dispatch and large-coalesced-queue regressions.

The next numerical-source work is the actual1C constructor and its following
updates, retaining actor identity and separating packet-supplied fields from
source-table values and purely presentational fields. No database import follows
from the mixed-batch test.
