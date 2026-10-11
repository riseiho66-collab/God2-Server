# TW255: owned blacklist input, persistence, reply and initial replay

Phase1 source connection only. No build, compiler, test, runtime, native/client
execution, codec execution, game database/SQL access, migration or deployment.

## Actual bidirectional branch

The feature connects original TW C89 add-name and C8A remove-row input to an
owned SQLite transaction and original A5/A4 replies. Explicit configuration
selects the feature in the actual Application, after the final existing world
handler has been chosen. It is not an unused factory or a competing server.
Existing parser variant indices and defaults are preserved by appending the
typed request and optional flag.

The ordered wrapper keeps non-blacklist contiguous runs with the original
handler, and combines its already framed replies with the blacklist replies in
input order. The fresh-ready hook marks the exact Session/owner/battle for
initial replay; a subsequent successful real Tick puts the durable A5 rows in
the normal returned-response queue. This avoids sending a later replay ahead
of an earlier response in the same input batch. Submission or clearing a
pending replay marker is not socket completion or a native acknowledgement.
Replay sends inactive A4 before active A5 in bounded batches. Unknown ID/classC
removal is a proven no-op; it does not take the matched-row missing-name edge.
After a disconnect, the next fresh admission restarts the durable replay,
including deleted-row tombstones. Initial replay must exclude intervening
mutations that could otherwise be followed by a stale A5 page. At most120 rows
and2520 logical bytes are replayed per Tick. The complete bounded rowset is
pinned and requalified per chunk; a changed rowset closes/reconnects rather
than silently skipping a reactivated earlier ID. Only blacklist mutations are
gated during initial replay; unrelated existing input remains available.
If unrelated gameplay changes the battle generation during unfinished replay,
the next successful real World Tick for the same exact Session/account/character
restarts from inactive rows with a fresh pinned rowset. It preserves queue order
and avoids leaving the feature permanently pending after returning from battle.

The repository validates the actual owner and one unique current CP950 target
name/profile, quota and row ownership on the same connection before mutation.
Mandatory pure Session Current reaches the transaction, before writes and
COMMIT. Full owner and new-target root snapshots are re-read exactly; callback
changes/autocommit and caught reentry invalidate the operation. It owns the
complete row material before committing; wire/vector projection may allocate
afterward. A commit is durable
even if later queue submission or connection lifetime fails; no fake rollback
or fabricated error acknowledgement is used. C8A can remove only an existing
row belonging to its actual account/character; a public DWORD is not authority.

## Same-image original wire and client boundaries

Mapped image149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763:

| Record | Exact logical shape |
|---|---|
| C89 |17 bytes: opcode plus16-byte CString area; editor caller allows at most14 encoded name bytes. Post-NUL native stack tail is unwritten, not required zero. |
| C8A |5 bytes: opcode plus full little-endian DWORD row ID. |
| A5 |21 bytes: opcode, full DWORD row ID,16-byte CString area; receiver creates class0C00. |
| A4 |5 bytes: opcode plus full DWORD row ID; receiver removes classC only. |

Native255 retains14 bounded code spans/2,195 bytes/736 instruction sites and
two dispatch cells/eight bytes. Six exact intervals from the separate peer
5fcf image match byte for byte; that does not make the whole images identical.
The source-ready13-span epoch remains retained separately from the added
476DD0 wrapper boundary. Global new native coverage and opcode values stay0.

The main contact bank guards count71 before its duplicate search. A matching
full ID/class overwrites the main row without incrementing the count, but
does not refresh the separate ten-name cache. New classC appends a name only
while that cache has room. A4 directly swaps/removes the matching name and
decrements the cache; its missing-name edge can still decrement the count.
The interaction/refresh helpers have unqualified opaque side effects. These
facts are format/lifecycle boundaries, not complete rendered-client acceptance.

The ordinary client initializer seeds a nonC GM row with ID0xFFFFFFFF. The
server reserves that ID and0. It never fabricates or publishes that GM row.

## Explicit CUSTOM-0096 policies

Server ownership scope, schema, allocator, quota and name lifecycle are custom
persistence policies, separately recorded in docs/custom-designs.json.

- Exact CP950 identity bytes remain unchanged; no display-language conversion,
  Unicode folding or CP936 alias selects a target. Ambiguous names fail.
  A valid non950 owner has blacklist unavailable; unrelated Tick/world/chat
  flows continue. Unsupported scope is not treated as corrupt saved data.
  Self ID and the explicit byte-ASCII-fold self-name guard are excluded.
- A row's captured name is immutable. Its target common ID records provenance
  at creation, with no live target FK. Rename/deletion does not silently change
  that row; a new name requires a new ID. Reuse of the captured name remains
  subject to this name-based policy. No all-social identity guarantee is claimed.
- Owner deletion cascades compatibly through its character_id. Deleting a
  target does not block existing character deletion or silently remove another
  owner's row without a corresponding native removal.
- Committed AUTOINCREMENT IDs1..0xFFFFFFFE are never reused. They are not common
  character IDs. Future contact kinds must share the allocator or establish
  disjoint full-DWORD namespaces before publication: a native first-ID scan
  can otherwise select the wrong class.
- Delete retains an inactive immutable tombstone. An owned repeated C8A can
  return A4 after a lost post-commit reply. Adding an inactive same name may
  reactivate that same ID; the allocator never repurposes it to another name.
- At most ten active entries and4096 lifetime captured names per owner are
  conservative custom limits. No implicit tombstone garbage collection resets
  the ID namespace; existing names may reactivate within the active quota.
  Ten cache slots and71 main rows do not establish an official server entitlement.
  Duplicate add reuses the same durable ID and immutable name.

Storage installation is an explicit schema-only operation. Ordinary reads,
login and ready handlers do not create tables. Configuration defaults off;
missing or incompatible schema fails rather than being repaired on read.
Shared tables remain the default. Nothing is installed or activated here.

## Scope and accounting

Nine existing C++ files and five new files implement this limited branch.
Two scoped request/storage/reply source branches are added. This does not
complete all contacts, mail, social gameplay or the whole TW game.
The connected scope is the requesting exact Session and its fresh-world replay.
Concurrent same-owner Sessions do not yet receive each other's live mutations.
An owner rename to an existing captured blacklist name also needs lifecycle
integration: native A4's self-name guard can leave that client row present.
Neither variant is counted as connected; the frozen rename flow is unchanged.

TW known C2S candidate union156, world S2C252 and battle table110 remain
separate from source connections. The round report records the parser and
reviewed-branch deltas. Full directional/state/variant route denominator and
TW percentage remain unknown; no64.6% or other subset ratio is called overall
completion. Mixed partial source segments239→240 are not completed routes.

Frozen chat/filter, IME, authentication, fonts, text conversion, accounts,
saves, client binaries and the peer browser files are not rewritten. Server
chat filtering, cross-codepage target lookup and all other contact/mail
features remain outside this limited branch. PK still needs real complete
combat inputs, RoomAuthority, dual Session publication and terminal/recovery.

Evidence: C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-blacklist-authority-source-255.
Full before/candidate/final files and native originals are retained. File seals
and source review are not gameplay acceptance. The main goal remains active.
