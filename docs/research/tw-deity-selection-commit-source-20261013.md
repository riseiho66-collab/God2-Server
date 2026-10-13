# Committed selected deity row and original S31 response

CUSTOM-0146 fixes two actual source problems in the existing Main C67 route.
The old helper read a full deity row outside the selection transaction and
preencoded its S31. The writer then checked only key presence and the selection
revision. A same-key deity update can change raw status/skills/revision without
changing selection revision, allowing row B to commit while the helper returns
row A. Even selecting the same key could bypass full row equality. Separately,
the old const vector response could require a copy/allocation on return into
optional after successful COMMIT.

Four existing C++ files now provide a private owning selected-row commit and
prepared reply result. The actual existing helper calls the typed transaction;
Main keeps its existing helper API, which moves the already prepared wire.
The original public repository select_deity implementation remains unchanged.

The new transaction owns the expected full row and selection before observers.
It qualifies actual main owner/catalog/row/selection/pending-battle sources,
rejects TEMP shadows/reentry and requires the complete requested raw19/raw29,
ordered saved34 bytes, revision and provenance to agree before any write,
including the same-key no-op. Existing selection CAS and pending-battle policy
remain. Intended write count/full row/selection readback are fenced while the
reserved transaction is open. Proof data/allocation exists before COMMIT.
After successful COMMIT, helper handoff uses no-throw moves of the owning proof
and preencoded mutable response. No old-source revalidation, allocation, SQL
retry or rollback is added after durable work.

The proof owns the one selected row, full64 account/character, repository
identity and actual before/after selection; it is not an entire current roster,
historical448 prefix, selected-menu adoption, local Written receipt or remote
ACK. A future Main publication must capture its one final whole original
aggregate response and connect the real committed marker to the same existing
skill source. Capturing only S31 or reusing a stale normal-entry restoration
cannot supply that next epoch. C56 action, MP/cost, other targets, effects/status,
formulas, persistence/next receipt and complete replies remain open.

This improves one actual C67 source branch; zero new native opcodes/formulas,
phase bindings or complete bidirectional gameplay routes. Source/10 pins28
current C++ files. No new Python project files. TW156 candidates/252 supported
S2C and parser75=50partial+11control+14unconnected; CN156/280phase/253supported
unchanged. Whole denominator/percentage unknown. PHASE1: no build/tests,
native/runtime/API/VM, packet codec, gameDBSQL, migration, activation/deployment.
The explicit approved duplicate cleanup remains tool-policy blocked with zero
files deleted; no alternate deletion mechanism or large resource copies.


Round370 connects this private commit/prebuilt S31 to the actual constructed
mixed C67 supplier and SAME common selected-skill source. The LAST Application
wrapper captures one complete original response/write/input hold, with ordered
commit/frame matching and exact private Written/current publication. See
tw-deity-selection-publication-source-20261014.md / source/11. Opt-in local
publication does not establish default CLI/C56 action/native adoption/rights.
