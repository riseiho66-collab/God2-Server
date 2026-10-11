# Battle Speed Backtrace

**No monster identity -> intrinsic attribute value/formula was recovered.**
Original monster speed remains null; all four intrinsic attributes remain
unqualified in this lane. The new positive evidence is a continuous original
queue-consumption -> marker-group -> actor-activation chain. It cannot uniquely
recover monster speed from observed action order.

Only this document and matching `current_battle_speed_backtrace.py` tool/test
were added. No child agents, UI, network, DB, shared changes, archived inputs,
ROM loading, name inventories or other attribute-system scans were used.
Neither the prior 83/0D manager+30B/+30C proof nor MP formatting was rerun.

## Pin And Scope

Mapped image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE `400000`; RVA equals file offset. Addresses/field offsets below are hex;
actor positions, markers, counts and packet lengths are decimal.

Define B=battle owner, M=B+144938, Q=B+A9EA4B0. The test starts at original
`1142F0` with a prepared inbound queue, not a live socket/transport decoder.
Three 15-byte logical records use opcode 83 and action discriminator 20
decimal (14 hex), with source positions 17,5,17 and markers 7,7,8.
Their action name is not guessed. This accepted branch invokes no renderer
and supplies no attack/defense/attribute values.

All 28 type-0 actor pointers are explicit runtime snapshots, as required by
these native loops. Only the two participating snapshots have active handles;
the rest use FFFF and action zero. Active render-kind bytes are explicitly
provided as 2, not returned by a simulated game helper. Other actor bytes are
poisoned. There is no original EnyName identity/attribute binding in these
snapshots and no claim that side alone proves a wild-monster discriminator.

## Exact Executed Chain

One original invocation runs continuously from `1142F0` to **before `12AE2F`**:

| RVA / caller | Native source -> operation / destination |
| --- | --- |
| 1142F8 -> 11D3B0 | Peek Q: compare read/write cursors +8/+C; return Q[+4]+readCursor |
| 11431C -> 15840 | Original logical-size lookup for opcode 83 returns 15 |
| 11432D -> 11D3D0 | Copy head record to B+A9E9CB0 with consume flag zero |
| 114376 / 11437C | First record BYTE +3 -> caller's initially-FFFFFFFF marker gate |
| 114384 -> 12AF90 | Original actor preparation; real type-0 lookups, render-kind checks and +277 resets |
| 11438F / 114395 | Compare copied record BYTE +3 with the retained marker gate |
| 11439C -> 116AE0 -> 12C520 | Consume matching action; real side/slot selection and original actor lookup |
| 12A94D / 12A953 | Read action's marker argument; write BYTE actor+1E7 |
| 12A95F | Write action discriminator BYTE actor+1E9=14 |
| 12AA63 / 12AA6A | Set action state actor+1EA=98 and actor+233=0 |
| 1143B3 -> 11D3D0 | Consume flag one; original 11D493 advances Q+8 by 15 modulo capacity |
| 114397 -> 1143BA | Different marker: do not consume record; clear B+A9EA4C4 |
| 1145CE..1145DB -> 12AC20 | Read caller's retained marker and pass it to the activation manager |
| 12AC6A -> 11E6E0 | Scan type-0 actors in side0 slots0..13, then side1 slots0..13 |
| 12ACA9 | Active handle's render-kind BYTE must equal 2 on this fixture path |
| 12ACEA / 12ACF0 | Read actor+1E7; compare with the marker argument |
| 12ACFA..12AD12 | Read actor+1E9; dispatch its action class through native tables |
| 12AD57 / 12ADD7 | For action14, write actor+1EA=98 and actor+233=1 |
| 12ADDD | Increment selected count M+A7FBC64 |
| 12AE29 | Store selected marker BYTE at M+308 |

The marker producer is the incoming record, not an actor speed calculation.
Within this bounded run, **all actor data reads** are exactly +1A WORD,
+1E7 BYTE, +1E9 BYTE and +239 BYTE. Complete read hooks and whole-actor poison
comparisons establish this set; it is not inferred from opcode names. No
actor numeric attribute, companion owner, role stat owner or sorting comparator
is read. This proves only the executed branch and declared readiness state.

## Decisive Counterfactuals

| Prepared queue | Actual receive order | Actual activation-write order | Pending queue |
| --- | --- | --- | --- |
| slot17/marker7, slot5/marker7, slot17/marker8 | 17,5 | 5,17 | Cursor30, marker8 untouched |
| slot5/marker7, slot17/marker7, slot17/marker8 | 5,17 | 5,17 | Cursor30, marker8 untouched |
| slot17/marker90, slot5/marker3 | 17 | 17 | Cursor15, marker3 untouched |

Thus the first queued marker chooses this group, not the smallest marker.
Within a group, activation writes follow the manager's fixed actor-slot scan,
not packet arrival order. They are **not** a measured animation-completion
order or proof of server combat priority. Both sides participate in the same
original scan. No marker is interpreted as a speed value, rank magnitude,
elapsed time, initiative coefficient or calibrated unit.

## What Cannot Be Inverted

Recovering a monster intrinsic speed needs an original identity-bound source
or a verified formula with sufficient inputs. This chain supplies neither.
Even a genuine observed action sequence does not uniquely determine numeric
speed without an authoritative ordering rule, tie handling, skill/priority
effects, state modifiers and any randomness. Pairwise speed inequalities are
also conditional on those rules; this proof does not establish them.

The independently identified companion owner +38/+3A/+3C/+3E attributes
(constitution/strength/intelligence/speed) are **not battle-actor offsets**.
Role +94/+98/+9C/+A0 attack/defense fields are likewise a different owner and
not speed. This lane imports neither set into monster actor state.

Exact remaining source: the sender-side producer that orders logical 83
records and assigns their BYTE +3 markers, joined to participant identity and
the server's intrinsic attribute calculation. The client-side marker writer
and fixed-slot activation consumer do not expose that producer. No claim is
made that the whole client lacks another speed source or formula.

Exact native continuation stop is `12AE2F`, before an imported clock call.
Static `12AE3B` would store its return at M+A7FBCC0; neither executes here.
Playback timestamps, frame pacing and animation speed are not combat speed
or intrinsic speed. Later rendering/completion and marker-advance callers are
not needed for this bounded exclusion and remain unqualified here.

## Reproduction

```powershell
python -B -m unittest tests.research.test_current_battle_speed_backtrace -v
python -B -m tools.strike_lab.current_battle_speed_backtrace
```

Three focused tests cover three positive sequence/poison scenarios, exact
queue cursor writes and preserved pending/input bytes, both sides, the complete
actor-read set, original-image immutability, whole-actor write reconstruction,
missing render-source guards and the narrow input contract. The source guard
stops at the actual `12AFEF` read, including when another fixture occupies the
same physical page; absent source state is not supplied as zero or success.

Final run: 3/3 tests passed in 0.077 seconds. The CLI subprocess exited 0 within
its ten-second bound; parsed JSON verified receive order [17,5], activation
order [5,17], cursor30, stop RVA12AE2F and null original monster speed.

Native code pages are read/execute; instructions have a 20,000-step budget and
closed ranges. Every data access records RVA, address, named owner, raw offset,
width and exact bytes. The CLI emits this trace plus span hashes. There are no
OS/game return adapters, deferred background processes or generated artifact
files. **Usable original monster attribute values recovered: 0.**
