# Companion evidence boundary follow-up, 2026-09-19

## Deliverable

Hardened `message_claims` against inconsistent or extended source records.
Black-box calls using real decoded SystemMessage records demonstrated that the
previous function accepted a forged SHA-256, accepted swapped identity/text
fields while retaining the original raw record, and copied unsupported fields
such as `growth_formula` into the claim's `source`. Returned claims also aliased
the caller's dictionaries, permitting subsequent mutation of evidence.

The function now reconstructs canonical records from raw bytes, requires exact
agreement of all derived fields and the six permitted record keys, checks source
location types/ranges and single-record structure, and returns independent
records. Unknown progression fields are rejected rather than carried forward.
Exact message ID/text checks and `runtime_eligible: false` remain enforced.

This is evidence extraction validation, not a gameplay or network defect.
Record consistency does not authenticate arbitrary source bytes or prove that a
positive offset belongs to a particular file. Source membership remains checked
against the actual client files by the recovery path and real-data tests; CLI
`--check` compares the complete rebuilt artifact, including source manifests.
No new catalog identity, protocol, growth, reward, skill or combat semantics are
inferred. Opaque positional source fields remain opaque.

## Evidence Read Before Changes

- `docs/research/gameplay-lanes-20260919.md`
- `docs/research/content-recovery-20260919.md`
- Existing `recover_companions.py` and all eight existing companion tests.
- XJZ root:
  `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`:
  `evidence-combat-pet-v0.md`, `evidence-god-acquisition-rule-v0.md`, and
  `evidence-combat-pet-skill-feed-unlock-rule-v0.md`.
- Classic root:
  `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`:
  `tools/God2.GameplayContentRecovery/OfficialImmortalCatalogExporter.cs`,
  `tools/God2.GameplayContentRecovery/OfficialBattlePetCatalogExporter.cs`, and
  `src/God2.ClassicServer.Runtime/PetLifecycleRuntime.cs`.

Classic's PET exporter calls its category battle pets and describes a different
row count. That designation is not imported: the current 147 PET rows remain
`pet_unqualified`, separate from COM/NCP. Both legacy trees are reference-only;
their formulas, runtime state and textual item rules do not qualify current
gameplay. Current original client bytes remain authoritative.

## Verification

Working directory for every command:
`C:/Users/risei/Desktop/God2/God2-Server`.

Before implementation, these new regressions failed as expected:

```powershell
python -B -m unittest tests.research.test_recover_companions.CompanionRecoveryTests.test_unsupported_progression_fields_rejected tests.research.test_recover_companions.CompanionRecoveryTests.test_message_identity_transplant_rejected tests.research.test_recover_companions.CompanionRecoveryTests.test_claims_do_not_alias_caller_records -v
```

Result: exit 1; 3 tests, 7 failures (five unsupported-field subtests plus identity
transplant and aliasing), 0.472 seconds. A separate direct probe also printed
`unsupported_progression_copied=True` and `forged_hash_accepted=True`.

After implementation:

```powershell
python -B -m unittest tests.research.test_recover_companions -v
```

Result: exit 0; 14 tests passed in 6.980 seconds. Existing tests were rerun because
record validation affects message extraction and the complete recovery artifact.
New coverage includes nine provenance mutations, five unsupported fields,
identity transplantation, internally consistent wrong message text, caller
mutation isolation, and a complete rebuild against both legacy reference roots.

After tightening the single-record LF boundary, its new focused regression ran:

```powershell
python -B -m unittest tests.research.test_recover_companions.CompanionRecoveryTests.test_self_consistent_invalid_raw_records_rejected -v
```

Result: exit 0; 1 test passed in 0.454 seconds, covering concatenated real records,
an extra LF, embedded NUL and an empty record with self-consistent hashes/fields.
These runs cover 15 distinct tests; the final 15-test suite was not rerun as one
batch. No mocks or synthetic positive companion definitions were used.

After the LF boundary change, the read-only CLI verification also passed:

```powershell
python -B -m tools.strike_lab.recover_companions --client-root C:/Users/risei/Desktop/God2/God2 --classic-root C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource --xjz-root artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation --output artifacts/world-atlas/companions.json --check
```

Result: exit 0, `checked: true`, 9 message claims. Counts: ItemType 46, GOD 34,
PET 147, COM 2070, NCP 1165, GodLevel 4, FightPetSkill 254,
NewFightPet2Skill 255. Artifact bytes unchanged, SHA-256:
`e75442ce039273f6dd3cf1af88c8b72853af444145bf2d3969102c4f6d4890c3`.

## Scope and Acceptance

Changed only `tools/strike_lab/recover_companions.py`,
`tests/research/test_recover_companions.py`, and this new document. The existing
artifact was only read. C++20 core, Lua gameplay, SQLite, shared build/state/docs,
world actor and NPCList native loader were not edited. Python used `-B` to avoid
writing bytecode caches.

All verification is offline Python API/CLI evidence testing. No UI automation,
original client launch, public connection, server process, native emulator run
or live E2E acceptance occurred. Runtime ownership/progression remains unproven.
