# Local logout, deletion and room-route release — 2026-09-27

## Installed result

Formal release: `artifacts/releases/native-logout-doors-20260927-03`.
Managed listener remains loopback port2592; installed executable SHA256:
`4d9ac6a4830e3f31f8637c89ae07359e51b31cf7fa6a6a45a1153164c07b9aaf`.
The code/config-only installation never replaced the live account database.
The release verification confirms all saved table schemas/rows unchanged and
the original client unchanged. The formal service was restarted only while idle.

* Genuine character logout sends C2S02/01; Session now returns S2C03 and drains
  the reply before closing. Source-qualified reasons0/1/2 are covered by the
  real-socket state regression. C2S66/S2C77 is pose synchronization, not logout.
* UI13 returned to the native server menu in1.922seconds. After the test clicked
  the previously selected server confirmation, a fresh character list arrived
  in2.828seconds total. The native application retains the selected server but
  requires confirmation; this is not automatic direct return to character choice.
* Native C2S19 deletion verifies the bound account, password, owned slot/name and
  inactive character lease. The transaction deletes owned descendants and the
  character, preserves other accounts/characters/catalogs, and rolls back on
  foreign-key failure. Its response and subsequent02/04→03 refresh are connected.
* UI13 deleted only the disposable fixture character in1.203seconds. The fresh
  list count became0 and the original client entered creation state21, its normal
  empty-account behavior. All nonfixture rows and source files remained unchanged.

## Room activation and qualification

Formal config enables23 town rooms and6 Kunlun rooms,38 entrance point pairs
and76 directed transitions. Town and Kunlun registries use distinct area/scene
keys, validated static navigation, explicit indoor kind2, S2C61, native C2S1C
arrival receipts, owner/pending/revision checks and saved destination restoration.
Town guides cannot spill into Kunlun indoor scene4. Multiplayer remains enabled.

All76 directed room transitions passed the service test, including cold restore,
selectors, ownership and pending/CAS gates. Actual current-client roundtrips and
cold login passed for town scenes5/7/9/30 and Kunlun scene4:10 of76 unique directed
points(13.2%). Repeat testing of the same point is not added to coverage. Final
candidate receipts cover town9/30 and Kunlun4; earlier unchanged route logic also
passed town5/7. A separate final-candidate two-client room5 test confirmed both
names/renderers, movement propagation and disconnected-peer removal. No screenshots,
injection, client memory writes or input-desktop switches were used.

The endpoint coordinates/navigation derive from the current client assets and
native projection/walk consumers. Ordered resource/scene joins and movement
activation retain the explicit CUSTOM-0052 policy; original server edge authority
has not been recovered. Three conflicting town resource joins stay excluded.

## Receipts

* `artifacts/playtests/private-logout-delete-20260927-13/run-result.json`
* `artifacts/playtests/private-room-presence-20260927-01/run-result.json`
* `artifacts/playtests/private-current-town-door-5-20260927-07/run-result.json`
* `artifacts/playtests/private-current-town-door-7-20260927-01/run-result.json`
* `artifacts/playtests/private-current-town-door-9-20260927-01/run-result.json`
* `artifacts/playtests/private-current-town-door-30-20260927-01/run-result.json`
* `artifacts/playtests/private-current-kunlun-door-4-20260927-02/run-result.json`
* `artifacts/releases/native-logout-doors-20260927-03/verification.json`

## Remaining scope

This is not all-world map completion. Island01 boundary routes have isolated
service tests but remain disabled in the formal multiplayer config. The blocked
original543,207 landing is not replaced with a guessed coordinate. The reciprocal
Kunlun–Island03 source points and full navigation are prepared under CUSTOM-0053
but are not integrated or activated. Other parent references and teleport menus
still need their packet/state/navigation/authority and actual-client qualification.
The1261 native coordinate-query joins are research coverage, not playable routes.

Scoped completion: logout/deletion functional acceptance100%; the76 registered
room directions' service/packet qualification100%; their unique native-client
point coverage13.2%. No whole-game completion percentage is inferred from these.
