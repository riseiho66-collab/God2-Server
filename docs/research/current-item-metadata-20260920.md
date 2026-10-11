# Original Item Metadata Row Loading

Main continuation while the three formula workers trace damage/hit/critical.
The immediate battle frontier110228 reads owner+85A30, qualified separately as
slot44's first WORD. Its later resource path9B670 calls9B720, which looks up
native item metadata and consumes WORDs+116/+118. This work establishes an
actual current-source producer for that metadata layout; it does not assign
an item to the player's slot44.

## Executed Evidence

Latest integration adds current MIS:4660 (line7636, original tag selector24).
Its source icon51123 becomes native group37 with initial actionFFFF. The same
loader can now attach to an existing resource VM after checking its original
code ranges; the resource VM's existing CRT adapter is retained. Optional record
retention keeps the original index store and rejects subsequent row replacement.
This joins the bootstrap's owner lookup without transplanting metadata from a
different VM. No action-resolution or actual equipment claim follows from it.

`current_item_metadata.py` pins the current mapped image and current gamedata
using existing `recover_combat_rules` SHA256 checks. It uses only the existing
CRT decimal adapter; original tokenizer, string-copy/search, item row parser,
index registration, lookup and resource-selector instructions execute unchanged.
No game function return is substituted.

- All57 RomMaps records run original51BE0 and59F47..59FA3. Output stride84h
  contains low/high WORDs and the exact original resource path; full poisoned
  output/canaries are checked. The source header contains extra locale labels,
  so existing item section parsing is used instead of the companion parser's
  two-field-only section envelope.
- 302 original59FC0 boundary probes include low/high endpoints, adjacent values,
  unmatched IDs and nonzero high argument bits. Results equal the first original
  matching range, withFFFF for no match. Arguments are consumed as low WORDs.
- All27 EGG and28 SPP rows execute the complete original59420 function to its
  real return, followed by original59A20 index registration,59A60 lookup and
  9B720 resource selection. Current image tag-array first matches at14/15 bind
  the section selector; this tag binding is static, not execution of59301's
  entire ItemType loader.
- Original source icon column3 becomes WORD+114; resource group becomesWORD+116
  through59FC0. All current EGG rows resolvegroup20, SPPgroup21. Original59420
  sets action WORD+118 toFFFF. The subsequent9B720 output reads these exact
  native-produced words, not pointers into raw CSV bytes.
- Names, two raw DWORD numeric fields, common bitfield columns14..25 and all
  record canaries are compared against the actual source. These are client
  data conversions, not server ownership, economy, effect or incubation rules.

## Scope And Limits

Native allocations/file dispatch are staged. The row starts with the zeroed
396-byte allocation precondition of the original599B0 calloc call. RomMaps
count/pointer and owner catalog pointer are explicit fixture inputs. Each row
uses one temporary native record; its registered index is cleared afterward
unless explicitly retained. A retained record cannot be overwritten, so prior
item IDs cannot silently alias a newly parsed row.

This is not the full ItemType/gamedata loader or all16,127 item definitions.
This module produces initialFFFF, not a usable handle. The separate
current_item_action_binding module now loads the actual MIS03 ROM and executes
the original action resolver/writer; bootstrap applies that stage in the same
VM before normal1112C0. See current-battle-bootstrap-20260920.md for its current
continuous boundary. No live client/server,
production database, original gameplay formula or hatch transaction is certified.

Execution is bounded to50,000 instructions/one second per call. Code allowlists
include exact tokenizer/accessor/row/lookup functions and the native strchr and
strncpy implementations. Native non-stack writes are bounded for row execution,
lookup outputs and index registration. Tests reject unknown code and disallowed
writes; original image bytes remain unchanged.

## Reproduction

```powershell
python -B -m unittest discover -s tests/research -p test_current_item_metadata.py -v
```

The initial complete source matrix passed in9.581s. After adding native-code
allowlists it passed in10.133s. A further guard-negative test was added and the
registered CTest rerun is recorded in the reconstruction status. Final standalone
four-test run passes in10.098s; latest registered target passes in10.52s.

After attached-VM/retained-record integration, seven metadata tests pass as part
of30 metadata/growth/progression tests in57.598s. They include retained MIS:4660,
overwrite rejection, changed attached-code rejection and typed-input guards.
Registered metadata/action-binding/owner-slot CTest3/3 passes in24.04s.

Early fixture failures were corrected: the RomMaps header has extra fields,
and the native count WORD atD2D54 has a two-byte gap before pointerD2D58.
No client bytes or source rows were changed to make these fixtures pass.
