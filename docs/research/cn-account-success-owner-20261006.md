# CN account success, shared grant and native disconnect source

Source phase only: no build, test, native/game/server execution, production DB
access or deployment. Previous reports and native baselines are retained.
Traditional/Simplified conversion, codepage edges and native fonts are unchanged.

## Complete native data requirement

SharedAccountSuccess requires a complete205-byte S2C1D and17-byte S2C0A from
the authenticated native data owner. Its move-only NativeData keeps all opaque
bytes and clears its credential record when discarded. It has no default
success constructor and never copies the incoming04 tail as an issued record,
replaces the credential with a password hash, chooses flags/paytype to bypass
the client, or zero-fills missing billing fields. Layout parsing does not prove
the issuer or serialization rules. The actual supplier remains open.

The exact shared Login snapshot delivered to this connection's Verified
continuation is tracked weakly. Success requires this exact object, verified
account identity, and issued1D account_id matching that identity. Incoming04's
claimed account_id/check_key supplies no authority. The newly issued1D key is
bound to this account/session, its enabled actual catalog destinations and an
explicit issuer deadline through SharedWorldAdmission.issue. Cross-process key
uniqueness/revocation and delayed-success credential-revision policy still need
the actual issuer owner; client30-second waits are not authorization TTLs.

Currently the qualified supplier form preserves exact account and credential
echo bytes.0047FE30 uses native_stricmp; case-changing native issuer forms
remain open. Authentication and control identifiers are not case-converted,
translated, rendered as display text, logged or sent to Lua by this controller.

## Output and continuation

The whole catalog is qualified/serialized before grant issuance. Only enabled
destinations represented by actual configured node slots enter the grant.
The installed SharedAccountSelection uses the same catalog and actual common
RecoveredCharacterRepository. Failure after grant issuance revokes that owned
pending grant and closes the connection; it does not expose generic gameplay.

The controller queues1D, complete ordered04/05/06 catalog records, then0A.
The 2026-10-07 queue-admission increment now submits the entire ordered sequence
through send_batch and completes its held credential ingress only after the
network queue result returns to game and confirms the exact grant. Until this
confirmation, close revokes the unpublished grant before account detach.
Published selected handoffs retain the existing distinct-world lifetime.
See cn-login-queue-admission-20261007.md; queue acceptance is not TCP delivery
or native waiter acceptance. No native data supplier is created by that change.
This is an integration emission order supported by the native receive switch,
not a recovered official server ordering rule.1D compares names/credentials,
copies204 bytes, handles provider flags, clears its record cursor and loops.
04/05/06 populate the directory.0A copies16 bytes and exits the waiter through
the local mutex-state gate. Records needed by this waiter must precede0A;
success cannot be asserted merely from a1D frame. Provider/UI exits and local
gate failure remain real client conditions; native acceptance has not run.

## Connection-owned C2S0A

0047F310 conditionally copies an account string through its NUL into a local
16-byte buffer, sends0A payload16, flushes and closes its account network.
Trailing stack bytes are uninitialized. The server's existing bounded parser
requires a NUL and does not assign meaning to those bytes. SharedAccountSelection
now accepts this terminal record, with an exact authenticated account-name
echo, either alone or following qualifiedA6 records. It never resolves another
account, session or grant from the claimed name. Malformed trailing input is
rejected before earlierA6 output; no disconnect reply is fabricated.

Transport cleanup detaches only its owned account session. It preserves the
already selected/world-owned grant needed by a distinct world connection.
Longer/nonterminated native names, case-changing issued aliases and other
account controls remain unqualified rather than silently normalized.

## Evidence and remaining work

Primary sources are pinned0047FE30 and0047F310 C/ASM/PE bytes, preserving
cn-admission-contract-agent-01 hashes. cn-billing-byte5-agent-01 qualifies
billing copy/opaque byte5 and local completion. Main source and exact native
spans are sealed in cn-account-success-owner-01. No observed request/response
payload containing real account credentials is written to these artifacts.

Actual native1D/0A fields/issuer, summary07/full world1F/02/2A suppliers,
authenticated alias/row lineage, actual listeners and Application controller
composition, TW enrollment in common ownership, bootstrap and later gameplay
are still open. This adds a conditional source chain and a connection-owned
disconnect branch; complete bidirectional routes added0. Whole-game route and
variant denominator/completion percentage remain unknown.
