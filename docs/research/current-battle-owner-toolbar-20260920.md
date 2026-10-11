# Retained Owner Toolbar Prefix

Pinned native image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
RVA=file offset, base400000 hexadecimal.

## Resource Prerequisite

B11E9 calls106C70 with resource group9, action5, control17 decimal. The existing
preload set lacked group9. The original FieldComm3 row9 resolves to
`data3/flow/speceff2.romz`,313016 compressed bytes and1156346 decoded bytes.

Raw SHA256: `6867c8639cafafb95077de1a583d737262f4f2f50b98e1ce26b4c49a1e3502b8`.
Decoded SHA256: `6694fbe66c07e31553ae50a11757ce8a6660b1f3024846534711f3d223b33739`.

This slot is added to the existing original preload iterations81620..8167B.
The native reader/ROM parser still loads the asset into the separate world bank;
no table entry or game-function return is fabricated. The focused resource
regression verifies source row binding, parser input and loaded bank slot.

The nested7E800 channel-interface producer also requires original FieldComm3
group32: `data3/flow/channelswitch.romz`,311821 compressed/587983 decoded bytes.
Raw SHA256 `27e3bf32fc6638635fb5d95eba017dc18baf16816495bee78e9301d80fdd97c7`;
decoded SHA256 `37192f309f3a7efcab63cd99d6522b78b9cc23ec83cdfc58d9b96fa1a1755b06`.
It is loaded by the same source-indexed native preload loop.

## Continuation Boundary

The first integration run reached CRT14CF19 with a null format pointer. The
mapped image's toolbar text globals are initially zero. Original B0AF0's prefix
binds them from the owner's catalog at+ CFF70, which is separate from the battle
message catalog in this fixture. `prepare_owner_toolbar_messages` now allocates
the fresh ProgramMsg pointer array in that owner catalog and runs the existing
native51BE0/58CD4 row parser for all1080 pinned source rows. It then executes
B0AF0..B0BEE, including the original pointer bindings and label copies, then
the complete native B3A10..B3A61 binder for five further toolbar captions. Seventeen
bound strings are compared with the independently loaded battle ProgramMsg
strings. Parser scratch, the pending main stack and CPU context are restored;
the native map rows must still validate. This is an explicit original producer
prefix, not execution of the entire owner constructor or a live packet receipt.

The oracle originally maps the image read/execute. The pinned PE places1B7000
inside writable .data. The binding stage marks only that page read/write,
non-executable, and guards native writes to the seventeen pointer slots and eight
fixed51-byte label buffers. The initial write-protection failure atB0B2F is not
handled by patching or skipping the store. No instruction page is made writable.

The second null-format failure after the first binder came from a distinct
five-entry array at1B7550..1B7563. B12B0 passes the1B7560 entry throughB2160
to1077C0. B3A10 is its original producer, using IDs at192580..192589. Those
values are now checked against the same pinned ProgramMsg source, not assigned
empty-string fallbacks. Channel UI defaults beyond these explicit producers are
still diagnostic fixture state, not proof of the complete normal owner startup.

`continue_owner_toolbar` enters at the retained81F0D after the real C3080 return.
The normal caller passes character+90 toB0D20. The continuation follows the actual
control creation, B12B0 and7E800 paths, stopping before E72D0 rather than executing
its as-yet unqualified character-data consumer.

The expected pending call has ESP=SP-8C and stack words
`(BASE+B129A, CHARACTER_ROOT+90, 0, 0)`. This is not a completed B0D20 call.
The pending1112C0 invocation remains the original single entry. Native control
calls are counted; owner/mouse/display changes reconstruct from observed writes,
while character bytes, native map records and the separate battle renderer remain
unchanged. The normal OS rectangle adapters remain part of this offline test.

After text binding, execution exposed an unconstructed control-cache pointer
at owner+232EBC. Original owner allocation80FDB requests3AE54 bytes;
81024 calls85DF0 with the owner argument, and81029 publishes its returned
pointer. `prepare_owner_toolbar_cache` allocates that exact bounded storage,
poisons it, executes the full original85DF0 constructor (including nested
control constructors), and executes the original81029 store. Constructor writes
must stay within the object/owner slot/stack/SEH; all object bytes reconstruct
from those writes. The pending main CPU/stack is restored afterwards. This is
explicit prerequisite construction, not the full normal owner constructor.
The subsequent toolbar trace includes and accounts for cache-object changes.

The next integration run completed this cache construction but stopped at7EB65:
the read of `[owner+39DE8]+67E8` followed descriptor slot11, still deliberately
poisoned in the fixture. The pinned original producer chain is:

- 6447E/64489 constructs the main object's embedded container at+153D5FD8
  using5FEB0, which calls5FEC0 and returns `this`.
- 65267/6526F resets the same container;652FF stores its pointer at stack+50,
  slot11 of the descriptor starting at stack+24. 65323 calls817C0.
- 81811..8181A copies descriptor+2C to owner+39DE8.
- 7EB5C/7EB65 consumes that pointer and the container count at+67E8.

`prepare_owner_toolbar_channel` provides relocated bounded67F4-byte storage,
executes the full native5FEB0 constructor, and executes the original descriptor
load/store. This models the native empty container, not existing player chat
history. Every constructor byte is reconstructed from native writes; the result
must be all zero, including counts+67E8/+67EC/+67F0. Pending CPU/stack are restored.
Toolbar execution is required to leave this source container unchanged.
The complete owning main-object constructor is not executed by this fixture.

## Limits

## Verification Result

Registered `current_battle_owner_toolbar` CTest passed1/1 in316.26 seconds on
2026-09-20, with both unittest methods passing (313.043 seconds). The fixture
also invokes the preceding retained map completion assertions. This establishes
the expected E72D0 pending call, single original1112C0 entry, source resource
presence, seventeen message bindings, exact tracked object writes, unchanged
channel source, map records, character bytes and separate battle renderer.
The earlier326.03-second failure at7EB65 is superseded by this completed run;
it was a missing fixture prerequisite, not evidence of client packet corruption.

## Remaining Character Consumer

E72D0 calls AC070 with the supplied character data; that call is not executed by
this continuation. Other owner81C20 calls and full battle initializer return,
live client acceptance, combat policy and original monster values remain open.
This change adds no production gameplay rules, runtime packets or database data.

Static next-boundary evidence only: AC07B reads argument+60 andAC08A reads
argument+68; with argument=character+90 these are character+F0 and+F8.
The routine also references argument+5C/+64 (character+EC/+F4). Nonzero capacity
branches include clamping and UI ratios. The field provenance and execution of
that consumer must be validated separately; this run stops before it and does
not supply invented capacity values to force a branch.

```text
ctest --test-dir build -C Release -R '^current_battle_owner_(toolbar|resources)$' --output-on-failure
```
