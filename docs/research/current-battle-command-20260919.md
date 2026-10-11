# Current basic-attack input boundary, 2026-09-19

## Delivery and integration

- `src/protocol/RecoveredBattleCommand.h`: header-only C++20,
  `god2::RecoveredBattleCommand::parse_logical(std::span<const std::uint8_t>)`
  returns `std::optional<BasicAttackRequest>`.
- Input is exactly one 17-byte decrypted C2S logical record, including `0x35`.
  Parent can use `RecoveredWorldFrame::decode(wire)` and its own record splitter.
  A whole wire frame, multiple records, and trailing bytes are rejected.
- `runtime_mutation_enabled` is false. A populated optional is structural
  parsing only. No authoritative battle session, participant ownership, turn,
  target existence, action permission, or outcome is established here.
- Only action byte `1`, the basic-attack family corroborated by Classic, is
  supported. Skills, continuation, and every other action are rejected.
  No CMake, runtime, session, application, DB, or shared transport edits.
- A separate [kind-0 skill record parser](current-skill-command-20260919.md)
  now covers a bounded action `0x03`/`0x83` shape with mutation disabled.
  This basic-attack decoder's accepted actions are unchanged.

## Evidence searched before reversing

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.
Files below are under `src/God2.ClassicServer.Protocol/`:

| File | SHA-256 |
| --- | --- |
| OfficialBattleCommandWire.cs | 06e147cac8ac7aed5df46fdbddd7cd114f0bccd13e2e9f22b11e6f86be4549c5 |
| OfficialBattleBatchWire.cs | b7175fc6faa06ede5e4ba515ee1b76deda24a99f56906a6f85a8da682ea2911f |
| PublicBetaCompatibilityBattleWireAdapter.cs | 764a29843fcdf884ede6eab9a1b3fe75527b52530dd22cdcf8d08c39bb6c00c3 |

These supply the `0x35` lead and action-family label, not current-image address
authority. Their `God2_opt` RVA `0x14E7D0` points into CRT code in the current
image. Their three-mask interpretation and gameplay-state gate were not copied.
The adapter explicitly withholds production mutation; the batch codec concerns
server output and is outside this input contract.

XJZ root:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.
Searched battle/command/attack material, then read
`cpp/xjz_combat_command_contracts.hpp`, SHA-256
`e25f8c5b8e89e6207b0185b640c6e5afd9b70a83251024813820695f26729ea3`.
It defines semantic session/actor/skill service contracts, not this client's
wire builder. None of its gameplay or formula assumptions were promoted.

## Current native authority

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
x86 base `0x400000`, RVA equals file offset.

Builder entry is RVA `0x118E50`, thiscall, four DWORD stack arguments:
action, actor position, signed target count, pointer to target bytes.
Only low bytes of action and position are used. Tests execute original code
from entry through the post-queue boundary `0x1191EE`, or the original early
return. Real lookup helpers `0x1156A0`, `0x11B8C0` / `0x11B900`, and queue
copier `0x132E0` execute without stubs. UI/state cleanup after that boundary is
not executed. Synthetic fixtures do not establish a successful live battle.

| Logical offset | Width | Current basic-attack behavior |
| --- | --- | --- |
| 0 | 1 | Opcode `0x35`; queue call at `0x11906B` |
| 1 | 1 | Actor low byte; unsigned `<=14` guard at `0x118E79` |
| 2 | 1 | Action low byte; only exact `1` accepted by this decoder |
| 3 | 1 | Side flag: 1 iff `this+A9E9C38 == 0` and `this+A9E9C3C != 0`, otherwise 0 |
| 4 | 1 | Unwritten stack byte, preserved without normalization |
| 5 | 2 LE | OR mask for target bytes 0..13 |
| 7 | 2 LE | OR mask for target bytes 14..27 |
| 9 | 4 LE | Raw storage initialized from DWORD `this+0x3C` |
| 13 | 4 LE | Unwritten stack DWORD for basic attack, preserved |

`0x118EC4` initializes body+8 with the complete context-storage DWORD;
`0x118EEF` clears only body+4..7. `0x119015..0x11904F` ORs target bits into
`body+4 + 2*(target/14)`, with bit `target%14`. Duplicate target bytes collapse.
Zero and negative counts generate empty masks. Count >14 returns before
building. There is no native target-byte range guard in this loop.

Consequently targets 28..41 OR into the low half of context storage. For
example, context `0x12348000` plus targets 28 and 41 becomes `0x1234A001`.
This is not promoted to a third target group. The decoder preserves the DWORD
and cannot distinguish this alias from an unchanged context with that value.
It only exposes the first two masks, rejects their upper two bits and more
than 14 distinct bits across those masks, and does not authorize those targets.
Callers must not interpret parsing as validation of an original target list.

Other original guards: at least one of `this+A9E9C38/C3C` is nonzero for action
1; `this+0x44` is nonzero; network object's byte `+0x2CB8` is nonzero before
queueing. These are client memory predicates, not recovered server-state
semantics. They are tested, not translated into invented server policy.

For a narrow negative control, native action 3 with a real synthetic lookup
entry (kind 0, ID byte `0x9B`, `this+0x468 == 0`) and targets 0,14 queues two
records. Actions are `0x83`, then `0x03`; parameter is `0x0000009B` and byte 3
remains unwritten. Both records are rejected by the basic-only decoder. No
skill catalog identity, cost, effect, or damage meaning is inferred.

## Verification

Run from repo root:

```text
python tests/research/test_current_battle_command.py -v
```

Six tests passed. Python pins the whole image, reuses the world-ready Unicorn
fixture, and compiles `tests/test_recovered_battle_command.cpp` in a private
temporary directory with C++20 and warnings as errors. Native output is fed
to the C++ executable; it returns every decoded field for comparison. Memory
write hooks prove unwritten bytes, with four stack poison patterns, actor and
action width checks, both side branches, boundary masks, duplicates, original
state guards, context aliasing, and the native skill negative control.
Black-box tests reject every truncated length, oversized/concatenated/framed
input, wrong opcode, unsupported action/flags/position/side, target high bits,
and fifteen distinct mask bits. The C++ assertions also enumerate all 256
action bytes. No sockets, UI, auth, client launch, or external services used.
