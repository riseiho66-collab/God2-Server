# Owned guild membership: CUSTOM-0078 development

## Delivered in this round

`RecoveredGuildMembership.h` implements the build-matched S2C8D prompt and
C2S6F name request. `OwnedGuildMembershipConversation.h` implements an isolated
authenticated-owner request lifecycle. Neither is registered in Application
or Session; it cannot create a guild, charge a player or approve membership.
This is development progress, not formal playable acceptance.

Native identity:

- Original mapped image SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Installed client SHA256 `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
- Formal server remains CUSTOM-0077, SHA256 `5fb51103e8b99a88ebdb1b815fa4cfc9e493d0d472a6b5a6537f2f0f4252bd1a`.

## Native wire and evidence

S2C8D is five logical bytes. Native dispatch468B8C calls4EE4E0. Body WORD0
copies to UI+AE64; byte2 selects create0 or join1; byte3 is unread. Modes0/1
prepare input window UI+232E20 through4F1E50(4/5),4F1890. Source titles are
`建立`/`加入`; descriptions are `建立洞府需求5萬`/`請輸入洞府名稱`.
The last description is not permission, a membership result or an invitation.

Forty unchanged original/current consumer cases cover valid and invalid modes,
opaque-tail variation, alternative input-mode branches, NULL selected actor,
context0000/FFFF and preserved header/name/selected-actor state. These execute
native branches with explicit leaf models; they are not live UI rendering.

Ordinary input submit4F21A0/4F2390 reaches4EE5F0. Modes4/5 append6F to4132E0:

| Logical offset | Width | Meaning qualified in producer |
|---|---:|---|
| 0 | BYTE | 6F |
| 1 | WORD LE | UI+AE64 copied context |
| 3 | WORD LE | First WORD read through existing UI+8688C selected actor pointer |
| 5 | 16 bytes | NUL-terminated name buffer; padding can contain stack residue |
| 21 | BYTE | Create0 / Join1 |
| 22 | BYTE | Unwritten stack residue |

Twelve original/current producer cases agree exactly for two operations, three
names and two stack residue patterns. The codec preserves the incoming opaque
bytes for reproduction, but its canonical name discards every byte after NUL.
The selected actor WORD has not been proved to be a server-authoritative NPC,
player or invitation identifier; the new lifecycle ignores it and the tail.

8D does not establish a selected actor pointer. It opens even with NULL; later
6F input submission dereferences that pointer. A future actual interaction
entry must qualify the client workflow before opening this prompt. The already
accepted help-to-roster route cannot simply be reused as proof that a create
prompt is safe.

## Separate native member management

The worker's final `producers/trace-v02.json` qualifies27 equal code intervals
and42 call bindings. It supersedes the preliminary terminology:

- 71: selected member operation; admission versus promotion remains unknown.
- 72: role-dependent refusal of an applicant, expulsion of a member or removal
  from office, confirmed by ProgramMsg649/648/344.
- 73 management branch: leadership transfer, ProgramMsg347. It shares opcode
  with previously installed self-leave; no extra authority has been granted.
- 75: dissolution, ProgramMsg346.
- 76 and95: diplomacy between guilds, not player membership invitations.
- 4EF5E0/610/640: roulette operations, not guild management.

Native local roster slots are never SQLite character/account/guild identities.
The accepted CUSTOM-0077 self-slot-only leave implementation is unchanged.

## Isolated custom lifecycle

CUSTOM-0078 supplies a30-second steady-clock lease, lifetime-nonwrapping WORD
context and a single bound operation. Owner equality includes transport session,
account, character, world generation, area, scene, position and codepage950/936.
Current interaction authority is required at open and consume. A changed owner
or unavailable current interaction invalidates the lease. Invalid context or
operation cannot renew it. A valid bound attempt consumes the lease before name
validation, including failed/throwing validators. A replay cannot retry a write.
Cancel/world-departure invalidates the lease; disconnect additionally releases
state only under the caller's lifetime-unique transport session ID guarantee.

These timers and authorization policies are CUSTOM; no original server rule
is inferred. Application must provide a real ready/world/battle/transfer gate,
production lossless name validation and the invalidate/disconnect calls.
Returning an Accepted value is not a database commit or a success reply.

## Validation and limits

`validation-v01.json` records a successful fresh C++20 build, one CTest suite
and the frozen-chat verifier. The suite covers framing truncation, fixed native
fixture bytes, all256 opaque residues, name canonicalization, cross-session
attempts, ownership/world/language changes, expiry boundaries, replay,
validator failure and context exhaustion at65535. The exhaustion loop is one
boundary test, not65535 gameplay features or live acceptance cases.

Independent review found no reproducible codec/lifecycle defect, and explicitly
retains the production responsibilities above. Only a new test-target addition
changes an existing tracked compiled-source path (`tests/CMakeLists.txt`).
Existing Application, Session, chat, authentication, IME, repositories, client
and formal server binary remain identical to accepted0077. No database writes,
test grants, service restart or visible-desktop操作 occurred in this round.

Protocol/lifecycle scope:100% of this bounded delivery. Formal playable
create/join acceptance:0%. Whole-game completion has no trustworthy denominator
and is not estimated from tests. This design remains ISOLATED_NOT_FORMAL.

## Next implementation gate

1. Qualify a player-accessible original interaction entry and selected actor
   lifetime; do not confuse the help toolbar or diplomatic invitations with it.
2. Implement exact lossless names and simultaneous native name-collision checks
   for both client languages; preserve case and reject unsafe printf names.
3. Establish native authoritative creation/join evidence where available. If
   unavailable, document CUSTOM rules and balance them before activation. The
   visible5萬 text alone does not establish currency, fee timing, eligibility,
   leader powers, duplicate-name handling or approval rules.
4. Commit owner membership atomically in a separate gameplay repository. Never
   use maintenance admin_create/admin_assign as gameplay permission. Preserve
   saves and coordinate frozen2D/91/92 membership projection after commit.
5. Wire typed Session/Application routes with record-order and stale-lease
   checks; qualify the actual hidden own-server client flow in950/936 before
   promotion, with the frozen chat release gate and saved-row checks.

Evidence resides in `artifacts/research/native-guild-membership-0078`; final
round receipt is `implementation-report-v02.json`. The retained v01 receipt
misnamed SQLite's unused `PRAGMA user_version` as the schema version. The
v02 correction reads `MAX(version)` from the actual `schema_migrations`
history; neither step migrates or writes the database.
