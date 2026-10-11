# Current Companion State, 2026-09-19

## Delivered Binding

One binding: current S2C `31`, a 29-byte logical deity-status record, to the
original scalar consumer at RVA `AA200`. Added a lossless decoder and state
projection in `tools/strike_lab/current_companion_state.py`, with original-code
regressions in `tests/research/test_current_companion_state.py`.

Actual original instructions executed offline in Unicorn: receive parser,
length function, dispatcher, and scalar consumer. No instructions or callees
were replaced. Positive matches stop immediately before the call at `AA2AF`;
missing keys execute the complete consumer to dispatcher join `6B517`.
Every native run has a 10,000-instruction and one-second limit and verifies its
exact stop address. This is bounded native execution, not live acceptance.

## Sources Consulted First

Both legacy corpora were consulted before selecting the binding. Their runtime
formulas and textual acquisition mappings were not imported.

- Classic root:
  `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.
  Read `src/God2.ClassicServer.Runtime/PetLifecycleRuntime.cs` and
  `docs/research/current-server-packet-function-map-zh-TW.md`.
  The concrete lead is
  `src/God2.ClassicServer.Protocol/PublicBetaCompatibilityGameplayWireAdapter.cs`,
  lines 88-96, 156-163 and 192-226: S2C31, 29 bytes, positional fields and two
  reserved spans. SHA256:
  `10d4a59018fcc3b88da9706c87f2148e5881c1b01505d7352928f16c3ab87552`.
- XJZ root:
  `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.
  Read `evidence-combat-pet-v0.md` (SHA256
  `4d58e23d57625b1d50aae84cc0f5e0cf650769ec9c936fa5797a19f6b4a5a351`)
  and `evidence-god-acquisition-rule-v0.md` (SHA256
  `bd64b46da6ace2321471c94e4e1426b16673f0d5f7ae9d56a1b184e91b26ee3d`).
  These explicitly leave runtime synchronization/acquisition samples missing;
  their name-derived bindings do not prove ownership or reward packets.
- Current original-client mapped image:
  `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
  The entire image is checked before tests. Image base is `00400000`; offsets
  below are hexadecimal RVAs, equal to file offsets in this mapped image.

The requested companion follow-up, content-recovery note, recovery tool and all
its existing tests were read. Existing companion recovery files were not edited.

## Exact Native Contract

Size table `1324 + 4*31` contains VA `004012FA`. Original function `12FA`
returns decimal 29. Dispatcher table `6B5D4 + 4*31` contains VA `00469FA9`.
Dispatch entry `69FA9` advances the packet pointer past the opcode, sets
`ECX = world + A7F2F6C`, and calls `AA200` at `69FB1`.

Let `UI = world + A7F2F6C`, `actor = DWORD[UI + 86888]`. The consumer reads
unsigned byte count `actor + D4` and searches WORD keys at
`actor + D8 + index*3EC`. At `AA223`, `movsx dx, byte ptr [eax]` sign-extends
logical byte 1 before the WORD comparison. The first equal key wins. Thus byte
`80` compares equal to WORD `FF80`, not WORD `0080`. Tests cover all 256 bytes,
duplicate matches, no match, and declared counts 0, 1, 16 and 255. The latter
is a memory-boundary probe, not an assertion that 255 deities can be owned.

All packet positions in the following table are zero-based decimal and include
the opcode. Destination offsets are hexadecimal relative to the matched row.

| Logical Bytes | Operation / Destination | Native Store RVA |
| --- | --- | --- |
| 1 | signed-byte lookup against existing WORD key; not stored | comparison `AA227` |
| 2 | byte to `+02` | `AA244` |
| 3-4, 5-6, 7-8, 9-10, 11-12 | zero-extended WORDs to DWORDs `+44,+48,+4C,+50,+54` | `AA24D,AA256,AA25F,AA268,AA26F` |
| 13-16 | ignored by this scalar consumer; preserved raw | none |
| 17-18, 19-20, 21-22, 23-24 | raw WORDs to `+38,+3A,+3C,+3E` | `AA276,AA27E,AA286,AA28E` |
| 25-26 | low 15 bits to WORD `+28`; high bit to byte `+5A` | `AA29C,AA2AC` |
| 27-28 | ignored by this scalar consumer; preserved raw | none |

The projection returns a new immutable snapshot and matched index, preserves
every other byte, and makes no insertion on a missing key. State must contain
the entire byte-count-declared row area. The record object retains the complete
29 bytes, including both ignored spans; properties are derived from those bytes.
No legacy labels such as experience basis points or elemental attributes are
promoted to current gameplay semantics by these stores alone.

The positive stop is **before** `AA2AF`. Selection pointer/index writes at
`AA2BB` and `AA2C7`, paging at `A97A0`, and refresh at `A9AF0` are outside this
projection and were not executed on the positive path. A missing match branches
at `AA239` to `AA2DB` and returns without modifying actor memory.

## Historical Regression

Classic source `src/God2.ClassicServer.Runtime/OfficialClientWorldProtocolFrames.cs`
defines `WorldServerToClientStream` at line 78 and `WorldCipherKey` at line 82.
Source SHA256:
`cb65fa7a8873b0d299a1727d4a388072494c2323168669a5dddad3dc39311bca`.
Stream SHA256:
`9da6c91446fb40abb223723091bafd8931f2cae5ca08f33456191377e2fdfa03`.

The test uses existing `tests/fixtures/recovered-world-entry.json` provenance,
reads the actual legacy source, verifies its hashes, decrypts stream bytes
`[473:1225]` with retained feedback `B0`, and validates the whole frame's length
and checksum. Frame SHA256:
`32cea8e0a2765036c4dd495179abfd045baaa51a2dfefbb0fe8f33d00ff171ef`.
Original length functions validate the prefix record boundaries (2B,2C,24,39,22)
before S2C31 at decoded frame bytes `[143:172]`:

```text
31110200001600000000000000040100001b0029000d00060083090000
```

Record SHA256:
`e20495147d99628c58a64267ec6eee525fa1f16603d501f8b5542ed7d41affa3`.
Its ignored bytes 13-16 are `04010000`, demonstrating why zero reconstruction
would be lossy. The actual record runs through the current dispatcher/consumer
with explicitly synthetic existing WORD keys 0010,0011,0012. This proves a
cross-build record's current scalar interpretation, not current character truth.

## Verification

```powershell
python -B -m unittest tests.research.test_current_companion_state -v
```

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.
Result: **8 tests passed in 4.898 seconds**, exit 0. No compilation required.
The initial harness run exposed two test-harness defects: Unicorn requires
immutable bytes for `mem_write`, and using image RVA 1000 as the return stop
intercepted a real parser helper. Both were corrected; the final run uses a
stack sentinel outside original code. These were not reported as native defects.

Checks include historical source membership, exact current binding, all lookup
bytes, duplicate/last/missing matches, five WORD boundaries, repeated updates,
opaque-byte mutations, immutable inputs and malformed records/state. Whole actor
snapshots and every non-stack write are checked against the scalar projection;
packet memory is read-only and ends at an unmapped page boundary.

Original buffered receive parser `13420` rejects partial lengths 1-28 and accepts
29; `13650` returns all 29 exact bytes. Direct consumer probes show that 27- and
28-byte buffers can reach the scalar stop because the tail is unused. Therefore
the decoder must retain parser-level length validation despite the smaller
consumer read footprint. Empty input, appended bytes, concatenated records and
wrong opcode are rejected by the decoder. The empty-buffer socket path is not run.

Suggested shared target for main: register the command above as
`research_current_companion_state`, using the repository root as working
directory and a 60-second test timeout. It needs the pinned image, existing
provenance fixture, Classic source and bundled Unicorn path; no C++ target or
shared runtime change is needed. No build artifacts were produced.

## Limits

This establishes one native packet-to-existing-row scalar binding. It does not
establish acquisition/ownership, the mapping of the WORD key to GOD catalog IDs,
summon/growth/rate/stat/skill rules, meanings or units of the scalar fields, or
the later selection/UI effects. The historical record is not a new live capture.
No UI, client/server process, socket, additional agent, visual resource manager,
GodDoll loader, shared runtime, CMake or world file was used or changed.
