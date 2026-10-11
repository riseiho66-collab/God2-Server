# OracleLab interface and protocol frontier

Scope: D owns only ICryptoBackend.h, CleanCryptoBackend.h,
oracle_lab_backend.py and this document. No protocol, CMake, crypto algorithm,
capsule or captured artifact changes are made here. Brute search is frozen.
No full client or UI is launched. Original executable code and capsule data
remain local artifacts and must not enter source or distribution packages.

## Shared interface

The C++ namespace is `god2::crypto`. C owns `God2CryptoClean.h`, including
`CryptoState` (key[256], proof[16], uint8 feedback, uint32 enabled) and
`CryptoSession` (tx/rx). D includes that header without duplicating its types.
`CryptoBackend` has `Clean` and `OracleLab` enumerators; it is not a factory or
a claim that a C++ OracleLab implementation exists.

`ICryptoBackend` exposes virtual `InitSession(span<const uint8_t>,
span<const uint8_t>) -> CryptoSession` (16/1024 bytes checked by C), and `Encrypt`/`Decrypt` with
`CryptoState&` first, `span<const uint8_t>` second, returning byte vectors.
`CleanCryptoBackend` delegates those calls directly to C's free functions.
Inputs are raw transform bodies, not complete framed packets. Each connection
owns its session state, encrypts through tx and decrypts through rx. Do not
serialize the C++ struct by copying its memory: padding is not a wire format.

The Python adapter is a separate local research interface, not a C++ production
bridge. It lazily loads B's actual `oracle.ClientCryptoOracle` class:

```python
backend = OracleLabBackend(
    capsule,
    lab_mode=True, production=False, endpoint="127.0.0.1",
)
backend.init_session(seed_bytes)  # exactly 16 bytes
wire_body = backend.encrypt(plain_body)
plain_body = backend.decrypt(wire_body_from_peer)
```

This illustrates API calls, not a proven server/client roundtrip or legal packet.
An optional `oracle_factory=ClientCryptoOracle` or fake supports explicit wiring
and isolated policy tests.
The adapter calls `ClientCryptoOracle(capsule)`, `init_session(seedbytes)` and
`encrypt/decrypt(statebytes, inputbytes)` using B's agreed dictionary keys
`state_after_hex` and `output_hex`. The initializer's opaque serialized state
starts two independent immutable byte lanes. Calls are serialized per adapter;
failed result validation does not commit a new lane. A successful new init
replaces both lanes. No C++ struct layout or capsule state offsets are inferred.
The table is capsule-bound on this Python path, not a second initializer input.

Construction defaults to lab disabled and production enabled, and rejects
anything other than literal True/False for the two opt-ins. Numeric loopback
addresses only; DNS names, URLs, remote addresses and scoped IPv6 are rejected.
All guards precede oracle import and factory invocation. The production
composition root must never import/start B's runtime. If injecting a factory,
the lab root must also validate policy before importing B. Importing
the adapter alone is inert. A supplied endpoint is policy input, not proof of
socket binding; a future host must inspect actual bind and peer addresses too.
Hash verification and original-code provenance remain B's responsibility.

## Exact frozen six-byte contract

Evidence: `artifacts/contracts/post-server-select-v1.json`,
`artifacts/golden/server-select/C2S_0001.bin`, and
`docs/GOD2_POST_SERVER_SELECT_STATUS.md`. UI acceptance is ui-gate-real-04;
"six" describes the request length, not an additional accepted UI run.

| Wire offset | Bytes | Established interpretation |
| --- | --- | --- |
| 0..1 | 06 00 | LE16 frame length 6 |
| 2 | a3 | Zero-seed decoded one-byte opcode a6 |
| 3 | a3 | Decoded 00; statically correlated low byte of arg1 from UI+0x8f4 |
| 4 | fd | Decoded 00; statically correlated low byte of arg2 from UI+0xb40; meaning unknown |
| 5 | d5 | Decoded checksum d8 |

Logical body is `a6 00 00`. Builder RVA 0x147d0 is a static attribution;
its execution/source reads were not dynamically captured. The matched send
return at RVA 0x12506 is observed. Post-TX state is null/unobserved;
`next_expected_direction` is `NOT_OBSERVED`; `next_s2c_candidate` is null.
Numeric state3 in a static UI path is not proof of Character phase. No next
C2S opcode, S2C response, receive, reconnect, Character, World, heartbeat or
movement packet contract is established. RX_POLL alone would not prove one.

`RecoveredPostServerSelect.h::ParsePostServerSelectRequest` accepts only the
exact six bytes. `Session.cpp::Impl::read` in God2PostServerSelect mode collects
them after TerminalSent, records PostSelectReceived, releases hold, and sends
nothing. Further C2S data fails with "Post-selection next C2S contract unknown".
This remains the supported boundary, including with an oracle available.

## Parent integration handoff

The actual recovered protocol path is in `Session.cpp`, bypassing the generic
`God2ProtocolSpec`/identity `CryptoPipeline`. Merely replacing CryptoPipeline
would not connect an oracle to that path. No hook is installed by D.

For a real future lab hook, the parent must own a per-connection backend/session
at the recovered path, initialize from the verified seed/table at the recovered
seed boundary, and pass only the proven transformed body range to the backend.
Framing, checksum ownership and state reset boundaries must be evidenced first;
existing Recovered* helpers already return/parse transformed fixture bytes and
must not be transformed a second time. Preserve stream buffering and existing
protocol state validation. Serialize each lane in actual packet order and
close on transform/write failure if state and wire delivery can diverge.

Python requires an explicit local host/bridge owned by the parent, with bounded
request sizes/timeouts, loopback bind and peer checks, and failure propagation.
It cannot be injected into the C++ vtable as delivered. First use it for offline
known-body differential checks. Prove original-client encrypt/decrypt direction
equivalence for server S2C/C2S and prove state continuity across the frozen
prefix before using it in a server. Oracle availability establishes neither
those facts nor a legal next protocol message. Keep the post-selection handler
silent until an existing local artifact establishes a next direction and full
packet contract; no fabricated Character/World packets or new UI runs.

The parent owns CMake release guards: GOD2_ENABLE_ORACLE_LAB defaults OFF;
production builds must reject ON, including Release and shipping
RelWithDebInfo/MinSizeRel configurations under multi-config generators. Keep
lab targets/dependencies out of production linking and installation; omit the
runtime, emulator and extracted code/table/capsule artifacts from distributions.
An enum value or Python runtime flag is not a build/distribution guard.

C's header and B's runtime appeared during this work; the wrappers now match
their actual signatures. C checks 16-byte seeds, 1024-byte tables and a 4096-byte
raw-body ceiling. B validates its capsule and enforces its own replay bounds.
Adapter policy and state transitions can be checked with an injected fake,
which does not establish crypto equivalence. No CRYPTO_RECOVERED or
Character/World promotion is warranted by this interface work.

## D verification

MSVC C++20 `/Zs /TP /Isrc src/crypto/CleanCryptoBackend.h` passed against C's
actual header. An in-memory Python fake passed default-off/strict-boolean
checks, numeric loopback acceptance (IPv4, IPv6 and mapped loopback), rejection
of DNS/remote/URL/scoped endpoints before factory invocation, no oracle import
on default rejection, invalid seed and uninitialized-call rejection, separate
TX/RX updates, malformed-state rollback, and session reset. The checks used
`python -B` and wrote no test artifacts. No real capsule replay, linked C++
runtime test, socket integration, client execution or UI execution was done.
