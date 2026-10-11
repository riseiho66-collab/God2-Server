# Scene arrival — actual current-client acceptance, 2026-09-27

Native Traditional client emits logical 1C body `04 00 00 00`; Simplified emits
`04 00 01 00`. The server now matches byte 2 against the session's recovered
language configuration (0/1). A mismatched language/configuration remains rejected.
The previously qualified `01 00 00 00` receipt remains supported.

The existing pending owned-transfer gate still applies. Destination 71/72/78
records are restored after accepted arrival, including a first movement coflush;
old scene records are not projected during a pending transfer.

Exact candidate SHA256:
`f9278c6ace0fb1d926fd72930cd051aaee6a5284feb39d0fbd72e76a2675497a`

Actual current Taiwan client, hidden desktop against isolated own server:
`artifacts/playtests/private-native-blackbox-scene-route-20260927-10/run-result.json`

- Initial actor and level consumers accepted 71/72/78.
- Entered area 2/scene 15; destination actors accepted in 0.25 seconds.
- Immediately returned to scene 4; destination actors accepted in 0.235 seconds.
- Continued movement to 83/73 persisted with revision 12; both render commands
  remained active. Observation occurred during the client's walk animation.
- Input desktop was never changed; no memory writes or screenshots were used.
- Client, live database and source fixture were unchanged.

Earlier attempts clicked immediately or near supplied actor hitboxes and produced
no movement request after return. The accepted test clicks clear ground after a
0.6-second interval. This does not establish the client's exact input-gate duration.

All supplied actor coordinates, identities and level 27 are isolated test operands,
not original-world recovery. Production world placement/level tables remain empty.

Installed with `tools/operations/scene_arrival_release_20260927.py`. All saved
tables, client and configuration compare equal to backup; account count 4,
character count 3. Release backup and verification:
`artifacts/releases/scene-arrival-20260927/`. Managed listener restarted on 2592.
Owner-confirmed growth Lua is available in this binary but not activated in the
Application leveling route; test coverage does not claim gameplay activation.
