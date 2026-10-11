# Projection Candidate: Native Text Output Boundary

## Result

The 119E30 candidate's tail calls a native text-message routine. Continuous
offline execution starts at RVA **11A959**, follows the original call
at11A96C to96990 and all reached
string/query helpers, stopping at132E0 before its first instruction executes.
No helper return is invented, no original instruction is patched, and no
network connection is made.

The input text at stack+1D4 and tail registers are explicitly synthetic.
The earlier multiplication, text formatting, and natural reachability of119E30
remain unexecuted in this test. This result qualifies a consumer/output path,
not the entire function's gameplay meaning or an attack/defense formula.

## Evidence

- The inspected prefix reads the WORD at VA592644 (bytes21 00) and writes
  bytes05/16 at119F00/119F08, producing the initial `!\x05\x16` text prefix.
- Tail11A959..11A96C passes the prepared text and three zero arguments to96990,
  with `this` read from the owner's +20 field.
- In96990, `!` dispatches to96A7E. Its related-object +3F98 must be nonzero
  for the tested channel1 path. The fixture supplies1 explicitly, not as a
  proven current-game-state value.
- 96AB1/96ABC advance the text pointer past `!`. Original string comparisons
  also inspect literal `/board` and `/board ` strings; these are not battle
  arithmetic operations.
- 96F16..96F24 pass opcode2F, an outgoing body pointer and its size to132E0.
  The run stops at that callee's entry; it does not prove a transmitted wire frame.

For synthetic text `!\x05\x16actor 3`, the native pre-encoder body is:

```text
11 00 01 00 00 00 05 16 61 63 74 6F 72 20 33 00
```

The body size is16 and its leading WORD is17. Channel low7 bits are1 and the
text is the original input with `!` removed, including its terminator. Body
byte3 is not assigned in this executed path: stack poison changes it from00
toA5. It must NOT be promoted as a verified constant or complete wire schema.

Only the stack and the related context's text-history region are written in
these runs. No actor HP, attack or defense is written. This supports classifying
the tail as a text-message producer, but does not establish whether its earlier
calculation is a preview, command aid, unused code, or something else.

## Reproduction

```powershell
python -B -m tools.strike_lab.current_projection_sink
python -B -m unittest discover -s tests/research -p test_current_projection_sink.py -v
```

Three test methods pass: four native text variants (3..120 bytes), two stack
padding counterfactuals, and invalid-fixture rejection. The default run executes
503 native instructions. JSON contains the current image SHA256, range hashes,
actual arguments at the encoder boundary, native writes, and explicit limits.
The length limit120 is a harness constraint, not a reconstructed protocol limit.

## Next Frontier

Do not install119E30 as a damage formula merely because it multiplies and
subtracts. Its populated input producer and natural caller remain unresolved.
Prioritize an evidenced writer of damage input or an attack/defense-to-result
chain over further synthetic variations of this text-output candidate. Existing
received-result arithmetic and the isolated custom combat rules remain unchanged.
