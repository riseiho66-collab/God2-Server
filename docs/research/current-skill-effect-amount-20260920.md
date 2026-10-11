# Skill Effect Amount: Original Store Provenance

## New Executed Edge

Pinned image SHA256149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
All code addresses below are hexadecimal RVAs, mapped base400000.

The previous static caller-to-store hypothesis now executes continuously:

`12C83F -> 12C845 -> 12C860 -> 12B060 -> 11E6E0 twice -> 1224A0 -> 12B619`.

Explicit live-ins are a14-byte consumer-record buffer, manager participant
table, source/target side0 slots0/1, coordinate table, actor states3 or23 and
effect-slot byte239. This is not a claimed full wire packet or an execution of
the preceding receive dispatcher. Both participant pointers come from the
original lookup function, not replacement return values. No instructions or
game calls are stubbed. Code ranges and1000-instruction bound are enforced.

The WORD at consumer-record+8 is passed as the fifth argument. After the native
callee's locals/saved registers,12B60D reads stack+60. The original12B619 stores
its low16 bits to actor+28A+2*actor[239]. High register bits deliberately contain
poison, demonstrating that the final WORD store preserves precisely the supplied
16 bits. No attack/defense read, coefficient multiplication, or saturation occurs
in this executed path. Only that WORD may change outside private stack; entire
source/target snapshots and the input buffer are compared afterwards.

All28 explicitly bounded slots before the next field at2C2, both states3/23,
and values0000,0001,7FFF,8000,FFFF execute:280 cases. This bounds the fixture;
it does not prove that all28 slots occur in legitimate server gameplay or that
the original writer validates its own index.

## Continuous Action-Consumer Entry Extension

The follow-up additionally starts at original12C520, not the intermediate
12C83F boundary. It supplies a complete diagnostic15-byte logical83/03 action
record and an existing one-entry skill cache containing a pinned definition.
The cache precondition is explicit; the earlier116AE0 resource-loading path is
not folded into this proof or bypassed in flight.

Original12C537 resolves the source,12C731 searches its cache,12C7D2 publishes
the calculated catalog pointer,12C817 executes the skill identity classifier,
and12C83A calls the full12A8D0 state-update function. Its12A95F changes the
deliberately poisoned prior action byte to3. Native execution then continues
through12C845/12C860 to12B619, with no skipped call or manually staged action
state. The amount read is logical-record offset9, size2, because ESI points to
logical+1. Original source/target lookups and coordinate-index helper execute.

All448 populated skill identities reach this store with diagnostic amountFFDB.
Five additional values0000,0001,7FFF,8000,FFFF cover the unsigned WORD range
boundaries for identity(0,1). Effect index239 starts at1, retaining the original
non-reset branch; this does not establish the fresh action-reset branch.
The resulting source+28C is exactly the supplied WORD and selected pointer
matches the pinned definition. All writes must reconstruct the two whole actor
snapshots, or belong to private stack/manager notification byte309. The received
record remains unchanged and overreads fail. No opaque actor bytes are promoted
to attack/defense semantics. This extension establishes no magnitude generation
before the action-record input and does not complete action playback.

Registered CTest `current_skill_effect_amount` passed in5.08 seconds after this
extension, covering five unittest methods, including invalid native identities
and amount types/ranges. It is not a five-formula completion count.

The corresponding native C2S command evidence in
`current-skill-command-20260919.md` identifies a selected-entry identity and
target masks in the qualified outgoing subset, not a client-calculated damage
amount. That is existing evidence, not a newly tested send path in this work.

## Separate Display Entry

A separately declared native caller stage begins at125866 on the SAME VM and
actor, with an explicit diagnostic skill definition pointer at actor+EC4.
125874 MOVSX reads actor+28A,125884 calls the original126120 formatter consumer,
and execution returns to125889 with the original stack restored. Intervening
game rendering between the store frontier and this caller is not executed.
This stage always reads slot zero; no claim is made that every effect slot is
displayed through this entry.

With physical-attack field+5E set to500, supplied amounts0,1,32767,32768,65535
produce the original CP950 label with signed decimal0,+1,+32767,-32768,-1.
The500 does not multiply or replace the supplied value. Original CRT formatting
executes, and writes remain on the private stack. Definition bytes and unrelated
actor bytes are unchanged. Synthetic definition/value inputs are diagnostics,
not native monster/skill magnitudes.

## Verification and Remaining Work

Three unittest methods passed in1.554 seconds, covering280 store cases, five
same-actor display cases and invalid record/type/slot/state inputs. The initial
harness bytes/bytearray mismatch was fixed; no native code was changed.

This replaces only the static caller/store portion of the prior
[field investigation](current-skill-effect-fields-20260920.md) with executable
evidence. It does NOT recover the upstream sender's magnitude calculation,
damage coefficients, hit/crit rates or element rules. No production database,
runtime packet sender, Lua formula or C++ combat policy changed.

```text
python -B -m unittest discover -s tests/research -p test_current_skill_effect_amount.py -v -f
```
