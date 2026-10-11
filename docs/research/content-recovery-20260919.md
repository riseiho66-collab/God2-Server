# Current Content Recovery Integration

## 2026-09-20 policy update

The owner now permits documented custom designs where native rules/data are
unavailable. Follow ../IMPLEMENTATION_PROVENANCE.md and ../custom-designs.json.
Original-only prohibitions below are historical where they conflict with this
update. Native evidence standards and retirement of legacy corpora still apply.
Existing unknown fields are not retroactively certified or filled by this note.

## Superseding source policy: legacy retired

Owner directive, 2026-09-19: the previously supplied XJZ and Classic server
corpora have no reference value and must no longer be consulted or imported.
This supersedes all earlier instructions in this and other reports to inspect
both legacy trees. Earlier sections below are historical work records, not an
active plan to reuse those sources. Current original-client bytes, qualified
current native behavior and own-server tests are the remaining evidence basis.
Conclusions supported only by retired sources are withdrawn, not migrated.

The owner also authorized deletion. Five exact archive/extraction paths were
checked for resolution and reparse points. The removal command was rejected by
the execution tool's policy before launch: NONE was deleted. Details are in
`legacy-data-retirement-20260919.md`. Do not report deletion as completed or
re-ingest these paths. No alternate deletion mechanism is used to bypass policy.

## Owner-wide original-rule requirement

The owner additionally requires finding and verifying the original basis as
the completion condition for every item. A missing field is an open recovery
task, not permission to invent a substitute or close the task as restored.
Continue source/consumer/protocol tracing and retain explicit unresolved scope.
This requirement does not turn a hypothesis into evidence or establish that
every historical server-side constant is necessarily stored in this client.

The latest owner requirement applies to ALL server data, formulas, attributes,
and gameplay rules, not only monsters. Role, combat-pet and immortal growth,
main/side quests, juveniles and incubation are explicitly included. No guessed
coefficients, substitute formulas or invented rewards may fill missing evidence.

Qualification requires the current source/build, exact record or code location,
field meaning, inputs, units, integer widths, rounding/overflow, state conditions,
and reproducible checks as applicable. Raw bytes, tooltips, native consumers and
live end-to-end acceptance are separate evidence levels. A client displaying a
server-supplied result does not establish the server's calculation. Retired
legacy implementations are no longer accepted even as research leads.

Unknown means unknown, never zero, a common MMORPG default, or a disabled legacy
rate relabeled as original. Unqualified mutations stay disabled; fixtures remain
explicitly separate. Existing Character HP=100/MP=50 and Monster HP=100 defaults
are placeholder skeleton values, NOT recovered original attributes. They have
not been certified by the recovered character profile or native scene tests.
Retained historical world-entry scalars are still unverified lab candidates.

Black-box synthetic peers and native-code emulation may test concrete boundaries,
but do not certify real-client task acceptance, combat or original game rules.
Implementation remains C++20 core/network/storage, Lua gameplay and SQLite.

The owner's requested NPC, monster, quest, combat/skill, item and immortal/pet
work was split into six bounded implementation lanes. All six completed their
first extraction slice and were closed. No imported row is a claim of live
gameplay, a guessed server formula or an enabled entity spawn.

| Output under artifacts/world-atlas | Source-backed extraction | Still required |
| --- | --- | --- |
| npcs.json |319 current template rows;2 archived placement definitions with matching retained message hashes | Current map/resource binding, consumer validation and visibility |
| monsters.json |215 field and215 battle definitions; raw legacy spawn candidates retained separately | Qualified spawn locations/rules and authoritative stats |
| quests.json |418 mission definitions,2014 objective-text rows,169 requirement rows,85 daily rows | Cross-table namespace proof and executable state/reward rules |
| combat-skills.json |381 skill-book definitions and4 menu rows | Runtime skill mapping, casting and actual combat formulas |
| items.json |16127 definitions across45 populated sections | Inventory/equipment packets and server effect/stack rules |
| companions.json |34 GOD,2070 COM,1165 NCP,509 skill-table rows,4 rank rows and9 message-text records | Ownership, summon/growth/skill state and packets |

These are per-source counts, not additive unique-world totals. The item catalog
overlaps skill-book and companion definitions.147 PET rows remain separately
classified; they are not automatically combat pets. Monster field and battle
IDs are not silently equated. Message/description text is never executed as a
formula or quest rule. Raw source bytes, hashes and source locations are retained.

The six tools are `tools/strike_lab/recover_{npcs,monsters,quests,combat_skills,
items,companions}.py`. Main ran their combined44 focused tests successfully in
10.944s, including source-byte comparisons, reproducible output and explicit
unresolved-state checks. NPC tests now also reproduce the real saved artifact
and run independently from tests/research, not only from repository-root imports.

## Next Concrete NPC Connection

Classic migration103 explicitly maps archived map170015007 to client area15,
map7. The current scene index resolves that numeric selector to
`Data2/map/North004/citywei01/citywei01.mdtZ`, via North004.can. This is a
cross-build selector candidate, **not a verified identity/coordinate match**.
The two retained coordinates65,61 and240,54 must not be placed on initial
indoor area2/scene15, which is an unrelated31x31 navigation grid.

The Classic NPC serializer uses S2C72 with21 logical bytes. In the current
pinned image, size-table entry1324+4*72 points to127C (`mov eax,21; ret`), and
dispatcher entry6B5D4+4*72 points to6A68B. That consumer checks WORD selectors
against a catalog count at resource+121E8 and uses94-byte catalog records.
Its resource branches and state effects must be validated before reusing a
legacy spawn layout. Other old protocol notes that say NPC formats were not yet
recovered are earlier-stage evidence, not authority over these concrete hooks.

No source client files or archived databases were modified. No guessed NPC,
monster placement, skill relationship, reward or battle coefficient was enabled.
## Owner-required monster fidelity

The owner's 2026-09-19 requirement explicitly includes level, HP, MP, all four
base attributes, physical/magical attack, physical/magical defense, all five
element values, monster skills, drop items and exact drop rates. None may be
filled from a visual record, transformation-card effect, player/pet definition,
legacy server-design formula or a zero default merely to make gameplay run.

Qualification is per field and per current monster identity/variant, not per
imported row or matching name. Preserve source bytes/hash and the relevant
consumer. Unknown stays unknown; a confirmed field does not certify the rest.
Skill ownership/slots, trigger/target conditions and combat effects must be
distinguished from merely recovering a skill-command encoding.

For drops, establish item identity, quantity, eligibility, rate unit or weight
denominator, number of rolls, no-drop outcome, and exclusive versus separate
selection. Quest/party/map/level/event modifiers must be retained when present.
A finite observed drop ratio is not an exact original probability. Collection
objectives, bag rewards and disabled default rates are not monster-drop rules.

Current source audits and concrete follow-ups are documented in
`monster-stats-skills-audit-20260919.md` and `monster-drops-audit-20260919.md`.
These are additional requirements and evidence leads, not a claim of completion.

The machine-readable monster extractor now enumerates the 19 requested fields
separately in `unknown_fields`, retaining the older generic keys for compatibility.
`artifacts/world-atlas/monsters.json` was regenerated: all 215 field and 215
battle definition rows retain exact source bytes and remain runtime-ineligible.
No unknown value is represented as a default zero. This artifact regeneration
supersedes the earlier artifact/script hashes recorded in the source audit;
those hashes identify the versions audited at that time.

`test_recover_monsters.py` now has 10 passing tests, including every actual
definition row's explicit unknown-field contract and a retained legacy SELFTEST
drop fixture (observed 0.12, disabled default 0, authoritative NULL) that must
never be promoted. Main reran the suite: 10/10 in 0.617 seconds, and separately
read back the regenerated artifact to check all 430 rows. These tests verify
provenance handling, not recovery of the original missing numeric values.
