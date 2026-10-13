# Actual C28 source rejects a retired common presence lease

Two existing C++ ready predicates now include the actual common presence
registry's pure retained_ready_current(lease) check inside their existing local
lambdas. Those lambdas already run before and after ready_lease/saved_position
observers. The change preserves all private input, owner, phase, generation,
position, custody, definition, source identity and existing reply checks.
No gameplay rule or custom design is added.

The concrete defect crosses a real virtual observer boundary.
SharedWorldPresence::saved_position first calls ready(lease), which calls the
virtual character list observer, then calls virtual load_position. That final
observer can release or replace the exact registered lease and return the same
position. The old C28 lambdas checked Session and other local state, but not
the actual active lease registry, so they could still return true. Source
selection/current/ready_current could accept the retired source, and actual
SharedTaiwanOwnedItemRequestSource::dispatch could enter Action.handle or
accept its durable prefix with a stale presence result.

The existing pure registry predicate checks game ownership, active state and
the complete stored Lease equality; it performs no SQL or virtual observation.
Putting it inside both existing lambdas repeats that exact check before and
after observers. Same owner/session/position with a replacement generation
does not preserve the old lease. Existing select/current/ready cuts and the
actual mandatory Action.handle remain in their original order. Postmutation
checks still compare readiness and the native reply decision, without rereading
the intentionally consumed old custody population. Refusal uses existing
invalidation/error behavior; it never retries or rolls back a durable prefix.

The two literal replacements exactly invert both complete current files to
the retained originals and Git63edc90. Independent review confirms the real
dispatch and observer supplier path. Source/13 pins36 current C++ inputs;
the previous29 source/12 pins remain byte-exact. No new C++/Python files.

The skill-book investigation exposed a separate concrete missing supplier:
NativeItemDefinitionObservation and observe_native_definition qualify only
historical TWP/WPN/EQU/TEQ material. The existing definitions-required C28
selection cannot supply SKB learning metadata from those catalogs. Historical
book identity bindings and raw shared book sources do not establish learning,
subject ownership, item consumption, the actual WORLD35 event or a joint
learning/item/replay transaction. Those sources/rules still need connection.
No skill, flag3 or item quantity is synthesized by this fix.

Round371 scope clarification:4A92D0 requires a positive learned count but has
no upper learned-count bound in its inspected body. Its definition flag/rowbit0
checks remain a separate selector with no qualified caller, not a universal
C56 gate. Original WORLD35 receive-only evidence/frontier24 stay unchanged.
Common453/TW Traditional names, owner poison current maximumHP/10 and CNcustom
126/150 requirements remain intact with their unresolved integrations.

This improves one actual conditional C28 source branch. No new native opcode,
formula, phase association, owner chain or complete route is added. TW156 C2S
candidates/252 supported S2C; parser75=50partial+11control+14unconnected;
TW unhosted3chains/40bindings/36unique. CN156/280phase/253supported and
35chains/93bindings/71unique unchanged. Receive-format-only17/unclassified109.
Whole denominator/percentage unknown. Goal active. PHASE1: no build/tests/
runtime/native/API/VM/codec/gameDBSQL/migrate/activate/deploy. Accounts/saves,
native resources/fonts/conversion, frozen features and common tables unchanged.


Round373 separately qualifies native staged81/83 conditional producer layout
and default-off raw ingress through actual Session/Others. This does not supply
the missing SKB C28 definition/learning authority or book-consumption transaction.
See tw-preborn-input-source-20261014.md and source/14; WORD namespace/issuer,
issued-window phase/stage/apply/rights/persistence/replies still OPEN.
