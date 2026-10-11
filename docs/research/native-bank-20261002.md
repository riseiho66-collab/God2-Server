# Native bank money route

This round connects original C2S39/61/62 and S2C46/47/27 to the owned
C++20/SQLite server. Native wire behavior and CUSTOM-0064 authority are
separate. The current candidate is `candidate-02/god2-server.exe`, SHA256
`090de7764db203f70d10fa0d2e771f962063ca0f7069d48b486d19547ec72a92`.
The money protocol is installed on the managed server (port2592, PID19452
at deployment). Formal qualified bank points remain zero, so this is not a
claim that a correctly placed banker is reachable on formal maps.
Release evidence: `artifacts/releases/native-bank-20261002/manifest.json`
and `deployment/release.json`. Existing schema/history/saved rows are exact;
only the three empty bank tables and two indices were added. Client/config
and frozen-chat baseline remain unchanged. Code or parser count alone does
not prove playable banking.

## Original machine evidence

`current_bank_20261002.py` executes the pinned original x86 image. Current
client intervals must match; external queue/drawing helpers are declared
stubs. 78/78 cases pass, including bank item-direction research. This does
not mean 78 implemented banking features or 78 live-client tests.

- 497390/497450 emit61/62, logical9: amount DWORD at1, target WORD at5,
  opaque/uninitialized WORD at7. Preserve the opaque bytes; never use them
  for authority or a request ID.
- 496860 emits39, logical5: target WORD at1, window-kind WORD at3.
  Ordinary bank471390 closes locally and sends kind1. No S2C close ACK is
  required.49 is another storage/modal path, **not a bank close ACK**.
- S2C46 logical13, mode0 at logical11, opens the bank with a DWORD target.
  The server only admits WORD-representable targets matching C2S61/62.
- S2C47 logical9 supplies absolute bank DWORD at1; trailing DWORD unused.
- S2C27 logical5 supplies absolute purse DWORD at1, consumed by498D70.
- Real ordinary-bank232DD2 UI uses numeric control59, deposit57,
  withdrawal58 and close54. Input839C8, bank839C4, target839C0,
  purse85604 and mode855ED are distinct.
-63/64 have logical7: target WORD, page/source/destination/quantity BYTEs.
  Actual callers establish63 bag-to-bank,64 bank-to-bag.65 is bank-internal
  movement with quantity1.48 supplies page/slot/quantity and20 metadata
  bytes. These contracts are recovered **but item banking is not implemented**.

The native UI checks a signed500000000 bank limit. Its addition can overflow:
bank1 plus input7fffffff wraps negative and the original producer sends61.
Server checked arithmetic and the cap are CUSTOM-0064 policy; this evidence
does not recover original server economic rules.

## Owned authority and persistence: CUSTOM-0064

`SqliteBankRepository` borrows a SQLite connection. Construction and load do
not install schema or create assets. Explicit startup installs balances and
receipts; the balance is created at zero only after qualified bank opening.
Existing trade wallets remain the purse authority. There is no funding API,
interest, fee or automatic NPC insertion.

One owned character's purse plus bank is conserved. Inputs must be positive
signed-int-compatible amounts. Calculations use checked wider intermediates;
bank cap500000000 and purse uint32 range are explicit custom rules. Commit
uses BEGIN IMMEDIATE, verifies account ownership and the complete expected
snapshot, rejects pending battle reservations, compares both amount/revision
pairs, performs both updates, inserts a unique64-hex server receipt and reads
back receipt and balances before COMMIT. Any failure rolls back every write.
Receipt operation codes61/62 **decimal** are internal deposit/withdraw
discriminants, not wire opcode numbers0x61/0x62.

`world_bank_service_points` is a separate capability table. Native bank-role
evidence and qualified native72 placement are both required. A catalog name,
model, client bank button or guessed location does not grant authority.
ISOLATED_TEST_ONLY roles require matching test placements and the existing
loopback2598/private-native-blackbox database guard. Startup adds no points.
No formal qualified banker position is currently available; placement remains
open recovery work, and private positions must never be promoted as original.

The session service requires an authenticated selected owned ready character,
no active trade, the same scene and a qualified bank target. CUSTOM-0064 uses
a square3-tile access radius and60-second inactivity lease; these distances
and expiry are not recovered original rules. One61/62/39 record may coexist
with ticks/common chat; duplicate or other mutation batches cannot commit.
Opening accepts oneNPC37 with ticks/common chat. Refused known bankers are
consumed without disconnecting or cancelling a trade; unknown NPCs retain
the existing route. Frozen chat dispatch is preserved.

Prepare absolute47/27 replies before writes. Native local close drops the
server lease and needs no response. Wrong target, expiry, cross-scene,
disconnect, stale state or malformed money cannot mutate savings. Native61/62
contain no unique request ID: separate equal-valued clicks may be legitimate
operations. Server receipts do not claim independent-frame replay deduplication.

## Verification and remaining scope

- Bank repository/service tests cover ownership, conservation, stale snapshot,
  insufficient amounts, cap/overflow/revision bounds, injected update and
  receipt/readback failures, test isolation and unrelated saved rows.
- Actual Application TCP4/4 checks two language peers, fragmented requests,
  deposit/withdraw/local close, close/restart/relogin authority, signed/zero/
  duplicate/mixed requests, known banker refusal during trade, distant access
  and unchanged common chat through coalesced open requests.
- Hidden original-client TW/CN money-control acceptance is recorded separately
  under `artifacts/playtests/private-native-blackbox-bank-20261002-*`.
  Failed run01 used a test NPC with unavailable scene sprite. It is not accepted
  as a bank test. Later runs must prove the current NPC renderer, native bank
  controls, displayed balance text and persisted amounts. No pixel acceptance
  is claimed from read-only renderer observation.
- Run02 accepted candidate02 with both native language clients.12 recorded
  events and6 durable receipts cover deposit250, withdrawal100, local close,
  reopening with bank150 preserved and withdrawal150. Both finish purse1000,
  bank0, native bank widget closed. Current NPC3793/type6 renderer is active;
  original money-label renderer contains the saved balance. All unrelated DB
  rows, client/config/source files are preserved; all owned private processes
  are closed and the foreground desktop is unchanged. The isolated NPC role,
  position128,126 and funding are CUSTOM_TEST_NOT_NATIVE.
- Release CTest13/13 passed, including actual bank TCP4/4, existing trade
  TCP3/3 and party TCP6/6. The packet-ledger test and frozen-chat verifier
  passed independently. The two reviewed routing defects (open with tick/chat,
  known-bank refusal cancelling a trade) were repaired before candidate02's
  original-client and deployment qualification.
- Managed release helper checks all13 banking/trade/party/world suites,
  current client identity, frozen chat and a qualified hidden-client receipt,
  then stages an isolated startup and compares every old schema/history/row.
  Formal startup may add only three empty bank tables and their two indices.
  It must not grant assets or insert guessed NPCs.

Whole-game completion denominator remains unknown. Candidate grammar41
distinct C2S producers is structural coverage only. Bank item63/64/65 runtime,
official economics, exact original bank roles/positions and large-player load
remain incomplete and must be qualified independently.
