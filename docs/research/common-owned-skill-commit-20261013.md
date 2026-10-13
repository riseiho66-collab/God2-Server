# Common owner skill action and saved authority — round361

The owner requires 瞬影三煞斬 (kind0/id126, CUSTOM-0058) and 牛轉仙界踏
(kind0/id150, CUSTOM-0059) to use one gameplay/learned-rights source for Taiwan
and mainland clients. Traditional Taiwan names remain primary. This round
connects the actual saved observation to existing action persistence; regional
native actor/list/wire/effect qualification remains separate.

## Actual source connections

`Application.cpp` already enables these skills from the selected owned deity
inside its isolated diagnostic battle. That hosting limitation is preserved.
Its existing common skill rules, MP costs, target limits, encoder bodies and
trial overrides are unchanged. The original CN453 catalog still has no native
126/150 rows and is neither extended nor relabeled.

After complete authenticated C35 key/sequence/target parsing and trusted policy
selection, `RecoveredBattleService` loads a fresh privately minted
`SelectedDeitySkillReadset` for the exact account, character and requested key.
It retains selection key/revision, deity revision, raw declaration/status,
complete saved skill sequence, selected skill bytes and provenance through
staged rule evaluation, encoding and any existing retaliation. Missing learned
state refuses the action. Catalog presence, metadata or a client request does
not grant a skill. Session identity/state/closing and battle generation remain
separate checks, including before and after the persistence callback.

The same actual App persistence supplier forwards the observation to all four
existing storage paths:

| Actual path | Source consumption |
| --- | --- |
| Active battle checkpoint | `commit_checkpoint`, before writes and before COMMIT |
| Terminal battle checkpoint | `settle_checkpoint`, including canonical replay |
| Resources without checkpoint | `commit_owned_skill_resources` |
| Settlement without checkpoint | `settle_owned_skill_battle`, including replay |

The repository requires the actual companion repository to use the same SQLite
connection. A private friend-only validator borrows that writer's
`BEGIN IMMEDIATE` transaction. It performs the existing full `main`-qualified
saved read, private repository identity validation, TEMP-shadow rejection and
complete selected-row equality without opening, closing or rolling back the
borrowed transaction. Each read cut checks reentry, transaction state and
unchanged total-change count. Failed validation before the writer's COMMIT
throws and its existing transaction destructor rolls back staged writes.

Owned settlement structured requests use version4 and retain the complete
selected saved authority. This binds a retry to the same observation, rather
than accepting a different skill/selection with numerically identical results.
Ordinary requests retain their previous versions and serialization. Existing
saved requests are not rewritten or migrated.

## Lifetime and preserved diagnostic scope

Opted action operations reject nested service mutations and retain a poisoned
state even if a callback catches the nested error. Removal is deferred until
operation RAII cleanup, after action references cease to be used. The final
Session fence refuses stale in-memory publication after a callback.

The pre-existing callback contract still requires synchronous game-executor
operation with no reentry, send or event pumping. A final fence cannot roll
back a COMMIT that already succeeded if a callback violates that contract.
Durable-prefix recovery remains the existing checkpoint/settlement recovery
scope; this change does not claim distributed atomic publication or completed
reconnect handling.

Existing diagnostic owner casts configured without saved battle resources
retain an explicit `nonpersistent_owned_skills` opt-in. It requires the
isolated single-action policy and no persistence callbacks. It still checks a
fresh saved learned observation before publication, but performs no durable
consumption. Other opted bindings require both ordinary and typed persistence
callbacks. Trial/manual/revival and ordinary defaults remain unchanged.

CUSTOM-0139 records this source ownership policy. It introduces no new balance
formula, skill grant, schema, opcode, timer or poisoned-status behavior.

## Bounded native mainland evidence

Pinned mainland image SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`:
complete `562510..5625A8` is 152 code bytes and46 aligned/reachable instruction
sites with one `RET14h`. It maps two modifier bytes through80 bytes of tables
and forwards to `564A30`. It does not itself read queued `actor+28A`, its index
at `+239`, or mutate HP. The first mapped local retains high24 bits from the
original Q DWORD (`PUSH ECX`); on the selected03h/17h route the parent's
`MOVZX` gives the other forwarded modifier zero high24 bits. Child semantics,
HP arithmetic/width/death and damage generation remain OPEN. This is new
bounded evidence, not a newly credited native method or completed gameplay
route. Native package:19 members,67,662 bytes, seal SHA256
`6347e4dfa8da5523bf4926a53d2b88773cc708bb9cb634188895d93acd16a824`.

## Qualification and remaining work

Source connects4 actual persistence branches for both existing owner skills;
new complete bidirectional routes, native opcodes and recovered formulas:0.
TW C2S156/S2C252; world74 =50 partial +11 control +13 unconnected.
CN C2S156, phase entries280, supported S2C lengths253. These denominators and
counts are unchanged. Whole-game route denominator/completion remains unknown.

Real CN Application hosting, exact caster/list/87 publication and qualified
custom resources/direction/shadows/four phases are still required. Wide64 native
HP presentation and every original skill formula also remain open. The owner's
poison maximum-HP/10 rule still needs genuine status/turn/checkpoint integration.

PHASE1 static source review/accounting only: no compiler, build, tests, game
runtime, native execution, product parser/codec/VM, database SQL, migration,
activation or deployment. Source acceptance and eventual real-client gameplay
acceptance are distinct. The complete active goal remains active.
