# Current Hit/Evasion Dataflow: 2026-09-20

## Result

**Hit probability formula NOT RECOVERED.** This delivery executes original x86
instructions to establish a supplied-outcome evasion branch, its action-state
binding, and the distinct destination of a nearby real RNG calculation. It does
not implement a substitute hit model or assert that such a formula is absent
elsewhere in the client.

Qualification: **offline original-native slices under Unicorn, synthetic entity
state and logical S2C input**. Not original-process gameplay, formal server
loopback, a captured player exchange, or live E2E. No server DB, socket, desktop,
archive, shared runtime, or CMake changes. The native image is mapped read/execute;
no instruction patch or original-callee replacement is used.

## Pinned Evidence

Source is `recover_combat_rules.IMAGE`, the current mapped image:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

- SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
- Size: 3,174,400 bytes. Mapping base: `0x400000`; file offset = RVA.
- PE section metadata is not used to translate these offsets.
- The JSON contains raw bytes and SHA256 for 13 exact code/data slices. End RVAs
  are exclusive. The full-image hash covers instructions outside those extracts.

Key slice identities:

| Slice | RVA interval | SHA256 |
| --- | --- | --- |
| Incoming record consumer | `12C520..12C636` | `6787749fb84608aeb5eb5b7cf116989dfc03f3695a87cd60626d087b9f50defe` |
| Evasion text decision | `12B3C2..12B4A4` | `f4acbb6d0ffd0a10087295dd9c6e9e6dd319b65ec21b6ad251264b8160c29eba` |
| Nearby RNG producer | `12A7F0..12A8CE` | `3f21da4ab6e1422fc7eee0060b9717b3bbb8ef7a0229793bcc1b0b2e3e01da57` |
| CRT RNG | `147D7F..147DA1` | `2cba33762e4a14c6cf8f10c08f10caf20d423d7879e24090d01a8a02d866e2d1` |
| Outcome action map | `171600..17160D` | `ca354080a1b19228f911980f15ace2e9b1b244fa7b439d4037841e7bfe13d6a7` |

Read first: `current_battle_result_fields.py`, its focused tests, original result
flag proof/tests, `skill-formula-validation-20260920.md`, and
`combat-rule-authority-20260919.md`. The existing S2C `0x86` discriminator-3
path (`117480 -> 12C3E0 -> 126270`) transfers a DWORD at record `+5` to entity
`+DB8` with bit-0 normalization. That does not establish a hit/evasion bit. The
fresh proof below follows a different logical action, S2C `0x83`, kind `1`.

## Supplied Outcome to Evasion

The native size-table entry at `1324 + 4*83` points to `1252`, which executes and
returns 15. The dispatch index at `11465C + (83-1C)` and target table at `114634`
resolve to `11436B`. Execution starts inside the original queue dispatcher at
`114332`, not at a Python implementation of its result decision.

Continuous executed route:

`114332 -> 116AE0 -> 116BB1 -> 117183 -> 12C520 -> 12A8D0 -> 12B060 -> 147AF7`

`147AF7` is a stop **before** formatting/rendering. Entity lookup and coordinate
arithmetic (`1224A0`) execute. The fixture supplies an already-initialized battle
(`battle+A9DF6B8=1`), so the native jump at `116AFC` skips initial clock/graphics
setup. Logical record and queue-control inputs are synthetic; socket framing and
decryption are outside this proof. The representative result-8 path executes 782
instructions. Each case uses a reused VM with freshly reset fixture data.

Let R be the 15-byte logical record, and P = R+1 (the parser's payload pointer).

| Value | Width and producer/consumer |
| --- | --- |
| Action kind | R+1 BYTE, fixture value 1 |
| Packed actor position | R+2 BYTE; parsed into side/slot using division by 14 |
| Target masks | R+5 and R+7 WORDs; consumed through `11E5E0`; fixture selects side 1, slot 0 |
| Numeric amount | R+9 = P+8 WORD loaded at `12C615`; low WORD of argument 5; sign-extended to int16 for numeric formatting |
| Supplied result | R+11 = P+0A unsigned BYTE loaded at `12C612`; low BYTE of argument 7 |
| Secondary input | R+12 BYTE exists in the fixture; this text call uses fixed argument 8 = `0x22`, not a claim that R+12 controls this call |

At `12B40E` the consumer loads the result argument's low BYTE. At `12B412`,
`cmp cl,8` selects the original evasion label at `19CE48` (CP950 bytes
`b0 6a c1 d7 00`), pushed at `12B41B`. The formatter call is at `12B421`.
Result 7 instead selects the defense label (`19CE00`, `a8 be bf 6d 00`);
6 selects an empty string; tested results 0, 9, 11, and 12 select `HP %+d`
(`19D968`, `48 50 20 25 2b 64 00`).

These are supplied result classifications, **not probability thresholds**. The
tests cross seven result values with all five signed amount probes
`-32768,-1,0,1,32767`. Amount changes cannot make result 7 select evasion or
result 8 select numeric text. Another 16 cases cross results 7/8, entity `+DB8`
values `0,1,0x40,0xFFFFFFFF`, and zero/`0xA5` surrounding-byte fill. Neither
entity's `+DB8` is read on this qualified route, and both remain unchanged.
This limited counterfactual is not an assertion about every battle action.

The tests verify both logical-input copies remain unchanged, all 11 ordered
non-stack writes including their widths/values, and the unchanged mapped image.
Every changed fixture byte must be explained by an observed native write. The
route has intended action/display state mutations; it is not a no-mutation path.

## Action-State Binding

A separate native execution starts at `12C000` and calls `12C0C0`. It does not
pretend that the stopped formatter returned. The byte lookup at `171600` maps
supplied values `0,7,8,11` to `15,3,5,130` respectively. Thus the value selecting
the evasion label also maps to action byte 5 in this consumer.

Entity `+1E8` stores the raw mapped action and `+1EB` the effective action. For the
tested states, a target prior action of 3 preserves effective action 3 except
when the raw mapped action is 5 or 130. The separate table at `171610` maps
secondary 0 to 9 and secondary 34 to 119. Mapped secondary 9 replaces effective
action with 9 except for raw action 130. Sixteen native cases cover these
combinations and restrict writes to the observed action-state bytes. These are
presentation/action-state modifiers, not established accuracy/evasion modifiers.
No extra gameplay semantics are assigned to numeric action codes.

## Nearby RNG: Exact Arithmetic, Wrong Destination for Hit Probability

The real nearby producer `12A7F0` is gated on entity BYTEs `+1E9==1` and
`+1EA==0`, calls the `122380` rectangle/selection helper, updates action state,
and calls the RNG at `12A89D`. That prefix and its OS-dependent selection helper
are statically inspected, **not executed** by this harness.

The original calls `12A89D -> 147D7F -> 14E001` do execute. Execution stops before
the TLS helper `14E001`, with actual return addresses `147D84` and `12A8A2` on
the stack. There is no fake TLS callee. A separate bounded execution of the RNG
body begins at `147D84` with an explicit synthetic thread-state pointer:

```text
seed: DWORD at thread+14
147D87: multiply by 0x343FD (214013)
147D8D: add 0x269EC3 (2531011)
147D93: store low 32 bits to thread+14
147D98: shift right 16
147D9B: mask with 0x7FFF
output = ((seed * 214013 + 2531011) mod 2^32 >> 16) & 32767
```

The output domain is 0..32767. For example seed 0 produces next state
`0x00269EC3`, output 38; seed 1 produces `0x0029E2C0`, output 41;
seed `0xFFFFFFFF` produces `0x00235AC6`, output 35. Thirty-two native transitions
test eight initial seeds, four successive steps each, including DWORD wrap.

A third execution begins at continuation `12A8A2`, supplying the observed RNG
output, explicit local coordinates, and already-pushed arguments. Original
`CDQ`/`IDIV` at `12A8A8` computes remainder 100. The resulting native call to
`12B060` has arguments:

```text
[0, 0, 1, 0, RNG_output % 100, 0, 0, 34]
```

The remainder goes to **numeric argument 5**, while result argument 7 is fixed
at zero. It reaches `HP %+d`, not the evasion push. Ten boundary inputs
`0,1,98,99,100,101,199,200,32766,32767` execute this distinction. The constant
100 is an integer divisor in this dataflow, **not a proven percent hit threshold**.
There is no RNG-to-outcome comparison in these executed slices. The three
executions are explicitly separated at TLS/continuation boundaries; they do not
constitute an uninterrupted execution of the full RNG producer.

## Reproduction and Results

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.current_hit_formula --output artifacts/research/current-hit-formula-20260920.json
python -B tests/research/test_current_hit_formula.py -v
```

Actual results on 2026-09-20:

- CLI: exit 0, 0.107 seconds; 35 incoming executions, 7 RNG seeds each followed
  by the numeric continuation, 16 action-binding executions, and the real
  RNG-to-TLS call boundary. Counts are scenario observations, not distinct
  gameplay actions or a hit-formula coverage denominator.
- Focused tests: **9 tests passed in 0.370 seconds** on the final rerun (initial
  run: 0.375 seconds). In addition to the report
  replay, they exercise the 35 outcome/amount cases, 16 flag/fill cases, 32 seed
  transitions, 10 remainder boundaries, and 16 action-state combinations above.
- Wrapper-invalid records/seeds/RNG outputs are rejected before fixture
  mutation. This is harness validation, not proof of native malformed-packet
  rejection. Tests prohibit subprocess, socket, and SQLite connection creation.
- An independent in-process `build_report()` serialization was byte-compared
  against the saved JSON: PASS. Artifact size 309,928 bytes, SHA256
  `1bbef1ff39a01ecb1f8ed16b838f25ba612f9a6a3f257ab9cd48caba57dd3bd8`.
  File output omits elapsed time, includes exact native observations/slice bytes,
  and stores compact trace hashes/counts instead of instruction trace dumps.
- No entire suite or unrelated integration checks were rerun.

Owned paths: the new `tools/strike_lab/current_hit_formula.py`,
`tests/research/test_current_hit_formula.py`, this document, and the generated
`artifacts/research/current-hit-formula-20260920.json` only.

## Precise Missing Link

Find the original producer choosing **logical S2C `0x83`, action-kind 1, BYTE
`+11`**, then bind its input accuracy/evasion stats (including widths), state
modifiers, RNG source, threshold, and comparison direction to that byte. The
qualified client receive consumer treats this outcome as supplied; no original
server producer executes here. Accuracy/evasion stat identities and a probability
comparison remain unidentified. The arithmetic proved above is a nearby numeric
display path and must not be promoted into server hit authority or a generic
hit/evasion formula.
