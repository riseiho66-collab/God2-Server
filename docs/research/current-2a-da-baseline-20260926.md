# Current2A initialization to ordinary player DA baseline

2026-09-26. Current executable SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
All instruction addresses below are **VA**, image base00400000. This audit uses
the current executable, not a retired packet corpus. No runtime, database,
client, desktop or shared implementation was changed.

## Exact projection

Let `B` be the36-byte2A body, **excluding opcode and outer frame**. Let `D` be
the15-byte DA logical record, **including opcode but excluding outer frame**.

| DA logical field | Initial2A source | Native destination | Current instruction evidence |
|---|---|---|---|
| D[1:3] actor WORD | `LE32(B+0)&0x3fff` | local role root+0 | 46861F..468633 masks the initial2A identity; DA469369 compares its full WORD without applying that mask |
| D[3:5] transform WORD | `LE16(B+32)` | world+1539AED2 | 468558 reads WORD[ESP+48];46855D stores the complete WORD |
| D[5] raw scalar5 | B[34] | role root+4695 = world+1539AED1 | 46827B loads WORD[ESP+4A];468284 stores AL |
| D[6] raw scalar6 | B[35] | role root+4698 = world+1539AED4 | 46828A stores AH from the same source WORD |
| D[7:15] complete components | B[12:20] | role root+4584/+4588 = world+1539ADC0/+1539ADC4 | 468328..46833F copies both DWORDs |

The offsets are established by the actual receive copy:46819C selects
`ESP+28`,4681A0 passes36, and4681A3 calls415690. After finding opcode2A,
4156FC..415716 copies bytes starting at packet+1 without conversion. Thus
the local stack offsets48 and4A are body offsets32 and34, respectively.
The new oracle executes this actual copy loop and consumes its resulting stack
bytes in each field slice. Values are not inferred from a zero-valued fixture.

DA503D30 stores logical offsets5/6/3 into exactly the same three destinations.
For an ordinary, unchanged appearance baseline, preserve the saved2A final
four bytes and all eight component bytes, then replace only the independently
authorized component bits. Do not pass the original flagged2A WORD as a DA
identity: use the identity actually bound to the role. This distinction does
not authorize masking arbitrary incoming/outgoing DA identities.

This is an **initial-state correspondence**. An intervening DA or36/37 event
can modify these fields; an old2A body then does not establish the current
authoritative appearance. The diagnostic route must preserve the latest owned
server after-state or establish that no intervening appearance mutation took
place. Nonzero transform keys take a resource-dependent substitution path and
are outside ordinary full-renderer acceptance. The native copy of their WORD
is proven; their resource validity is not.

## Read-only hidden-client observations

The existing hidden helper already reads `P=LE32(ui+86888)`, the role source
pointer. Its role root is `R=P-90`, and for this native world object
`W=R-1539683C`. Validate these pointers against readable process regions and
the already bound actor before reading. These are reads, not instructions to
patch client memory.

| Observation | Read address/width |
|---|---|
| Bound local identity | R+0, DWORD |
| Saved full component block | R+4584,8bytes (W+1539ADC0) |
| Raw scalar5 | R+4695, BYTE |
| Transform key | R+4696, WORD little endian |
| Raw scalar6 | R+4698, BYTE |
| Existing packed selectors | R+44, DWORD; first=`(value>>18)&255`,second=`(value>>10)&255` |
| Force-variant flag | W+1539AD70, BYTE bit10 |
| Local component object C | W+0A7E04D0 |
| Four handles | WORD at C+4+6*i, i=0..3 |
| Four live variants | BYTE at C+8+6*i, i=0..3 |

503F9A selects the component object.503FB2 calls actual4FF450, which stores the
handle at+4+6*i.503FCD calls actual4FFA20, which stores the variant at+8+6*i.
Absent override bit10, the variant is `D[8+2*i]>>5`; with it set, the immediate
DA setter forces7.503FFA/50400D copy the original ordinary8-byte input to the
saved component block before504013 calls501810. The latter re-enters component
selection/refresh, so acceptance must inspect stable after-state following
the actual complete handler, rather than reporting the intermediate stores
as proof of complete rendering.

Useful acceptance comparisons: all8 saved bytes equal the emitted authorized
block; three scalar fields equal their preserved baseline; each handle points
to the independently qualified source resource; variants and override behavior
agree with the current state; packet processing and subsequent input continue.
These conditions support a memory/resource observation. They do not themselves
prove graphical drawing or an original WPN-key-to-HeroDoll relation.

## Executable evidence and limits

```
python -B -m tools.strike_lab.current_2a_da_baseline_20260926
python -O -B -m tools.strike_lab.current_2a_da_baseline_20260926
```

Both **PASS266 cases**:262 body-copy/scalar/component/identity cases, including
all256 values of both scalar bytes and multiple nonzero/high transform WORDs;
four actual component handle/variant setter returns. Current EXE identity,
read-only code, execution ranges/budget, exact stop PCs, allowed writes, input
guards and component canaries are enforced with non-optimizable checks.

This is segmented execution of actual native instructions with explicit
synthetic inputs. It does not execute full2A scene initialization, resource
loaders, transform eligibility, DA refresh tail, or renderer. No game callee
is replaced with a success stub. The existing49-case audit and compiled45-wire
DA test remain separate evidence in `current-weapon-appearance-20260926.md`
and `tests/research/test_player_appearance_update_native.py`.
