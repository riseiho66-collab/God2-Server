# Arrival1C identity correction — 2026-09-27

Urgent read-only follow-up to the role2 indoor cold-login→town failure. No
client/server/UI process, storage mutation, or shared runtime editing occurred.
Current `God2.exe` SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.

## Fixed1/4 was a fixture identity assumption

`004157F0` receives a DWORD, retains its low WORD, calls `00531C10`, and forms
`(config<<16)|(supplied&FFFF)` before queueing logical1C with four-byte payload.
`00531C10` returns1 exactly when globalWORD59DFD8=4 and WORD59DFDA=2; otherwise0.

The actual scene caller at `0046C4E2` tests the second transfer argument at
`[esp+44]`. If nonzero, `0046C4EA` reads world+1539683C (the local character ID),
pushes it at46C4F0, and calls4157F0 at46C4F7. Second argument zero skips the call.
The world initialization tail at465520/46552D and reload tail at465DE9/465DF2
also supply the local character ID. Thus receipt02000000 for current local
character2/config0 is native, as04000000 was native for fixturecharacter4.
The values2/4 do not describe different caller classes, scenes, or transfer types.

Earlier descriptions of a literal caller4 versus probe1 must be read as
fixture observations, not the native identity contract. The existing generic
ContextNotification parser was correct to preserve four raw bytes.

## Original-code verification

Tool: `tools/strike_lab/current_scene_arrival_identity_20260927.py`.
Artifact: `artifacts/research/current-scene-arrival-identity-20260927.json`.

Five byte spans match current PE exactly:157F0(49hex),131C10(1Dhex),
6C4E2(1Ahex),65520(12hex),65DE9(Ehex).

- Full original4157F0→531C10→132E0, no stubs: IDs1/2/4/3FFF × configs0/1
  produce exactly `1C + little-endian ID WORD + little-endian config WORD`.
- Native46C4E2 caller slice, no stubs: secondarg0 does not reach the producer;
  secondarg1 passes the local ID2 or4 unchanged.
- These are synthetic offline operands; no successful live transition is claimed.

## Server repair boundary

Only a session with an outstanding owned transfer may consume arrival. Require
the payload lowWORD to equal that session's existing local character identity
and highWORD to equal its accepted native configuration (currently0/1).
The current2A encoder already rejects identity0 or>3FFF; do not silently truncate
an unsupported database ID. Keep movement ready/pending/account/character and
persisted-baseline checks, registered source/destination and receipt completion.

Apply the same identity rule to qualified island/parent transfers; scene0 is
not a reason to require literal4. A first2E co-flushed with1C must be handled
only after the ring reset, using ordinary destination movement authorization.
An unsolicited1C or another character's ID must not release pending transfer.
No unconditional1/0 compatibility shortcut for arbitrary characters is supported
by this native source. Root owns runtime/test integration and live verification.
