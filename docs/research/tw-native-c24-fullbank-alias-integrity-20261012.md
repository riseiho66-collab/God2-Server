# C24 complete native bank alias integrity, round343

The existing C24 planner now rejects any exact pinned TW item20 alias outside
its50-row native bank before either move mode can prepare a result or write.
The check visits all owned cells and aliases, including those outside the two
requested bag locations. This repairs the actual population reconciliation;
it creates no item, bank population, native witness or Main provider.

## Defect and exact repair

OwnedItemNativeAlias.native_slot is a BYTE; the generic SQLite alias schema
permits0..255 for multiple client/profile formats. Generic validity checks
unique(client_sha256,profile,native_slot) but has no TW-specific bank boundary.
The C24 alias_row function previously ran only for slots0..49 and skipped any
alias whose native_slot did not equal the current row. Consequently an extra
exact TW149c/tw149c-item20 alias at50..255 in another owned cell could evade
both old and next50-row predicates. Generic joint writer checks/issuer replay
did not add that omitted format-specific condition.

The inserted block matches precisely NativeEquipmentSnapshot::client_pin and
SharedTaiwanOwnedItemSelectionSource::alias_profile, then rejects slot>=50.
The whole BYTE domain partitions into50 in-bank values0..49 and206 outside
values50..255. This is a source-domain proof, not an executed sample inventory.
All matching in-bank values and all other client/profile pairs bypass only
this new guard and retain their prior downstream behavior.

Both CUSTOM-0093 same18-tail and CUSTOM-0094 full25-material modes use the
same plan before output encoding, joint CAS and synchronous issuer callbacks.
The guard precedes the original old50-row checks. Existing raw request limits
source/destination<30 and their distinctness remain. Later projected slot
changes use those exact two request slots, so they cannot introduce an outside
TW slot; the original next50-row reconciliation remains unchanged.

The rest of the original C++ file survives byte-for-byte;562 new LF bytes are
inserted once. No schema/global BYTE bound changed, no aliases were deleted,
no saved bank was normalized and no acquisition/quantity/full20/DA15 was invented.
The independent audit retained exact old HEAD and final source and verified
the source-only diff/domain reasoning. No C++ predicate or planner was executed.

## Concrete route and missing real suppliers

C24 already has a full-next whole-instance planner, owned ready lease/root
checks, joint inventory/equipment CAS and two prebuilt native41 replies. Its
server relocation policy stays CUSTOM-0093, not recovered original server rules.
Main still calls run_server(config,seconds), which selects no world plan.

The bank audit qualifies the actual same-connection joint observe_before and
observe_committed readers only for already-stored complete pairs. A read receipt
is not original acquisition or population authority. Generic writers require
real full-state issuers; C24 retains an existing before pair. The bounded current
src/tools/config search found no concrete initial owned/native-equipment bank
population controller. This is not a claim of global absence. Legacy scalar,
weapon/armor/PET or diagnostic data cannot fill raw1215/aliases/acquisition fields.

The host audit identifies actual2A qualification, complete initial publication,
direction, ROM model+1C prefix, resource/publication generations, full5D pending
Authority, records Current and real Others as missing Main suppliers. Context
readers do not supply those fields. Existing with_owned_inventory_movement is
also required for walk-then-C24 so position and native witness move atomically;
that CUSTOM-0095 path already exists and no new wrapper is added here.

The independent13 gameplay gap inventory and50 reviewed opcode crosswalk remain
separate from route completion. The selected native preview audit also corrects
4D68D0 to control22's alternative prefix, not a child after common49B820; its
local20 type-only projection does not create owned instance material or B1 send.
Its exact native evidence is retained externally and gives no new route credit.

## Custody and limits

Heavy artifacts are external under20261012. Prior gap/line-correction/preview/
bank/host/audit/implementation packages are immutable and each member is hashed.
Bank and host snapshots deliberately retain old HEAD43f4d29; this additive C24
repair is a separate later delta. Five public helpers are exact LF originals
from successful sealed sources, not rerun. Helper failure candidates/corrections
remain in their original packages. Baseline goal bytes survive as exact prefix;
ledger preserves every prior parsed field and v23 remains byte-identical.

New complete bidirectional routes/opcode/format/parser/phase/method credits0.
TW156C2S/252S2C; world74=50partial/11control/13unconnected. Parser source67.6%
is not TW completion. Whole-game denominator and percent remain unknown.
Full TW-first/CN/fourWS/common tables/common64/coin99999999999/qualifiedstack99/
native levels/frozen/fonts/conversion objective stays active. PHASE1: no builds,
compiler/tests/runtime/native/API/CRT/VM/codec/parser/gameDBSQL/migration/
activation/deployment. Static source/hash/PE/metadata/custody inspection only.
