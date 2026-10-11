# Owner-confirmed character growth: current-client integration

## Authority and scope

The owner confirmed the following per-level awards from level1 to level2 onward.
These are OWNER_CONFIRMED_20260927 rules, not recovered original-server formulas.
All classes receive four additional manual allocation points per gained level.

| Catalog ID / class | Constitution | Strength | Intelligence | Speed |
| --- | ---: | ---: | ---: | ---: |
| 1 / Swordsman | 2 | 3 | 0 | 1 |
| 2 / Taoist | 1 | 0 | 3 | 2 |
| 3 / Pharmacist | 2 | 0 | 2 | 2 |
| 4 / Warlock | 1 | 1 | 1 | 3 |

Level1 attributes, HP/MP growth, real XP thresholds and level caps are not inferred.
Lua owns growth arithmetic; C++ owns profile qualification, transport and atomic
SQLite settlement. The existing isolated seed [10,10,10,10], maxHP120/maxMP80
and test thresholds [0,200,600] remain CUSTOM-0013. The persisted snapshot's
CUSTOM-0013 design ID denotes this mixed fixture, not native growth authority.

## Original client contracts

Current Taiwan EXE SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Port-only private client SHA256:
`9ff8b9c99271e2e528270ce6475f231c338a09daf463c300fe39b62f66258c4f`.
Mapped original image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Create handlers4097A0 and40C680 compute pre-wire byte29 as
`2*(control-11)+sex`; senders40C0B0 and40C160 increment byte29 for native17/1B.
Refresh409680/40C580 selects FlowGui actions56..59: TipSword, TipWizard,
TipRuse, TipDoctor. Original art identifies the latter three as Taoist,
Warlock, Pharmacist. Thus wire29 pairs1/2,3/4,5/6,7/8 map to catalog1,2,4,3.
Both sender paths and both sexes were executed:16 pinned cases passed.
`artifacts/research/character-growth-native-20260927/binding.json` retains pins.

Native22 consumer4E6B40 directly dereferences UI+86888, then writes level+26,
remaining points+90 and zero-extended four-stat DWORDs+78/+7C/+80/+84.
Role-panel controls0E/0F/10/11 and16 bind these fields to original labels.
The world-position locator uses a different base preceding that pointer by90h;
subtracting90h in the first live observer was a test bug and was corrected.
Run06's NATIVE_GROWTH_SNAPSHOT_NOT_APPLIED does not prove a client apply failure.

## Runtime fixes and isolation

`diagnostic_character_growth` requires the existing isolated persisted level
snapshot route and defaults off. Owned profile is qualified before battle
reservation. Growth uses the previously saved snapshot and gained-level delta;
no gain means no award. Four-stat uint16 overflow, points exceeding signed
display32767, descending levels and invalid profiles fail before persistence.
The existing settlement request binds full role bytes; exact replay returns
the prior settlement, and a changed projection is rejected.

Actual terminal victory in this Taiwan hidden client emitted context04000000.
It is admitted once only with this growth flag, a released committed diagnostic
and the same session's recorded victory. Byte2 semantics are not inferred.
Existing town diagnostic receipt rules are preserved. This admission does not
grant XP, apply growth again or authorize arbitrary world notices.

Candidate SHA256:
`20d0c30ea40e3559e20250713cc598a8acaac3325e753d110c29976b30f72f34`.
Tools: `run_private_character_growth.py`, `private_character_growth_ui.py`.
All tests use an own loopback server, fresh SQLite copies and a hidden desktop;
no input-desktop switch, screenshots, packet injection or client-memory writes.

## Verification and outstanding work

Runs07,08,09 and run10's first-stage UI qualify all four professions, native22 application, saved
revision2/XP250 and one accepted post-battle receipt. Their native values match
the owner awards independently of DB/client agreement. Run10's complete result
is false because its immediate reconnect observer did not wait for native
snapshot application; it must not be summarized as an entirely passing run.

`private-native-blackbox-character-growth-restore-20260927-03` is the passing
fresh-client restoration receipt. It copies run10's accepted settled state,
disables every diagnostic battle/growth flag and waits for unique native22
stores plus the original UI ownership-pointer relation. The world prefix also
proves area2/scene15/kind2/x18/y12. Native level2, four stats12/10/12/12 and
points4 are retained. All SQLite tables match before/after login; no reseed,
healing, XP or growth award occurs. Live DB, source fixture and both client
identities remain unchanged. Earlier immediate probes are retained as failures,
not counted as passing. No screenshot or memory write was used.

Unit coverage:1020 level/class cases, partition/no-gain replay, overflow and
Lua reload; eight native-profile sex/class mappings and eight atomic SQLite
settlement/retry checks. Focused growth, native22, configuration and account
authentication tests passed. The full CTest attempt finished with failures;
the follow-up repaired and reran36 applicable failed tests successfully. Two
retired-beta raw-asset checks are now explicit opt-in research, not passing
current-client checks. The corrected pre-HUD guarded-return test passed2/2;
the independent original role-progression clamp/guard tests passed14/14.

No production flag or player database was changed for this feature. Formal
production growth activation and a build-matched real XP curve remain open.
Pet/immortal growth is not covered by character growth acceptance.

Saved-evidence verification:
`python -X utf8 -B -m tools.strike_lab.verify_character_growth_acceptance_20260927`.
This re-executes16 native sender cases and checks all four live-growth receipts,
actual role/profile/XP/ledger rows, accepted terminal context and reconnect
native values/location. Output: `character-growth-native-20260927/acceptance.json`.
This historical verifier pins the old growth-only candidate and must not be
used to certify a subsequently rebuilt executable without requalification.

## Native manual allocation, completed isolated acceptance

Pinned sender496300 ->4132E0 queues exactly21 followed by one selector byte.
Original4E8910 controls20/21/22/23 map respectively to selectors2/3/1/4 and
Con/Strength/Intelligence/Speed. The client optimistically increments the
selected DWORD once and decrements its WORD budget once. Four original event
branches and four complete sender executions qualify this one-point rule.
There is no request nonce: repeated same-selector clicks are separate spends.

C++ `OwnedAttributeAllocation.h` loads an existing owned snapshot, Lua
`character_growth.allocate` applies the one-point rule, and the existing atomic
role/resources transaction commits before the authoritative native22 response.
The snapshot's level/progress/maxima/opaque bytes and provenance are preserved;
XP and current/maxHP/MP values are unchanged. No snapshot is seeded or points
granted by an allocation request. Zero budget returns the owned native22;
overflow, invalid selectors and mismatched ownership are rejected. A late
resources-update failure rolls back the role update, verified in SQLite.

Config `world.owned_attribute_allocation.enabled` defaults false. The live
Application path requires authenticated native world entry, completed tail,
owned projection, owned position, no pending map transfer and no owned pending
battle. The original client retains CharacterSelected until first movement;
requiring InWorld alone incorrectly discarded valid pre-movement allocations.
That actual-client failure was repaired without removing the other gates.

Hidden receipt `private-native-blackbox-attribute-allocation-20260927-09`
opened the real primary toolbar via +232DB6/control5, then used the four live
child rectangles of the role sheet +232DDA/controls20..23. No packet injection,
screenshots or process-memory writes were used. Native statistics progress
12/10/12/12 ->13/11/13/13; points4 ->0; saved role revision2 ->6. Each request
was handled once in selector order2/3/1/4. A fifth click at zero points changed
neither client stores nor the save. Only role/resources tables changed;
resources revision4 ->8 while values100/120/50/80 stayed fixed; XP stayed250.

Fresh hidden receipt `private-native-blackbox-attribute-allocation-restore-20260927-01`
restored the allocated native values using a new game process, with battle,
growth and allocation flags disabled. Every SQLite table stayed identical.
Both receipts preserve source fixture, live account DB and both client files.

Accepted server SHA256:
`fee579ab029aba362d7d333daf9bcc6e3a382f76ba9d644cbb7c515652ad6a7c`.
An immutable accepted executable is retained in the research evidence folder;
`verify_attribute_allocation_acceptance_20260927` checks its hash, re-executes
native button/sender traces and audits actual stored rows and live receipts.
The four-button allocation/restore lane is accepted. Production activation is
still false; derived attack/defense/HP/MP growth formulas remain unrecovered.
The [10,10,10,10] seed and250XP remain explicitly isolated CUSTOM-0013 inputs.

Queued21 batches are preflighted before one atomic commit. Only allocations
and native idle ticks may coexist in that route; unrelated mutations are
rejected before any spend. Each selector is evaluated in Lua in order.
Insufficient points or a selected-stat overflow returns the original native22
without committing any partial allocation. Tests verify repeated selectors,
five requests against four points, invalid middle selectors and late rollback
of the complete four-request batch. These are transaction checks; they do not
by themselves prove the current client emitted a multi-request wire frame.

Latest queued-batch-capable candidate SHA256:
`59591afb03b4bb0aadfe5063c636557ccb127a6c925221d954e78358346f50d6`.
Rapid repeated-selector receipt
`private-native-blackbox-attribute-allocation-rapid-20260927-02` accepts
selector order2/2/1/4 with native attributes14/10/13/13 and points0. Each mouse
transition is held40ms so the original frame-sampled input sees actual clicks;
the earlier5ms automation transitions yielded only two actual requests and
are retained as a failed test, not blamed on server packet loss. This accepted
run sent four separate one-request frames. Actual multi-request client-frame
observation remains unproven, separately from the verified batch transaction.
Fresh process receipt
`private-native-blackbox-attribute-allocation-rapid-restore-20260927-01`
restores14/10/13/13, level2 and points0 with allocation/battle/growth disabled;
all SQLite tables and external files remain unchanged. The saved-evidence
verifier qualifies both immutable candidate revisions separately.
