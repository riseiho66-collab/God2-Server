# Native common actor initialization

## Boundary

`NativeWorldActor` extends the previously qualified world RoleDoll loader with
actual Cat and ProgramMsg row loading, startup localization, Petdrv bindings,
and the common actor initialization tail. This is an offline original-code
oracle. It does not launch the client, allocate a graphics device, qualify a
complete scene or change production session acceptance.

Pinned image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are hexadecimal RVAs relative to image base `400000`.
Existing legacy/world-entry/appearance evidence is reference context; these
new field results come from the pinned current client and its current assets.

## Native sources

| Source | Compressed SHA-256 | Decoded SHA-256 |
| --- | --- | --- |
| Data/Patch/Cat.csvZ | `9a1fad6c037cb276910b5d1a99a7c7755d8e723fa8dd4d5bc65c4d2c366d5bed` | `b518ebba78180078a6ac784c7c107d6563d72042eacb51ad0153305040dbe4c0` |
| Data2/Patch/Comm/message.csvZ | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` | `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8` |

Both sources have a 1 MiB compressed/decoded bound and identities checked
before row execution. Cat's actual path is under Data, not Data2. Original
`5E0F0` initializes the Cat object. Original tokenizer `51BE0` and row loader
`5E20A..5E329` load all eight CareerType rows, including three strings and five
numeric fields per 44-byte record. The count is nine because slot zero remains
empty. Other tables loaded by the full `5E150` path are not claimed here.

ProgramMsg is distinct from SystemMessage. Its exact 1080-record section is
located using the existing bounded structured section parser. An explicitly
allocated zeroed pointer array supplies storage; original `51BE0` and
`58CD4..58D67` parse IDs/text, allocate and copy each string, install pointers
and maintain the native count. Empty text records remain empty. This is the
row path of `58C90`, not the full message-file/startup lifecycle.
Input preserves the LF returned by text-mode fgets: `2530` opens the decoded
stream using `rt` at VA `582378`, and `51A90` passes its line to `51BE0`.
The oracle performs CRLF-to-LF translation only. Its initial removal of the
entire newline was caught by the all-message comparison and corrected; a
missing final delimiter makes the original tokenizer drop the last field.

Original `64A15..64A59` selects ProgramMsg IDs 482..485 using the pinned WORD
table at VA `58AB40`. Original `6506C..650E3` copies their actual localized
labels into Cat job-text slots 1..8, two career slots per label. The captured
global pointer array initially contains zeros; treating that as a completed
startup binding would incorrectly bypass real job text.

The already qualified component manager is copied to its actual world-inline
location, preserving real Drv and DrvDoll records and allocations. Original
Petdrv constructor `64200` and binding slice `64EC5..64EEB` establish its Drv
record pointer, DrvDoll pointer and count-minus-one. Actual `64280` reads Drv
column 4, the signed WORD hero vertical offset. Selector 27 in the retained
2A body produces **30**, replacing the old scalar-only oracle's zero stub.
All 92 source rows are checked against this original getter.

## Actor execution

Input is deliberately restricted to the retained 36-byte normal mounted body
family, B6=27, no secondary component selector, B32 WORD zero, valid area,
and the two already-qualified appearance variants 0..6. Name is a bounded
ASCII test name. These restrictions bound the oracle; they do not establish
all possible client records or a production name encoding.

1. Execute original `681CF..68290`: area check, flags and early actor writes.
2. **Do not execute `68290..68315`**. The scene/resource phase remains unjoined;
   its calls are not replaced with successful stubs. Supply the same resource
   manager pointer expected at the following boundary.
3. Execute continuous `68315..68851`, including actual `61270`, RoleDoll and
   mount loading, component setters, localized job text, packed field
   normalization, position/direction/name writes, `64280`, `68120` and `97FE0`.

The resulting actor references five genuine loaded resource slots and a native
FFFF absent secondary resource. Slots are observed cache indices for this load
order, not universal client constants. Repeated inputs reuse the five slots.
`68120/97FE0` clear the actual actor/UI ranges rather than bypassing them.
The native tail mutates its stack copy of packed input fields; immutable
caller bytes are not modified. Tests must not confuse normalized stack bytes
with the original transport body.

The renderer owner remains explicitly unqualified. Its input pointer is an
unmapped poison value `30000000`; the original pointer addition writes
`3A924D7C` to actor +4504, but no dereference is allowed or claimed. This is
not a functioning renderer binding. Exact stop hooks, inherited instruction
budgets, RX code, RW/NX fixture pages, native return/stack checks and file/SEH
guards remain active.

## Verification

Run `python -B tests/research/test_current_world_actor.py -v`.
The suite checks every Cat field and ProgramMsg string, localized pointer
bindings, all Drv offsets, original reset ranges and surrounding guards,
bounded input rejection, and C++ packet emission through original decoding
into this native actor path for all 49 appearance combinations, three local
IDs and four coordinate pairs (including scalar bounds, not walkability).
All six tests passed in 66.742 seconds after correcting the row newline
adapter. An initial assertion also incorrectly equated normalized actor +90
with raw selector +4590; the original `6858A/6859E` instructions write these
different representations, and the regression now checks each independently.

This does not promote `InWorld`, full renderer/animation acceptance, NPC
placement, combat rules, or complete playable-world status. The next world
integration boundary is the explicitly skipped scene phase and the live
renderer-owner chain, not another guessed packet or synthetic success flag.
