# CN native6F tag1 text projection, 2026-10-07

Catalog44 connected ordinary CN peer5C identity to the current private6F
incarnation for raw tag0 names. This round recovers the alternate native helper
and adds a conditional success-only Windows NLS source projection for tag1.
No APIs/native helpers, binaries, tests, build, game/Lua, production database,
resource decoder or deployment were run. The C++ implementation remains source
for later full testing; Python only decodes/copies pinned PE bytes and accounts
for sources. No original client code or fonts change.

## Primary native behavior

In the pinned CN executable,00405A30 returns0. The6F first body DWORD bit25
selects the string branch, independently of player presentation preference.
When bit25==1 and self0, the world branch calls0053F880 first on logical29.
Only a nonzero first result allows copying it and invoking the helper on45/61;
the second/third results are not checked before copying the reused temporary.
That failure/stale-buffer behavior is not a safe success contract and remains
unconnected. Output expansion across a16-byte region can affect the subsequent
source string; the new success projection excludes that overlap rather than
inventing output or silently clipping identity bytes.

0053F880 first requires nonzero008A4594 and00405A40 (loads008AEEB8). Its exact
successful API sequence and parameters are:

1. MultiByteToWideChar(CP936, flags0, original, -1, NULL,0), returning a wide
   count including NUL.
2. LCMapStringA(locale0804, flag04000000, original,-1, local1024-byte buffer,
   original wide count*2). It uses the ANSI function and locale data.
3. MultiByteToWideChar(CP936,flags0,mapped,-1,local1024-WCHAR buffer,
   **the original wide count**, not a newly guessed output capacity).
4. WideCharToMultiByte(CP950,flags0,wide,-1,NULL,0,NULL,NULL), then the same
   API with the queried destination length and NULL default-char pointers.

The reverse0053F5E0 uses CP950 decode ->CP936 encode ->LCMapStringA0804/
02000000. Neither helper is equivalent to the shared strict display codec or
an OpenCC dictionary. Successful default-character substitution is native API
behavior and is not removed by a strict substitute encoder. Failed conversion
can clear008A4594; disabled paths and uninitialized/stale output do not create
a qualified name. All flags and codepages are copied from primary calls.

00405A60 initializes008AEEB8 from GetVersionExA: successful NT platform2 and
major>=5 sets1; failure/other platform/older version sets0. It is a Unicode
capability gate, not a codepage, region or preference detector. The packed PE
initial008A4594 and later failure writes remain distinct from current runtime
state. No initial value or old receipt is reused as actual current native state.

Important scope clarification: self-tag0 alone does **not** prove CP936.
0053F880's destination is CP950 even in this CN executable. The imported
upstream CnTextProfile explicitly selects936/tag0 for its unhosted adapter;
that is an adapter profile requiring actual receiver qualification, not a
derivation from the native bit. The current source keeps explicit CP936 input/
body edges unchanged while correcting that overbroad code comment. Credential,
world snapshots, raw names and other fields require their own primary format
evidence; the helper is not used to silently change their encoding baseline.

## Actual source increment

New CnNativeActorText::prepare calls the native successful Windows API sequence
in source, in the original three-field order, with native capacities/flags.
It requires a real nonzero native text revision, actual nonzero capability and
latch values, and a mandatory receiver-environment qualifier. The actual owner
must prove the predicting Windows NLS/API environment matches that recipient
and that its state/revision remains current; executable identity and this
server's OS do not prove it. Non-Windows targets have no substitute projector.
During this phase, prepare is not executed and no predictor result is accepted.

Only successful terminated outputs of at most15 bytes are retained. Failed/
disabled/overflow/cross-field overwrite branches return no candidate and remain
pending exact native owners. No native latch/error UI is simulated and no
default name, dictionary fallback, success reply or identity truncation exists.
Projection construction is private; it owns all three predicted strings, exact
raw input regions and actual state. current checks low12 identity/tag/all three
raw regions plus actual environment, while ordinary position changes are
independent of text. This is predicted native state, never observed memory.

SharedActorVisibility::Mainland can retain that qualified projection with its
actual submitted6F. Existing show/send behavior is unchanged. Its chat query
uses the raw tag0 name or the qualified tag1 expected name. It copies the native
snapshot before invoking actual-owner callbacks and rechecks the private
incarnation/position afterward, so a callback cannot leave a borrowed map entry
or stale replacement token in use. The existing SharedNativeChat ordinary peer
check then requires the exact current expected-name prefix and native identity.
The original sent6F bytes, account identity and native name lookup remain intact.
Name prediction is separate from body-only user-authorized Chinese presentation.

The actual WorldOwner must still qualify full5C header, text/prefix codepage,
body range, downstream destination/backing-buffer state and real audience.
The CP950 helper result is not blindly converted into a CP936 name or treated
as permission to assemble a mixed-encoding native packet. Actual current text
environment and native rendered-client acceptance remain outstanding.

Two new C++ files, three modified C++ files (one comment-only clarification)
and one catalog-tool update. No extra owner chain/phase binding/opcode or
completed route. Catalog45/report retain all earlier sealed evidence; only the
live source/ledger gains this bounded increment. Whole-game denominator and
percentage remain unknown. Next recover the full5C issuance/audience and
remaining name/state/format variants; do not promote this prediction into
production before all routes and the later full testing/release phase.
