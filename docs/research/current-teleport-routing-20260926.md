# Native teleport selection transport route — 2026-09-26

The unpacked-client reconstruction now resides independently at
`C:/Users/risei/Desktop/God2-解殼EXE原始碼重建` per the owner's organization request.
The former `God2/Client-Reconstruction` directory was moved in full. Its README
records backup, analysis, rebuild, and native comparison evidence.

`RecoveredWorldRecords` now recognizes exact five-byte C2S 99/A9 selections
using `RecoveredTeleport::decode_selection`. `RecoveredWorldService` has an
optional sixth `Teleport` callback accepting a Selection. It accepts only one
standalone selection in InWorld or CharacterSelected with completed world tail,
and requires account/character identity. Mixed actions, battle, incomplete entry,
and absent authority callback are rejected. The opaque final byte is preserved.

Focused records/service CTests pass 2/2; the complete god2-server target builds.
Tests cover 2,304 parser combinations, 768 callback cases, boundary states and
absent callback. This is TRANSPORT_ROUTE, not authoritative gameplay or live
client acceptance. Application has no teleport authority callback installed;
the running server binary was not replaced during this work.

The C2S 6D zero-control record remains separate and sends no fabricated response.
Current caller evidence includes inventory/equipment updates and UI callbacks;
it does not justify automatically pairing that request with S2C 6D teleport UI.
See current-teleport-ui-20260926.md and current-teleport-authority-20260926.md.

Outstanding integration requirements: prove the opening trigger, map the
server-supplied context to the authoritative offer, establish actual available
destinations/arrival coordinates, costs/cooldown/ownership, and verify a current
client using an isolated own server. New packet syntax alone does not satisfy
those requirements. Do not invent a cooldown menu to mean unavailable.
