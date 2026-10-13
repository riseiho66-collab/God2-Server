# Shared TW/CN skill source composition (2026-10-13)

Round359 adds one owning shared skill definition beside retained native records.
The actual Application Lua provider and CN private preborn skill selection now
carry that same definition. This is source integration of definition metadata;
the full cast/formula/debit/status/effect routes are still open. Phase1 permits
static source, raw-byte inspection and accounting only. No build, tests, native
execution, VM, product parser/codec, game database SQL, import, migration,
activation or deployment was performed. Goal remains active.

Previous358 main8520e6330e32631df630fecc46204f040a6f911a was pushed with exact-head
notification38352661594 success. Its root603 members40,426,056B and eight upstream
packages, together1197 members72,070,834B, were verified individually before this
round. Original accounts/saves, frozen chat, custom TW assets, fonts, conversion,
64-bit common domain, coin99999999999, stack99 and all four binary WebSocket
entrypoints retain their existing scope. Source accounting is not acceptance.

## Owner scope and source choice

The owner requires all skills in ONE common gameplay/catalog core, complete
settings preferred, Taiwan Traditional text primary, actual client formulas
primary and player guides secondary. Unequal regional raw rows are adapter
bindings; they do not justify independent gameplay cores. Zero alone does not
mean missing. Root's routine choice when both profiles are complete but conflict
is the TW complete shared base, with original CN values retained. This chosen
composition is CUSTOM-0138 and is not a recovered native formula or permission.

The owner also explicitly requires CUSTOM-0058 瞬影三煞斬 and CUSTOM-0059
牛轉仙界踏 to apply to CN. These two are scoped exceptions to prior CN native-only
policy. Their existing common formulas, definitions and learned rights must be
reused, then connected to qualified CN wire/effects. No new dedicated custom
opcode is inferred. Existing TW uses native S83/type3 logical15B, 86 HP/MP17B and
88 cycle121B. Instant shadowless clones are explicitly permitted for0058; real
caster shadow/direction and0059 four presentation phases remain protected.
Four phases do not mean four damage hits. This round does not activate CN casts.

## Actual BIN identities and differences

Each plain1.03 source is112660 bytes, four kind banks with110-byte rows at
8+kind*0x6E04+(id-1)*110. OriginalTW7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51
declares121/129/87/111=448. InstalledTW3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7
declares126/129/87/111=453. OriginalCN857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004
declares125/130/87/111=453. All448 originalTW rows are unchanged in installedTW.
Its five additions are reserve0/122..125 and custom0/126. CN source is independently
pinned current input, separate from retired corpora.

OriginalTW/CN share448 keys;445 have equal identity plus physical3E..6D tail.
Chinese encodings/text prevent full110-byte equality. Three parameter-different
rows have the SAME IDs:0/95 WORD42 TW120/CN50;1/83 empty candidate labels with
TW zeros versus populated CN fields;1/129 WORD42 TW120/CN100 and WORD4A55/35.
InstalledTW/CN share452 keys and have454-key union. TW-only0/126 is custom;
CN-only1/130 is native 雷神. The four CN0/122..125 rows are populated native
skills versus confirmed installed TW reserves. None of these counts certifies
453 original native TW skills, 453 recovered formulas or a complete cast route.

Selection uses complete CN rows for confirmed reserve0/122..125 and pinned
empty1/83; complete TW base for both-complete conflicts0/95 and1/129. Four
borrowed reserves use CN names converted to Traditional rather than the TW
placeholder 預留技能, preserving distinct name versus short name. Other pinned
nonempty TW name/short literals take precedence. Source projections2..1F and
20..3D are bounded retained views, exclude WORD3E and do not certify native UI
field widths. Actual MP display also performs a separate SKB text lookup.

## Common definition and actual consumers

NativeSkillSource moves into its own header; NativeSkillRecord's original fields,
equality and legacy lookup behavior remain unchanged. SharedSkillLookup carries
optional requested_native separately from SharedSkillDefinition. The definition
owns canonical(kind<<8)|id, source profiles, full110 raw bytes, source ordinal/
offset/digest, source-text projections and an optional chosen parameter profile.
The stable key does not assert identical native effects or grant learned rights.

907 independently pinned rows comprise448 originalTW,453 originalCN, four actual
TW reserves, installed custom126 and separately retained custom150 candidate.
The last candidate sourcef159b61f0aeacc46e71519cd6e98910381eda22336ad07487b2cf7213ec6297d
has477 rows and is not claimed installed or native CN. Every pin has exact110
expected bytes, digest, key, source hash, ordinal, offset and row count; original
rows also require their corresponding native image hash. Unknown snapshots retain
metadata without a qualified chosen profile. Selected-row qualification does not
attest a loaded whole file, observed native bank or actual entitlement.

Independent review found and corrected a public value-contract flaw: a writable
digest flag could previously qualify changed raw bytes. Qualification now resets
caller claims and compares ALL110 bytes against retained expected data; the flag
is informational. Positional TW/CN inputs must match their region enum before
policy selection. All907 arrays/99,770B were independently compared with their
sealed sources, including retained custom150. No product implementation ran.

NativeSkillCatalog.lookup_shared_definition_main uses two explicit main namespace
joined reads in one read scope on the existing connection. It owns BEGIN/COMMIT
only when autocommit was active, otherwise borrows the caller's transaction.
Missing CN does not discard a valid TW snapshot; missing TW never fabricates a
requested native row. Existing source validation and row digest reader remain.
This metadata view is not a new schema/import or private native Current issuer.

Application passes an optional common provider as the LAST LuaEngine argument;
existing callers and native_skill_catalog remain intact. Initial and rebuilt VM
own the provider. common_skill_definition(kind,id) exposes owning profiles,
Traditional projections and chosen raw profile; gameplay_authority is false.
Lua cannot treat the common profile as learned permission or a new MP debit.

CN.lookup_shared first retains its private actual native453 row under existing
Operation/observed Current checks. Shared CN fullraw/source/ordinal/offset/hash
must equal that retained row; requested_native becomes the original CN row,
never the chosen TW parameters. Extra observations fail terminally. Original CN
gate still rejects custom126/150 absent from original453; future owner-custom
adapter/profile must be distinct and may not forge original857 provenance.

CnPrebornSkillChoiceSource resolves each already-qualified requested row to the
same owning definition, retaining order/duplicates and the old learned/book/
subject/primary fences. Existing SharedPrebornWindowSource.apply and delivery
qualification carry the owning facts after commit; no obsolete Current is reused
and no borrowed record survives. Two actual source branches are counted: Main
Lua definition provider and CN actual selection facts, not two completed routes.

## CN action3 consumer and formula limits

Pinned current CN image582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8
supports three complete selected bodies:54C510..54CBB3 (1699B/441sites),556D40
(1713B/574sites) and55E2F0 (70B/29sites), totaling3482B/1044sites. Parent union239B/
67sites, overlapping83 caller bytes retained separately;175B tables plus padding
excluded from code. Earlier size metadata described partial prefixes, not whole
bodies. These were known methods, so new native-method/opcode/route credit is0.
In-place PE bytes are pinned; no independent mapped-memory pair is claimed.

S83 uses Main+A97180 logical packet with body atlogical+1. Type3 skill key is
WORD logical11 (ID then kind), source selector2, masks5/7 and WORD logical9
forwarded unsigned to formal5's low16. Marker bytes13/14 are retained. Catalog
lookup includes the four-byte bank header at Main+9D223C+4+(id-1)*110+kind*6E04.
55E2F0 chooses first set bit side0 then1, positions0..13, zero sentinel side2/14.

5634E0 remains only a664B/199site prefix; actual type3/type17 signed HP/math tail
near563A3E is OPEN. MOVSX SI in this prefix belongs to actor-state5 notice and
does not certify type3 negative HP semantics. Blindly copying TW custom replies
to CN is not justified. Native MP checks in both clients compare current role MP
against rawWORD42 and B67; those checks do not deduct MP. Known CN MP bodies
4D3B60/4D3BB0 are existing qualification, not new recovery credit. Client received
HP-delta clamps are consumers, not generators for all skill damage or 64-bit rules.

## Poison and remaining work

Owner poison rule is target CURRENT MAXIMUM HP divided by10, not remaining HP.
Common BattleActor already has64-bit HP/maxHP; current battle/checkpoint input
has no qualified poison status/turn executor. Integrate native skill bindings
into one effect descriptor, actual turn boundary, staged maxHP/10 mutation and
checkpoint-before-publish pipeline. Rounding, immunity, stack, tick timing,
expiration and lethal policy require explicit qualification. No arbitrary world
timer, unused helper or replacement of all ordinary direct attacks is installed.

Raw equality alone does not close client formulas. Continue actual consumers for
MP debit, target selection, damage/defense/hit/critical/status and the CN custom
effect bridge. Formula use remains separate from row provenance and UI text.
Community guides are secondary; no unsupported indexed claim became a formula.

## Accounting and custody

Nine existing C++ files and three new headers/source files implement this change;
whole existing-file inverse chains, additive corrections, failed prewrites and
independent reviews are retained. The prior292-source baseline plus17 extra
dependencies remain covered. AGENTS preserves its original
binary prefix and the custom index preserves135 old entries, adding0138 only.
Plan appends preserve old bytes; report registration adds exactly two LF lines.
Old ledger fields and immutable frontier-v23 are retained; successful helper
copies are LF, immutable, separately hashed and are never rerun.

New opcode values, independent formats, native-method credits, recovered skill
formulas, parsers, handlers, phase bindings and complete bidirectional routes are0.
Global counters stay TW156C2S/252S2C, world74=50partial11control13unconnected;
CN156C2S/280phase/253length, distinct inventories. Whole-game/TW denominator and
completion percentages remain null. Parser67.6% does not represent playability.
Unique static report20261013-tw-cn-shared-skill-source-359 precedes root sealing
and exact-head private-main publication/notification. Goal stays active.
