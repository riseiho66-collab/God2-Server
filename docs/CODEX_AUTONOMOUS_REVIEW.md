# Codex Autonomous Review

## Operative Policy

The owner replaced mandatory human review with Codex-only technical review in
directive SHA256 `5e0589dcacb0f129fa7b189bbb12a7ab7cd76cb28200f1421a2c4480754356d5`.
The directive is bound verbatim by the new G02 review tool. No human policy or
attestation is created. Earlier human-review instructions and reports are history,
not the operative blocker for this authorized research path.

The operative acceptance class is CODEX_VERIFIED, never HUMAN_VERIFIED. Approval
requires fresh technical cross-checks, counter-evidence examination and passing
regressions. Missing technical evidence still blocks progression.

## Narrow Implementation

`tools/research/codex_g02_review.py` currently issues only G02_CODEX_CERTIFICATE
for the original sealed transition capture. It is deliberately not a generic
issuer for G03, IAT, repaired images, network protocols or gameplay.

Independent checking means a different evidence path/algorithm, not a second
human: native stack/register/step output versus normalized events, manual struct
PE reconstruction versus the original pefile-based derivation, and fresh hashes
versus recorded attachment hashes. These checks cannot establish external origin
or protect against coordinated rewriting by someone controlling the workspace.

Certificate records live under `artifacts/codex-certificates/`, separately from
the unchanged historical human ledger. Contents include the owner directive,
file/source/log hash bindings, narrow claim, rationale, unresolved claims,
counter-evidence assessment and newly executed regression commands/results.
They are local unsigned content-addressed records, not digital signatures.

```powershell
python tools/research/codex_g02_review.py audit CERTIFICATE_SHA256
python tools/research/codex_g02_review.py revoke CERTIFICATE_SHA256 --reason "Evidence and reason"
```

Audit rechecks evidence/index consistency, bound files and registered counter
evidence/rejections. Changes or revocation fail closed. Source changes require
fresh review. Revocations are separate content-addressed records; no evidence or
certificate is deleted. No automated descendant certificates exist yet; future
issuers must audit same-capture prerequisites and implement dependency invalidation.

Legacy `gate_review.py status` continues to describe the human ledger only; its
BLOCKED is not the operative Codex review result. Consult the new certificate
audit, not a historical generated snapshot, for Codex acceptance.

## Claim Boundaries

G02 may confirm only the observed transition into restored bytes. It does not
confirm stable OEP, normal startup, imports, executable permissions or a repaired
analysis image. PAGE_READWRITE interpretation remains unresolved. The later
ddraw/termination observation limits startup claims and is retained in the
certificate's bound diagnostic archive; it does not negate the earlier RET.

Each future G03 capture needs its own fresh automated G02 checks and receipt.
An old capture's receipt cannot certify new events. Old sealed captures are
immutable. The immediate G03 experiment uses explicit return/exit breakpoints
to investigate the missing continuation, without patching the client or DLL.
