# ZENITH Local Review And Certificates

This implements a narrow review workflow for G02, G03, G04 and G04.5. It does
not recover runtime evidence, authenticate remote humans, certify network roots
or establish real-client protocol compatibility. No real reviews/certificates
have been issued for this project. A real host capture now has G02 consistency
READY_FOR_REVIEW, with trust UNREVIEWED; independent human review is the current
G02 blocker. See ../../docs/G02_HUMAN_REVIEW_HANDOFF.md.

## Authority Boundary

The workspace owner must create `artifacts/review-policy.json` with exactly:

```json
{"schema_version": 1, "reviewers": ["owner-chosen-human-reviewer-id"]}
```

This is an example, NOT an installed policy. The agent must not create a trusted
reviewer identity or attest on behalf of a human. Missing policy disables
submission and promotion. The capture producer cannot approve their own work.
The named reviewer must personally inspect the native evidence and relevant
regression/reproduction results, not merely tick boxes because Python passed.

Identity strings are local policy identifiers, not authenticated identities.
Anyone with write access to this trusted workspace can impersonate them or alter
the policy. SHA256 detects byte changes; it is NOT a digital signature. External
identity authentication, signed review envelopes, trusted timestamps and external
append-only checkpoints are future interfaces, not implemented guarantees.
Accordingly, a VALID certificate means valid under this local human-review
policy. It is not independently verified cryptographic proof of a person's identity.

## Workflow

First ingest a genuine capture with the [runtime intake](RUNTIME_CAPTURE.md).
Then, from the project root:

```powershell
python tools/research/gate_review.py prepare CAPTURE_SHA256 G02 review-g02.json
# Independent human completes the request and supplies test-report.txt beside it.
python tools/research/gate_review.py submit review-g02.json
# Submission records the review only. Explicit promotion is a separate step.
python tools/research/gate_review.py promote REVIEW_SHA256
python tools/research/gate_review.py audit CERTIFICATE_SHA256
python tools/research/gate_review.py status CLIENT_ARTIFACT_SHA256
```

For G03, G04 and G04.5, `promote` also requires
`--prerequisite PREVIOUS_GATE_CERTIFICATE_SHA256`. All certificates in a chain
must bind the same artifact AND capture. Combining captures is deliberately not
supported in v1. G02 binds directly to the reverified artifact/capture.
G05 certification is disabled: a Winsock-name match is not a verified network root.

```powershell
python tools/research/gate_review.py revoke CERTIFICATE_OR_REVIEW_SHA256 --reviewer HUMAN_ID --reason "Independent review found a contradiction"
```

Revocation appends an immutable object. It does not delete or edit the target.
Descendants become unusable on their next audit; no descendant rewrite is needed.
`audit` lists `affected_dependents` and the nested dependency chain. Revoking an
approval prevents new certificates from that approval; reissuing the exact
revoked certificate is rejected. Revocations themselves cannot be revoked.

`submit`, `promote` and `revoke` CLI operations emit fresh report snapshots under
`artifacts/reports/review-*`. API consumers explicitly call RuntimeStore.report.
Snapshots are historical; always run audit/status before relying on a certificate.
`audit` exits 2 for an invalid object, 1 for malformed/corrupt/missing input,
and 0 for valid input. `status` exits 0 even when gates are BLOCKED; inspect JSON.

## Review Requirements

The generated request starts without a reviewer, timestamp, decision or rationale,
with human_attestation=false and every checkbox false. It cannot be submitted as-is.
Required fields are version, capture_id, gate, reviewer, reviewed_at, decision,
rationale, human_attestation, checks, evidence_ids and test_report (relative path).
All fields are strict; no unknown fields are accepted. Decisions are APPROVE/REJECT.

Approval requires runtime source_kind, READY_FOR_REVIEW consistency, all gate
event IDs, a nonempty UTF-8 test/reproduction transcript, independent reviewer,
explicit human attestation and the complete gate-specific checklist. A transcript
is content-hashed and retained verbatim; this tool does not infer test success by
parsing arbitrary console output. The human confirms relevance, results and scope.
It does not accept generic server unit tests as proof of successful client unpacking.

The common checklist covers native trace, artifact/module provenance, execution
semantics, regression results and unresolved counter-evidence. Specific checks
cover unpack transitions, stable OEP continuation, all repaired import targets,
or independent analysis-image/disassembly quality, depending on the gate.
REJECT can preserve a structurally valid but unready/synthetic observation.
Synthetic input can never support approval.

## Object And Provenance Model

Objects reside at `artifacts/proofs/<SHA256>.json`. SHA256 covers the canonical
JSON bytes, including schema_version, kind, artifact_id, capture_id, created_at,
tool_version, parents and payload. `proof_objects` in research.db indexes exact
bytes; god2.db and artifact-vault metadata/schema are unchanged.

| Object | Parents and retained provenance |
| --- | --- |
| review | Capture/artifact references; evidence IDs; reviewer/checklist/rationale; policy snapshot/hash; transcript/hash |
| certificate | Approving review; immediately preceding certificate except G02 |
| resolution | Previous resolution if any; counter event; state; supporting references; independent reviewer; policy and report hashes |
| revocation | Target review, certificate or resolution; acting reviewer, reason, policy hash |

Capture IDs resolve to exact manifests and attachment hashes. Artifact IDs resolve
to verified original bytes. Thus the local chain reaches the original SHA256;
it does not invent function, packet, experiment or original-client session proofs.
Those are not available yet. The validator version includes hashes of all five
Python source modules in the current assessment/review path. Changes invalidate
old approval/certificate eligibility until independently re-reviewed. Existing
revocations remain effective. Removing a reviewer from policy invalidates approvals.

Audit rechecks archived bytes, indexes, capture consistency and dependencies.
A live rejection for the same artifact/gate blocks approval, including across
captures. Resolving a rejected review requires an explicit revocation with rationale.
Runtime counter-evidence anywhere in the same artifact/gate blocks certification
unless independently resolved as RESOLVED_SUPPORT. OPEN, RESOLVED_REJECT and
INCONCLUSIVE remain blocking. Prepare a worksheet with `prepare-resolution
CAPTURE_SHA256 COUNTER_EVENT_ID resolution.json`, then a trusted independent
human supplies the rationale, supporting event references and reproduction
report before `resolve resolution.json`. The agent must not attest for them.

Resolution proofs are append-only: updates reference the previous head, stale
branches are rejected, and original counter events remain unchanged. Revocation,
policy loss or invalid evidence reopens the contradiction. Support cannot repair
failed byte-level checks. Fresh schema-2 approval must acknowledge the current
resolution IDs; old approval does not revive automatically. Audit output omits
transcript text while retaining its hash; the archived proof retains the report.

## Operational Limits

This is a single-writer trusted-workspace tool, not a concurrent review service.
Keep backups of proofs, runtime captures and research.db together. File publication
and SQLite commit are not atomic together. A crash can leave a missing/unindexed
object; auditing then fails closed. There is no automatic repair/recovery command.
Restore a consistent backup or investigate explicitly; do not delete contradictory
records to make an audit pass. Hashes cannot detect coordinated whole-store rollback.

Bounds: 4,096 proof objects, 1,024 captures per artifact audit, dependency depth 32,
2 MiB per object, 256 KiB UTF-8 transcript. Capacity failures block rather than skip.
Remote signing, multi-writer transactions, certificate portability and general claim
blast-radius analysis are deferred. The current blast radius concerns review and
gate certificate dependencies only.
