# CN transport seed source (2026-10-08)

Round: `20261008-cn-transport-seed-source`. PHASE1 source integration only.
Own-server transport operation and recovered native format are distinct.
No build, RNG execution, native/client/codec/server execution, test, database
access, migration or deployment occurred in this round.

## Pinned native operand chain

Input: `C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe`, PE32/x86,
47,541,760 bytes, SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
Artifact: `artifacts/integration/packet-connections-20261006/cn-transport-seed-source-01/native`.
The actual file-backed metadata envelopes and their decompiled navigation
sources were retained; Capstone only disassembled bytes, never ran the image.

|Native location|Retained bytes|Concrete operand relationship|
|---|---:|---|
|0047A800|657|Socket input, header/body acquisition and decoded-buffer extraction. 0047AA21 chooses min(available,16); 0047AA4C requires exactly16 copied. 0047AA55/5B installs those literal bytes at object+2420; 0047AA62 calls00479650. Only afterward +8/+C become1 and +0 becomes0.|
|00479650|548|Expands seed16 at+2420 into key256, constructs challenge16 at+2520 and the byte accumulator at+2556. Seed-index selection is masked to low4 bits; challenge key indices are masked to low8 bits. No content whitelist or seed RNG call is in this retained function.|
|0047A590|295|Decode is gated by object+8, then checksum/body copy or compressed S2C handling. This is not the official server's RNG and does not make all compressed variants supported by our server.|
|0047A760|158|Native encoder copies body, adds length3, computes byte checksum using+3C, and encrypts body/checksum only when object+8 is enabled.|
|0047A3C0|45|Emits the derived challenge at+2520 with literal length16 through0047A760 and the socket send import; then clears object+4.|
|00895790|256 table bytes|Actual file-backed key-table bytes consumed by the existing reconstructed transport.|

Total captured metadata envelopes: 1,703 bytes; table256 gives 1,959 distinct
file bytes in this bounded capture. These functions were previously identified;
retaining their primary bytes is not discovery of new opcodes or a claim that
all bytes are new to the project's historical evidence. The metadata spans
decode through their terminating returns, but do not establish an exhaustive
whole-program CFG, startup state, every compression/extra-body variant or all
callers. The intake's min(available,16) is not a claim that the native client
rejects extra decoded body bytes. Our existing seed frame remains the bounded
uncompressed19-byte form. Existing key derivation, checksum and framing code
were kept byte-for-byte unchanged in this round.

The client does not provide the official server seed distribution, seed
uniqueness policy, generator implementation or entropy source. Nor is this
transport seed the check_key in1D, the shared admission grant, password hash,
billing0A record or entitlement. Those actual suppliers remain separate gaps.

## Actual source integration

`OperationalTransportSeed.h/.cpp` implements the explicit
`WindowsSystemCngV1` policy for OUR server. It obtains16 output bytes with
`BCryptGenRandom(nullptr,...,BCRYPT_USE_SYSTEM_PREFERRED_RNG)` and only returns
them on CNG success. The official Windows contract requires a null algorithm
handle for this flag, a buffer size in bytes, and a checked status result:
[Microsoft BCryptGenRandom documentation](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptgenrandom).
The existing Windows `bcrypt` library dependency and frozen
`auth/PasswordHash.cpp` are unchanged; password hashing is not used as a seed
source. CMake already discovers the new.cpp via its source glob; it was not run.

The composition takes exactly one explicit source: either its existing seed
callback, or the new optional operational policy. Both present is an error;
both absent remains an error. Account/world/native data suppliers are still
mandatory. Choosing this policy copies the same actual Context listener
endpoints into one retained issuer before controllers are returned. There is
no implicit fallback selection in `main.cpp` or `Application.cpp`.

The issuer validates one account endpoint and actual unique world endpoints,
socket addresses, ports, roles and target indices. Issuance requires the
constructing serial game thread, a matching copied listener endpoint and a
nonzero increasing connection ID. Copies of the callback retain the SAME
issuer gate. The existing listener obtains that ID on its game owner, invokes
the configured source, and copies returned seed bytes into the real connection
transport. Each account/world accepted socket obtains its own issuance; world
reconnection does not reuse the account connection's seed. A failed issuance
consumes its connection ID and leaves the existing listener's nullopt-close
path intact. A new future connection has a new ID.

There are no fixed bytes, persisted seed records, cached generators, guessed
time/PID seeds, hash derivations, retries or random_device fallback. Temporary
CNG output is wiped on failure and after copying the successful owned result.
No extra-byte restriction or nonzero-byte requirement is invented; legitimate
CNG output may contain zero bytes. This policy does not claim seed values can
never collide, persist its one-shot gate across process restart, provide secure
native transport encryption, or replace TLS/WSS and shared authority checks.
Other platforms and unrecognized policy values reject construction.

## Remaining work and counting

This closes the *implementation absence* of an explicit own-server transport
byte supplier in the source composition. It does not configure or host the
formal Application, recover official seed randomness, supply1D/0A/entitlements,
or complete account/world/gameplay routes. Native runtime compatibility remains
unproven until the owner's later comprehensive phase. New complete gameplay
routes0; new opcode/phase binding/complete owner chain0; total and percentage
remain unknown. Native07, world1F/02/2A/6F/equipment/scene/ACT sources, TW common
registry, PC/web/WSS hosting, credential revision/ABA/revocation, all remaining
gameplay, numeric extensions and route denominator are still open.

Next native login frontier: recover actual1D/0A producer-consumer constraints
and account server-directory/entitlement sources; keep source provenance and
operational issuance separate, and wire complete actual account/world suppliers
without changing frozen authentication, saves, fonts, text conversion or levels.
