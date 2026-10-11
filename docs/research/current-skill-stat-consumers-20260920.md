# Skill Stat Consumer Candidate Index

## Whole-Range Wider-Operand Follow-Up

`wide_image_inventory()` extends overlapping read/address operands to RVA
1000..170000, retaining byte/WORD/DWORD widths but excluding ESP/EBP bases.
It returns 263 candidates, not 263 skill consumers or formulas. Skipdata and
linear-decoding limitations remain explicit; indirect/rebased aliases remain
unresolved. The list is reproducible from the pinned image via the function.

One arithmetic candidate at10A666/10A66B/10A66E now has an executed discriminator.
`translation_candidate()` runs unchanged10A646..10A67D and stops BEFORE the
call at10A67D. ESI object, EBP manager and stack new values are synthetic live-ins.
Two signed WORDs at object+4C/+4E are replaced with new values. The respective
signed differences are added modulo2^32 to DWORDs58/60 and5C/64. The complete
80-byte object comparison proves every other byte unchanged in nine runs with
signed-WORD extremes and zero. The instruction immediately after this bound
calls18BD0 with object+58 and object+2C; that callee is not executed here.

This demonstrates paired delta translation, not a verified skill-record pointer
or attack/defense-to-damage chain. No gameplay semantic is assigned solely from
these offsets. New tests pass3/3 and the existing consumer suite passes6/6.
The other candidate instructions are not individually cleared by this test;
the exercised branch itself contains multiple indexed candidates.
No original formula or production value is promoted.

## Finding

No original damage formula is promoted. This step follows known skill-record
effect fields rather than extending the unrelated text-output candidate119E30.
It eliminates one concrete same-offset false match and records a reproducible
bounded search, not a claim that the client has no formulas.

The current image SHA256 is
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Only this image was read. No retired archive, production database, live process,
or custom combat formula was modified.

## Search Scope

The existing skill effect label proof binds record WORD offsets5E,60,62,64 to
attack/defense-related text conditions. A Capstone linear sweep of RVA1000
through170000 indexes direct WORD memory operands at these displacements,
excluding ESP/EBP-based operands. The output includes skipped-byte count,
instruction RVA, base/index registers and operand access mode.

There are13 candidate instruction hits in this exact sweep:

- 126201,126218,12622F,126246: the four known `cmp word [edi+offset],0`
  conditions in126120. In the battle region110000..131000 these are the only
  matches under this narrow query. Prior native execution establishes that
  nonzero values select labels; they do not multiply the received amount.
- FB584,FB598,FB5EB,FB8A9,FB8C3,FBBE4,FD5DB,FD666,FD752: nine matches at
  displacement60 only. These are NOT automatically skill-field consumers.
  Inspection finds object/record addressing and downstream UI-related calls,
  not a proven skill definition pointer. Only the FD5DB slice below receives
  new executable qualification in this step.

This is a candidate index, not a whole-program alias analysis. Linear decoding
can misalign or decode embedded data. Pointer rebasing, aliases, wider loads,
ESP/EBP operands, indirect addressing and runtime code are not exhausted.

## Executed False-Match Discriminator

Original FD5C2..FD5E8 is executed continuously until1091C0 entry. EAX is an
explicit synthetic index, supplied AFTER the unexecuted FC960 lookup. No
callee return is replaced and no transport/renderer is run.

```text
ECX = index * 9
EDX = index + ECX * 2 = index * 19
EAX = index + EDX * 4 = index * 77
WORD read address = manager + EAX * 8 + 0x60
                  = manager + index * 616 + 0x60
row start         = manager + index * 616 + 0x18
field within row  = 0x48
```

The supplied WORD is passed unchanged as the first argument to1091C0, whose
`this` comes from manager+8. It is not a read of a skill definition at+60.
The earlier index lookup and broader field meaning remain unqualified.
No monster-stat or server-formula claim follows from this value transfer.

## Verification

Three unittest methods pass: pinned13-hit inventory,12 native executions
(indices0/1/127 crossed with values0/1/32768/65535), and invalid-live-in
rejection. The native tests check exact read address and width, callee entry,
argument, context pointer and unchanged source WORD.

```powershell
python -B -m tools.strike_lab.current_skill_stat_consumers
python -B -m unittest discover -s tests/research -p test_current_skill_stat_consumers.py -v
```

## Next Evidence Needed

Trace aliases or wider loads tied to a verified skill/stat pointer, or locate
another independently bound attack/defense source. Do not label same-offset
UI/object fields as attack/defense. The original attack/defense-to-damage,
critical calculation and authoritative MP transaction remain unverified.

## Wider-Load Follow-Up

A new bounded sweep of110000..131000 includes overlapping operand widths,
EBP-based accesses and LEA address candidates (ESP still excluded). It produces
16 candidate instructions. This is not16 calculations: most are stores, four
are the known skill display tests, and11662F is in apparent embedded data
after the116628 return. Linear decoding alone must not certify that as code.
11C676 rebases a pointer to+60, but inspected11C679 loads a pointer and compares
its ID/kind bytes. The pre-existing skill identity proof classifies this as
auxiliary skill-list matching, not reading a skill magnitude WORD.

### New Continuous Native Binding

The new executable edge starts at114A35, calls original115700 and1156E0,
then calls the entire11EDA0 target-mask routine and its11ED00/11ECA0/11EC70
helpers, stopping before114A5E. No callee is replaced, no renderer is run,
and no attack/defense values or skills are invented. Entry state and the two
occupancy masks are synthetic diagnostic inputs; upstream battle setup is not
part of this execution.

Primary branch11570A reads one byte from battle+64. Secondary branch115718
reads battle+68 instead. The corresponding actor slot comes from battle+51
or+52. Both full paths use this byte as the reach argument to11EDA0. High
DWORD bytes are poisoned, and the inactive branch holds a different value.
Observed non-stack writes are confined to battle+434/+438 target masks.
The source occupancy masks are unchanged and the native stack is restored.

With actor0 and both occupancy masks3FFF:

| Reach byte | Output side0 | Output side1 |
| --- | --- | --- |
| 0 | 001F | 0000 |
| 1 | 01FF | 001F |
| 3 | 3FFF | 0FFF |

Thus the battle object's+64 is a range input on this caller path, not the
skill definition's+64 magical-defense-related text flag. This is another
concrete same-offset collision. It does not establish the meaning of every
read of+64 throughout the client or prove global absence of damage formulas.

Static inspection also finds117968 and118064 store a value loaded from item
metadata+120 (or fallback2) to battle+64. That upstream metadata binding is
not included in the new continuous execution and is not promoted as a
source-to-gameplay proof.

Follow-up: `current-item-battle-reach-20260920.md` now qualifies the117940
lookup/store edge using four source-loaded equipment records, followed by the
target consumer in the same VM at a separately declared entry. It also executes
the native missing-key fallback. It remains offline staged evidence, not live
gameplay or a damage formula.

The expanded suite has six passing methods, including64 continuous native
range runs over primary/secondary selection, occupied/sparse rows and reach
boundaries, plus explicit target-change and invalid-input checks. The previous
three methods remain intact. Counts measure diagnostics, not recovered formulas.
