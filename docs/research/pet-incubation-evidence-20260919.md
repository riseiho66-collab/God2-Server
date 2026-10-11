# Egg and juvenile source evidence

`recover_pet_incubation.py` adds a pinned, reproducible inventory of all 27 EGG
and 28 SPP rows in the current gamedata.csvZ. Original record bytes, decoded
offsets, row hashes, ItemType classification and opaque fields are retained.
This is source-text recovery, not an implemented pet lifecycle or formula.

Raw SHA-256: 70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731.
Decoded SHA-256: 75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815.
Different or malformed builds fail before extraction rather than inheriting
current labels or positional interpretations.

## Concrete findings

- EGG 9324 text says one hour of care; 9325 says 20 hours until hatching.
  Neither establishes online/offline timing, pause/reset, cost or transaction.
- SPP columns 10/11/12 contain explicit compatibility/health/cleanliness cap
  descriptions. For 9403 these are 70/80/80; 9408 is 90/100/100.
- SPP 9420/9427/9428/9433 explicitly describe immediate evolution. The first
  three have no cap descriptions; 9433 still has 100/100/100 descriptions.
  Immediate evolution must not be generalized to absent or zero care values.
- Ten juvenile descriptions say unsuitable for breeding; exact text remains
  distinct from an enforced native condition or authoritative quest turn-in.
- There is an SPP 9426, but no EGG 9326. No arithmetic hatch-result relation
  is generated. Tooltips alone do not prove a complete outcome distribution.

## Legacy comparison

Historical context only: the owner subsequently retired both corpora. Do not
consult them again. This extractor and both incubation tests require only the
current original client and current captured native image, not either old root.

Both retained corpora were consulted before extraction. XJZ's
`server_implementation/db-evidence-schema-v0.sql` near 594944-595030 creates
incubation/hatchling configuration and joins hatchling.item_id=egg.item_id+100.
Its `evidence-server-ready-v0.md` reports 27 mappings. This is not imported as
an original runtime rule merely because item keys align. Classic's
`tools/God2.GameplayContentRecovery/Phase3SemanticRecovery.cs` and
`src/God2.ClassicServer.Persistence/MariaDbPromotedGameplayContentRuntime.cs`
retain disabled/unqualified hatch probability checks; disabled zero is not
evidence of an original zero probability.

## Verification and limits

`python -B -m unittest tests.research.test_recover_pet_incubation -v`:
6/6 passed in 1.108 seconds. Tests compare every retained raw record against
the actual decoded offsets, preserve absent values, cover immediate/cap
differences, reject changed sources and verify deterministic output.

Generated `artifacts/world-atlas/pet-incubation.json`, SHA-256
f9e484817a4a465ff56cbd06105ca6b7f2d2bd0677dc4fd09d0b857415d34564.
All 55 rows are runtime-ineligible. Growth formula, success probability,
outcome distribution, timer rule and request/result protocol stay explicitly
null. No client source, C++/Lua gameplay state, database or live process changed.

## Original guard follow-up

`test_current_pet_incubation_guard.py`: 5/5 passed in 1.775 seconds. The pinned
native image retains pmpetegg.cpp assertion strings and executes D6C80 -> D6C40
-> 59A60. The guard accepts low-byte slots 0..29 or 45 and low-word item IDs
9301..9500 only when a catalog pointer exists. All 55 original source identities
were checked at slots 0, 29 and 45. Absent keys and outside-range IDs reach
distinct original assertion sites; execution stops before the assertion handler.

The index is explicitly staged with pointers to exact original row bytes, not
produced by the native gamedata loader. The guard does not dereference those
records. This proves range/argument-width/presence behavior, NOT full loader
semantics, ownership, incubation, evolution, rates, care arithmetic or EXP.
No game code bytes are patched, no original callee result is substituted, and
snapshots confirm no non-stack state mutation. Wide inputs alias native byte/
word arguments; this is not permission for wide server IDs to alias similarly.
