# Legacy post-world-init response evidence, 2026-09-19

Scope: retained evidence for C2S `1F00`, `2300`, and `1C<id DWORD>` only.
Read alongside `current-world-initialization-sequence-20260919.md` and
`legacy-world-entry-provenance-20260919.md`. No server edits, current-client
disassembly, UI, game/server runtime, or live capture was performed.
Lengths/offsets are decimal; opcodes/bytes are hexadecimal; hashes are SHA-256.

## Result: no recovered direct post-ready reply contract

The targeted Classic sources preserve **temporal response candidates**, not
an exact reply transcript for the initialization tail. They do not establish
`1F -> 1F`, `23 -> 23`, `1C -> 1C`, or that the scalar records below must be
sent after these requests. XJZ supplies no populated samples for this boundary.

Roots:

- `C` = `C:\God2Evidence\classic-20260820\files\God2-Classic-Server-Formal-Handoff-20260820-020345\ServerSource`
- `E` = `C/src/God2.ClassicServer.Protocol/Evidence/OfficialProtocolCompletion`
- `R` = `C:\Users\risei\Desktop\God2\God2-Server`
- `X` = `R/artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`
- `F` = `C/src/God2.ClassicServer.Runtime/OfficialClientWorldProtocolFrames.cs`

## Actual retained request/response associations

`E/God2Evidence.20260807.112752.json`, `actionGroupingEvidence.patterns`:

| C2S opcode / frame length | Saved pattern | S2C opcode / frame length | Occurrences | Median / p95 ms |
| --- | --- | --- | ---: | --- |
| 1F / 5 | AP-0037, line 2175 | 36 / 14 | 1 | 142.586 / 142.586 |
| 1C / 8 | AP-0038, line 2199 | 72 / 24 | 2 | 172.243 / 187.429 |
| 1C / 8 | AP-0059 | B2 / 262 | 1 | 184.846 / 184.846 |
| 1C / 8 | AP-0097 | B2 / 120 | 3 | 184.814 / 185.746 |
| 23 / 5 | No matching pattern retained | Unestablished | - | - |

All four patterns say `semanticStatus: Unknown`, `productionEligible: false`,
and have empty `handlerOpcodeSequence`. Each contains a single response, not
a `72 -> B2` sequence. These are aggregate associations without paired raw
request/response bytes, per-instance timestamps, or a world-init stage label.
They cannot establish causal triggers, response contents, or ordering relative
to `1F00 -> 2300 -> 1C`. The request catalog reports 1F six times, 23 twice,
1C thirteen times, each with one unique frame; it does not expose those bodies.

The package identifies `God2_opt.exe` SHA
`6B127086E0C00014DE26137B4EC482801E06E0724C5C05C64561D7F9FF32BD9B`,
session `C6A8BF34-73F6-4859-AAA0-6FE49530CEC9`, source ZIP SHA
`20F8D5A60119CE9FA4F82C0CB0F546F832E594E7B3DBF5679B2464044F497F27`.
This is a different executable identity from the current client documented
in the preceding provenance note. The July bootstrap below is a separate
evidence source; do not bind it to this August identity silently.

`E/DecryptedPacketCorpus.20260807.v2.json` preserves hashes, not sample bytes:

| Entry suffix (prefix `evidence-package-20260806-`) | Sample SHA-256 |
| --- | --- |
| c2s-opcode-1f | `780630A6070CDCB62EE1B72BD77CA0D007087026570095130DD55B820A1563EF` |
| c2s-opcode-23 | `0190F7B20646B92E2B26FE20A4420860BB189C57341723605971DFC6C556D7B9` |
| c2s-opcode-1c | `C121BBC395A0E700B0C57129B38564F203305ACFCB8E1CBF2EB314457F0FDC76` |
| s2c-opcode-36 (lengths 14, 25) | `4F445606B53911F781DCB53165E121CF74954B44F5124E6284F0A980829D3693` |

These hashes do not recover the ID, prove zero request bodies, or identify the
specific AP-0037 reply. The same catalog's S2C23 entry is explicitly
`INCOMPLETE_DEFINITION`, with no plaintext hash (outer lengths 20 and 1254).
Its S2C1C sample is a 45-byte handler record, not a reply association.

## Exact scalar candidates, with bootstrap-only provenance

`F:78` retains `WorldServerToClientStream`. Its absolute `[473,1225)` frame
(752 bytes; bootstrap-relative 454) starts with these records. Extracted by
the existing `F:912` decode formula, `WorldCipherKey`, initial feedback B0;
the **entire decoded frame hash**, not just its prefix, matches independently
saved `E/WorldProtocolRecovery.Phase32.MountStateSource.json`,
`mountedBaseline.frames[3]`:

- Encoded: `32CEA8E0A2765036C4DD495179ABFD045BAAA51A2DFEFBB0FE8F33D00FF171EF`
- Decoded: `A19FFB01241C8B49F8CE4014AF18516F51874F235488DD8A0FF0C0C3A3BD57C8`

Ranges below are within that decoded frame, including its two-byte length
prefix. Hex is **logical opcode plus body**, without framing/checksum.
Boundaries use the coordinating task's supplied fixed lengths; no suffix
parse or current-client analysis is claimed here.

| Frame range | Exact retained candidate bytes |
| --- | --- |
| [2,23), 2B / 21 | `2BCC0000001C02000036000000CF0000008C1F8309` |
| [23,84), 2C / 61 | `2C0500000008000000020000000100000000000000040000000000000000000000000000000F0000000000000006000000120000000500000025000000` |
| [84,101), 24 / 17 | `24CC00000036000000CC00000036000000` |
| [101,118), 39 / 17 | `391C020000CF0000001C020000CF000000` |
| [118,143), 22 / 25 | `22020000001E002700140015008C1F0000CC00000036000000` |

`F:222` also explicitly retains and checks the same 21-byte 2B literal.
Its record hash is `736319FB99619FFFD3F86BEEDF4DDAEC2E64840B163677B4BE3D1D4D2D185683`.
This supplies historical bytes for comparison, **not a recovered post-ready
response policy or authority for persistent player stats**. Standalone
wrapping or replacing values would be new serialization. No assumption is
made about the `3B` record at offset 202 or the later suffix.

## Ordering, saved captures, and exclusions

The retained Classic implementation sends a world follow-up after handshake,
then waits for an opaque 208-byte world-entry request
(`C/src/God2.ClassicServer.Runtime/RuntimeFoundation.cs:3265..3315`). After
session binding/projection it sends the remaining bootstrap (`:3473`). This
is a source-level trigger for the bootstrap scalar records above, **not**
a `1F/23/1C` response handler. Targeted runtime source search found no explicit
reply mapping for those three requests.

`E/WorldContentRecovery.Phase41.MapRuntime.json:40..42` records a July local
WorldReady matrix of 79 packets, all C2S, with zero post-bootstrap S2C. That
supports only this frozen local baseline, not absence of replies on the
official server. Phase32 names `Artifacts/ClientInstrumentation/ElevatedAutomationHost/host-run-20260730-061702`
and `Artifacts/Runtime/ServerRuns/phase31-final-mounted-20260730-061639`;
the referenced client trace directory is absent under C. `C/PACKAGE-CONTENTS.md`
explicitly excludes packet captures/runtime output. Surviving evidence here
is source byte arrays and saved JSON extracts/metadata, not an inspectable
paired post-ready capture.

The saved 128-byte S2C1F bootstrap at stream offset 25 has decoded hash
`1B8106D46D80F5DA73D78C1A7349CF77D7A6EF0201027AF05B9A3D83C4F505C6`,
also independently matched to Phase32. Its existence does not make it a
reply to C2S1F. Per the coordinator's current dispatcher findings, S2C1F and
1C take the ignored default; S2C23 copies a 16-byte string of unproven meaning.
No character-name/guild/title interpretation is assigned here.

XJZ read-only SQLite queries found zero rows in `account_login_sync_sample`,
`character_create_sample`, `character_profile_sync_sample`,
`inventory_sync_sample`, `official_memory_capture_sample`, and
`evidence_reverse_probe_capture_sample`. Its
`evidence-account-character-sync-capture-target-v0.md` explicitly leaves
packet formats and synchronization order behind `packet_evidence_boundary=1`.
Capture targets and empty tables supply no reply bytes or ordering proof.

## Recomputed source hashes

| Path | SHA-256 |
| --- | --- |
| F | `CB65FA7A8873B0D299A1727D4A388072494C2323168669A5DDDAD3DC39311BCA` |
| C/src/God2.ClassicServer.Runtime/RuntimeFoundation.cs | `B546C025A02092257249DC4DAC7A9FC66C992867E241D925EA13E02E07166444` |
| E/God2Evidence.20260807.112752.json | `E626ADF4FE92566A5A8806658FF9B77E0BE284144D8D8EC662717DDB1EF1A994` |
| E/DecryptedPacketCorpus.20260807.v2.json | `73F969E120BDD198851A973A669639DC88D2F16722B82DD380FF79E94201F19B` |
| E/WorldProtocolRecovery.Phase32.MountStateSource.json | `8C374A564602D4F5BB66293D2E0E22824983D2880F2D6309C2485E21D694D857` |
| E/WorldContentRecovery.Phase41.MapRuntime.json | `AD1FBBB92D6D74971B5EE2E56A2EC478263703D032341D95A843F568016E2117` |
| C/PACKAGE-CONTENTS.md | `B17E225C8094CD2F88D9F65D38F48B5ABA72B1A2A47AD0711189F5D196418FA4` |
| X/xjz_evidence.sqlite | `44048EE3D664F1418E60EAA267D46E4BA118AA3689FAE03F7350D544A9FC1774` |
| X/evidence-account-character-sync-capture-target-v0.md | `A62746009DABF2F6C77E6EA38DF09F3B86F344728DCFAC0EBE37856E2A9DCFD4` |

Only changed path: `docs/research/legacy-world-ready-responses-20260919.md`.
