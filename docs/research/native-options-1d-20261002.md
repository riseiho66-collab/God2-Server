# Native1D local-options notification —2026-10-02

## Qualified source and actual route

Captured image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Native497D80 reads its caller's pointer and queues opcode1D plus exactly2 bytes
through497D8F ->4132E0. Callers4F4B50 and4C7520 change local option bits at
the object referenced by UI+86888,+449C **before** queuing the notification.
There is no client-supplied player identity. Do not confuse this three-byte
C2S record with the unrelated173-byte native S2C1D record.

RecoveredWorldRecords now preserves both raw bytes, including reserved/high
bits, and rejects truncation/unknown suffixes before dispatch. Application
routes the typed standalone record to RecoveredWorldService; authenticated,
owned, ready-world admission emits no reply and does not mutate character or
chat state. Logged flags allow actual native UI output to be checked.

Wire/toggle masks are NATIVE_VERIFIED; admission/no-server-mutation is
**CUSTOM-0060**. This does not recover original server preference storage,
social restrictions or any extra original response. Battle, mixed/coalesced
and premature-selection flows remain unqualified and are rejected by this
bounded candidate policy. No claim of complete native options semantics.

## Native and client verification

-20 executed native producer cases: zero, all bits, patterns and each one-bit
  WORD. Queue boundary is isolated, payload width/bytes/owner pointer and stack
  balance verified. Native receive table independently confirms S2C1D173.
- C++ parser roundtrips all65536 raw WORD values. Truncation and unsupported
  suffixes rejected. World service rejects mixed movement, battle and premature
  selection; qualified admission changes no movement/battle callback.
- Own-server TCP sends five different flag values, sees no fabricated reply,
  preserves saved tables and successfully sends native66 afterward.
- Hidden original-client TW run02 and CN run03 each use native Ctrl+H menu,
  select category26/action27, then toggle actual options controls4..8 twice.
  Masks1/4/2/8/100 produce ten1D notices per client, each exact raw WORD matching
  client memory; original bits restored after each pair. Server receives20
  actual UI-originating notices total. No packet injection or memory write.
- Current client is
  `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
  Producer/UI code bytes match captured native regions; temporary images only
  change loopback port and use isolated950/936 LE profiles. Client/config/source
  fixture hashes stayed unchanged. Hidden desktop never becomes input desktop.
  No screenshots or rendered-pixel acceptance claimed.
- Main menu labels0..4 are noninteractive. Run01's incorrect control selection
  was rejected by the test; native4A6D90 identified the real22..26 category and
  27..42 action buttons. Runs02/03 passed. Original-client binaries unchanged.

Receipts:
`artifacts/playtests/private-options-1d-20261002-02/run-result.json`,
`artifacts/playtests/private-options-1d-20261002-03/run-result.json`.

Candidate gate:4 TCP cases (options, existing pose lifecycle/replay and bilingual
chat/movement),3 C++ targets,1 inventory test;8/8 passed. Frozen-chat baseline
passed unchanged. This pass rate is not whole-game packet completion.

## Installed scope

Executable-only release installed on2026-10-02; formal server PID26244 listens
on127.0.0.1:2592. SHA256:
`72d5d6fb72a72cc80323cf81015743a0e1b4396562a46a874edb5c3224051a75`.
Cloned startup migration and exact staged/live saved-row comparison show zero
schema/save changes. Live client/config unchanged; no connected players during
restart. Existing save-preserving release lifecycle and rollback executable
retained in `artifacts/releases/native-options-1d-20261002/deployment/`.
All12 test-owned temporary EXE/profile files removed after hash/process checks.

World parser inventory is now28 opcodes (was27). S2C receive-size contracts
remain230 fixed +22 variable. Neither is a full-game functional denominator;
overall completion percentage remains unknown.
