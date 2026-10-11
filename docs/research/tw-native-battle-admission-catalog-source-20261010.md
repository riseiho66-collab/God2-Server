# TW253: battle admission ownership and common skill catalog observations

Phase1 source integration only. No build, compiler, test, runtime, native,
codec, gameplay database/SQL execution, migration or deployment.

## Concrete source increment

Seven existing C++ files change; no new gameplay handler or packet is invented.
NativeSkillCatalog adds lookup_main_digest_checked and lookup_main_source.
The digest API owns a main-schema row through the existing strict row parser,
then recomputes SHA-256 over its entire110 bytes using the existing Windows
BCrypt dependency. Missing rows, unavailable hashing or mismatched digests
return absent; malformed rows/SQLite errors retain rejection by exception.
Hash destruction precedes the backing buffer and algorithm destruction.
Original lookup and lookup_main retain their prior lookup resolution and
metadata parsing behavior. The source API observes all NativeSkillSource
fields from main.native_data_sources; missing is absent and duplicates or
invalid/null metadata reject. It owns the dataset selector before SQL observers.

The actual normal-entry prefix reader now uses the shared digest API for both
initial definition material and full-row Current reobservation. Its original
historical448 policy and empty/pet-only behavior remain unchanged.
SharedTaiwanIssuedSkillSource uses the same API at all three definition reads:
full model Current, direct87 update and aggregate publication87. Full model
Current compares its owned catalog_source against main source metadata before
and after traversing every present primary/auxiliary, optional secondary and
roster learned/auxiliary definition, including inactive tails and empty models.
SharedTaiwanNativeSkillCommandSource uses it at both dispatch/current reads.
SharedTaiwanOwnedDeitySkillSource uses it at its two saved-skill definition
observation/current reads. Thus these concrete connected source components use
one main-row/digest qualification rather than independently resolved rows.

Existing exact Session/ready lease/position/battle-generation, creation-thread,
reentry poison, private ticket CAS and pending write checks remain.
Before-write and actual completion still reobserve both old and next full
models. C35 after_action still checks the actual next durable receipt without
re-reading a consumed old grant/definition. No new authority comes from a row
hash, client operand, selected saved deity, queue admission or local write.

## Native source recovered

Pinned image149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Twelve bounded code spans494B/133 instruction sites plus16B tables identify
WORLD S82 logical9: table46B7DC→46AE12 writes its two raw DWORDs to the actual
event T+28/T+2C and returns transition4. S5D is a different branch.

Actual Main4655E0 creates the stack descriptor: D+4 is the same T, D+8 is
U=Main+A7F2F6C, and D+10 is R=Main+1539683C. At465836 it calls5112C0 with that
descriptor and the actual B from Main+A7E05EC;511323/326 stores B+14=R,
511317/31A stores B+20=U. The row initializer then derives S=R+90 for arg7.
This binds an actual root/event epoch; a saved deity key cannot replace it.

S82 supplies only two context DWORDs. Other native code copies R0 to T0 and
the initializer copies1004B of event data; zero-filling the rest from a nine-byte
packet would invent state. Retained actual86/5 bytes identify the actor nibbles,
not their mapping to saved deity/common participant identity or turn authority.
Full native GUI/helper afterstate and original server producer policy remain open.

## Limits and next source connection

The issued model remains generic within its existing qualified source shape;
this round does not tighten it to448 or enable the distinct453 profile.
The normal receiving prefix remains explicitly448/7676; current453/3adc remains
a separate resource epoch. Full metadata equality and referenced-row hashes
do not attest the full catalog file, native loaded memory, factory success or
cross-source atomicity. Completely empty issued models observe source metadata,
not nonexistent row hashes. On non-Windows, referenced-row digest qualification
is unavailable and rejects those observations; empty metadata-only models are
not misreported as hashed rows.

The existing Application normal-prefix observer consumes the shared reader.
The registry/command/selected-deity components still require their real issuer,
WorldOwner and selected ordinary Main host. This round does not activate them.
Next is the actual owned S82 admission publisher and ordered participant/86
issuer tied to the same normal receiving source/readset/position/Session epoch,
then learned actor membership, grant, MP/resources, once settlement/full replies.
Do not create another uncalled admission wrapper or infer actor14 from a row.

TW indexed counts stay C2S156, world S2C252 and battle S2C110. Mixed partial
source segments237→238 are bookkeeping, not completed TW routes.
New complete routes/opcode values/global native coverage:0.
Complete TW directional/state/variant denominator and percentage remain unknown.

Evidence: C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-battle-admission-owner-source-253.
All source originals, before/candidate/final epochs, exact diffs and independent
static reviews remain separately retained. Seals attest filesystem bytes only.
