# Original skill identity to book binding

## What is executed

Original image RVA A8E10 through RET 0C at A8F9C, including the original
147AF7 formatter, 148810 bounded string comparison and 59A60 index lookup.
Image SHA256:
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.

The image hash in the generated artifact is authoritative; both source assets
are independently checked against the existing pinned current-client hashes.
Inputs are all 448 populated cbspec2 definitions. No skill identity is guessed
from a translated name or inferred from book ID subtraction.

| Native kind | Code prefix | Search base |
| --- | --- | --- |
| 0 | SpcA | 6500 |
| 1 | SpcD | 6600 |
| 2 | SpcC | 6700 |
| 3 | SpcB | 6800 |

The original loop scans base+1 through base+399, ascending. It compares the
book record's string at +11C against the formatted code, using six bytes below
ID 100 and seven bytes at or above 100. The first match wins. This is the
actual native prefix comparison, not a replacement dictionary or name join.

All SKB records and PFD records in the total 6501..7199 search interval are
parsed with original 59420 code, retained in separate records, and published
through the original 59A20 store. PFD entries are included because the native
scan can cross into their index interval. The existing row-loader CRT decimal
adapter remains in use; original sprintf and comparison execute unadapted.

The owner, stack and table are explicitly staged test memory. This qualifies
the metadata lookup, not a full live UI session, learning eligibility, damage
arithmetic, stacking order, or probability calculations. A zero-initialized WORD
output is an explicit harness precondition for absence checks; the original
function does not promise to clear a caller's stale output on a miss.

## Description links

The artifact joins matched book IDs to the earlier description ledger only
after checking the same canonical source-record SHA256. Descriptions preserve
their original text, conditions and `executable=false`. A verified identity
does not promote a description claim to a verified runtime equation.

For example, book 6568 stores SpcA96, not SpcA68; book 6571 stores SpcA99.
Book 6885 stores SpcB100, requiring the seven-byte branch. These are why simple
arithmetic conversion of book IDs is not acceptable.

## Qualified result

The generated run parsed 446 records: 381 SKB and 65 PFD. Of 448 populated
battle skill definitions, 381 return distinct book IDs and 67 do not match.
All 381 source books are covered once. Thus book coverage is 100%, and battle
definition-to-book coverage is 381/448 (85.04%); neither is formula completion.
All 61 description-ledger entries now have a source-checked native identity link.
The 67 unmatched definitions remain explicit; no multiplier is borrowed for them.

CTest passed current_item_metadata (13.78s), current_skill_description_rules
(0.52s), and current_skill_book_binding (59.52s), total 73.85s. The latter
contains three methods, including full-catalog and all-bank boundary checks.

## Emulator instrumentation correction

An isolated diagnostic on the installed Unicorn build reproduced a flag error:
`CMP AL,100; REP MOVSD` with AL=255 should preserve CF=0, but a global memory
write hook changes the flags during the repeated copy and produces CF=1.
That instrumentation incorrectly selected the six-byte comparison and aliased
255 to 25. A diagnostic without the global write hook preserves CF=0.

The binding harness removes its inherited global write hook after parsing.
It makes the image, input records, owner, index table and other input pages
read-only, and observes writes only in the output allocation. The private stack
remains writable. No flags, original instructions, comparisons, or branches
are patched. The tests check actual comparison width and post-copy carry for
boundary IDs, including 99, 100, 127 and 255 in all four banks.

The base parser now retains its hook handle; its default monitoring behavior
is unchanged. This correction is scoped to the new binding harness and is not
a claim that every other emulator-backed test has been audited for this issue.

## Reproduction

```powershell
python tests/research/test_current_skill_book_binding.py
python -m tools.strike_lab.current_skill_book_binding --output artifacts/research/current-skill-book-binding-20260920.json
```

The tests cover all populated identities, invalid input rejection, boundary and
missing lookups, original comparison widths/flags, and source-checked description
joins without formula promotion. No production database, C++/Lua combat rule,
or retired server archive is modified or used.
