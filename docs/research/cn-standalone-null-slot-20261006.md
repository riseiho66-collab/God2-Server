# CN standalone open failure, null slots and prior-cell preservation

Previous round made progress: retained standalone MAP bytes now follow the native
pointer rotation and valid slots avoid disk rereads. This round connects known
plain-file open failures through null-slot snapshots, native composition and
cache commit. Nine existing C++ files change; no new C++ file or opcode binding
is added. The owner requested stopping after this round: save evidence/report,
then pause the active goal. No following round is authorized until resumed.
No build, tests, loaders, Lua, client/server, production DB or deployment runs.
Native fonts, Traditional/Simplified conversion, saves and frozen features remain.

## Primary return and failure evidence

Recovered C incorrectly declares004657E0 void. Its assembly returns0 for an
empty reference (0046580C xor eax,eax), and for failed fopen:00465830 tests the
FILE pointer,0046583B calls the diagnostic,00465840 jumps to00465DE6, and
00465DE9 clears EAX before return00465DF8. The successful final section closes
the file and sets EAX=1 at00465DB7.0045E7F0 calls this reader at0045E829,
tests EAX at0045E82E and returns failure when zero. Historical raw recovered C
and prior receipts are preserved, with the return correction recorded separately.

00470C90 calls0045E7F0 at004715A4, tests EAX at004715A9 and, on failure,
invokes the slot destructor at004715C3 and writes the slot pointer zero at
004715C5. It continues the row-major loop, calls0046F630 at00471628 and sets
ESI=1 at00471653 after the qualified branch, independent of individual open
failures. This is native switch success with potentially missing slots, not a
full-nine load success or server movement authorization.

0046F630 skips a null slot at0046F675/0046F677 before any terrain write; the
corresponding21x21 area retains the exact prior passability bytes at the same
memory indices. It does not clear, shift or regenerate them. At0046F6BE..0046F6DE
it requires the center slot and current resource before traversing models; a
missing center skips model masks/markers.0046C280 also checks center pointer
at0046C2EC/0046C2F3 before its type7 renderer refresh.

## Actual source integration

try_read_cn_plain_map_file returns absence only when the actual plain file
cannot be opened. After a successful open, length, budget, short/changing reads
remain errors; unsupported format/axis/root/encoding is not converted into an
invented native failure. The existing mandatory asset reader still throws on
open failure and uses the same bounded open-stream implementation. No global
fallback, ignored format error, zero file or synthetic resource is introduced.

CnSceneAssets retains the attempted filename and an optional actual MAP asset.
CnOutdoorWindow passes its current initialized grid bytes into both different-MDT
replacement and same-MDT standalone reuse. Successful slots retain native loaded
coordinates; failed open slots have no coordinate, no MAP payload and valid=false.
Load-attempt flags remain distinct from successful-loaded flags. An absent slot
can be retried when the native pointer flow reaches its allocation/load branch;
there is no fabricated successful native+64/+68 or actor coordinate.

CnOutdoorSceneResources.compose_standalone_frame_window passes present actual
chunks and the exact initialized prior63x63 grid to the recovered compositor.
With center present it uses the actual retained MDL/model-ROM declared traversal;
with center absent it performs the proven model skip. No prior bytes with a
missing chunk raises an error, preserving the original full-coverage bootstrap
requirement. Cache/snapshot candidates remain private identity/generation-bound;
commit returns the conditional camera result and actual center_slot_available,
without granting permission, writing player position, applying a real camera or
publishing a packet.

## Null-pointer recycle boundary and open work

0046D460's adjacent rotation writes the recycled edge's+54 without a null check;
its long-jump/all-invalid branch checks each pointer before clearing. The source
preserves the exact pointer ordering but explicitly refuses an adjacent recycle
whose edge has no coordinate/payload, rather than inventing a successful native
null dereference. After horizontal invalidation a nonnull recycled corner still
retains its old coordinate, so the vertical phase distinguishes allocated-invalid
from an absent/deleted pointer. This crash/unqualified edge variant stays open.

MBD failed-offset/file paths, malformed scanf and other MAP versions/dimensions,
high-byte/nonalphabet axes and runtime model/frame/reset/renderer state remain
open. Actual camera/viewport/map34/prefix ownership, scene/position/cache transaction,
WorldOwner, movement timing/pending/reset/full5D, TW/CN publication, Application/
listeners/native login/bootstrap and remaining game routes still need integration.
Added complete bidirectional routes0; whole-game total/completed/percentage null.
Six native function spans and the plain-open mode are preserved along with old
source baselines. Finish this round's catalog/report, then stop work as requested.
