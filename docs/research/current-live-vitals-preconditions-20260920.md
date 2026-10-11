# Live Vitals Receiver Prerequisite Failure

## Experiment

Opt-in `--probe-native-vitals` follows the successful diagnostic constructor
and phase0 scanner. It would call original118A90 with an immutable121-byte88
record: explicit test HP1000+slot and MP50+slot for14 positions, other bytes0.
These values are diagnostic, not native stats or balance-approved designs.
There is no listener, socket, database mutation or production activation.
The probe checks all28 type0 actors' current/max vitals before/after and requires
the original batch/cleanup stages and RET4. None of this has passed live yet.

## Actual Evidence

`artifacts/runs/offline-vitals-live-20260920-01`, PID8476, reached118A90 after
the original constructor and phase scanner returned. It then faulted at118B0B:
`cmp eax,[ecx]`, ECX=0, EAX=FFFF. The original consumer loaded the null local
role pointer from battle+14. Batch writer12D360 was not reached. An observer
bug initially masked classification as TOOL_ERROR: unclassified native stops
have indexNone, which the new interval-based handler compared with integers.
That handler now type-checks before comparison; the raw native fault remains
preserved in the first report. The failed process was terminated, never resumed
with a pointer patch or fabricated successful return.

Run02, PID6932, added a read-only role preflight. It completes constructor and
phase probes but terminates before the receiver with
`NATIVE_VITALS_ROLE_BINDING_MISSING`, error=null. No diagnostic88 is invoked in
that run. Both owned PIDs were confirmed absent after the runners exited.

## Original Binding, Not A Substitute Pointer

Pinned1112C0's normal battle-session initializer reads descriptor+10 at111323
and stores it into battle+14 at111326. Its normal world caller passes the
stack descriptor at6582B and calls1112C0 at65836. The previous text-only
initializer11F920 intentionally did not execute this full session setup.
Thus constructor/phase success cannot certify receiver readiness. Next work
must trace the descriptor's role producer and normal battle-entry prerequisites;
do not write an arbitrary role pointer or local-slotFF to bypass this branch.

## Verification

Ten offline-monster regression tests pass, including explicit121-byte diagnostic
layout, thunk ABI/trap, and indexNone handling. The new receiver probe is kept
disabled by default and requires explicit phase/constructor flags. Success is
reserved for `NATIVE_VITALS_RECEIVER_RETURNED`; neither recorded run has it.
This is a verified live prerequisite failure, not a server crash or a recovered
formula. No playable-world percentage is implied.

## Role Producer Qualified

`world_descriptor_prefix()` executes original655E0..65638, stopping before
state dispatch. After the original stack adjustment and four saved registers,
frame=entryESP-A24 and descriptor=frame+1C. The seven DWORDs are:

1. Application from world+A7E05C4.
2. Event/context address frame+238.
3. Embedded world UI world+A7F2F6C.
4. Owner from world+AA3647C.
5. Embedded role address world+1539683C, produced by6560F's LEA.
6. Catalog from world+AA36480.
7. Embedded address world+15383410.

The regression passes this exact native-produced descriptor, unchanged, to a
separate original1112C0 entry and executes through11132C. Battle+14 receives
the role address; +20/+24/+2C receive the corresponding descriptor fields.
Image bytes stay unchanged. This is two explicit entries, not continuous world
state4 execution or completion of1112C0. All20 battle-entry tests pass.

Fresh run `offline-vitals-live-20260920-03` (PID9100) records the computed source
address624666716 and a32-byte raw snapshot with SHA256
f7c16f8b1423c5a97d740dfd84f848afeb7f293b9416f0e38b8c55a103855317.
The source is readable while battle+14 remains0 and local slot is0. No source
field is relabeled native combat stats; this is an offline, not logged-in role.
The read-only preflight again stops before invoking88. Entry/timer restoration
and unchanged disk executable are reported; PID9100 is absent after completion.

The actionable missing path is full normal battle-session initialization with
its event context and existing owners, not an88 HP/MP format adjustment. Do not
transfer the source pointer by a direct memory write: other1112C0 side effects
remain prerequisites for real gameplay. No additional receiver fault was run.
