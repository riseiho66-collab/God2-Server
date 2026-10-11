# Legacy world-entry provenance, 2026-09-19

Scope: retained evidence and runtime sequence only. No parser re-analysis,
production edits, builds, live sessions, or UI. Offsets/lengths below are decimal;
opcodes and byte strings are hexadecimal. SHA values are SHA-256.

## Finding: retained embedded 2A, not a captured standalone 40-byte frame

Roots used:

- `C` = `C:\God2Evidence\classic-20260820\files\God2-Classic-Server-Formal-Handoff-20260820-020345\ServerSource`
- `E` = `C/src/God2.ClassicServer.Protocol/Evidence/OfficialProtocolCompletion`
- `R` = `C:\Users\risei\Desktop\God2\God2-Server`
- `X` = `R/artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

`C/src/God2.ClassicServer.Runtime/OfficialClientWorldProtocolFrames.cs:78`
retains the complete 1797-byte `WorldServerToClientStream` as literal hex.
The 320-byte encoded frame at absolute stream `[153,473)` has SHA
`C2DB6E90071C425F0D3B69952F940C3D979F64879863CBCC6612DF2B954E99B7`.
Its first 32 bytes are
`4001AC9EC7C53FA566FB9EBBC53720D7CC4F4F96C863F8287333C6277C4C5703`.

Crucially, **independent saved JSON** `E/WorldProtocolRecovery.Phase32.MountStateSource.json:541`,
`mountedBaseline.frames[2]`, records that exact encoded SHA, stream offset 134
(bootstrap excludes the 19-byte handshake), length 320, decoded SHA
`B0837934E2AA71A0C552160C4F54B20FF8073F81737CC0CF8E19E3B2DB910D3A`,
and this saved 64-byte decoded prefix:

```text
400102000000000000000000000000000000000000000000002AD900800005101B020000000001800160016031006000310CC203000046001A00000000001BFB
```

Decoded frame `[25,62)` is the complete candidate opcode plus 36-byte body:

```text
2A D9 00 80 00 05 10 1B 02 00 00 00 00 01 80 01 60 01 60 31 00 60 00 31 0C C2 03 00 00 46 00 1A 00 00 00 00 00
```

- 37-byte opcode/body SHA: `B4CF5BD6CEE76B6EB876D93812BA982ACA22E3DB01C15236FC5DDE430964126D`.
- 36-byte body only, frame `[26,62)`, SHA: `79E98FEF8D5E97C16EB60B52BA806CF965509F46E230B6010FF9671BEA8E8AA7`.
- These bytes were extracted directly from the saved JSON prefix, not invented defaults or a new decoder. The encoded frame hash was independently recomputed from the retained source constant and matches the JSON.
- Main reports checksum-valid decoding of this frame with the existing decoder, `WorldCipherKey`, initial feedback `B0`. This sidecar does not independently qualify current parser fields. Do not apply fixed `B0` to later frames at absolute 1225 onward; main reports checksum failure there.
- Wrapping this body into standalone `2A`, 36 payload / 40 total, would be a **new framing operation**, not an existing captured 40-byte packet. Preserve unknown body bytes pending current-parser qualification.

## Retained Sequence And Missing Adjacency

`E/WorldBootstrapSequence.json` records a Feb 4 2026 / 0.30.33 client and
`OfficialWorldBootstrap1778`, dependent on the world handshake and second
connection role. Its outer-frame order is:

```text
19-byte handshake, then bootstrap-relative offset: opcode / total length
0:01/6 -> 6:1F/128 -> 134:02/320 -> 454:2B/752 -> 1206:9C/68
-> 1274:B3/182 -> 1456:96/36 -> 1492:D3/63 -> 1555:61/42
-> 1597:66/67 -> 1664:A7/88 -> 1752:9E/26
```

These are saved outer-frame labels, not an independently validated logical
dispatch sequence. The embedded `2A` starts at decoded frame offset 25, logical
offset 23 after the length WORD. The next two **saved bytes** at offsets 62/63
are `1B FB`, not `30`; interpreting the entire logical continuation is main's
parser task. `E/WorldSemanticDispatchMap.json:99` independently preserves the
same prefix through offset 47 and identifies source trace
`Artifacts/ClientInstrumentation/ElevatedAutomationHost/host-run-20260730-073322/attempt-1-trace/general.log`.
Phase32 attributes its mounted baseline to `host-run-20260730-061702` and
`Artifacts/Runtime/ServerRuns/phase31-final-mounted-20260730-061639`.

Those referenced trace directories/files are absent under `C`.
`C/PACKAGE-CONTENTS.md` explicitly excludes runtime output, generated artifacts,
reports, and packet captures. Thus the surviving evidence is literal stream
bytes plus saved trace extracts/metadata, not an inspectable original pcap or
complete chronological log. No retained adjacent current select-success
`02 -> standalone 2A/40 -> S2C30 -> bootstrap` was established here.
`login-to-character-select-records.json` points the bootstrap back to this same
source constant; it supplies no missing adjacency. `world-unknown-first-batch.json`
reports C2S 41/71/12-byte follow-ups and 5-byte heartbeats after bootstrap,
without a raw current select-to-world transcript.

Do not substitute opcode `29` or `30`: neither is the saved embedded byte `2A`.
The separate `DecryptedPacketCorpus.20260807.v2.json` top-level S2C entries have
no opcode 0x29/0x2A/0x30; its sole S2C length-40 entry is opcode **0x3B**
(`evidence-package-20260806-s2c-opcode-3b`). That manifest indexes outer packets
and does not invalidate the embedded `2A` above.

## Identity And Literal Default Provenance

- The Classic corpus's later client identity (`C/protocol/evidence/battle-v1/client-builds.json`) is `God2_opt.exe`, SHA `6B127086E0C00014DE26137B4EC482801E06E0724C5C05C64561D7F9FF32BD9B`. The July JSON does not bind the complete retained stream to an executable hash. This later identity cannot silently certify July bytes or current compatibility.
- Current disk `C:\Users\risei\Desktop\God2\God2\God2.exe` hashes to `FB72296CAB5950B74D8F7C98155145F7C5F58749C3011ADB0540325B60749DD1`; `God2-run.exe` hashes to `FE4328489AA47ED634B123C5DD4FA21E56C9FEED8893C03F1FF5A6F23A1A88E6`. Both differ from Classic. These are disk identities, not a claim about a running process.
- `E/CurrentWorldIdentity.json` explicitly says frozen official bootstrap map identity is `NOT_FULLY_DECODED`. Its separate **DbBackedExperimental** map `1785918668`, scene `1`, region `r_b720effd89db741cf7bb9830f6a01bee`, "Fenghua town candidate", spawn `(4860,34399,0)`, direction `South`, comes from `NormalizedContent:Phase4DbBackedRuntime`. This is experimental configuration referencing a mounted baseline, not decoded `2A` map/coordinate proof.
- `E/WorldProtocolRecovery.Phase3.Batch1.json` preserves actual movement sample encoded `0A0080B8D9C14BA69488`, decoded `0A00803859F9125F86D7`: offsets 5/6 give **4857**, offsets 7/8 give **34399**. This proves that recorded sample, not exact x=4860. Phase31 explicitly leaves coordinate scale `NOT_FIXED`. Neither sample establishes a map ID or maps these coordinates into the embedded `2A` body.
- `E/WorldContentRecovery.Phase41.MapRuntime.json` calls the frozen runtime map/scene/region `UNRESOLVED_FROM_DB`; the golden bootstrap was sent without DB map binding. No literal current map/coordinate interpretation is promoted by this sidecar.
- Current `R/src/game/Character.h:10` and `Entity.h:10` initialize map `1`, x/y `100,100`; `R/src/core/Application.cpp:44` calls map 1 a **mock map**. These are synthetic implementation defaults, not captured world defaults. The historical `2A` byte string above has retained-byte provenance; its field meanings require main's current parser check.
- XJZ `X/data` is empty in this extraction. Read-only SQLite checks find **zero rows** in `account_login_sync_sample`, `character_create_sample`, `character_profile_sync_sample`, `teleport_flow_sample`, `official_memory_capture_sample`, and `evidence_reverse_probe_capture_sample`. Its static tables and capture-target plans supply no select/world packet or captured spawn coordinate. `X/evidence-transport-binding-v0.md` explicitly leaves destination maps/coordinates and packet results to official flow samples. No broad map catalog was used.

## Reproduction Hashes

All below were computed from retained bytes during this task; source file hashes
for the class, Phase32 JSON, and bootstrap JSON also match `C/SOURCE-SHA256-MANIFEST.txt`.

| Artifact | SHA-256 |
| --- | --- |
| Runtime class file under C | `CB65FA7A8873B0D299A1727D4A388072494C2323168669A5DDDAD3DC39311BCA` |
| Extracted 1797-byte stream | `9DA6C91446FB40ABB223723091BAFD8931F2CAE5CA08F33456191377E2FDFA03` |
| E/WorldProtocolRecovery.Phase32.MountStateSource.json | `8C374A564602D4F5BB66293D2E0E22824983D2880F2D6309C2485E21D694D857` |
| E/WorldBootstrapSequence.json | `3723EB3E7828C7035AA0E16211C8DF1BF7CD76C7137BE27718D905A1C51595DC` |
| E/WorldSemanticDispatchMap.json | `1C7585C9357FAD2407E6EA81BC76F4F612A14E92F480214610E3600254625940` |
| E/CurrentWorldIdentity.json | `103175D250C6562DE0598C5DD752875F7565AB45AFD5B94FCC9D63468FAA715F` |
| E/WorldProtocolRecovery.Phase3.Batch1.json | `B5B170B5D7CAA2DAEA5EAAD18A6C4DCE4AD06A59C067ACDC0AB9F7887C84E13D` |
| X/xjz_evidence.sqlite | `44048EE3D664F1418E60EAA267D46E4BA118AA3689FAE03F7350D544A9FC1774` |

Changed paths: only `docs/research/legacy-world-entry-provenance-20260919.md`.
