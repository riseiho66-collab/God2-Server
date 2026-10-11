# Current Character-Socket 1F Context

## Result

**Do not replace the current preselection zero-body candidate with historical
player fields.** In the established main-object path, `B910 -> 14A70`, all 124
body bytes are copied into a temporary stack output and then discarded. The
successful continuation reads only the waiter's return status. No body-derived
context is published for the following `1A`, `2A` or world initialization by
this caller. This eliminates a speculative dependency; it does not establish a
canonical original-server reply or prove the complete live initialization.

The current world dispatcher routes S2C `1F` directly to record consumption,
not a player-spawn handler. Legacy code calling a 128-byte `1F` "PlayerSpawn"
is not a current-build field contract.

An alternate caller `F930` **does retain the same body**. Its later `F410`
accessor reads bytes at `38 + 40 * selected_index` (decimal). Therefore the
main-path discard result must not be generalized to every caller/session.

## Evidence Identity

Current mapped x86 image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`

Base VA `00400000`; all instruction addresses below are RVAs. Body offsets
and lengths are decimal unless explicitly written with `0x`.

## Legacy Sources First

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`

Both files below are in `src/God2.ClassicServer.Runtime`:

| Source / literal | Source SHA-256 | Actual decoded-literal SHA-256 |
| --- | --- | --- |
| `OfficialClientLoginProtocolFrames.cs`, `CharacterCreationBootstrapDecodedTemplate` | `bee45cfe9d1d775f8886aef23edd8dc74a1645a6381e47f2242597ca42cff890` | `8bbf3ba1d0d4882cc6de29e56c4ae70150763fd677a21722f7d9eb56d2508a8f` |
| `OfficialClientWorldProtocolFrames.cs`, `CurrentCreateProfilePlayerSpawnDecoded` | `cb65fa7a8873b0d299a1727d4a388072494c2323168669a5dddad3dc39311bca` | `59d0625cf2a013da19891bd43d8f47124de7ba2f384569e240bb676062df8456` |

Both retained literals have length 128, opcode `1F`, and a valid additive
checksum. Both pass the current preselection parser/copy/return regression.
This corroborates their **structural acceptance only**, not their historical
field meanings, suitability for this account, or current world behavior.

The world source's nearby comment claims decoded hash
`ccc098f41f68d2c2836951935fba067900ceb93a9ff98433fe9e3b2392e8caf8`.
It does **not** match its actual retained literal. The regression preserves
both facts. No historical trace authenticity or exact-capture match is inferred.
The older `WorldProtocolRecovery.Phase36.PriorityReset.json` associates its
player-spawn claim with parser RVA `7C8B0` in `god2_opt.exe`; this is not the
current image's dispatch contract. No literal is promoted into a runtime reply.

XJZ root:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

Searches covered `0x1f`, `s2c.?1f`, `character context`, bootstrap, 128-byte,
player spawn and character/login terms in source, evidence documents and SQL.
`evidence-account-character-sync-capture-target-v0.md` explicitly describes
capture targets, not complete packet layouts. A read-only SQLite query found:

| Table | Rows |
| --- | ---: |
| `account_login_sync_sample` | 0 |
| `character_create_sample` | 0 |
| `character_profile_sync_sample` | 0 |

No qualified XJZ 124-byte replacement was found within those sources. This is
not a claim that all possible content or every database table was searched.

## Exact Current Consumption

| Boundary | Original behavior |
| --- | --- |
| S2C size table `1324 + 4*1F` -> `1000` | Returns 125 logical bytes: opcode + 124-byte body. Full standalone frame is 128 bytes. |
| `14AB9..14AC3` | Distinguishes reply opcode `1F` from error opcode `1E`. |
| `14B1A..14B28` | Reads output pointer; copies 31 DWORDs from logical pointer+1, exactly 124 bytes. |
| `14B2C..14B37` | Consumes record through real `13670`, returns zero, `ret 8`. |
| `B980..B993` | Supplies local output and separate error-text buffer to `14A70`. |
| `B998 -> B9E5..B9F2` | Success returns 1, unwinding locals without reading the copied body. |
| `14A73..14A80` | Disconnected network object also returns zero **without copying any reply**. Caller success alone is not reception proof. |
| `68B4C..68B61`, table `6B5D4 + 4*1F` | Current world dispatch selects `6B517`, the common consume path; no payload access. |

At `B980`, with stack pointer `S`, the output is `[S+108h,S+184h)`;
`[S+184h]` is the caller return address. Native 31-DWORD writes and sentinel
bytes on both sides are asserted. A zero baseline and 124 independent one-byte
mutations all return identically without any read of the output after copying.
The synthetic main object remains byte-for-byte unchanged by this continuation.
The receive buffer retains stale bytes after consumption, but its pending count
is zero; the test does not infer a permanent erasure or global absence of reads.

The receive regression executes actual `13420`, size dispatch, `13650` and
`13670`. Every partial length 1..124 remains incomplete, while a complete 125
is consumed without swallowing the next logical message. Zero-length and
oversized records are checked by the bounded C++ decoder.

## Alternate-Caller Hazard

`F967..F979` passes `*(object+668h)` as the output pointer. `F97E..F9CD`
returns success but does not discard that pointed-to allocation. In the tested
`F410..F43E` slice, signed WORD `object+660h` selects a byte at:

```text
output + 38 + 40 * selected_index
```

Indices 0, 1 and 2 read body offsets 38, 78 and 118, respectively, and pass
the zero-extended byte as the third argument to `14C50`. No field meaning beyond
this observed selection argument is assigned. The accessor itself contains no
local bounds check: index 3 reads offset 158, outside a 124-byte allocation.
A guard page reproduces that read at `F425`. Upstream reachability, actual
allocation size and selector validation are unresolved, so this is **not** a
claim of an exploitable or reachable live-client fault.

Other bytes, alleged names/IDs/stats and creation-version fields remain opaque.
Do not infer these from the Classic literal, turn zero into guessed defaults,
or use the new decoder as validation of this alternate caller's state.

## Delivered Contract

`src/protocol/RecoveredCharacterContext.h` provides only:

```cpp
RecoveredCharacterContext::decode_preselection_reply(logical)
// optional<PreselectionReply>, containing an owning opaque_body[124]
```

It accepts exactly opcode `1F` and 125 bytes and preserves every body byte.
The caller must already have checked transport/checksum and split records.
It does not serialize a candidate, populate world state, authorize a character,
or interpret an alternate-caller token. Successful decoding is structural only.

The standalone C++ fixture validates all opcode values, every truncation,
byte preservation, and bounded generated inputs of lengths 0..4095. No existing
runtime, shared helper, fixture, CMake file or gameplay/Lua code was modified.
Parent integration must keep this standalone `main` out of any test-source glob
that links another `main` and register a separate executable if desired.

## Executable Regression

From `tests/research`:

```text
python -B -m unittest test_current_character_context -v
```

Result on 2026-09-19: **8 tests passed**, including private C++20 compilation
with warnings treated as errors and its standalone assertions (9.111 seconds).

The suite builds only the new C++ fixture in a private temporary directory.
Original native slices and parser are unpatched. The only service adapter is
the OS tick-count import, fixed at 1000 for the bounded receive test; optional
native logging is disabled through its real null check. B910/F930 begin after
their outgoing `149C0` request returns. No authentication builder, socket,
live process, GUI, rendering, scene loader or appearance helper executes.
The world-dispatch test stops at the common consume boundary; alternate F410
stops at `14C50` before it sends anything.

## Next Action

For the currently established B910 selection route, continue the real `2A`
scene/actor initialization and its owned profile/resource inputs. There is no
proven reason here to substitute historical nonzero 1F content before doing so.
If execution instead reaches F930, first establish that caller's constructor
argument, backing allocation, selector bounds and downstream use; do not reuse
the B910 discard contract. Retained literal hashes and exact bytes are kept in
the source-reading regression for that future comparison, not replayed.
