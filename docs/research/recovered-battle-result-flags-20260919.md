# S2C86 result flags codec, 2026-09-19

`src/protocol/RecoveredBattleResultFlags.h` is an owning, lossless codec for
17-byte S2C86 discriminator3 records in the qualified position0..27 domain.
It is not C2S86 dialogue close, a server battle policy or a damage formula.
Callers must establish S2C direction and battle context; bytes alone cannot
authenticate direction. No runtime route or emitter is installed.

Authority: [bounded native result-field execution](current-battle-result-fields-20260919.md).
The pinned current image executes 114332 -> 117480 -> 12C3E0 with real
entity lookup. Raw WORD at3 and DWORD at5 remain unnamed gameplay fields.
The native mutable queue normalizes flags to1 when bit0 is set. The codec
exposes this normalization separately while preserving every original byte
on encode. Bytes9..16 remain opaque. Positions outside0..27 are outside the
qualified codec domain, not proven native rejections.

Verification:

- Standalone C++ bounds, byte-domain, ownership and exact round-trip checks.
- Native/C++ differential suite: 2,444 additional cases, plus8 inherited
  native-proof tests (10 unittest methods total).
- Independent black-box verifier: 8,300 mixed valid/invalid batch inputs,
  recovery after rejection and normalization idempotence (2 tests).

These checks do not validate transport, downstream renderer behavior,
authoritative state generation, damage arithmetic or live client acceptance.
`runtime_emission_enabled` and `runtime_mutation_enabled` remain false.
