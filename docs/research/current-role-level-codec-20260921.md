# Native level snapshot codec and follow-on resource clamp

RecoveredRoleLevel is a lossless25-byte logical22 codec. This integrates the
previously recorded E6B40 scalar contract; it does not present that old mapping
as a newly discovered XP/growth formula. Level-progress replacement requires
a complete parsed snapshot and changes only logical1 and13..14. No runtime
sender, synthetic stat growth or default actor record has been introduced.

Logical offsets: level1/BYTE, unclassified state3/WORD, four base stat slots
5/7/9/11 WORDs, progress13/WORD, maxHP17/DWORD, maxMP21/DWORD. Opaque2,15,16
survive unchanged. Original WORD base stats are zero-extended into actor DWORDs.
Stat ordering is not newly assigned a gameplay meaning here. Structural parsing
preserves all bit patterns, not an endorsement of level0 or any official cap.

## Native follow-on evidence

Pinned current image SHA256149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Full function disassembly shows E6BD4 -> E6DB0 (UI refresh), then E6BE6 -> E72D0.
The latter is a forwarding shim E72D0..E72E4 calling AC070 at E72DF. Its current
HP/MP clamp was previously qualified separately; this test executes the actual
forwarder after C++-encoded22 has populated the new maxima.

test_current_role_level_codec.py executes20 snapshot cases: levels1,2,127,255
crossed with maxima120/80,50/10,0/80,120/0,FFFFFFFF/80000000. Exact whole-actor
comparison and read hooks verify all native scalar reads/stores, no prefix HP/MP
refill, untouched bytes and input preservation. Then original E72D0 -> AC070
executes with its real arguments. With nonzero maxima, HP76/MP26 is clamped to
the new maxima; raising maxima does not heal. Either zero maximum skips the
clamp in this path. No production zero maximum is authorized by that finding.

E6DB0 formatting and the remainder of AC070 rendering are excluded, not replaced
with success stubs. This is bounded native-slice execution, not a full live22
receive or visual upgrade acceptance. Original code and source hash are unchanged.

## Tests and limits

C++ checks1280 level/progress combinations, all shorter lengths, oversized
input, every opcode, ownership, roundtrip and untouched fields. Initial strict
private compilation rejected an implicit int-to-WORD test-loop conversion;
using an explicit WORD array resolved it. Its diagnostic output also exposed
the existing compiler adapter's encoding weakness; no failed run was counted.
Both Python tests then pass, including strict C++ compilation and actual native
store/clamp slices.

Before production level-up, persist a complete authoritative role snapshot and
curve version, apply growth in Lua, and atomically reconcile current resources
with new maxima. Emit22/2B consistently with that committed state. Do not zero
unknown stats, assume automatic full heal, or treat22 as an incremental command.
Official growth, thresholds, locks, populated UI refresh and live level update
remain open. Reusable codec has no production or diagnostic sender yet.
