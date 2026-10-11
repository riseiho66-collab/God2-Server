# Native First, Documented Custom Fallback

Effective owner directive: 2026-09-20. This supersedes the requirement that every
missing native rule must remain blocked indefinitely. It does not change the
meaning of native evidence or certify existing placeholders.

## Decision Rule

Latest owner clarification (2026-09-20): prioritize original evidence, packet
protocols and build-matched client behavior before further custom gameplay.
Keep existing CUSTOM implementations labeled and preserve their isolation;
do not promote them merely because their synthetic tests pass. Historical web
references support cross-checking, not native packet or formula certification.
Custom fallback remains secondary to this evidence-first execution order.

1. Use verified native behavior/data for the applicable client build.
2. For a missing item, inspect its source, consumer and existing evidence first.
   Record the concrete gap; a failed search is not proof of global absence.
3. If the native rule is unavailable, design a coherent custom implementation.
   The owner has authorized this fallback; repeated approval is not required.
4. Document, implement, test and integrate the custom rule without relabeling it
   as recovered. Gameplay completion and native fidelity are separate measures.

Protocol acceptance is still determined by the actual client, not by a custom
opcode guessed to fit it. Synthetic tests do not replace own-server live checks.

## Traceable Custom Designs

The machine-readable index is [custom-designs.json](custom-designs.json).
Use a stable `CUSTOM-NNNN` ID in code/Lua comments and generated data provenance.
Search with `rg "CUSTOM-" src scripts docs`.

Each entry records its authority, implementation paths, missing original
evidence, rules/values, rationale, activation scope, tests and replacement plan.
Use `NATIVE_VERIFIED`, `CUSTOM_DESIGNED`, `CUSTOM_TEST_NOT_NATIVE`, or
`UNVERIFIED_PLACEHOLDER` at the field/rule level as appropriate. These labels
describe origin, not whether a test passed. A native ID/name does not make a
custom monster stat, skill formula or drop rate native.

New persistent custom data must retain its design ID and origin in its storage
contract. Do not bulk relabel existing database records or mutate saved player
state just because the policy changed. Data migrations must preserve values and
support review/rollback. Verified native replacements need version/build checks,
regressions and an explicit migration, not silent overwrite.

The initial index covers identified existing fixture combat and character
defaults; it is not a completed audit of every historical placeholder. Additional
unclassified values must be classified as their systems are integrated.

## Client Identity

Current supplied Taiwan client artifacts (SHA256, checked 2026-09-20):

- `../God2/God2.unpacked.exe`:
  `5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`
- `../God2/God2.exe`:
  `fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1`

File presence/hash does not certify unpacking completeness or live server
compatibility. The simplified-Chinese God2_opt client is a separate build;
its successful login is not Taiwan-client or own-server acceptance.
