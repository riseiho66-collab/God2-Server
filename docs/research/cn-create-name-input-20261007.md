# CN ordinary character creation: name input and resource owner

PHASE1 static PE/resource/source recovery only. Levels are unchanged. No build,
tests, native/server execution, database access or deployment. The preceding
goal turn only acknowledged the owner's level decision and made no source
progress; this round resumes the available name-producer recovery action.

CN image SHA256 is
582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.
Delivery: `cn-create-name-input-01`; file-only extraction tool:
`tools/reconstruction/cn_create_name_input.py`. Prior ordinary17 record/caller
and appearance recovery remains retained evidence, not new routes here.

## Actual submission gate and return-value corrections

00440140 case11/bit1 calls0043D8B0, ignores its result, rejects an empty first
name byte, then uses0043D640's EAX. Only a nonzero result, with the existing
state guard, selects18 and feeds the retained43D280/47E900 ordinary17 path.
0043D8B0 first invokes00433B00 to copy at most14 encoded bytes plusNUL into
UI+15578; it then queries00458C70's AL. That latter result is edit commit
readiness and is not the ordinary event's acceptance gate. Some decompiled
functions incorrectly use `void`: primary instructions preserve the actual
AL/EAX assignments and caller tests. No UTF-8 character count or DBCS boundary
repair may replace the original byte copy or alter name identity.

0043D640 uses several distinct filters:

- A1 40 scan over starts0..12 in the retained14-byte buffer ->SystemMessage203.
  This scan does not stop at an earlierNUL; the copied name's trailing UI bytes
  can influence this local gate. It does not establish wire padding rules.
- 16 pointers at00888210 passed to CRT substring0074FF90 ->SystemMessage205.
  All four ASCII gm capitalizations and12 explicitly encoded fullwidth/mixed
  patterns are retained as raw bytes. This is not a generic Unicode casefold.
- A legacy three-position window after the first G/g orA2EF/A2D5 at starts0..11
  also rejects205. Its actual comparisons include4F (uppercase O),6D (m) and
  A2F5/A2DB. Preserve the unusual4F comparison and postNUL behavior; do not
  silently fix these to a presumed GM algorithm or CP936 Unicode equivalents.
  The two-byte branch can read through buffer offset16, beyond the14-byte
  entered-name maximum. A name-only string cannot reproduce those trailing
  UI buffer reads; the full ordinary17 raw payload remains preserved.
- 004462F0 returns AL1 on dynamic match, AL0 at end. The caller tests AL and
  rejects206 on1. This is confirmed even though its decompiler says `void`.

The dynamic filter consumes a24-byte string vector at009EDDA0/4/8; strings use
inline storage at capacity<=15 and a pointer above that threshold. Its actual
004463E3 indirect call is declared as SHLWAPI StrStrA by the bounded primary
PE import reader. No loaded IAT binding, external DLL implementation, locale
or runtime vector is observed. Do not approximate that external function with
a new byte-search/Unicode matcher and call it native acceptance.

## Actual resource loading differs from the declared word count

00445040 calls00446550 at00445B12 and ignores its return. The loader opens
`.\Data2\Patch\Comm\forbidwords.csv` through00423350/0045B270, which first
tries the Z resource, signature0516 and0045A060 decoder, then plain fallback.
The current packed resource is89602 bytes, SHA256
6e334654fa7d5b461da3ee08ddb85efc435dbe2415c0cb995bd0907123baefc0;
declared/decoded plain length129940, SHA256
c08a2f54f309b2dc06411f97b7a83449279ad7f98e3ac08052fd571df38ed46c.
The existing upstream file-only decoder is retained with its hash, reused
without invoking its main or any native code.

004232D0(1) clamps the parser's column budget to5, not1. 00423390 reads the
first header's count2 and skips count-2=0 additional lines. 00423480 returns
EAX1 after each successful fgets, independent of parsed column count, and0
at EOF. 00446550 loops on that return and copies every nonempty column0 via
004231B0; it never treats the later `forbidwordsNum,12921` row as a loop bound.
Thus a single successful load of this exact resource appends **12924** strings:
`RowDesc`, the raw CP936 text label, `forbidwordsNum`, and12921 body entries.
This is the recovered loader's resource-to-vector behavior;12921 alone would
lose three actual entries. The loader itself does not clear or deduplicate the
global vector. Repeated loading and other writers still require separate owner
tracing; on-disk zero DWORDs do not prove a runtime-empty or disabled filter.

The extracted row ledger retains raw bytes, source line indices, order,
duplicates and metadata entries. No permission, locale, profanity policy,
server-side uniqueness/collation, database write or guessed02 result is added.
Native metadata spans remain source navigation evidence, not a complete CFG
or producer-variant census. Ordinary17 UI gate evidence is not proof that
special1B or every possible17 producer obeys the same gate.

## Next source integration

Actual common create/delete operation owners, uniqueness/collation rules,
transaction/defaults, complete02/1E/18/03 suppliers and configured Application
hosting remain open. Preserve CnCharacterCreate's optional UI accessor and all
raw payload bytes. The new input evidence changes the next rule investigation;
it does not authorize applying a client filter as a shared gameplay rule.
No new phase/opcode bindings, owner chains or complete bidirectional routes
are counted. Whole-game denominator and completion percentage remain null.
