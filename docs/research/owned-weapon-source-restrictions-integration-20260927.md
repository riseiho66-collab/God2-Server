# Source-bound weapon sex restrictions and native refusal

## Integrated result

The authenticated owned28 route now checks the actual matching occupied bag
instance against the pinned source description. Current1259 WPN/TWP definitions
contain69 explicit TWP restrictions:35 male-only and34 female-only. Exact
CP950 phrases are read from definition+2E; ambiguous or unterminated descriptions
are not accepted as unrestricted. The underlying catalog validates the complete
pinned source fingerprint before lookup. No condition is inferred from an item
name, category, tooltip attack range or profession.

For restricted items, the character must belong to the session account and
have a valid persisted40-byte profile. Native FlowGui Boy/Girl button assets and
both17/1B producer paths prove sex profile33:0 male,1 female. Paired29 and packed38
must agree; no unknown sex default is used. Restrictions apply before transfer,
CAS updates or appearance mutation. Slot34 unequip is not prohibited by this
condition, so a previously saved incompatible weapon can still be removed.

Refusal returns exact native23-byte S2C02/SystemMessage27 with the trusted owned
item key. The16-byte name and final variant/opaque bytes are zero. The native
client resolves its local item name and displays `%s 無法使用或裝備。` in
channel4/colorFF80FF. This does not send fake occupied3B, clear pending or
change any gameplay value. The server pairing and activation policy is
CUSTOM-0048; native source wording, profile sex and presentation contract are
independently verified. This is not the complete original server equip rule.

## Actual own-server acceptance

Candidate SHA256:
`80f09ca536f7b58fc32abd03412f2d44cc40e3931edfab6a93dfbe33a52b4f60`.

`artifacts/playtests/private-weapon-rejection-20260927-02` accepted a real female
client4 double-clicking male-only TWP19071 in owned bag2. Both native visible
and archive rings gain one channel4/colorFF80FF entry with the actual source
name `神裝-嗜血殺戮 無法使用或裝備。`. All50 native slots,31 saved cells/full
metadata/revisions, HP/MP, four attack/defense values, appearance revision1 and
battle reservations/settlements/checkpoints remain unchanged. Subsequent legal
WPN1 equip0→34 and unequip34→0 succeed, with appearance revisions2/3; restricted
slot2 remains unchanged. The20-byte TWP/WPN operands are explicitly synthetic,
not native instance generation or balanced production item grants.

`artifacts/playtests/private-weapon-peer-20260927-04` reruns the complete hidden
two-client acceptance on this exact candidate: four equips1/2/0/1, matching
owner/peer source resource handles, peer reconnect/full6F, movement and clocks.
Both runs preserve source DB, client files and input desktop; all owned
processes close and2598 is released. No screenshots/pixel claim or actual God
fixture qualification is included.

Native evidence:32 sex slices+160 invalid profile cases per interpreter mode;
16 complete native refusal flows+4 guard cases; four fresh TWP hover/double-click
returns in normal and optimized modes, with original source restriction/name
formatting and no game-callee stubs. The fresh TWP fixture does not infer legal
stats from its zero tail. Tools/reports are separate bounded evidence.

## Test runner repair and qualification

CTest's existing ENVIRONMENT property overwrote the shell's candidate variable
with historical weapon/appearance EXEs. The newly added TCP sex-refusal check
timed out on that old executable. Removing the two overrides and using the
managed executable as the default fixes this concrete test selection problem.
The suites now print the tested path and SHA256. Both TCP suites then pass on
the exact candidate above, including atomic whole-instance/DA commit, rejection
without mutation, wrong key/mixed frame rejection and server restart. Eight
focused CTest checks pass. Preserve the old failures as evidence; a successful
run against a stale binary is not same-candidate qualification.

The previous peer report's same-candidate TCP wording was unsupported by those
CTest overrides. Its actual hidden peer test was correctly candidate-pinned.
This round supplies the corrected, explicit-hash TCP recheck for the current
formal candidate. See release `same-candidate-tcp.log`.

## Formal release and remaining scope

Release `artifacts/releases/owned-weapon-source-restrictions-20260927-01` is
INSTALLED_GATED, schema29, same accepted candidate, service PID25644/listen2592.
There were no connected players during update. The online backup, pre-existing
tables, trigger/index definitions, config and client are preserved; appearance
rows0. The installed weapon/appearance options remain disabled because full
original item-to-world mapping, legal instance generation, level/profession
requirements and final attack/defense/combat formulas remain unrecovered.

Overall playable completion remains approximately11%, an estimate rather than
measured full packet coverage. This round closes a real source eligibility and
native refusal route; it does not claim all equipment gameplay completed.
