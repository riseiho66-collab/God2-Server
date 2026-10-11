# Current peer secondary role text through native6F

## Source contract

Current client SHA256 is
`9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336`.
The retained native image is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are hexadecimal; field byte offsets explicitly marked decimal
refer to the81-byte logical record including its opcode.

S2C6F has a native81-byte length leaf and dispatches to `4695C8`. Its second
16-byte string begins at logical offset45 decimal (`0x2D`, body`+0x2C`). The
original constructor `4FC2FA..4FC31B` copies it to remote actor`+0x14` (20
decimal), and display creation at `4FD435..4FD442` passes it to `509E70`, the
same secondary renderer field`+0x81` used by local S2C23. Primary and third
strings are separate adjacent cells. Native copies are unbounded, so server
fields require a NUL within16 bytes and canonical zero tail.

On an already present identity, `4FB460` executes `4FC960` lookup, `4FC560`
removal and `4FC1C0` reconstruction. This replaces the visible text but also
clears the movement/interpolation queue through `4FCC60`. It is a complete
native actor replacement, not a text-only setter. The server must use the
latest committed position, pose and appearance in that6F. The targeted scan of
direct `509E70` callers found no separate qualified peer text-update opcode;
this implementation does not invent one.

## Current consumer execution

`tools/strike_lab/current_peer_role_text_20260930.py` uses the existing
resource-backed original world/display oracle and its documented OS/CRT
adapters. It executes the full6F consumer including original resource lookup,
remote pool replacement, constructor and secondary renderer writes. The current
client has owner-approved frozen streamer/font wrappers: the old mapped image
differs at primary renderer call `509D1E -> 70FB61`. The new oracle therefore
loads the actual current PE `.text`, `.imefix`, `.stream` and `.fontcfg` into
its offline VM while preserving initialized import/data bindings. Every executed
instruction in those sections is checked against the pinned current PE. No
current game hook is skipped or replaced, and no client file is edited.

`artifacts/reports/peer-role-text-20260930/native.json` reports PASS over5832
distinct current instructions. Cases cover existing identity,15-byte text,
shorter replacement, clear, CJK, an untouched neighboring actor, a queued step,
replacement with latest committed position, the next5E step, and remove then
fresh6F insertion. The queued step is intentionally cleared by native6F; saved
position does not regress and a subsequent movement target is accepted. Only
appearance resource handles/variants, packed components and scalar fields are
asserted unchanged. Internal component runtime bookkeeping is not an immutable
appearance record. Display buffers are verified; this oracle has no real
graphics device or live client.

## Common source-language flag and native conversion

Bit25 of the first body DWORD (`logical[4]&2`) is the common language flag for
all three6F strings:0 is CP950,1 is CP936. `4695F6..469765` converts all three
when that flag differs from the receiver language. Re-encoding only secondary
bytes into the receiver page while retaining a different source flag would
mislabel the packet. The new helper instead writes secondary bytes in the
unchanged6F source page and predicts the native receiver's conversion.

The original functions use these exact Windows NLS pipelines:

| Source → recipient | Native function | Operations |
| --- | --- | --- |
| CP950 → CP936 | `52F170` | MultiByteToWideChar950; WideCharToMultiByte936; LCMapStringA(locale804, simplified flag02000000). |
| CP936 → CP950 | `52F330` | LCMapStringA(locale804, traditional flag04000000) in936; MultiByteToWideChar936; WideCharToMultiByte950. |

The original allows default/best-fit conversion and fixed intermediate buffer
capacities. `NativePeerRoleTextCodec` duplicates the order and predicts those
capacities, but requires exact encoding roundtrips and no substitution. Its
ANSI LCMap result must equal the Unicode LCMap result encoded strictly in936.
Results longer than15 bytes or unrepresentable source/recipient values are
suppressed for that projection; only secondary is cleared and stored data is
preserved. Intended native simplified/traditional script conversion is allowed.
No common chat, primary name, IME or existing appearance codec is changed.

`tools/strike_lab/current_peer_role_text_codec_20260930.py` executes unchanged
original52F170/52F330 plus original531C30. Captured OS import boundaries marshal
bounded buffers to the host's actual Windows NLS APIs. No game callee or mapping
result is mocked. Its15 vectors/147 distinct native instructions pass, including
神仙, 測試↔测试, AB mixed text,15-byte boundaries, 繁體/简体 and 专→專. Receipt:
`artifacts/reports/peer-role-text-20260930/codec-native.json`. The conversion
feature globals are explicit enabled test inputs; these are offline results.

## Additive helpers and integration boundary

- `RecoveredRemoteRoleText::with_source_text` changes only logical45..60.
  `source_codepage` reads the unchanged common language bit.
- `RecoveredPeerRoleText::per_recipient` first uses the existing strict owned
  row projection into that source page, then validates the native receiver
  conversion. It returns source6F, predicted receiver bytes, and display status.
- `NativePeerRoleTextCodec` is a new isolated codec; the qualified production
  implementation uses Windows NLS. Other operating systems admit unchanged
  ASCII across pages until matching native NLS behavior is qualified there.
- `tests/test_peer_role_text.cpp` checks exact preservation outside secondary,
  canonical fields, all lengths0..15, both source/recipient pages, CJK native
  results, no substitution, unsupported stored source projection and immutable
  saves. Its standalone MSVC C++20 build and execution pass. The registered Release CTest `peer_role_text` also passes (1/1, 0.04 seconds).

CUSTOM-0056 covers ownership, persistence, suppression and broadcast policy.
The native contract establishes packet/display behavior, not original server
moderation or durability rules. Parent integration owns shared visibility plans,
world-entry cache projection and precommit preparation. Review identified that
initial cached6F must include the source projection (otherwise clearing an
initial saved label could appear unchanged) and that per-recipient preparation
must complete before database commit. Both findings were corrected in the shared Application integration and independently rechecked: initial presence includes the owned source-page field, and the save callback prepares every recipient before commit; the post-commit path sends those prepared bytes directly.

## Real-client gate

`tools/strike_lab/private_peer_role_text_20260930.py` prepares two unique
current port-only client copies with separate per-executable TW/CN Locale
Emulator profiles, using the already supported launcher pathway. It uses an
owned hidden desktop, disposable SQLite fixture, read-only native fields and
window-local input. Global locale settings, launcher settings and the deployed
client stay unchanged. Planned cases cover seeded CJK both directions, ordinary
UI clear and15-byte edit, existing peer, later movement, fresh observer and
owner reconnect. The actual-client results below close these cases within their
recorded candidate and source-language scopes.


## Completed current-client acceptance and stop record

Two complete runs passed using the current `9be38ef8...` client with only the
isolated port changed. The TW and CN per-image profiles were actually observed
as native language words `04000100` and `04000200`. These are normal client UI
and read-only native text/render-buffer checks; no rendered-pixel claim is made.

| Receipt | Source / receiving page | Candidate SHA256 | Receipt SHA256 | Result |
| --- | --- | --- | --- | --- |
| `artifacts/playtests/private-peer-role-text-20260930-02/run-result.json` | 950 → 936 | `81bcf822a26c36076c5fdd51b2b3bbf7f465136048ea5f080dfd0673d1410874` | `7628a34c99cdccfab4672659473e9460ae5df148912ec15f7fc81c1edbf06fbf` | PASS |
| `artifacts/playtests/private-peer-role-text-20260930-04/run-result.json` | 936 → 950 | `b94ea3dda7bd8c5de8023f2dbaa8be7391d1f72f0b3feac66d2cabca84effc2c` | `c873ea909b1225ebe912cfdf65f45f2323a1b2ebe255787b24f10b1581f055d2` | PASS |

Both runs prove seeded CJK owner restoration and peer conversion (測試 / 测试,
and 神仙), ordinary UI clear then a 15-byte `PeerNativeProof` edit, revision 8
then 9 persistence, existing observer refresh, a fresh observer process, and a
cold owner reconnect. The actor moves from (126,126) to (127,126) before the
edits; each repeated 6F preserves that latest position, primary/third names,
appearance handles/variants and status/scalars. The next move to (128,126)
succeeds, and both reconnect checks retain it. Unrelated database tables/rows
and the role rows across reconnect remain unchanged.

All accepted receipts report unchanged source client/profile, source fixture
DB/config, launcher settings, global LE config/runtime, candidate and private
client/profile hashes. Each hidden desktop remains distinct from `Default`;
input desktop is unchanged. Every owned client, runner and candidate server is
closed. This lane did not modify or restart the managed production service.

### Candidate difference and honest scope

The complete 950-source run used `81bcf822...`; the complete 936-source run used
final `b94ea3dd...`. They are not claimed as two runs of the same binary. The
parent's intervening integration fix added two conditional scalar-projection
skips in `Application.cpp` (currently lines 1683 and 2159):
`config.owned_teleport_gem_enabled && slot.item_id==RecoveredTeleportGem::item_id`.
The peer fixtures omit that feature and `Config.h` defaults it to false, so the
new branch is inactive in these fixtures. The parent accepted the final-binary
936-source regression plus the complete preceding 950-source result and
directed no redundant fifth run because the owner requested this round stop.

### Rejected attempts retained

Run `01` is not accepted: posting only WM_CHAR Backspace did not edit the
native input; server revision remained 7. The private driver now uses normal
window-local Backspace keydown/up and asserts the actual native input buffer
before confirming. No game client or IME code changed.

Run `03` is not accepted: the last cold owner startup never sent a new login
connection, after its CJK/UI/movement/fresh-observer cases had passed. The driver
now bounds each login transition by a new account-bound event for the expected
identity on the isolated server, plus exact owned image/window checks. The
final run `04` passes both cold logins with these checks. Failed attempts also
closed all private processes and preserved source hashes. No further retry,
new feature, research lane or service action follows this record.
